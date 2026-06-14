from __future__ import annotations

import torch
import torch.nn as nn
import torch.nn.functional as F

from .base import BaseModel
from .encoders import EdgeTemporalEncoder


def scatter_mean(src: torch.Tensor, index: torch.Tensor, dim_size: int) -> torch.Tensor:
    out = torch.zeros(dim_size, src.size(-1), dtype=src.dtype, device=src.device)
    count = torch.zeros(dim_size, 1, dtype=src.dtype, device=src.device)
    out.index_add_(0, index, src)
    ones = torch.ones(src.size(0), 1, dtype=src.dtype, device=src.device)
    count.index_add_(0, index, ones)
    return out / count.clamp_min(1.0)


class DirectionalEdgeGateLayer(nn.Module):
    """Directional edge-gated aggregation for directed fund-flow graphs.

    For each directed edge src -> dst:
      - incoming channel aggregates src messages to dst
      - outgoing channel aggregates dst messages to src, representing outgoing counterpart context
    """

    def __init__(self, in_channels: int, out_channels: int, edge_dim: int, edge_hidden: int = 64, dropout: float = 0.1):
        super().__init__()
        self.self_lin = nn.Linear(in_channels, out_channels)
        self.in_lin = nn.Linear(in_channels, out_channels)
        self.out_lin = nn.Linear(in_channels, out_channels)
        self.edge_encoder = EdgeTemporalEncoder(edge_dim, hidden_dim=edge_hidden, out_dim=edge_hidden, dropout=dropout)
        self.gate_in = nn.Linear(edge_hidden, out_channels)
        self.gate_out = nn.Linear(edge_hidden, out_channels)
        self.fusion = nn.Sequential(
            nn.Linear(out_channels * 3, out_channels),
            nn.LayerNorm(out_channels),
            nn.ReLU(),
            nn.Dropout(dropout),
        )

    def forward(self, x: torch.Tensor, edge_index: torch.Tensor, edge_attr: torch.Tensor, return_gates: bool = False):
        src, dst = edge_index[0], edge_index[1]
        e = self.edge_encoder(edge_attr)
        gate_in = torch.sigmoid(self.gate_in(e))
        gate_out = torch.sigmoid(self.gate_out(e))
        msg_in = gate_in * self.in_lin(x[src])
        msg_out = gate_out * self.out_lin(x[dst])
        h_in = scatter_mean(msg_in, dst, x.size(0))
        h_out = scatter_mean(msg_out, src, x.size(0))
        h_self = self.self_lin(x)
        h = self.fusion(torch.cat([h_self, h_in, h_out], dim=-1))
        if return_gates:
            return h, {'gate_in': gate_in.detach(), 'gate_out': gate_out.detach()}
        return h


class ETDSAGE(BaseModel):
    """Edge-Temporal Directional GraphSAGE-like model.

    This is the main research model skeleton: it separately aggregates incoming and outgoing
    transaction neighbors using edge-time gates.
    """

    def __init__(self, in_channels: int, hidden_channels: int, out_channels: int, edge_dim: int, num_layers: int = 3, dropout: float = 0.3, edge_hidden: int = 64, **kwargs):
        super().__init__(in_channels, hidden_channels, out_channels)
        if num_layers < 1:
            raise ValueError('num_layers must be >= 1')
        self.layers = nn.ModuleList()
        self.layers.append(DirectionalEdgeGateLayer(in_channels, hidden_channels, edge_dim, edge_hidden=edge_hidden, dropout=dropout))
        for _ in range(num_layers - 1):
            self.layers.append(DirectionalEdgeGateLayer(hidden_channels, hidden_channels, edge_dim, edge_hidden=edge_hidden, dropout=dropout))
        self.classifier = nn.Linear(hidden_channels, out_channels)
        self.dropout = dropout

    def forward(self, x, edge_index=None, edge_attr=None, return_embeddings=False, return_explanations=False, **kwargs):
        if edge_index is None or edge_attr is None:
            raise ValueError('ETDSAGE requires edge_index and edge_attr')
        h = x
        explanations = []
        for layer in self.layers:
            if return_explanations:
                h, gates = layer(h, edge_index, edge_attr, return_gates=True)
                explanations.append(gates)
            else:
                h = layer(h, edge_index, edge_attr)
            h = F.dropout(h, p=self.dropout, training=self.training)
        logits = self.classifier(h)
        if return_embeddings and return_explanations:
            return logits, h, explanations
        if return_embeddings:
            return logits, h
        if return_explanations:
            return logits, explanations
        return logits
