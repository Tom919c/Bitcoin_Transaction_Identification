# Project status after first-round baseline

## Completed results already observed

| Dataset | MLP Macro-F1 | SAGE Macro-F1 | SAGE Gain | MLP Minority-F1 | SAGE Minority-F1 | SAGE Gain |
|---|---:|---:|---:|---:|---:|---:|
| label_preserving | 0.3952 | 0.4627 | +0.0675 | 0.4227 | 0.4873 | +0.0646 |
| class_balanced_khop | 0.4114 | 0.5868 | +0.1754 | 0.4510 | 0.6239 | +0.1728 |
| temporal_balanced | 0.1255 | 0.1931 | +0.0675 | 0.1852 | 0.2448 | +0.0596 |

## Current conclusion

The first-round baseline is complete. The next useful step is not to train more ordinary GNNs blindly, but to export detailed per-class results and diagnose temporal/generalization failures.

## Stage 2 code update in this package

This package now supports:

1. Per-class precision / recall / F1 export.
2. Classification report export.
3. Raw and normalized confusion matrix export.
4. Node-level prediction CSV export.
5. Post-hoc detailed evaluation from existing checkpoints.
6. Benchmark summary table generation from `experiments/runs/*/results.csv`.
7. Removal of old top-level modules and GUI code.

## Immediate local commands

If your previous run directories contain checkpoints:

```powershell
python scripts/export_detailed_eval.py --run-dir experiments/runs/20260615_000734_class_balanced_khop_mlp-sage --data data/processed/protocols/class_balanced_khop.pt --models mlp sage --device cpu
python scripts/export_detailed_eval.py --run-dir experiments/runs/20260615_000802_label_preserving_mlp-sage --data data/processed/protocols/label_preserving.pt --models mlp sage --device cpu
python scripts/export_detailed_eval.py --run-dir experiments/runs/20260615_000816_temporal_balanced_mlp-sage --data data/processed/protocols/temporal_balanced.pt --models mlp sage --device cpu
python scripts/summarize_benchmark_runs.py --runs-dir experiments/runs --out experiments/summary/baseline_protocol_comparison.csv
```

If old run directories do not contain checkpoints, rerun the three benchmark commands once. The updated code will automatically save all detailed outputs.

## Next stage after obtaining new detailed data

After the per-class tables and confusion matrices are available:

1. Identify which classes fail most under `temporal_balanced`.
2. Analyze whether PONZI / RANSOMWARE / MIXER / BRIDGE are being confused with INDIVIDUAL, EXCHANGE or BET.
3. Compare `class_balanced_khop` vs `temporal_balanced` per class.
4. Then implement EdgeGatedSAGE / ETD-SAGE with a clear target: improve the temporal and minority-class failure cases.
