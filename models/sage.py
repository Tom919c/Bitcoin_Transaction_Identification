"""
GraphSAGE模型
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.nn import SAGEConv
from .base import BaseModel


class GraphSAGE(BaseModel):
    """
    GraphSAGE模型
    """

    def __init__(
        self,
        in_channels: int,
        hidden_channels: int,
        out_channels: int,
        num_layers: int = 3,
        dropout: float = 0.3
    ):
        super().__init__(in_channels, hidden_channels, out_channels)
        if num_layers != 3:
            raise ValueError("GraphSAGE按规范固定为3层SAGEConv")

        self.num_layers = num_layers
        self.dropout = dropout

        self.convs = nn.ModuleList([
            SAGEConv(in_channels, hidden_channels),
            SAGEConv(hidden_channels, hidden_channels),
            SAGEConv(hidden_channels, out_channels),
        ])
        self.norms = nn.ModuleList([
            nn.LayerNorm(hidden_channels),
            nn.LayerNorm(hidden_channels),
        ])

        self.reset_parameters()

    def reset_parameters(self):
        for conv in self.convs:
            conv.reset_parameters()
        for norm in self.norms:
            norm.reset_parameters()

    def forward(self, x: torch.Tensor, edge_index: torch.Tensor) -> torch.Tensor:
        for conv, norm in zip(self.convs[:-1], self.norms):
            x = conv(x, edge_index)
            x = norm(x)
            x = F.relu(x)
            x = F.dropout(x, p=self.dropout, training=self.training)

        x = self.convs[-1](x, edge_index)
        return x
