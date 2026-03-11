"""
特征工程模块：Z-score标准化、缺失值处理等
"""

import numpy as np
import torch
from typing import Dict, Optional, Tuple


def zscore_normalize(
    features: np.ndarray,
    c: float = 6,
    alpha: float = 0.3,
    beta: float = 0.2,
    gamma: float = 0.2,
    theta: float = 0.3
) -> np.ndarray:
    """
    Z-score标准化（论文公式11-13）

    Args:
        features: 原始特征矩阵 [N, F]
        c: 截断参数
        alpha, beta, gamma, theta: 权重参数

    Returns:
        标准化后的特征矩阵
    """
    mean = np.mean(features, axis=0)
    std = np.std(features, axis=0)
    std[std == 0] = 1  # 避免除零

    # Z-score标准化
    z_scores = (features - mean) / std

    # 截断到[-c, c]范围
    z_scores = np.clip(z_scores, -c, c)

    return z_scores


def normalize_features(
    features: torch.FloatTensor,
    params: Optional[Dict] = None
) -> torch.FloatTensor:
    """
    特征标准化

    Args:
        features: 特征张量 [N, F]
        params: Z-score参数字典

    Returns:
        标准化后的特征张量
    """
    if params is None:
        params = {}

    features_np = features.numpy()
    normalized = zscore_normalize(features_np, **params)

    return torch.FloatTensor(normalized)


def handle_missing_values(
    features: torch.FloatTensor,
    strategy: str = 'mean'
) -> torch.FloatTensor:
    """
    处理缺失值

    Args:
        features: 特征张量 [N, F]
        strategy: 填充策略 ('mean', 'median', 'zero')

    Returns:
        处理后的特征张量
    """
    features_np = features.numpy()

    # 检测NaN和Inf
    mask = np.isnan(features_np) | np.isinf(features_np)

    if not mask.any():
        return features

    if strategy == 'mean':
        col_means = np.nanmean(features_np, axis=0)
        for i in range(features_np.shape[1]):
            features_np[mask[:, i], i] = col_means[i]
    elif strategy == 'median':
        col_medians = np.nanmedian(features_np, axis=0)
        for i in range(features_np.shape[1]):
            features_np[mask[:, i], i] = col_medians[i]
    elif strategy == 'zero':
        features_np[mask] = 0

    return torch.FloatTensor(features_np)


def compute_feature_statistics(features: torch.FloatTensor) -> Dict:
    """
    计算特征统计信息

    Args:
        features: 特征张量 [N, F]

    Returns:
        统计信息字典
    """
    features_np = features.numpy()

    return {
        'mean': np.mean(features_np, axis=0),
        'std': np.std(features_np, axis=0),
        'min': np.min(features_np, axis=0),
        'max': np.max(features_np, axis=0),
        'num_features': features_np.shape[1],
        'num_samples': features_np.shape[0]
    }
