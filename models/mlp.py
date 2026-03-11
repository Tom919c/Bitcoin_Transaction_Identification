"""
MLP模型
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from .base import BaseModel


class MLP(BaseModel):
    """
    多层感知机模型（不使用图结构）
    """

    def __init__(
        self,
        in_channels: int,
        hidden_channels: int,
        out_channels: int,
        num_layers: int = 2,
        dropout: float = 0.5
    ):
        super().__init__(in_channels, hidden_channels, out_channels)
        self.num_layers = num_layers
        self.dropout = dropout

        self.layers = nn.ModuleList()

        # 输入层
        self.layers.append(nn.Linear(in_channels, hidden_channels))

        # 隐藏层
        for _ in range(num_layers - 2):
            self.layers.append(nn.Linear(hidden_channels, hidden_channels))

        # 输出层
        self.layers.append(nn.Linear(hidden_channels, out_channels))

        self.reset_parameters()

    def reset_parameters(self):
        for layer in self.layers:
            layer.reset_parameters()

    def forward(self, x: torch.Tensor, edge_index: torch.Tensor = None) -> torch.Tensor:
        """
        前向传播（忽略edge_index，仅使用节点特征）
        """
        for i, layer in enumerate(self.layers[:-1]):
            x = layer(x)
            x = F.relu(x)
            x = F.dropout(x, p=self.dropout, training=self.training)

        x = self.layers[-1](x)
        return x
