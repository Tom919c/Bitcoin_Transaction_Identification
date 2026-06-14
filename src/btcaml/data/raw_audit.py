from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

import pandas as pd

from .db import fetch_dataframe
from .label_maps import RAW_LABELS_11


@dataclass
class RawAuditResult:
    scale: dict[str, Any]
    label_counts: list[dict[str, Any]]
    per_class_temporal: list[dict[str, Any]]
    topology: dict[str, Any]
    notes: list[str]

    def to_dict(self) -> dict:
        return asdict(self)


def _safe_scalar_query(conn, query: str, default=None):
    try:
        df = fetch_dataframe(conn, query)
        return df.iloc[0, 0] if not df.empty else default
    except Exception:
        return default


def audit_raw_database(conn, node_table='node_features', edge_table='transaction_edges') -> RawAuditResult:
    scale = {
        'node_table': node_table,
        'edge_table': edge_table,
        'nodes_estimate': _safe_scalar_query(conn, f"SELECT COUNT(*) FROM {node_table}"),
        'edges_estimate': _safe_scalar_query(conn, f"SELECT COUNT(*) FROM {edge_table}"),
    }

    label_df = fetch_dataframe(conn, f"""
        SELECT UPPER(TRIM(label)) AS label, COUNT(*) AS count
        FROM {node_table}
        WHERE label IS NOT NULL AND TRIM(label) <> '' AND UPPER(TRIM(label)) <> 'NONE'
        GROUP BY UPPER(TRIM(label))
        ORDER BY count DESC
    """)
    label_counts = label_df.to_dict('records')

    temporal_df = fetch_dataframe(conn, f"""
        SELECT
            UPPER(TRIM(label)) AS label,
            AVG(first_transaction_in)::bigint AS avg_fi,
            AVG(last_transaction_in)::bigint AS avg_li,
            AVG(first_transaction_out)::bigint AS avg_fo,
            AVG(last_transaction_out)::bigint AS avg_lo,
            AVG(GREATEST(last_transaction_in - first_transaction_in, 0))::bigint AS dur_in,
            AVG(GREATEST(last_transaction_out - first_transaction_out, 0))::bigint AS dur_out,
            COUNT(*) AS n
        FROM {node_table}
        WHERE label IS NOT NULL AND TRIM(label) <> '' AND UPPER(TRIM(label)) <> 'NONE'
        GROUP BY UPPER(TRIM(label))
        ORDER BY label
    """)
    per_class_temporal = temporal_df.to_dict('records')

    degree_df = fetch_dataframe(conn, f"""
        SELECT
          MIN(degree) AS degree_min, AVG(degree)::float AS degree_avg,
          percentile_cont(0.5) WITHIN GROUP (ORDER BY degree) AS degree_med,
          percentile_cont(0.95) WITHIN GROUP (ORDER BY degree) AS degree_p95,
          percentile_cont(0.99) WITHIN GROUP (ORDER BY degree) AS degree_p99,
          MAX(degree) AS degree_max,
          MAX(degree_in) AS degree_in_max,
          MAX(degree_out) AS degree_out_max
        FROM {node_table}
    """)
    topology = degree_df.iloc[0].to_dict() if not degree_df.empty else {}

    observed = {str(r['label']).upper() for r in label_counts}
    missing = [l for l in RAW_LABELS_11 if l not in observed]
    notes = []
    if missing:
        notes.append(f'Missing expected labels in raw DB audit: {missing}')
    notes.append('Use these raw counts to validate label-preserving subgraph protocols.')
    return RawAuditResult(scale, label_counts, per_class_temporal, topology, notes)


def audit_to_text(result: RawAuditResult) -> str:
    lines = []
    lines.append('# Raw Database Label Audit')
    lines.append('')
    lines.append('## Scale')
    for k, v in result.scale.items():
        lines.append(f'- {k}: {v}')
    lines.append('')
    lines.append('## Label Counts')
    lines.append('| label | count |')
    lines.append('|---|---:|')
    for row in result.label_counts:
        lines.append(f"| {row.get('label')} | {int(row.get('count', 0)):,} |")
    lines.append('')
    lines.append('## Per-class temporal summary')
    lines.append(pd.DataFrame(result.per_class_temporal).to_markdown(index=False))
    lines.append('')
    lines.append('## Topology')
    for k, v in result.topology.items():
        lines.append(f'- {k}: {v}')
    lines.append('')
    lines.append('## Notes')
    for note in result.notes:
        lines.append(f'- {note}')
    return '\n'.join(lines)
