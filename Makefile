.PHONY: test audit build-label build-balanced build-temporal compare inspect smoke summarize

test:
	python -m pytest -q

audit:
	python scripts/audit_raw_labels.py --config configs/data/raw_db.yaml

build-label:
	python scripts/build_protocol_dataset.py --config configs/data/label_preserving.yaml

build-balanced:
	python scripts/build_protocol_dataset.py --config configs/data/class_balanced_khop.yaml

build-temporal:
	python scripts/build_protocol_dataset.py --config configs/data/temporal_balanced.yaml

compare:
	python scripts/compare_protocols.py --data-dir data/processed/protocols

inspect:
	python scripts/inspect_protocol_dataset.py --data-dir data/processed/protocols

smoke:
	python scripts/run_benchmark.py --data data/processed/protocols/class_balanced_khop.pt --models mlp --smoke --device cpu

summarize:
	python scripts/summarize_benchmark_runs.py --runs-dir experiments/runs --out experiments/summary/baseline_protocol_comparison.csv
