from __future__ import annotations

"""E4: temporal-slice robustness diagnostics (pre-registered; val only).

No training. Splits the supervised validation nodes of a campaign run into
`--slices` equal-count consecutive slices ordered by node_time (the same field
the protocol's temporal split uses) and reports per-slice Macro-F1, per-class
F1, prediction distribution, mean confidence and conservative ranking metrics.

Decision rule frozen in sprint1_prereg.yaml: a "temporal robustness" claim
requires delta F1 on the LATEST slice > 0 and at least 2/3 positive slices.
"""

import argparse
import json
from pathlib import Path

import numpy as np
import torch
from sklearn.metrics import f1_score, precision_recall_curve, auc, roc_auc_score

import _bootstrap  # noqa: F401
from btcaml.data.label_maps import LABEL_TO_ID_11, RISK_GROUPS, UNKNOWN_LABEL
from campaign_eval_utils import forward_logits, load_campaign_model, load_protocol

LABELS = [
    'INDIVIDUAL', 'BET', 'GAMBLING', 'EXCHANGE', 'MINING', 'PONZI',
    'RANSOMWARE', 'FAUCET', 'MARKETPLACE', 'MIXER', 'BRIDGE',
]
ALL_LABELS = list(range(11))


def conservative_auprc(scores: np.ndarray, risk_y: np.ndarray) -> dict[str, float]:
    if risk_y.sum() == 0:
        return {'conservative_auprc': float('nan'), 'conservative_auroc': float('nan')}
    precision, recall, _ = precision_recall_curve(risk_y, scores)
    out = {'conservative_auprc': float(auc(recall, precision))}
    try:
        out['conservative_auroc'] = float(roc_auc_score(risk_y, scores))
    except ValueError:
        out['conservative_auroc'] = float('nan')
    return out


def main():
    ap = argparse.ArgumentParser(description='Temporal slice diagnostics for a campaign model.')
    ap.add_argument('--run-dir', required=True, help='Model directory containing model_config.json.')
    ap.add_argument('--data', default=None, help='Protocol .pt; defaults to the model config data_path.')
    ap.add_argument('--slices', type=int, default=3)
    ap.add_argument('--device', default='cpu')
    args = ap.parse_args()

    model, config, _ = load_campaign_model(args.run_dir, device=args.device)
    data_path = args.data or config['data_path']
    data = load_protocol(data_path)
    y = data.y.numpy()
    node_time = data.node_time.numpy().astype(np.float64)

    logits = forward_logits(model, data, device=args.device)
    probs = torch.softmax(torch.from_numpy(logits), dim=1).numpy()
    pred = logits.argmax(axis=1)

    val_mask = data.val_mask.numpy().astype(bool) & (y != UNKNOWN_LABEL)
    idx = np.where(val_mask)[0]
    order = idx[np.argsort(node_time[idx], kind='stable')]
    splits = np.array_split(order, args.slices)

    sensitive_ids = [LABEL_TO_ID_11[x] for x in RISK_GROUPS.get('conservative_sensitive', [])]
    risk_scores = probs[:, sensitive_ids].sum(axis=1)
    risk_y = data.risk_y.numpy() if hasattr(data, 'risk_y') else None

    report: dict = {
        'run_dir': str(args.run_dir),
        'data_path': str(data_path),
        'split': 'val',
        'n_slices': args.slices,
        'time_field': 'node_time',
        'model': config['model'],
        'slices': [],
    }
    for i, slice_idx in enumerate(splits, start=1):
        y_true, y_pred = y[slice_idx], pred[slice_idx]
        f1s = f1_score(y_true, y_pred, average=None, labels=ALL_LABELS, zero_division=0)
        entry = {
            'slice': i,
            'n': int(len(slice_idx)),
            'time_min': float(node_time[slice_idx].min()),
            'time_max': float(node_time[slice_idx].max()),
            'macro_f1': float(f1_score(y_true, y_pred, average='macro', labels=ALL_LABELS, zero_division=0)),
            'per_class_f1': {name: float(v) for name, v in zip(LABELS, f1s)},
            'pred_class_distribution': {name: float((y_pred == k).mean()) for k, name in enumerate(LABELS)},
            'mean_confidence': float(probs[slice_idx].max(axis=1).mean()),
        }
        if risk_y is not None:
            entry.update(conservative_auprc(risk_scores[slice_idx], risk_y[slice_idx].astype(int)))
        report['slices'].append(entry)

    report['latest_slice_macro_f1'] = report['slices'][-1]['macro_f1']

    out_dir = Path(args.run_dir)
    (out_dir / 'temporal_slice_report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    lines = ['| slice | n | macro_f1 | mean_conf | conservative_AUPRC |', '|---|---:|---:|---:|---:|']
    for e in report['slices']:
        lines.append(f"| {e['slice']} | {e['n']} | {e['macro_f1']:.4f} | {e['mean_confidence']:.4f} | {e.get('conservative_auprc', float('nan')):.4f} |")
    (out_dir / 'temporal_slice_report.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print('\n'.join(lines))
    print(f"Saved: {out_dir / 'temporal_slice_report.json'}")


if __name__ == '__main__':
    main()
