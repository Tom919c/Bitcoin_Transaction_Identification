from __future__ import annotations

import argparse
from pathlib import Path

import _bootstrap  # noqa: F401
from btcaml.data.db import connect_db
from btcaml.data.raw_audit import audit_raw_database, audit_to_text
from btcaml.utils.config import load_config
from btcaml.utils.io import save_json


def main():
    ap = argparse.ArgumentParser(description='Audit raw Bitcoin DB labels, scale and temporal distribution.')
    ap.add_argument('--config', default='configs/data/raw_db.yaml')
    ap.add_argument('--out-dir', default='experiments/results/raw_audit')
    args = ap.parse_args()
    cfg = load_config(args.config)
    data_cfg = cfg.get('data', {})
    conn = connect_db(data_cfg.get('raw_db'))
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    try:
        result = audit_raw_database(conn, data_cfg.get('node_table', 'node_features'), data_cfg.get('edge_table', 'transaction_edges'))
    finally:
        conn.close()
    save_json(result.to_dict(), out_dir / 'raw_audit.json')
    text = audit_to_text(result)
    (out_dir / 'raw_audit.md').write_text(text, encoding='utf-8')
    print(text)


if __name__ == '__main__':
    main()
