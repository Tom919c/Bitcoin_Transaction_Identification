"""
从数据库构建子图，生成data.pt
"""

from __future__ import annotations

import heapq
import os
from typing import Dict, List, Optional, Sequence, Set, Tuple

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
    """标准化节点特征列并清理基础字段。"""
    cleaned = ensure_feature_columns(chunk)
    if 'alias' not in cleaned.columns:
        raise KeyError("节点数据缺少 alias 列")

    cleaned = cleaned.copy()
    cleaned['alias'] = cleaned['alias'].astype(str)
    if 'label' not in cleaned.columns:
        cleaned['label'] = ''
    cleaned['label'] = cleaned['label'].fillna('').astype(str)
    return cleaned


def _compute_global_stats(
    conn,
    chunk_size: int,
    node_table: str
) -> Tuple[pd.Series, pd.Series, Set[str]]:
    """
    第一遍扫描：
    - 统计全图特征 mean/std（用于全局Z-score）
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


def _build_edge_index(
    edge_pairs: np.ndarray,
    node_to_index: Dict[str, int]
) -> torch.LongTensor:
    """将边数组转换为 PyG edge_index。"""
    if edge_pairs.size == 0:
        return torch.empty((2, 0), dtype=torch.long)

    sources = []
    targets = []
    for source, target in edge_pairs:
        src_idx = node_to_index.get(str(source))
        dst_idx = node_to_index.get(str(target))
        if src_idx is None or dst_idx is None:
            continue
        sources.append(src_idx)
        targets.append(dst_idx)

    if not sources:
        return torch.empty((2, 0), dtype=torch.long)

    return torch.tensor([sources, targets], dtype=torch.long)


def build_and_save_data(output_path: str, config: Dict) -> Data:
    """
    从数据库读取原始数据，执行节点筛选、特征工程、掩码划分，保存data.pt。
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

    x, edge_index, y = load_raw_data(
        db_connection_string=db_config.get('raw_db'),
        target_labels=target_labels,
        max_nodes=max_nodes,
        chunk_size=chunk_size,
        node_table=db_config.get('node_table', 'node_features'),
        edge_table=db_config.get('edge_table', 'transaction_edges')
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
        'y': y,
        'train_mask': train_mask,
        'val_mask': val_mask,
        'test_mask': test_mask
    }

    # 按文档要求保存字典；load_data 会负责兼容读取为 PyG Data
    torch.save(payload, output_path)

    data = Data(**payload)
    labeled_count = int((y != LABEL_MAP['NONE']).sum().item())
    print(f"数据已保存到: {output_path}")
    print(f"节点数: {data.num_nodes}, 边数: {data.num_edges}, 特征维度: {data.num_features}")
    print(f"有标签节点数: {labeled_count}, train/val/test: {int(train_mask.sum())}/{int(val_mask.sum())}/{int(test_mask.sum())}")

    return data


def load_raw_data(
    db_connection_string: Optional[str],
    target_labels: Sequence[str],
    max_nodes: int,
    chunk_size: int = 50000,
    node_table: str = 'node_features',
    edge_table: str = 'transaction_edges'
) -> tuple:
    """
    从数据库加载并筛选原始数据。
    """
    if not db_connection_string:
        raise ValueError("缺少数据库连接字符串: data.raw_db")

    if max_nodes <= 0:
        raise ValueError("max_nodes 必须大于0")

    conn = connect_db(db_connection_string)
    sql_batch_size = max(1000, min(chunk_size, 20000))

    try:
        print("阶段1/5: 统计全图特征分布并收集 BRIDGE 节点...")
        mean, std, bridge_nodes = _compute_global_stats(
            conn=conn,
            chunk_size=chunk_size,
            node_table=node_table
        )

        print("阶段2/5: 计算 FinalScore 并筛选 TopK 节点...")
        topk_nodes = _select_topk_nodes(
            conn=conn,
            max_nodes=max_nodes,
            chunk_size=chunk_size,
            node_table=node_table,
            mean=mean,
            std=std
        )

        print("阶段3/5: 执行 BRIDGE 邻居增强...")
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

        print("阶段4/5: 读取选中节点特征与标签...")
        selected_df = load_nodes_by_aliases(
            conn=conn,
            node_ids=list(selected_nodes),
            table_name=node_table,
            chunk_size=chunk_size,
            insert_batch_size=sql_batch_size
        )
        if selected_df.empty:
            raise ValueError("未读取到选中节点特征，请检查节点表和字段")

        selected_df = _clean_node_chunk(selected_df)
        selected_df = selected_df.drop_duplicates(subset='alias', keep='first').reset_index(drop=True)

        normalized_df = z_score_normalize(
            selected_df[FEATURE_COLUMNS],
            feature_columns=FEATURE_COLUMNS,
            mean=mean,
            std=std
        )
        x = torch.tensor(normalized_df[FEATURE_COLUMNS].to_numpy(dtype=np.float32), dtype=torch.float32)
        y = _encode_labels(selected_df['label'], target_labels)

        node_aliases = selected_df['alias'].astype(str).tolist()
        node_to_index = {alias: idx for idx, alias in enumerate(node_aliases)}

        print("阶段5/5: 读取选中子图边并构建 edge_index...")
        edge_pairs = load_edges_filtered(
            conn=conn,
            selected_nodes=node_aliases,
            table_name=edge_table,
            chunk_size=chunk_size,
            insert_batch_size=sql_batch_size
        )
        edge_index = _build_edge_index(edge_pairs, node_to_index)

        return x, edge_index, y
    finally:
        conn.close()


def load_data(data_path: str) -> Data:
    """
    加载已处理的data.pt文件（兼容字典和Data两种格式）。
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

    return Data(
        x=x,
        edge_index=edge_index,
        y=y,
        train_mask=train_mask,
        val_mask=val_mask,
        test_mask=test_mask
    )
