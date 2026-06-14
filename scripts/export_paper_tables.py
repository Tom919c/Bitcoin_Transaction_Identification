from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


def main():
    ap = argparse.ArgumentParser(description='Export CSV results as Markdown tables for paper drafts.')
    ap.add_argument('--input', required=True)
    ap.add_argument('--output', default='experiments/paper_tables/table.md')
    args = ap.parse_args()
    df = pd.read_csv(args.input)
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(df.to_markdown(index=False), encoding='utf-8')
    print(out)


if __name__ == '__main__':
    main()
