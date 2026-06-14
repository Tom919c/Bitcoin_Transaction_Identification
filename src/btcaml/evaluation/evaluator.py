from __future__ import annotations

import torch

from .metrics import classification_metrics, ranking_metrics


class Evaluator:
    def __init__(self, labels: list[str] | None = None):
        self.labels = labels

    @torch.no_grad()
    def evaluate(self, model, data, mask_name='val_mask') -> dict:
        model.eval()
        x = data.x if hasattr(data, 'x') else data['x']
        edge_index = data.edge_index if hasattr(data, 'edge_index') else data.get('edge_index')
        edge_attr = data.edge_attr if hasattr(data, 'edge_attr') else data.get('edge_attr')
        y = data.y if hasattr(data, 'y') else data['y']
        mask = getattr(data, mask_name) if hasattr(data, mask_name) else data[mask_name]
        logits = model(x, edge_index=edge_index, edge_attr=edge_attr)
        metrics = classification_metrics(logits, y, mask, self.labels)
        if hasattr(data, 'risk_y') or (isinstance(data, dict) and 'risk_y' in data):
            risk_y = data.risk_y if hasattr(data, 'risk_y') else data['risk_y']
            scores = torch.softmax(logits, dim=-1).max(dim=-1).values
            metrics.update(ranking_metrics(scores, risk_y, mask))
        return metrics
