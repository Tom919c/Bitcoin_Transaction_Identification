from __future__ import annotations

import torch


def one_hop_edges(edge_index: torch.Tensor, node_idx: int) -> torch.Tensor:
    mask = (edge_index[0] == node_idx) | (edge_index[1] == node_idx)
    return edge_index[:, mask]
