from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable

import pandas as pd
import torch

from btcaml.data.label_maps import UNKNOWN_LABEL
from btcaml.evaluation.metrics import (
    classification_report_table,
    confusion_matrix_table,
    per_class_metrics_table,
    prediction_numpy,
)


def _get(data: Any, name: str):
    if hasattr(data, name):
        return getattr(data, name)
    return data[name]


def _has(data: Any, name: str) -> bool:
    return hasattr(data, name) or (isinstance(data, dict) and name in data)


def _write_table(df: pd.DataFrame, csv_path: Path, md_path: Path | None = None) -> None:
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(csv_path)
    if md_path is not None:
        md_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.write_text(df.to_markdown(), encoding='utf-8')


def prediction_table(
    logits: torch.Tensor,
    y: torch.Tensor,
    mask: torch.Tensor,
    labels: list[str],
) -> pd.DataFrame:
    """Return node-level predictions for one split.

    Only supervised nodes are exported: split mask must be true and y != UNKNOWN_LABEL.
    This is intentionally strict so unlabeled context nodes never leak into evaluation tables.
    """

    if logits.ndim != 2:
        raise ValueError(f'logits must be 2D, got {tuple(logits.shape)}')
    valid_mask = (mask.bool() & (y != UNKNOWN_LABEL)).detach().cpu()
    node_index = torch.nonzero(valid_mask, as_tuple=False).view(-1).numpy()
    y_true, y_pred = prediction_numpy(logits, y, mask)

    if len(node_index) == 0:
        return pd.DataFrame(
            columns=['node_index', 'y_true', 'y_pred', 'y_true_name', 'y_pred_name', 'confidence', 'correct']
        )

    probs = torch.softmax(logits.detach().cpu()[valid_mask], dim=1)
    confidence = probs.max(dim=1).values.numpy()
    true_names = [labels[int(i)] if 0 <= int(i) < len(labels) else str(i) for i in y_true]
    pred_names = [labels[int(i)] if 0 <= int(i) < len(labels) else str(i) for i in y_pred]

    return pd.DataFrame(
        {
            'node_index': node_index.astype(int),
            'y_true': y_true.astype(int),
            'y_pred': y_pred.astype(int),
            'y_true_name': true_names,
            'y_pred_name': pred_names,
            'confidence': confidence.astype(float),
            'correct': (y_true == y_pred).astype(bool),
        }
    )


def export_detailed_evaluation(
    output_dir: str | Path,
    data: Any,
    logits: torch.Tensor,
    labels: list[str],
    splits: Iterable[str] = ('train', 'val', 'test'),
) -> dict[str, Path]:
    """Export per-class metrics, classification reports, confusion matrices and predictions.

    This function performs no training. It only consumes model logits and split masks, so it can be
    used both immediately after `run_benchmark.py` and later by `export_detailed_eval.py` when a
    checkpoint already exists.
    """

    eval_dir = Path(output_dir) / 'evaluation'
    eval_dir.mkdir(parents=True, exist_ok=True)
    y = _get(data, 'y')
    saved: dict[str, Path] = {}

    for split in splits:
        mask_name = f'{split}_mask'
        if not _has(data, mask_name):
            continue
        mask = _get(data, mask_name)

        per_class = per_class_metrics_table(logits, y, mask, labels)
        report = classification_report_table(logits, y, mask, labels)
        cm = confusion_matrix_table(logits, y, mask, labels)
        cm_norm = confusion_matrix_table(logits, y, mask, labels, normalize='true')
        preds = prediction_table(logits, y, mask, labels)

        paths = {
            f'{split}_per_class_csv': eval_dir / f'{split}_per_class.csv',
            f'{split}_per_class_md': eval_dir / f'{split}_per_class.md',
            f'{split}_classification_report_csv': eval_dir / f'{split}_classification_report.csv',
            f'{split}_classification_report_md': eval_dir / f'{split}_classification_report.md',
            f'{split}_confusion_matrix_csv': eval_dir / f'{split}_confusion_matrix.csv',
            f'{split}_confusion_matrix_norm_true_csv': eval_dir / f'{split}_confusion_matrix_norm_true.csv',
            f'{split}_predictions_csv': eval_dir / f'{split}_predictions.csv',
        }

        _write_table(per_class, paths[f'{split}_per_class_csv'], paths[f'{split}_per_class_md'])
        _write_table(report, paths[f'{split}_classification_report_csv'], paths[f'{split}_classification_report_md'])
        _write_table(cm, paths[f'{split}_confusion_matrix_csv'])
        _write_table(cm_norm, paths[f'{split}_confusion_matrix_norm_true_csv'])
        preds.to_csv(paths[f'{split}_predictions_csv'], index=False)

        saved.update(paths)

    return saved
