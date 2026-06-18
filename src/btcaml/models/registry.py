from __future__ import annotations

from .edge_sage import EdgeGatedSAGE
from .edge_transformer import EdgeTransformerGNN
from .etd_sage import ETDSAGE
from .mlp import MLP
from .sage import GraphSAGE

MODEL_REGISTRY = {
    'mlp': MLP,
    'sage': GraphSAGE,
    'graphsage': GraphSAGE,
    'edge_transformer': EdgeTransformerGNN,
    'etd_sage': ETDSAGE,
    'etd_gnn': ETDSAGE,
    'edge_gated_sage': EdgeGatedSAGE,
    'egs': EdgeGatedSAGE,
}


def build_model(name: str, in_channels: int, out_channels: int, edge_dim: int | None = None, params: dict | None = None):
    params = dict(params or {})
    key = str(name).lower()
    if key not in MODEL_REGISTRY:
        raise KeyError(f'Unknown model {name}. Available: {sorted(MODEL_REGISTRY)}')
    cls = MODEL_REGISTRY[key]
    if key in {'edge_transformer', 'etd_sage', 'etd_gnn', 'edge_gated_sage', 'egs'}:
        if edge_dim is None:
            raise ValueError(f'{name} requires edge_dim')
        params.setdefault('edge_dim', edge_dim)
    return cls(in_channels=in_channels, out_channels=out_channels, **params)
