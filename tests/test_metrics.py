import torch

from btcaml.data.label_maps import UNKNOWN_LABEL
from btcaml.evaluation.metrics import (
    classification_metrics,
    classification_report_table,
    confusion_matrix_table,
    per_class_metrics_table,
    prediction_numpy,
    ranking_metrics,
)


def _sample_inputs():
    logits = torch.tensor(
        [
            [9.0, 1.0, 0.0],
            [0.0, 9.0, 1.0],
            [0.0, 1.0, 9.0],
            [9.0, 0.0, 0.0],
        ]
    )
    y = torch.tensor([0, 1, 2, UNKNOWN_LABEL])
    mask = torch.ones(4, dtype=torch.bool)
    labels = ['INDIVIDUAL', 'BET', 'GAMBLING']
    return logits, y, mask, labels


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


def test_unknown_label_is_ignored_and_label_zero_is_kept():
    logits, y, mask, labels = _sample_inputs()

    y_true, y_pred = prediction_numpy(logits, y, mask)
    assert y_true.tolist() == [0, 1, 2]
    assert y_pred.tolist() == [0, 1, 2]

    metrics = classification_metrics(logits, y, mask, labels=labels)
    assert metrics['num_eval'] == 3
    assert metrics['INDIVIDUAL_support'] == 1
    assert metrics['BET_support'] == 1
    assert metrics['GAMBLING_support'] == 1

    per_class = per_class_metrics_table(logits, y, mask, labels=labels)
    assert per_class.loc['INDIVIDUAL', 'support'] == 1
    assert per_class.loc['INDIVIDUAL', 'precision'] == 1.0

    report = classification_report_table(logits, y, mask, labels=labels)
    assert 'accuracy' in report.index
    assert report.loc['INDIVIDUAL', 'support'] == 1
    assert report.loc['accuracy', 'f1-score'] == 1.0


def test_confusion_matrix_shape_correct():
    logits, y, mask, labels = _sample_inputs()
    cm = confusion_matrix_table(logits, y, mask, labels=labels)
    cm_norm = confusion_matrix_table(logits, y, mask, labels=labels, normalize='true')

    assert cm.shape == (3, 3)
    assert cm_norm.shape == (3, 3)
    assert cm.index.tolist() == labels
    assert cm.columns.tolist() == labels
    assert cm.loc['INDIVIDUAL', 'INDIVIDUAL'] == 1


def test_prediction_table_exports_only_supervised_nodes():
    from btcaml.evaluation.export import prediction_table

    logits, y, mask, labels = _sample_inputs()
    table = prediction_table(logits, y, mask, labels)

    assert table['node_index'].tolist() == [0, 1, 2]
    assert table['y_true_name'].tolist() == ['INDIVIDUAL', 'BET', 'GAMBLING']
    assert table['y_pred_name'].tolist() == ['INDIVIDUAL', 'BET', 'GAMBLING']
    assert table['correct'].tolist() == [True, True, True]
