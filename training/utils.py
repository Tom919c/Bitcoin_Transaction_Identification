"""
训练工具函数：学习率调度、早停等
"""

import torch
from torch.optim.lr_scheduler import StepLR, CosineAnnealingLR, ReduceLROnPlateau
from typing import Dict, Optional


class EarlyStopping:
    """早停机制"""

    def __init__(self, patience: int = 50, min_delta: float = 0.0, mode: str = 'max'):
        """
        Args:
            patience: 耐心值，多少个epoch没有改善就停止
            min_delta: 最小改善阈值
            mode: 'max' 或 'min'，指标是越大越好还是越小越好
        """
        self.patience = patience
        self.min_delta = min_delta
        self.mode = mode
        self.counter = 0
        self.best_score = None
        self.early_stop = False

    def __call__(self, score: float) -> bool:
        """
        检查是否应该早停

        Args:
            score: 当前指标值

        Returns:
            是否应该停止训练
        """
        if self.best_score is None:
            self.best_score = score
            return False

        if self.mode == 'max':
            improved = score > self.best_score + self.min_delta
        else:
            improved = score < self.best_score - self.min_delta

        if improved:
            self.best_score = score
            self.counter = 0
        else:
            self.counter += 1
            if self.counter >= self.patience:
                self.early_stop = True
                return True

        return False

    def reset(self):
        """重置早停状态"""
        self.counter = 0
        self.best_score = None
        self.early_stop = False


def get_scheduler(optimizer, config: Dict) -> Optional[torch.optim.lr_scheduler._LRScheduler]:
    """
    获取学习率调度器

    Args:
        optimizer: 优化器
        config: 配置字典

    Returns:
        学习率调度器或None
    """
    train_config = config.get('train', {})
    scheduler_type = train_config.get('scheduler', None)

    if scheduler_type is None:
        return None

    if scheduler_type == 'step':
        return StepLR(
            optimizer,
            step_size=train_config.get('scheduler_step_size', 50),
            gamma=train_config.get('scheduler_gamma', 0.5)
        )
    elif scheduler_type == 'cosine':
        return CosineAnnealingLR(
            optimizer,
            T_max=train_config.get('epochs', 200)
        )
    elif scheduler_type == 'plateau':
        return ReduceLROnPlateau(
            optimizer,
            mode='max',
            factor=train_config.get('scheduler_factor', 0.5),
            patience=train_config.get('scheduler_patience', 10)
        )

    return None


def set_seed(seed: int):
    """
    设置随机种子

    Args:
        seed: 随机种子
    """
    import random
    import numpy as np

    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False
