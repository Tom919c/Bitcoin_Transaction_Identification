# Sensitive Ranking Summary

## Conservative Sensitive

| Seed | k% | AUPRC | AUROC | Recall | Precision | Yield |
|---|---|---|---|---|---|---|
| seed42 | 1% | 0.7501 | 0.9871 | 0.3370 | 0.8971 | 0.8971 |
| seed42 | 5% | 0.7501 | 0.9871 | 0.8287 | 0.4399 | 0.4399 |
| seed42 | 10% | 0.7501 | 0.9871 | 0.9724 | 0.2581 | 0.2581 |
| seed3407 | 1% | 0.7739 | 0.9878 | 0.3536 | 0.9412 | 0.9412 |
| seed3407 | 5% | 0.7739 | 0.9878 | 0.8343 | 0.4428 | 0.4428 |
| seed3407 | 10% | 0.7739 | 0.9878 | 0.9834 | 0.2610 | 0.2610 |
| seed1234 | 1% | 0.7207 | 0.9863 | 0.3481 | 0.9265 | 0.9265 |
| seed1234 | 5% | 0.7207 | 0.9863 | 0.8177 | 0.4340 | 0.4340 |
| seed1234 | 10% | 0.7207 | 0.9863 | 0.9890 | 0.2625 | 0.2625 |

**Mean AUPRC**: 0.7483 +/- 0.0231
**Mean AUROC**: 0.9871 +/- 0.0006

## Extended Sensitive

| Seed | k% | AUPRC | AUROC | Recall | Precision | Yield |
|---|---|---|---|---|---|---|
| seed42 | 1% | 0.9866 | 0.9943 | 0.0369 | 1.0000 | 1.0000 |
| seed42 | 5% | 0.9866 | 0.9943 | 0.1849 | 1.0000 | 1.0000 |
| seed42 | 10% | 0.9866 | 0.9943 | 0.3698 | 1.0000 | 1.0000 |
| seed3407 | 1% | 0.9879 | 0.9948 | 0.0369 | 1.0000 | 1.0000 |
| seed3407 | 5% | 0.9879 | 0.9948 | 0.1849 | 1.0000 | 1.0000 |
| seed3407 | 10% | 0.9879 | 0.9948 | 0.3698 | 1.0000 | 1.0000 |
| seed1234 | 1% | 0.9846 | 0.9933 | 0.0369 | 1.0000 | 1.0000 |
| seed1234 | 5% | 0.9846 | 0.9933 | 0.1849 | 1.0000 | 1.0000 |
| seed1234 | 10% | 0.9846 | 0.9933 | 0.3698 | 1.0000 | 1.0000 |

**Mean AUPRC**: 0.9864 +/- 0.0015
**Mean AUROC**: 0.9941 +/- 0.0006

## Analysis

Conservative mean AUPRC: 0.7483
Extended mean AUPRC: 0.9864
Difference: 0.2381

Extended ranking significantly outperforms conservative, indicating BET/GAMBLING dominate ranking signal.

Conservative AUPRC > 0.5: meaningful risk ranking for high-sensitivity AML classes.
Risk ranking can serve as application contribution (validate with case studies).