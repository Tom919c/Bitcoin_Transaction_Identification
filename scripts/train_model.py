"""
启动训练脚本
"""

import argparse
import yaml
import os
import sys
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import torch
from data.build_graph import load_data
from models import get_model
from training import Trainer
from training.utils import set_seed
from training.evaluator import print_metrics


def setup_wandb(config: dict, model, args):
    """根据配置初始化wandb，未启用时返回None。"""
    wandb_config = config.get('wandb', {})
    enabled = bool(wandb_config.get('enabled', False))
    mode = str(wandb_config.get('mode', 'online'))
    if not enabled or mode == 'disabled':
        return None

    try:
        import wandb
    except ImportError as exc:
        raise ImportError("已启用wandb但未安装，请先执行: pip install wandb") from exc

    train_cfg = config.get('train', {})
    model_cfg = config.get('model', {})
    default_run_name = f"{model_cfg.get('name', 'model')}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

    run = wandb.init(
        project=wandb_config.get('project', 'bitcoin-transaction-identification'),
        entity=wandb_config.get('entity'),
        name=wandb_config.get('run_name') or default_run_name,
        mode=mode,
        config={
            'data_path': config.get('data', {}).get('processed_data_path'),
            'model_name': model_cfg.get('name'),
            'model_params': model_cfg.get('params', {}),
            'train': train_cfg,
            'mini_batch': bool(args.mini_batch)
        }
    )

    if bool(wandb_config.get('watch_model', False)):
        wandb.watch(model, log='gradients', log_freq=100)

    return run


def main():
    parser = argparse.ArgumentParser(description='模型训练')
    parser.add_argument('--config', type=str, default='config/default.yaml',
                        help='配置文件路径')
    parser.add_argument('--mini-batch', action='store_true',
                        help='使用mini-batch训练')
    parser.add_argument('--resume-checkpoint', type=str, default=None,
                        help='断点续训的checkpoint路径，未指定则从配置读取 train.resume_from_checkpoint')
    args = parser.parse_args()

    # 加载配置
    with open(args.config, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    # 设置随机种子
    seed = config.get('train', {}).get('seed', 42)
    set_seed(seed)

    # 加载数据
    data_path = config.get(
        'data', {}
    ).get(
        'processed_data_path',
        'D:\\Code\\VSCode\\Bitcoin_Transaction_Identification\\data\\processed\\data.pt'
    )
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

    wandb_run = setup_wandb(config, model, args)

    # 创建训练器
    trainer = Trainer(model, data, config, wandb_run=wandb_run)

    # 断点续训（可由CLI参数覆盖配置）
    resume_checkpoint = args.resume_checkpoint
    if not resume_checkpoint:
        resume_checkpoint = config.get('train', {}).get('resume_from_checkpoint')

    if resume_checkpoint:
        if not os.path.exists(resume_checkpoint):
            raise FileNotFoundError(f"断点续训文件不存在: {resume_checkpoint}")
        trainer.load_checkpoint(resume_checkpoint)
        print(f"已加载checkpoint: {resume_checkpoint}")
        print(f"将从第 {trainer.start_epoch + 1} 轮继续训练，目标总轮数: {trainer.epochs}")

    try:
        # 训练
        print(f"\n开始训练...")
        train_log = trainer.train(use_mini_batch=args.mini_batch)

        # 最终评估
        print(f"\n训练完成! 最终评估:")
        test_metrics = trainer.evaluate(data.test_mask)
        print_metrics(test_metrics)
        if wandb_run is not None:
            wandb_run.log({
                'test/accuracy': test_metrics['accuracy'],
                'test/macro_f1': test_metrics['macro_f1'],
                'test/micro_f1': test_metrics['micro_f1'],
                'test/weighted_f1': test_metrics['weighted_f1']
            })

        # 保存最终模型
        checkpoint_dir = config.get('train', {}).get('checkpoint_dir', './experiments/checkpoints')
        final_path = os.path.join(checkpoint_dir, 'final_model.pt')
        trainer.save_checkpoint(final_path)
        print(f"\n模型已保存到: {final_path}")
    finally:
        if wandb_run is not None:
            wandb_run.finish()


if __name__ == '__main__':
    main()
