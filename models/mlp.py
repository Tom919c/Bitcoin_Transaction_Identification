import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Callable, Optional

from .base import BaseModel


class MLP(BaseModel):
    """多层感知机，用于在无图结构时对节点特征做分类"""

    def __init__(
        self,
        in_channels: int,
        hidden_channels: int,
        out_channels: int,
        num_layers: int = 2,
        dropout: float = 0.5,
        activation: str = 'relu',
        use_batch_norm: bool = False
    ) -> None:
        if num_layers < 1:
            raise ValueError("num_layers must be at least 1 for MLP")

        super().__init__(in_channels, hidden_channels, out_channels)
        self.num_layers = num_layers
        self.dropout = dropout
        self.activation = self._resolve_activation(activation)
        self.use_batch_norm = use_batch_norm

        self.hidden_layers = self._build_hidden_layers()
        self.out_layer = nn.Linear(hidden_channels, out_channels)
        self.norms = nn.ModuleList(
            nn.BatchNorm1d(hidden_channels) for _ in range(num_layers)
        ) if use_batch_norm else None

        self.reset_parameters()

    def _resolve_activation(self, name: str) -> Callable[[torch.Tensor], torch.Tensor]:
        name = name.lower()
        activations = {
            'relu': F.relu,
            'gelu': F.gelu,
            'elu': F.elu,
            'selu': F.selu
        }
        if name not in activations:
            raise ValueError(f"Unsupported activation '{name}'. Available: {list(activations.keys())}")
        return activations[name]

    def _build_hidden_layers(self) -> nn.ModuleList:
        layers = nn.ModuleList()
        input_dim = self.in_channels
        for _ in range(self.num_layers):
            layers.append(nn.Linear(input_dim, self.hidden_channels))
            input_dim = self.hidden_channels
        return layers

    def reset_parameters(self) -> None:
        for layer in list(self.hidden_layers) + [self.out_layer]:
            if isinstance(layer, nn.Linear):
                nn.init.kaiming_uniform_(layer.weight, nonlinearity='relu')
                if layer.bias is not None:
                    nn.init.zeros_(layer.bias)
        if self.norms is not None:
            for norm in self.norms:
                norm.reset_parameters()

    def forward(
        self,
        x: torch.Tensor,
        edge_index: Optional[torch.Tensor] = None
    ) -> torch.Tensor:
        del edge_index  # MLP不依赖图结构，只需节点特征

        for idx, layer in enumerate(self.hidden_layers):
            x = layer(x)
            if self.use_batch_norm and self.norms is not None:
                x = self.norms[idx](x)
            x = self.activation(x)
            x = F.dropout(x, p=self.dropout, training=self.training)

        x = self.out_layer(x)
        return x

    def __repr__(self) -> str:
        return (
            "MLP("
            f"in_channels={self.in_channels}, "
            f"hidden_channels={self.hidden_channels}, "
            f"out_channels={self.out_channels}, "
            f"num_layers={self.num_layers}, "
            f"dropout={self.dropout}, "
            f"batch_norm={self.use_batch_norm}"
            ")"
        )