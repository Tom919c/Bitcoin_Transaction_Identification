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
        dropout: float = 0.5,
        class_logit_bias: list[float] | None = None
    ):
        super().__init__(in_channels, hidden_channels, out_channels)
        if num_layers < 1:
            raise ValueError("num_layers 必须 >= 1")

        self.num_layers = num_layers
        self.dropout = dropout

        if class_logit_bias is None:
            self.register_buffer('class_logit_bias', torch.zeros(out_channels))
        else:
            bias = torch.tensor(class_logit_bias, dtype=torch.float32)
            if bias.numel() != out_channels:
                raise ValueError("class_logit_bias 长度必须等于 out_channels")
            self.register_buffer('class_logit_bias', bias)

        self.convs = torch.nn.ModuleList()

        if num_layers == 1:
            # 单层GCN直接映射到类别空间。
            self.convs.append(GCNConv(in_channels, out_channels))
        else:
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

    @staticmethod
    def _parse_inputs(
        x: torch.Tensor,
        edge_index: torch.Tensor
    ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor | None]:
        """
        兼容两类输入：
        1) 常规张量输入: x + edge_index
        2) data.pt 字典输入: x 为包含 x/edge_index/edge_attr 的 dict
        """
        edge_weight = None

        if isinstance(x, dict):
            data_dict = x
            x = data_dict['x']
            edge_index = data_dict['edge_index']

            edge_attr = data_dict.get('edge_attr')
            if edge_attr is not None:
                if edge_attr.dim() == 1:
                    edge_weight = edge_attr
                elif edge_attr.dim() == 2:
                    if edge_attr.size(1) == 1:
                        edge_weight = edge_attr.view(-1)
                    else:
                        # 多维边特征压缩为标量边权重，避免完全丢失边属性信息。
                        edge_weight = edge_attr.abs().mean(dim=1)

                if edge_weight is not None:
                    edge_weight = edge_weight.float()
                    edge_weight = edge_weight / (edge_weight.mean() + 1e-12)
                    edge_weight = edge_weight.clamp(min=0.0)

        if edge_index is None:
            raise ValueError("edge_index 不能为空")

        return x, edge_index, edge_weight

    def forward(self, x: torch.Tensor, edge_index: torch.Tensor) -> torch.Tensor:
        x, edge_index, edge_weight = self._parse_inputs(x, edge_index)

        for conv in self.convs[:-1]:
            x = conv(x, edge_index, edge_weight=edge_weight)
            x = F.relu(x)
            x = F.dropout(x, p=self.dropout, training=self.training)

        x = self.convs[-1](x, edge_index, edge_weight=edge_weight)
        x = x + self.class_logit_bias.to(x.device)
        return x
