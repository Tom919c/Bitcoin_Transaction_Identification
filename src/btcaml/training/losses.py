from __future__ import annotations

import torch
import torch.nn as nn
import torch.nn.functional as F

from btcaml.data.label_maps import UNKNOWN_LABEL


class FocalLoss(nn.Module):
    def __init__(self, gamma: float = 2.0, weight: torch.Tensor | None = None, ignore_index: int = UNKNOWN_LABEL):
        super().__init__()
        self.gamma = gamma
        self.weight = weight
        self.ignore_index = ignore_index

    def forward(self, logits: torch.Tensor, target: torch.Tensor) -> torch.Tensor:
        ce = F.cross_entropy(logits, target, weight=self.weight, ignore_index=self.ignore_index, reduction='none')
        valid = target != self.ignore_index
        if valid.sum() == 0:
            return logits.sum() * 0
        pt = torch.exp(-ce[valid])
        return (((1 - pt) ** self.gamma) * ce[valid]).mean()


def compute_class_weights(y: torch.Tensor, train_mask: torch.Tensor, num_classes: int, power: float = 1.0, cap: float = 10.0, device=None) -> torch.Tensor:
    labels = y[train_mask & (y != UNKNOWN_LABEL)]
    counts = torch.bincount(labels.clamp_min(0), minlength=num_classes).float()
    weights = torch.zeros(num_classes, dtype=torch.float32)
    valid = counts > 0
    if valid.sum() == 0:
        return weights.to(device or y.device)
    mean_count = counts[valid].mean()
    weights[valid] = torch.pow(mean_count / counts[valid], power)
    if cap and cap > 0:
        weights[valid] = torch.clamp(weights[valid], max=cap)
    weights[valid] = weights[valid] / weights[valid].mean().clamp_min(1e-9)
    return weights.to(device or y.device)


def build_loss(name: str, y: torch.Tensor, train_mask: torch.Tensor, num_classes: int, cfg: dict, device=None):
    name = str(name or 'weighted_ce').lower()
    if name == 'cross_entropy':
        return nn.CrossEntropyLoss(ignore_index=UNKNOWN_LABEL)
    if name == 'weighted_ce':
        w = compute_class_weights(y, train_mask, num_classes, cfg.get('class_weight_power', 1.0), cfg.get('class_weight_cap', 10.0), device=device)
        return nn.CrossEntropyLoss(ignore_index=UNKNOWN_LABEL, weight=w)
    if name == 'focal':
        w = compute_class_weights(y, train_mask, num_classes, cfg.get('class_weight_power', 1.0), cfg.get('class_weight_cap', 10.0), device=device)
        return FocalLoss(gamma=cfg.get('focal_gamma', 2.0), weight=w, ignore_index=UNKNOWN_LABEL)
    raise ValueError(f'Unknown loss: {name}')
