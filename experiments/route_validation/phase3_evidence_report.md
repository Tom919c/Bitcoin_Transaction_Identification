# Phase 3 Evidence Report

## 1. Task Completion

| Task | Status | Output Files |
|---|---|---|
| A: Conservative Sensitive Ranking | DONE | experiments/ranking/*.csv, sensitive_ranking_summary.md |
| B: Temporal Feature Failure | DONE | experiments/diagnostics/temporal_feature_*.csv, *_delta_*.csv, temporal_feature_failure_report.md |
| C: Confusion Case Study | DONE | experiments/case_studies/*.csv, *.md |

## 2. Key Numbers

### Task A: Ranking

- Conservative AUPRC: 0.7207 - 0.7739 (mean ~0.748, 3 seeds)
- Conservative AUROC: 0.9863 - 0.9878
- Conservative Recall@5%: 0.8177 - 0.8343
- Conservative Recall@10%: 0.9724 - 0.9890
- Extended AUPRC: 0.9846 - 0.9879
- Extended-AUPRC gap vs Conservative: ~0.24 (BET/GAMBLING dominate extended)

### Task B: Temporal Feature Failure

- CBK: removing temporal features improves 9/11 classes
- Temporal: removing temporal features improves 7/11 classes
- CBK edge feature drift: very small (KS < 0.04)
- Temporal edge feature drift: MASSIVE (KS up to 0.57 for last_seen, frequency, reveal)
- Conclusion: temporal features exhibit severe drift under temporal split, acting as noise

### Task C: Confusion

- MIXER->EXCHANGE: 4 misclassified, 6 correct (support=16 total)
- GAMBLING->EXCHANGE: 34 misclassified, 199 correct
- RANSOMWARE->INDIVIDUAL: 0 misclassified! (good directional discrimination)
- PONZI->EXCHANGE: 7 misclassified
- MIXER same-label neighbor ratio: 0.4% (almost no local signal)

## 3. Corrections to route_gate_decision.md

1. Conservative ranking is STRONG (AUPRC ~0.75, AUROC ~0.99): this strengthens the application contribution claim
2. RANSOMWARE->INDIVIDUAL confusion is ZERO: directional aggregation works well for this pair
3. Temporal feature drift is now QUANTIFIED: KS=0.57 for temporal_balanced vs KS=0.04 for CBK, confirming pseudo-correlation in random split

## 4. Evidence Strengthening Current Mainline

- Direction-aware EGS consistently outperforms non-directional models
- Conservative ranking (PONZI/RANSOMWARE/MIXER) AUPRC=0.75 supports real AML application
- RANSOMWARE is well-separated from INDIVIDUAL by directional features
- Temporal feature failure is now explained: drift + pseudo-correlation, not just noise

## 5. Evidence Weakening Current Mainline

- MIXER has almost no node-level signal (0.4% same-label ratio, 16 test nodes)
- Extended ranking is much higher than conservative, meaning easy classes inflate ranking metrics
- Temporal OOD gap (0.25 vs 0.65) still not solved

## 6. Unsolved Problems

- Temporal OOD: no method has closed the 0.40 gap
- MIXER classification: node-level may be fundamentally insufficient
- Conservative ranking at 1% yield: only 0.35 recall (need to review 5% of nodes to catch 83% of high-risk)
- Whether temporal features can be salvaged with better encoding/filtering