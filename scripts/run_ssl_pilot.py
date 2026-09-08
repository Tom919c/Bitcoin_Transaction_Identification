from __future__ import annotations

"""Frozen-protocol self-supervised representation-learning screen (validation only)."""

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import torch
import torch.nn.functional as F
from torch import nn

from btcaml.data.label_maps import RAW_LABELS_11, UNKNOWN_LABEL
from btcaml.evaluation.metrics import classification_metrics
from btcaml.models.sage import GraphSAGE
from btcaml.training.losses import build_loss
from btcaml.utils.config import load_config
from btcaml.utils.seed import seed_everything

DEFAULT_METHODS = ('random_init', 'dgi', 'masked_feature', 'flow_edge_reconstruction')
FLOW_FEATURES = ('total', 'total_sent', 'edge_duration', 'avg_sent', 'tx_frequency')
PROTOCOL_PATH = Path('configs/experiment/ssl_pilot_v1.yaml')


def _get(data, name):
    return getattr(data, name) if hasattr(data, name) else data[name]


def load_data(path: str):
    try:
        payload = torch.load(path, map_location='cpu', weights_only=False)
    except TypeError:
        payload = torch.load(path, map_location='cpu')
    return (payload['data'], payload.get('metadata', {})) if isinstance(payload, dict) and 'data' in payload else (payload, {})


def fingerprint_file(path: str | Path) -> dict:
    path = Path(path)
    digest = hashlib.sha256()
    with path.open('rb') as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(chunk)
    return {'sha256': digest.hexdigest(), 'size_bytes': path.stat().st_size}


def validate_graph(data, expected: dict) -> dict:
    x, edge_index, y = _get(data, 'x'), _get(data, 'edge_index'), _get(data, 'y')
    train_mask, val_mask, test_mask = (_get(data, name).bool() for name in ('train_mask', 'val_mask', 'test_mask'))
    if x.ndim != 2 or edge_index.ndim != 2 or edge_index.shape[0] != 2 or y.ndim != 1:
        raise ValueError('Expected x[N,F], edge_index[2,E], and y[N].')
    if x.shape[0] != y.shape[0] or any(mask.shape != y.shape for mask in (train_mask, val_mask, test_mask)):
        raise ValueError('Node features, labels, train_mask, val_mask, and test_mask must share N.')
    if edge_index.numel() == 0 or edge_index.min() < 0 or edge_index.max() >= x.shape[0]:
        raise ValueError('edge_index is empty or contains an invalid node index.')
    if not torch.isfinite(x).all():
        raise ValueError('x contains non-finite values.')
    if not (((y == UNKNOWN_LABEL) | ((y >= 0) & (y < len(RAW_LABELS_11)))).all()):
        raise ValueError('y must contain only -1 or valid 11-class entity-type IDs.')
    if (train_mask & val_mask).any() or (train_mask & test_mask).any() or (val_mask & test_mask).any():
        raise ValueError('train_mask, val_mask, and test_mask must be pairwise disjoint.')
    if not (train_mask & (y != UNKNOWN_LABEL)).any() or not (val_mask & (y != UNKNOWN_LABEL)).any():
        raise ValueError('Both train_mask and val_mask need labeled entities.')
    edge_attr = _get(data, 'edge_attr') if hasattr(data, 'edge_attr') else None
    if edge_attr is not None and (edge_attr.ndim != 2 or edge_attr.shape[0] != edge_index.shape[1]):
        raise ValueError('edge_attr must have one row per edge.')
    actual = {'nodes': int(x.shape[0]), 'edges': int(edge_index.shape[1]), 'labeled_nodes': int((y != UNKNOWN_LABEL).sum())}
    for key, expected_key in [('nodes', 'expected_nodes'), ('edges', 'expected_edges'), ('labeled_nodes', 'expected_labeled_nodes')]:
        if actual[key] != int(expected[expected_key]):
            raise ValueError(f'{key}={actual[key]} does not match protocol {expected_key}={expected[expected_key]}.')
    return {
        **actual,
        'x_shape': list(x.shape),
        'edge_index_shape': list(edge_index.shape),
        'edge_attr_shape': list(edge_attr.shape) if edge_attr is not None else None,
        'y_shape': list(y.shape),
        'split_counts': {'train': int(train_mask.sum()), 'val': int(val_mask.sum()), 'test': int(test_mask.sum())},
        'split_overlap': int(((train_mask & val_mask) | (train_mask & test_mask) | (val_mask & test_mask)).sum()),
    }


def validate_data_integrity(path: str | Path, data, expected: dict) -> dict:
    fingerprint = fingerprint_file(path)
    if fingerprint['sha256'] != expected['sha256'] or fingerprint['size_bytes'] != int(expected['size_bytes']):
        raise ValueError('Data SHA256 or size does not match the selected protocol.')
    return fingerprint | validate_graph(data, expected)


def flow_feature_indices(metadata: dict, required: tuple[str, ...] = FLOW_FEATURES) -> list[int]:
    names = metadata.get('edge_feature_columns')
    if not isinstance(names, (list, tuple)):
        raise TypeError('flow_edge_reconstruction requires metadata.edge_feature_columns.')
    missing = [name for name in required if name not in names]
    if missing:
        raise ValueError(f'flow_edge_reconstruction missing edge features: {missing}')
    return [list(names).index(name) for name in required]


def sample_train_mask(y: torch.Tensor, train_mask: torch.Tensor, fraction: float, seed: int, forbidden_mask: torch.Tensor | None = None) -> torch.Tensor:
    """Classwise deterministic labeled-only sample, with one item per present class."""
    if not 0 < fraction <= 1:
        raise ValueError('fraction must be in (0, 1].')
    if y.ndim != 1 or train_mask.shape != y.shape:
        raise ValueError('y and train_mask must be matching 1D tensors.')
    allowed = train_mask.bool() & (y != UNKNOWN_LABEL)
    if forbidden_mask is not None:
        if forbidden_mask.shape != y.shape:
            raise ValueError('forbidden_mask must match y.')
        allowed &= ~forbidden_mask.bool()
    out = torch.zeros_like(allowed)
    generator = torch.Generator(device='cpu').manual_seed(seed)
    for label in torch.unique(y[allowed], sorted=True).tolist():
        members = torch.where(allowed & (y == label))[0]
        count = max(1, round(len(members) * fraction))
        chosen = members[torch.randperm(len(members), generator=generator)[:count]]
        out[chosen] = True
    if not out.any():
        raise ValueError('No labeled training nodes available for sampling.')
    return out


def encoder_embeddings(model: GraphSAGE, x: torch.Tensor, edge_index: torch.Tensor) -> torch.Tensor:
    """Exact GraphSAGE prefix before its task-specific final convolution."""
    h = x
    for conv, norm in zip(model.convs[:-1], model.norms):
        h = F.dropout(F.relu(norm(conv(h, edge_index))), p=model.dropout, training=model.training)
    return h


def load_encoder_prefix(target: GraphSAGE, source: GraphSAGE) -> list[str]:
    """Copy only matching pre-classifier GraphSAGE tensors; never copy final conv."""
    target_state, source_state = target.state_dict(), source.state_dict()
    encoder_prefixes = tuple([f'convs.{i}.' for i in range(len(target.convs) - 1)] + [f'norms.{i}.' for i in range(len(target.norms))])
    matched = {k: v for k, v in source_state.items() if k.startswith(encoder_prefixes) and k in target_state and target_state[k].shape == v.shape}
    target.load_state_dict(matched, strict=False)
    return sorted(matched)


def make_model(in_channels: int, model_cfg: dict) -> GraphSAGE:
    return GraphSAGE(in_channels, hidden_channels=int(model_cfg['hidden_channels']), out_channels=len(RAW_LABELS_11), num_layers=int(model_cfg['num_layers']), dropout=float(model_cfg['dropout']))


def pretrain(method: str, model: GraphSAGE, x: torch.Tensor, edge_index: torch.Tensor, edge_attr: torch.Tensor | None, flow_indices: list[int] | None, epochs: int, pretrain_cfg: dict, device: torch.device) -> list[dict]:
    """Uses only x/edge_index/edge_attr: labels and split masks never enter this function."""
    if method == 'random_init':
        return [{'method': method, 'epoch': epoch, 'loss': 0.0} for epoch in range(1, epochs + 1)]
    model.to(device)
    for parameter in model.convs[-1].parameters():
        parameter.requires_grad_(False)
    x, edge_index = x.to(device), edge_index.to(device)
    if method == 'dgi':
        head: nn.Module = nn.Bilinear(model.hidden_channels, model.hidden_channels, 1).to(device)
    elif method == 'masked_feature':
        head = nn.Linear(model.hidden_channels, x.shape[1]).to(device)
    elif method == 'flow_edge_reconstruction':
        if edge_attr is None or flow_indices is None:
            raise ValueError('flow_edge_reconstruction requires edge_attr and resolved metadata feature indices.')
        if max(flow_indices, default=-1) >= edge_attr.shape[1] or not torch.isfinite(edge_attr).all():
            raise ValueError('edge_attr is non-finite or does not match its metadata columns.')
        edge_attr = edge_attr.to(device)
        head = nn.Linear(2 * model.hidden_channels, len(flow_indices)).to(device)
    else:
        raise ValueError(f'Unknown method {method}; choose from {DEFAULT_METHODS}.')
    optimizer = torch.optim.Adam(list(model.parameters()) + list(head.parameters()), lr=float(pretrain_cfg['learning_rate']), weight_decay=float(pretrain_cfg['weight_decay']))
    history = []
    for epoch in range(1, epochs + 1):
        model.train(); head.train(); optimizer.zero_grad()
        if method == 'dgi':
            positive, negative = encoder_embeddings(model, x, edge_index), encoder_embeddings(model, x[torch.randperm(x.shape[0], device=device)], edge_index)
            summary = torch.sigmoid(positive.mean(0, keepdim=True)).expand_as(positive)
            loss = -(F.logsigmoid(head(positive, summary)).mean() + F.logsigmoid(-head(negative, summary)).mean())
        elif method == 'masked_feature':
            masked = torch.rand(x.shape, device=device) < float(pretrain_cfg['mask_ratio'])
            x_masked = x.masked_fill(masked, 0.0)
            loss = F.mse_loss(head(encoder_embeddings(model, x_masked, edge_index))[masked], x[masked])
        else:
            sample_size = min(int(pretrain_cfg['edge_sample_size']), edge_index.shape[1])
            chosen = torch.randperm(edge_index.shape[1], device=device)[:sample_size]
            h = encoder_embeddings(model, x, edge_index)
            prediction = head(torch.cat((h[edge_index[0, chosen]], h[edge_index[1, chosen]]), dim=-1))
            loss = F.mse_loss(prediction, edge_attr[chosen][:, flow_indices])
        if not torch.isfinite(loss):
            raise FloatingPointError(f'{method} pretraining loss became non-finite at epoch {epoch}.')
        loss.backward(); optimizer.step()
        history.append({'method': method, 'epoch': epoch, 'loss': float(loss.detach().cpu())})
        print(f'  pretrain {method} epoch {epoch}/{epochs}: loss={history[-1]["loss"]:.6f}', flush=True)
    return history


def finetune(model: GraphSAGE, x: torch.Tensor, edge_index: torch.Tensor, y: torch.Tensor, train_mask: torch.Tensor, val_mask: torch.Tensor, epochs: int, patience: int, downstream_cfg: dict, device: torch.device) -> dict:
    model.to(device); x, edge_index, y, train_mask, val_mask = (v.to(device) for v in (x, edge_index, y, train_mask, val_mask))
    loss_name = {'weighted_cross_entropy': 'weighted_ce'}.get(str(downstream_cfg['loss']), downstream_cfg['loss'])
    criterion = build_loss(loss_name, y, train_mask, len(RAW_LABELS_11), {}, device=device)
    optimizer = torch.optim.Adam(model.parameters(), lr=float(downstream_cfg['learning_rate']), weight_decay=float(downstream_cfg['weight_decay']))
    best, best_state, best_epoch, stalled = -1.0, None, 0, 0
    for epoch in range(1, epochs + 1):
        model.train(); optimizer.zero_grad(); logits = model(x, edge_index=edge_index)
        loss = criterion(logits[train_mask], y[train_mask])
        if not torch.isfinite(loss):
            raise FloatingPointError(f'Downstream loss became non-finite at epoch {epoch}.')
        loss.backward(); optimizer.step()
        model.eval()
        with torch.no_grad(): metrics = classification_metrics(model(x, edge_index=edge_index), y, val_mask, RAW_LABELS_11)
        if metrics['macro_f1'] > best:
            best, best_state, best_epoch, stalled = metrics['macro_f1'], {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}, epoch, 0
        else: stalled += 1
        if stalled >= patience:
            break
    model.load_state_dict(best_state)
    with torch.no_grad():
        best_metrics = classification_metrics(model(x, edge_index=edge_index), y, val_mask, RAW_LABELS_11)
    return {'best_epoch': best_epoch, 'last_epoch': epoch, **best_metrics}


def write_validation_results(out_dir: Path, rows: list[dict]) -> None:
    csv_path, json_path = out_dir / 'validation_results.csv', out_dir / 'validation_results.json'
    csv_tmp, json_tmp = csv_path.with_suffix('.csv.tmp'), json_path.with_suffix('.json.tmp')
    pd.DataFrame(rows).to_csv(csv_tmp, index=False)
    json_tmp.write_text(json.dumps(rows, indent=2), encoding='utf-8')
    csv_tmp.replace(csv_path)
    json_tmp.replace(json_path)


def write_json(path: Path, value: dict) -> None:
    tmp = path.with_suffix(path.suffix + '.tmp')
    tmp.write_text(json.dumps(value, indent=2), encoding='utf-8')
    tmp.replace(path)


def runtime_metadata() -> dict:
    try:
        import torch_geometric
        pyg_version = torch_geometric.__version__
    except ImportError:
        pyg_version = None
    root = Path(__file__).resolve().parents[1]
    head = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=root, capture_output=True, text=True, check=False).stdout.strip() or None
    dirty = bool(subprocess.run(['git', 'status', '--porcelain'], cwd=root, capture_output=True, text=True, check=False).stdout.strip())
    return {'python': sys.version.split()[0], 'torch': torch.__version__, 'pyg': pyg_version, 'git_head': head, 'git_dirty': dirty}


def safe_path_ref(path: str | Path) -> str:
    path = Path(path)
    return path.name if path.is_absolute() else str(path)


def plot_outputs(out_dir: Path, history: list[dict], results: list[dict]) -> None:
    fig, ax = plt.subplots(figsize=(6, 4))
    for method, group in pd.DataFrame(history).groupby('method'):
        ax.plot(group['epoch'], group['loss'], marker='o', label=method)
    ax.set(xlabel='Pretraining epoch', ylabel='Loss', title='SSL pretraining loss'); ax.legend(); fig.tight_layout(); fig.savefig(out_dir / 'pretrain_loss.png', dpi=160); plt.close(fig)
    fig, ax = plt.subplots(figsize=(6, 4))
    for method, group in pd.DataFrame(results).groupby('method'):
        ax.plot(group['fraction'], group['macro_f1'], marker='o', label=method)
    ax.set(xlabel='Labeled training fraction', ylabel='Validation macro-F1', title='Label efficiency'); ax.legend(); fig.tight_layout(); fig.savefig(out_dir / 'label_efficiency.png', dpi=160); plt.close(fig)


def main() -> None:
    protocol_ap = argparse.ArgumentParser(add_help=False)
    protocol_ap.add_argument('--protocol', default=str(PROTOCOL_PATH))
    protocol_args, _ = protocol_ap.parse_known_args()
    protocol_path = Path(protocol_args.protocol)
    protocol = load_config(protocol_path)
    ap = argparse.ArgumentParser(description='Frozen SSL pilot: test split is audited but never trained on or evaluated.')
    ap.add_argument('--protocol', default=str(protocol_path), help='Frozen YAML protocol that supplies CLI defaults.')
    ap.add_argument('--data', default=protocol['data']['path']); ap.add_argument('--methods', nargs='+', default=protocol['methods'], choices=DEFAULT_METHODS)
    ap.add_argument('--fractions', nargs='+', type=float, default=protocol['downstream']['train_label_fractions']); ap.add_argument('--epochs', type=int, default=protocol['pretraining']['epochs'])
    ap.add_argument('--finetune-epochs', type=int, default=protocol['downstream']['max_epochs'])
    ap.add_argument('--early-stopping-patience', type=int, default=protocol['downstream']['early_stopping_patience'])
    ap.add_argument('--seed', type=int, default=protocol['screen']['seed']); ap.add_argument('--device', default='cpu'); ap.add_argument('--out-root', default=protocol['artifacts']['output_root'])
    ap.add_argument('--smoke', action='store_true', help='Use two epochs and only 1% labels.')
    ap.add_argument('--audit-only', action='store_true', help='Verify data and write provenance without training.')
    args = ap.parse_args(); seed_everything(args.seed)
    if args.epochs < 1 or args.finetune_epochs < 1 or args.early_stopping_patience < 1:
        raise ValueError('--epochs, --finetune-epochs, and --early-stopping-patience must be positive.')
    if args.smoke:
        args.epochs, args.finetune_epochs, args.fractions = min(args.epochs, 2), min(args.finetune_epochs, 2), [.01]
    out_dir = Path(args.out_root); out_dir.mkdir(parents=True, exist_ok=True)
    data, metadata = load_data(args.data)
    integrity = validate_data_integrity(args.data, data, protocol['data'])
    x, edge_index, y, train_mask, val_mask = (_get(data, name) for name in ('x', 'edge_index', 'y', 'train_mask', 'val_mask'))
    train_mask, val_mask = train_mask.bool(), val_mask.bool()
    device = torch.device(args.device)
    if device.type == 'cuda' and not torch.cuda.is_available(): raise ValueError('CUDA requested but unavailable.')
    if any(m == 'flow_edge_reconstruction' for m in args.methods): flow_indices = flow_feature_indices(metadata, tuple(protocol['pretraining']['flow_edge_feature_names']))
    else: flow_indices = None
    edge_attr = _get(data, 'edge_attr') if hasattr(data, 'edge_attr') else None
    config = vars(args) | {
        'data': safe_path_ref(args.data),
        'out_root': safe_path_ref(args.out_root),
        'protocol': safe_path_ref(protocol_path),
        'model': protocol['model'],
        'pretraining': protocol['pretraining'],
        'downstream': protocol['downstream'],
        'data_integrity': integrity,
        'runtime': runtime_metadata(),
        'evaluation': 'validation_only; test mask used only for split-integrity audit',
    }
    protocol_data = dict(protocol['data'])
    protocol_data['path'] = safe_path_ref(protocol_data['path'])
    write_json(out_dir / 'run_config.json', config)
    write_json(out_dir / 'data_integrity.json', {'protocol_data': protocol_data, 'actual': integrity})
    if args.audit_only:
        print(f'Data integrity audit passed; artifacts saved to {out_dir}', flush=True)
        return
    print('Pilot checks whether label-free pretraining improves validation-only 11-class recognition under matched classwise label budgets; it does not inspect test data.', flush=True)
    histories, rows = [], []
    for method in args.methods:
        print(f'[{method}] testing whether its label-free objective transfers to validation-only entity-type recognition.', flush=True)
        seed_everything(args.seed)
        pretrained = make_model(x.shape[1], protocol['model'])
        histories.extend(pretrain(method, pretrained, x, edge_index, edge_attr, flow_indices, args.epochs, protocol['pretraining'], device))
        for fraction in args.fractions:
            sampled = sample_train_mask(y, train_mask, fraction, args.seed)
            seed_everything(args.seed)
            downstream = make_model(x.shape[1], protocol['model'])
            loaded = load_encoder_prefix(downstream, pretrained)
            result = finetune(downstream, x, edge_index, y, sampled, val_mask, args.finetune_epochs, args.early_stopping_patience, protocol['downstream'], device)
            rows.append({'method': method, 'fraction': fraction, 'seed': args.seed, 'train_nodes': int(sampled.sum()), 'encoder_tensors_loaded': len(loaded), **result})
            write_validation_results(out_dir, rows)
            print(f'  validation {method} fraction={fraction:.0%}: macro_f1={rows[-1]["macro_f1"]:.4f}; best_epoch={rows[-1]["best_epoch"]}; last_epoch={rows[-1]["last_epoch"]}', flush=True)
    pd.DataFrame(histories).to_csv(out_dir / 'pretrain_history.csv', index=False)
    write_validation_results(out_dir, rows)
    (out_dir / 'notes.txt').write_text(
        'Validation-only frozen SSL pilot. Test mask was used only for split-integrity audit; '
        'no test metric was computed. -1 remains unlabeled context.\n',
        encoding='utf-8',
    )
    plot_outputs(out_dir, histories, rows)
    print(f'Saved validation-only artifacts to {out_dir}', flush=True)


if __name__ == '__main__':
    main()
