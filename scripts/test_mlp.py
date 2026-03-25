"""快速验证配置模型可在当前数据和检查点上运行的脚本"""

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
    parser = argparse.ArgumentParser(description="测试模型前向推理")
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
    parser.add_argument(
        "--checkpoint",
        type=str,
        default=None,
        help="可选：模型检查点路径（.pt）"
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="可选：覆盖配置文件中的模型名（如 mlp/gcn/gat/sage/res_sage/appnp）"
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

    model_cfg = config.get("model", {})
    model_name = args.model or model_cfg.get("name", "mlp")
    model_params = dict(model_cfg.get("params", {}))
    model_params.setdefault("hidden_channels", data.num_features)
    model_params.setdefault("num_layers", 2)
    model_params.setdefault("dropout", 0.5)

    model = get_model(
        name=model_name,
        in_channels=data.num_features,
        out_channels=num_classes,
        **model_params
    ).to(device)
    print(f"模型: {model_name}")

    if args.checkpoint:
        print(f"加载检查点: {args.checkpoint}")
        checkpoint = torch.load(args.checkpoint, map_location=device)
        state_dict = checkpoint.get("model_state_dict", checkpoint) if isinstance(checkpoint, dict) else checkpoint
        try:
            model.load_state_dict(state_dict)
        except RuntimeError as e:
            raise RuntimeError(
                f"检查点与当前模型结构不匹配（当前模型: {model_name}）。"
                "请确认 checkpoint 与配置/--model 指定的模型一致。"
            ) from e
        print("检查点加载完成。")

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
