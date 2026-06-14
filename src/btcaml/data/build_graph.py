from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch
from tqdm import tqdm

from .db import connect_db, create_temp_alias_table, fetch_dataframe, stream_dataframe_regular
from .feature_engineering import (
    default_edge_feature_columns,
    default_node_feature_columns,
    derive_edge_features,
    derive_node_features,
)
from .label_maps import UNKNOWN_LABEL, map_label, normalize_label, risk_binary_label
from .protocols import ProtocolSelection, make_protocol
from .splits import build_split
from .transforms import FeatureTransformConfig, FeatureTransformer
from ..utils.io import atomic_torch_save, save_json


def _make_data_obj(**kwargs):
    try:
        from torch_geometric.data import Data
        return Data(**kwargs)
    except Exception:
        return dict(kwargs)


def load_nodes_by_aliases(conn, node_table: str, aliases: list[int]) -> pd.DataFrame:
    create_temp_alias_table(conn, aliases, temp_name='tmp_selected_aliases')
    return fetch_dataframe(conn, f"""
        SELECT nf.*
        FROM {node_table} nf
        JOIN tmp_selected_aliases s ON nf.alias = s.alias
        ORDER BY nf.alias
    """)


def stream_edges_between_selected(
    conn,
    edge_table: str,
    aliases: list[int],
    chunk_size: int = 200000,
    statement_timeout_ms: int | None = None,
):
    create_temp_alias_table(conn, aliases, temp_name='tmp_selected_aliases')
    query = f"""
        SELECT e.*
        FROM tmp_selected_aliases sa
        JOIN {edge_table} e ON e.a = sa.alias
        JOIN tmp_selected_aliases sb ON e.b = sb.alias
    """
    yield from stream_dataframe_regular(
        conn, query, chunk_size=chunk_size, statement_timeout_ms=statement_timeout_ms
    )


def build_protocol_dataset(cfg: dict, output_path: str | Path | None = None) -> dict[str, Any]:
    data_cfg = cfg.get('data', {})
    raw_db = data_cfg.get('raw_db')
    node_table = data_cfg.get('node_table', 'node_features')
    edge_table = data_cfg.get('edge_table', 'transaction_edges')
    label_space = str(data_cfg.get('label_space', '11'))
    output_path = Path(output_path or data_cfg.get('processed_data_path', 'data/processed/protocols/data.pt'))
    output_path.parent.mkdir(parents=True, exist_ok=True)

    conn = connect_db(raw_db)
    try:
        # Step 1: Protocol selection
        tqdm.write("[1/7] Selecting nodes by protocol ...")
        protocol = make_protocol(cfg)
        selection = protocol.select_aliases(conn)
        tqdm.write(f"       -> {len(selection.aliases):,} nodes selected")

        # Step 2: Load node features
        tqdm.write("[2/7] Loading node features from DB ...")
        nodes = load_nodes_by_aliases(conn, node_table, selection.aliases)
        if nodes.empty:
            raise ValueError('No nodes selected; check protocol config.')
        nodes['alias'] = nodes['alias'].astype(int)
        tqdm.write(f"       -> {len(nodes):,} rows loaded")

        # Step 3: Derive node features
        tqdm.write("[3/7] Deriving node features ...")
        max_block = int(max(nodes['last_transaction_in'].max(), nodes['last_transaction_out'].max()))
        nodes = derive_node_features(nodes, global_max_block=max_block)
        node_feature_cols = cfg.get('features', {}).get('node_columns') or default_node_feature_columns(nodes)
        label_names = nodes['label'].apply(normalize_label)
        y = torch.tensor([map_label(x, label_space=label_space) for x in label_names], dtype=torch.long)
        risk_group = cfg.get('task', {}).get('risk_group', 'conservative_sensitive')
        risk_y = torch.tensor([risk_binary_label(x, risk_group) if map_label(x, label_space=label_space) != UNKNOWN_LABEL else -1 for x in label_names], dtype=torch.long)
        alias_to_idx = {int(a): i for i, a in enumerate(nodes['alias'].tolist())}
        tqdm.write(f"       -> {len(node_feature_cols)} features, {int((y != UNKNOWN_LABEL).sum().item()):,} labeled")

        # Step 4: Split & transform
        tqdm.write("[4/7] Building splits & fitting transforms ...")
        time_values = torch.tensor(nodes[cfg.get('split', {}).get('time_column', 'last_transaction_in')].astype(float).to_numpy(), dtype=torch.float32)
        split = build_split(y, time_values, cfg.get('split', {'type': 'random_stratified'}))

        trans_cfg = cfg.get('transform', {})
        node_log_cols = [c for c in node_feature_cols if any(tok in c for tok in ['sent', 'received', 'degree', 'transactions', 'cluster', 'span', 'activity'])]
        transformer = FeatureTransformer(FeatureTransformConfig(
            log1p_columns=trans_cfg.get('log1p_node_columns', node_log_cols),
            clip_quantile=trans_cfg.get('clip_quantile', 0.995),
            robust=trans_cfg.get('robust', False),
        ))
        train_node_df = nodes.loc[split.train_mask.numpy(), node_feature_cols]
        transformer.fit(train_node_df, node_feature_cols)
        nodes_t = transformer.transform(nodes[node_feature_cols])
        x = torch.tensor(nodes_t[node_feature_cols].to_numpy(dtype='float32'), dtype=torch.float32)
        tqdm.write("       -> done")

        # Step 5: Stream edges (slowest step)
        tqdm.write("[5/7] Streaming edges from DB (slowest step; first chunk can take several minutes) ...")
        edge_indices = []
        edge_attrs = []
        edge_feature_cols = None
        chunk_size = int(data_cfg.get('edge_chunk_size', 200000))
        edge_global_max = max_block
        edge_transformer = None
        total_edges = 0
        pbar = tqdm(unit=" chunks", desc="       edges")
        protocol_sampling = cfg.get('protocol', {}).get('sampling', {})
        statement_timeout_ms = int(
            data_cfg.get('edge_query_timeout_ms', data_cfg.get('query_timeout_ms', protocol_sampling.get('query_timeout_ms', 0))) or 0
        )
        for chunk in stream_edges_between_selected(
            conn, edge_table, selection.aliases, chunk_size=chunk_size,
            statement_timeout_ms=statement_timeout_ms or None,
        ):
            chunk['a'] = chunk['a'].astype(int)
            chunk['b'] = chunk['b'].astype(int)
            chunk = derive_edge_features(chunk, global_max_block=edge_global_max)
            if edge_feature_cols is None:
                edge_feature_cols = cfg.get('features', {}).get('edge_columns') or default_edge_feature_columns(chunk)
                edge_log_cols = [c for c in edge_feature_cols if any(tok in c for tok in ['sent', 'amount', 'total', 'avg', 'range'])]
                edge_transformer = FeatureTransformer(FeatureTransformConfig(
                    log1p_columns=trans_cfg.get('log1p_edge_columns', edge_log_cols),
                    clip_quantile=trans_cfg.get('clip_quantile', 0.995),
                    robust=trans_cfg.get('robust', False),
                ))
                edge_transformer.fit(chunk[edge_feature_cols], edge_feature_cols)
            src = chunk['a'].map(alias_to_idx)
            dst = chunk['b'].map(alias_to_idx)
            valid = src.notna() & dst.notna()
            n_valid = int(valid.sum())
            if n_valid == 0:
                pbar.update(1)
                continue
            total_edges += n_valid
            src_np = src[valid].astype('int64').to_numpy(copy=False)
            dst_np = dst[valid].astype('int64').to_numpy(copy=False)
            edge_indices.append(torch.from_numpy(np.vstack((src_np, dst_np))).long())
            chunk_t = edge_transformer.transform(chunk.loc[valid, edge_feature_cols])
            edge_attrs.append(torch.from_numpy(chunk_t[edge_feature_cols].to_numpy(dtype='float32', copy=False)))
            pbar.update(1)
            pbar.set_postfix(edges=f"{total_edges:,}")
        pbar.close()
        tqdm.write(f"       -> {total_edges:,} edges collected")

        # Step 6: Concatenate
        tqdm.write("[6/7] Concatenating edge tensors ...")
        if edge_indices:
            edge_index = torch.cat(edge_indices, dim=1)
            edge_attr = torch.cat(edge_attrs, dim=0)
        else:
            edge_index = torch.empty((2, 0), dtype=torch.long)
            edge_attr = torch.empty((0, 0), dtype=torch.float32)
            edge_feature_cols = []
        tqdm.write("       -> done")

        # Step 7: Save
        tqdm.write(f"[7/7] Saving to {output_path} ...")
        data_obj = _make_data_obj(
            x=x,
            edge_index=edge_index,
            edge_attr=edge_attr,
            y=y,
            risk_y=risk_y,
            train_mask=split.train_mask,
            val_mask=split.val_mask,
            test_mask=split.test_mask,
            alias=torch.tensor(nodes['alias'].to_numpy(dtype='int64'), dtype=torch.long),
            node_time=time_values,
        )
        metadata = {
            'protocol': selection.metadata,
            'label_space': label_space,
            'node_feature_columns': node_feature_cols,
            'edge_feature_columns': edge_feature_cols,
            'split': split.metadata,
            'node_transform': transformer.state_dict(),
            'edge_transform': edge_transformer.state_dict() if edge_transformer else None,
            'num_nodes': int(x.shape[0]),
            'num_edges': int(edge_index.shape[1]),
            'num_labeled': int((y != UNKNOWN_LABEL).sum().item()),
        }
        payload = {'data': data_obj, 'metadata': metadata}
        atomic_torch_save(payload, output_path)
        save_json(metadata, output_path.with_suffix('.metadata.json'))
        tqdm.write("       -> all done")
        return payload
    finally:
        conn.close()
