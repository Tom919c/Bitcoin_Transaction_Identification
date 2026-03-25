"""
数据库连接、节点筛选等工具函数
"""

import numpy as np
import torch
from typing import Dict, List, Tuple, Optional
from sklearn.model_selection import train_test_split

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


def get_db_connection(connection_string: str):
    """
    获取数据库连接

    Args:
        connection_string: 数据库连接字符串

    Returns:
        数据库连接对象
    """
    try:
        import psycopg2
        conn = psycopg2.connect(connection_string)
        return conn
    except Exception as e:
        raise ConnectionError(f"无法连接数据库: {e}")


def filter_nodes(
    node_ids: np.ndarray,
    labels: np.ndarray,
    target_labels: List[str],
    max_nodes: int
) -> Tuple[np.ndarray, np.ndarray]:
    """
    筛选节点，保留目标标签的节点

    Args:
        node_ids: 节点ID数组
        labels: 节点标签数组
        target_labels: 目标标签列表
        max_nodes: 最大节点数量

    Returns:
        筛选后的节点ID和标签
    """
    target_label_ids = [LABEL_MAP[label] for label in target_labels]
    mask = np.isin(labels, target_label_ids)

    filtered_ids = node_ids[mask]
    filtered_labels = labels[mask]

    if len(filtered_ids) > max_nodes:
        indices = np.random.choice(len(filtered_ids), max_nodes, replace=False)
        filtered_ids = filtered_ids[indices]
        filtered_labels = filtered_labels[indices]

    return filtered_ids, filtered_labels


def create_masks(
    num_nodes: int,
    labels: Optional[torch.LongTensor] = None,
    train_ratio: float = 0.6,
    val_ratio: float = 0.2,
    seed: int = 42,
    stratified: bool = True
) -> Tuple[torch.BoolTensor, torch.BoolTensor, torch.BoolTensor]:
    """
    创建训练/验证/测试集掩码

    Args:
        num_nodes: 节点数量
        labels: 节点标签，用于分层划分
        train_ratio: 训练集比例
        val_ratio: 验证集比例
        seed: 随机种子
        stratified: 是否启用分层划分

    Returns:
        train_mask, val_mask, test_mask
    """
    np.random.seed(seed)

    if labels is not None and stratified:
        label_array = labels.cpu().numpy() if torch.is_tensor(labels) else np.asarray(labels)
        indices = np.arange(num_nodes)

        try:
            train_idx, temp_idx, _, temp_y = train_test_split(
                indices,
                label_array,
                train_size=train_ratio,
                random_state=seed,
                stratify=label_array
            )

            remain_ratio = 1.0 - train_ratio
            val_ratio_in_remain = val_ratio / remain_ratio
            unique_temp_labels = np.unique(temp_y)
            temp_stratify = temp_y if len(unique_temp_labels) > 1 else None

            val_idx, test_idx = train_test_split(
                temp_idx,
                train_size=val_ratio_in_remain,
                random_state=seed,
                stratify=temp_stratify
            )
        except ValueError as exc:
            print(f"警告: 分层划分失败，回退到随机划分，原因: {exc}")
            stratified = False

    if labels is None or not stratified:
        indices = np.random.permutation(num_nodes)

        train_size = int(num_nodes * train_ratio)
        val_size = int(num_nodes * val_ratio)

        train_idx = indices[:train_size]
        val_idx = indices[train_size:train_size + val_size]
        test_idx = indices[train_size + val_size:]

    train_mask = torch.zeros(num_nodes, dtype=torch.bool)
    val_mask = torch.zeros(num_nodes, dtype=torch.bool)
    test_mask = torch.zeros(num_nodes, dtype=torch.bool)

    train_mask[torch.from_numpy(train_idx)] = True
    val_mask[torch.from_numpy(val_idx)] = True
    test_mask[torch.from_numpy(test_idx)] = True

    return train_mask, val_mask, test_mask


def encode_labels(labels: List[str]) -> torch.LongTensor:
    """
    将字符串标签编码为整数

    Args:
        labels: 字符串标签列表

    Returns:
        整数编码的标签张量
    """
    encoded = [LABEL_MAP.get(label, 0) for label in labels]
    return torch.LongTensor(encoded)


def decode_labels(encoded: torch.LongTensor) -> List[str]:
    """
    将整数标签解码为字符串

    Args:
        encoded: 整数编码的标签张量

    Returns:
        字符串标签列表
    """
    return [LABEL_MAP_INV.get(int(e), 'NONE') for e in encoded]
