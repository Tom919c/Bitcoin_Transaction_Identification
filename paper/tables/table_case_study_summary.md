# Table 6: Confusion Case Study Summary

| Focus Class | Confusion Target | Misclassified | Correct | Avg Unlabeled Ratio | Conclusion |
|---|---|---|---|---|---|
| MIXER | EXCHANGE | 4 | 6 | ~85% | Insufficient same-label signal |
| GAMBLING | EXCHANGE | 34 | 199 | ~76% | High overlap in flow patterns |
| RANSOMWARE | INDIVIDUAL | 0 | 42 | ~86% | Direction-aware separation works |
| PONZI | EXCHANGE | N/A | N/A | ~82% | Temporal drift complicates separation |
| MARKETPLACE | EXCHANGE | N/A | N/A | ~83% | Very few test samples |

MIXER has only 10 test samples; node-level classification may be fundamentally insufficient.
RANSOMWARE benefits most from direction-aware aggregation.
