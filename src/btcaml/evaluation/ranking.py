from __future__ import annotations

import torch


def sensitive_score_from_logits(logits: torch.Tensor, sensitive_class_ids: list[int]) -> torch.Tensor:
    prob = torch.softmax(logits, dim=-1)
    idx = torch.tensor(sensitive_class_ids, dtype=torch.long, device=logits.device)
    return prob.index_select(dim=-1, index=idx).sum(dim=-1)
