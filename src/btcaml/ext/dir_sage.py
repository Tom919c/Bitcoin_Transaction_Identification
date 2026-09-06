from __future__ import annotations

import torch
import torch.nn as nn
import torch.nn.functional as F

from btcaml.models.base import BaseModel


def _scatter_mean(src: torch.Tensor, index: torch.Tensor, dim_size: int) -> torch.Tensor:
    out = torch.zeros(dim_size, src.size(-1), dtype=src.dtype, device=src.device)
    count = torch.zeros(dim_size, 1, dtype=src.dtype, device=src.device)
    out.index_add_(0, index, src)
    ones = torch.ones(src.size(0), 1, dtype=src.dtype, device=src.device)
    count.index_add_(0, index, ones)
    return out / count.clamp_min(1.0)


class DirSAGEConv(nn.Module):
    """Direction-separated mean aggregation: incoming and outgoing neighbors
    are transformed and pooled on separate channels, then linearly combined.

    No edge features and no edge gating, so any gain of this model over
    GraphSAGE is attributable to direction separation alone.
    """

    def __init__(self, in_channels: int, out_channels: int):
        super().__init__()
        self.self_lin = nn.Linear(in_channels, out_channels)
        self.in_lin = nn.Linear(in_channels, out_channels)
        self.out_lin = nn.Linear(in_channels, out_channels)

    def forward(self, x: torch.Tensor, edge_index: torch.Tensor) -> torch.Tensor:
        src, dst = edge_index[0], edge_index[1]
        m_in = _scatter_mean(x[src], dst, x.size(0))
        m_out = _scatter_mean(x[dst], src, x.size(0))
        return self.self_lin(x) + self.in_lin(m_in) + self.out_lin(m_out)


class DirSAGE(BaseModel):
    """Two-channel (in/out) GraphSAGE. Depth defaults to 3 to stay matched with
    the frozen EGS configuration (controlled comparison takes precedence over
    the "two-layer" phrasing in the reasoning result; recorded in run config).
    """

    def __init__(
        self,
        in_channels: int,
        hidden_channels: int,
        out_channels: int,
        num_layers: int = 3,
        dropout: float = 0.3,
        **kwargs,
    ):
        super().__init__(in_channels, hidden_channels, out_channels)
        if num_layers < 2:
            raise ValueError("num_layers must be >= 2")
        self.layers = nn.ModuleList(
            DirSAGEConv(in_channels if i == 0 else hidden_channels, hidden_channels)
            for i in range(num_layers)
        )
        self.norms = nn.ModuleList(
            nn.LayerNorm(hidden_channels) for _ in range(num_layers - 1)
        )
        self.classifier = nn.Linear(hidden_channels, out_channels)
        self.dropout = dropout

    def forward(self, x, edge_index=None, edge_attr=None, return_embeddings=False, **kwargs):
        if edge_index is None:
            raise ValueError("DirSAGE requires edge_index")
        h = x
        for i, layer in enumerate(self.layers[:-1]):
            h = layer(h, edge_index)
            h = F.dropout(F.relu(self.norms[i](h)), p=self.dropout, training=self.training)
        emb = h
        h = self.layers[-1](h, edge_index)
        logits = self.classifier(h)
        if return_embeddings:
            return logits, emb
        return logits
