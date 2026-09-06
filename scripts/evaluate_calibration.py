from __future__ import annotations

"""E5: calibration + selective-prediction evaluation (pre-registered).

Reloads a campaign model, refits ONE global temperature on validation logits
only (log T in [-3, 3]), then reports ECE / classwise-ECE / multiclass Brier /
NLL / AURC and risk-coverage rejection operating points.

Discipline frozen in sprint1_prereg.yaml:
- The temperature and the rejection thresholds are derived from val only and
  written to JSON BEFORE any test evaluation.
- Test metrics require --final-test and reuse the frozen val-derived artifacts.
- Temperature scaling is monotone: the script verifies the argmax set is
  (essentially) unchanged; a large change indicates an implementation error.
"""

import argparse
import json
from pathlib import Path

import numpy as np
import torch
import torch.nn.functional as F
from scipy.optimize import minimize_scalar

import _bootstrap  # noqa: F401
from btcaml.data.label_maps import UNKNOWN_LABEL
from campaign_eval_utils import forward_logits, load_campaign_model, load_protocol

LABELS = [
    'INDIVIDUAL', 'BET', 'GAMBLING', 'EXCHANGE', 'MINING', 'PONZI',
    'RANSOMWARE', 'FAUCET', 'MARKETPLACE', 'MIXER', 'BRIDGE',
]


def ece_equal_frequency(conf: np.ndarray, correct: np.ndarray, n_bins: int) -> float:
    n = len(conf)
    if n == 0:
        return float('nan')
    order = np.argsort(conf, kind='stable')
    bins = np.array_split(order, n_bins)
    total = 0.0
    for b in bins:
        if len(b) == 0:
            continue
        total += (len(b) / n) * abs(correct[b].mean() - conf[b].mean())
    return float(total)


def classwise_ece(probs: np.ndarray, y_true: np.ndarray, n_bins: int = 10) -> dict:
    per_class = {}
    for k in range(probs.shape[1]):
        conf = probs[:, k]
        correct = (y_true == k).astype(float)
        per_class[LABELS[k]] = ece_equal_frequency(conf, correct, n_bins)
    values = np.array([v for v in per_class.values() if np.isfinite(v)])
    return {'per_class': per_class, 'macro': float(values.mean()) if len(values) else float('nan')}


def multiclass_brier(probs: np.ndarray, y_true: np.ndarray) -> float:
    onehot = np.zeros_like(probs)
    onehot[np.arange(len(y_true)), y_true] = 1.0
    return float(((probs - onehot) ** 2).sum(axis=1).mean())


def nll(probs: np.ndarray, y_true: np.ndarray) -> float:
    p = np.clip(probs[np.arange(len(y_true)), y_true], 1e-12, 1.0)
    return float(-np.log(p).mean())


def risk_coverage(probs: np.ndarray, y_true: np.ndarray) -> dict:
    conf = probs.max(axis=1)
    correct = (probs.argmax(axis=1) == y_true).astype(float)
    order = np.argsort(-conf, kind='stable')
    c = correct[order]
    risks = 1.0 - np.cumsum(c) / np.arange(1, len(c) + 1)
    aurc = float(risks.mean())
    out = {'aurc': aurc}
    n = len(c)
    for cov in [0.05, 0.10, 0.25, 0.50, 0.75, 1.00]:
        k = max(1, int(np.ceil(cov * n)))
        out[f'risk_at_{int(cov * 100)}pct_coverage'] = float(risks[k - 1])
    return out


def fit_temperature(logits: np.ndarray, y_val: np.ndarray) -> float:
    z = torch.from_numpy(logits)

    def neg_ll(log_t: float) -> float:
        p = F.softmax(z / float(np.exp(log_t)), dim=1).numpy()
        return nll(p, y_val)

    res = minimize_scalar(neg_ll, bounds=(-3.0, 3.0), method='bounded')
    return float(np.exp(res.x))


def rejection_thresholds(conf_val: np.ndarray, correct_val: np.ndarray, targets: list[float]) -> dict:
    order = np.argsort(-conf_val, kind='stable')
    c = correct_val[order]
    out = {}
    for target in targets:
        best_k = 0
        for k in range(1, len(c) + 1):
            risk = 1.0 - c[:k].mean()
            if risk <= target:
                best_k = k
            else:
                break
        if best_k == 0:
            out[f'max_coverage_at_risk_{int(target * 100)}pct'] = {'coverage': 0.0, 'threshold': None, 'status': 'unavailable_on_val'}
        else:
            cov = best_k / len(c)
            thr = float(conf_val[order][:best_k].min())
            out[f'max_coverage_at_risk_{int(target * 100)}pct'] = {'coverage': float(cov), 'threshold': thr, 'status': 'ok'}
    return out


def evaluate(probs: np.ndarray, y_true: np.ndarray) -> dict:
    conf = probs.max(axis=1)
    correct = (probs.argmax(axis=1) == y_true).astype(float)
    return {
        'n': int(len(y_true)),
        'ece_15bins': ece_equal_frequency(conf, correct, 15),
        'classwise_ece_10bins': classwise_ece(probs, y_true),
        'brier': multiclass_brier(probs, y_true),
        'nll': nll(probs, y_true),
        **risk_coverage(probs, y_true),
    }


def main():
    ap = argparse.ArgumentParser(description='Calibration and selective-prediction report for a campaign model.')
    ap.add_argument('--run-dir', required=True, help='Model directory containing model_config.json.')
    ap.add_argument('--data', default=None)
    ap.add_argument('--device', default='cpu')
    ap.add_argument('--risk-targets', nargs='+', type=float, default=[0.05, 0.10, 0.20])
    ap.add_argument('--final-test', action='store_true')
    args = ap.parse_args()

    model, config, _ = load_campaign_model(args.run_dir, device=args.device)
    data_path = args.data or config['data_path']
    data = load_protocol(data_path)
    y = data.y.numpy()

    logits = forward_logits(model, data, device=args.device)
    base_probs = torch.softmax(torch.from_numpy(logits), dim=1).numpy()

    val_mask = data.val_mask.numpy().astype(bool) & (y != UNKNOWN_LABEL)
    val_logits = logits[val_mask]
    y_val = y[val_mask]

    temperature = fit_temperature(val_logits, y_val)
    scaled_probs = torch.softmax(torch.from_numpy(logits) / temperature, dim=1).numpy()

    argmax_changed = float((base_probs.argmax(axis=1) != scaled_probs.argmax(axis=1)).mean())

    report: dict = {
        'run_dir': str(args.run_dir),
        'data_path': str(data_path),
        'model': config['model'],
        'temperature_val_fitted': temperature,
        'argmax_change_fraction': argmax_changed,
        'val': {'raw': evaluate(base_probs[val_mask], y_val), 'calibrated': evaluate(scaled_probs[val_mask], y_val)},
    }

    # Val-derived rejection thresholds are frozen BEFORE any test evaluation.
    val_conf = scaled_probs[val_mask].max(axis=1)
    val_correct = (scaled_probs[val_mask].argmax(axis=1) == y_val).astype(float)
    thresholds = rejection_thresholds(val_conf, val_correct, args.risk_targets)
    (Path(args.run_dir) / 'rejection_thresholds_val.json').write_text(
        json.dumps({'temperature': temperature, 'thresholds': thresholds}, ensure_ascii=False, indent=2),
        encoding='utf-8',
    )
    report['rejection_thresholds_val'] = thresholds

    if args.final_test:
        test_mask = data.test_mask.numpy().astype(bool) & (y != UNKNOWN_LABEL)
        y_test = y[test_mask]
        report['test'] = {'raw': evaluate(base_probs[test_mask], y_test), 'calibrated': evaluate(scaled_probs[test_mask], y_test)}
        applied = {}
        for key, spec in thresholds.items():
            thr = spec['threshold']
            if thr is None:
                applied[key] = {'status': 'unavailable_on_val'}
                continue
            conf_t = scaled_probs[test_mask].max(axis=1)
            sel = conf_t >= thr
            risk_t = 1.0 - (scaled_probs[test_mask][sel].argmax(axis=1) == y_test[sel]).mean() if sel.any() else float('nan')
            applied[key] = {'status': 'ok', 'coverage': float(sel.mean()), 'empirical_risk': float(risk_t)}
        report['test_thresholds_applied'] = applied

    out = Path(args.run_dir)
    (out / 'calibration_report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    v = report['val']
    print(f"T*={temperature:.4f} | argmax_change={argmax_changed:.2%}")
    print(f"val raw   ECE={v['raw']['ece_15bins']:.4f} cwECE={v['raw']['classwise_ece_10bins']['macro']:.4f} Brier={v['raw']['brier']:.4f} AURC={v['raw']['aurc']:.4f}")
    print(f"val calib ECE={v['calibrated']['ece_15bins']:.4f} cwECE={v['calibrated']['classwise_ece_10bins']['macro']:.4f} Brier={v['calibrated']['brier']:.4f} AURC={v['calibrated']['aurc']:.4f}")
    print(f"Saved: {out / 'calibration_report.json'}")


if __name__ == '__main__':
    main()
