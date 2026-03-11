"""
数据和模型加载器
"""

import torch
from torch_geometric.data import Data
from typing import Dict, Type
import torch.nn as nn


def load_data(data_path: str) -> Data:
    """
    加载data.pt文件

    Args:
        data_path: data.pt文件路径

    Returns:
        PyG Data对象
    """
    data = torch.load(data_path, map_location='cpu')
    return data


def load_model(
    model_class: Type[nn.Module],
    model_path: str,
    config: Dict
) -> nn.Module:
    """
    加载训练好的模型

    Args:
        model_class: 模型类
        model_path: 模型权重文件路径
        config: 模型配置

    Returns:
        加载权重后的模型
    """
    model_params = config.get('model', {}).get('params', {})
    data_config = config.get('data', {})

    # 需要从data获取in_channels，这里假设已知
    in_channels = config.get('in_channels', 64)  # 需要根据实际数据设置
    out_channels = data_config.get('num_classes', 6)

    model = model_class(
        in_channels=in_channels,
        out_channels=out_channels,
        **model_params
    )

    checkpoint = torch.load(model_path, map_location='cpu')
    if 'model_state_dict' in checkpoint:
        model.load_state_dict(checkpoint['model_state_dict'])
    else:
        model.load_state_dict(checkpoint)

    model.eval()
    return model


@torch.no_grad()
def predict(model: nn.Module, data: Data) -> Dict:
    """
    使用模型进行预测

    Args:
        model: 训练好的模型
        data: PyG Data对象

    Returns:
        预测结果字典
    """
    model.eval()
    out = model(data.x, data.edge_index)
    probs = torch.softmax(out, dim=1)
    preds = out.argmax(dim=1)

    return {
        'predictions': preds,
        'probabilities': probs,
        'logits': out
    }
