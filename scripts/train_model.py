"""
启动训练脚本
"""

import argparse
import yaml
import os
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import torch
from data.build_graph import load_data
from models import get_model
from training import Trainer
from training.utils import set_seed
from training.evaluator import print_metrics


FULL_LABEL_NAMES = ['NONE', 'INDIVIDUAL', 'BET', 'GAMBLING', 'EXCHANGE', 'BRIDGE']


def _safe_int(value, default: int) -> int:
    """将配置值转换为 int，失败时回退到默认值。"""
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _prepare_data_for_exclude_none(data, config):
    """可选地移除 NONE 类对训练/评估的影响，并将标签重映射到连续区间。"""
    data_cfg = config.setdefault('data', {})
    exclude_none = bool(data_cfg.get('exclude_none', False))
    num_classes = _safe_int(data_cfg.get('num_classes', 6), 6)

    if not exclude_none:
        return data, FULL_LABEL_NAMES[:num_classes]

    none_label = _safe_int(data_cfg.get('none_label_id', 0), 0)
    keep_mask = data.y != none_label

    for mask_name in ('train_mask', 'val_mask', 'test_mask'):
        if hasattr(data, mask_name):
            setattr(data, mask_name, getattr(data, mask_name) & keep_mask)

    # 将剩余标签压缩到 0..K-1，保证分类头维度与标签一致。
    y = data.y.clone()
    y[y > none_label] = y[y > none_label] - 1
    data.y = y

    data_cfg['num_classes'] = max(num_classes - 1, 1)
    label_names = [name for i, name in enumerate(FULL_LABEL_NAMES) if i != none_label]
    print(f"已排除 NONE 类（label={none_label}），当前类别数: {data_cfg['num_classes']}")
    return data, label_names[:data_cfg['num_classes']]


def main():
    parser = argparse.ArgumentParser(description='模型训练')
    parser.add_argument('--config', type=str, default='config/default.yaml',
                        help='配置文件路径')
    parser.add_argument('--mini-batch', action='store_true',
                        help='使用mini-batch训练')
    parser.add_argument('--model', type=str, default=None,
                        help='可选：覆盖配置文件中的模型名，如 mlp/gcn/gat/sage/res_sage/appnp')
    args = parser.parse_args()

    # 加载配置
    with open(args.config, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    # 设置随机种子
    seed = config.get('train', {}).get('seed', 42)
    set_seed(seed)

    # 加载数据
    data_path = config.get('data', {}).get('processed_data_path', './data/processed/data.pt')
    print(f"加载数据: {data_path}")
    data = load_data(data_path)
    data, label_names = _prepare_data_for_exclude_none(data, config)
    print(f"节点数: {data.num_nodes}, 边数: {data.num_edges}, 特征维度: {data.num_features}")

    # 创建模型
    model_config = config.get('model', {})
    model_name = args.model if args.model else model_config.get('name', 'GCN')
    model_params = model_config.get('params', {})

    model = get_model(
        name=model_name,
        in_channels=data.num_features,
        out_channels=config.get('data', {}).get('num_classes', 6),
        **model_params
    )
    print(f"模型: {model_name}, 参数量: {model.count_parameters()}")

    # 创建训练器
    trainer = Trainer(model, data, config)

    # 训练
    print(f"\n开始训练...")
    use_mini_batch = args.mini_batch
    train_config = config.get('train', {})
    auto_mini_batch = bool(train_config.get('auto_mini_batch', True))
    full_batch_max_edges = _safe_int(train_config.get('full_batch_max_edges', 2_000_000), 2_000_000)

    if (
        not use_mini_batch
        and auto_mini_batch
        and trainer.device.type == 'cuda'
        and data.num_edges > full_batch_max_edges
    ):
        print(
            f"检测到大图（边数 {data.num_edges} > 阈值 {full_batch_max_edges}），"
            "在 CUDA 上自动切换为 mini-batch 训练。"
        )
        use_mini_batch = True

    try:
        train_log = trainer.train(use_mini_batch=use_mini_batch)
    except torch.cuda.OutOfMemoryError:
        if use_mini_batch:
            raise
        print("检测到 CUDA OOM，自动清理显存并切换为 mini-batch 重试...")
        torch.cuda.empty_cache()
        train_log = trainer.train(use_mini_batch=True)

    # 最终评估
    print(f"\n训练完成! 最终评估:")
    test_metrics = trainer.evaluate(data.test_mask)
    print_metrics(test_metrics, label_names=label_names)

    # 保存最终模型
    checkpoint_dir = config.get('train', {}).get('checkpoint_dir', './experiments/checkpoints')
    final_path = os.path.join(checkpoint_dir, 'final_model.pt')
    trainer.save_checkpoint(final_path)
    print(f"\n模型已保存到: {final_path}")


if __name__ == '__main__':
    main()
