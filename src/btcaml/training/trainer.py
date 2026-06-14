from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
import torch
from torch.optim import Adam
from tqdm import tqdm

from btcaml.data.label_maps import UNKNOWN_LABEL
from btcaml.evaluation.metrics import classification_metrics
from btcaml.training.callbacks import EarlyStopping
from btcaml.training.losses import build_loss
from btcaml.utils.io import atomic_torch_save, save_json


class Trainer:
    """Concise full-batch trainer for protocol datasets.

    The protocol datasets currently fit in memory (about 2e5 nodes / 1e6 edges), so the
    first stable baseline uses full-batch training. NeighborLoader can be added later
    after baseline results are reliable.
    """

    def __init__(self, model, data, cfg: dict, labels: list[str] | None = None):
        self.model = model
        self.data = data
        self.cfg = dict(cfg)
        self.labels = labels
        self.device = torch.device(self.cfg.get('device', 'cpu'))
        self.model.to(self.device)
        self._move_data_to_device()

        y = self._get('y')
        train_mask = self.supervised_mask(self._get('train_mask'))
        self.criterion = build_loss(
            self.cfg.get('loss', 'weighted_ce'),
            y,
            train_mask,
            int(self.cfg['num_classes']),
            self.cfg,
            device=self.device,
        )
        self.optimizer = Adam(
            self.model.parameters(),
            lr=float(self.cfg.get('lr', 1e-3)),
            weight_decay=float(self.cfg.get('weight_decay', 5e-4)),
        )
        self.early = EarlyStopping(patience=int(self.cfg.get('early_stopping_patience', 50)))
        self.checkpoint_dir = Path(self.cfg.get('checkpoint_dir', 'experiments/checkpoints'))
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        self.history_path = Path(self.cfg.get('history_path', self.checkpoint_dir / 'train_history.json'))
        self.history_csv_path = self.history_path.with_suffix('.csv')

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

    def supervised_mask(self, mask: torch.Tensor) -> torch.Tensor:
        y = self._get('y')
        return mask.bool() & (y != UNKNOWN_LABEL)

    def _model_forward(self):
        x = self._get('x')
        edge_index = self._get('edge_index') if self._has('edge_index') else None
        edge_attr = self._get('edge_attr') if self._has('edge_attr') else None
        return self.model(x, edge_index=edge_index, edge_attr=edge_attr)

    def _save_history(self, history: list[dict[str, Any]]) -> None:
        save_json(history, self.history_path)
        if history:
            self.history_csv_path.parent.mkdir(parents=True, exist_ok=True)
            pd.DataFrame(history).to_csv(self.history_csv_path, index=False)

    def train_full_batch(self) -> list[dict[str, Any]]:
        history: list[dict[str, Any]] = []
        best_metric = -1.0
        best_path = self.checkpoint_dir / 'best.pt'
        y = self._get('y')
        train_mask = self.supervised_mask(self._get('train_mask'))
        val_mask = self.supervised_mask(self._get('val_mask'))

        if int(train_mask.sum().item()) == 0:
            raise ValueError('No supervised nodes in train_mask. Check labels: unlabeled must be -1, classes are 0..C-1.')

        epochs = int(self.cfg.get('epochs', 300))
        eval_every = max(1, int(self.cfg.get('eval_every', 1)))
        log_every = max(1, int(self.cfg.get('log_every', 10)))
        metric_name = str(self.cfg.get('early_stop_metric', 'macro_f1'))
        clip = float(self.cfg.get('grad_clip_norm', 0) or 0)

        pbar = tqdm(range(1, epochs + 1), desc='train', unit='epoch')
        for epoch in pbar:
            self.model.train()
            self.optimizer.zero_grad()
            logits = self._model_forward()
            loss = self.criterion(logits[train_mask], y[train_mask])
            loss.backward()
            if clip > 0:
                torch.nn.utils.clip_grad_norm_(self.model.parameters(), clip)
            self.optimizer.step()

            record: dict[str, Any] = {'epoch': epoch, 'loss': float(loss.item())}
            if epoch == 1 or epoch % eval_every == 0 or epoch == epochs:
                with torch.no_grad():
                    self.model.eval()
                    logits = self._model_forward()
                    val_metrics = classification_metrics(logits, y, val_mask, self.labels)
                record.update({f'val_{k}': v for k, v in val_metrics.items()})
                metric = float(val_metrics.get(metric_name, val_metrics.get('macro_f1', 0.0)))
                if metric > best_metric:
                    best_metric = metric
                    atomic_torch_save(
                        {
                            'model_state_dict': self.model.state_dict(),
                            'epoch': epoch,
                            f'val_{metric_name}': best_metric,
                            'config': self.cfg,
                        },
                        best_path,
                    )
                if self.early.step(metric):
                    record['early_stop'] = True
                    history.append(record)
                    pbar.set_postfix(loss=f'{loss.item():.4f}', best=f'{best_metric:.4f}')
                    break
            history.append(record)
            if epoch == 1 or epoch % log_every == 0:
                val_macro = record.get('val_macro_f1')
                if val_macro is not None:
                    pbar.write(f"epoch {epoch:04d} | loss {loss.item():.4f} | val_macro {val_macro:.4f} | best {best_metric:.4f}")
                else:
                    pbar.write(f"epoch {epoch:04d} | loss {loss.item():.4f}")
            pbar.set_postfix(loss=f'{loss.item():.4f}', best=f'{best_metric:.4f}')
        pbar.close()
        self._save_history(history)
        return history
