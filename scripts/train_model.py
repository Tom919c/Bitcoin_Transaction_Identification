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
from data.utils import LABEL_MAP
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

    # APPNP与mini-batch参数一致性检查
    train_config = config.get('train', {})
    if args.mini_batch and str(model_name).lower() == 'appnp' and bool(train_config.get('appnp_full_batch_only', True)):
        print("检测到 APPNP + mini-batch 组合，已自动切换为全图训练")
        args.mini_batch = False

    # 打印评估口径
    eval_labels = config.get('eval', {}).get('metric_labels', config.get('preprocessing', {}).get('target_labels', []))
    valid_eval_labels = [name for name in eval_labels if name in LABEL_MAP]
    if valid_eval_labels:
        print(f"评估类别顺序: {', '.join(valid_eval_labels)}")
    else:
        print("评估类别顺序: NONE, INDIVIDUAL, BET, GAMBLING, EXCHANGE, BRIDGE")

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

    # 默认加载最佳模型进行最终评估，避免最后一轮退化影响结果
    checkpoint_dir = config.get('train', {}).get('checkpoint_dir', './experiments/checkpoints')
    best_path = os.path.join(checkpoint_dir, 'best_model.pt')
    if os.path.exists(best_path):
        trainer.load_checkpoint(best_path)
        print(f"\n已加载最佳模型: {best_path}")
    else:
        print(f"\n警告: 未找到最佳模型，将使用当前模型评估")

    # 最终评估
    print(f"\n训练完成! 测试集评估:")
    test_metrics = trainer.evaluate(data.test_mask)
    print_metrics(test_metrics, label_names=test_metrics.get('metric_label_names'))

    # 保存最终模型
    final_path = os.path.join(checkpoint_dir, 'final_model.pt')
    trainer.save_checkpoint(final_path)
    print(f"\n模型已保存到: {final_path}")


if __name__ == '__main__':
    main()
