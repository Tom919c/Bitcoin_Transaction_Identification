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


def main():
    parser = argparse.ArgumentParser(description='模型训练')
    parser.add_argument('--config', type=str, default='config/default.yaml',
                        help='配置文件路径')
    parser.add_argument('--mini-batch', action='store_true',
                        help='使用mini-batch训练')
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
    print(f"节点数: {data.num_nodes}, 边数: {data.num_edges}, 特征维度: {data.num_features}")

    # 创建模型
    model_config = config.get('model', {})
    model_name = model_config.get('name', 'GCN')
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
    train_log = trainer.train(use_mini_batch=args.mini_batch)

    # 最终评估
    print(f"\n训练完成! 最终评估:")
    test_metrics = trainer.evaluate(data.test_mask)
    print_metrics(test_metrics)

    # 保存最终模型
    checkpoint_dir = config.get('train', {}).get('checkpoint_dir', './experiments/checkpoints')
    final_path = os.path.join(checkpoint_dir, 'final_model.pt')
    trainer.save_checkpoint(final_path)
    print(f"\n模型已保存到: {final_path}")


if __name__ == '__main__':
    main()
