from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import torch

import _bootstrap  # noqa: F401
from btcaml.data.label_maps import get_label_space
from btcaml.evaluation.export import export_detailed_evaluation
from btcaml.models.registry import build_model
from btcaml.utils.run_artifacts import safe_name


DEFAULT_MODEL_PARAMS = {
    'mlp': {'hidden_channels': 128, 'num_layers': 3, 'dropout': 0.5},
    'sage': {'hidden_channels': 128, 'num_layers': 3, 'dropout': 0.3},
    'graphsage': {'hidden_channels': 128, 'num_layers': 3, 'dropout': 0.3},
    'edge_transformer': {'hidden_channels': 128, 'num_layers': 3, 'heads': 2, 'dropout': 0.3},
    'etd_sage': {'hidden_channels': 128, 'num_layers': 3, 'dropout': 0.3, 'edge_hidden': 64},
}


def _get(data: Any, name: str):
    if hasattr(data, name):
        return getattr(data, name)
    return data[name]


def _has(data: Any, name: str) -> bool:
    return hasattr(data, name) or (isinstance(data, dict) and name in data)


def load_data(path: str | Path):
    try:
        payload = torch.load(path, map_location='cpu', weights_only=False)
    except TypeError:
        payload = torch.load(path, map_location='cpu')
    if isinstance(payload, dict) and 'data' in payload:
        return payload['data'], payload.get('metadata', {})
    return payload, {}


def infer_models(run_dir: Path) -> list[str]:
    models: list[str] = []
    for child in sorted(run_dir.iterdir()):
        if child.is_dir() and (child / 'checkpoints' / 'best.pt').exists():
            models.append(child.name)
    return models


def load_manifest(model_dir: Path) -> dict[str, Any]:
    path = model_dir / 'model_config.json'
    if path.exists():
        return json.loads(path.read_text(encoding='utf-8'))
    return {}


def forward_model(model, data):
    x = _get(data, 'x')
    edge_index = _get(data, 'edge_index') if _has(data, 'edge_index') else None
    edge_attr = _get(data, 'edge_attr') if _has(data, 'edge_attr') else None
    return model(x, edge_index=edge_index, edge_attr=edge_attr)


def main() -> None:
    ap = argparse.ArgumentParser(
        description='Export per-class metrics, confusion matrices and predictions from saved benchmark checkpoints.'
    )
    ap.add_argument('--run-dir', required=True, help='One experiments/runs/<run> directory.')
    ap.add_argument('--data', required=True, help='Protocol dataset .pt used by that run.')
    ap.add_argument('--models', nargs='+', default=None, help='Model names to export. Default: infer from checkpoint dirs.')
    ap.add_argument('--label-space', default=None, choices=['11'])
    ap.add_argument('--device', default='cpu')
    args = ap.parse_args()

    run_dir = Path(args.run_dir)
    if not run_dir.exists():
        raise FileNotFoundError(f'Run directory not found: {run_dir}')

    data, meta = load_data(args.data)
    label_space = str(args.label_space or meta.get('label_space', '11'))
    labels = get_label_space(label_space).labels
    device = torch.device(args.device)

    if hasattr(data, 'to'):
        data = data.to(device)
    elif isinstance(data, dict):
        for key, value in list(data.items()):
            if torch.is_tensor(value):
                data[key] = value.to(device)

    models = args.models or infer_models(run_dir)
    if not models:
        raise FileNotFoundError(
            f'No model checkpoints found under {run_dir}. Expected <model>/checkpoints/best.pt. '
            'Detailed evaluation cannot be exported from results.csv alone.'
        )

    edge_attr = _get(data, 'edge_attr') if _has(data, 'edge_attr') else None
    edge_dim = int(edge_attr.shape[1]) if edge_attr is not None and edge_attr.numel() > 0 else None
    in_channels = int(_get(data, 'x').shape[1])
    out_channels = len(labels)

    for model_name in models:
        model_dir = run_dir / safe_name(model_name)
        ckpt_path = model_dir / 'checkpoints' / 'best.pt'
        if not ckpt_path.exists():
            raise FileNotFoundError(
                f'Checkpoint not found for {model_name}: {ckpt_path}. '
                'If the historical run saved only results.csv, rerun benchmark once with the updated code.'
            )

        manifest = load_manifest(model_dir)
        canonical_name = manifest.get('model', model_name)
        params = dict(DEFAULT_MODEL_PARAMS.get(str(canonical_name).lower(), {}))
        params.update(manifest.get('params', {}))

        model = build_model(canonical_name, in_channels, out_channels, edge_dim=edge_dim, params=params)
        ckpt = torch.load(ckpt_path, map_location=device)
        model.load_state_dict(ckpt['model_state_dict'])
        model.to(device)
        model.eval()

        with torch.no_grad():
            logits = forward_model(model, data)

        saved = export_detailed_evaluation(model_dir, data, logits, labels)
        print(f'[{model_name}] exported {len(saved)} files to {model_dir / "evaluation"}')


if __name__ == '__main__':
    main()
