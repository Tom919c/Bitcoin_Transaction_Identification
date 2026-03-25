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
        dropout: float = 0.3
    ):
        super().__init__(in_channels, hidden_channels, out_channels)
        if num_layers != 3:
            raise ValueError("ResGraphSAGE按规范固定为3层SAGEConv")

        self.num_layers = num_layers
        self.dropout = dropout

        # 共享残差路径: X -> X_res
        self.input_proj = nn.Linear(in_channels, hidden_channels)
        self.conv1 = SAGEConv(in_channels, hidden_channels)
        self.conv2 = SAGEConv(hidden_channels, hidden_channels)
        self.conv3 = SAGEConv(hidden_channels, out_channels)
        self.norm1 = nn.LayerNorm(hidden_channels)
        self.norm2 = nn.LayerNorm(hidden_channels)

        self.reset_parameters()

    def reset_parameters(self):
        self.input_proj.reset_parameters()
        self.conv1.reset_parameters()
        self.conv2.reset_parameters()
        self.conv3.reset_parameters()
        self.norm1.reset_parameters()
        self.norm2.reset_parameters()

    def forward(self, x: torch.Tensor, edge_index: torch.Tensor) -> torch.Tensor:
        x_res = self.input_proj(x)

        # 第1层：SAGEConv -> LN -> ReLU -> +X_res -> Dropout
        h = self.conv1(x, edge_index)
        h = self.norm1(h)
        h = F.relu(h)
        h = h + x_res
        h = F.dropout(h, p=self.dropout, training=self.training)

        # 第2层：SAGEConv -> LN -> ReLU -> +X_res -> Dropout
        h = self.conv2(h, edge_index)
        h = self.norm2(h)
        h = F.relu(h)
        h = h + x_res
        h = F.dropout(h, p=self.dropout, training=self.training)

        # 第3层：仅输出logits，不加残差
        out = self.conv3(h, edge_index)
        return out
