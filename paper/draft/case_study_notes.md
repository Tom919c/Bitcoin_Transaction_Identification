# Case Study Notes

## RANSOMWARE: Direction-Aware Success

RANSOMWARE is the strongest success case for direction-aware aggregation:
- 0 misclassified out of 42 test nodes (EGS)
- In-edge: 9.3% from INDIVIDUAL (highest cross-class connection)
- Out-edge: directed fund flow pattern distinct from INDIVIDUAL
- Direction separation allows model to distinguish RANSOMWARE from INDIVIDUAL despite high in-edge heterophily

This validates the core hypothesis: directed fund flow patterns carry identity signals that undirected aggregation misses.

## MIXER/EXCHANGE Boundary

MIXER is the hardest confusion pair with EXCHANGE:
- 4 misclassified as EXCHANGE out of 10 test MIXER nodes
- MIXER out-edge: 4% to EXCHANGE (highest cross-class out-edge)
- Both classes involve bidirectional fund flow
- MIXER has multi-in/multi-out pattern with分散 amounts, but node-level features may not capture this

Implication: MIXER identity may require motif-level or subgraph-level reasoning, not just node classification.

## GAMBLING/EXCHANGE Confusion

GAMBLING has the highest absolute misclassification count:
- 34 misclassified as EXCHANGE out of 282 test nodes (12% error rate)
- GAMBLING in-edge: 1.3% from EXCHANGE
- Both classes have high transaction volume
- GAMBLING typically has higher frequency, smaller amounts

This confusion is partially addressable through better edge feature engineering (amount distributions, frequency patterns).

## PONZI/EXCHANGE Confusion

PONZI shows moderate confusion with EXCHANGE:
- In-edge unlabeled ratio: 82.4%
- PONZI pattern: receive funds -> quickly transfer out (pyramid structure)
- This temporal pattern is captured by duration and recency features
- Under temporal split, these features drift, worsening the confusion

## Key Takeaway

Direction-aware aggregation helps most for classes with distinctive flow patterns (RANSOMWARE, BRIDGE). Classes with flow patterns similar to EXCHANGE (MIXER, GAMBLING, PONZI) remain challenging and may require richer structural reasoning.
