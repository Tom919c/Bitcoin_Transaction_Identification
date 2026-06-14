from __future__ import annotations

import argparse
import time

import _bootstrap  # noqa: F401
from btcaml.data.build_graph import build_protocol_dataset
from btcaml.utils.config import load_config


def main():
    ap = argparse.ArgumentParser(description='Build protocol dataset from raw DB.')
    ap.add_argument('--config', required=True, help='configs/data/*.yaml')
    ap.add_argument('--output', default=None)
    args = ap.parse_args()
    cfg = load_config(args.config)
    t0 = time.time()
    payload = build_protocol_dataset(cfg, output_path=args.output)
    elapsed = time.time() - t0
    meta = payload['metadata']
    print('Built dataset:')
    print(f"  protocol: {meta['protocol'].get('protocol')}")
    print(f"  nodes: {meta['num_nodes']:,}")
    print(f"  edges: {meta['num_edges']:,}")
    print(f"  labeled: {meta['num_labeled']:,}")
    print(f"  elapsed: {elapsed:.1f}s ({elapsed/60:.1f}min)")


if __name__ == '__main__':
    main()