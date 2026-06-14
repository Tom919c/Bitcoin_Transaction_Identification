from __future__ import annotations

from dataclasses import dataclass, fields
import random
from typing import Iterable

import pandas as pd
from tqdm import tqdm

from .db import create_temp_alias_table, fetch_dataframe
from .label_maps import RAW_LABELS_11


@dataclass
class SamplingBudget:
    max_nodes: int = 350000
    max_neighbors_per_class: int = 30000
    max_neighbors_per_seed: int = 50
    seed_batch_size: int = 512
    background_nodes: int = 150000
    background_candidate_factor: int = 8
    background_window_attempts: int = 12
    degree_cap: int = 100000
    seed_degree_cap: int | None = None
    query_timeout_ms: int = 120000
    seed: int = 42


@dataclass
class ProtocolSelection:
    aliases: list[int]
    labeled_aliases: list[int]
    metadata: dict


class BaseProtocol:
    name = 'base'

    def __init__(self, cfg: dict):
        self.cfg = cfg
        self.node_table = cfg.get('node_table', 'node_features')
        self.edge_table = cfg.get('edge_table', 'transaction_edges')
        self.labels = [str(x).upper() for x in cfg.get('target_labels', RAW_LABELS_11)]
        budget_keys = {f.name for f in fields(SamplingBudget)}
        budget_values = {k: v for k, v in cfg.get('sampling', {}).items() if k in budget_keys}
        self.budget = SamplingBudget(**{**SamplingBudget().__dict__, **budget_values})

    def select_aliases(self, conn) -> ProtocolSelection:
        raise NotImplementedError

    def _load_all_labeled(self, conn) -> pd.DataFrame:
        tqdm.write("  Loading all labeled nodes ...")
        labels_tuple = tuple(self.labels)
        df = fetch_dataframe(conn, f"""
            SELECT alias::bigint AS alias, UPPER(TRIM(label)) AS label,
                   first_transaction_in, last_transaction_in,
                   first_transaction_out, last_transaction_out,
                   degree, degree_in, degree_out
            FROM {self.node_table}
            WHERE label IS NOT NULL
              AND TRIM(label) <> ''
              AND UPPER(TRIM(label)) = ANY(%s)
        """, (list(labels_tuple),))
        tqdm.write(f"  -> {len(df):,} labeled nodes found across {df['label'].nunique()} classes")
        return df

    def _select_background_top_activity(self, conn, exclude_aliases: Iterable[int], n: int) -> list[int]:
        if n <= 0:
            return []
        tqdm.write(f"  Selecting up to {n:,} background nodes from bounded alias windows ...")
        temp_name = 'tmp_exclude_aliases'
        create_temp_alias_table(conn, exclude_aliases, temp_name=temp_name)

        bounds = fetch_dataframe(conn, f"SELECT MIN(alias)::bigint AS min_alias, MAX(alias)::bigint AS max_alias FROM {self.node_table}")
        if bounds.empty or pd.isna(bounds.loc[0, 'min_alias']) or pd.isna(bounds.loc[0, 'max_alias']):
            return []

        min_alias = int(bounds.loc[0, 'min_alias'])
        max_alias = int(bounds.loc[0, 'max_alias'])
        candidate_limit = max(n, n * max(1, int(self.budget.background_candidate_factor)))
        rng = random.Random(self.budget.seed)
        selected: set[int] = set()
        attempts = max(1, int(self.budget.background_window_attempts))

        for attempt in range(attempts):
            if len(selected) >= n:
                break
            start_alias = rng.randint(min_alias, max_alias)
            remaining = n - len(selected)
            df = fetch_dataframe(
                conn,
                f"""
                SELECT alias FROM (
                    SELECT nf.alias::bigint AS alias,
                           (0.30 * nf.degree + 0.20 * nf.total_transactions_in +
                            0.20 * nf.total_transactions_out + 0.30 * nf.cluster_size) AS activity_score
                    FROM {self.node_table} nf
                    LEFT JOIN {temp_name} ex ON nf.alias = ex.alias
                    WHERE nf.alias >= %s
                      AND ex.alias IS NULL
                      AND (nf.label IS NULL OR TRIM(nf.label) = '' OR UPPER(TRIM(nf.label)) = 'NONE')
                      AND nf.degree <= %s
                    ORDER BY nf.alias
                    LIMIT %s
                ) cand
                ORDER BY activity_score DESC
                LIMIT %s
                """,
                (start_alias, self.budget.degree_cap, int(candidate_limit), int(remaining)),
                statement_timeout_ms=self.budget.query_timeout_ms,
            )
            selected.update(int(x) for x in df['alias'].tolist())
            tqdm.write(f"    background window {attempt + 1}/{attempts}: {len(selected):,}/{n:,} selected")

        if len(selected) < n:
            tqdm.write(f"  -> background budget underfilled ({len(selected):,}/{n:,}); continuing without full-table sort")
        else:
            tqdm.write(f"  -> {len(selected):,} background nodes selected")
        return sorted(selected)[:n]

    def _neighbors_for_labeled(self, conn, labeled: pd.DataFrame, max_per_class: int) -> list[int]:
        if max_per_class <= 0:
            return []
        all_neighbors: set[int] = set()
        classes = list(labeled.groupby('label'))
        pbar = tqdm(classes, desc="  Neighbors per class", unit="class")
        per_class_stats: dict[str, dict[str, int]] = {}
        for class_idx, (label, part) in enumerate(pbar):
            pbar.set_postfix_str(label)
            seed_degree_cap = self.budget.seed_degree_cap or self.budget.degree_cap
            expandable = part[part['degree'].fillna(0).astype(float) <= seed_degree_cap].copy()
            skipped_supernodes = len(part) - len(expandable)
            if expandable.empty:
                tqdm.write(f"    {label}: no expandable seeds ({skipped_supernodes:,} above seed_degree_cap)")
                per_class_stats[str(label)] = {
                    'neighbors': 0,
                    'new_global_neighbors': 0,
                    'expandable_seeds': 0,
                    'skipped_supernode_seeds': int(skipped_supernodes),
                }
                continue

            expandable = expandable.sample(frac=1.0, random_state=self.budget.seed + class_idx)
            seed_aliases = [int(x) for x in expandable['alias'].tolist()]
            class_neighbors: set[int] = set()
            batch_size = max(1, int(self.budget.seed_batch_size))
            per_seed_limit = max(1, int(self.budget.max_neighbors_per_seed))
            out_limit = max(1, (per_seed_limit + 1) // 2)
            in_limit = max(1, per_seed_limit // 2)

            batch_iter = range(0, len(seed_aliases), batch_size)
            for batch_start in tqdm(batch_iter, desc=f"    {label} seed batches", unit="batch", leave=False):
                if len(class_neighbors) >= max_per_class:
                    break
                batch_aliases = seed_aliases[batch_start: batch_start + batch_size]
                temp_name = 'tmp_seed_batch'
                create_temp_alias_table(conn, batch_aliases, temp_name=temp_name)
                remaining = max_per_class - len(class_neighbors)
                batch_limit = max(remaining, min(remaining * 2, len(batch_aliases) * per_seed_limit))
                try:
                    df = fetch_dataframe(
                        conn,
                        f"""
                        SELECT DISTINCT neighbor
                        FROM (
                            SELECT out_e.b::bigint AS neighbor
                            FROM {temp_name} s
                            JOIN LATERAL (
                                SELECT e.b
                                FROM {self.edge_table} e
                                WHERE e.a = s.alias
                                LIMIT %s
                            ) out_e ON TRUE
                            UNION ALL
                            SELECT in_e.a::bigint AS neighbor
                            FROM {temp_name} s
                            JOIN LATERAL (
                                SELECT e.a
                                FROM {self.edge_table} e
                                WHERE e.b = s.alias
                                LIMIT %s
                            ) in_e ON TRUE
                        ) u
                        JOIN {self.node_table} nf ON nf.alias = u.neighbor
                        WHERE u.neighbor IS NOT NULL
                          AND nf.degree <= %s
                        LIMIT %s
                        """,
                        (out_limit, in_limit, self.budget.degree_cap, int(batch_limit)),
                        statement_timeout_ms=self.budget.query_timeout_ms,
                    )
                except Exception as exc:
                    tqdm.write(f"      batch starting at {batch_start:,} timed out/failed and was skipped: {exc}")
                    continue
                for neighbor in df['neighbor'].tolist():
                    class_neighbors.add(int(neighbor))
                    if len(class_neighbors) >= max_per_class:
                        break

            new_neighbors = class_neighbors - all_neighbors
            all_neighbors.update(class_neighbors)
            per_class_stats[str(label)] = {
                'neighbors': len(class_neighbors),
                'new_global_neighbors': len(new_neighbors),
                'expandable_seeds': len(seed_aliases),
                'skipped_supernode_seeds': int(skipped_supernodes),
            }
            tqdm.write(
                f"    {label}: {len(class_neighbors):,} neighbors "
                f"(+{len(new_neighbors):,} new, {skipped_supernodes:,} supernode seeds skipped)"
            )
        self._last_neighbor_stats = per_class_stats
        return sorted(all_neighbors)


class CurrentTopKBaselineProtocol(BaseProtocol):
    name = 'current_topk_baseline'

    def select_aliases(self, conn) -> ProtocolSelection:
        raise RuntimeError(
            'current_topk_baseline is a compatibility protocol for existing data.pt. '
            'Use data.processed_data_path directly instead of rebuilding from raw DB.'
        )


class LabelPreservingProtocol(BaseProtocol):
    name = 'label_preserving'

    def select_aliases(self, conn) -> ProtocolSelection:
        labeled = self._load_all_labeled(conn)
        labeled_aliases = [int(x) for x in labeled['alias'].tolist()]
        remaining = max(0, self.budget.max_nodes - len(labeled_aliases))
        background = self._select_background_top_activity(conn, labeled_aliases, min(remaining, self.budget.background_nodes))
        aliases = sorted(set(labeled_aliases) | set(background))
        return ProtocolSelection(
            aliases=aliases[: self.budget.max_nodes],
            labeled_aliases=labeled_aliases,
            metadata={
                'protocol': self.name,
                'raw_labeled_count': len(labeled_aliases),
                'label_counts': labeled['label'].value_counts().to_dict(),
                'background_count': len(background),
                'degree_cap': self.budget.degree_cap,
                'background_candidate_factor': self.budget.background_candidate_factor,
                'background_window_attempts': self.budget.background_window_attempts,
            },
        )


class ClassBalancedKHopProtocol(BaseProtocol):
    name = 'class_balanced_khop'

    def select_aliases(self, conn) -> ProtocolSelection:
        labeled = self._load_all_labeled(conn)
        labeled_aliases = [int(x) for x in labeled['alias'].tolist()]
        tqdm.write(f"  Expanding {self.budget.max_neighbors_per_class} neighbors per class ...")
        neighbors = self._neighbors_for_labeled(conn, labeled, self.budget.max_neighbors_per_class)
        seed_plus_neighbors = sorted(set(labeled_aliases) | set(neighbors))
        remaining = max(0, self.budget.max_nodes - len(seed_plus_neighbors))
        background = self._select_background_top_activity(conn, seed_plus_neighbors, min(remaining, self.budget.background_nodes))
        aliases = sorted(set(seed_plus_neighbors) | set(background))[: self.budget.max_nodes]
        return ProtocolSelection(
            aliases=aliases,
            labeled_aliases=labeled_aliases,
            metadata={
                'protocol': self.name,
                'raw_labeled_count': len(labeled_aliases),
                'label_counts': labeled['label'].value_counts().to_dict(),
                'neighbor_count': len(neighbors),
                'background_count': len(background),
                'degree_cap': self.budget.degree_cap,
                'seed_degree_cap': self.budget.seed_degree_cap or self.budget.degree_cap,
                'max_neighbors_per_class': self.budget.max_neighbors_per_class,
                'max_neighbors_per_seed': self.budget.max_neighbors_per_seed,
                'seed_batch_size': self.budget.seed_batch_size,
                'neighbor_stats': getattr(self, '_last_neighbor_stats', {}),
            },
        )


class TemporalBalancedProtocol(ClassBalancedKHopProtocol):
    name = 'temporal_balanced'


def make_protocol(cfg: dict) -> BaseProtocol:
    name = cfg.get('protocol', {}).get('name') or cfg.get('name') or 'label_preserving'
    protocol_cfg = {**cfg.get('data', {}), **cfg.get('protocol', {})}
    if name == 'current_topk_baseline':
        return CurrentTopKBaselineProtocol(protocol_cfg)
    if name == 'label_preserving':
        return LabelPreservingProtocol(protocol_cfg)
    if name == 'class_balanced_khop':
        return ClassBalancedKHopProtocol(protocol_cfg)
    if name == 'temporal_balanced':
        return TemporalBalancedProtocol(protocol_cfg)
    raise ValueError(f'Unknown protocol: {name}')
