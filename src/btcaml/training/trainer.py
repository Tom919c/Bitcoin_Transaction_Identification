from __future__ import annotations

from pathlib import Path
from typing import Any

import torch
from torch.optim import Adam

from btcaml.data.label_maps import UNKNOWN_LABEL
from btcaml.evaluation.metrics import classification_metrics
from btcaml.training.callbacks import EarlyStopping
from btcaml.training.losses import build_loss
from btcaml.utils.io import atomic_torch_save, save_json


class Trainer:
    """Minimal full-batch trainer for paper baselines.

    Large-scale mini-batch NeighborLoader support should be enabled after protocol datasets are
    generated and PyG is available on the user's machine. This class intentionally keeps the
    first research package deterministic and easy to debug.
    """

    def __init__(self, model, data, cfg: dict, labels: list[str] | None = None):
        self.model = model
        self.data = data
        self.cfg = cfg
        self.labels = labels
        self.device = torch.device(cfg.get('device', 'cpu'))
        self.model.to(self.device)
        self._move_data_to_device()
        train_mask = self._get('train_mask')
        y = self._get('y')
        self.criterion = build_loss(
            cfg.get('loss', 'weighted_ce'), y, train_mask, int(cfg['num_classes']), cfg, device=self.device
        )
        self.optimizer = Adam(
            self.model.parameters(), lr=cfg.get('lr', 1e-3), weight_decay=cfg.get('weight_decay', 5e-4)
        )
        self.early = EarlyStopping(patience=cfg.get('early_stopping_patience', 50))
        self.checkpoint_dir = Path(cfg.get('checkpoint_dir', 'experiments/checkpoints'))
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

    def _move_data_to_device(self):
        if hasattr(self.data, 'to'):
            self.data = self.data.to(self.device)
        elif isinstance(self.data, dict):
            for k, v in list(self.data.items()):
                if torch.is_tensor(v):
                    self.data[k] = v.to(self.device)

    def _get(self, name: str):
        if hasattr(self.data, name):
            return getattr(self.data, name)
        return self.data[name]

    def _has(self, name: str) -> bool:
        return hasattr(self.data, name) or (isinstance(self.data, dict) and name in self.data)

    def _model_forward(self):
        x = self._get('x')
        edge_index = self._get('edge_index') if self._has('edge_index') else None
        edge_attr = self._get('edge_attr') if self._has('edge_attr') else None
        return self.model(x, edge_index=edge_index, edge_attr=edge_attr)

    def train_full_batch(self) -> list[dict[str, Any]]:
        history = []
        best_metric = -1.0
        best_path = self.checkpoint_dir / 'best.pt'
        y = self._get('y')
        train_mask = self._get('train_mask') & (y != UNKNOWN_LABEL)
        val_mask = self._get('val_mask')
        for epoch in range(1, int(self.cfg.get('epochs', 300)) + 1):
            self.model.train()
            self.optimizer.zero_grad()
            logits = self._model_forward()
            loss = self.criterion(logits[train_mask], y[train_mask])
            loss.backward()
            clip = float(self.cfg.get('grad_clip_norm', 0) or 0)
            if clip > 0:
                torch.nn.utils.clip_grad_norm_(self.model.parameters(), clip)
            self.optimizer.step()
            with torch.no_grad():
                self.model.eval()
                logits = self._model_forward()
                val_metrics = classification_metrics(logits, y, val_mask, self.labels)
            record = {'epoch': epoch, 'loss': float(loss.item()), **{f'val_{k}': v for k, v in val_metrics.items()}}
            history.append(record)
            metric = val_metrics.get('macro_f1', 0.0)
            if metric > best_metric:
                best_metric = metric
                atomic_torch_save(
                    {'model_state_dict': self.model.state_dict(), 'epoch': epoch, 'val_macro_f1': best_metric},
                    best_path,
                )
            if self.early.step(metric):
                break
        save_json(history, self.checkpoint_dir / 'train_history.json')
        return history
