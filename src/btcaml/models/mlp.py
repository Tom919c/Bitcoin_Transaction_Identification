from __future__ import annotations

import torch
import torch.nn as nn
import torch.nn.functional as F

from .base import BaseModel


class MLP(BaseModel):
    def __init__(self, in_channels: int, hidden_channels: int, out_channels: int, num_layers: int = 2, dropout: float = 0.5, **kwargs):
        super().__init__(in_channels, hidden_channels, out_channels)
        if num_layers < 2:
            raise ValueError('MLP num_layers must be >= 2')
        self.dropout = dropout
        layers = [nn.Linear(in_channels, hidden_channels)]
        for _ in range(num_layers - 2):
            layers.append(nn.Linear(hidden_channels, hidden_channels))
        layers.append(nn.Linear(hidden_channels, out_channels))
        self.layers = nn.ModuleList(layers)

    def forward(self, x, edge_index=None, edge_attr=None, return_embeddings=False, **kwargs):
        h = x
        for layer in self.layers[:-1]:
            h = F.dropout(F.relu(layer(h)), p=self.dropout, training=self.training)
        emb = h
        logits = self.layers[-1](h)
        if return_embeddings:
            return logits, emb
        return logits
