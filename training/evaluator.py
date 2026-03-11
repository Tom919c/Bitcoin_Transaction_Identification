"""
评估函数
"""

import torch
import numpy as np
from typing import Dict
from sklearn.metrics import f1_score, accuracy_score, precision_score, recall_score


def compute_metrics(
    out: torch.Tensor,
    y: torch.Tensor,
    mask: torch.BoolTensor,
    num_classes: int = 6
) -> Dict:
    """
    计算评估指标

    Args:
        out: logits, shape [N, num_classes]
        y: 标签, shape [N]
        mask: bool mask, shape [N]
        num_classes: 类别数量

    Returns:
        字典，包含 accuracy, macro_f1, 各类别f1等
    """
    # 获取预测结果
    pred = out[mask].argmax(dim=1).cpu().numpy()
    true = y[mask].cpu().numpy()

    # 计算指标
    accuracy = accuracy_score(true, pred)
    macro_f1 = f1_score(true, pred, average='macro', zero_division=0)
    micro_f1 = f1_score(true, pred, average='micro', zero_division=0)
    weighted_f1 = f1_score(true, pred, average='weighted', zero_division=0)

    # 各类别F1
    per_class_f1 = f1_score(true, pred, average=None, labels=range(num_classes), zero_division=0)
    per_class_precision = precision_score(true, pred, average=None, labels=range(num_classes), zero_division=0)
    per_class_recall = recall_score(true, pred, average=None, labels=range(num_classes), zero_division=0)

    return {
        'accuracy': accuracy,
        'macro_f1': macro_f1,
        'micro_f1': micro_f1,
        'weighted_f1': weighted_f1,
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
        label_names = ['NONE', 'INDIVIDUAL', 'BET', 'GAMBLING', 'EXCHANGE', 'BRIDGE']

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
