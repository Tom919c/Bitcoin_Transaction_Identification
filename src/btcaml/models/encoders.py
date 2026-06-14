from __future__ import annotations

import torch
import torch.nn as nn
import torch.nn.functional as F


class MLPEncoder(nn.Module):
    def __init__(self, in_channels: int, hidden_channels: int = 64, out_channels: int = 32, num_layers: int = 2, dropout: float = 0.0, layer_norm: bool = True):
        super().__init__()
        if num_layers < 1:
            raise ValueError('num_layers must be >= 1')
        dims = [in_channels] + [hidden_channels] * max(0, num_layers - 1) + [out_channels]
        self.layers = nn.ModuleList(nn.Linear(dims[i], dims[i+1]) for i in range(len(dims)-1))
        self.norm = nn.LayerNorm(out_channels) if layer_norm else nn.Identity()
        self.dropout = dropout

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        h = x
        for layer in self.layers[:-1]:
            h = F.dropout(F.relu(layer(h)), p=self.dropout, training=self.training)
        return self.norm(self.layers[-1](h))


class EdgeTemporalEncoder(nn.Module):
    def __init__(self, edge_dim: int, hidden_dim: int = 64, out_dim: int = 32, dropout: float = 0.1):
        super().__init__()
        self.encoder = MLPEncoder(edge_dim, hidden_dim, out_dim, num_layers=2, dropout=dropout)

    def forward(self, edge_attr: torch.Tensor) -> torch.Tensor:
        return self.encoder(edge_attr)
