"""
从数据库构建子图，生成data.pt
"""

import os
import torch
import numpy as np
from typing import Dict, Optional
from torch_geometric.data import Data

from .utils import (
    get_db_connection,
    filter_nodes,
    create_masks,
    LABEL_MAP
)
from .features import normalize_features, handle_missing_values


def build_and_save_data(output_path: str, config: Dict) -> Data:
    """
    从数据库读取原始数据，执行节点筛选、特征工程、掩码划分，保存data.pt

    Args:
        output_path: 输出文件路径
        config: 配置字典，包含数据库连接、预处理参数等

    Returns:
        PyG Data对象
    """
    # 确保输出目录存在
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # 从配置获取参数
    db_config = config.get('data', {})
    preprocess_config = config.get('preprocessing', {})

    # 加载原始数据（这里需要根据实际数据库结构实现）
    x, edge_index, y = load_raw_data(
        db_connection_string=db_config.get('raw_db'),
        target_labels=preprocess_config.get('target_labels', []),
        max_nodes=preprocess_config.get('max_nodes', 350000)
    )

    # 特征工程
    zscore_params = preprocess_config.get('zscore_params', {})
    x = handle_missing_values(x)
    x = normalize_features(x, zscore_params)

    # 创建掩码
    train_mask, val_mask, test_mask = create_masks(
        num_nodes=x.shape[0],
        labels=y,
        seed=config.get('train', {}).get('seed', 42),
        stratified=True
    )

    # 构建PyG Data对象
    data = Data(
        x=x,
        edge_index=edge_index,
        y=y,
        train_mask=train_mask,
        val_mask=val_mask,
        test_mask=test_mask
    )

    # 保存
    torch.save(data, output_path)
    print(f"数据已保存到: {output_path}")
    print(f"节点数: {data.num_nodes}, 边数: {data.num_edges}, 特征维度: {data.num_features}")

    for split_name, split_mask in [
        ('train', train_mask),
        ('val', val_mask),
        ('test', test_mask)
    ]:
        split_labels = y[split_mask]
        split_counts = torch.bincount(split_labels, minlength=len(LABEL_MAP)).tolist()
        print(f"{split_name}类别计数: {split_counts}")

    return data


def load_raw_data(
    db_connection_string: Optional[str],
    target_labels: list,
    max_nodes: int
) -> tuple:
    """
    从数据库加载原始数据

    Args:
        db_connection_string: 数据库连接字符串
        target_labels: 目标标签列表
        max_nodes: 最大节点数

    Returns:
        x: 特征张量
        edge_index: 边索引
        y: 标签张量
    """
    # TODO: 根据实际数据库结构实现数据加载
    # 以下为示例代码，需要根据实际情况修改

    if db_connection_string:
        conn = get_db_connection(db_connection_string)
        # 执行SQL查询获取节点特征、边、标签
        # cursor = conn.cursor()
        # cursor.execute("SELECT ...")
        # ...
        conn.close()

    # 占位符：返回空数据结构
    raise NotImplementedError(
        "请根据实际数据库结构实现load_raw_data函数。"
        "需要返回: x (FloatTensor [N,F]), edge_index (LongTensor [2,E]), y (LongTensor [N])"
    )


def load_data(data_path: str) -> Data:
    """
    加载已处理的data.pt文件

    Args:
        data_path: data.pt文件路径

    Returns:
        PyG Data对象
    """
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"数据文件不存在: {data_path}")

    data = torch.load(data_path, map_location='cpu')
    if isinstance(data, dict):
        data = Data(**data)
    if not isinstance(data, Data):
        raise TypeError(f"不支持的数据格式: {type(data)}，期望 PyG Data 或可转换的 dict")
    return data
