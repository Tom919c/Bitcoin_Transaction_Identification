from __future__ import annotations

import torch


def degree_summary(edge_index: torch.Tensor, num_nodes: int) -> dict:
    deg = torch.bincount(edge_index.reshape(-1), minlength=num_nodes).float()
    return {
        'mean_degree': float(deg.mean().item()),
        'median_degree': float(deg.median().item()),
        'p99_degree': float(torch.quantile(deg, 0.99).item()),
        'max_degree': int(deg.max().item()),
    }
