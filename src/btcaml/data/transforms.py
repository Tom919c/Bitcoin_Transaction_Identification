from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

import numpy as np
import pandas as pd


@dataclass
class FeatureTransformConfig:
    log1p_columns: list[str] = field(default_factory=list)
    clip_quantile: float | None = 0.995
    robust: bool = False
    eps: float = 1e-9


class FeatureTransformer:
    """Train-only feature transformer: log1p -> quantile clipping -> standard/robust scaling."""

    def __init__(self, config: FeatureTransformConfig):
        self.config = config
        self.columns_: list[str] = []
        self.clip_values_: dict[str, float] = {}
        self.center_: dict[str, float] = {}
        self.scale_: dict[str, float] = {}

    def _prepare(self, df: pd.DataFrame, columns: Iterable[str]) -> pd.DataFrame:
        out = df.copy()
        for c in columns:
            out[c] = pd.to_numeric(out[c], errors='coerce').replace([np.inf, -np.inf], np.nan).fillna(0.0)
            if c in self.config.log1p_columns:
                out[c] = np.log1p(np.clip(out[c].astype(float), 0, None))
        return out

    def fit(self, df: pd.DataFrame, columns: list[str]) -> 'FeatureTransformer':
        self.columns_ = list(columns)
        prep = self._prepare(df, self.columns_)
        for c in self.columns_:
            s = prep[c].astype(float)
            if self.config.clip_quantile is not None:
                q = float(s.quantile(self.config.clip_quantile))
                self.clip_values_[c] = q
                s = s.clip(upper=q)
            if self.config.robust:
                center = float(s.median())
                q75 = float(s.quantile(0.75))
                q25 = float(s.quantile(0.25))
                scale = max(q75 - q25, self.config.eps)
            else:
                center = float(s.mean())
                scale = max(float(s.std(ddof=0)), self.config.eps)
            self.center_[c] = center
            self.scale_[c] = scale
        return self

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        if not self.columns_:
            raise RuntimeError('FeatureTransformer is not fitted')
        out = self._prepare(df, self.columns_)
        for c in self.columns_:
            if c in self.clip_values_:
                out[c] = out[c].astype(float).clip(upper=self.clip_values_[c])
            out[c] = (out[c].astype(float) - self.center_[c]) / self.scale_[c]
        return out

    def fit_transform(self, df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
        return self.fit(df, columns).transform(df)

    def state_dict(self) -> dict:
        return {
            'columns': self.columns_,
            'clip_values': self.clip_values_,
            'center': self.center_,
            'scale': self.scale_,
            'config': self.config.__dict__,
        }
