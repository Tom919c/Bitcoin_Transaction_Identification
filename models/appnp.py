"""
APPNP模型
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.nn import APPNP as APPNPConv
from .base import BaseModel


class APPNP(BaseModel):
    """
    APPNP模型 (Approximate Personalized Propagation of Neural Predictions)
    """

    def __init__(
        self,
        in_channels: int,
        hidden_channels: int,
        out_channels: int,
        num_layers: int = 2,
        dropout: float = 0.5,
        K: int = 10,
        alpha: float = 0.1
    ):
        super().__init__(in_channels, hidden_channels, out_channels)
        self.num_layers = num_layers
        self.dropout = dropout

        # MLP部分
        self.lins = nn.ModuleList()
        self.lins.append(nn.Linear(in_channels, hidden_channels))
        for _ in range(num_layers - 2):
            self.lins.append(nn.Linear(hidden_channels, hidden_channels))
        self.lins.append(nn.Linear(hidden_channels, out_channels))

        # APPNP传播层
        self.prop = APPNPConv(K=K, alpha=alpha)

        self.reset_parameters()

    def reset_parameters(self):
        for lin in self.lins:
            lin.reset_parameters()
        if hasattr(self.prop, 'reset_parameters'):
            self.prop.reset_parameters()

    def forward(self, x: torch.Tensor, edge_index: torch.Tensor) -> torch.Tensor:
        # MLP变换
        for i, lin in enumerate(self.lins[:-1]):
            x = lin(x)
            x = F.relu(x)
            x = F.dropout(x, p=self.dropout, training=self.training)

        x = self.lins[-1](x)

        # APPNP传播
        x = self.prop(x, edge_index)
        return x
