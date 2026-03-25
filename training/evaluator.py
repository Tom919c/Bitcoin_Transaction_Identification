"""
评估函数
"""

import torch
import numpy as np
from typing import Dict, List, Optional
from sklearn.metrics import f1_score, accuracy_score, precision_score, recall_score


def compute_metrics(
    out: torch.Tensor,
    y: torch.Tensor,
    mask: torch.BoolTensor,
    num_classes: int = 6,
    label_indices: Optional[List[int]] = None,
    label_names: Optional[List[str]] = None
) -> Dict:
    """
    计算评估指标

    Args:
        out: logits, shape [N, num_classes]
        y: 标签, shape [N]
        mask: bool mask, shape [N]
        num_classes: 类别数量
        label_indices: 计算per-class与macro/weighted时使用的标签索引
        label_names: 与label_indices对应的标签名称

    Returns:
        字典，包含 accuracy, macro_f1, 各类别f1等
    """
    # 获取预测结果
    pred = out[mask].argmax(dim=1).cpu().numpy()
    true = y[mask].cpu().numpy()

    if label_indices is None:
        metric_label_indices = list(range(num_classes))
    else:
        metric_label_indices = [int(i) for i in label_indices]

    # 计算指标
    accuracy = accuracy_score(true, pred)
    macro_f1 = f1_score(true, pred, average='macro', labels=metric_label_indices, zero_division=0)
    micro_f1 = f1_score(true, pred, average='micro', labels=metric_label_indices, zero_division=0)
    weighted_f1 = f1_score(true, pred, average='weighted', labels=metric_label_indices, zero_division=0)

    # 各类别F1
    per_class_f1 = f1_score(true, pred, average=None, labels=metric_label_indices, zero_division=0)
    per_class_precision = precision_score(true, pred, average=None, labels=metric_label_indices, zero_division=0)
    per_class_recall = recall_score(true, pred, average=None, labels=metric_label_indices, zero_division=0)

    if label_names is None:
        metric_label_names = [f'class_{i}' for i in metric_label_indices]
    else:
        metric_label_names = label_names

    return {
        'accuracy': accuracy,
        'macro_f1': macro_f1,
        'micro_f1': micro_f1,
        'weighted_f1': weighted_f1,
        'metric_label_indices': metric_label_indices,
        'metric_label_names': metric_label_names,
        'per_class_f1': per_class_f1.tolist(),
        'per_class_precision': per_class_precision.tolist(),
        'per_class_recall': per_class_recall.tolist()
    }


def print_metrics(metrics: Dict, label_names: list = None):
    """
    打印评估指标

    Args:
        metrics: 指标字典
        label_names: 标签名称列表
    """
    if label_names is None:
        label_names = metrics.get('metric_label_names', ['NONE', 'INDIVIDUAL', 'BET', 'GAMBLING', 'EXCHANGE', 'BRIDGE'])

    print(f"评估类别顺序: {', '.join(label_names)}")

    print(f"Accuracy: {metrics['accuracy']:.4f}")
    print(f"Macro F1: {metrics['macro_f1']:.4f}")
    print(f"Micro F1: {metrics['micro_f1']:.4f}")
    print(f"Weighted F1: {metrics['weighted_f1']:.4f}")
    print("\n各类别指标:")
    print(f"{'类别':<12} {'F1':<10} {'Precision':<10} {'Recall':<10}")
    print("-" * 42)

    for i, name in enumerate(label_names):
        if i < len(metrics['per_class_f1']):
            print(f"{name:<12} {metrics['per_class_f1'][i]:<10.4f} "
                  f"{metrics['per_class_precision'][i]:<10.4f} "
                  f"{metrics['per_class_recall'][i]:<10.4f}")
