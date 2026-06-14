from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Mapping

import yaml


def _expand_env(value: Any) -> Any:
    if isinstance(value, str):
        return os.path.expandvars(value)
    if isinstance(value, list):
        return [_expand_env(v) for v in value]
    if isinstance(value, dict):
        return {k: _expand_env(v) for k, v in value.items()}
    return value


def deep_update(base: dict, override: Mapping[str, Any]) -> dict:
    out = dict(base)
    for key, value in override.items():
        if isinstance(value, Mapping) and isinstance(out.get(key), Mapping):
            out[key] = deep_update(dict(out[key]), value)
        else:
            out[key] = value
    return out


def load_yaml(path: str | Path) -> dict:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(path)
    with path.open('r', encoding='utf-8') as f:
        data = yaml.safe_load(f) or {}
    if not isinstance(data, dict):
        raise ValueError(f'YAML root must be mapping: {path}')
    return _expand_env(data)


def load_config(*paths: str | Path) -> dict:
    cfg: dict = {}
    for path in paths:
        cfg = deep_update(cfg, load_yaml(path))
    return cfg


def ensure_dir(path: str | Path) -> Path:
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p
