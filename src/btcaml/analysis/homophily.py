from __future__ import annotations

import torch

from btcaml.data.label_maps import UNKNOWN_LABEL


def edge_label_homophily(edge_index: torch.Tensor, y: torch.Tensor) -> dict:
    src, dst = edge_index
    valid = (y[src] != UNKNOWN_LABEL) & (y[dst] != UNKNOWN_LABEL)
    if valid.sum() == 0:
        return {'labeled_edges': 0, 'homophily': 0.0}
    same = (y[src[valid]] == y[dst[valid]]).float().mean().item()
    return {'labeled_edges': int(valid.sum().item()), 'homophily': float(same)}
