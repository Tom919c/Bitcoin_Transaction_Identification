"""
APPNP模型
"""

import itertools
from typing import Dict, List

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.nn import APPNP as APPNPConv

from data.utils import LABEL_MAP, LABEL_MAP_INV, create_masks
from training.evaluator import compute_metrics
from .base import BaseModel


class APPNP(BaseModel):
    """
    APPNP模型 (Approximate Personalized Propagation of Neural Predictions)
    """

    def __init__(
        self,
        in_channels: int,
        hidden_channels: int,
        out_channels: int,
        num_layers: int = 2,
        dropout: float = 0.5,
        K: int = 10,
        alpha: float = 0.1
    ):
        super().__init__(in_channels, hidden_channels, out_channels)
        self.num_layers = num_layers
        self.dropout = dropout

        # MLP部分
        self.lins = nn.ModuleList()
        self.lins.append(nn.Linear(in_channels, hidden_channels))
        for _ in range(num_layers - 2):
            self.lins.append(nn.Linear(hidden_channels, hidden_channels))
        self.lins.append(nn.Linear(hidden_channels, out_channels))

        # APPNP传播层
        self.prop = APPNPConv(K=K, alpha=alpha)

        self.reset_parameters()

    def reset_parameters(self):
        for lin in self.lins:
            lin.reset_parameters()
        if hasattr(self.prop, 'reset_parameters'):
            self.prop.reset_parameters()

    def forward(self, x: torch.Tensor, edge_index: torch.Tensor) -> torch.Tensor:
        # MLP变换
        for i, lin in enumerate(self.lins[:-1]):
            x = lin(x)
            x = F.relu(x)
            x = F.dropout(x, p=self.dropout, training=self.training)

        x = self.lins[-1](x)

        # APPNP传播
        x = self.prop(x, edge_index)
        return x


def class_counts(y: torch.Tensor, mask: torch.BoolTensor, num_classes: int) -> torch.Tensor:
    if mask is None:
        return torch.zeros(num_classes, dtype=torch.long)
    return torch.bincount(y[mask], minlength=num_classes)


def print_split_stats(data, eval_label_indices: List[int], eval_label_names: List[str], num_classes: int):
    print("\n数据划分统计:")
    for split_name in ['train_mask', 'val_mask', 'test_mask']:
        split_mask = getattr(data, split_name, None)
        if split_mask is None:
            print(f"{split_name}: MISSING")
            continue
        split_counts = class_counts(data.y, split_mask.bool(), num_classes)
        tracked = [int(split_counts[idx]) for idx in eval_label_indices]
        tracked_str = ", ".join(f"{name}:{count}" for name, count in zip(eval_label_names, tracked))
        print(f"{split_name}: size={int(split_mask.sum())}, {tracked_str}")


def maybe_rebuild_masks(data, config: Dict, eval_label_indices: List[int], eval_label_names: List[str]):
    train_config = config.get('train', {})
    auto_rebuild = bool(train_config.get('auto_rebuild_masks_on_load', True))
    force_rebuild = bool(train_config.get('force_rebuild_masks_on_load', False))
    min_train_samples = int(train_config.get('min_train_samples_per_class', 80))
    mask_train_ratio = float(train_config.get('mask_train_ratio', 0.75))
    mask_val_ratio = float(train_config.get('mask_val_ratio', 0.1))
    seed = int(train_config.get('seed', 42))
    num_classes = int(config.get('data', {}).get('num_classes', 6))

    has_masks = all(hasattr(data, k) for k in ['train_mask', 'val_mask', 'test_mask'])
    if not has_masks:
        force_rebuild = True

    if has_masks and not force_rebuild:
        train_counts = class_counts(data.y, data.train_mask.bool(), num_classes)
        low_classes = [
            (label_name, int(train_counts[label_idx]))
            for label_name, label_idx in zip(eval_label_names, eval_label_indices)
            if int(train_counts[label_idx]) < min_train_samples
        ]
        if not low_classes:
            return data

        if not auto_rebuild:
            print("检测到训练集少数类样本偏少，但 auto_rebuild_masks_on_load=false，跳过重建")
            for name, count in low_classes:
                print(f"  - {name}: train={count} < {min_train_samples}")
            return data

        print("检测到训练集少数类样本偏少，将自动重建分层掩码:")
        for name, count in low_classes:
            print(f"  - {name}: train={count} < {min_train_samples}")
    elif not auto_rebuild and not force_rebuild:
        return data

    candidate_mask = torch.zeros_like(data.y, dtype=torch.bool)
    for label_idx in eval_label_indices:
        candidate_mask |= (data.y == int(label_idx))

    candidate_indices = torch.where(candidate_mask)[0]
    if candidate_indices.numel() == 0:
        print("警告: 未找到可用于重建掩码的目标类别样本，保留原掩码")
        return data

    subset_labels = data.y[candidate_indices]
    train_sub, val_sub, test_sub = create_masks(
        num_nodes=int(candidate_indices.numel()),
        labels=subset_labels,
        train_ratio=mask_train_ratio,
        val_ratio=mask_val_ratio,
        seed=seed,
        stratified=True
    )

    train_mask = torch.zeros(data.num_nodes, dtype=torch.bool)
    val_mask = torch.zeros(data.num_nodes, dtype=torch.bool)
    test_mask = torch.zeros(data.num_nodes, dtype=torch.bool)

    train_mask[candidate_indices[train_sub]] = True
    val_mask[candidate_indices[val_sub]] = True
    test_mask[candidate_indices[test_sub]] = True

    data.train_mask = train_mask
    data.val_mask = val_mask
    data.test_mask = test_mask

    print(
        f"已重建掩码: train_ratio={mask_train_ratio}, val_ratio={mask_val_ratio}, "
        f"test_ratio={1.0 - mask_train_ratio - mask_val_ratio:.2f}"
    )
    return data


def apply_logit_bias(logits: torch.Tensor, bias_by_class_idx: Dict[int, float]) -> torch.Tensor:
    if not bias_by_class_idx:
        return logits

    biased = logits.clone()
    for class_idx, bias in bias_by_class_idx.items():
        biased[:, int(class_idx)] = biased[:, int(class_idx)] + float(bias)
    return biased


@torch.no_grad()
def tune_minority_logit_bias(trainer, data, config: Dict, eval_label_indices: List[int], eval_label_names: List[str]) -> Dict[int, float]:
    tune_cfg = config.get('eval', {}).get('minority_bias_tuning', {})
    if not bool(tune_cfg.get('enabled', False)):
        return {}

    target_labels = tune_cfg.get('target_labels', ['BET', 'GAMBLING'])
    candidate_values = [float(v) for v in tune_cfg.get('candidate_values', [-0.8, -0.6, -0.4, -0.2, 0.0])]
    objective = str(tune_cfg.get('objective', 'minority_hmean_f1')).lower()

    target_items = []
    for label_name in target_labels:
        if label_name in LABEL_MAP:
            target_items.append((label_name, LABEL_MAP[label_name]))

    if not target_items:
        print("minority_bias_tuning 已开启，但 target_labels 均无效，跳过")
        return {}

    trainer.model.eval()
    out = trainer.model(data.x, data.edge_index)
    val_mask = data.val_mask.bool()

    best_score = -1.0
    best_bias = {}
    best_metrics = None

    grid_size = len(candidate_values) ** len(target_items)
    print(f"\n开始验证集偏置搜索: 目标={','.join([n for n, _ in target_items])}, 组合数={grid_size}")

    for combo in itertools.product(candidate_values, repeat=len(target_items)):
        bias_map = {class_idx: bias for (_, class_idx), bias in zip(target_items, combo)}
        out_biased = apply_logit_bias(out, bias_map)
        metrics = compute_metrics(
            out_biased,
            data.y,
            val_mask,
            num_classes=int(config.get('data', {}).get('num_classes', 6)),
            label_indices=eval_label_indices,
            label_names=eval_label_names
        )

        if objective == 'macro_f1':
            score = float(metrics['macro_f1'])
        else:
            per_class = metrics['per_class_f1']
            idx_map = {name: i for i, name in enumerate(eval_label_names)}
            selected_scores = []
            for label_name, _ in target_items:
                if label_name in idx_map:
                    selected_scores.append(float(per_class[idx_map[label_name]]))

            if not selected_scores:
                score = float(metrics['macro_f1'])
            elif objective == 'minority_min_f1':
                score = float(min(selected_scores))
            elif objective == 'minority_hmean_f1':
                eps = 1e-12
                inv_sum = sum(1.0 / max(v, eps) for v in selected_scores)
                score = float(len(selected_scores) / inv_sum)
            else:
                score = float(sum(selected_scores) / len(selected_scores))

        if score > best_score:
            best_score = score
            best_bias = bias_map
            best_metrics = metrics

    if best_metrics is None:
        return {}

    readable = {LABEL_MAP_INV.get(k, str(k)): round(v, 4) for k, v in best_bias.items()}
    print(f"偏置搜索完成: objective={objective}, best_score={best_score:.4f}, best_bias={readable}")
    print("验证集(应用最佳偏置)各类别F1:")
    for name, f1 in zip(eval_label_names, best_metrics['per_class_f1']):
        print(f"  - {name}: {float(f1):.4f}")

    return best_bias
