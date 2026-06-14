.PHONY: audit build-current build-label build-balanced build-temporal compare test

audit:
	PYTHONPATH=src python scripts/audit_raw_labels.py --config configs/data/raw_db.yaml

build-current:
	PYTHONPATH=src python scripts/build_protocol_dataset.py --config configs/data/current_topk_baseline.yaml

build-label:
	PYTHONPATH=src python scripts/build_protocol_dataset.py --config configs/data/label_preserving.yaml

build-balanced:
	PYTHONPATH=src python scripts/build_protocol_dataset.py --config configs/data/class_balanced_khop.yaml

build-temporal:
	PYTHONPATH=src python scripts/build_protocol_dataset.py --config configs/data/temporal_balanced.yaml

compare:
	PYTHONPATH=src python scripts/compare_protocols.py --data-dir data/processed/protocols

test:
	PYTHONPATH=src pytest -q
