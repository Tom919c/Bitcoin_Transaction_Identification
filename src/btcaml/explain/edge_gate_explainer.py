from __future__ import annotations

import torch


def topk_edges_by_gate(edge_index: torch.Tensor, gate: torch.Tensor, k: int = 20) -> dict:
    score = gate.mean(dim=-1) if gate.ndim == 2 else gate
    vals, idx = torch.topk(score, k=min(k, score.numel()))
    return {'edge_index': edge_index[:, idx].detach().cpu(), 'score': vals.detach().cpu()}
