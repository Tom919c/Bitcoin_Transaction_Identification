from __future__ import annotations

"""Pre-registered final-test evaluator: reload a completed val-only run's
best.pt and open the protocol test split ONCE, without retraining.

This is the test-once gate of sprint1_prereg.yaml: run it only after the model
configuration is frozen. Produces test Macro-F1, per-class F1, conservative
ranking metrics and prediction CSV in the run directory.
"""

import argparse
import json
from pathlib import Path

import numpy as np
import torch
from sklearn.metrics import f1_score, precision_recall_curve, auc, roc_auc_score

import _bootstrap  # noqa: F401
from btcaml.data.label_maps import LABEL_TO_ID_11, RISK_GROUPS, UNKNOWN_LABEL
from btcaml.evaluation.metrics import classification_metrics
from campaign_eval_utils import forward_logits, load_campaign_model, load_protocol

LABELS = [
    'INDIVIDUAL', 'BET', 'GAMBLING', 'EXCHANGE', 'MINING', 'PONZI',
    'RANSOMWARE', 'FAUCET', 'MARKETPLACE', 'MIXER', 'BRIDGE',
]


def main() -> None:
    ap = argparse.ArgumentParser(description='Open the test split once for a frozen campaign run.')
    ap.add_argument('--run-dir', required=True, help='Model dir containing model_config.json and checkpoints/best.pt')
    ap.add_argument('--data', default=None)
    ap.add_argument('--device', default='cpu')
    ap.add_argument('--confirm-frozen', required=True, action='store_true',
                    help='Acknowledges the configuration is frozen per sprint1_prereg.yaml.')
    args = ap.parse_args()
    if not args.confirm_frozen:
        raise SystemExit('Refusing to open test without --confirm-frozen (test-once discipline).')

    model, config, ckpt = load_campaign_model(args.run_dir, device=args.device)
    data_path = args.data or config['data_path']
    data = load_protocol(data_path)
    y = data.y.numpy()

    logits = forward_logits(model, data, device=args.device)
    probs = torch.softmax(torch.from_numpy(logits), dim=1).numpy()
    pred = logits.argmax(axis=1)

    test_mask = data.test_mask.numpy().astype(bool) & (y != UNKNOWN_LABEL)
    m = classification_metrics(torch.from_numpy(logits), torch.from_numpy(y), torch.from_numpy(test_mask), LABELS)

    sensitive_ids = [LABEL_TO_ID_11[x] for x in RISK_GROUPS.get('conservative_sensitive', [])]
    risk_scores = probs[:, sensitive_ids].sum(axis=1)
    risk_y = data.risk_y.numpy().astype(int) if hasattr(data, 'risk_y') else None
    if risk_y is not None:
        precision, recall, _ = precision_recall_curve(risk_y[test_mask], risk_scores[test_mask])
        m['conservative_auprc'] = float(auc(recall, precision))
        try:
            m['conservative_auroc'] = float(roc_auc_score(risk_y[test_mask], risk_scores[test_mask]))
        except ValueError:
            pass
        for frac in (0.01, 0.05, 0.10):
            k = max(1, int(np.ceil(frac * test_mask.sum())))
            order = np.argsort(-risk_scores[test_mask], kind='stable')
            m[f'conservative_recall_at_{int(frac * 100)}pct'] = float(risk_y[test_mask][order[:k]].sum() / max(1, risk_y[test_mask].sum()))

    marker = {
        'final_test': True,
        'run_dir': str(args.run_dir),
        'data_path': str(data_path),
        'model': config['model'],
        'checkpoint_epoch': int(ckpt.get('epoch', -1)),
        'test_macro_f1': m.get('macro_f1'),
    }
    out = Path(args.run_dir)
    (out / 'final_test_metrics.json').write_text(json.dumps(marker | m, ensure_ascii=False, indent=2), encoding='utf-8')

    idx = np.where(test_mask)[0]
    with open(out / 'final_test_predictions.csv', 'w', encoding='utf-8', newline='') as f:
        f.write('node_index,y_true,y_pred,confidence,correct\n')
        for i, yt, yp, p in zip(idx, y[idx], pred[idx], probs[idx].max(axis=1)):
            f.write(f'{i},{yt},{yp},{p},{yt == yp}\n')

    print(f"FINAL TEST opened for {config['model']} @ {args.run_dir}")
    print(f"test macro_f1={m.get('macro_f1'):.4f} weighted={m.get('weighted_f1'):.4f}")
    if 'conservative_auprc' in m:
        print(f"conservative AUPRC={m['conservative_auprc']:.4f} AUROC={m.get('conservative_auroc', float('nan')):.4f}")


if __name__ == '__main__':
    main()
