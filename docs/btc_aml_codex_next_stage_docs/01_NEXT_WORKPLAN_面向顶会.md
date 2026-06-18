# 下一步工作方案：从 EGS 结果到顶会级研究路线

## 1. 当前结论：项目已经进入“研究问题重定义”阶段

当前项目已经不是单纯的“MLP / GraphSAGE / EGS 谁分数更高”。已有结果暴露出一个更有研究价值的问题：

```text
在大规模、低标签、长尾、有向、边属性丰富的比特币实体图中，
普通图消息传递在随机协议下可以有效，
但在时间外推协议下明显失效。
同时，邻居高度异配，未标注邻居大量主导，资金流方向又显著影响结果。
```

当前已知事实：

```text
1. class_balanced_khop 上，EGS multi-seed Macro-F1 = 0.6505 ± 0.0138。
2. class_balanced_khop 上，GraphSAGE multi-seed Macro-F1 = 0.5785 ± 0.0095。
3. temporal_balanced 上，EGS Macro-F1 = 0.2565，仍然很低。
4. 大多数类别同类邻居比例 < 15%。
5. 入边未标注邻居比例约 77%–95%。
6. MIXER 同类邻居比例约 0.4%，且容易被误分为 EXCHANGE。
7. 敏感实体排序已有应用价值，但 conservative setting 还需补证据。
```

这些现象说明：当前最值得发展的不是“更复杂版 EGS”，而是一个更明确的问题定义：

> Directed temporal heterophily OOD risk identification on Bitcoin entity graphs.

中文可写为：

> 有向时间异配比特币实体图上的分布外风险识别。

## 2. 面向顶会的主线不应现在直接拍板

当前不应直接宣称：

```text
最终方法 = EGS / ETD-SAGE
```

更合理的流程是：

```text
候选路线池
→ 机制诊断
→ 晋级实验
→ 路线选择
→ 方法收敛
→ 论文包装
```

也就是说，下一步的核心不是写最终模型，而是做“路线筛选实验”。

## 3. 候选路线池

### 路线 A：Benchmark + Mechanism Analysis

核心贡献：

```text
提出一个真实、可复现、面向未来时间外推的比特币实体风险识别 benchmark；
证明随机分层会高估真实泛化能力；
定义 temporal edge heterophily、unlabeled-neighbor dilution、directional gain 等挑战。
```

优点：

```text
与当前资产高度匹配；
风险低；
很适合 KDD / WWW / CIKM 应用数据挖掘论文；
即使新方法提升有限，也能形成稳定贡献。
```

短板：

```text
需要可复现协议、清晰 challenge taxonomy、强 baseline 和可公开结果。
如果不能公开数据或协议，上限会下降。
```

### 路线 B：Temporal OOD Method

核心贡献：

```text
把 temporal_balanced 视为真实 graph OOD 场景；
设计 temporal environment reweighting / feature-structure decoupling / direction-aware robust aggregation；
目标是在时间外推下稳定提升，而不是只在随机 split 上涨分。
```

优点：

```text
顶会潜力最高；
与当前 temporal failure 强相关；
能对接 graph OOD / causal GNN / temporal heterophily 文献。
```

短板：

```text
实验风险更高；
如果 temporal 上提升不稳定，就不能作为主方法。
```

### 路线 C：Open-world / PU / Risk Discovery

核心贡献：

```text
从闭集 11 类分类转向已知风险 + 未知风险发现 + 人工审查排序。
```

优点：

```text
贴近真实 AML；
能利用大量未标注节点。
```

短板：

```text
当前 -1 节点主要是背景上下文，不天然等于未知类。
如果任务定义不严谨，容易被质疑概念偷换。
```

### 路线 D：Subgraph / Flow-Motif Boundary

核心贡献：

```text
证明 MIXER / EXCHANGE 等混淆类别可能不是纯节点属性问题，
而是局部资金流模式或子图形状问题。
```

优点：

```text
很有研究新意；
适合作为 secondary contribution 或下一篇论文方向。
```

短板：

```text
需要稳定 motif / subgraph 构造；
额外工程成本高；
不建议作为立即主线。
```

## 4. 当前推荐优先级

下一阶段建议采用：

```text
主候选：路线 B Temporal OOD Method
证据底座：路线 A Benchmark + Mechanism Analysis
补充验证：路线 D Subgraph Boundary
暂缓：路线 C Open-world / PU
```

原因：

```text
1. temporal_balanced 的失败最明显，是最有价值的问题信号。
2. EGS 已证明方向有价值，但未解决 temporal OOD。
3. Benchmark/机制分析能让论文不只依赖模型涨分。
4. MIXER/EXCHANGE 混淆可作为节点分类边界分析，而不是现在就切换成子图主线。
```

## 5. 下一阶段必须完成的四组验证

### 验证 1：Temporal Edge Heterophily 量化

目标：把“temporal 为什么崩”从直觉变成可量化证据。

必须输出：

```text
experiments/diagnostics/temporal_edge_heterophily.csv
experiments/diagnostics/directional_compatibility_matrix_*.csv
experiments/diagnostics/unlabeled_neighbor_dilution.csv
experiments/diagnostics/temporal_drift_by_class.csv
experiments/diagnostics/diagnostics_report.md
```

### 验证 2：Temporal OOD 机制实验

目标：判断是否存在可做方法创新的稳定切入点。

至少比较：

```text
GraphSAGE
EGS
EGS w/o temporal edge features
EGS w/o direction split
EGS + temporal environment reweighting
EGS + feature/structure decoupled head
EGS + temporal edge filtering
```

### 验证 3：Conservative Sensitive Ranking

目标：避免 extended sensitive 被 BET 等较容易类别抬高。

必须定义：

```text
conservative_sensitive = PONZI + RANSOMWARE + MIXER
extended_sensitive = BET + GAMBLING + MARKETPLACE + BRIDGE + PONZI + RANSOMWARE + MIXER
```

输出：

```text
AUPRC
Recall@1%
Recall@5%
Recall@10%
Precision@K
Yield@Budget
```

### 验证 4：节点分类边界分析

目标：正式检验 MIXER / EXCHANGE、GAMBLING / EXCHANGE 等关键混淆是否需要 subgraph reasoning。

输出：

```text
paper/case_studies/mixer_exchange_boundary.md
paper/case_studies/gambling_exchange_boundary.md
experiments/diagnostics/confusion_pair_flow_stats.csv
```

## 6. 晋级阈值

### Temporal OOD 方法成为主线的阈值

必须满足：

```text
1. temporal_balanced 上 3 seeds。
2. 相比当前 EGS，Macro-F1 mean 至少 +0.03。
3. Minority Macro-F1 或 Conservative Sensitive AUPRC 至少 +0.03。
4. 至少一个关键难类 recall 明显改善，例如 RANSOMWARE / MIXER / MARKETPLACE。
5. 不以 class_balanced_khop 明显退化为代价。
```

### Benchmark + Analysis 成为主线的阈值

如果 Temporal OOD 方法没有稳定提升，则转为 benchmark/analysis 主线。必须满足：

```text
1. 协议、split、baseline、评估脚本可复现。
2. temporal edge heterophily 指标能解释 temporal 性能下降。
3. 方向性收益、未标注邻居稀释、时间漂移至少三者中两者有清晰证据。
4. 能生成完整 paper tables / figures。
```

### Subgraph Boundary 成为主线的阈值

不建议立即主线化，除非满足：

```text
1. MIXER→EXCHANGE 或 GAMBLING→EXCHANGE 关键混淆显著降低。
2. local flow stats / motif features 的增益明显高于节点特征。
3. 不依赖人工挑选案例。
```

## 7. 本阶段结束时应做出的决策

完成下一阶段后，必须在 `docs/DECISION_LOG.md` 写明：

```text
最终主线选择：
A. Temporal OOD Method
B. Benchmark + Mechanism Analysis
C. Subgraph Boundary
D. Hybrid: Benchmark foundation + temporal OOD method
```

推荐默认收敛到 D，但必须由实验结果支撑。
