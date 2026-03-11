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


class Trainer:
    """
    通用训练器类
    """

    def __init__(self, model: nn.Module, data: Data, config: Dict):
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

        # 训练配置
        train_config = config.get('train', {})
        self.device = torch.device(train_config.get('device', 'cuda' if torch.cuda.is_available() else 'cpu'))
        self.epochs = train_config.get('epochs', 200)
        self.lr = train_config.get('lr', 0.01)
        self.weight_decay = train_config.get('weight_decay', 5e-4)
        self.batch_size = train_config.get('batch_size', 1024)
        self.neighbor_sizes = train_config.get('neighbor_sizes', [25, 10])
        self.patience = train_config.get('early_stopping_patience', 50)
        self.checkpoint_dir = train_config.get('checkpoint_dir', './experiments/checkpoints')

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
        self.criterion = nn.CrossEntropyLoss()

        # 训练日志
        self.train_log = []

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

    def _train_full_batch(self) -> List[Dict]:
        """全图训练"""
        best_val_f1 = 0

        for epoch in range(self.epochs):
            # 训练
            self.model.train()
            self.optimizer.zero_grad()

            out = self.model(self.data.x, self.data.edge_index)
            loss = self.criterion(out[self.data.train_mask], self.data.y[self.data.train_mask])

            loss.backward()
            self.optimizer.step()

            if self.scheduler:
                self.scheduler.step()

            # 评估
            train_metrics = self.evaluate(self.data.train_mask)
            val_metrics = self.evaluate(self.data.val_mask)

            log_entry = {
                'epoch': epoch + 1,
                'train_loss': loss.item(),
                'train_acc': train_metrics['accuracy'],
                'train_f1': train_metrics['macro_f1'],
                'val_acc': val_metrics['accuracy'],
                'val_f1': val_metrics['macro_f1']
            }
            self.train_log.append(log_entry)

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
        train_loader = NeighborLoader(
            self.data,
            num_neighbors=self.neighbor_sizes,
            batch_size=self.batch_size,
            input_nodes=self.data.train_mask,
            shuffle=True
        )

        best_val_f1 = 0

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

            if self.scheduler:
                self.scheduler.step()

            avg_loss = total_loss / len(train_loader)
            val_metrics = self.evaluate(self.data.val_mask)

            log_entry = {
                'epoch': epoch + 1,
                'train_loss': avg_loss,
                'val_acc': val_metrics['accuracy'],
                'val_f1': val_metrics['macro_f1']
            }
            self.train_log.append(log_entry)

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
