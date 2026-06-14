from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

import yaml

import _bootstrap  # noqa: F401
from btcaml.utils.config import load_config


def main():
    ap = argparse.ArgumentParser(description='Run benchmark for multiple seeds by materializing temp configs.')
    ap.add_argument('--config', required=True)
    ap.add_argument('--seeds', nargs='+', type=int, default=None)
    args = ap.parse_args()
    cfg = load_config(args.config)
    seeds = args.seeds or cfg.get('train', {}).get('seeds', [42, 3407, 1234])
    tmp_dir = Path('experiments/logs/multiseed_configs')
    tmp_dir.mkdir(parents=True, exist_ok=True)
    for seed in seeds:
        c = dict(cfg)
        c['train'] = dict(cfg.get('train', {}))
        c['train']['seed'] = int(seed)
        c['train']['checkpoint_dir'] = f"experiments/checkpoints/seed_{seed}"
        c.setdefault('experiment', {})['output_csv'] = f"experiments/results/seed_{seed}.csv"
        tmp = tmp_dir / f'seed_{seed}.yaml'
        tmp.write_text(yaml.safe_dump(c, allow_unicode=True), encoding='utf-8')
        print(f'Running seed {seed}')
        subprocess.check_call([sys.executable, 'scripts/run_benchmark.py', '--config', str(tmp)])


if __name__ == '__main__':
    main()
