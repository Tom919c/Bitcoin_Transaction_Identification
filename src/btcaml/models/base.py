from __future__ import annotations

from abc import ABC, abstractmethod

import torch
import torch.nn as nn


class BaseModel(nn.Module, ABC):
    def __init__(self, in_channels: int, hidden_channels: int, out_channels: int, **kwargs):
        super().__init__()
        self.in_channels = in_channels
        self.hidden_channels = hidden_channels
        self.out_channels = out_channels

    @abstractmethod
    def forward(
        self,
        x: torch.Tensor,
        edge_index: torch.Tensor | None = None,
        edge_attr: torch.Tensor | None = None,
        node_time: torch.Tensor | None = None,
        edge_time: torch.Tensor | None = None,
        batch: torch.Tensor | None = None,
        return_embeddings: bool = False,
        return_explanations: bool = False,
        **kwargs,
    ):
        raise NotImplementedError
