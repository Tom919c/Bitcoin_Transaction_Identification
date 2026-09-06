from __future__ import annotations

"""Shared model reload helper for campaign evaluation scripts.

Rebuilds a campaign model from its model_config.json and loads best.pt, so no
existing file has to change. Only campaign-produced run directories (which
record 'model' and 'params') are supported.
"""

import json
from pathlib import Path

import torch

import _bootstrap  # noqa: F401
from btcaml.models.registry import build_model
from btcaml.ext import DGResEGS, DirSAGE


def load_protocol(data_path: str):
    try:
        payload = torch.load(data_path, map_location='cpu', weights_only=False)
    except TypeError:
        payload = torch.load(data_path, map_location='cpu')
    data = payload['data'] if isinstance(payload, dict) and 'data' in payload else payload
    return data


def load_campaign_model(model_dir: str | Path, device: str = 'cpu'):
    model_dir = Path(model_dir)
    config = json.loads((model_dir / 'model_config.json').read_text(encoding='utf-8'))
    name = str(config['model'])
    params = dict(config.get('params', {}))
    variant = params.pop('variant', None)
    in_channels = int(config['in_channels'])
    out_channels = int(config['out_channels'])
    edge_dim = config.get('edge_dim')

    if name in {'egs', 'edge_gated_sage'}:
        model = build_model('edge_gated_sage', in_channels, out_channels, edge_dim=edge_dim, params=params)
    elif name == 'dir_sage':
        model = DirSAGE(
            in_channels=in_channels,
            hidden_channels=params['hidden_channels'],
            out_channels=out_channels,
            num_layers=params['num_layers'],
            dropout=params['dropout'],
        )
    elif name in {'resegs_a1', 'resegs_a2', 'resegs_a3', 'dg_resegs'}:
        model = DGResEGS(
            in_channels=in_channels,
            hidden_channels=params['hidden_channels'],
            out_channels=out_channels,
            edge_dim=edge_dim,
            num_layers=params['num_layers'],
            dropout=params['dropout'],
            edge_hidden=params['edge_hidden'],
            use_direction=params['use_direction'],
            variant=variant or 'a2',
        )
    else:
        raise KeyError(f'Unsupported campaign model: {name}')

    ckpt = torch.load(model_dir / 'checkpoints' / 'best.pt', map_location=device)
    model.load_state_dict(ckpt['model_state_dict'])
    model.to(torch.device(device))
    model.eval()
    return model, config, ckpt


def forward_logits(model, data, device: str = 'cpu') -> torch.Tensor:
    dev = torch.device(device)
    x = data.x.to(dev)
    edge_index = data.edge_index.to(dev) if data.edge_index is not None else None
    edge_attr = data.edge_attr.to(dev) if getattr(data, 'edge_attr', None) is not None else None
    with torch.no_grad():
        logits = model(x, edge_index=edge_index, edge_attr=edge_attr)
    return logits.cpu()
