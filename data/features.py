"""
特征工程模块：Z-score标准化、评分计算、缺失值处理等
"""

from __future__ import annotations

from typing import Dict, Optional, Sequence

import numpy as np
import pandas as pd
import torch

# 模型输入统一使用这4个特征名
FEATURE_COLUMNS = ['degree', 'total_in', 'total_out', 'cluster_size']

# 数据库原始列到统一列名的映射
DB_TO_MODEL_COLUMNS = {
    'total_transactions_in': 'total_in',
    'total_transactions_out': 'total_out'
}

# FinalScore 权重（用户已确认采用加权求和）
SCORE_WEIGHTS = {
    'degree': 0.3,
    'total_in': 0.2,
    'total_out': 0.2,
    'cluster_size': 0.3
}


def ensure_feature_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    将DataFrame特征列规范化为统一命名。
    """
    normalized_df = df.copy()

    for source_col, target_col in DB_TO_MODEL_COLUMNS.items():
        if target_col not in normalized_df.columns and source_col in normalized_df.columns:
            normalized_df[target_col] = normalized_df[source_col]

    missing_cols = [col for col in FEATURE_COLUMNS if col not in normalized_df.columns]
    if missing_cols:
        raise KeyError(f"缺少特征列: {missing_cols}")

    numeric_frame = normalized_df[FEATURE_COLUMNS].apply(pd.to_numeric, errors='coerce')
    numeric_frame = numeric_frame.replace([np.inf, -np.inf], np.nan).fillna(0.0)
    normalized_df.loc[:, FEATURE_COLUMNS] = numeric_frame
    return normalized_df


def z_score_normalize(
    df: pd.DataFrame,
    feature_columns: Optional[Sequence[str]] = None,
    mean: Optional[pd.Series] = None,
    std: Optional[pd.Series] = None
) -> pd.DataFrame:
    """
    对DataFrame执行Z-score标准化（文档要求接口）。

    Args:
        df: 输入DataFrame
        feature_columns: 参与标准化的列
        mean: 可选外部均值（用于全图统计后复用）
        std: 可选外部标准差（用于全图统计后复用）

    Returns:
        标准化后的DataFrame（仅目标列被替换）
    """
    normalized_df = ensure_feature_columns(df)
    columns = list(feature_columns) if feature_columns else FEATURE_COLUMNS

    if mean is None:
        mean_series = normalized_df[columns].mean(axis=0)
    else:
        mean_series = pd.Series(mean, index=columns, dtype=np.float64)

    if std is None:
        std_series = normalized_df[columns].std(axis=0, ddof=0)
    else:
        std_series = pd.Series(std, index=columns, dtype=np.float64)

    std_series = std_series.replace(0, 1.0)
    # 先转为 float，避免 dtype 警告
    normalized_df[columns] = normalized_df[columns].astype(float)
    normalized_df.loc[:, columns] = (normalized_df[columns] - mean_series) / std_series
    normalized_df.loc[:, columns] = normalized_df[columns].replace([np.inf, -np.inf], np.nan).fillna(0.0)

    return normalized_df


def compute_score(
    df: pd.DataFrame,
    feature_columns: Optional[Sequence[str]] = None,
    weights: Optional[Dict[str, float]] = None,
    normalized: bool = False,
    mean: Optional[pd.Series] = None,
    std: Optional[pd.Series] = None
) -> pd.Series:
    """
    计算节点重要性分数 FinalScore（文档要求接口）。

    FinalScore = 0.3*Z(degree) + 0.2*Z(total_in) + 0.2*Z(total_out) + 0.3*Z(cluster_size)
    """
    columns = list(feature_columns) if feature_columns else FEATURE_COLUMNS
    if normalized:
        score_df = ensure_feature_columns(df)
    else:
        score_df = z_score_normalize(df, feature_columns=columns, mean=mean, std=std)

    weight_map = dict(SCORE_WEIGHTS)
    if weights:
        weight_map.update(weights)

    missing_weight_cols = [col for col in columns if col not in weight_map]
    if missing_weight_cols:
        raise KeyError(f"缺少评分权重: {missing_weight_cols}")

    score = np.zeros(len(score_df), dtype=np.float64)
    for col in columns:
        score += weight_map[col] * score_df[col].to_numpy(dtype=np.float64)

    return pd.Series(score, index=score_df.index, name='final_score')


def zscore_normalize(
    features: np.ndarray,
    c: Optional[float] = 6,
    alpha: float = 0.3,
    beta: float = 0.2,
    gamma: float = 0.2,
    theta: float = 0.3
) -> np.ndarray:
    """
    历史接口：对numpy数组做Z-score标准化（保留旧签名）。

    alpha/beta/gamma/theta 参数为兼容保留位，不参与该函数计算。
    """
    _ = (alpha, beta, gamma, theta)
    features = np.asarray(features, dtype=np.float32)
    mean = np.mean(features, axis=0)
    std = np.std(features, axis=0)
    std[std == 0] = 1.0

    z_scores = (features - mean) / std
    if c is not None:
        clip_range = abs(float(c))
        z_scores = np.clip(z_scores, -clip_range, clip_range)
    return z_scores


def normalize_features(
    features: torch.FloatTensor,
    params: Optional[Dict] = None
) -> torch.FloatTensor:
    """
    历史接口：对张量做标准化。
    """
    if params is None:
        params = {}

    features_np = features.detach().cpu().numpy()
    normalized = zscore_normalize(features_np, **params)
    return torch.FloatTensor(normalized)


def handle_missing_values(
    features: torch.FloatTensor,
    strategy: str = 'mean'
) -> torch.FloatTensor:
    """
    处理缺失值。
    """
    features_np = features.detach().cpu().numpy().copy()
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
    else:
        raise ValueError(f"不支持的缺失值策略: {strategy}")

    return torch.FloatTensor(features_np)


def compute_feature_statistics(features: torch.FloatTensor) -> Dict:
    """
    计算特征统计信息
    """
    features_np = features.detach().cpu().numpy()

    return {
        'mean': np.mean(features_np, axis=0),
        'std': np.std(features_np, axis=0),
        'min': np.min(features_np, axis=0),
        'max': np.max(features_np, axis=0),
        'num_features': features_np.shape[1],
        'num_samples': features_np.shape[0]
    }
