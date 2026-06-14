import torch

from btcaml.data.splits import random_stratified_split, classwise_temporal_split


def test_random_split_no_overlap():
    y = torch.tensor([0, 0, 0, 0, 1, 1, 1, 1, -1, -1])
    s = random_stratified_split(y, val_ratio=0.25, test_ratio=0.25, seed=1)
    assert not bool((s.train_mask & s.val_mask).any())
    assert not bool((s.train_mask & s.test_mask).any())
    assert not bool((s.val_mask & s.test_mask).any())


def test_classwise_temporal_split_has_labels():
    y = torch.tensor([0,0,0,0,1,1,1,1])
    t = torch.arange(8).float()
    s = classwise_temporal_split(y, t, val_ratio=0.25, test_ratio=0.25)
    assert s.train_mask.sum() > 0
    assert s.val_mask.sum() > 0
    assert s.test_mask.sum() > 0
