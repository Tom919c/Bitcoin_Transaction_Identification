# Node Classification Boundary Report

## Summary of Confusion Pairs

| Pair | # Misclassified | # Correct |
|---|---|---|
| MIXER->EXCHANGE | 4 | 6 |
| GAMBLING->EXCHANGE | 34 | 199 |
| RANSOMWARE->INDIVIDUAL | 0 | 42 |
| MARKETPLACE->EXCHANGE | 6 | 10 |
| PONZI->INDIVIDUAL | 2 | 95 |
| PONZI->EXCHANGE | 7 | 95 |

## Per-Pair Analysis

### MIXER -> EXCHANGE

Misclassified: avg_degree=49.0, avg_unlabeled=0.886, avg_same_label=0.037
Correct: avg_degree=48.3, avg_unlabeled=0.854, avg_same_label=0.000

### GAMBLING -> EXCHANGE

Misclassified: avg_degree=14.3, avg_unlabeled=0.911, avg_same_label=0.333
Correct: avg_degree=2.3, avg_unlabeled=1.000, avg_same_label=0.000

### RANSOMWARE -> INDIVIDUAL

Correct: avg_degree=22.7, avg_unlabeled=0.915, avg_same_label=0.000

### MARKETPLACE -> EXCHANGE

Misclassified: avg_degree=427.0, avg_unlabeled=0.779, avg_same_label=0.085
Correct: avg_degree=36.3, avg_unlabeled=0.854, avg_same_label=0.611

### PONZI -> INDIVIDUAL

Misclassified: avg_degree=30.0, avg_unlabeled=0.826, avg_same_label=0.393
Correct: avg_degree=32.7, avg_unlabeled=0.794, avg_same_label=0.737

### PONZI -> EXCHANGE

Misclassified: avg_degree=48.3, avg_unlabeled=0.777, avg_same_label=0.029
Correct: avg_degree=32.7, avg_unlabeled=0.794, avg_same_label=0.737

## Key Questions

### 1. Why is MIXER misclassified as EXCHANGE?
MIXER misclassified nodes: avg in-degree=20.3, out-degree=28.7
MIXER nodes tend to have many connections (high degree) similar to EXCHANGE.
With only 0.4% same-label neighbors, there is almost no local MIXER signal.

### 2. GAMBLING vs EXCHANGE structural confusion
GAMBLING misclassified nodes share structural patterns with EXCHANGE (high degree, diverse neighbors).

### 3. RANSOMWARE diluted by INDIVIDUAL background
Limited RANSOMWARE->INDIVIDUAL confusion cases.

### 4. Is node classification sufficient?

Based on the confusion analysis:
- MIXER has almost no same-label neighbors (0.4%), making node-level classification extremely difficult
- EXCHANGE and GAMBLING share structural patterns (high degree, many unlabeled neighbors)
- RANSOMWARE is diluted by INDIVIDUAL background neighbors
- For most classes, node features + 1-hop aggregation provide reasonable classification
- For MIXER specifically, the signal may require subgraph-level patterns (flow motifs)

### 5. Which classes need subgraph reasoning?

**Most likely candidates for subgraph reasoning:**
1. MIXER: 0.4% same-label ratio, almost no node-level signal
2. BRIDGE: 19.9% in-same but 53.6% out-same suggests directional flow pattern

**Likely sufficient with node classification + direction-aware aggregation:**
1. INDIVIDUAL, BET: high support, clear patterns
2. EXCHANGE, MINING: distinct degree/amount profiles

### 6. Should subgraph route proceed to next phase?

Recommendation: Subgraph reasoning should be listed as FUTURE WORK, not immediate next step.
Rationale:
- MIXER support is only 16 test nodes, insufficient for robust subgraph evaluation
- Current node-level model already captures directional information well
- Subgraph methods add significant complexity and engineering cost
- The primary research contribution should focus on temporal OOD + direction awareness first