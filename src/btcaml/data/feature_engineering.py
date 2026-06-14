from __future__ import annotations

import numpy as np
import pandas as pd


def safe_divide(a, b, default=0.0):
    a = np.asarray(a, dtype=np.float64)
    b = np.asarray(b, dtype=np.float64)
    out = np.full_like(a, float(default), dtype=np.float64)
    np.divide(a, b, out=out, where=b != 0)
    return out


def derive_node_features(df: pd.DataFrame, global_max_block: int | None = None) -> pd.DataFrame:
    df = df.copy()
    max_block = int(global_max_block or max(
        df.get('last_transaction_in', pd.Series([0])).max(),
        df.get('last_transaction_out', pd.Series([0])).max(),
    ))
    for col in df.columns:
        if col not in {'alias', 'label'}:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    df['node_active_span_in'] = (df['last_transaction_in'] - df['first_transaction_in']).clip(lower=0)
    df['node_active_span_out'] = (df['last_transaction_out'] - df['first_transaction_out']).clip(lower=0)
    df['node_recency_in'] = (max_block - df['last_transaction_in']).clip(lower=0)
    df['node_recency_out'] = (max_block - df['last_transaction_out']).clip(lower=0)
    df['node_total_activity'] = df['total_transactions_in'] + df['total_transactions_out']
    df['degree_in_out_ratio'] = safe_divide(df['degree_in'], df['degree_out'] + 1)
    df['tx_in_out_ratio'] = safe_divide(df['total_transactions_in'], df['total_transactions_out'] + 1)
    df['amount_sent_received_ratio'] = safe_divide(df['total_sent'], df['total_received'] + 1)
    return df


def derive_edge_features(df: pd.DataFrame, global_max_block: int | None = None) -> pd.DataFrame:
    df = df.copy()
    max_block = int(global_max_block or df.get('last_seen', pd.Series([0])).max())
    for col in df.columns:
        if col not in {'a', 'b'}:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    df['edge_duration'] = (df['last_seen'] - df['reveal']).clip(lower=0)
    df['edge_recency'] = (max_block - df['last_seen']).clip(lower=0)
    df['avg_sent'] = safe_divide(df['total_sent'], df['total'].replace(0, np.nan).fillna(1))
    df['amount_range'] = (df['max_sent'] - df['min_sent']).clip(lower=0)
    df['tx_frequency'] = safe_divide(df['total'], df['edge_duration'] + 1)
    return df


def default_node_feature_columns(df: pd.DataFrame) -> list[str]:
    return [c for c in df.columns if c not in {'alias', 'label'}]


def default_edge_feature_columns(df: pd.DataFrame) -> list[str]:
    return [c for c in df.columns if c not in {'a', 'b'}]
