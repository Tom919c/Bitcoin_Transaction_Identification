# Phase 8/6 实验决策日志

## 2026-06-18 Phase 8：Multi-Seed

### 已完成
- class_balanced_khop 上 MLP/SAGE/EGS 各 3 个种子（42、3407、1234）
- 总计 9 次训练

### 关键结果
- EGS Macro-F1: 0.651 +/- 0.014（稳定）
- EGS Minority-F1: 0.667 +/- 0.016
- EGS Weighted-F1: 0.924 +/- 0.004
- 相对 SAGE 增益：Macro-F1 +0.072，Minority-F1 +0.055

### 决策
- EGS 在所有种子上均一致优于 SAGE，结果可信
- 标准差小（0.014），说明模型稳定性好

## 2026-06-18 Phase 6：Focal Loss

### 已完成
- EGS + focal loss（gamma=2.0）在 class_balanced_khop 上训练

### 关键结果
- Focal loss Macro-F1: 0.330（vs weighted_ce 0.647，下降 49%）
- Focal loss Minority-F1: 0.462（vs weighted_ce 0.660，下降 30%）
- Focal loss Weighted-F1: 0.226（vs weighted_ce 0.925，下降 76%）

### 决策
- gamma=2.0 过于激进，不适用于当前 11 类问题
- 后续如需长尾优化，应尝试 LDAM 或 class-balanced focal（gamma<1）
- 当前 weighted_ce 配合 EGS 已是最佳策略

## 下一步
- Phase 9：汇总 sensitive ranking 指标（AUPRC、Recall@K）
- Phase 10：case study 分析
- Phase 11：论文材料整理
