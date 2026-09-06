from __future__ import annotations

"""E2: CPU LightGBM node-feature baseline (pre-registered, frozen config).

Uses only the 27-dim node features of a protocol .pt; graph structure is not
seen. Unlabeled nodes (y == -1) never enter training, validation or metrics and
are not a 12th class. All hyperparameters are frozen in
experiments/campaign/sprint1_prereg.yaml; no tuning in sprint 1.

Test metrics are only computed with --final-test (once, frozen protocol).
"""

import argparse
import json
from pathlib import Path

import numpy as np
import torch
from lightgbm import early_stopping, log_evaluation, LGBMClassifier
from sklearn.metrics import f1_score

import _bootstrap  # noqa: F401
from btcaml.data.label_maps import UNKNOWN_LABEL
from btcaml.utils.seed import seed_everything

LABELS = [
    'INDIVIDUAL', 'BET', 'GAMBLING', 'EXCHANGE', 'MINING', 'PONZI',
    'RANSOMWARE', 'FAUCET', 'MARKETPLACE', 'MIXER', 'BRIDGE',
]
ALL_LABELS = list(range(11))

FROZEN_PARAMS = {
    'objective': 'multiclass',
    'num_class': 11,
    'learning_rate': 0.05,
    'num_leaves': 63,
    'n_estimators': 1000,
    'colsample_bytree': 0.8,   # feature_fraction
    'subsample': 0.8,          # bagging_fraction
    'bagging_freq': 1,
    'reg_lambda': 1.0,
    'verbosity': -1,
}


def macro_f1(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    return float(f1_score(y_true, y_pred, average='macro', labels=ALL_LABELS, zero_division=0))


def per_class_f1(y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, float]:
    f = f1_score(y_true, y_pred, average=None, labels=ALL_LABELS, zero_division=0)
    return {name: float(v) for name, v in zip(LABELS, f)}


def main():
    ap = argparse.ArgumentParser(description='Frozen LightGBM node-feature baseline.')
    ap.add_argument('--data', default='data/processed/protocols/temporal_balanced_no_temporal.pt')
    ap.add_argument('--seeds', nargs='+', type=int, default=[42, 3407, 1234])
    ap.add_argument('--final-test', action='store_true')
    ap.add_argument('--out-root', default='experiments/campaign/runs')
    ap.add_argument('--run-name', default=None)
    args = ap.parse_args()

    try:
        payload = torch.load(args.data, map_location='cpu', weights_only=False)
    except TypeError:
        payload = torch.load(args.data, map_location='cpu')
    data = payload['data']
    x = data.x.numpy()
    y = data.y.numpy()

    run_name = args.run_name or f"sprint1_gbdt_{'s' + '-s'.join(str(s) for s in args.seeds)}{'_finaltest' if args.final_test else ''}"
    run_dir = Path(args.out_root) / run_name
    run_dir.mkdir(parents=True, exist_ok=True)
    run_config = {
        'prereg': 'experiments/campaign/sprint1_prereg.yaml',
        'packet_id': 'btc-expcampaign-20260906-01',
        'data_path': str(args.data),
        'params': FROZEN_PARAMS,
        'seeds': args.seeds,
        'early_stopping_rounds': 50,
        'final_test': bool(args.final_test),
        'model': 'lightgbm_multiclass',
    }
    (run_dir / 'run_config.json').write_text(json.dumps(run_config, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f"GBDT | data={Path(args.data).name} | seeds={args.seeds} | final_test={args.final_test}")

    rows = []
    for seed in args.seeds:
        seed_everything(seed)
        train_mask = data.train_mask.numpy().astype(bool) & (y != UNKNOWN_LABEL)
        val_mask = data.val_mask.numpy().astype(bool) & (y != UNKNOWN_LABEL)
        test_mask = data.test_mask.numpy().astype(bool) & (y != UNKNOWN_LABEL)
        model = LGBMClassifier(random_state=seed, n_jobs=-1, **FROZEN_PARAMS)
        model.fit(
            x[train_mask], y[train_mask],
            eval_set=[(x[val_mask], y[val_mask])],
            eval_metric='multi_logloss',
            callbacks=[early_stopping(50, verbose=False), log_evaluation(0)],
        )
        val_pred = model.predict(x[val_mask])
        row = {
            'model': 'lightgbm',
            'seed': seed,
            'best_iteration': int(model.best_iteration_ or 0),
            'split': 'val',
            'macro_f1': macro_f1(y[val_mask], val_pred),
            **{f'f1_{k}': v for k, v in per_class_f1(y[val_mask], val_pred).items()},
        }
        rows.append(row)
        print(f"[seed {seed}] val macro={row['macro_f1']:.4f} (best_iter={row['best_iteration']})")
        if args.final_test:
            test_pred = model.predict(x[test_mask])
            trow = {
                'model': 'lightgbm',
                'seed': seed,
                'best_iteration': int(model.best_iteration_ or 0),
                'split': 'test',
                'macro_f1': macro_f1(y[test_mask], test_pred),
                **{f'f1_{k}': v for k, v in per_class_f1(y[test_mask], test_pred).items()},
            }
            rows.append(trow)
            print(f"[seed {seed}] test macro={trow['macro_f1']:.4f}")

    with open(run_dir / 'metrics.json', 'w', encoding='utf-8') as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)
    print(f"Saved: {run_dir / 'metrics.json'}")


if __name__ == '__main__':
    main()
