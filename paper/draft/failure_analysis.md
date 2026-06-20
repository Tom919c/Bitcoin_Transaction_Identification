# Failure Analysis

## 1. Temporal OOD Gap

The most significant finding is the dramatic performance drop under temporal split:
- EGS: 0.6505 (CBK) -> 0.2524 (temporal), a 61% relative drop
- This gap persists across all models and seeds
- It cannot be explained by class imbalance alone (same class distribution in both protocols)

Root cause: temporal distribution shift in edge features (KS>0.5 for key features) and node neighborhood patterns.

## 2. Temporal Feature Drift / Pseudo-Correlation

Edge features like last_seen, frequency, and reveal have systematic temporal trends:
- Train set contains earlier entities, test set contains later entities
- Under random split, these features are pseudo-correlated with labels (model memorizes temporal patterns)
- Under temporal split, the correlation breaks, causing severe performance degradation

This is a fundamental issue that cannot be solved by simply removing temporal features (as shown by no-temporal-edge ablation).

## 3. MIXER Node-Level Boundary

MIXER is the hardest class:
- Only 80 labeled nodes total, 10 in test set
- 0.4% same-label in-edge ratio (almost no MIXER neighbors)
- F1: 0.245 (best single seed)
- 4 out of 10 test MIXER nodes misclassified as EXCHANGE

Node-level classification may be fundamentally insufficient for MIXER. The entity's identity may depend on local flow patterns (motifs) rather than individual node features.

## 4. Extended Ranking Inflation

Extended sensitive ranking (AUPRC 0.986) appears excellent but is misleading:
- BET and GAMBLING have very high recall (easy to rank)
- Conservative ranking (PONZI/RANSOMWARE/MIXER only) drops to AUPRC 0.748
- Recall@1% for conservative is only 34.6%, meaning 65% of high-risk entities are missed in the top 1% of flagged nodes

## 5. Focal Loss Failure

Focal loss with gamma=2 catastrophically failed:
- Macro-F1 dropped from 0.6505 to 0.3299
- The aggressive down-weighting of easy examples destabilized training
- This confirms that standard class-weighted CE is more robust for this task
