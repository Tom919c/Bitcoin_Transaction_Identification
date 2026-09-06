from __future__ import annotations

import torch
import torch.nn as nn
import torch.nn.functional as F

from btcaml.models.base import BaseModel
from btcaml.models.edge_sage import EdgeGatedSAGE


class DGResEGS(BaseModel):
    """EGS backbone + node-only self residual with an optional node-level scalar gate.

    Sprint-1 pre-registered variants:
      - ``variant='a1'``: h = LN(s + g)                          (self residual)
      - ``variant='a2'``: h = LN(s + alpha * g), alpha in (0,1)  (gated residual)
    A3 = A2 trained with the three-environment V-REx penalty (handled by the
    campaign runner, not by the model).

    The gate input is strictly u = [LN(s) | LN(g) | |LN(s)-LN(g)|]; it sees no
    labels, class frequencies, test statistics, absolute times or raw temporal
    edge features. ``g`` is the EGS representation before the classifier head,
    obtained by composing the frozen backbone layers (EdgeGatedSAGE's own
    ``return_embeddings`` exposes the penultimate layer instead).
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
        variant: str = "a2",
        **kwargs,
    ):
        super().__init__(in_channels, hidden_channels, out_channels)
        if variant not in {"a1", "a2"}:
            raise ValueError(f"Unknown DGResEGS variant: {variant}")
        self.variant = variant
        self.backbone = EdgeGatedSAGE(
            in_channels=in_channels,
            hidden_channels=hidden_channels,
            out_channels=out_channels,
            edge_dim=edge_dim,
            num_layers=num_layers,
            dropout=dropout,
            edge_hidden=edge_hidden,
            use_direction=use_direction,
        )
        self.self_branch = nn.Sequential(
            nn.Linear(in_channels, hidden_channels),
            nn.GELU(),
            nn.Linear(hidden_channels, hidden_channels),
        )
        self.norm_s = nn.LayerNorm(hidden_channels)
        self.norm_g = nn.LayerNorm(hidden_channels)
        self.norm_out = nn.LayerNorm(hidden_channels)
        if variant == "a2":
            self.gate = nn.Sequential(
                nn.Linear(hidden_channels * 3, hidden_channels),
                nn.GELU(),
                nn.Linear(hidden_channels, 1),
            )
        self.head = nn.Linear(hidden_channels, out_channels)
        self.last_alpha: torch.Tensor | None = None

    def backbone_features(self, x, edge_index, edge_attr) -> torch.Tensor:
        gnn = self.backbone
        h = x
        for i, layer in enumerate(gnn.layers[:-1]):
            h = layer(h, edge_index, edge_attr)
            h = F.dropout(F.relu(gnn.norms[i](h)), p=gnn.dropout, training=self.training)
        return gnn.layers[-1](h, edge_index, edge_attr)

    def forward(self, x, edge_index=None, edge_attr=None, return_embeddings=False, **kwargs):
        if edge_index is None or edge_attr is None:
            raise ValueError("DGResEGS requires edge_index and edge_attr")
        g = self.backbone_features(x, edge_index, edge_attr)
        s = self.self_branch(x)
        if self.variant == "a1":
            h = self.norm_out(s + g)
            self.last_alpha = None
        else:
            u = torch.cat([self.norm_s(s), self.norm_g(g), (self.norm_s(s) - self.norm_g(g)).abs()], dim=-1)
            alpha = torch.sigmoid(self.gate(u))
            self.last_alpha = alpha.detach()
            h = self.norm_out(s + alpha * g)
        logits = self.head(h)
        if return_embeddings:
            return logits, h
        return logits
