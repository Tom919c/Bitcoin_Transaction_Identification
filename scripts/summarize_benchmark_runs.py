from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

import _bootstrap  # noqa: F401


PREFERRED_COLUMNS = [
    'run_dir',
    'results_path',
    'dataset',
    'model',
    'split',
    'best_epoch',
    'accuracy',
    'macro_f1',
    'minority_macro_f1',
    'weighted_f1',
    'num_eval',
    'auprc',
    'recall_at_1pct',
    'yield_at_1pct',
    'recall_at_5pct',
    'yield_at_5pct',
    'recall_at_10pct',
    'yield_at_10pct',
]


def _load_results_csv(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    if 'split' not in df.columns:
        return pd.DataFrame()
    test_df = df[df['split'].astype(str).str.lower() == 'test'].copy()
    if test_df.empty:
        return pd.DataFrame()
    test_df['run_dir'] = path.parent.name
    test_df['results_path'] = str(path)
    return test_df


def build_summary(runs_dir: Path) -> pd.DataFrame:
    results_paths = sorted(runs_dir.glob('*/results.csv'))
    if not results_paths:
        raise FileNotFoundError(f'No results.csv files found under {runs_dir}')

    frames = []
    for path in results_paths:
        df = _load_results_csv(path)
        if not df.empty:
            frames.append(df)

    if not frames:
        raise ValueError(f'No test split rows found in results.csv files under {runs_dir}')

    summary = pd.concat(frames, ignore_index=True, sort=False)
    for col in PREFERRED_COLUMNS:
        if col not in summary.columns:
            summary[col] = pd.NA

    remaining = [c for c in summary.columns if c not in PREFERRED_COLUMNS]
    summary = summary[PREFERRED_COLUMNS + remaining]
    summary = summary.sort_values(['dataset', 'model', 'run_dir'], kind='stable').reset_index(drop=True)
    return summary


def main() -> None:
    ap = argparse.ArgumentParser(description='Summarize benchmark run results.')
    ap.add_argument('--runs-dir', default='experiments/runs')
    ap.add_argument('--output-csv', default='experiments/summary/baseline_protocol_comparison.csv')
    ap.add_argument('--output-md', default='experiments/summary/baseline_protocol_comparison.md')
    args = ap.parse_args()

    runs_dir = Path(args.runs_dir)
    summary = build_summary(runs_dir)

    output_csv = Path(args.output_csv)
    output_md = Path(args.output_md)
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    output_md.parent.mkdir(parents=True, exist_ok=True)

    summary.to_csv(output_csv, index=False)
    output_md.write_text(summary.to_markdown(index=False), encoding='utf-8')

    print(f'Saved summary CSV: {output_csv}')
    print(f'Saved summary MD: {output_md}')
    print(summary.to_markdown(index=False))


if __name__ == '__main__':
    main()
