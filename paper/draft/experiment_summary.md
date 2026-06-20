# Experiment Summary (Phase 0-3)

## Phase 0: Environment Verification
- pytest: 9/9 passed
- All 3 protocol datasets verified
- Label logic: -1=unlabeled, 0-10=11 supervised classes

## Phase 1: Baseline Results

### class_balanced_khop (Primary Protocol)
| Model | Macro-F1 | Minority-F1 | Weighted-F1 |
|---|---|---|---|
| MLP (3 seeds) | 0.4077 +/- 0.001 | 0.4408 +/- 0.008 | 0.7340 +/- 0.002 |
| GraphSAGE (3 seeds) | 0.5785 +/- 0.010 | 0.6122 +/- 0.009 | 0.8953 +/- 0.001 |
| EGS (3 seeds) | 0.6505 +/- 0.014 | 0.6667 +/- 0.016 | 0.9240 +/- 0.004 |

### temporal_balanced (Temporal Generalization)
| Model | Macro-F1 | Minority-F1 | Weighted-F1 |
|---|---|---|---|
| MLP | 0.1255 | 0.1852 | 0.1680 |
| GraphSAGE (3 seeds) | 0.1899 +/- 0.007 | 0.2363 +/- 0.008 | 0.3363 +/- 0.029 |
| EGS (3 seeds) | 0.2524 +/- 0.006 | 0.2595 +/- 0.005 | 0.5461 +/- 0.035 |

## Phase 2: Diagnostic Analysis
- Severe heterophily: <10% same-label neighbors for most classes
- Temporal feature drift: KS>0.5 for last_seen, frequency, reveal
- Unlabeled neighbor dominance: 77-95% of in-edge neighbors
- Degree distribution highly skewed: INDIVIDUAL max degree 12,273

## Phase 3: Ablation & Multi-seed
- Direction-aware aggregation: +0.082 Macro-F1 (core contribution)
- Edge gating alone: -0.003 Macro-F1 (no benefit without direction)
- Focal loss (gamma=2): catastrophic failure (Macro-F1 0.33)
- Sensitive ranking: Conservative AUPRC 0.748, Recall@5% 0.827

## Phase 4: OOD Lite Gate
- Topology-aware reweighting: FAIL (temporal delta +0.005, threshold +0.03)
- CBK not degraded (slight improvement 0.600 -> 0.618)
- Temporal OOD remains an open challenge
