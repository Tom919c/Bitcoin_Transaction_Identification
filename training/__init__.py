"""
训练与评估模块
"""

from .trainer import Trainer
from .evaluator import compute_metrics
from .utils import EarlyStopping, get_scheduler

__all__ = ['Trainer', 'compute_metrics', 'EarlyStopping', 'get_scheduler']
