from __future__ import annotations

"""Sprint-1 campaign runner (pre-registered; additive only).

Implements experiments E0/E1/E3 of docs/大创调研/bridge/result-20260906-01.md
on top of the frozen protocol datasets without touching any existing file.

Discipline:
- Development stages never read test metrics; pass --final-test only after the
  configuration is frozen (recorded as final_test in the run config).
- All hyperparameters come from experiments/campaign/sprint1_prereg.yaml.
- A3 (V-REx) uses a training loop that mirrors Trainer exactly, plus the
  environment risk-variance penalty. Environments are computed once from
  labeled TRAIN nodes via node_time quantiles and written to the run config.
"""

import argparse
import gc
import json
from pathlib import Path
from typing import Any

import pandas as pd
import torch

import _bootstrap  # noqa: F401
from btcaml.data.label_maps import UNKNOWN_LABEL
from btcaml.evaluation.export import export_detailed_evaluation
from btcaml.evaluation.metrics import classification_metrics
from btcaml.models.registry import build_model
from btcaml.training.losses import build_loss
from btcaml.training.trainer import Trainer
from btcaml.utils.io import atomic_torch_save, save_json
from btcaml.utils.seed import seed_everything
from btcaml.ext import DGResEGS, DirSAGE

DEFAULT_PARAMS = {
    'hidden_channels': 128,
    'num_layers': 3,
    'dropout': 0.3,
    'edge_hidden': 64,
    'use_direction': True,
}

RESEGS_VARIANTS = {'resegs_a1': 'a1', 'resegs_a2': 'a2', 'resegs_a3': 'a2'}


def load_data(path):
    try:
        payload = torch.load(path, map_location='cpu', weights_only=False)
    except TypeError:
        payload = torch.load(path, map_location='cpu')
    if isinstance(payload, dict) and 'data' in payload:
        return payload['data'], payload.get('metadata', {})
    return payload, {}


def _get(data, name):
    if hasattr(data, name):
        return getattr(data, name)
    return data[name]


def _has(data, name) -> bool:
    return hasattr(data, name) or (isinstance(data, dict) and name in data)


def build_campaign_model(name: str, in_channels: int, out_channels: int, edge_dim: int | None, params: dict):
    key = name.lower()
    if key == 'egs':
        return build_model('edge_gated_sage', in_channels, out_channels, edge_dim=edge_dim, params=params)
    if key == 'dir_sage':
        return DirSAGE(
            in_channels=in_channels,
            hidden_channels=params['hidden_channels'],
            out_channels=out_channels,
            num_layers=params['num_layers'],
            dropout=params['dropout'],
        )
    if key in RESEGS_VARIANTS:
        return DGResEGS(
            in_channels=in_channels,
            hidden_channels=params['hidden_channels'],
            out_channels=out_channels,
            edge_dim=edge_dim,
            num_layers=params['num_layers'],
            dropout=params['dropout'],
            edge_hidden=params['edge_hidden'],
            use_direction=params['use_direction'],
            variant=RESEGS_VARIANTS[key],
        )
    raise KeyError(f'Unknown campaign model: {name}')


def compute_env_boundaries(data, n_envs: int) -> dict[str, Any]:
    """Env boundaries from labeled TRAIN nodes only, via node_time quantiles."""
    y = _get(data, 'y')
    train_mask = _get(data, 'train_mask').bool() & (y != UNKNOWN_LABEL)
    times = _get(data, 'node_time')[train_mask].float()
    if times.numel() == 0:
        raise ValueError('No labeled train nodes for environment split.')
    qs = [i / n_envs for i in range(1, n_envs)]
    bounds = torch.quantile(times, torch.tensor(qs, dtype=times.dtype))
    return {
        'time_field': 'node_time',
        'n_envs': n_envs,
        'boundaries': [float(b) for b in bounds.tolist()],
        'n_labeled_train': int(train_mask.sum().item()),
        'rule': f'labeled_train_quantiles_{qs}',
    }


def env_masks(data, env_cfg: dict[str, Any]) -> list[torch.Tensor]:
    y = _get(data, 'y')
    train_sup = _get(data, 'train_mask').bool() & (y != UNKNOWN_LABEL)
    t = _get(data, 'node_time').float()
    bounds = env_cfg['boundaries']
    masks = []
    lower = None
    for b in bounds:
        m = train_sup & (t <= b) if lower is None else train_sup & (t > lower) & (t <= b)
        masks.append(m)
        lower = b
    masks.append(train_sup & (t > lower))
    return masks


def train_vrex(model, data, cfg: dict, labels: list[str], env_cfg: dict[str, Any]) -> list[dict[str, Any]]:
    """Mirror of Trainer.train_full_batch with the V-REx environment penalty.

    Same base weighted_ce criterion (global class weights), optimizer, grad
    clip, val macro_f1 early stopping and checkpoint format as Trainer.
    """
    device = torch.device(cfg.get('device', 'cpu'))
    model.to(device)
    y = _get(data, 'y')
    train_mask = _get(data, 'train_mask').bool() & (y != UNKNOWN_LABEL)
    val_mask = _get(data, 'val_mask').bool() & (y != UNKNOWN_LABEL)
    criterion = build_loss(
        cfg.get('loss', 'weighted_ce'),
        y,
        train_mask,
        int(cfg['num_classes']),
        cfg,
        device=device,
    )
    optimizer = torch.optim.Adam(model.parameters(), lr=float(cfg.get('lr', 1e-3)), weight_decay=float(cfg.get('weight_decay', 5e-4)))
    masks = env_masks(data, env_cfg)
    lam = float(cfg.get('vrex_lambda', 0.3))
    epochs = int(cfg.get('epochs', 200))
    patience = int(cfg.get('early_stopping_patience', 50))
    clip = float(cfg.get('grad_clip_norm', 0) or 0)
    best_metric, best_epoch = -1.0, -1
    best_path = Path(cfg['checkpoint_dir']) / 'best.pt'
    best_path.parent.mkdir(parents=True, exist_ok=True)
    history: list[dict[str, Any]] = []

    def forward_logits():
        return model(_get(data, 'x'), edge_index=_get(data, 'edge_index'), edge_attr=_get(data, 'edge_attr'))

    for epoch in range(1, epochs + 1):
        model.train()
        optimizer.zero_grad()
        logits = forward_logits()
        env_risks = [criterion(logits[m], y[m]) for m in masks]
        risks = torch.stack(env_risks)
        loss = risks.mean() + lam * risks.var(unbiased=False)
        loss.backward()
        if clip > 0:
            torch.nn.utils.clip_grad_norm_(model.parameters(), clip)
        optimizer.step()
        record: dict[str, Any] = {'epoch': epoch, 'loss': float(loss.item()), 'env_risks': [float(r.item()) for r in env_risks]}
        with torch.no_grad():
            model.eval()
            val_logits = forward_logits()
            val_metrics = classification_metrics(val_logits, y, val_mask, labels)
        record.update({f'val_{k}': v for k, v in val_metrics.items()})
        metric = float(val_metrics.get('macro_f1', 0.0))
        if metric > best_metric:
            best_metric, best_epoch = metric, epoch
            atomic_torch_save(
                {'model_state_dict': model.state_dict(), 'epoch': epoch, 'val_macro_f1': best_metric, 'config': cfg},
                best_path,
            )
        history.append(record)
        if epoch - best_epoch >= patience:
            record['early_stop'] = True
            break
    save_json(history, Path(cfg['history_path']))
    Path(cfg['history_path']).with_suffix('.csv').parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(history).to_csv(Path(cfg['history_path']).with_suffix('.csv'), index=False)
    return history


def main():
    ap = argparse.ArgumentParser(description='Pre-registered sprint-1 campaign runner.')
    ap.add_argument('--data', default='data/processed/protocols/temporal_balanced_no_temporal.pt')
    ap.add_argument('--models', nargs='+', required=True,
                    choices=['egs', 'dir_sage', 'resegs_a1', 'resegs_a2', 'resegs_a3'])
    ap.add_argument('--seed', type=int, default=42)
    ap.add_argument('--epochs', type=int, default=200)
    ap.add_argument('--early-stopping-patience', type=int, default=50)
    ap.add_argument('--device', default='cpu')
    ap.add_argument('--vrex-lambda', type=float, default=0.3, help='A3 only; screen {0.1,0.3,1.0} on val.')
    ap.add_argument('--n-envs', type=int, default=3)
    ap.add_argument('--smoke', action='store_true', help='2 epochs, patience 2.')
    ap.add_argument('--final-test', action='store_true', help='Open the protocol test split (once, frozen config only).')
    ap.add_argument('--out-root', default='experiments/campaign/runs')
    ap.add_argument('--run-name', default=None)
    args = ap.parse_args()

    data, meta = load_data(args.data)
    if hasattr(data, 'to'):
        data = data.to(torch.device(args.device))
    labels = [
        'INDIVIDUAL', 'BET', 'GAMBLING', 'EXCHANGE', 'MINING', 'PONZI',
        'RANSOMWARE', 'FAUCET', 'MARKETPLACE', 'MIXER', 'BRIDGE',
    ]
    y = _get(data, 'y')
    if int((y == UNKNOWN_LABEL).sum().item()) == 0:
        raise ValueError('Protocol missing unlabeled context (-1); check the dataset file.')

    epochs, patience = (2, 2) if args.smoke else (args.epochs, args.early_stopping_patience)
    run_name = args.run_name or f"sprint1_{'-'.join(args.models)}_s{args.seed}{'_smoke' if args.smoke else ''}{'_finaltest' if args.final_test else ''}"
    run_dir = Path(args.out_root) / run_name
    run_dir.mkdir(parents=True, exist_ok=True)

    env_cfg = None
    if 'resegs_a3' in args.models:
        env_cfg = compute_env_boundaries(data, args.n_envs)

    run_config = {
        'prereg': 'experiments/campaign/sprint1_prereg.yaml',
        'packet_id': 'btc-expcampaign-20260906-01',
        'data_path': str(args.data),
        'models': args.models,
        'seed': args.seed,
        'epochs': epochs,
        'early_stopping_patience': patience,
        'device': args.device,
        'vrex_lambda': args.vrex_lambda if 'resegs_a3' in args.models else None,
        'environment': env_cfg,
        'final_test': bool(args.final_test),
        'smoke': bool(args.smoke),
    }
    (run_dir / 'run_config.json').write_text(json.dumps(run_config, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f"Sprint1 | data={Path(args.data).name} | models={','.join(args.models)} | seed={args.seed} | final_test={args.final_test}")

    all_rows: list[dict[str, Any]] = []
    for model_name in args.models:
        seed_everything(args.seed)
        edge_attr = _get(data, 'edge_attr') if _has(data, 'edge_attr') else None
        edge_dim = int(edge_attr.shape[1]) if edge_attr is not None and edge_attr.numel() > 0 else None
        in_channels = int(_get(data, 'x').shape[1])
        model = build_campaign_model(model_name, in_channels, len(labels), edge_dim, dict(DEFAULT_PARAMS))
        model_dir = run_dir / model_name
        model_dir.mkdir(parents=True, exist_ok=True)
        train_cfg = {
            'seed': args.seed,
            'device': args.device,
            'epochs': epochs,
            'lr': 0.001,
            'weight_decay': 0.0005,
            'loss': 'weighted_ce',
            'class_weight_power': 1.0,
            'class_weight_cap': 10.0,
            'grad_clip_norm': 1.0,
            'early_stopping_patience': patience,
            'eval_every': 1,
            'log_every': 10,
            'num_classes': len(labels),
            'vrex_lambda': args.vrex_lambda,
            'checkpoint_dir': str(model_dir / 'checkpoints'),
            'history_path': str(model_dir / 'train_history.json'),
        }
        model_config = {
            'model': model_name,
            'params': {**DEFAULT_PARAMS, 'variant': RESEGS_VARIANTS.get(model_name)},
            'in_channels': in_channels,
            'out_channels': len(labels),
            'edge_dim': edge_dim,
            'labels': labels,
            'data_path': str(args.data),
            'n_parameters': int(sum(p.numel() for p in model.parameters())),
            'train': {k: v for k, v in train_cfg.items() if k != 'vrex_lambda'},
        }
        (model_dir / 'model_config.json').write_text(json.dumps(model_config, ensure_ascii=False, indent=2), encoding='utf-8')
        print(f"[{model_name}] params={model_config['n_parameters']:,} epochs={epochs} device={args.device}")

        if model_name == 'resegs_a3':
            train_vrex(model, data, train_cfg, labels, env_cfg)
        else:
            trainer = Trainer(model, data, train_cfg, labels=labels)
            trainer.train_full_batch()
            del trainer
            gc.collect()

        ckpt = torch.load(Path(train_cfg['checkpoint_dir']) / 'best.pt', map_location=args.device)
        model.load_state_dict(ckpt['model_state_dict'])
        model.eval()
        with torch.no_grad():
            logits = model(
                _get(data, 'x'),
                edge_index=_get(data, 'edge_index'),
                edge_attr=_get(data, 'edge_attr') if _has(data, 'edge_attr') else None,
            )
            logits = logits.cpu()
        y_dev = _get(data, 'y').cpu()
        rows: list[dict[str, Any]] = []
        for split in ['train', 'val']:
            mask = _get(data, f'{split}_mask').bool().cpu()
            m = classification_metrics(logits, y_dev, mask, labels)
            rows.append({'split': split, 'model': model_name, 'seed': args.seed, **m})
        if args.final_test:
            mask = _get(data, 'test_mask').bool().cpu()
            m = classification_metrics(logits, y_dev, mask, labels)
            rows.append({'split': 'test', 'model': model_name, 'seed': args.seed, **m})
        export_detailed_evaluation(model_dir, data, logits, labels)
        all_rows.extend(rows)
        val_row = next(r for r in rows if r['split'] == 'val')
        print(f"[{model_name}] val macro={val_row['macro_f1']:.4f}" + (
            f" test macro={next(r for r in rows if r['split'] == 'test')['macro_f1']:.4f}" if args.final_test else ''
        ))
        del model, logits
        gc.collect()

    df = pd.DataFrame(all_rows)
    df.to_csv(run_dir / 'metrics.csv', index=False)
    with open(run_dir / 'metrics.json', 'w', encoding='utf-8') as f:
        json.dump(all_rows, f, ensure_ascii=False, indent=2)
    print(f"Saved: {run_dir / 'metrics.csv'}")


if __name__ == '__main__':
    main()
