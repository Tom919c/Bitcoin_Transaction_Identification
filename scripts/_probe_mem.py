"""One-step memory probe: plain vs gradient-checkpointed EGS training step.

Usage: uv run python scripts/_probe_mem.py plain|ckpt
Prints Windows working-set high-water after each stage. Temporary diagnostic.
"""

import ctypes
import sys
from ctypes import wintypes

import torch

import _bootstrap  # noqa: F401
from btcaml.data.label_maps import UNKNOWN_LABEL
from btcaml.training.losses import build_loss
from btcaml.ext import DGResEGS  # noqa: F401
from btcaml.models.registry import build_model

mode = sys.argv[1] if len(sys.argv) > 1 else 'plain'


class PMC(ctypes.Structure):
    _fields_ = [
        ("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD),
        ("PeakWorkingSetSize", ctypes.c_size_t), ("WorkingSetSize", ctypes.c_size_t),
        ("QuotaPeakPagedPoolUsage", ctypes.c_size_t), ("QuotaPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t), ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
        ("PagefileUsage", ctypes.c_size_t), ("PeakPagefileUsage", ctypes.c_size_t),
    ]


def mem() -> str:
    pmc = PMC()
    pmc.cb = ctypes.sizeof(PMC)
    psapi = ctypes.WinDLL('psapi')
    psapi.GetProcessMemoryInfo.argtypes = [wintypes.HANDLE, ctypes.POINTER(PMC), wintypes.DWORD]
    psapi.GetProcessMemoryInfo.restype = wintypes.BOOL
    k32 = ctypes.WinDLL('kernel32')
    k32.GetCurrentProcess.restype = wintypes.HANDLE
    ok = psapi.GetProcessMemoryInfo(k32.GetCurrentProcess(), ctypes.byref(pmc), pmc.cb)
    if not ok:
        return 'GetProcessMemoryInfo FAILED'
    return f"WS={pmc.WorkingSetSize // 1048576}MB PeakWS={pmc.PeakWorkingSetSize // 1048576}MB Commit={pmc.PagefileUsage // 1048576}MB"


def load(path):
    try:
        payload = torch.load(path, map_location='cpu', weights_only=False)
    except TypeError:
        payload = torch.load(path, map_location='cpu')
    return payload['data']


data = load('data/processed/protocols/temporal_balanced_no_temporal.pt')
y = data.y
train_mask = data.train_mask.bool() & (y != UNKNOWN_LABEL)
labels = [f'c{i}' for i in range(11)]
criterion = build_loss('weighted_ce', y, train_mask, 11, {'class_weight_power': 1.0, 'class_weight_cap': 10.0})
model = build_model('egs', int(data.x.shape[1]), 11, edge_dim=int(data.edge_attr.shape[1]),
                    params={'hidden_channels': 128, 'num_layers': 3, 'dropout': 0.3, 'edge_hidden': 64, 'use_direction': True})
opt = torch.optim.Adam(model.parameters(), lr=1e-3)
model.train()
print(f'[{mode}] after load+build: {mem()}', flush=True)


def fwd():
    if mode in ('ckpt', 'perlayer'):
        if mode == 'perlayer':
            from run_sprint1 import _forward_ckpt
            return _forward_ckpt(model, data)

        def _f(x_, ei_, ea_):
            return model(x_, edge_index=ei_, edge_attr=ea_)
        return torch.utils.checkpoint.checkpoint(_f, data.x, data.edge_index, data.edge_attr, use_reentrant=False)
    return model(data.x, edge_index=data.edge_index, edge_attr=data.edge_attr)


logits = fwd()
print(f'[{mode}] after forward: {mem()}', flush=True)
loss = criterion(logits[train_mask], y[train_mask])
loss.backward()
print(f'[{mode}] after backward: {mem()}', flush=True)
opt.zero_grad(set_to_none=True)
opt.step()
print(f'[{mode}] after step: {mem()}', flush=True)
