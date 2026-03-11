"""
模型定义模块

提供各种图神经网络模型
"""

from .mlp import MLP
from .gcn import GCN
from .gat import GAT
from .sage import GraphSAGE
from .res_sage import ResGraphSAGE
from .appnp import APPNP

__all__ = ['MLP', 'GCN', 'GAT', 'GraphSAGE', 'ResGraphSAGE', 'APPNP']

# 模型注册表，便于动态加载
MODEL_REGISTRY = {
    'mlp': MLP,
    'gcn': GCN,
    'gat': GAT,
    'sage': GraphSAGE,
    'res_sage': ResGraphSAGE,
    'resgraphsage': ResGraphSAGE,
    'appnp': APPNP
}


def get_model(name: str, **kwargs):
    """
    根据名称获取模型类

    Args:
        name: 模型名称
        **kwargs: 模型参数

    Returns:
        模型实例
    """
    name_lower = name.lower()
    if name_lower not in MODEL_REGISTRY:
        raise ValueError(f"未知模型: {name}. 可用模型: {list(MODEL_REGISTRY.keys())}")
    return MODEL_REGISTRY[name_lower](**kwargs)
