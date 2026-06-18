from __future__ import annotations

import torch
import torch.nn as nn
import torch.nn.functional as F

from .base import BaseModel
from .encoders import EdgeTemporalEncoder


def _scatter_mean(src: torch.Tensor, index: torch.Tensor, dim_size: int) -> torch.Tensor:
    """Mean aggregation via scatter, safe for empty index."""
    out = torch.zeros(dim_size, src.size(-1), dtype=src.dtype, device=src.device)
    count = torch.zeros(dim_size, 1, dtype=src.dtype, device=src.device)
    out.index_add_(0, index, src)
    ones = torch.ones(src.size(0), 1, dtype=src.dtype, device=src.device)
    count.index_add_(0, index, ones)
    return out / count.clamp_min(1.0)


class EdgeGatedConv(nn.Module):
    """Single edge-gated aggregation layer with directional in/out split.

    For directed fund-flow graphs:
      - incoming channel: src -> dst (funding received)
      - outgoing channel: dst -> src (funding sent)
    Edge gates filter heterophilic neighbors using transaction semantics.
    """

    def __init__(
        self,
        in_channels: int,
        out_channels: int,
        edge_dim: int,
        edge_hidden: int = 64,
        use_direction: bool = True,
        dropout: float = 0.1,
    ):
        super().__init__()
        self.use_direction = use_direction
        self.self_lin = nn.Linear(in_channels, out_channels)
        self.edge_encoder = EdgeTemporalEncoder(edge_dim, hidden_dim=edge_hidden, out_dim=edge_hidden, dropout=dropout)

        if use_direction:
            self.in_msg_lin = nn.Linear(in_channels, out_channels)
            self.out_msg_lin = nn.Linear(in_channels, out_channels)
            self.gate_in = nn.Linear(edge_hidden, out_channels)
            self.gate_out = nn.Linear(edge_hidden, out_channels)
            self.fusion = nn.Sequential(
                nn.Linear(out_channels * 3, out_channels),
                nn.LayerNorm(out_channels),
                nn.ReLU(),
                nn.Dropout(dropout),
            )
        else:
            self.msg_lin = nn.Linear(in_channels, out_channels)
            self.gate = nn.Linear(edge_hidden, out_channels)

    def forward(self, x: torch.Tensor, edge_index: torch.Tensor, edge_attr: torch.Tensor) -> torch.Tensor:
        src, dst = edge_index[0], edge_index[1]
        e = self.edge_encoder(edge_attr)
        h_self = self.self_lin(x)

        if self.use_direction:
            gate_in = torch.sigmoid(self.gate_in(e))
            gate_out = torch.sigmoid(self.gate_out(e))
            msg_in = gate_in * self.in_msg_lin(x[src])
            msg_out = gate_out * self.out_msg_lin(x[dst])
            h_in = _scatter_mean(msg_in, dst, x.size(0))
            h_out = _scatter_mean(msg_out, src, x.size(0))
            return self.fusion(torch.cat([h_self, h_in, h_out], dim=-1))
        else:
            gate = torch.sigmoid(self.gate(e))
            msg = gate * self.msg_lin(x[src])
            h_nbr = _scatter_mean(msg, dst, x.size(0))
            return h_self + h_nbr


class EdgeGatedSAGE(BaseModel):
    """Edge-gated GraphSAGE with directional in/out aggregation.

    Designed for heterophilic Bitcoin transaction graphs where:
    - Most neighbors are unlabeled (77-95%)
    - Same-label ratios are very low (0.4-30%)
    - Edge attributes carry transaction semantics (amount, frequency, duration, recency)
    - Fund flow direction (in/out) has different meaning
    """

    def __init__(
        self,
        in_channels: int,
        hidden_channels: int,
        out_channels: int,
        edge_dim: int,
        num_layers: int = 3,
        dropout: float = 0.3,
        edge_hidden: int = 64,
        use_direction: bool = True,
        **kwargs,
    ):
        super().__init__(in_channels, hidden_channels, out_channels)
        if num_layers < 2:
            raise ValueError("num_layers must be >= 2")
        self.layers = nn.ModuleList()
        self.norms = nn.ModuleList()
        for i in range(num_layers):
            self.layers.append(
                EdgeGatedConv(
                    in_channels if i == 0 else hidden_channels,
                    hidden_channels,
                    edge_dim,
                    edge_hidden=edge_hidden,
                    use_direction=use_direction,
                    dropout=dropout,
                )
            )
            if i < num_layers - 1:
                self.norms.append(nn.LayerNorm(hidden_channels))
        self.classifier = nn.Linear(hidden_channels, out_channels)
        self.dropout = dropout

    def forward(self, x, edge_index=None, edge_attr=None, return_embeddings=False, **kwargs):
        if edge_index is None or edge_attr is None:
            raise ValueError("EdgeGatedSAGE requires edge_index and edge_attr")
        h = x
        for i, layer in enumerate(self.layers[:-1]):
            h = layer(h, edge_index, edge_attr)
            h = F.dropout(F.relu(self.norms[i](h)), p=self.dropout, training=self.training)
        emb = h
        h = self.layers[-1](h, edge_index, edge_attr)
        logits = self.classifier(h)
        if return_embeddings:
            return logits, emb
        return logits
