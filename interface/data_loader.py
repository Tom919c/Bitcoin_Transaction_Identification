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
    loaded = torch.load(data_path, map_location='cpu')
    if isinstance(loaded, Data):
        return loaded

    if not isinstance(loaded, dict):
        raise TypeError(f"不支持的数据格式: {type(loaded)}")

    required = {'x', 'edge_index'}
    missing = required - set(loaded.keys())
    if missing:
        raise KeyError(f"data.pt 缺少必要字段: {sorted(missing)}")

    x = loaded['x'] if torch.is_tensor(loaded['x']) else torch.tensor(loaded['x'], dtype=torch.float32)
    edge_index = loaded['edge_index'] if torch.is_tensor(loaded['edge_index']) else torch.tensor(loaded['edge_index'], dtype=torch.long)

    y = loaded.get('y')
    if y is None:
        y = torch.zeros(x.shape[0], dtype=torch.long)
    elif not torch.is_tensor(y):
        y = torch.tensor(y, dtype=torch.long)

    train_mask = loaded.get('train_mask')
    if train_mask is None:
        train_mask = torch.zeros(x.shape[0], dtype=torch.bool)
    elif not torch.is_tensor(train_mask):
        train_mask = torch.tensor(train_mask, dtype=torch.bool)

    val_mask = loaded.get('val_mask')
    if val_mask is None:
        val_mask = torch.zeros(x.shape[0], dtype=torch.bool)
    elif not torch.is_tensor(val_mask):
        val_mask = torch.tensor(val_mask, dtype=torch.bool)

    test_mask = loaded.get('test_mask')
    if test_mask is None:
        test_mask = torch.zeros(x.shape[0], dtype=torch.bool)
    elif not torch.is_tensor(test_mask):
        test_mask = torch.tensor(test_mask, dtype=torch.bool)

    edge_attr = loaded.get('edge_attr')
    if edge_attr is None:
        edge_attr = torch.empty((edge_index.shape[1], 0), dtype=torch.float32)
    elif not torch.is_tensor(edge_attr):
        edge_attr = torch.tensor(edge_attr, dtype=torch.float32)

    data = Data(
        x=x,
        edge_index=edge_index,
        edge_attr=edge_attr,
        y=y,
        train_mask=train_mask,
        val_mask=val_mask,
        test_mask=test_mask
    )

    if 'feature_columns' in loaded:
        data.feature_columns = list(loaded['feature_columns'])
    if 'edge_attr_columns' in loaded:
        data.edge_attr_columns = list(loaded['edge_attr_columns'])

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
