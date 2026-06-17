# BTC-AML Research Code

Research code for **sampling-aware Bitcoin entity identification**.

Current main task:

```text
11-class long-tailed Bitcoin entity classification
-1 = UNLABELED / context node, ignored by loss and metrics
0..10 = supervised entity classes
```

Current stable datasets expected locally:

```text
data/processed/protocols/label_preserving.pt
data/processed/protocols/class_balanced_khop.pt
data/processed/protocols/temporal_balanced.pt
```

## Clean project layout

```text
src/btcaml/                  Core package
  data/                      Raw DB audit, protocol dataset building, label maps
  models/                    MLP, GraphSAGE, EdgeTransformer, ETD-SAGE
  training/                  Full-batch trainer and losses
  evaluation/                Metrics, detailed eval export, ranking metrics
  analysis/                  Drift / homophily / supernode analysis utilities

scripts/                     Runnable experiment commands
configs/                     Data, model and training configs
docs/                        Operation notes and current project status
tests/                       Unit tests
data/                        Local data mount point; large .pt files are not shipped
experiments/                 Local run outputs; not shipped
```

Old top-level modules (`models/`, `training/`, `interface/`, legacy `data/*.py`) have been removed. Use only `src/btcaml` and the scripts in `scripts/`.

## First check after unpacking

```powershell
conda activate MCM
python -m pytest -q
```

## First-round baseline commands

```powershell
python scripts/run_benchmark.py --data data/processed/protocols/label_preserving.pt --models mlp sage --device cpu
python scripts/run_benchmark.py --data data/processed/protocols/class_balanced_khop.pt --models mlp sage --device cpu
python scripts/run_benchmark.py --data data/processed/protocols/temporal_balanced.pt --models mlp sage --device cpu
```

Each benchmark now exports:

```text
results.csv
results.md
<model>/model_config.json
<model>/checkpoints/best.pt
<model>/train_history.json
<model>/evaluation/{train,val,test}_per_class.csv
<model>/evaluation/{train,val,test}_classification_report.csv
<model>/evaluation/{train,val,test}_confusion_matrix.csv
<model>/evaluation/{train,val,test}_confusion_matrix_norm_true.csv
<model>/evaluation/{train,val,test}_predictions.csv
```

## Export detailed metrics from an existing checkpoint

No retraining is needed if the run directory contains `<model>/checkpoints/best.pt`.

```powershell
python scripts/export_detailed_eval.py `
  --run-dir experiments/runs/20260615_000734_class_balanced_khop_mlp-sage `
  --data data/processed/protocols/class_balanced_khop.pt `
  --models mlp sage `
  --device cpu
```

If a historical run contains only `results.csv` and no checkpoint/predictions, confusion matrices cannot be reconstructed; rerun the benchmark once with the updated code.

## Summarize benchmark runs

```powershell
python scripts/summarize_benchmark_runs.py --runs-dir experiments/runs --out experiments/summary/baseline_protocol_comparison.csv
```

## Current interpretation of first-round results

The current first-round results show:

1. GraphSAGE outperforms MLP on all three new 11-class protocols.
2. `class_balanced_khop` is the strongest main training protocol so far.
3. `temporal_balanced` is much harder, making temporal generalization the next main research challenge.

Next code stage after detailed metric export: inspect per-class failures and temporal drift before implementing EdgeGatedSAGE / ETD-SAGE.
