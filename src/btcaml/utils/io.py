from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd
import torch


def _json_default(obj):
    """Fallback for numpy/pandas scalar types that json.dumps cannot serialize."""
    import numpy as np
    if isinstance(obj, np.integer):
        return int(obj)
    if isinstance(obj, np.floating):
        return float(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


def atomic_torch_save(obj: Any, path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + '.tmp')
    torch.save(obj, tmp)
    tmp.replace(path)


def save_json(obj: Any, path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2, default=_json_default), encoding='utf-8')


def load_json(path: str | Path) -> Any:
    return json.loads(Path(path).read_text(encoding='utf-8'))


def save_dataframe(df: pd.DataFrame, path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.suffix.lower() == '.csv':
        df.to_csv(path, index=False)
    elif path.suffix.lower() in {'.json', '.jsonl'}:
        df.to_json(path, orient='records', lines=path.suffix.lower()=='.jsonl', force_ascii=False)
    else:
        raise ValueError(f'Unsupported table format: {path}')