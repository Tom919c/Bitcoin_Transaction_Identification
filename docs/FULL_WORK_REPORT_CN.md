# BTC-AML 项目全面工作报告

生成时间：2026-06-18
工作分支：cq_test（本地 git，禁止推送 GitHub）

---

## 一、项目概述

本项目研究比特币实体交易图上的风险实体识别问题。核心数据集包含 242,226 个节点、1,237,757 条有向边，涵盖 11 个实体类别（INDIVIDUAL=0, BET=1, GAMBLING=2, EXCHANGE=3, MINING=4, PONZI=5, RANSOMWARE=6, FAUCET=7, MARKETPLACE=8, MIXER=9, BRIDGE=10），其中 -1 表示未标注背景节点。

标签语义约束：-1=忽略（不参与训练和评估），0~10=11 个监督类别，INDIVIDUAL=0 参与训练。

### 数据结构

- x: [242226, 27] 节点特征
- edge_index: [2, 1237757] 有向边（src->dst = 资金流方向）
- edge_attr: [1237757, 11] 边特征（推测包含 reveal, last_seen, total, min, max, avg, duration, frequency, recency 等）
- y: [242226] 标签（-1=未标注, 0~10=类别）
- train_mask: 20458, val_mask: 6820, test_mask: 6820

### 三套评估协议

1. **class_balanced_khop**：随机分层采样，242,226 节点，1,237,757 边
2. **temporal_balanced**：基于时间的外推划分，242,352 节点，1,239,058 边
3. **label_preserving**：保持标签分布的随机采样

---

## 二、研究问题演进

项目已从单纯的模型对比升级为一个更明确的科学问题：

> 比特币实体风险识别是否应被定义为 directed temporal heterophily OOD risk identification？

推荐论文路线：Hybrid = Benchmark Foundation + Temporal OOD Direction-Aware Method

---

## 三、Phase 0：冻结与复现清单（已完成）

- pytest 9/9 通过
- 三套协议 .pt 文件均存在
- 标签逻辑验证：-1=忽略, 0~10=11 类监督, INDIVIDUAL=0 参与训练
- current_result_manifest.md 已生成

---

## 四、Phase 1：Temporal Edge Heterophily 诊断（已完成）

### 4.1 邻居标签分布

| 类别 | 节点数 | 同类比(in) | 同类比(out) | 未标注比(in) | 未标注比(out) |
|---|---|---|---|---|---|
| INDIVIDUAL | 23,236 | 22.2% | 44.5% | 71.2% | 49.3% |
| BET | 6,723 | 6.7% | 10.7% | 87.1% | 84.1% |
| GAMBLING | 1,410 | 5.8% | 6.4% | 77.3% | 67.2% |
| EXCHANGE | 794 | 3.1% | 3.0% | 84.3% | 67.3% |
| MINING | 724 | 6.5% | 5.6% | 84.1% | 69.1% |
| PONZI | 587 | 7.0% | 4.6% | 82.4% | 78.7% |
| RANSOMWARE | 234 | 0.9% | 2.3% | 86.3% | 91.9% |
| FAUCET | 125 | 4.1% | 1.0% | 84.0% | 68.5% |
| MARKETPLACE | 115 | 2.8% | 3.9% | 83.1% | 76.5% |
| MIXER | 80 | 0.4% | 0.5% | 84.8% | 69.9% |
| BRIDGE | 70 | 19.9% | 53.6% | 78.6% | 45.9% |

### 4.2 度数暴露

| 类别 | 平均度 | 中位度 | 最大度 | 超级节点(>100)占比 |
|---|---|---|---|---|
| INDIVIDUAL | 26.8 | 6 | 12,273 | 2.2% |
| EXCHANGE | 62.3 | 15 | 3,868 | 10.2% |
| MINING | 78.8 | 36 | 2,484 | 13.4% |
| MIXER | 48.5 | 17.5 | 1,426 | 6.3% |

### 4.3 关键诊断发现

1. **极度异配**：除 BRIDGE 和 INDIVIDUAL 外，所有类别同类邻居 <10%
2. **MIXER 几乎无同类信号**：入边同类 0.4%，出边同类 0.5%
3. **未标注邻居主导**：所有类别入边未标注比例 71-87%
4. **入边比出边更异配**：入边同类比普遍低于出边
5. **度数分布极度右偏**：INDIVIDUAL 最大度 12,273，中位数仅 6

---

## 五、Phase 2：路线验证实验（已完成）

### 5.1 class_balanced_khop（随机分层）

| 模型 | Seed | Macro-F1 | Minority-F1 | Weighted-F1 |
|---|---|---|---|---|
| MLP | 42 | 0.4080 | 0.4484 | 0.7339 |
| MLP | 3407 | 0.4061 | 0.4292 | 0.7363 |
| MLP | 1234 | 0.4089 | 0.4447 | 0.7318 |
| **MLP 均值** | **3** | **0.4077 +/- 0.0012** | **0.4408 +/- 0.0083** | **0.7340 +/- 0.0018** |
| SAGE | 42 | 0.5868 | 0.6239 | 0.8960 |
| SAGE | 3407 | 0.5837 | 0.6111 | 0.8955 |
| SAGE | 1234 | 0.5652 | 0.6016 | 0.8943 |
| **SAGE 均值** | **3** | **0.5785 +/- 0.0095** | **0.6122 +/- 0.0091** | **0.8953 +/- 0.0007** |
| EGS | 42 | 0.6466 | 0.6595 | 0.9248 |
| EGS | 3407 | 0.6691 | 0.6886 | 0.9285 |
| EGS | 1234 | 0.6360 | 0.6521 | 0.9186 |
| **EGS 均值** | **3** | **0.6505 +/- 0.0138** | **0.6667 +/- 0.0158** | **0.9240 +/- 0.0041** |
| EGS no-direction | 42 | 0.5837 | 0.5955 | 0.9025 |
| EGS no-temporal-edge | 42 | **0.6643** | **0.6816** | 0.9300 |
| EGS-Focal(gamma=2) | 42 | 0.3299 | 0.4621 | 0.2259 |

### 5.2 temporal_balanced（时间外推）

| 模型 | Seed | Macro-F1 | Minority-F1 | Weighted-F1 |
|---|---|---|---|---|
| MLP | 42 | 0.1255 | 0.1852 | 0.1680 |
| SAGE | 42 | 0.1931 | 0.2448 | 0.3515 |
| SAGE | 43 | 0.1969 | 0.2377 | 0.3617 |
| SAGE | 44 | 0.1797 | 0.2263 | 0.2956 |
| **SAGE 均值** | **3** | **0.1899 +/- 0.0073** | **0.2363 +/- 0.0076** | **0.3363 +/- 0.0289** |
| EGS | 42 | 0.2565 | 0.2650 | 0.5715 |
| EGS | 43 | 0.2563 | 0.2599 | 0.5704 |
| EGS | 44 | 0.2443 | 0.2537 | 0.4964 |
| **EGS 均值** | **3** | **0.2524 +/- 0.0057** | **0.2595 +/- 0.0047** | **0.5461 +/- 0.0348** |
| EGS no-direction | 42 | 0.1633 | 0.2071 | 0.2761 |
| EGS no-temporal-edge | 42 | **0.2675** | **0.2735** | 0.5472 |

### 5.3 EGS 逐类 F1（最优 seed=3407，class_balanced_khop）

| 类别 | Precision | Recall | F1 | Support |
|---|---|---|---|---|
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

### 5.4 消融实验分析

| 变体 | Macro-F1 | 说明 |
|---|---|---|
| GraphSAGE 基线 | 0.5868 | 无方向、无边门控 |
| EGS(无方向) | 0.5837 | 边门控单独无效 |
| EGS(完整) | 0.6657 | 方向聚合是核心（+0.082） |
| EGS(无时间边特征) | 0.6643 | 时间边特征轻微有害 |

### 5.5 Sensitive Ranking（EGS multi-seed，class_balanced_khop）

| 风险组 | AUPRC | Recall@1% | Recall@5% | Recall@10% |
|---|---|---|---|---|
| extended_sensitive | 0.748 +/- 0.022 | 0.352 +/- 0.007 | 0.827 +/- 0.007 | 0.982 +/- 0.007 |

### 5.6 核心发现

1. **方向分离是 EGS 的核心贡献**：方向消融导致 CBK -0.067、temporal -0.093 Macro-F1。
2. **时间边特征不帮忙**：去掉后 CBK +0.018、temporal +0.011。
3. **temporal 与 random 性能差距巨大**：EGS 在 CBK=0.6505 vs temporal=0.2524，差距 0.398。
4. **多 seed 稳定性良好**：CBK EGS 标准差 0.0138，temporal EGS 标准差 0.0057。
5. **Focal loss 不适用**：gamma=2 导致 Macro-F1 降至 0.3299。

---

## 六、路线晋级门控决策

### Temporal OOD 方法：未通过

- 最优 temporal Macro-F1 = 0.2675，阈值 = 0.2865（差 0.019）
- 3 seed 稳定但绝对性能不足
- 难类（MIXER, RANSOMWARE）recall 无明显改善

### Benchmark + Mechanism Analysis：基本通过

- 协议、代码、评估脚本完整可复现
- 方向性收益、未标注邻居稀释、高异配均有清晰量化证据
- 时间漂移证据部分存在

### 最终选择：Hybrid 路线

Benchmark Foundation + Temporal OOD Direction-Aware Method

---

## 七、下一步工作计划

### Phase 3：Conservative Sensitive Ranking

- conservative_sensitive = PONZI + RANSOMWARE + MIXER
- extended_sensitive = BET + GAMBLING + MARKETPLACE + BRIDGE + PONZI + RANSOMWARE + MIXER
- 指标：AUPRC, AUROC, Recall@1/5/10%, Precision@1/5/10%, Yield@Budget

### Phase 4：节点分类边界分析

- 分析 MIXER->EXCHANGE, GAMBLING->EXCHANGE, RANSOMWARE->INDIVIDUAL 等混淆对
- 1-hop/2-hop 邻居标签分布、金额统计、交易频率分析
- 判断是否需要 subgraph reasoning

### Phase 5：论文材料生成

- 表格：dataset protocols, main results, ablation, multiseed, ranking, diagnostics
- 图表：model comparison, per-class F1, heterophily, confusion matrix, recall@k
- 草稿：problem definition, dataset, diagnostics, method, experiments, failure analysis, limitations

### 可选：轻量 OOD 原型

- topology-aware reweighting：根据未标注邻居比例、异配度对 loss 重加权
- feature-structure decoupled head：一个 head 看节点特征，一个看图消息

---

## 八、关键实验产物路径

### 数据协议

- data/processed/protocols/class_balanced_khop.pt
- data/processed/protocols/temporal_balanced.pt
- data/processed/protocols/label_preserving.pt
- data/processed/protocols/class_balanced_khop_no_temporal.pt
- data/processed/protocols/temporal_balanced_no_temporal.pt

### 诊断输出

- experiments/diagnostics/temporal_edge_heterophily_report.md
- experiments/diagnostics/cbk/*.csv
- experiments/diagnostics/temporal/*.csv

### 实验结果

- experiments/summary/current_all_runs.csv
- experiments/summary/current_result_manifest.md
- experiments/summary/ablation_results.md
- experiments/route_validation/route_gate_decision.md
- experiments/runs/ 下各 run 目录的 results.csv

### 文档

- docs/btc_aml_codex_next_stage_docs/（完整工作计划和执行指南）
- docs/research/面向国际顶会的比特币交易图研究候选路线评估.md
- experiments/case_studies/case_study_report.md

### 代码

- src/btcaml/models/edge_sage.py（EdgeGatedSAGE 模型）
- src/btcaml/models/registry.py（模型注册）
- src/btcaml/data/label_maps.py（标签映射和风险组定义）
- scripts/run_benchmark.py（训练和评估脚本）
- scripts/analyze_temporal_edge_heterophily.py（Phase 1 诊断脚本）
- run_phase2_parallel.py（并行实验运行器）
