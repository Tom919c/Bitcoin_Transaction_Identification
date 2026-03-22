"""快速验证 MLP 模型可在当前配置和数据上运行的脚本"""

import argparse
import os
import sys
from typing import Any, Dict

import torch
import yaml
from torch_geometric.data import Data

# 将项目根目录加入路径，保证脚本可直接运行
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.build_graph import load_data
from models import get_model
from training.evaluator import compute_metrics, print_metrics
from training.utils import set_seed


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="测试 MLP 前向推理")
    parser.add_argument(
        "--config",
        type=str,
        default="config/default.yaml",
        help="配置文件路径"
    )
    parser.add_argument(
        "--device",
        type=str,
        default=None,
        help="运行设备，默认自动检测"
    )
    return parser.parse_args()


def load_config(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def main() -> None:
    args = parse_args()
    config = load_config(args.config)

    seed = config.get("train", {}).get("seed", 42)
    set_seed(seed)

    device = torch.device(
        args.device
        if args.device is not None
        else config.get("train", {}).get("device", "cuda" if torch.cuda.is_available() else "cpu")
    )

    data_path = config.get("data", {}).get("processed_data_path", "./data/processed/data.pt")
    print(f"加载数据: {data_path}")
    raw_data = load_data(data_path)
    if isinstance(raw_data, dict):
        print("检测到 data.pt 存储为字典，已在内存中临时转换为 PyG Data 对象。")
        data = Data(**raw_data)
    else:
        data = raw_data
    data = data.to(device)
    num_classes = config.get("data", {}).get("num_classes", 6)

    model_params = dict(config.get("model", {}).get("params", {}))
    model_params.setdefault("hidden_channels", data.num_features)
    model_params.setdefault("num_layers", 2)
    model_params.setdefault("dropout", 0.5)

    model = get_model(
        name="mlp",
        in_channels=data.num_features,
        out_channels=num_classes,
        **model_params
    ).to(device)

    model.eval()
    with torch.no_grad():
        logits = model(data.x, data.edge_index)

    print("\n模型信息:")
    print(model)
    print("\n输出张量: ")
    print(f"形状: {tuple(logits.shape)} | 设备: {logits.device}")

    if hasattr(data, "train_mask") and hasattr(data, "test_mask"):
        train_metrics = compute_metrics(logits, data.y, data.train_mask, num_classes)
        test_metrics = compute_metrics(logits, data.y, data.test_mask, num_classes)
        print("\n训练集指标:")
        print_metrics(train_metrics)
        print("\n测试集指标:")
        print_metrics(test_metrics)
    else:
        print("未检测到 train/test 掩码，跳过指标计算。")

if __name__ == "__main__":
    main()
