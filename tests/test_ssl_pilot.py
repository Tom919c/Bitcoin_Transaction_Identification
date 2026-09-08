import sys
from pathlib import Path

import pytest
import torch
from torch import nn

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from run_ssl_pilot import (
    flow_feature_indices,
    load_encoder_prefix,
    make_model,
    sample_train_mask,
    validate_data_integrity,
    validate_graph,
)


def test_classwise_sample_is_stable_and_excludes_forbidden_and_unlabeled():
    y = torch.tensor([0, 0, 0, 1, 1, -1, 2])
    train = torch.tensor([1, 1, 1, 1, 1, 1, 0], dtype=torch.bool)
    forbidden = torch.tensor([0, 1, 0, 0, 1, 0, 1], dtype=torch.bool)  # val/test nodes
    first = sample_train_mask(y, train, .01, 42, forbidden)
    assert torch.equal(first, sample_train_mask(y, train, .01, 42, forbidden))
    assert not (first & forbidden).any() and not first[5]
    assert set(y[first].tolist()) == {0, 1}


class _TinySage(nn.Module):
    def __init__(self, hidden=3):
        super().__init__()
        self.convs = nn.ModuleList([nn.Linear(2, hidden), nn.Linear(hidden, hidden), nn.Linear(hidden, 11)])
        self.norms = nn.ModuleList([nn.LayerNorm(hidden), nn.LayerNorm(hidden)])


def test_encoder_transfer_uses_only_shape_matched_prefixes():
    source, target = _TinySage(), _TinySage()
    source.convs[1] = nn.Linear(4, 4)  # incompatible middle encoder layer
    source.convs[2].weight.data.fill_(9)  # task output must never transfer
    before = target.convs[2].weight.detach().clone()
    loaded = load_encoder_prefix(target, source)
    assert any(name.startswith('convs.0.') for name in loaded)
    assert not any(name.startswith(('convs.1.', 'convs.2.')) for name in loaded)
    assert torch.equal(target.convs[2].weight, before)


def test_flow_feature_names_and_missing_metadata():
    metadata = {'edge_feature_columns': ['total', 'total_sent', 'edge_duration', 'avg_sent', 'tx_frequency']}
    assert flow_feature_indices(metadata) == [0, 1, 2, 3, 4]
    with pytest.raises(ValueError, match='missing edge features'):
        flow_feature_indices({'edge_feature_columns': ['total']})


def test_integrity_rejects_overlapping_splits_and_wrong_hash(tmp_path):
    data = {
        'x': torch.ones(3, 2),
        'edge_index': torch.tensor([[0, 1], [1, 2]]),
        'y': torch.tensor([0, 1, -1]),
        'train_mask': torch.tensor([1, 0, 0], dtype=torch.bool),
        'val_mask': torch.tensor([1, 1, 0], dtype=torch.bool),
        'test_mask': torch.tensor([0, 0, 1], dtype=torch.bool),
        'edge_attr': torch.ones(2, 1),
    }
    expected = {'expected_nodes': 3, 'expected_edges': 2, 'expected_labeled_nodes': 2}
    with pytest.raises(ValueError, match='pairwise disjoint'):
        validate_graph(data, expected)
    artifact = tmp_path / 'data.pt'
    artifact.write_bytes(b'not-the-protocol-data')
    expected |= {'sha256': '0' * 64, 'size_bytes': artifact.stat().st_size}
    with pytest.raises(ValueError, match='SHA256'):
        validate_data_integrity(artifact, data, expected)


def test_model_uses_protocol_dimensions():
    model = make_model(2, {'hidden_channels': 7, 'num_layers': 2, 'dropout': 0.15})
    assert model.hidden_channels == 7 and len(model.convs) == 2 and model.dropout == 0.15
