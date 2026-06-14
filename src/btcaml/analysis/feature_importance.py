from __future__ import annotations

import pandas as pd


def correlation_table(df: pd.DataFrame, threshold: float = 0.8) -> pd.DataFrame:
    corr = df.corr(numeric_only=True).abs()
    rows = []
    cols = list(corr.columns)
    for i, a in enumerate(cols):
        for b in cols[i+1:]:
            if corr.loc[a, b] >= threshold:
                rows.append({'feature_a': a, 'feature_b': b, 'abs_corr': corr.loc[a, b]})
    return pd.DataFrame(rows).sort_values('abs_corr', ascending=False)
