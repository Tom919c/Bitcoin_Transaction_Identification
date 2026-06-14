from __future__ import annotations

import argparse
import gc
from pathlib import Path
from typing import Any

import pandas as pd
import torch

import _bootstrap  # noqa: F401
from btcaml.data.label_maps import LABEL_TO_ID_11, RISK_GROUPS, get_label_space
from btcaml.evaluation.metrics import (
    classification_metrics,
    classification_report_table,
    confusion_matrix_table,
    per_class_metrics_table,
    ranking_metrics,
)
from btcaml.evaluation.ranking import sensitive_score_from_logits
from btcaml.models.registry import build_model
from btcaml.training.trainer import Trainer
from btcaml.utils.config import deep_update, load_config
from btcaml.utils.run_artifacts import RunArtifacts, file_size_mb, safe_name
from btcaml.utils.seed import seed_everything


DEFAULT_MODEL_PARAMS = {
    'mlp': {'hidden_channels': 128, 'num_layers': 3, 'dropout': 0.5},
    'sage': {'hidden_channels': 128, 'num_layers': 3, 'dropout': 0.3},
    'graphsage': {'hidden_channels': 128, 'num_layers': 3, 'dropout': 0.3},
    'edge_transformer': {'hidden_channels': 128, 'num_layers': 3, 'heads': 2, 'dropout': 0.3},
    'etd_sage': {'hidden_channels': 128, 'num_layers': 3, 'dropout': 0.3, 'edge_hidden': 64},
}


def _get(data, name):
    if hasattr(data, name):
        return getattr(data, name)
    return data[name]


def _has(data, name: str) -> bool:
    return hasattr(data, name) or (isinstance(data, dict) and name in data)


def load_data(path):
    try:
        payload = torch.load(path, map_location='cpu', weights_only=False)
    except TypeError:
        payload = torch.load(path, map_location='cpu')
    if isinstance(payload, dict) and 'data' in payload:
        return payload['data'], payload.get('metadata', {})
    return payload, {}


def dataset_name(path: str | Path) -> str:
    return safe_name(Path(path).stem)


def make_base_cfg(args) -> dict[str, Any]:
    cfg: dict[str, Any] = {}
    if args.config:
        cfg = load_config(args.config)
    if args.data:
        cfg = deep_update(cfg, {'data': {'processed_data_path': args.data}})
    if args.label_space:
        cfg = deep_update(cfg, {'data': {'label_space': args.label_space}})
    train_overrides = {}
    for key in ['device', 'epochs', 'seed', 'loss', 'lr', 'weight_decay', 'early_stopping_patience']:
        value = getattr(args, key, None)
        if value is not None:
            train_overrides[key] = value
    if args.smoke:
        train_overrides['epochs'] = min(int(train_overrides.get('epochs', 3)), 3)
        train_overrides['early_stopping_patience'] = 3
        train_overrides['log_every'] = 1
    if train_overrides:
        cfg = deep_update(cfg, {'train': train_overrides})
    return cfg


def model_params_for(name: str, cfg: dict[str, Any], args) -> dict[str, Any]:
    key = str(name).lower()
    params = dict(DEFAULT_MODEL_PARAMS.get(key, {'hidden_channels': 128, 'num_layers': 3, 'dropout': 0.3}))
    if cfg.get('model', {}).get('name', '').lower() == key:
        params.update(cfg.get('model', {}).get('params', {}))
    if args.hidden_channels is not None:
        params['hidden_channels'] = args.hidden_channels
    if args.num_layers is not None:
        params['num_layers'] = args.num_layers
    if args.dropout is not None:
        params['dropout'] = args.dropout
    return params


def evaluate_splits(trainer: Trainer, logits: torch.Tensor, labels: list[str], risk_group: str) -> list[dict[str, Any]]:
    rows = []
    y = trainer._get('y')
    risk_y = trainer._get('risk_y') if trainer._has('risk_y') else None
    sensitive_ids = [LABEL_TO_ID_11[x] for x in RISK_GROUPS.get(risk_group, []) if x in LABEL_TO_ID_11]
    risk_scores = sensitive_score_from_logits(logits, sensitive_ids) if sensitive_ids else None
    for split in ['train', 'val', 'test']:
        mask = trainer._get(f'{split}_mask')
        m = classification_metrics(logits, y, mask, labels)
        if risk_y is not None and risk_scores is not None:
            m.update(ranking_metrics(risk_scores, risk_y, mask))
        rows.append({'split': split, **m})
    return rows


def _write_table(df: pd.DataFrame, csv_path: Path, md_path: Path | None = None) -> None:
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(csv_path)
    if md_path is not None:
        md_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.write_text(df.to_markdown(), encoding='utf-8')


def export_detailed_evaluation(model_dir: Path, trainer: Trainer, logits: torch.Tensor, labels: list[str]) -> dict[str, Path]:
    eval_dir = model_dir / 'evaluation'
    eval_dir.mkdir(parents=True, exist_ok=True)

    y = trainer._get('y')
    split_masks = {split: trainer._get(f'{split}_mask') for split in ('train', 'val', 'test')}
    saved: dict[str, Path] = {}

    for split, mask in split_masks.items():
        per_class = per_class_metrics_table(logits, y, mask, labels)
        report = classification_report_table(logits, y, mask, labels)
        cm = confusion_matrix_table(logits, y, mask, labels)
        cm_norm = confusion_matrix_table(logits, y, mask, labels, normalize='true')

        per_class_csv = eval_dir / f'{split}_per_class.csv'
        per_class_md = eval_dir / f'{split}_per_class.md'
        report_csv = eval_dir / f'{split}_classification_report.csv'
        report_md = eval_dir / f'{split}_classification_report.md'
        cm_csv = eval_dir / f'{split}_confusion_matrix.csv'
        cm_norm_csv = eval_dir / f'{split}_confusion_matrix_norm_true.csv'

        _write_table(per_class, per_class_csv, per_class_md)
        _write_table(report, report_csv, report_md)
        _write_table(cm, cm_csv)
        _write_table(cm_norm, cm_norm_csv)

        saved.update(
            {
                f'{split}_per_class_csv': per_class_csv,
                f'{split}_per_class_md': per_class_md,
                f'{split}_classification_report_csv': report_csv,
                f'{split}_classification_report_md': report_md,
                f'{split}_confusion_matrix_csv': cm_csv,
                f'{split}_confusion_matrix_norm_true_csv': cm_norm_csv,
            }
        )

    return saved


def main():
    ap = argparse.ArgumentParser(description='Run concise MLP/GNN benchmarks on a protocol dataset.')
    ap.add_argument('--config', default=None, help='Optional experiment YAML. CLI args override it.')
    ap.add_argument('--data', default=None, help='Protocol dataset .pt path. Required if --config has no data path.')
    ap.add_argument('--models', nargs='+', default=None, help='Models: mlp sage edge_transformer etd_sage')
    ap.add_argument('--label-space', default=None, choices=['5', '11'])
    ap.add_argument('--epochs', type=int, default=None)
    ap.add_argument('--smoke', action='store_true', help='Run <=3 epochs only to verify pipeline.')
    ap.add_argument('--device', default=None)
    ap.add_argument('--seed', type=int, default=None)
    ap.add_argument('--loss', default=None)
    ap.add_argument('--lr', type=float, default=None)
    ap.add_argument('--weight-decay', type=float, default=None)
    ap.add_argument('--early-stopping-patience', type=int, default=None)
    ap.add_argument('--hidden-channels', type=int, default=None)
    ap.add_argument('--num-layers', type=int, default=None)
    ap.add_argument('--dropout', type=float, default=None)
    ap.add_argument('--out-root', default='experiments/runs')
    ap.add_argument('--run-name', default=None)
    args = ap.parse_args()

    cfg = make_base_cfg(args)
    data_path = cfg.get('data', {}).get('processed_data_path')
    if not data_path:
        raise ValueError('Pass --data or set data.processed_data_path in --config.')

    data, meta = load_data(data_path)
    label_space = str(cfg.get('data', {}).get('label_space', meta.get('label_space', '11')))
    labels = get_label_space(label_space).labels
    models = args.models or [cfg.get('model', {}).get('name', 'mlp')]
    train_cfg_base = {
        'seed': 42,
        'device': 'cpu',
        'epochs': 300,
        'lr': 0.001,
        'weight_decay': 0.0005,
        'loss': 'weighted_ce',
        'class_weight_power': 1.0,
        'class_weight_cap': 10.0,
        'grad_clip_norm': 1.0,
        'early_stopping_patience': 50,
        'eval_every': 1,
        'log_every': 10,
        **cfg.get('train', {}),
        'num_classes': len(labels),
    }

    run = RunArtifacts.create(
        'benchmark',
        root=args.out_root,
        run_name=args.run_name or f"{dataset_name(data_path)}_{'-'.join(models)}",
    )
    if args.config:
        run.copy_file(args.config, 'config.yaml')
    summary = {
        'data_path': str(data_path),
        'data_size_mb': round(file_size_mb(data_path), 2),
        'label_space': label_space,
        'models': models,
        'num_nodes': int(_get(data, 'x').shape[0]),
        'num_edges': int(_get(data, 'edge_index').shape[1]) if _has(data, 'edge_index') else 0,
        'num_features': int(_get(data, 'x').shape[1]),
    }
    run.write_json('run_config.json', {'summary': summary, 'train': train_cfg_base})
    print(f"Benchmark | data={Path(data_path).name} | models={','.join(models)} | run={run.run_dir}")

    all_rows: list[dict[str, Any]] = []
    for model_name in models:
        seed_everything(int(train_cfg_base.get('seed', 42)))
        params = model_params_for(model_name, cfg, args)
        edge_attr = _get(data, 'edge_attr') if _has(data, 'edge_attr') else None
        edge_dim = int(edge_attr.shape[1]) if edge_attr is not None and edge_attr.numel() > 0 else None
        in_channels = int(_get(data, 'x').shape[1])
        model = build_model(model_name, in_channels, len(labels), edge_dim=edge_dim, params=params)
        model_dir = run.run_dir / safe_name(model_name)
        train_cfg = {**train_cfg_base, 'checkpoint_dir': str(model_dir / 'checkpoints'), 'history_path': str(model_dir / 'train_history.json')}
        print(f"\n[{model_name}] params={sum(p.numel() for p in model.parameters()):,} epochs={train_cfg['epochs']} device={train_cfg['device']}")
        trainer = Trainer(model, data, train_cfg, labels=labels)
        trainer.train_full_batch()
        ckpt_path = Path(train_cfg['checkpoint_dir']) / 'best.pt'
        ckpt = torch.load(ckpt_path, map_location=trainer.device)
        model.load_state_dict(ckpt['model_state_dict'])
        model.eval()
        with torch.no_grad():
            logits = trainer._model_forward()
        export_detailed_evaluation(model_dir, trainer, logits, labels)
        rows = evaluate_splits(trainer, logits, labels, cfg.get('task', {}).get('risk_group', 'conservative_sensitive'))
        for row in rows:
            row['model'] = model_name
            row['dataset'] = dataset_name(data_path)
            row['best_epoch'] = int(ckpt.get('epoch', -1))
        all_rows.extend(rows)
        test_row = next(r for r in rows if r['split'] == 'test')
        print(f"[{model_name}] test macro={test_row['macro_f1']:.4f} minority={test_row.get('minority_macro_f1', 0.0):.4f} weighted={test_row['weighted_f1']:.4f}")
        del trainer, model, logits
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    df = pd.DataFrame(all_rows)
    # Put identifier columns first.
    front = [c for c in ['dataset', 'model', 'split', 'best_epoch', 'macro_f1', 'minority_macro_f1', 'weighted_f1', 'num_eval'] if c in df.columns]
    df = df[front + [c for c in df.columns if c not in front]]
    run.write_dataframe('results.csv', df)
    run.write_dataframe('results.md', df)
    run.flush_log()
    print(f"\nSaved: {run.run_dir / 'results.csv'}")
    print(df[df['split'].eq('test')][front].to_markdown(index=False))


if __name__ == '__main__':
    main()
