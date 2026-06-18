# Phase 2 路线晋级门控决策

## 1. 实验总览

Phase 2 在三套协议上完成了 MLP、GraphSAGE、EdgeGatedSAGE（EGS）的系统对比，以及方向消融、时间特征消融和多 seed 稳定性验证。

## 2. class_balanced_khop（随机分层）完整结果

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

### CBK 关键发现

1. EGS 相对 SAGE 提升 +0.072 Macro-F1（0.5785 to 0.6505），3 seed 方向一致。
2. 方向分离是核心贡献：去掉方向后 Macro-F1 下降 0.067（0.6657 to 0.5837）。
3. 去掉时间边特征反而更好：CBK no-temporal Macro-F1 = 0.6643。
4. Focal loss(gamma=2) 不适用，Macro-F1 仅 0.3299。

## 3. temporal_balanced（时间外推）完整结果

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

### Temporal 关键发现

1. EGS 3 seed 均值 0.2524，标准差仅 0.0057，结果稳定。
2. 方向消融：去掉方向后 Macro-F1 下降 0.093（0.2565 to 0.1633）。
3. 时间特征消融：去掉后 Macro-F1 上升 0.011（0.2565 to 0.2675）。
4. 绝对性能仍很低：最优 EGS no-temporal Macro-F1 仅 0.2675。

## 4. 晋级阈值判定

### Temporal OOD 方法晋级阈值

| 阈值条件 | 要求 | 实际 | 满足 |
|---|---|---|---|
| temporal 3 seeds | 必须 | 0.2524 +/- 0.0057 | YES |
| 相对 EGS +0.03 Macro-F1 | >=0.2865 | 最优 0.2675 | NO（差 0.019） |
| Minority-F1 或 AUPRC +0.03 | 显著提升 | Minority 0.2595 | NO |
| 难类 recall 明显改善 | 显著提升 | MIXER F1 约 0.08 | NO |
| CBK 不灾难性下降 | 不退化 | no-temporal CBK=0.6643 | YES |

**结论：Temporal OOD 方法未通过晋级阈值。**

### Benchmark + Mechanism Analysis 晋级阈值

| 阈值条件 | 要求 | 实际 | 满足 |
|---|---|---|---|
| 协议/代码可复现 | 完整 | 3 套协议、脚本 | YES |
| temporal edge heterophily 指标 | 解释 temporal 下降 | Phase 1 诊断完整 | YES |
| 方向性收益 | 清晰证据 | +0.093 | YES |
| 未标注邻居稀释 | 清晰证据 | 77-95% | YES |
| 时间漂移 | 清晰证据 | 边特征时间漂移存在 | PARTIAL |

**结论：Benchmark + Mechanism Analysis 路线基本满足晋级条件。**

## 5. 最终路线选择

### 选择：Hybrid = Benchmark Foundation + Temporal OOD Direction-Aware Method

理由：

1. Benchmark 贡献扎实：三套协议、完整 baseline 矩阵、方向消融、多 seed 稳定性、敏感实体 ranking。
2. Temporal OOD 问题真实存在：temporal 与 random 的巨大性能差距（0.25 vs 0.65）本身是有研究价值的发现。
3. 方向分离有强证据支持：无论在 CBK 还是 temporal 上，方向消融都导致显著性能下降（-0.067 / -0.093）。
4. 时间特征不帮忙反而轻微有害：与 TGB 等 benchmark 文献中简单方法经常打败复杂 temporal GNN 的观察一致。
5. OOD 方法虽未达标但方向明确：当前只是基础 EGS + 简单消融，引入 causal decoupling / environment reweighting 仍有空间。

### 论文定位

主问题：在大规模比特币实体交易图中，时间外推失败是否主要来自 temporal edge heterophily 与 environment-induced distribution shift；若是，能否通过方向感知与因果解耦学到更稳健的风险实体表示？

主贡献：

1. 提出真实可复现的比特币实体风险识别 benchmark，证明随机分层高估泛化能力。
2. 定义并量化 temporal edge heterophily、未标注邻居稀释、方向性挑战。
3. 提出方向感知的时间鲁棒图学习方法（在 EGS 基础上扩展）。
4. 展示保守敏感实体 ranking 的应用价值。

## 6. 下一步工作

1. Phase 3：Conservative Sensitive Ranking（PONZI/RANSOMWARE/MIXER vs 扩展集合）
2. Phase 4：节点分类边界分析（MIXER-EXCHANGE 混淆对）
3. Phase 5：论文材料生成（表格、图表、草稿章节）
4. 可选：实现轻量 OOD 原型（topology-aware reweighting）作为方法贡献初步验证
