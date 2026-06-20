# Table 1: Dataset Protocols

| Protocol | Nodes | Edges | Labeled | Supervised Classes | Split Type | Purpose |
|---|---|---|---|---|---|---|
| label_preserving | ~150K | ~156K | 2,961 | 11 | Random stratified | Sampling bias control |
| class_balanced_khop | 242,226 | 1,237,757 | 34,098 | 11 | Random stratified | Primary training |
| temporal_balanced | 242,352 | 1,239,058 | 34,098 | 11 | Temporal (classwise) | Temporal generalization |
