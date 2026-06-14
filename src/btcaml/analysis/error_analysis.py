from __future__ import annotations

import pandas as pd
import torch


def error_table(logits: torch.Tensor, y: torch.Tensor, mask: torch.Tensor, aliases=None) -> pd.DataFrame:
    pred = logits.argmax(dim=-1).detach().cpu()
    y_cpu = y.detach().cpu()
    idx = torch.where(mask.detach().cpu() & (pred != y_cpu))[0]
    data = {'idx': idx.numpy(), 'true': y_cpu[idx].numpy(), 'pred': pred[idx].numpy()}
    if aliases is not None:
        data['alias'] = aliases.detach().cpu()[idx].numpy()
    return pd.DataFrame(data)
