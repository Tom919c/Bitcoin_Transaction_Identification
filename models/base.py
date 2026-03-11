"""
模型基类
"""

import torch
import torch.nn as nn
from abc import ABC, abstractmethod


class BaseModel(nn.Module, ABC):
    """
    所有模型的基类

    所有模型应继承此类并实现forward方法
    forward方法应返回未经Softmax的logits
    """

    def __init__(self, in_channels: int, hidden_channels: int, out_channels: int):
        super().__init__()
        self.in_channels = in_channels
        self.hidden_channels = hidden_channels
        self.out_channels = out_channels

    @abstractmethod
    def forward(self, x: torch.Tensor, edge_index: torch.Tensor) -> torch.Tensor:
        """
        前向传播

        Args:
            x: 节点特征矩阵 [N, in_channels]
            edge_index: 边索引 [2, E]

        Returns:
            logits: 未经Softmax的输出 [N, out_channels]
        """
        pass

    def reset_parameters(self):
        """重置模型参数"""
        for module in self.modules():
            if hasattr(module, 'reset_parameters'):
                module.reset_parameters()

    def count_parameters(self) -> int:
        """统计可训练参数数量"""
        return sum(p.numel() for p in self.parameters() if p.requires_grad)
