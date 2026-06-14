from __future__ import annotations

import numpy as np
import torch
from sklearn.metrics import average_precision_score, classification_report, f1_score, precision_recall_fscore_support

from btcaml.data.label_maps import UNKNOWN_LABEL


def _valid_numpy(logits: torch.Tensor, y: torch.Tensor, mask: torch.Tensor):
    valid = (mask.bool() & (y != UNKNOWN_LABEL)).detach().cpu().numpy()
    y_np = y.detach().cpu().numpy()[valid]
    logits_np = logits.detach().cpu().numpy()[valid]
    return logits_np, y_np


def classification_metrics(logits: torch.Tensor, y: torch.Tensor, mask: torch.Tensor, labels: list[str] | None = None) -> dict:
    logits_np, y_np = _valid_numpy(logits, y, mask)
    if len(y_np) == 0:
        return {'macro_f1': 0.0, 'weighted_f1': 0.0, 'num_eval': 0}
    pred = logits_np.argmax(axis=1)
    num_classes = logits_np.shape[1]
    all_labels = list(range(num_classes))
    p, r, f, support = precision_recall_fscore_support(y_np, pred, labels=all_labels, zero_division=0)
    out = {
        'macro_f1': float(f1_score(y_np, pred, average='macro', labels=all_labels, zero_division=0)),
        'weighted_f1': float(f1_score(y_np, pred, average='weighted', zero_division=0)),
        'num_eval': int(len(y_np)),
    }
    if labels is None:
        labels = [str(i) for i in all_labels]
    for i, name in enumerate(labels):
        out[f'{name}_precision'] = float(p[i])
        out[f'{name}_recall'] = float(r[i])
        out[f'{name}_f1'] = float(f[i])
        out[f'{name}_support'] = int(support[i])
    # Minority F1 convention: risk/sensitive small classes if present.
    minority_names = [x for x in ['BET', 'GAMBLING', 'PONZI', 'RANSOMWARE', 'MIXER', 'BRIDGE'] if x in labels]
    if minority_names:
        vals = [out[f'{name}_f1'] for name in minority_names]
        out['minority_macro_f1'] = float(np.mean(vals))
    return out


def ranking_metrics(scores: torch.Tensor, risk_y: torch.Tensor, mask: torch.Tensor, ks=(0.01, 0.05, 0.10)) -> dict:
    valid = (mask.bool() & (risk_y >= 0)).detach().cpu().numpy()
    y = risk_y.detach().cpu().numpy()[valid]
    s = scores.detach().cpu().numpy()[valid]
    out = {'ranking_num_eval': int(len(y)), 'risk_positive': int((y == 1).sum())}
    if len(y) == 0 or (y == 1).sum() == 0:
        for k in ks:
            out[f'recall_at_{int(k*100)}pct'] = 0.0
            out[f'yield_at_{int(k*100)}pct'] = 0.0
        out['auprc'] = 0.0
        return out
    out['auprc'] = float(average_precision_score(y, s))
    order = np.argsort(-s)
    positives = (y == 1).sum()
    for k in ks:
        topn = max(1, int(np.ceil(len(y) * k)))
        top = y[order[:topn]]
        hits = int((top == 1).sum())
        out[f'recall_at_{int(k*100)}pct'] = float(hits / positives)
        out[f'yield_at_{int(k*100)}pct'] = float(hits / topn)
    return out


def make_classification_report(logits: torch.Tensor, y: torch.Tensor, mask: torch.Tensor, labels: list[str] | None = None) -> str:
    logits_np, y_np = _valid_numpy(logits, y, mask)
    pred = logits_np.argmax(axis=1)
    target_names = labels if labels is not None else None
    return classification_report(y_np, pred, target_names=target_names, zero_division=0)
