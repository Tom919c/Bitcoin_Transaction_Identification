from __future__ import annotations

import torch
import torch.nn as nn
import torch.nn.functional as F

from .base import BaseModel


class GraphSAGE(BaseModel):
    def __init__(self, in_channels: int, hidden_channels: int, out_channels: int, num_layers: int = 3, dropout: float = 0.3, **kwargs):
        super().__init__(in_channels, hidden_channels, out_channels)
        try:
            from torch_geometric.nn import SAGEConv
        except Exception as exc:  # pragma: no cover
            raise ImportError('GraphSAGE requires torch_geometric. Install torch_geometric to use GNN baselines.') from exc
        if num_layers < 2:
            raise ValueError('num_layers must be >= 2')
        dims = [in_channels] + [hidden_channels] * (num_layers - 1) + [out_channels]
        self.convs = nn.ModuleList(SAGEConv(dims[i], dims[i + 1]) for i in range(num_layers))
        self.norms = nn.ModuleList(nn.LayerNorm(hidden_channels) for _ in range(num_layers - 1))
        self.dropout = dropout

    def forward(self, x, edge_index=None, edge_attr=None, return_embeddings=False, **kwargs):
        if edge_index is None:
            raise ValueError('GraphSAGE requires edge_index')
        h = x
        for conv, norm in zip(self.convs[:-1], self.norms):
            h = conv(h, edge_index)
            h = F.dropout(F.relu(norm(h)), p=self.dropout, training=self.training)
        emb = h
        logits = self.convs[-1](h, edge_index)
        if return_embeddings:
            return logits, emb
        return logits
