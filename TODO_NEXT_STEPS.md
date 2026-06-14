# TODO Next Steps

## Step 1: Verify environment

```bash
python -m pytest -q
python -c "import torch; print(torch.__version__)"
python -c "import torch_geometric; print(torch_geometric.__version__)"
```

## Step 2: Run raw audit

```bash
python scripts/audit_raw_labels.py --config configs/data/raw_db.yaml
```

Send back:

- `experiments/results/raw_audit/raw_audit.md`
- `experiments/results/raw_audit/raw_audit.json`

## Step 3: Build protocol datasets

Start with label-preserving. If it is too slow, reduce `max_nodes`, `background_nodes` and `max_neighbors_per_class` in the YAML.

```bash
python scripts/build_protocol_dataset.py --config configs/data/label_preserving.yaml
python scripts/build_protocol_dataset.py --config configs/data/class_balanced_khop.yaml
python scripts/build_protocol_dataset.py --config configs/data/temporal_balanced.yaml
python scripts/compare_protocols.py --data-dir data/processed/protocols
```

Send back:

- `experiments/results/protocol_comparison.csv`
- `experiments/results/protocol_comparison.md`
- each `*.metadata.json`

## Step 4: Baseline

```bash
python scripts/run_benchmark.py --config configs/experiment/baseline_current_topk_mlp.yaml
```

After protocol data is built, run the paper main config:

```bash
python scripts/run_benchmark.py --config configs/experiment/paper_main_etd.yaml
```
