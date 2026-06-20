# Table 4: Sensitive Ranking (EGS multi-seed, class_balanced_khop)

| Risk Group | AUPRC | AUROC | Recall@1% | Recall@5% | Recall@10% |
|---|---|---|---|---|---|
| Conservative (PONZI/RANSOMWARE/MIXER) | 0.748 +/- 0.022 | 0.987 +/- 0.001 | 0.346 +/- 0.007 | 0.827 +/- 0.007 | 0.982 +/- 0.007 |
| Extended (+BET/GAMBLING/MARKETPLACE/BRIDGE) | 0.986 +/- 0.002 | 0.994 +/- 0.001 | 0.037 +/- 0.000 | 0.185 +/- 0.000 | 0.370 +/- 0.000 |

Conservative ranking targets high-sensitivity AML classes.
Extended ranking is inflated by easy classes (BET, GAMBLING) with high recall.
