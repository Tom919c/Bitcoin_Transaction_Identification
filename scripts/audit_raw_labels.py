from __future__ import annotations

import argparse
from pathlib import Path

import _bootstrap  # noqa: F401
from btcaml.data.db import connect_db
from btcaml.data.raw_audit import audit_raw_database, audit_to_text
from btcaml.utils.config import load_config
from btcaml.utils.io import save_json
from btcaml.utils.run_artifacts import RunArtifacts


def main():
    ap = argparse.ArgumentParser(description='Audit raw Bitcoin DB labels, scale and temporal distribution.')
    ap.add_argument('--config', default='configs/data/raw_db.yaml')
    ap.add_argument('--out-dir', default='experiments/results/raw_audit', help='Stable/latest output dir.')
    ap.add_argument('--out-root', default='experiments/runs', help='Timestamped archive root.')
    args = ap.parse_args()
    cfg = load_config(args.config)
    data_cfg = cfg.get('data', {})
    run = RunArtifacts.create('raw_audit', root=args.out_root)
    run.copy_file(args.config, 'config.yaml')
    print(f"Raw audit | run={run.run_dir}")
    conn = connect_db(data_cfg.get('raw_db'))
    try:
        result = audit_raw_database(conn, data_cfg.get('node_table', 'node_features'), data_cfg.get('edge_table', 'transaction_edges'))
    finally:
        conn.close()
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    result_dict = result.to_dict()
    save_json(result_dict, out_dir / 'raw_audit.json')
    text = audit_to_text(result)
    (out_dir / 'raw_audit.md').write_text(text, encoding='utf-8')
    run.write_json('raw_audit.json', result_dict)
    run.write_text('raw_audit.md', text)
    print(text)
    print(f"saved_log: {run.run_dir}")


if __name__ == '__main__':
    main()
