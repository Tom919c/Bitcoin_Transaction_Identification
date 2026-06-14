import torch

from btcaml.models.etd_sage import ETDSAGE
from btcaml.models.mlp import MLP


def test_mlp_forward_shape():
    model = MLP(in_channels=5, hidden_channels=8, out_channels=3, num_layers=2)
    x = torch.randn(7, 5)
    out = model(x)
    assert out.shape == (7, 3)


def test_etd_sage_forward_shape():
    model = ETDSAGE(in_channels=5, hidden_channels=8, out_channels=3, edge_dim=4, num_layers=2)
    x = torch.randn(7, 5)
    edge_index = torch.tensor([[0, 1, 2, 3, 4], [1, 2, 3, 4, 5]])
    edge_attr = torch.randn(5, 4)
    out = model(x, edge_index=edge_index, edge_attr=edge_attr)
    assert out.shape == (7, 3)
