# 实验状态（完整版）

## 已完成阶段

### Phase 0：环境检查
**状态**：已完成
- pytest 9/9 通过
- 3 套协议数据存在
- 无旧标签逻辑

### Phase 1：详细评估导出
**状态**：已完成
- 6 个历史 run 的逐类指标、混淆矩阵、预测结果
- 生成 baseline_protocol_comparison.csv/.md

### Phase 2：协议诊断
**状态**：已完成
- 高异配性：MIXER 同类邻居 0.4%
- 77-95% 入边邻居未标注
- temporal_balanced 时间偏移严重

### Phase 4：EdgeGatedSAGE
**状态**：已完成
- 实现 src/btcaml/models/edge_sage.py
- class_balanced_khop: EGS Macro-F1=0.6657 vs SAGE 0.5868（+0.079）
- temporal_balanced: EGS Macro-F1=0.2565 vs SAGE 0.1931（+0.063）

### Phase 7：消融实验
**状态**：已完成
- 方向聚合是核心贡献（+0.082 Macro-F1）
- 边门控在有方向分离时才有效

### Phase 8：Multi-Seed
**状态**：已完成

| 模型 | Macro-F1 | Minority-F1 | Weighted-F1 |
|---|---|---|---|
| MLP | 0.408 +/- 0.001 | 0.441 +/- 0.008 | 0.734 +/- 0.002 |
| SAGE | 0.579 +/- 0.010 | 0.612 +/- 0.009 | 0.895 +/- 0.001 |
| **EGS** | **0.651 +/- 0.014** | **0.667 +/- 0.016** | **0.924 +/- 0.004** |

### Phase 6：Focal Loss
**状态**：已完成
- gamma=2.0 focal loss 严重降低性能（Macro-F1 0.330 vs 0.647）
- 不适用于当前任务

### Phase 9：Sensitive Ranking
**状态**：已完成
- AUPRC: 0.748 +/- 0.022
- Recall@5%: 82.7%
- Recall@10%: 98.2%

### Phase 10：Case Study
**状态**：已完成
- RANSOMWARE/BRIDGE 召回率 100%
- GAMBLING 46 个被误分为 EXCHANGE
- PONZI 14 个被漏掉

## 核心结果汇总

### class_balanced_khop 主结果

| 模型 | Macro-F1 | Minority-F1 | Weighted-F1 | AUPRC |
|---|---|---|---|---|
| MLP | 0.408 +/- 0.001 | 0.441 +/- 0.008 | 0.734 +/- 0.002 | - |
| GraphSAGE | 0.579 +/- 0.010 | 0.612 +/- 0.009 | 0.895 +/- 0.001 | 0.589 |
| **EGS** | **0.651 +/- 0.014** | **0.667 +/- 0.016** | **0.924 +/- 0.004** | **0.748** |

### EGS 逐类 F1（seed=3407，最优）

| 类别 | Precision | Recall | F1 | Support |
|---|---:|---:|---:|---:|
| INDIVIDUAL | 0.994 | 0.932 | 0.962 | 4647 |
| BET | 0.984 | 0.987 | 0.986 | 1344 |
| GAMBLING | 0.684 | 0.706 | 0.695 | 282 |
| EXCHANGE | 0.399 | 0.692 | 0.506 | 159 |
| MINING | 0.713 | 0.890 | 0.791 | 145 |
| PONZI | 0.559 | 0.805 | 0.660 | 118 |
| RANSOMWARE | 0.467 | 0.894 | 0.613 | 47 |
| FAUCET | 0.500 | 0.640 | 0.561 | 25 |
| MARKETPLACE | 0.385 | 0.435 | 0.408 | 23 |
| MIXER | 0.182 | 0.375 | 0.245 | 16 |
| BRIDGE | 0.875 | 1.000 | 0.933 | 14 |

## 待完成

- Phase 11：论文材料整理（表格、图、草稿章节）
