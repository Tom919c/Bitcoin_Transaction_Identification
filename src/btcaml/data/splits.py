from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import torch
from sklearn.model_selection import train_test_split

from .label_maps import UNKNOWN_LABEL


@dataclass
class SplitResult:
    train_mask: torch.BoolTensor
    val_mask: torch.BoolTensor
    test_mask: torch.BoolTensor
    metadata: dict


def _empty_masks(n: int):
    return torch.zeros(n, dtype=torch.bool), torch.zeros(n, dtype=torch.bool), torch.zeros(n, dtype=torch.bool)


def random_stratified_split(y: torch.Tensor, val_ratio=0.2, test_ratio=0.2, seed=42) -> SplitResult:
    y_np = y.detach().cpu().numpy()
    labeled_idx = np.where(y_np != UNKNOWN_LABEL)[0]
    if len(labeled_idx) == 0:
        raise ValueError('No labeled nodes for split')
    labels = y_np[labeled_idx]
    tmp_ratio = val_ratio + test_ratio
    train_idx, tmp_idx = train_test_split(
        labeled_idx, test_size=tmp_ratio, random_state=seed, stratify=labels
    )
    tmp_labels = y_np[tmp_idx]
    val_fraction = val_ratio / tmp_ratio if tmp_ratio > 0 else 0.5
    val_idx, test_idx = train_test_split(
        tmp_idx, test_size=1 - val_fraction, random_state=seed, stratify=tmp_labels
    )
    train_mask, val_mask, test_mask = _empty_masks(len(y_np))
    train_mask[torch.as_tensor(train_idx, dtype=torch.long)] = True
    val_mask[torch.as_tensor(val_idx, dtype=torch.long)] = True
    test_mask[torch.as_tensor(test_idx, dtype=torch.long)] = True
    return SplitResult(train_mask, val_mask, test_mask, {'type': 'random_stratified', 'seed': seed})


def classwise_temporal_split(y: torch.Tensor, time_values: torch.Tensor, val_ratio=0.2, test_ratio=0.2) -> SplitResult:
    y_np = y.detach().cpu().numpy()
    t_np = time_values.detach().cpu().numpy()
    train_mask, val_mask, test_mask = _empty_masks(len(y_np))
    meta = {'type': 'classwise_temporal', 'classes': {}}
    for label in sorted(set(y_np.tolist())):
        if label == UNKNOWN_LABEL:
            continue
        idx = np.where(y_np == label)[0]
        idx = idx[np.argsort(t_np[idx], kind='mergesort')]
        n = len(idx)
        n_train = max(1, int(round(n * (1 - val_ratio - test_ratio))))
        n_val = max(1, int(round(n * val_ratio))) if n - n_train > 1 else 0
        train_idx = idx[:n_train]
        val_idx = idx[n_train:n_train+n_val]
        test_idx = idx[n_train+n_val:]
        train_mask[torch.as_tensor(train_idx, dtype=torch.long)] = True
        val_mask[torch.as_tensor(val_idx, dtype=torch.long)] = True
        test_mask[torch.as_tensor(test_idx, dtype=torch.long)] = True
        meta['classes'][int(label)] = {'n': n, 'train': len(train_idx), 'val': len(val_idx), 'test': len(test_idx)}
    return SplitResult(train_mask, val_mask, test_mask, meta)


def global_temporal_split(y: torch.Tensor, time_values: torch.Tensor, val_ratio=0.2, test_ratio=0.2) -> SplitResult:
    y_np = y.detach().cpu().numpy()
    t_np = time_values.detach().cpu().numpy()
    labeled_idx = np.where(y_np != UNKNOWN_LABEL)[0]
    labeled_idx = labeled_idx[np.argsort(t_np[labeled_idx], kind='mergesort')]
    n = len(labeled_idx)
    n_train = int(round(n * (1 - val_ratio - test_ratio)))
    n_val = int(round(n * val_ratio))
    train_idx = labeled_idx[:n_train]
    val_idx = labeled_idx[n_train:n_train+n_val]
    test_idx = labeled_idx[n_train+n_val:]
    train_mask, val_mask, test_mask = _empty_masks(len(y_np))
    train_mask[torch.as_tensor(train_idx, dtype=torch.long)] = True
    val_mask[torch.as_tensor(val_idx, dtype=torch.long)] = True
    test_mask[torch.as_tensor(test_idx, dtype=torch.long)] = True
    return SplitResult(train_mask, val_mask, test_mask, {'type': 'global_temporal'})


def build_split(y: torch.Tensor, time_values: torch.Tensor | None, cfg: dict) -> SplitResult:
    split_type = cfg.get('type', 'random_stratified')
    if split_type == 'random_stratified':
        return random_stratified_split(y, cfg.get('val_ratio', 0.2), cfg.get('test_ratio', 0.2), cfg.get('seed', 42))
    if time_values is None:
        raise ValueError(f'{split_type} requires time_values')
    if split_type == 'classwise_temporal':
        return classwise_temporal_split(y, time_values, cfg.get('val_ratio', 0.2), cfg.get('test_ratio', 0.2))
    if split_type == 'global_temporal':
        return global_temporal_split(y, time_values, cfg.get('val_ratio', 0.2), cfg.get('test_ratio', 0.2))
    raise ValueError(f'Unknown split type: {split_type}')
