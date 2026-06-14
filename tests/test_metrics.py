import torch

from btcaml.evaluation.metrics import classification_metrics, ranking_metrics


def test_classification_metrics_runs():
    logits = torch.randn(5, 3)
    y = torch.tensor([0, 1, 2, -1, 1])
    mask = torch.ones(5, dtype=torch.bool)
    m = classification_metrics(logits, y, mask, labels=['A', 'B', 'C'])
    assert 'macro_f1' in m


def test_ranking_metrics_runs():
    scores = torch.tensor([0.1, 0.9, 0.8, 0.2])
    y = torch.tensor([0, 1, 1, -1])
    mask = torch.ones(4, dtype=torch.bool)
    m = ranking_metrics(scores, y, mask)
    assert 'auprc' in m
