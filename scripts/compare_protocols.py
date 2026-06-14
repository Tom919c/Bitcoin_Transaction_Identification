from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

import _bootstrap  # noqa: F401
from btcaml.data.label_maps import UNKNOWN_LABEL, get_label_space
from btcaml.utils.run_artifacts import RunArtifacts


def _load_payload(path: Path):
    import torch
    try:
        return torch.load(path, map_location='cpu', weights_only=False)
    except TypeError:
        return torch.load(path, map_location='cpu')


def _get(data, name):
    if hasattr(data, name):
        return getattr(data, name)
    return data[name]


def summarize(path: Path) -> dict:
    payload = _load_payload(path)
    data = payload.get('data', payload)
    meta = payload.get('metadata', {})
    y = _get(data, 'y')
    edge_index = _get(data, 'edge_index')
    label_space = str(meta.get('label_space', '11'))
    labels = get_label_space(label_space).labels
    row = {
        'dataset': path.stem,
        'path': str(path),
        'protocol': meta.get('protocol', {}).get('protocol', meta.get('protocol', {}).get('name', 'unknown')),
        'nodes': int(_get(data, 'x').shape[0]),
        'edges': int(edge_index.shape[1]),
        'labeled': int((y != UNKNOWN_LABEL).sum().item()),
        'label_space': label_space,
    }
    for i, label in enumerate(labels):
        row[f'label_{label}'] = int((y == i).sum().item())
    row['covered_classes'] = int(sum(row.get(f'label_{l}', 0) > 0 for l in labels))
    return row


def main():
    ap = argparse.ArgumentParser(description='Compare protocol dataset .pt files.')
    ap.add_argument('--data-dir', default='data/processed/protocols')
    ap.add_argument('--out', default='experiments/results/protocol_comparison.csv')
    ap.add_argument('--out-root', default='experiments/runs')
    args = ap.parse_args()
    paths = sorted(Path(args.data_dir).glob('*.pt'))
    if not paths:
        raise FileNotFoundError(f'No .pt files found in {args.data_dir}')
    rows = [summarize(p) for p in paths]
    df = pd.DataFrame(rows)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False)
    md = df.to_markdown(index=False)
    out.with_suffix('.md').write_text(md, encoding='utf-8')
    run = RunArtifacts.create('protocol_comparison', root=args.out_root)
    run.write_dataframe('protocol_comparison.csv', df)
    run.write_text('protocol_comparison.md', md)
    print(md)
    print(f"saved_log: {run.run_dir}")


if __name__ == '__main__':
    main()
