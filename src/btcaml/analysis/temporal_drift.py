from __future__ import annotations

import pandas as pd


def class_time_summary(labels, times) -> pd.DataFrame:
    df = pd.DataFrame({'label': labels, 'time': times})
    return df.groupby('label')['time'].agg(['count', 'min', 'median', 'max']).reset_index()
