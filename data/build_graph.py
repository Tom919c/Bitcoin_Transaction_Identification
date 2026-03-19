"""
从数据库构建子图，生成 data.pt。
"""

from __future__ import annotations

import heapq
import json
import os
import tempfile
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

import numpy as np
import pandas as pd
import torch
from torch_geometric.data import Data

from .features import FEATURE_COLUMNS, compute_score, ensure_feature_columns, z_score_normalize
from .utils import (
    LABEL_MAP,
    connect_db,
    create_semi_supervised_masks,
    get_neighbors,
    load_edges_filtered,
    load_nodes_by_aliases,
    load_nodes_in_chunks
)


def _clean_node_chunk(chunk: pd.DataFrame) -> pd.DataFrame:
    """标准化用于筛选的4个特征列并清理基础字段。"""
    cleaned = ensure_feature_columns(chunk)
    if 'alias' not in cleaned.columns:
        raise KeyError("节点数据缺少 alias 列")

    cleaned = cleaned.copy()
    cleaned['alias'] = cleaned['alias'].astype(str)
    if 'label' not in cleaned.columns:
        cleaned['label'] = ''
    cleaned['label'] = cleaned['label'].fillna('').astype(str)
    return cleaned


def _make_checkpoint_signature(
    node_table: str,
    edge_table: str,
    target_labels: Sequence[str],
    max_nodes: int,
    chunk_size: int
) -> str:
    """生成缓存签名，用于校验缓存是否可复用。"""
    payload = {
        'node_table': str(node_table),
        'edge_table': str(edge_table),
        'target_labels': sorted({str(label).upper().strip() for label in target_labels}),
        'max_nodes': int(max_nodes),
        'chunk_size': int(chunk_size),
        'score_feature_columns': list(FEATURE_COLUMNS)
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)


def _atomic_torch_save(obj: Any, path: str) -> None:
    """原子写入，避免中断导致缓存文件损坏。"""
    target_dir = os.path.dirname(path)
    if target_dir:
        os.makedirs(target_dir, exist_ok=True)

    fd, temp_path = tempfile.mkstemp(prefix='.tmp_ckpt_', suffix='.pt', dir=target_dir or '.')
    os.close(fd)
    try:
        torch.save(obj, temp_path)
        os.replace(temp_path, path)
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


def _load_stage_checkpoint(
    path: str,
    signature: str,
    resume_enabled: bool,
    force_recompute: bool
) -> Optional[Any]:
    """加载单阶段缓存，校验签名后返回 data。"""
    if not resume_enabled or force_recompute or not os.path.exists(path):
        return None

    try:
        payload = torch.load(path, map_location='cpu')
    except Exception as exc:
        print(f"缓存读取失败，忽略并重算: {path}, 错误: {exc}")
        return None

    if not isinstance(payload, dict):
        print(f"缓存格式无效，忽略并重算: {path}")
        return None

    if payload.get('signature') != signature:
        print(f"缓存签名不匹配，忽略并重算: {path}")
        return None

    if 'data' not in payload:
        print(f"缓存缺少 data 字段，忽略并重算: {path}")
        return None

    return payload['data']


def _save_stage_checkpoint(
    path: str,
    signature: str,
    data: Any,
    resume_enabled: bool
) -> None:
    """保存单阶段缓存。"""
    if not resume_enabled:
        return
    _atomic_torch_save({'signature': signature, 'data': data}, path)


def _compute_global_stats(
    conn,
    chunk_size: int,
    node_table: str
) -> Tuple[pd.Series, pd.Series, Set[str]]:
    """
    第一遍扫描：
    - 统计全图筛选特征 mean/std（用于全局 Z-score）
    - 收集 BRIDGE 节点
    """
    feature_sum = np.zeros(len(FEATURE_COLUMNS), dtype=np.float64)
    feature_square_sum = np.zeros(len(FEATURE_COLUMNS), dtype=np.float64)
    total_count = 0
    bridge_nodes: Set[str] = set()

    for chunk in load_nodes_in_chunks(conn, chunk_size=chunk_size, table_name=node_table):
        cleaned = _clean_node_chunk(chunk)
        values = cleaned[FEATURE_COLUMNS].to_numpy(dtype=np.float64)
        values = np.nan_to_num(values, nan=0.0, posinf=0.0, neginf=0.0)

        feature_sum += values.sum(axis=0)
        feature_square_sum += np.square(values).sum(axis=0)
        total_count += values.shape[0]

        labels = cleaned['label'].str.upper().str.strip()
        bridge_aliases = cleaned.loc[labels == 'BRIDGE', 'alias'].astype(str).tolist()
        bridge_nodes.update(bridge_aliases)

    if total_count == 0:
        raise ValueError("node_features 表为空，无法构建数据")

    mean = feature_sum / total_count
    variance = np.maximum(feature_square_sum / total_count - np.square(mean), 1e-12)
    std = np.sqrt(variance)

    return (
        pd.Series(mean, index=FEATURE_COLUMNS, dtype=np.float64),
        pd.Series(std, index=FEATURE_COLUMNS, dtype=np.float64),
        bridge_nodes
    )


def _select_topk_nodes(
    conn,
    max_nodes: int,
    chunk_size: int,
    node_table: str,
    mean: pd.Series,
    std: pd.Series
) -> Set[str]:
    """第二遍扫描：基于 FinalScore 选择 TopK 节点。"""
    if max_nodes <= 0:
        raise ValueError("max_nodes 必须大于0")

    min_heap: List[Tuple[float, str]] = []

    for chunk in load_nodes_in_chunks(conn, chunk_size=chunk_size, table_name=node_table):
        cleaned = _clean_node_chunk(chunk)
        normalized_df = z_score_normalize(
            cleaned[FEATURE_COLUMNS],
            feature_columns=FEATURE_COLUMNS,
            mean=mean,
            std=std
        )
        scores = compute_score(normalized_df, feature_columns=FEATURE_COLUMNS, normalized=True)

        aliases = cleaned['alias'].astype(str).tolist()
        score_values = scores.to_numpy(dtype=np.float64)
        for alias, score in zip(aliases, score_values):
            if len(min_heap) < max_nodes:
                heapq.heappush(min_heap, (float(score), alias))
            elif score > min_heap[0][0]:
                heapq.heapreplace(min_heap, (float(score), alias))

    return {alias for _, alias in min_heap}


def _encode_labels(labels: pd.Series, target_labels: Sequence[str]) -> torch.LongTensor:
    """将字符串标签编码为整数标签。"""
    target_set = {str(label).upper().strip() for label in target_labels}
    encoded = []

    for raw_label in labels.fillna('').astype(str):
        label = raw_label.upper().strip()
        if label in target_set and label in LABEL_MAP:
            encoded.append(LABEL_MAP[label])
        else:
            encoded.append(LABEL_MAP['NONE'])

    return torch.LongTensor(encoded)


def _build_node_features(selected_df: pd.DataFrame) -> Tuple[torch.FloatTensor, List[str]]:
    """
    构建节点特征矩阵：
    - 仅保留数值可用列
    - 统一做 Z-score（在选中子图范围内）
    """
    excluded = {'alias', 'label'}
    candidate_columns = [col for col in selected_df.columns if col not in excluded]
    if not candidate_columns:
        raise ValueError("节点表中没有可用于训练的特征列")

    numeric_df = selected_df[candidate_columns].apply(pd.to_numeric, errors='coerce')
    valid_columns = [col for col in numeric_df.columns if not numeric_df[col].isna().all()]
    if not valid_columns:
        raise ValueError("节点特征列均无法转换为数值")

    dropped_columns = [col for col in candidate_columns if col not in valid_columns]
    if dropped_columns:
        preview = dropped_columns[:8]
        suffix = ' ...' if len(dropped_columns) > 8 else ''
        print(f"提示: 跳过非数值节点列 {preview}{suffix}")

    numeric_df = numeric_df[valid_columns].replace([np.inf, -np.inf], np.nan).fillna(0.0)
    mean = numeric_df.mean(axis=0)
    std = numeric_df.std(axis=0, ddof=0).replace(0, 1.0)
    normalized = (numeric_df - mean) / std
    normalized = normalized.replace([np.inf, -np.inf], np.nan).fillna(0.0)

    x = torch.tensor(normalized.to_numpy(dtype=np.float32), dtype=torch.float32)
    return x, valid_columns


def _build_edge_index_and_attr(
    edge_df: pd.DataFrame,
    node_to_index: Dict[str, int]
) -> Tuple[torch.LongTensor, torch.FloatTensor, List[str]]:
    """从边表构建 edge_index 和 edge_attr。"""
    if edge_df.empty:
        return (
            torch.empty((2, 0), dtype=torch.long),
            torch.empty((0, 0), dtype=torch.float32),
            []
        )

    if 'a' not in edge_df.columns or 'b' not in edge_df.columns:
        raise KeyError("transaction_edges 缺少必要字段 a/b")

    working_df = edge_df.copy()
    working_df['a'] = working_df['a'].astype(str)
    working_df['b'] = working_df['b'].astype(str)

    sources: List[int] = []
    targets: List[int] = []
    kept_rows: List[int] = []

    for idx, (source_alias, target_alias) in enumerate(
        zip(working_df['a'].tolist(), working_df['b'].tolist())
    ):
        src_idx = node_to_index.get(source_alias)
        dst_idx = node_to_index.get(target_alias)
        if src_idx is None or dst_idx is None:
            continue
        sources.append(src_idx)
        targets.append(dst_idx)
        kept_rows.append(idx)

    if not sources:
        return (
            torch.empty((2, 0), dtype=torch.long),
            torch.empty((0, 0), dtype=torch.float32),
            []
        )

    edge_index = torch.tensor([sources, targets], dtype=torch.long)

    attr_candidates = [col for col in working_df.columns if col not in {'a', 'b'}]
    if not attr_candidates:
        edge_attr = torch.empty((len(sources), 0), dtype=torch.float32)
        return edge_index, edge_attr, []

    attr_df = working_df.iloc[kept_rows][attr_candidates].apply(pd.to_numeric, errors='coerce')
    valid_attr_columns = [col for col in attr_df.columns if not attr_df[col].isna().all()]
    dropped_attr_columns = [col for col in attr_candidates if col not in valid_attr_columns]
    if dropped_attr_columns:
        preview = dropped_attr_columns[:8]
        suffix = ' ...' if len(dropped_attr_columns) > 8 else ''
        print(f"提示: 跳过非数值边列 {preview}{suffix}")

    if not valid_attr_columns:
        edge_attr = torch.empty((len(sources), 0), dtype=torch.float32)
        return edge_index, edge_attr, []

    attr_df = attr_df[valid_attr_columns].replace([np.inf, -np.inf], np.nan).fillna(0.0)
    edge_attr = torch.tensor(attr_df.to_numpy(dtype=np.float32), dtype=torch.float32)
    return edge_index, edge_attr, valid_attr_columns


def build_and_save_data(output_path: str, config: Dict) -> Data:
    """
    从数据库读取原始数据，执行节点筛选、特征工程、掩码划分，保存 data.pt。
    """
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    db_config = config.get('data', {})
    preprocess_config = config.get('preprocessing', {})
    train_config = config.get('train', {})

    target_labels = preprocess_config.get(
        'target_labels',
        ['INDIVIDUAL', 'BET', 'GAMBLING', 'EXCHANGE', 'BRIDGE']
    )
    max_nodes = int(preprocess_config.get('max_nodes', 350000))
    chunk_size = int(preprocess_config.get('chunk_size', 50000))
    val_ratio = float(preprocess_config.get('val_ratio', 0.2))
    test_ratio = float(preprocess_config.get('test_ratio', 0.2))
    seed = int(train_config.get('seed', 42))

    resume_enabled = bool(preprocess_config.get('resume_enabled', True))
    force_recompute = bool(preprocess_config.get('force_recompute', False))
    checkpoint_dir = preprocess_config.get('checkpoint_dir', './data/processed/checkpoints')
    if not checkpoint_dir:
        checkpoint_dir = './data/processed/checkpoints'

    x, edge_index, y, edge_attr, feature_columns, edge_attr_columns = load_raw_data(
        db_connection_string=db_config.get('raw_db'),
        target_labels=target_labels,
        max_nodes=max_nodes,
        chunk_size=chunk_size,
        node_table=db_config.get('node_table', 'node_features'),
        edge_table=db_config.get('edge_table', 'transaction_edges'),
        resume_enabled=resume_enabled,
        checkpoint_dir=checkpoint_dir,
        force_recompute=force_recompute
    )

    train_mask, val_mask, test_mask = create_semi_supervised_masks(
        labels=y,
        val_ratio=val_ratio,
        test_ratio=test_ratio,
        seed=seed
    )

    payload = {
        'x': x,
        'edge_index': edge_index,
        'edge_attr': edge_attr,
        'y': y,
        'train_mask': train_mask,
        'val_mask': val_mask,
        'test_mask': test_mask,
        'feature_columns': feature_columns,
        'edge_attr_columns': edge_attr_columns
    }

    torch.save(payload, output_path)

    data = Data(
        x=x,
        edge_index=edge_index,
        edge_attr=edge_attr,
        y=y,
        train_mask=train_mask,
        val_mask=val_mask,
        test_mask=test_mask
    )
    data.feature_columns = feature_columns
    data.edge_attr_columns = edge_attr_columns

    labeled_count = int((y != LABEL_MAP['NONE']).sum().item())
    print(f"数据已保存到: {output_path}")
    print(f"节点数: {data.num_nodes}, 边数: {data.num_edges}, 节点特征维度: {data.num_features}, 边特征维度: {edge_attr.shape[1]}")
    print(f"有标签节点数: {labeled_count}, train/val/test: {int(train_mask.sum())}/{int(val_mask.sum())}/{int(test_mask.sum())}")

    return data


def load_raw_data(
    db_connection_string: Optional[str],
    target_labels: Sequence[str],
    max_nodes: int,
    chunk_size: int = 50000,
    node_table: str = 'node_features',
    edge_table: str = 'transaction_edges',
    resume_enabled: bool = True,
    checkpoint_dir: str = './data/processed/checkpoints',
    force_recompute: bool = False
) -> Tuple[torch.FloatTensor, torch.LongTensor, torch.LongTensor, torch.FloatTensor, List[str], List[str]]:
    """
    从数据库加载并筛选原始数据。
    """
    if not db_connection_string:
        raise ValueError("缺少数据库连接字符串: data.raw_db")
    if max_nodes <= 0:
        raise ValueError("max_nodes 必须大于0")

    signature = _make_checkpoint_signature(
        node_table=node_table,
        edge_table=edge_table,
        target_labels=target_labels,
        max_nodes=max_nodes,
        chunk_size=chunk_size
    )
    if resume_enabled:
        os.makedirs(checkpoint_dir, exist_ok=True)

    stage_paths = {
        'stage1': os.path.join(checkpoint_dir, 'stage_1_stats.pt'),
        'stage2': os.path.join(checkpoint_dir, 'stage_2_topk.pt'),
        'stage3': os.path.join(checkpoint_dir, 'stage_3_selected_nodes.pt'),
        'stage4': os.path.join(checkpoint_dir, 'stage_4_selected_df.pt'),
        'stage5': os.path.join(checkpoint_dir, 'stage_5_edges_df.pt')
    }

    conn = connect_db(db_connection_string)
    sql_batch_size = max(1000, min(chunk_size, 20000))

    try:
        print("阶段1/5: 统计全图特征分布并收集 BRIDGE 节点...")
        stage1_data = _load_stage_checkpoint(
            stage_paths['stage1'],
            signature=signature,
            resume_enabled=resume_enabled,
            force_recompute=force_recompute
        )
        if stage1_data is not None:
            mean = pd.Series(stage1_data['mean'], index=FEATURE_COLUMNS, dtype=np.float64)
            std = pd.Series(stage1_data['std'], index=FEATURE_COLUMNS, dtype=np.float64)
            bridge_nodes = set(stage1_data['bridge_nodes'])
            print(f"阶段1命中缓存: BRIDGE节点 {len(bridge_nodes)}")
        else:
            mean, std, bridge_nodes = _compute_global_stats(
                conn=conn,
                chunk_size=chunk_size,
                node_table=node_table
            )
            _save_stage_checkpoint(
                stage_paths['stage1'],
                signature=signature,
                data={
                    'mean': mean.to_dict(),
                    'std': std.to_dict(),
                    'bridge_nodes': sorted(bridge_nodes)
                },
                resume_enabled=resume_enabled
            )

        print("阶段2/5: 计算 FinalScore 并筛选 TopK 节点...")
        stage2_data = _load_stage_checkpoint(
            stage_paths['stage2'],
            signature=signature,
            resume_enabled=resume_enabled,
            force_recompute=force_recompute
        )
        if stage2_data is not None:
            topk_nodes = set(stage2_data['topk_nodes'])
            print(f"阶段2命中缓存: TopK节点 {len(topk_nodes)}")
        else:
            topk_nodes = _select_topk_nodes(
                conn=conn,
                max_nodes=max_nodes,
                chunk_size=chunk_size,
                node_table=node_table,
                mean=mean,
                std=std
            )
            _save_stage_checkpoint(
                stage_paths['stage2'],
                signature=signature,
                data={'topk_nodes': sorted(topk_nodes)},
                resume_enabled=resume_enabled
            )

        print("阶段3/5: 执行 BRIDGE 邻居增强...")
        stage3_data = _load_stage_checkpoint(
            stage_paths['stage3'],
            signature=signature,
            resume_enabled=resume_enabled,
            force_recompute=force_recompute
        )
        if stage3_data is not None:
            selected_nodes = set(stage3_data['selected_nodes'])
            print(f"阶段3命中缓存: 选中节点 {len(selected_nodes)}")
        else:
            bridge_neighbors = get_neighbors(
                conn=conn,
                node_ids=list(bridge_nodes),
                table_name=edge_table,
                batch_size=sql_batch_size
            )
            selected_nodes = topk_nodes.union(bridge_nodes).union(bridge_neighbors)
            if not selected_nodes:
                raise ValueError("筛选后节点集合为空，请检查数据库数据和配置")
            print(f"TopK节点: {len(topk_nodes)}, BRIDGE节点: {len(bridge_nodes)}, BRIDGE邻居: {len(bridge_neighbors)}")
            print(f"最终选中节点总数: {len(selected_nodes)}")
            _save_stage_checkpoint(
                stage_paths['stage3'],
                signature=signature,
                data={'selected_nodes': sorted(selected_nodes)},
                resume_enabled=resume_enabled
            )

        print("阶段4/5: 读取选中节点特征与标签（保留全部节点特征）...")
        stage4_data = _load_stage_checkpoint(
            stage_paths['stage4'],
            signature=signature,
            resume_enabled=resume_enabled,
            force_recompute=force_recompute
        )
        if stage4_data is not None:
            selected_df = stage4_data['selected_df']
            print(f"阶段4命中缓存: 节点行数 {len(selected_df)}")
        else:
            selected_df = load_nodes_by_aliases(
                conn=conn,
                node_ids=list(selected_nodes),
                table_name=node_table,
                chunk_size=chunk_size,
                insert_batch_size=sql_batch_size
            )
            if selected_df.empty:
                raise ValueError("未读取到选中节点特征，请检查节点表和字段")
            selected_df = selected_df.drop_duplicates(subset='alias', keep='first').reset_index(drop=True)
            _save_stage_checkpoint(
                stage_paths['stage4'],
                signature=signature,
                data={'selected_df': selected_df},
                resume_enabled=resume_enabled
            )

        if 'alias' not in selected_df.columns:
            raise KeyError("节点数据缺少 alias 列")
        selected_df = selected_df.copy()
        selected_df['alias'] = selected_df['alias'].astype(str)
        if 'label' not in selected_df.columns:
            selected_df['label'] = ''
        selected_df['label'] = selected_df['label'].fillna('').astype(str)

        x, feature_columns = _build_node_features(selected_df)
        y = _encode_labels(selected_df['label'], target_labels)
        node_aliases = selected_df['alias'].tolist()
        node_to_index = {alias: idx for idx, alias in enumerate(node_aliases)}

        print("阶段5/5: 读取选中子图边（保留全部边特征）并构建 edge_index...")
        stage5_data = _load_stage_checkpoint(
            stage_paths['stage5'],
            signature=signature,
            resume_enabled=resume_enabled,
            force_recompute=force_recompute
        )
        if stage5_data is not None:
            edge_df = stage5_data['edge_df']
            print(f"阶段5命中缓存: 边行数 {len(edge_df)}")
        else:
            edge_df = load_edges_filtered(
                conn=conn,
                selected_nodes=node_aliases,
                table_name=edge_table,
                chunk_size=chunk_size,
                insert_batch_size=sql_batch_size
            )
            _save_stage_checkpoint(
                stage_paths['stage5'],
                signature=signature,
                data={'edge_df': edge_df},
                resume_enabled=resume_enabled
            )

        edge_index, edge_attr, edge_attr_columns = _build_edge_index_and_attr(edge_df, node_to_index)
        return x, edge_index, y, edge_attr, feature_columns, edge_attr_columns
    finally:
        conn.close()


def load_data(data_path: str) -> Data:
    """
    加载已处理的 data.pt 文件（兼容字典和 Data 两种格式）。
    """
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"数据文件不存在: {data_path}")

    loaded = torch.load(data_path, map_location='cpu')
    if isinstance(loaded, Data):
        return loaded

    if not isinstance(loaded, dict):
        raise TypeError(f"不支持的数据格式: {type(loaded)}")

    required_keys = {'x', 'edge_index', 'y', 'train_mask', 'val_mask', 'test_mask'}
    missing_keys = required_keys - set(loaded.keys())
    if missing_keys:
        raise KeyError(f"data.pt 缺少必要字段: {sorted(missing_keys)}")

    x = loaded['x'] if torch.is_tensor(loaded['x']) else torch.tensor(loaded['x'], dtype=torch.float32)
    edge_index = loaded['edge_index'] if torch.is_tensor(loaded['edge_index']) else torch.tensor(loaded['edge_index'], dtype=torch.long)
    y = loaded['y'] if torch.is_tensor(loaded['y']) else torch.tensor(loaded['y'], dtype=torch.long)
    train_mask = loaded['train_mask'] if torch.is_tensor(loaded['train_mask']) else torch.tensor(loaded['train_mask'], dtype=torch.bool)
    val_mask = loaded['val_mask'] if torch.is_tensor(loaded['val_mask']) else torch.tensor(loaded['val_mask'], dtype=torch.bool)
    test_mask = loaded['test_mask'] if torch.is_tensor(loaded['test_mask']) else torch.tensor(loaded['test_mask'], dtype=torch.bool)

    if 'edge_attr' in loaded:
        edge_attr = loaded['edge_attr'] if torch.is_tensor(loaded['edge_attr']) else torch.tensor(loaded['edge_attr'], dtype=torch.float32)
    else:
        edge_attr = torch.empty((edge_index.shape[1], 0), dtype=torch.float32)

    data = Data(
        x=x,
        edge_index=edge_index,
        edge_attr=edge_attr,
        y=y,
        train_mask=train_mask,
        val_mask=val_mask,
        test_mask=test_mask
    )

    if 'feature_columns' in loaded:
        data.feature_columns = list(loaded['feature_columns'])
    if 'edge_attr_columns' in loaded:
        data.edge_attr_columns = list(loaded['edge_attr_columns'])

    return data
