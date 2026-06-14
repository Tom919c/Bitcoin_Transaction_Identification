# Bitcoin Transaction Identification Research v2.1

This package is the first research-oriented refactor for a high-quality paper project on Bitcoin entity risk identification.

## Core change in v2.1

The old `data.pt` is no longer treated as the final main dataset. It is now **Protocol A / current_topk_baseline** only. EDA showed that the original DB contains 11 labels, while the old TopK subgraph keeps only 5 supervised categories and drops AML-critical categories such as PONZI, RANSOMWARE and MIXER.

Therefore, the new project pipeline is:

```text
Raw PostgreSQL DB
  -> raw label audit
  -> label-preserving / class-balanced / temporal-balanced protocol datasets
  -> baseline diagnosis
  -> ETD-GNN model experiments
  -> ablation + multi-seed + paper tables
```

## First commands to run locally

Create `.env` from `.env.example`, then:

```bash
conda activate MCM
set PYTHONPATH=src  # Windows PowerShell: $env:PYTHONPATH="src"
python scripts/audit_raw_labels.py --config configs/data/raw_db.yaml
python scripts/build_protocol_dataset.py --config configs/data/label_preserving.yaml
python scripts/build_protocol_dataset.py --config configs/data/class_balanced_khop.yaml
python scripts/build_protocol_dataset.py --config configs/data/temporal_balanced.yaml
python scripts/compare_protocols.py --data-dir data/processed/protocols
```

For legacy baseline:

```bash
python scripts/run_benchmark.py --config configs/experiment/baseline_current_topk_mlp.yaml
```

## Important notes

- Database scripts require your local PostgreSQL DB and `BITCOIN_DB_URL`.
- GNN baselines require `torch_geometric`; the ETD-SAGE model itself only uses PyTorch operations.
- `current_topk_baseline` is intentionally preserved as a negative/control protocol.
- Main paper protocol should be `temporal_balanced.pt` after raw DB rebuilding succeeds.

See `docs/research/` for the full research roadmap and Codex refactor specification.
