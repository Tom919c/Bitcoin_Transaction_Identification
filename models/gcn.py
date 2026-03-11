"""
GCN模型
"""

import torch
import torch.nn.functional as F
from torch_geometric.nn import GCNConv
from .base import BaseModel


class GCN(BaseModel):
    """
    图卷积网络 (Graph Convolutional Network)
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

        self.convs = torch.nn.ModuleList()

        # 输入层
        self.convs.append(GCNConv(in_channels, hidden_channels))

        # 隐藏层
        for _ in range(num_layers - 2):
            self.convs.append(GCNConv(hidden_channels, hidden_channels))

        # 输出层
        self.convs.append(GCNConv(hidden_channels, out_channels))

        self.reset_parameters()

    def reset_parameters(self):
        for conv in self.convs:
            conv.reset_parameters()

    def forward(self, x: torch.Tensor, edge_index: torch.Tensor) -> torch.Tensor:
        for i, conv in enumerate(self.convs[:-1]):
            x = conv(x, edge_index)
            x = F.relu(x)
            x = F.dropout(x, p=self.dropout, training=self.training)

        x = self.convs[-1](x, edge_index)
        return x
