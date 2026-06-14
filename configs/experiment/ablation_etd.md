# ETD-GNN ablation manifest

Run these after `temporal_balanced.pt` has been built:

```bash
PYTHONPATH=src python scripts/run_benchmark.py --config configs/experiment/paper_main_etd.yaml
# create variants by copying paper_main_etd.yaml and changing model/data/features:
# - w/o edge features
# - w/o temporal features
# - w/o direction split
# - focal loss
```
