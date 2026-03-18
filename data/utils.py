"""
数据库连接、节点筛选等工具函数
"""

from __future__ import annotations

import uuid
from typing import Iterator, List, Sequence, Set, Tuple

import numpy as np
import pandas as pd
import torch

# 标签映射
LABEL_MAP = {
    'NONE': 0,
    'INDIVIDUAL': 1,
    'BET': 2,
    'GAMBLING': 3,
    'EXCHANGE': 4,
    'BRIDGE': 5
}

LABEL_MAP_INV = {v: k for k, v in LABEL_MAP.items()}


def _chunked(items: Sequence[str], chunk_size: int) -> Iterator[List[str]]:
    """按固定大小切分列表。"""
    if chunk_size <= 0:
        raise ValueError("chunk_size 必须大于0")

    for start in range(0, len(items), chunk_size):
        yield list(items[start:start + chunk_size])


def connect_db(connection_string: str):
    """
    获取数据库连接（文档接口）。

    Args:
        connection_string: 数据库连接字符串

    Returns:
        数据库连接对象
    """
    try:
        import psycopg2
        return psycopg2.connect(connection_string)
    except Exception as exc:
        raise ConnectionError(f"无法连接数据库: {exc}") from exc


def get_db_connection(connection_string: str):
    """
    获取数据库连接（历史接口，保持兼容）。
    """
    return connect_db(connection_string)


def load_nodes_in_chunks(
    conn,
    chunk_size: int = 100000,
    table_name: str = 'node_features'
) -> Iterator[pd.DataFrame]:
    """
    分批读取节点特征数据。

    Args:
        conn: PostgreSQL连接
        chunk_size: 每批读取行数
        table_name: 节点表名

    Yields:
        DataFrame，包含 alias、特征列、label
    """
    from psycopg2 import sql

    query = sql.SQL("""
        SELECT
            alias::text AS alias,
            degree,
            total_transactions_in,
            total_transactions_out,
            cluster_size,
            label
        FROM {table}
    """).format(table=sql.Identifier(table_name))

    cursor_name = f"node_features_cursor_{uuid.uuid4().hex[:8]}"
    cursor = conn.cursor(name=cursor_name)
    cursor.itersize = chunk_size

    try:
        cursor.execute(query)
        print(cursor.statusmessage)
        first_batch = cursor.fetchmany(chunk_size)
        if not first_batch:
            return
        columns = [desc[0] for desc in cursor.description]
        yield pd.DataFrame(first_batch, columns=columns)

        while True:
            rows = cursor.fetchmany(chunk_size)
            if not rows:
                break
            yield pd.DataFrame(rows, columns=columns)
    finally:
        cursor.close()


def _materialize_aliases(
    conn,
    aliases: Sequence[str],
    temp_table: str,
    insert_batch_size: int
) -> None:
    """将节点集合写入临时表，便于SQL层做JOIN过滤。"""
    from psycopg2 import sql
    from psycopg2.extras import execute_values

    cursor = conn.cursor()
    try:
        cursor.execute(sql.SQL("DROP TABLE IF EXISTS {table}").format(
            table=sql.Identifier(temp_table)
        ))
        cursor.execute(sql.SQL("""
            CREATE TEMP TABLE {table} (
                alias TEXT PRIMARY KEY
            ) ON COMMIT DROP
        """).format(table=sql.Identifier(temp_table)))

        insert_sql = sql.SQL(
            "INSERT INTO {table} (alias) VALUES %s ON CONFLICT DO NOTHING"
        ).format(table=sql.Identifier(temp_table)).as_string(conn)

        for batch in _chunked(list(aliases), insert_batch_size):
            execute_values(
                cursor,
                insert_sql,
                [(str(alias),) for alias in batch],
                page_size=insert_batch_size
            )
    finally:
        cursor.close()


def get_neighbors(
    conn,
    node_ids: Sequence[str],
    table_name: str = 'transaction_edges',
    batch_size: int = 10000
) -> Set[str]:
    """
    获取给定节点集合在边表中的一跳邻居。

    Args:
        conn: PostgreSQL连接
        node_ids: 节点ID列表
        table_name: 边表名
        batch_size: 分批查询大小

    Returns:
        邻居节点集合（字符串）
    """
    from psycopg2 import sql

    node_list = [str(node_id) for node_id in node_ids if node_id is not None]
    if not node_list:
        return set()

    query = sql.SQL("""
        SELECT DISTINCT e.a::text AS neighbor
        FROM {table} e
        WHERE e.b::text = ANY(%s)
        UNION
        SELECT DISTINCT e.b::text AS neighbor
        FROM {table} e
        WHERE e.a::text = ANY(%s)
    """).format(table=sql.Identifier(table_name))

    neighbors: Set[str] = set()
    cursor = conn.cursor()
    try:
        for batch in _chunked(node_list, batch_size):
            cursor.execute(query, (batch, batch))
            neighbors.update(
                str(row[0]) for row in cursor.fetchall() if row and row[0] is not None
            )
    finally:
        cursor.close()

    return neighbors


def load_edges_filtered(
    conn,
    selected_nodes: Sequence[str],
    table_name: str = 'transaction_edges',
    chunk_size: int = 50000,
    insert_batch_size: int = 10000,
    temp_table: str = 'tmp_selected_nodes'
) -> np.ndarray:
    """
    读取子图边，仅保留 source/target 都在 selected_nodes 中的边。

    Args:
        conn: PostgreSQL连接
        selected_nodes: 目标节点集合
        table_name: 边表名
        chunk_size: 流式拉取边的批大小
        insert_batch_size: 写临时表的批大小
        temp_table: 临时表名称

    Returns:
        边数组，形状 [E, 2]，每行 [source, target]
    """
    from psycopg2 import sql

    node_list = [str(node_id) for node_id in selected_nodes if node_id is not None]
    if not node_list:
        return np.empty((0, 2), dtype=object)

    _materialize_aliases(conn, node_list, temp_table=temp_table, insert_batch_size=insert_batch_size)

    query = sql.SQL("""
        SELECT
            e.a::text AS source,
            e.b::text AS target
        FROM {edge_table} e
        INNER JOIN {tmp_table} s1 ON e.a::text = s1.alias
        INNER JOIN {tmp_table} s2 ON e.b::text = s2.alias
    """).format(
        edge_table=sql.Identifier(table_name),
        tmp_table=sql.Identifier(temp_table)
    )

    cursor_name = f"edge_filtered_cursor_{uuid.uuid4().hex[:8]}"
    cursor = conn.cursor(name=cursor_name)
    cursor.itersize = chunk_size

    edges: List[Tuple[str, str]] = []
    try:
        cursor.execute(query)
        while True:
            rows = cursor.fetchmany(chunk_size)
            if not rows:
                break
            edges.extend((str(src), str(dst)) for src, dst in rows)
    finally:
        cursor.close()

    if not edges:
        return np.empty((0, 2), dtype=object)

    return np.asarray(edges, dtype=object)


def load_nodes_by_aliases(
    conn,
    node_ids: Sequence[str],
    table_name: str = 'node_features',
    chunk_size: int = 50000,
    insert_batch_size: int = 10000,
    temp_table: str = 'tmp_selected_nodes'
) -> pd.DataFrame:
    """
    按节点ID集合读取节点特征。

    Args:
        conn: PostgreSQL连接
        node_ids: 目标节点ID集合
        table_name: 节点表名
        chunk_size: 流式拉取节点的批大小
        insert_batch_size: 写临时表的批大小
        temp_table: 临时表名称

    Returns:
        节点特征DataFrame
    """
    from psycopg2 import sql

    node_list = [str(node_id) for node_id in node_ids if node_id is not None]
    columns = [
        'alias',
        'degree',
        'total_transactions_in',
        'total_transactions_out',
        'cluster_size',
        'label'
    ]
    if not node_list:
        return pd.DataFrame(columns=columns)

    _materialize_aliases(conn, node_list, temp_table=temp_table, insert_batch_size=insert_batch_size)

    query = sql.SQL("""
        SELECT
            n.alias::text AS alias,
            n.degree,
            n.total_transactions_in,
            n.total_transactions_out,
            n.cluster_size,
            n.label
        FROM {node_table} n
        INNER JOIN {tmp_table} s ON n.alias::text = s.alias
    """).format(
        node_table=sql.Identifier(table_name),
        tmp_table=sql.Identifier(temp_table)
    )

    cursor_name = f"selected_nodes_cursor_{uuid.uuid4().hex[:8]}"
    cursor = conn.cursor(name=cursor_name)
    cursor.itersize = chunk_size

    chunks: List[pd.DataFrame] = []
    try:
        cursor.execute(query)
        while True:
            rows = cursor.fetchmany(chunk_size)
            if not rows:
                break
            chunks.append(pd.DataFrame(rows, columns=columns))
    finally:
        cursor.close()

    if not chunks:
        return pd.DataFrame(columns=columns)

    return pd.concat(chunks, ignore_index=True)


def filter_nodes(
    node_ids: np.ndarray,
    labels: np.ndarray,
    target_labels: List[str],
    max_nodes: int
) -> Tuple[np.ndarray, np.ndarray]:
    """
    筛选节点（保留历史接口不变）。

    - 传入 target_labels 时按标签筛选；
    - 若筛选后超出 max_nodes，浮点标签视作分数做TopK，否则随机采样。
    """
    if max_nodes <= 0:
        raise ValueError("max_nodes 必须大于0")

    node_ids = np.asarray(node_ids)
    labels = np.asarray(labels)
    if node_ids.shape[0] != labels.shape[0]:
        raise ValueError("node_ids 和 labels 长度不一致")

    target_label_ids = [LABEL_MAP[label] for label in target_labels if label in LABEL_MAP]
    if target_label_ids:
        mask = np.isin(labels, target_label_ids)
        filtered_ids = node_ids[mask]
        filtered_labels = labels[mask]
    else:
        filtered_ids = node_ids
        filtered_labels = labels

    if len(filtered_ids) > max_nodes:
        if np.issubdtype(filtered_labels.dtype, np.floating):
            top_indices = np.argpartition(filtered_labels, -max_nodes)[-max_nodes:]
        else:
            top_indices = np.random.choice(len(filtered_ids), max_nodes, replace=False)
        filtered_ids = filtered_ids[top_indices]
        filtered_labels = filtered_labels[top_indices]

    return filtered_ids, filtered_labels


def create_masks(
    num_nodes: int,
    train_ratio: float = 0.6,
    val_ratio: float = 0.2,
    seed: int = 42
) -> Tuple[torch.BoolTensor, torch.BoolTensor, torch.BoolTensor]:
    """
    创建训练/验证/测试集掩码（历史接口）。
    """
    if num_nodes < 0:
        raise ValueError("num_nodes 不能小于0")
    if not (0 <= train_ratio <= 1 and 0 <= val_ratio <= 1 and train_ratio + val_ratio <= 1):
        raise ValueError("train_ratio/val_ratio 非法")

    np.random.seed(seed)
    indices = np.random.permutation(num_nodes)

    train_size = int(num_nodes * train_ratio)
    val_size = int(num_nodes * val_ratio)

    train_mask = torch.zeros(num_nodes, dtype=torch.bool)
    val_mask = torch.zeros(num_nodes, dtype=torch.bool)
    test_mask = torch.zeros(num_nodes, dtype=torch.bool)

    train_mask[indices[:train_size]] = True
    val_mask[indices[train_size:train_size + val_size]] = True
    test_mask[indices[train_size + val_size:]] = True

    return train_mask, val_mask, test_mask


def create_semi_supervised_masks(
    labels: torch.LongTensor,
    val_ratio: float = 0.2,
    test_ratio: float = 0.2,
    seed: int = 42
) -> Tuple[torch.BoolTensor, torch.BoolTensor, torch.BoolTensor]:
    """
    创建半监督场景掩码。

    规则：
    - train_mask = (y != 0)
    - val/test 从有标签节点中随机采样
    """
    num_nodes = labels.shape[0]
    train_mask = labels != 0
    val_mask = torch.zeros(num_nodes, dtype=torch.bool)
    test_mask = torch.zeros(num_nodes, dtype=torch.bool)

    labeled_indices = torch.where(train_mask)[0].cpu().numpy()
    labeled_count = labeled_indices.size
    if labeled_count == 0:
        return train_mask, val_mask, test_mask

    rng = np.random.default_rng(seed)
    rng.shuffle(labeled_indices)

    val_size = int(labeled_count * val_ratio)
    test_size = int(labeled_count * test_ratio)

    if labeled_count >= 3:
        val_size = max(1, val_size)
        test_size = max(1, test_size)
    if val_size + test_size > labeled_count:
        overflow = val_size + test_size - labeled_count
        test_size = max(0, test_size - overflow)

    val_indices = labeled_indices[:val_size]
    test_indices = labeled_indices[val_size:val_size + test_size]

    val_mask[val_indices] = True
    test_mask[test_indices] = True

    return train_mask, val_mask, test_mask


def encode_labels(labels: List[str]) -> torch.LongTensor:
    """
    将字符串标签编码为整数
    """
    encoded = [LABEL_MAP.get(label, 0) for label in labels]
    return torch.LongTensor(encoded)


def decode_labels(encoded: torch.LongTensor) -> List[str]:
    """
    将整数标签解码为字符串
    """
    return [LABEL_MAP_INV.get(int(e), 'NONE') for e in encoded]
