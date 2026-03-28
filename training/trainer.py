"""
通用训练器，支持全图训练和mini-batch训练
"""

import os
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.optim import Adam
from torch.optim.lr_scheduler import ReduceLROnPlateau
from torch_geometric.data import Data
from torch_geometric.loader import NeighborLoader
from typing import Dict, List, Optional, Sequence
from tqdm import tqdm

from data.utils import create_semi_supervised_masks
from .evaluator import compute_metrics
from .utils import EarlyStopping, get_scheduler


def _as_float(value, field_name: str, default: float) -> float:
    """将配置值安全转换为 float，兼容 YAML 中的字符串数值。"""
    target = default if value is None else value
    try:
        return float(target)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"配置项 train.{field_name} 必须是数值，当前值: {target}") from exc


def _as_int(value, field_name: str, default: int) -> int:
    """将配置值安全转换为 int，兼容 YAML 中的字符串数值。"""
    target = default if value is None else value
    try:
        return int(target)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"配置项 train.{field_name} 必须是整数，当前值: {target}") from exc


def _as_int_list(value, field_name: str, default: Sequence[int]) -> List[int]:
    """将配置值安全转换为 int 列表。"""
    target = list(default) if value is None else value
    if not isinstance(target, (list, tuple)):
        raise ValueError(f"配置项 train.{field_name} 必须是列表，当前值: {target}")

    result: List[int] = []
    for idx, item in enumerate(target):
        try:
            result.append(int(item))
        except (TypeError, ValueError) as exc:
            raise ValueError(
                f"配置项 train.{field_name}[{idx}] 必须是整数，当前值: {item}"
            ) from exc

    if not result:
        raise ValueError(f"配置项 train.{field_name} 不能为空列表")
    return result


class FocalLoss(nn.Module):
    """多分类 Focal Loss（支持 ignore_index 与类别权重）。"""

    def __init__(
        self,
        gamma: float = 2.0,
        weight: Optional[torch.Tensor] = None,
        ignore_index: int = 0
    ):
        super().__init__()
        self.gamma = float(gamma)
        self.ignore_index = int(ignore_index)
        if weight is not None:
            self.register_buffer('weight', weight.float())
        else:
            self.weight = None

    def forward(self, logits: torch.Tensor, target: torch.Tensor) -> torch.Tensor:
        valid_mask = target != self.ignore_index
        if int(valid_mask.sum().item()) == 0:
            raise ValueError("FocalLoss 输入不包含有效标签（全部为 ignore_index）")

        logits = logits[valid_mask]
        target = target[valid_mask]

        log_probs = F.log_softmax(logits, dim=1)
        probs = torch.exp(log_probs)
        sample_indices = torch.arange(target.shape[0], device=target.device)

        log_p_t = log_probs[sample_indices, target]
        p_t = probs[sample_indices, target]

        focal_factor = torch.pow(1.0 - p_t, self.gamma)
        loss = -focal_factor * log_p_t

        if self.weight is not None:
            class_weight = self.weight[target]
            loss = loss * class_weight

        return loss.mean()


class Trainer:
    """
    通用训练器类
    """

    def __init__(self, model: nn.Module, data: Data, config: Dict, wandb_run=None):
        """
        初始化训练器

        Args:
            model: PyTorch模型
            data: PyG Data对象
            config: 配置字典
        """
        self.model = model
        self.data = data
        self.config = config
        self.wandb_run = wandb_run

        # 训练配置
        train_config = config.get('train', {})
        self.device = torch.device(train_config.get('device', 'cuda' if torch.cuda.is_available() else 'cpu'))
        self.seed = _as_int(train_config.get('seed'), 'seed', 42)
        self.epochs = _as_int(train_config.get('epochs'), 'epochs', 200)
        self.lr = _as_float(train_config.get('lr'), 'lr', 0.001)
        self.weight_decay = _as_float(train_config.get('weight_decay'), 'weight_decay', 5e-4)
        self.batch_size = _as_int(train_config.get('batch_size'), 'batch_size', 1024)
        self.neighbor_sizes = _as_int_list(train_config.get('neighbor_sizes'), 'neighbor_sizes', [25, 10, 5])
        self.patience = _as_int(train_config.get('early_stopping_patience'), 'early_stopping_patience', 50)
        self.grad_clip_norm = _as_float(train_config.get('grad_clip_norm'), 'grad_clip_norm', 1.0)
        self.checkpoint_dir = train_config.get('checkpoint_dir', './experiments/checkpoints')
        self.loss_type = str(train_config.get('loss', 'weighted_ce')).strip().lower()
        self.focal_gamma = _as_float(train_config.get('focal_gamma'), 'focal_gamma', 2.0)
        self.class_weight_power = _as_float(train_config.get('class_weight_power'), 'class_weight_power', 1.0)
        self.class_weight_cap = _as_float(train_config.get('class_weight_cap'), 'class_weight_cap', 10.0)
        if self.grad_clip_norm < 0:
            raise ValueError("配置项 train.grad_clip_norm 不能小于 0")
        if self.focal_gamma < 0:
            raise ValueError("配置项 train.focal_gamma 不能小于 0")
        if self.class_weight_power < 0:
            raise ValueError("配置项 train.class_weight_power 不能小于 0")

        # 移动到设备
        self.model = self.model.to(self.device)
        self.data = self.data.to(self.device)
        self._repair_overlapped_masks_if_needed()

        # 优化器
        self.optimizer = Adam(
            self.model.parameters(),
            lr=self.lr,
            weight_decay=self.weight_decay
        )

        # 学习率调度器
        self.scheduler = get_scheduler(self.optimizer, config)

        # 早停
        self.early_stopping = EarlyStopping(patience=self.patience)

        # 损失函数
        self.class_weights = self._compute_class_weights() if self.loss_type in {'weighted_ce', 'focal'} else None
        self.criterion = self._build_criterion()
        print(f"损失函数: {self.loss_type}")

        # 训练日志
        self.train_log = []
        self.start_epoch = 0

    def train(self, use_mini_batch: bool = False) -> List[Dict]:
        """
        训练模型

        Args:
            use_mini_batch: 是否使用mini-batch训练

        Returns:
            训练日志列表
        """
        if use_mini_batch:
            return self._train_mini_batch()
        else:
            return self._train_full_batch()

    def _get_best_logged_val_f1(self) -> float:
        if not self.train_log:
            return 0.0
        return max(float(entry.get('val_f1', 0.0)) for entry in self.train_log)

    def _labeled_mask(self, mask: torch.BoolTensor) -> torch.BoolTensor:
        """仅保留有标签节点（NONE=0 会被排除）。"""
        return mask & (self.data.y != 0)

    def _repair_overlapped_masks_if_needed(self):
        """兼容旧版 data.pt：若 train/val/test 重叠，则按当前配置重建互斥掩码。"""
        train_mask = self.data.train_mask.bool()
        val_mask = self.data.val_mask.bool()
        test_mask = self.data.test_mask.bool()
        overlap = (train_mask & val_mask) | (train_mask & test_mask) | (val_mask & test_mask)
        overlap_count = int(overlap.sum().item())
        if overlap_count == 0:
            return

        preprocess_config = self.config.get('preprocessing', {})
        val_ratio = float(preprocess_config.get('val_ratio', 0.2))
        test_ratio = float(preprocess_config.get('test_ratio', 0.2))
        new_train_mask, new_val_mask, new_test_mask = create_semi_supervised_masks(
            labels=self.data.y.detach().cpu(),
            val_ratio=val_ratio,
            test_ratio=test_ratio,
            seed=self.seed
        )
        self.data.train_mask = new_train_mask.to(self.device)
        self.data.val_mask = new_val_mask.to(self.device)
        self.data.test_mask = new_test_mask.to(self.device)
        print(f"检测到掩码重叠节点 {overlap_count} 个，已在训练前自动修复为互斥划分。")

    def _compute_class_weights(self) -> torch.Tensor:
        """基于训练集有标签样本计算类别权重（忽略 NONE=0）。"""
        num_classes = int(self.config.get('data', {}).get('num_classes', 6))
        train_mask = self._labeled_mask(self.data.train_mask)
        train_labels = self.data.y[train_mask]
        if int(train_labels.numel()) == 0:
            raise ValueError("训练集中没有有标签节点，无法计算类别权重")

        counts = torch.bincount(train_labels, minlength=num_classes).float()
        weights = torch.zeros(num_classes, dtype=torch.float32, device=self.device)
        valid = counts > 0
        if valid.shape[0] > 0:
            valid[0] = False

        if int(valid.sum().item()) == 0:
            return weights

        mean_count = counts[valid].mean()
        weights[valid] = torch.pow(mean_count / counts[valid], self.class_weight_power)
        if self.class_weight_cap > 0:
            weights[valid] = torch.clamp(weights[valid], max=self.class_weight_cap)

        weight_mean = weights[valid].mean()
        if float(weight_mean.item()) > 0:
            weights[valid] = weights[valid] / weight_mean

        readable = [f"{idx}:{weights[idx].item():.3f}" for idx in range(1, num_classes) if counts[idx] > 0]
        if readable:
            print("训练集类别权重(忽略NONE): " + ", ".join(readable))
        return weights

    def _build_criterion(self) -> nn.Module:
        if self.loss_type == 'cross_entropy':
            return nn.CrossEntropyLoss(ignore_index=0)
        if self.loss_type == 'weighted_ce':
            if self.class_weights is None:
                raise ValueError("loss=weighted_ce 但未生成类别权重")
            return nn.CrossEntropyLoss(ignore_index=0, weight=self.class_weights)
        if self.loss_type == 'focal':
            return FocalLoss(
                gamma=self.focal_gamma,
                weight=self.class_weights,
                ignore_index=0
            )
        raise ValueError("配置项 train.loss 仅支持: cross_entropy / weighted_ce / focal")

    def _clip_gradients(self):
        if self.grad_clip_norm <= 0:
            return
        torch.nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=self.grad_clip_norm)

    def _step_scheduler(self, val_f1: float):
        if not self.scheduler:
            return
        if isinstance(self.scheduler, ReduceLROnPlateau):
            self.scheduler.step(val_f1)
        else:
            self.scheduler.step()

    def _current_lr(self) -> float:
        if not self.optimizer.param_groups:
            return self.lr
        return float(self.optimizer.param_groups[0].get('lr', self.lr))

    def _log_wandb(self, payload: Dict):
        if self.wandb_run is None:
            return
        self.wandb_run.log(payload)

    def _train_full_batch(self) -> List[Dict]:
        """全图训练"""
        best_val_f1 = self._get_best_logged_val_f1()
        train_mask = self._labeled_mask(self.data.train_mask)
        if int(train_mask.sum().item()) == 0:
            raise ValueError("train_mask 中没有有标签节点（y != 0），无法训练")

        for epoch in range(self.start_epoch, self.epochs):
            # 训练
            self.model.train()
            self.optimizer.zero_grad()

            out = self.model(self.data.x, self.data.edge_index)
            loss = self.criterion(out[train_mask], self.data.y[train_mask])

            loss.backward()
            self._clip_gradients()
            self.optimizer.step()

            # 评估
            train_metrics = self.evaluate(train_mask)
            val_metrics = self.evaluate(self.data.val_mask)
            self._step_scheduler(val_metrics['macro_f1'])

            log_entry = {
                'epoch': epoch + 1,
                'train_loss': loss.item(),
                'train_acc': train_metrics['accuracy'],
                'train_f1': train_metrics['macro_f1'],
                'val_acc': val_metrics['accuracy'],
                'val_f1': val_metrics['macro_f1']
            }
            self.train_log.append(log_entry)
            self.start_epoch = epoch + 1
            self._log_wandb({
                'epoch': epoch + 1,
                'train/loss': loss.item(),
                'train/acc': train_metrics['accuracy'],
                'train/macro_f1': train_metrics['macro_f1'],
                'val/acc': val_metrics['accuracy'],
                'val/macro_f1': val_metrics['macro_f1'],
                'train/lr': self._current_lr()
            })

            # 打印进度
            if (epoch + 1) % 10 == 0:
                print(f"Epoch {epoch+1}/{self.epochs} | "
                      f"Loss: {loss.item():.4f} | "
                      f"Val F1: {val_metrics['macro_f1']:.4f}")

            # 保存最佳模型
            if val_metrics['macro_f1'] > best_val_f1:
                best_val_f1 = val_metrics['macro_f1']
                self.save_checkpoint(os.path.join(self.checkpoint_dir, 'best_model.pt'))

            # 早停检查
            if self.early_stopping(val_metrics['macro_f1']):
                print(f"早停于 epoch {epoch + 1}")
                break

        return self.train_log

    def _train_mini_batch(self) -> List[Dict]:
        """Mini-batch训练"""
        labeled_train_mask = self._labeled_mask(self.data.train_mask)
        if int(labeled_train_mask.sum().item()) == 0:
            raise ValueError("train_mask 中没有有标签节点（y != 0），无法执行 mini-batch 训练")

        train_loader = NeighborLoader(
            self.data,
            num_neighbors=self.neighbor_sizes,
            batch_size=self.batch_size,
            input_nodes=labeled_train_mask,
            shuffle=True
        )

        best_val_f1 = self._get_best_logged_val_f1()

        for epoch in range(self.start_epoch, self.epochs):
            self.model.train()
            total_loss = 0
            effective_batches = 0
            skipped_batches = 0

            for batch in tqdm(train_loader, desc=f"Epoch {epoch+1}", leave=False):
                batch = batch.to(self.device)
                self.optimizer.zero_grad()

                out = self.model(batch.x, batch.edge_index)
                seed_out = out[:batch.batch_size]
                seed_y = batch.y[:batch.batch_size]
                valid_seed_mask = seed_y != 0
                if int(valid_seed_mask.sum().item()) == 0:
                    skipped_batches += 1
                    continue

                loss = self.criterion(seed_out[valid_seed_mask], seed_y[valid_seed_mask])

                loss.backward()
                self._clip_gradients()
                self.optimizer.step()
                total_loss += loss.item()
                effective_batches += 1

            if effective_batches == 0:
                raise ValueError("当前 epoch 的 mini-batch 均无有标签 seed 节点，无法计算训练损失")

            avg_loss = total_loss / effective_batches
            val_metrics = self.evaluate(self.data.val_mask)
            self._step_scheduler(val_metrics['macro_f1'])

            log_entry = {
                'epoch': epoch + 1,
                'train_loss': avg_loss,
                'val_acc': val_metrics['accuracy'],
                'val_f1': val_metrics['macro_f1']
            }
            self.train_log.append(log_entry)
            self.start_epoch = epoch + 1
            self._log_wandb({
                'epoch': epoch + 1,
                'train/loss': avg_loss,
                'val/acc': val_metrics['accuracy'],
                'val/macro_f1': val_metrics['macro_f1'],
                'train/lr': self._current_lr()
            })

            if skipped_batches > 0:
                print(f"Epoch {epoch+1}: 跳过 {skipped_batches} 个仅含 NONE 标签的 batch")

            if (epoch + 1) % 10 == 0:
                print(f"Epoch {epoch+1}/{self.epochs} | "
                      f"Loss: {avg_loss:.4f} | "
                      f"Val F1: {val_metrics['macro_f1']:.4f}")

            if val_metrics['macro_f1'] > best_val_f1:
                best_val_f1 = val_metrics['macro_f1']
                self.save_checkpoint(os.path.join(self.checkpoint_dir, 'best_model.pt'))

            if self.early_stopping(val_metrics['macro_f1']):
                print(f"早停于 epoch {epoch + 1}")
                break

        return self.train_log

    @torch.no_grad()
    def evaluate(self, mask: torch.BoolTensor) -> Dict:
        """
        在指定掩码上评估模型

        Args:
            mask: 评估掩码

        Returns:
            指标字典
        """
        self.model.eval()
        out = self.model(self.data.x, self.data.edge_index)
        num_classes = self.config.get('data', {}).get('num_classes', 6)
        return compute_metrics(out, self.data.y, mask, num_classes)

    def save_checkpoint(self, path: str):
        """保存检查点"""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        torch.save({
            'epoch': self.start_epoch,
            'model_state_dict': self.model.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'scheduler_state_dict': self.scheduler.state_dict() if self.scheduler else None,
            'early_stopping_state': {
                'counter': self.early_stopping.counter,
                'best_score': self.early_stopping.best_score,
                'early_stop': self.early_stopping.early_stop
            },
            'train_log': self.train_log
        }, path)

    def load_checkpoint(self, path: str):
        """加载检查点"""
        checkpoint = torch.load(path, map_location=self.device)
        self.model.load_state_dict(checkpoint['model_state_dict'])
        optimizer_state = checkpoint.get('optimizer_state_dict')
        if optimizer_state is not None:
            self.optimizer.load_state_dict(optimizer_state)

        scheduler_state = checkpoint.get('scheduler_state_dict')
        if self.scheduler is not None and scheduler_state is not None:
            self.scheduler.load_state_dict(scheduler_state)

        early_stopping_state = checkpoint.get('early_stopping_state')
        if isinstance(early_stopping_state, dict):
            self.early_stopping.counter = int(early_stopping_state.get('counter', 0))
            self.early_stopping.best_score = early_stopping_state.get('best_score', None)
            self.early_stopping.early_stop = bool(early_stopping_state.get('early_stop', False))

        self.start_epoch = int(checkpoint.get('epoch', len(checkpoint.get('train_log', []))))
        self.train_log = checkpoint.get('train_log', [])
