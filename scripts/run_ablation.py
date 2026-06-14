from __future__ import annotations

import argparse
import subprocess
import sys


def main():
    ap = argparse.ArgumentParser(description='Ablation launcher placeholder. Use configs/experiment/ablation_etd.yaml as the manifest.')
    ap.add_argument('--configs', nargs='+', required=True)
    args = ap.parse_args()
    for cfg in args.configs:
        subprocess.check_call([sys.executable, 'scripts/run_benchmark.py', '--config', cfg])


if __name__ == '__main__':
    main()
