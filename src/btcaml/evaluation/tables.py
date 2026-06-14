from __future__ import annotations

from pathlib import Path

import pandas as pd


def results_to_markdown(csv_path: str | Path, out_path: str | Path | None = None) -> str:
    df = pd.read_csv(csv_path)
    md = df.to_markdown(index=False)
    if out_path:
        Path(out_path).parent.mkdir(parents=True, exist_ok=True)
        Path(out_path).write_text(md, encoding='utf-8')
    return md
