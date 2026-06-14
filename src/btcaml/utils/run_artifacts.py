from __future__ import annotations

import json
import os
import shutil
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd


def timestamp() -> str:
    return datetime.now().strftime('%Y%m%d_%H%M%S')


def safe_name(name: str) -> str:
    return ''.join(c if c.isalnum() or c in {'-', '_', '.'} else '_' for c in str(name)).strip('_') or 'run'


def make_run_dir(task: str, root: str | Path = 'experiments/runs', run_name: str | None = None) -> Path:
    task = safe_name(task)
    suffix = safe_name(run_name) if run_name else task
    path = Path(root) / f'{timestamp()}_{suffix}'
    path.mkdir(parents=True, exist_ok=False)
    return path


def json_default(obj: Any):
    try:
        import numpy as np
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
    except Exception:
        pass
    try:
        import torch
        if torch.is_tensor(obj):
            return obj.detach().cpu().tolist()
    except Exception:
        pass
    if isinstance(obj, Path):
        return str(obj)
    raise TypeError(f'Object of type {type(obj).__name__} is not JSON serializable')


@dataclass
class RunArtifacts:
    task: str
    run_dir: Path
    latest_dir: Path | None = None
    messages: list[str] = field(default_factory=list)

    @classmethod
    def create(
        cls,
        task: str,
        root: str | Path = 'experiments/runs',
        latest_root: str | Path | None = 'experiments/latest',
        run_name: str | None = None,
    ) -> 'RunArtifacts':
        run_dir = make_run_dir(task, root=root, run_name=run_name)
        latest_dir = Path(latest_root) / safe_name(task) if latest_root else None
        if latest_dir:
            latest_dir.mkdir(parents=True, exist_ok=True)
        return cls(task=safe_name(task), run_dir=run_dir, latest_dir=latest_dir)

    def log(self, message: str, console: bool = True) -> None:
        msg = str(message)
        self.messages.append(msg)
        if console:
            print(msg)

    def write_text(self, name: str, text: str, latest: bool = True) -> Path:
        path = self.run_dir / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding='utf-8')
        if latest and self.latest_dir:
            latest_path = self.latest_dir / name
            latest_path.parent.mkdir(parents=True, exist_ok=True)
            latest_path.write_text(text, encoding='utf-8')
        return path

    def write_json(self, name: str, obj: Any, latest: bool = True) -> Path:
        text = json.dumps(obj, ensure_ascii=False, indent=2, default=json_default)
        return self.write_text(name, text, latest=latest)

    def write_dataframe(self, name: str, df: pd.DataFrame, latest: bool = True) -> Path:
        path = self.run_dir / name
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.suffix.lower() == '.csv':
            df.to_csv(path, index=False)
        elif path.suffix.lower() == '.md':
            path.write_text(df.to_markdown(index=False), encoding='utf-8')
        else:
            raise ValueError(f'Unsupported dataframe output: {path}')
        if latest and self.latest_dir:
            latest_path = self.latest_dir / name
            latest_path.parent.mkdir(parents=True, exist_ok=True)
            if path.suffix.lower() == '.csv':
                df.to_csv(latest_path, index=False)
            else:
                latest_path.write_text(df.to_markdown(index=False), encoding='utf-8')
        return path

    def copy_file(self, src: str | Path, name: str | None = None, latest: bool = True) -> Path:
        src = Path(src)
        dst = self.run_dir / (name or src.name)
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        if latest and self.latest_dir:
            latest_dst = self.latest_dir / (name or src.name)
            latest_dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, latest_dst)
        return dst

    def flush_log(self, name: str = 'console_summary.log', latest: bool = True) -> Path:
        return self.write_text(name, '\n'.join(self.messages) + ('\n' if self.messages else ''), latest=latest)


def file_size_mb(path: str | Path) -> float:
    p = Path(path)
    return p.stat().st_size / (1024 * 1024) if p.exists() else 0.0
