# Table 5: Temporal Edge Feature Drift

| Feature | Train Mean | Test Mean | Abs Shift | KS Stat | Drift Level |
|---|---|---|---|---|---|
| last_seen | 2013.6 | 2015.5 | 1.94 | 0.5720 | SEVERE |
| frequency | 4.98 | 10.42 | 5.44 | 0.5720 | SEVERE |
| reveal | 2012.5 | 2014.0 | 1.48 | 0.5463 | SEVERE |
| duration | 380.4 | 537.2 | 156.8 | 0.2560 | MODERATE |
| min_sent | 0.241 | 0.079 | 0.162 | 0.2347 | MODERATE |
| avg_sent | 1.153 | 0.452 | 0.701 | 0.2160 | MODERATE |
| total | 4.24 | 3.37 | 0.87 | 0.1213 | LOW |
| max_sent | 3.39 | 2.38 | 1.01 | 0.1952 | LOW |
| total_received | 4.27 | 4.18 | 0.09 | 0.0619 | LOW |
| max_received | 3.44 | 3.43 | 0.01 | 0.0565 | LOW |
| min_received | 0.307 | 0.327 | 0.02 | 0.0356 | LOW |

Severe drift in temporal features (last_seen, frequency, reveal) under temporal split.
These features are pseudo-correlated with the target under random split.
