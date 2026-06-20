# Paper and Artifact Spec

## 1. 论文暂定题目

### 英文候选

```text
When Do Graph Neural Networks Help in Bitcoin Entity Risk Identification?
A Study of Sampling Bias, Temporal Edge Heterophily, and Directional Message Passing
```

或：

```text
Directed Temporal Heterophily in Bitcoin Entity Risk Identification
```

### 中文候选

```text
面向比特币实体风险识别的采样偏差、时间异配与方向感知图学习研究
```

## 2. 论文主叙事

不要写成：

```text
我们提出了一个更强的 GNN。
```

应该写成：

```text
我们发现比特币实体风险识别不是普通静态节点分类；
它受到采样偏差、时间外推、异配邻居、未标注邻居稀释和资金流方向共同影响。
我们首先构建可复现协议并量化挑战，再验证方向感知和时间 OOD 机制是否能稳定提升风险识别。
```

## 3. 必须生成的表格

```text
paper/tables/table_1_dataset_protocols.md
paper/tables/table_2_main_results.md
paper/tables/table_3_temporal_ood_gate.md
paper/tables/table_4_ablation.md
paper/tables/table_5_sensitive_ranking.md
paper/tables/table_6_diagnostics.md
paper/tables/table_7_case_studies.md
```

### Table 1: Dataset Protocols

字段：

```text
protocol
nodes
edges
labeled_nodes
split_type
purpose
num_classes
edge_attr_dim
```

### Table 2: Main Results

字段：

```text
dataset
model
macro_f1_mean
macro_f1_std
minority_f1_mean
weighted_f1_mean
sensitive_auprc
num_seeds
```

### Table 3: Temporal OOD Gate

字段：

```text
model_variant
uses_direction
uses_edge_attr
uses_temporal_features
uses_reweighting
temporal_macro_f1
delta_vs_egs
gate_pass
```

### Table 4: Ablation

字段：

```text
variant
removed_component
class_balanced_macro_f1
temporal_macro_f1
interpretation
```

### Table 5: Sensitive Ranking

字段：

```text
risk_group
auprc
recall_at_1
recall_at_5
recall_at_10
precision_at_1
precision_at_5
precision_at_10
```

### Table 6: Diagnostics

字段：

```text
class_name
same_label_ratio_in
same_label_ratio_out
unlabeled_ratio_in
unlabeled_ratio_out
feature_drift_score
edge_time_drift_score
degree_exposure
```

## 4. 必须生成的图

```text
paper/figures/fig_1_protocol_overview.png
paper/figures/fig_2_main_results_cbk.png
paper/figures/fig_3_temporal_results.png
paper/figures/fig_4_temporal_edge_heterophily.png
paper/figures/fig_5_unlabeled_neighbor_dilution.png
paper/figures/fig_6_directional_compatibility_heatmap.png
paper/figures/fig_7_sensitive_recall_at_k.png
paper/figures/fig_8_confusion_matrix_temporal_egs.png
paper/figures/fig_9_mixer_exchange_case.png
```

## 5. 草稿章节

```text
paper/draft/01_introduction.md
paper/draft/02_related_work_notes.md
paper/draft/03_problem_definition.md
paper/draft/04_dataset_and_protocols.md
paper/draft/05_diagnostics_temporal_edge_heterophily.md
paper/draft/06_method_candidates.md
paper/draft/07_experiments.md
paper/draft/08_failure_analysis.md
paper/draft/09_limitations.md
```

## 6. 章节写作要点

### Introduction

必须包含：

```text
1. Bitcoin entity risk identification differs from static node classification.
2. Existing random-split evaluation may overestimate real future generalization.
3. Directed transaction flow and edge-time semantics are essential.
4. Strong heterophily and unlabeled-neighbor dilution challenge standard GNNs.
```

### Problem Definition

必须明确：

```text
- Node labels are entity categories, not purely illicit labels.
- UNLABELED nodes are graph context, not negative/normal class.
- Risk ranking is evaluated separately from closed-set classification.
```

### Diagnostics

必须回答：

```text
1. temporal_balanced 为什么显著更难？
2. 哪些类的异配最强？
3. 未标注邻居是否稀释消息传递？
4. 方向信息为何有用？
5. MIXER / EXCHANGE 混淆是否提示节点分类边界？
```

### Experiments

必须包含：

```text
1. baseline comparison
2. protocol comparison
3. temporal OOD gate experiments
4. ablation
5. multi-seed
6. conservative and extended sensitive ranking
7. case study
```

## 7. 不能写的 claim

禁止：

```text
1. 我们达到 SOTA。
2. EXCHANGE 是非法类别。
3. UNLABELED 是正常类别。
4. EGS 已解决 temporal generalization。
5. random split 结果代表真实部署效果。
6. 模型能直接识别非法交易。
```

推荐：

```text
1. EGS/方向聚合在随机分层主协议上显著提升。
2. temporal_balanced 显示时间外推仍然困难。
3. conservative sensitive ranking 反映高敏感实体发现能力。
4. MIXER 等类可能需要 subgraph reasoning。
```
