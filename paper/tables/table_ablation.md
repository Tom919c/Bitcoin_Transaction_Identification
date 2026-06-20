# Table 3: Ablation Study (class_balanced_khop)

| Variant | Macro-F1 | Minority-F1 | Weighted-F1 | Delta Macro |
|---|---|---|---|---|
| GraphSAGE | 0.5868 | 0.6239 | 0.8960 | - |
| EGS (no-direction) | 0.5837 | 0.5955 | 0.9025 | -0.0031 |
| **EGS (full)** | **0.6657** | **0.6795** | **0.9313** | **+0.0820** |

Direction-aware aggregation is the core contribution (+0.082 Macro-F1).
Edge gating alone (no-direction) does not improve over GraphSAGE.
