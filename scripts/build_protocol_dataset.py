from __future__ import annotations

import argparse
import time
from pathlib import Path

import _bootstrap  # noqa: F401
from btcaml.data.build_graph import build_protocol_dataset
from btcaml.utils.config import load_config
from btcaml.utils.run_artifacts import RunArtifacts, file_size_mb, safe_name


def main():
    ap = argparse.ArgumentParser(description='Build one protocol dataset from raw DB.')
    ap.add_argument('--config', required=True, help='configs/data/*.yaml')
    ap.add_argument('--output', default=None)
    ap.add_argument('--run-name', default=None)
    ap.add_argument('--out-root', default='experiments/runs')
    args = ap.parse_args()
    cfg = load_config(args.config)
    protocol_name = cfg.get('protocol', {}).get('name', Path(args.config).stem)
    run = RunArtifacts.create('build_dataset', root=args.out_root, run_name=args.run_name or safe_name(protocol_name))
    run.copy_file(args.config, 'config.yaml')
    print(f"Build dataset | protocol={protocol_name} | run={run.run_dir}")
    t0 = time.time()
    payload = build_protocol_dataset(cfg, output_path=args.output)
    elapsed = time.time() - t0
    meta = payload['metadata']
    out_path = Path(args.output or cfg.get('data', {}).get('processed_data_path', 'data/processed/protocols/data.pt'))
    summary = {
        'protocol': meta['protocol'].get('protocol'),
        'nodes': meta['num_nodes'],
        'edges': meta['num_edges'],
        'labeled': meta['num_labeled'],
        'output_path': str(out_path),
        'output_size_mb': round(file_size_mb(out_path), 2),
        'elapsed_sec': round(elapsed, 2),
        'elapsed_min': round(elapsed / 60, 2),
    }
    run.write_json('summary.json', summary)
    run.write_json('metadata.json', meta)
    run.write_text('summary.md', '\n'.join([
        '# Build Dataset Summary',
        '',
        f"- protocol: {summary['protocol']}",
        f"- nodes: {summary['nodes']:,}",
        f"- edges: {summary['edges']:,}",
        f"- labeled: {summary['labeled']:,}",
        f"- output: `{summary['output_path']}`",
        f"- size: {summary['output_size_mb']:.2f} MB",
        f"- elapsed: {summary['elapsed_min']:.2f} min",
        '',
    ]))
    print('Built dataset:')
    print(f"  protocol: {summary['protocol']}")
    print(f"  nodes: {summary['nodes']:,}")
    print(f"  edges: {summary['edges']:,}")
    print(f"  labeled: {summary['labeled']:,}")
    print(f"  elapsed: {elapsed:.1f}s ({elapsed/60:.1f}min)")
    print(f"  saved_log: {run.run_dir}")


if __name__ == '__main__':
    main()
