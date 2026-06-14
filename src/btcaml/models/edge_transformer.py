from __future__ import annotations

import torch
import torch.nn as nn
import torch.nn.functional as F

from .base import BaseModel


class EdgeTransformerGNN(BaseModel):
    """PyG TransformerConv baseline that uses edge_attr via edge_dim."""

    def __init__(self, in_channels: int, hidden_channels: int, out_channels: int, edge_dim: int, num_layers: int = 3, heads: int = 2, dropout: float = 0.3, **kwargs):
        super().__init__(in_channels, hidden_channels, out_channels)
        try:
            from torch_geometric.nn import TransformerConv
        except Exception as exc:  # pragma: no cover
            raise ImportError('EdgeTransformerGNN requires torch_geometric.') from exc
        self.dropout = dropout
        self.convs = nn.ModuleList()
        self.norms = nn.ModuleList()
        self.convs.append(TransformerConv(in_channels, hidden_channels // heads, heads=heads, edge_dim=edge_dim, dropout=dropout))
        self.norms.append(nn.LayerNorm(hidden_channels))
        for _ in range(num_layers - 2):
            self.convs.append(TransformerConv(hidden_channels, hidden_channels // heads, heads=heads, edge_dim=edge_dim, dropout=dropout))
            self.norms.append(nn.LayerNorm(hidden_channels))
        self.convs.append(TransformerConv(hidden_channels, out_channels, heads=1, concat=False, edge_dim=edge_dim, dropout=dropout))

    def forward(self, x, edge_index=None, edge_attr=None, return_embeddings=False, **kwargs):
        if edge_index is None or edge_attr is None:
            raise ValueError('EdgeTransformerGNN requires edge_index and edge_attr')
        h = x
        for conv, norm in zip(self.convs[:-1], self.norms):
            h = conv(h, edge_index, edge_attr=edge_attr)
            h = F.dropout(F.relu(norm(h)), p=self.dropout, training=self.training)
        emb = h
        logits = self.convs[-1](h, edge_index, edge_attr=edge_attr)
        if return_embeddings:
            return logits, emb
        return logits
