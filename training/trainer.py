"""
通用训练器，支持全图训练和mini-batch训练
"""

import os
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.optim import Adam
from torch_geometric.data import Data
from torch_geometric.loader import NeighborLoader
from typing import Dict, Optional, List
from tqdm import tqdm

from .evaluator import compute_metrics
from .utils import EarlyStopping, get_scheduler
from data.utils import LABEL_MAP, LABEL_MAP_INV


class FocalLoss(nn.Module):
    """多分类 Focal Loss，用于提升少数类学习信号。"""

    def __init__(self, weight: Optional[torch.Tensor] = None, gamma: float = 2.0, reduction: str = 'mean'):
        super().__init__()
        self.weight = weight
        self.gamma = float(gamma)
        self.reduction = reduction

    def forward(self, logits: torch.Tensor, targets: torch.Tensor) -> torch.Tensor:
        log_prob = F.log_softmax(logits, dim=1)
        log_pt = log_prob.gather(1, targets.unsqueeze(1)).squeeze(1)
        pt = log_pt.exp()

        alpha_t = 1.0
        if self.weight is not None:
            alpha_t = self.weight[targets]

        focal = -alpha_t * ((1 - pt) ** self.gamma) * log_pt

        if self.reduction == 'mean':
            return focal.mean()
        if self.reduction == 'sum':
            return focal.sum()
        return focal


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
            wandb_run: 可选的 wandb run 对象
        """
        self.model = model
        self.data = data
        self.config = config
        self.wandb_run = wandb_run

        # 训练配置
        train_config = config.get('train', {})
        self.device = torch.device(train_config.get('device', 'cuda' if torch.cuda.is_available() else 'cpu'))
        self.epochs = int(train_config.get('epochs', 200))
        self.lr = float(train_config.get('lr', 0.01))
        self.weight_decay = float(train_config.get('weight_decay', 5e-4))
        self.batch_size = int(train_config.get('batch_size', 1024))
        self.neighbor_sizes = [int(n) for n in train_config.get('neighbor_sizes', [25, 10])]
        self.patience = int(train_config.get('early_stopping_patience', 50))
        self.checkpoint_dir = train_config.get('checkpoint_dir', './experiments/checkpoints')
        self.use_class_weights = bool(train_config.get('use_class_weights', True))
        self.appnp_full_batch_only = bool(train_config.get('appnp_full_batch_only', True))
        self.loss_type = str(train_config.get('loss_type', 'cross_entropy')).lower()
        self.focal_gamma = float(train_config.get('focal_gamma', 2.0))
        self.class_weight_strategy = str(train_config.get('class_weight_strategy', 'inverse')).lower()
        self.class_weight_beta = float(train_config.get('class_weight_beta', 0.999))
        self.class_weight_power = float(train_config.get('class_weight_power', 1.0))
        self.class_weight_overrides = train_config.get('class_weight_overrides', {})
        self.model_name = str(config.get('model', {}).get('name', '')).lower()
        self.num_classes = int(config.get('data', {}).get('num_classes', 6))
        self.load_best_at_end = bool(train_config.get('load_best_at_end', True))
        self.logit_bias_by_class_idx = {}

        # 评估标签口径（默认使用配置中的5个业务类）
        eval_config = config.get('eval', {})
        metric_label_names = eval_config.get('metric_labels', config.get('preprocessing', {}).get('target_labels', []))
        metric_label_indices = []
        resolved_label_names = []
        for label_name in metric_label_names:
            if label_name in LABEL_MAP:
                metric_label_indices.append(LABEL_MAP[label_name])
                resolved_label_names.append(label_name)
            else:
                print(f"警告: 未知评估标签 {label_name}，将忽略")

        if not metric_label_indices:
            metric_label_indices = list(range(self.num_classes))
            resolved_label_names = [LABEL_MAP_INV.get(i, f'class_{i}') for i in metric_label_indices]

        self.metric_label_indices = metric_label_indices
        self.metric_label_names = resolved_label_names

        # APPNP 训练前可选自动重建掩码，并打印划分统计
        self._prepare_appnp_masks_if_needed()

        # 移动到设备
        self.model = self.model.to(self.device)
        self.data = self.data.to(self.device)

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
        self.criterion = self._build_criterion()

        # 训练日志
        self.train_log = []

    def _prepare_appnp_masks_if_needed(self):
        if self.model_name != 'appnp':
            return

        try:
            from models.appnp import maybe_rebuild_masks, print_split_stats
            self.data = maybe_rebuild_masks(
                self.data,
                self.config,
                self.metric_label_indices,
                self.metric_label_names
            )
            print_split_stats(
                self.data,
                self.metric_label_indices,
                self.metric_label_names,
                self.num_classes
            )
        except Exception as exc:
            print(f"警告: APPNP 掩码准备阶段失败，继续使用原始掩码。原因: {exc}")

    def _finalize_training(self, best_path: str):
        if self.load_best_at_end and os.path.exists(best_path):
            self.load_checkpoint(best_path)
            print(f"训练结束后已自动加载最佳模型: {best_path}")

        if self.model_name != 'appnp':
            return

        try:
            from models.appnp import tune_minority_logit_bias
            self.logit_bias_by_class_idx = tune_minority_logit_bias(
                self,
                self.data,
                self.config,
                self.metric_label_indices,
                self.metric_label_names
            )
        except Exception as exc:
            print(f"警告: APPNP 验证集偏置调优失败，将使用原始logits评估。原因: {exc}")
            self.logit_bias_by_class_idx = {}

    def _build_criterion(self) -> nn.Module:
        """根据配置构建损失函数，默认启用训练集类别权重。"""
        weights = None

        if not self.use_class_weights:
            print(f"损失函数: {self.loss_type} (无类别权重)")
        else:
            train_y = self.data.y[self.data.train_mask]
            class_counts = torch.bincount(train_y, minlength=self.num_classes).float()
            weights = torch.zeros(self.num_classes, dtype=torch.float, device=class_counts.device)

            present_mask = class_counts > 0
            if int(present_mask.sum()) == 0:
                print("警告: 训练集中没有有效类别，回退到无权重损失")
                weights = None
            else:
                if self.class_weight_strategy == 'effective_num':
                    beta = torch.tensor(self.class_weight_beta, device=class_counts.device)
                    effective_num = 1.0 - torch.pow(beta, class_counts[present_mask])
                    weights[present_mask] = (1.0 - beta) / torch.clamp(effective_num, min=1e-12)
                else:
                    total_present = class_counts[present_mask].sum()
                    num_present = present_mask.sum().float()
                    weights[present_mask] = total_present / (class_counts[present_mask] * num_present)

                if self.class_weight_power != 1.0:
                    weights[present_mask] = torch.pow(weights[present_mask], self.class_weight_power)

                # 支持按标签名或类别索引对权重进行微调
                if isinstance(self.class_weight_overrides, dict) and self.class_weight_overrides:
                    for key, value in self.class_weight_overrides.items():
                        class_idx = None
                        if isinstance(key, int):
                            class_idx = key
                        elif isinstance(key, str):
                            key_upper = key.upper()
                            if key_upper in LABEL_MAP:
                                class_idx = LABEL_MAP[key_upper]
                            elif key.isdigit():
                                class_idx = int(key)

                        if class_idx is None or class_idx < 0 or class_idx >= self.num_classes:
                            continue

                        if present_mask[class_idx]:
                            weights[class_idx] = weights[class_idx] * float(value)

                norm = weights[present_mask].mean()
                if norm > 0:
                    weights[present_mask] = weights[present_mask] / norm

                print("训练集类别计数:", class_counts.tolist())
                print(f"类别权重策略: {self.class_weight_strategy}, power={self.class_weight_power}")
                print("类别权重:", weights.tolist())

        if self.loss_type == 'focal':
            print(f"损失函数: focal (gamma={self.focal_gamma})")
            return FocalLoss(weight=weights, gamma=self.focal_gamma)

        print("损失函数: cross_entropy")
        return nn.CrossEntropyLoss(weight=weights)

    def train(self, use_mini_batch: bool = False) -> List[Dict]:
        """
        训练模型

        Args:
            use_mini_batch: 是否使用mini-batch训练

        Returns:
            训练日志列表
        """
        if use_mini_batch and self.model_name == 'appnp' and self.appnp_full_batch_only:
            print("检测到 APPNP + mini-batch 组合，已自动切换为全图训练以保持传播正确性")
            use_mini_batch = False

        if use_mini_batch:
            return self._train_mini_batch()
        else:
            return self._train_full_batch()

    def _train_full_batch(self) -> List[Dict]:
        """全图训练"""
        best_val_f1 = -1
        best_path = os.path.join(self.checkpoint_dir, 'best_model.pt')

        for epoch in range(self.epochs):
            # 训练
            self.model.train()
            self.optimizer.zero_grad()

            out = self.model(self.data.x, self.data.edge_index)
            loss = self.criterion(out[self.data.train_mask], self.data.y[self.data.train_mask])

            loss.backward()
            self.optimizer.step()

            # 评估
            train_metrics = self.evaluate(self.data.train_mask)
            val_metrics = self.evaluate(self.data.val_mask)

            if self.scheduler:
                if isinstance(self.scheduler, torch.optim.lr_scheduler.ReduceLROnPlateau):
                    self.scheduler.step(val_metrics['macro_f1'])
                else:
                    self.scheduler.step()

            log_entry = {
                'epoch': epoch + 1,
                'train_loss': loss.item(),
                'train_acc': train_metrics['accuracy'],
                'train_f1': train_metrics['macro_f1'],
                'val_acc': val_metrics['accuracy'],
                'val_f1': val_metrics['macro_f1']
            }
            self.train_log.append(log_entry)
            if self.wandb_run is not None:
                self.wandb_run.log({
                    'epoch': epoch + 1,
                    'train/loss': loss.item(),
                    'train/accuracy': train_metrics['accuracy'],
                    'train/macro_f1': train_metrics['macro_f1'],
                    'val/accuracy': val_metrics['accuracy'],
                    'val/macro_f1': val_metrics['macro_f1']
                })

            # 打印进度
            if (epoch + 1) % 10 == 0:
                print(f"Epoch {epoch+1}/{self.epochs} | "
                      f"Loss: {loss.item():.4f} | "
                      f"Val F1: {val_metrics['macro_f1']:.4f}")

            # 保存最佳模型
            if val_metrics['macro_f1'] > best_val_f1:
                best_val_f1 = val_metrics['macro_f1']
                self.save_checkpoint(best_path)

            # 早停检查
            if self.early_stopping(val_metrics['macro_f1']):
                print(f"早停于 epoch {epoch + 1}")
                break

        self._finalize_training(best_path)

        return self.train_log

    def _train_mini_batch(self) -> List[Dict]:
        """Mini-batch训练"""
        train_loader = NeighborLoader(
            self.data,
            num_neighbors=self.neighbor_sizes,
            batch_size=self.batch_size,
            input_nodes=self.data.train_mask,
            shuffle=True
        )

        best_val_f1 = -1
        best_path = os.path.join(self.checkpoint_dir, 'best_model.pt')

        for epoch in range(self.epochs):
            self.model.train()
            total_loss = 0

            for batch in tqdm(train_loader, desc=f"Epoch {epoch+1}", leave=False):
                batch = batch.to(self.device)
                self.optimizer.zero_grad()

                out = self.model(batch.x, batch.edge_index)
                loss = self.criterion(out[:batch.batch_size], batch.y[:batch.batch_size])

                loss.backward()
                self.optimizer.step()
                total_loss += loss.item()

            avg_loss = total_loss / len(train_loader)
            val_metrics = self.evaluate(self.data.val_mask)

            if self.scheduler:
                if isinstance(self.scheduler, torch.optim.lr_scheduler.ReduceLROnPlateau):
                    self.scheduler.step(val_metrics['macro_f1'])
                else:
                    self.scheduler.step()

            log_entry = {
                'epoch': epoch + 1,
                'train_loss': avg_loss,
                'val_acc': val_metrics['accuracy'],
                'val_f1': val_metrics['macro_f1']
            }
            self.train_log.append(log_entry)
            if self.wandb_run is not None:
                self.wandb_run.log({
                    'epoch': epoch + 1,
                    'train/loss': avg_loss,
                    'val/accuracy': val_metrics['accuracy'],
                    'val/macro_f1': val_metrics['macro_f1']
                })

            if (epoch + 1) % 10 == 0:
                print(f"Epoch {epoch+1}/{self.epochs} | "
                      f"Loss: {avg_loss:.4f} | "
                      f"Val F1: {val_metrics['macro_f1']:.4f}")

            if val_metrics['macro_f1'] > best_val_f1:
                best_val_f1 = val_metrics['macro_f1']
                self.save_checkpoint(best_path)

            if self.early_stopping(val_metrics['macro_f1']):
                print(f"早停于 epoch {epoch + 1}")
                break

        self._finalize_training(best_path)

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

        # 可选后处理：在验证集网格搜索到的类别logit偏置用于最终评估
        if self.logit_bias_by_class_idx:
            for class_idx, bias in self.logit_bias_by_class_idx.items():
                out[:, int(class_idx)] = out[:, int(class_idx)] + float(bias)

        return compute_metrics(
            out,
            self.data.y,
            mask,
            num_classes=self.num_classes,
            label_indices=self.metric_label_indices,
            label_names=self.metric_label_names
        )

    def save_checkpoint(self, path: str):
        """保存检查点"""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        torch.save({
            'model_state_dict': self.model.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'train_log': self.train_log
        }, path)

    def load_checkpoint(self, path: str):
        """加载检查点"""
        checkpoint = torch.load(path, map_location=self.device)
        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        self.train_log = checkpoint.get('train_log', [])
