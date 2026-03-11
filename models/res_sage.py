"""
残差GraphSAGE模型
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.nn import SAGEConv
from .base import BaseModel


class ResGraphSAGE(BaseModel):
    """
    带残差连接的GraphSAGE模型
    """

    def __init__(
        self,
        in_channels: int,
        hidden_channels: int,
        out_channels: int,
        num_layers: int = 3,
        dropout: float = 0.5
    ):
        super().__init__(in_channels, hidden_channels, out_channels)
        self.num_layers = num_layers
        self.dropout = dropout

        self.convs = nn.ModuleList()
        self.norms = nn.ModuleList()

        # 输入投影层
        self.input_proj = nn.Linear(in_channels, hidden_channels)

        # 隐藏层（带残差）
        for _ in range(num_layers - 1):
            self.convs.append(SAGEConv(hidden_channels, hidden_channels))
            self.norms.append(nn.LayerNorm(hidden_channels))

        # 输出层
        self.output_proj = nn.Linear(hidden_channels, out_channels)

        self.reset_parameters()

    def reset_parameters(self):
        self.input_proj.reset_parameters()
        self.output_proj.reset_parameters()
        for conv in self.convs:
            conv.reset_parameters()
        for norm in self.norms:
            norm.reset_parameters()

    def forward(self, x: torch.Tensor, edge_index: torch.Tensor) -> torch.Tensor:
        # 输入投影
        x = self.input_proj(x)
        x = F.relu(x)
        x = F.dropout(x, p=self.dropout, training=self.training)

        # 残差层
        for conv, norm in zip(self.convs, self.norms):
            residual = x
            x = conv(x, edge_index)
            x = norm(x)
            x = F.relu(x)
            x = F.dropout(x, p=self.dropout, training=self.training)
            x = x + residual  # 残差连接

        # 输出投影
        x = self.output_proj(x)
        return x
