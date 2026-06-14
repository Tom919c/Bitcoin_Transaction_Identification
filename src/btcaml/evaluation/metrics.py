from __future__ import annotations

import numpy as np
import pandas as pd
import torch
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_recall_fscore_support,
)

from btcaml.data.label_maps import UNKNOWN_LABEL


def _resolve_label_names(labels: list[str] | None, num_classes: int) -> list[str]:
    if labels is None:
        return [str(i) for i in range(num_classes)]
    names = [str(label) for label in labels]
    if len(names) != num_classes:
        raise ValueError(f'labels length {len(names)} does not match num_classes {num_classes}')
    return names


def _prediction_numpy_full(logits: torch.Tensor, y: torch.Tensor, mask: torch.Tensor):
    if logits.ndim != 2:
        raise ValueError(f'logits must be 2D, got shape {tuple(logits.shape)}')
    if y.ndim != 1:
        raise ValueError(f'y must be 1D, got shape {tuple(y.shape)}')
    if mask.ndim != 1:
        raise ValueError(f'mask must be 1D, got shape {tuple(mask.shape)}')
    if logits.shape[0] != y.shape[0] or y.shape[0] != mask.shape[0]:
        raise ValueError('logits, y and mask must have the same first dimension')

    mask_np = mask.detach().cpu().numpy().astype(bool, copy=False)
    y_np = y.detach().cpu().numpy()
    valid = mask_np & (y_np != UNKNOWN_LABEL)
    logits_np = logits.detach().cpu().numpy()[valid]
    y_true = y_np[valid].astype(np.int64, copy=False)
    if logits_np.shape[0] == 0:
        y_pred = np.empty((0,), dtype=np.int64)
    else:
        y_pred = logits_np.argmax(axis=1).astype(np.int64, copy=False)
    return logits_np, y_true, y_pred


def prediction_numpy(logits: torch.Tensor, y: torch.Tensor, mask: torch.Tensor):
    y_true, y_pred = _prediction_numpy_full(logits, y, mask)[1:]
    return y_true, y_pred


def _classification_arrays(logits: torch.Tensor, y: torch.Tensor, mask: torch.Tensor, labels: list[str] | None):
    logits_np, y_true, y_pred = _prediction_numpy_full(logits, y, mask)
    label_names = _resolve_label_names(labels, logits.shape[1])
    label_ids = list(range(len(label_names)))
    return logits_np, y_true, y_pred, label_ids, label_names


def _empty_classification_dict(labels: list[str] | None, num_classes: int) -> dict:
    label_names = _resolve_label_names(labels, num_classes)
    out = {'macro_f1': 0.0, 'weighted_f1': 0.0, 'num_eval': 0}
    for name in label_names:
        out[f'{name}_precision'] = 0.0
        out[f'{name}_recall'] = 0.0
        out[f'{name}_f1'] = 0.0
        out[f'{name}_support'] = 0
    minority_names = [x for x in ['BET', 'GAMBLING', 'PONZI', 'RANSOMWARE', 'MIXER', 'BRIDGE'] if x in label_names]
    if minority_names:
        out['minority_macro_f1'] = 0.0
    return out


def classification_metrics(logits: torch.Tensor, y: torch.Tensor, mask: torch.Tensor, labels: list[str] | None = None) -> dict:
    _, y_np, pred_np = _prediction_numpy_full(logits, y, mask)
    num_classes = logits.shape[1]
    label_names = _resolve_label_names(labels, num_classes)
    if len(y_np) == 0:
        return _empty_classification_dict(label_names, num_classes)
    all_labels = list(range(num_classes))
    p, r, f, support = precision_recall_fscore_support(y_np, pred_np, labels=all_labels, zero_division=0)
    out = {
        'accuracy': float(accuracy_score(y_np, pred_np)),
        'macro_f1': float(f1_score(y_np, pred_np, average='macro', labels=all_labels, zero_division=0)),
        'weighted_f1': float(f1_score(y_np, pred_np, average='weighted', labels=all_labels, zero_division=0)),
        'num_eval': int(len(y_np)),
    }
    for i, name in enumerate(label_names):
        out[f'{name}_precision'] = float(p[i])
        out[f'{name}_recall'] = float(r[i])
        out[f'{name}_f1'] = float(f[i])
        out[f'{name}_support'] = int(support[i])
    # Minority F1 convention: risk/sensitive small classes if present.
    minority_names = [x for x in ['BET', 'GAMBLING', 'PONZI', 'RANSOMWARE', 'MIXER', 'BRIDGE'] if x in label_names]
    if minority_names:
        vals = [out[f'{name}_f1'] for name in minority_names]
        out['minority_macro_f1'] = float(np.mean(vals))
    return out


def per_class_metrics_table(
    logits: torch.Tensor,
    y: torch.Tensor,
    mask: torch.Tensor,
    labels: list[str] | None = None,
) -> pd.DataFrame:
    _, y_true, y_pred, label_ids, label_names = _classification_arrays(logits, y, mask, labels)
    if len(y_true) == 0:
        precision = np.zeros(len(label_ids), dtype=np.float64)
        recall = np.zeros(len(label_ids), dtype=np.float64)
        f1 = np.zeros(len(label_ids), dtype=np.float64)
        support = np.zeros(len(label_ids), dtype=np.int64)
    else:
        precision, recall, f1, support = precision_recall_fscore_support(
            y_true,
            y_pred,
            labels=label_ids,
            zero_division=0,
        )

    table = pd.DataFrame(
        {
            'precision': precision,
            'recall': recall,
            'f1': f1,
            'support': support.astype(int, copy=False),
        },
        index=pd.Index(label_names, name='label'),
    )
    return table


def classification_report_table(
    logits: torch.Tensor,
    y: torch.Tensor,
    mask: torch.Tensor,
    labels: list[str] | None = None,
) -> pd.DataFrame:
    _, y_true, y_pred, label_ids, label_names = _classification_arrays(logits, y, mask, labels)
    if len(y_true) == 0:
        precision = np.zeros(len(label_ids), dtype=np.float64)
        recall = np.zeros(len(label_ids), dtype=np.float64)
        f1 = np.zeros(len(label_ids), dtype=np.float64)
        support = np.zeros(len(label_ids), dtype=np.int64)
        accuracy = 0.0
    else:
        precision, recall, f1, support = precision_recall_fscore_support(
            y_true,
            y_pred,
            labels=label_ids,
            zero_division=0,
        )
        accuracy = float(accuracy_score(y_true, y_pred))

    rows: list[tuple[str, float, float, float, int]] = []
    for idx, name in enumerate(label_names):
        rows.append((name, float(precision[idx]), float(recall[idx]), float(f1[idx]), int(support[idx])))

    total_support = int(support.sum())
    rows.extend(
        [
            ('accuracy', np.nan, np.nan, float(accuracy), total_support),
            (
                'macro avg',
                float(np.mean(precision)) if len(precision) else 0.0,
                float(np.mean(recall)) if len(recall) else 0.0,
                float(np.mean(f1)) if len(f1) else 0.0,
                total_support,
            ),
            (
                'weighted avg',
                float(np.average(precision, weights=support)) if total_support > 0 else 0.0,
                float(np.average(recall, weights=support)) if total_support > 0 else 0.0,
                float(np.average(f1, weights=support)) if total_support > 0 else 0.0,
                total_support,
            ),
        ]
    )

    return pd.DataFrame(rows, columns=['label', 'precision', 'recall', 'f1-score', 'support']).set_index('label')


def confusion_matrix_table(
    logits: torch.Tensor,
    y: torch.Tensor,
    mask: torch.Tensor,
    labels: list[str] | None = None,
    normalize: str | bool = False,
) -> pd.DataFrame:
    _, y_true, y_pred, label_ids, label_names = _classification_arrays(logits, y, mask, labels)
    raw = confusion_matrix(y_true, y_pred, labels=label_ids)
    if normalize in (True, 'true'):
        denom = raw.sum(axis=1, keepdims=True)
        matrix = np.divide(raw, denom, out=np.zeros_like(raw, dtype=np.float64), where=denom != 0)
    elif normalize == 'pred':
        denom = raw.sum(axis=0, keepdims=True)
        matrix = np.divide(raw, denom, out=np.zeros_like(raw, dtype=np.float64), where=denom != 0)
    elif normalize == 'all':
        total = raw.sum()
        matrix = raw / total if total > 0 else np.zeros_like(raw, dtype=np.float64)
    elif normalize in (False, None):
        matrix = raw.astype(np.int64, copy=False)
    else:
        raise ValueError("normalize must be one of False, True, 'true', 'pred', or 'all'")

    return pd.DataFrame(
        matrix,
        index=pd.Index(label_names, name='true_label'),
        columns=pd.Index(label_names, name='pred_label'),
    )


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
    logits_np, y_np, pred = _prediction_numpy_full(logits, y, mask)
    num_classes = logits.shape[1]
    all_labels = list(range(num_classes))
    target_names = labels if labels is not None else None
    return classification_report(y_np, pred, labels=all_labels, target_names=target_names, zero_division=0)
