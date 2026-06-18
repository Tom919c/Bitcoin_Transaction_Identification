# Temporal Feature Failure Analysis Report

## 1. Per-Class Delta: CBK (full vs no-temporal)

| Class | F1_full | F1_no_temp | Delta | P_full | P_no_temp | R_full | R_no_temp |
|---|---|---|---|---|---|---|---|
| INDIVIDUAL | 0.9600 | 0.9633 | +0.0033 | 0.9945 | 0.9929 | 0.9279 | 0.9354 |
| BET | 0.9829 | 0.9840 | +0.0011 | 0.9800 | 0.9815 | 0.9859 | 0.9866 |
| GAMBLING | 0.6761 | 0.6930 | +0.0169 | 0.6749 | 0.6711 | 0.6773 | 0.7163 |
| EXCHANGE | 0.4786 | 0.5379 | +0.0593 | 0.3625 | 0.4400 | 0.7044 | 0.6918 |
| MINING | 0.7720 | 0.7911 | +0.0191 | 0.6902 | 0.7310 | 0.8759 | 0.8621 |
| PONZI | 0.7036 | 0.7143 | +0.0107 | 0.6593 | 0.6716 | 0.7542 | 0.7627 |
| RANSOMWARE | 0.5342 | 0.5150 | -0.0192 | 0.3772 | 0.3583 | 0.9149 | 0.9149 |
| FAUCET | 0.4557 | 0.4471 | -0.0086 | 0.3333 | 0.3167 | 0.7200 | 0.7600 |
| MARKETPLACE | 0.4889 | 0.4783 | -0.0106 | 0.5000 | 0.4783 | 0.4783 | 0.4783 |
| MIXER | 0.1935 | 0.2500 | +0.0565 | 0.2000 | 0.2500 | 0.1875 | 0.2500 |
| BRIDGE | 0.8667 | 0.9333 | +0.0667 | 0.8125 | 0.8750 | 0.9286 | 1.0000 |

## 2. Per-Class Delta: Temporal (full vs no-temporal)

| INDIVIDUAL | 0.5511 | 0.5095 | -0.0417 |
| BET | 0.8866 | 0.8987 | +0.0121 |
| GAMBLING | 0.0933 | 0.0867 | -0.0067 |
| EXCHANGE | 0.0298 | 0.0402 | +0.0104 |
| MINING | 0.5024 | 0.5163 | +0.0139 |
| PONZI | 0.2429 | 0.3034 | +0.0606 |
| RANSOMWARE | 0.1014 | 0.1250 | +0.0236 |
| FAUCET | 0.0676 | 0.1093 | +0.0417 |
| MARKETPLACE | 0.0807 | 0.1265 | +0.0458 |
| MIXER | 0.0781 | 0.0781 | +0.0000 |
| BRIDGE | 0.1879 | 0.1489 | -0.0390 |

## 3. Edge Feature Drift Summary

### class_balanced_khop

| Feature | Train Mean | Test Mean | Abs Shift | Std Shift | KS Stat | Wasserstein |
|---|---|---|---|---|---|---|
| min | 0.1057 | 0.1738 | 0.0681 | 0.0800 | 0.0377 | 0.0681 |
| frequency | -1.2549 | -1.3078 | 0.0528 | 0.0298 | 0.0367 | 0.1140 |
| last_seen | 0.8025 | 0.7959 | 0.0066 | 0.0063 | 0.0356 | 0.0547 |
| reveal | 0.5749 | 0.5663 | 0.0086 | 0.0097 | 0.0302 | 0.0322 |
| recency | 0.1965 | 0.2703 | 0.0739 | 0.0918 | 0.0290 | 0.0739 |
| max | 0.2348 | 0.3078 | 0.0730 | 0.0890 | 0.0253 | 0.0730 |
| avg | 0.2630 | 0.3266 | 0.0637 | 0.0755 | 0.0210 | 0.0637 |
| feat9 | 0.2656 | 0.2834 | 0.0179 | 0.0164 | 0.0157 | 0.0180 |
| duration | 0.4465 | 0.3963 | 0.0502 | 0.0282 | 0.0096 | 0.0543 |
| total | 0.2817 | 0.2529 | 0.0287 | 0.0217 | 0.0088 | 0.0287 |
| feat10 | -0.2392 | -0.2377 | 0.0015 | 0.0015 | 0.0068 | 0.0163 |

### temporal_balanced

| Feature | Train Mean | Test Mean | Abs Shift | Std Shift | KS Stat | Wasserstein |
|---|---|---|---|---|---|---|
| last_seen | 0.2081 | 1.1802 | 0.9721 | 0.9741 | 0.5720 | 0.9721 |
| frequency | -0.2315 | -1.9266 | 1.6951 | 1.5925 | 0.5720 | 1.6951 |
| reveal | 0.2003 | 0.7465 | 0.5462 | 0.5598 | 0.5463 | 0.5462 |
| min | 0.3429 | -0.1403 | 0.4832 | 0.5989 | 0.2579 | 0.4845 |
| duration | -0.1005 | 0.8339 | 0.9343 | 1.3201 | 0.2249 | 0.9343 |
| feat10 | -0.0164 | -0.4135 | 0.3970 | 0.4075 | 0.2002 | 0.3970 |
| feat9 | 0.0452 | 0.4305 | 0.3853 | 0.3675 | 0.1918 | 0.3854 |
| total | -0.0509 | 0.5270 | 0.5779 | 0.6265 | 0.1823 | 0.5779 |
| recency | 0.3348 | 0.0312 | 0.3036 | 0.3809 | 0.1802 | 0.3049 |
| max | 0.3208 | 0.1138 | 0.2070 | 0.2581 | 0.1124 | 0.2082 |
| avg | 0.3108 | 0.1694 | 0.1413 | 0.1742 | 0.0772 | 0.1502 |

## 4. Key Findings

- CBK mean F1 delta (no_temp - full): +0.0177
- Temporal mean F1 delta (no_temp - full): +0.0110

Top drifting temporal edge features (temporal_balanced):
- last_seen: KS=0.5720, standardized shift=0.9741
- frequency: KS=0.5720, standardized shift=1.5925
- reveal: KS=0.5463, standardized shift=0.5598

## 5. Why Temporal Features Do Not Help

Removing temporal edge features improves performance on BOTH protocols.
This suggests temporal features are adding noise rather than useful signal.
Possible explanations:
1. Temporal features encode information that correlates with the random split but not with actual risk patterns
2. Temporal features have high distribution drift between train/test, making them unreliable
3. The model may overfit to temporal artifacts in the training data
4. Edge gating may be overwhelmed by noisy temporal features, reducing its filtering ability

## 6. Can Temporal Features Be a Method Contribution?

Based on current evidence: NO, raw temporal edge features should NOT be used as a method contribution.
They add noise and exhibit drift. Any temporal modeling should be more sophisticated than direct feature inclusion.

## 7. Should We Continue Temporal OOD Methods?

The temporal OOD problem is real (0.25 vs 0.65 performance gap).
But the solution should NOT be simply adding temporal edge features.
Potential lightweight approaches:
1. Topology-aware reweighting based on neighbor heterophily
2. Direction-aware temporal edge filtering (drop or downweight drifted edges)
3. Environment-invariant training with temporal split as environment