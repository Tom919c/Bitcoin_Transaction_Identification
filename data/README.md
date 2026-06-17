# data/

Large protocol datasets are not stored in git or in this zip package.

Expected local paths after building or copying datasets:

```text
data/processed/protocols/label_preserving.pt
data/processed/protocols/class_balanced_khop.pt
data/processed/protocols/temporal_balanced.pt
```

Use `scripts/build_protocol_dataset.py` to rebuild them from the raw PostgreSQL database.
