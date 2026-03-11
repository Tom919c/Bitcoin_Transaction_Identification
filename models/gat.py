"""
GAT模型
"""

import torch
import torch.nn.functional as F
from torch_geometric.nn import GATConv
from .base import BaseModel


class GAT(BaseModel):
    """
    图注意力网络 (Graph Attention Network)
    """

    def __init__(
        self,
        in_channels: int,
        hidden_channels: int,
        out_channels: int,
        num_layers: int = 2,
        dropout: float = 0.5,
        heads: int = 8
    ):
        super().__init__(in_channels, hidden_channels, out_channels)
        self.num_layers = num_layers
        self.dropout = dropout
        self.heads = heads

        self.convs = torch.nn.ModuleList()

        # 输入层
        self.convs.append(GATConv(in_channels, hidden_channels, heads=heads, dropout=dropout))

        # 隐藏层
        for _ in range(num_layers - 2):
            self.convs.append(GATConv(hidden_channels * heads, hidden_channels, heads=heads, dropout=dropout))

        # 输出层（单头）
        self.convs.append(GATConv(hidden_channels * heads, out_channels, heads=1, concat=False, dropout=dropout))

        self.reset_parameters()

    def reset_parameters(self):
        for conv in self.convs:
            conv.reset_parameters()

    def forward(self, x: torch.Tensor, edge_index: torch.Tensor) -> torch.Tensor:
        for i, conv in enumerate(self.convs[:-1]):
            x = conv(x, edge_index)
            x = F.elu(x)
            x = F.dropout(x, p=self.dropout, training=self.training)

        x = self.convs[-1](x, edge_index)
        return x
