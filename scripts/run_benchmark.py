from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
import torch

import _bootstrap  # noqa: F401
from btcaml.data.label_maps import get_label_space
from btcaml.evaluation.metrics import classification_metrics
from btcaml.models.registry import build_model
from btcaml.training.trainer import Trainer
from btcaml.utils.config import load_config
from btcaml.utils.seed import seed_everything


def _get(data, name):
    if hasattr(data, name):
        return getattr(data, name)
    return data[name]


def load_data(path):
    payload = torch.load(path, map_location='cpu')
    if isinstance(payload, dict) and 'data' in payload:
        return payload['data'], payload.get('metadata', {})
    return payload, {}


def main():
    ap = argparse.ArgumentParser(description='Run one benchmark experiment.')
    ap.add_argument('--config', required=True)
    args = ap.parse_args()
    cfg = load_config(args.config)
    seed_everything(cfg.get('train', {}).get('seed', 42))
    data, meta = load_data(cfg['data']['processed_data_path'])
    label_space = str(cfg['data'].get('label_space', meta.get('label_space', '11')))
    labels = get_label_space(label_space).labels
    model_cfg = cfg['model']
    train_cfg = cfg['train']
    in_channels = int(_get(data, 'x').shape[1])
    edge_attr = _get(data, 'edge_attr') if (hasattr(data, 'edge_attr') or (isinstance(data, dict) and 'edge_attr' in data)) else None
    edge_dim = int(edge_attr.shape[1]) if edge_attr is not None and edge_attr.numel() > 0 else None
    model = build_model(model_cfg['name'], in_channels, len(labels), edge_dim=edge_dim, params=model_cfg.get('params', {}))
    train_cfg = {**train_cfg, 'num_classes': len(labels)}
    trainer = Trainer(model, data, train_cfg, labels=labels)
    trainer.train_full_batch()
    ckpt = torch.load(Path(train_cfg.get('checkpoint_dir', 'experiments/checkpoints')) / 'best.pt', map_location=trainer.device)
    model.load_state_dict(ckpt['model_state_dict'])
    model.eval()
    with torch.no_grad():
        logits = trainer._model_forward()
    rows = []
    for split in ['train', 'val', 'test']:
        m = classification_metrics(logits, trainer._get('y'), trainer._get(f'{split}_mask'), labels)
        rows.append({'split': split, **m})
    df = pd.DataFrame(rows)
    out = Path(cfg.get('experiment', {}).get('output_csv', 'experiments/results/benchmark_result.csv'))
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False)
    print(df.to_markdown(index=False))


if __name__ == '__main__':
    main()
