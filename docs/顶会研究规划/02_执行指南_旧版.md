# Codex 执行指南：BTC-AML 下一阶段研究验证

## 0. 角色边界

你是本项目的代码与实验执行代理，不是完全自主的研究负责人。你可以实现脚本、运行实验、整理结果、生成报告、提出建议，但不能私自推翻以下约束：

```text
-1 = UNLABELED / 背景节点，不参与训练和评估
0~10 = 11 个监督类别
num_classes = 11
ignore_index = -1
INDIVIDUAL = 0，必须参与监督
不能使用 y != 0 / label > 0 / ignore_index=0
不能把 EXCHANGE / INDIVIDUAL 说成非法类别
不能把 -1 / UNLABELED 说成正常类
```

当前目标不是继续堆普通 GNN，而是验证：

```text
比特币实体风险识别是否应被定义为 directed temporal heterophily OOD risk identification。
```

## 1. 执行原则

### 1.1 不要一上来写最终模型

本阶段目标是“路线验证”，不是“最终方法定型”。

先做：

```text
诊断指标
路线晋级实验
严格对比表
失败原因分析
```

再决定是否继续做复杂方法。

### 1.2 每次改动必须可验收

每个 Phase 结束必须输出：

```text
1. 修改了哪些文件
2. 运行了哪些命令
3. 生成了哪些结果文件
4. pytest 是否通过
5. 结果是否满足晋级阈值
6. 下一步建议
```

必须更新：

```text
docs/EXPERIMENT_STATUS.md
docs/DECISION_LOG.md
docs/KNOWN_ISSUES.md
```

### 1.3 先 smoke，再正式实验

任何新脚本、新模型、新损失、新评估函数都必须先 smoke。

示例：

```powershell
python -m pytest -q
python scripts/run_benchmark.py --data data/processed/protocols/class_balanced_khop.pt --models edge_gated_sage --smoke --device cpu
```

## 2. Phase 0：冻结当前状态与复现清单

### 目标

确认当前结果、代码、数据协议、run 目录和文档一致。

### 必做任务

1. 创建或更新：

```text
docs/EXPERIMENT_STATUS.md
docs/DECISION_LOG.md
docs/KNOWN_ISSUES.md
experiments/summary/current_result_manifest.md
```

2. 记录当前核心结果：

```text
class_balanced_khop:
    MLP Macro-F1 ≈ 0.4077
    GraphSAGE Macro-F1 ≈ 0.5785
    EGS Macro-F1 ≈ 0.6505

temporal_balanced:
    MLP Macro-F1 ≈ 0.1255
    GraphSAGE Macro-F1 ≈ 0.1931
    EGS Macro-F1 ≈ 0.2565

sensitive ranking:
    extended_sensitive AUPRC ≈ 0.748
    Recall@5% ≈ 0.827
```

3. 确认数据文件存在：

```text
data/processed/protocols/label_preserving.pt
data/processed/protocols/class_balanced_khop.pt
data/processed/protocols/temporal_balanced.pt
```

4. 确认模型结果目录存在，或记录缺失项。

### 命令

```powershell
python -m pytest -q
python scripts/summarize_benchmark_runs.py --runs-dir experiments/runs --out experiments/summary/current_all_runs.csv
```

### 验收标准

```text
pytest 通过
current_result_manifest.md 存在
EXPERIMENT_STATUS.md 更新
DECISION_LOG.md 写入 Phase 0
```

## 3. Phase 1：Temporal Edge Heterophily 诊断

### 目标

把“temporal 为什么难”量化出来。

### 新增模块建议

```text
src/btcaml/diagnostics/temporal_heterophily.py
src/btcaml/diagnostics/neighbor_stats.py
src/btcaml/diagnostics/drift.py
scripts/analyze_temporal_edge_heterophily.py
```

### 输入

```text
data/processed/protocols/class_balanced_khop.pt
data/processed/protocols/temporal_balanced.pt
data/processed/protocols/label_preserving.pt
```

### 必须输出

```text
experiments/diagnostics/temporal_edge_heterophily.csv
experiments/diagnostics/class_direction_compatibility_in.csv
experiments/diagnostics/class_direction_compatibility_out.csv
experiments/diagnostics/unlabeled_neighbor_dilution.csv
experiments/diagnostics/same_label_ratio_by_class_direction.csv
experiments/diagnostics/degree_exposure_by_class.csv
experiments/diagnostics/temporal_feature_drift_by_class.csv
experiments/diagnostics/temporal_edge_heterophily_report.md
```

### 指标定义

至少实现以下统计：

```text
1. same_label_ratio_in / same_label_ratio_out
2. labeled_neighbor_ratio_in / labeled_neighbor_ratio_out
3. unlabeled_neighbor_ratio_in / unlabeled_neighbor_ratio_out
4. class-to-class directed compatibility matrix
5. train-val-test feature drift per class
6. edge time distribution drift per class
7. degree exposure and supernode exposure
8. top confusion-pair neighborhood profile
```

如果 Data 中缺少明确时间字段：

```text
不要伪造时间。
先使用 edge_attr 中 reveal / last_seen / duration / recency 等列。
如果列名不可得，输出列索引假设，并在 report 中写明。
```

### 命令

```powershell
python scripts/analyze_temporal_edge_heterophily.py --data data/processed/protocols/class_balanced_khop.pt --out experiments/diagnostics/cbk
python scripts/analyze_temporal_edge_heterophily.py --data data/processed/protocols/temporal_balanced.pt --out experiments/diagnostics/temporal
```

### 测试

新增：

```text
tests/test_temporal_heterophily.py
```

测试内容：

```text
small synthetic graph 的 same_label_ratio 正确
-1 标签不进入 supervised class matrix
edge_index 与 edge_attr 长度一致
in/out 方向统计正确
```

### 验收标准

```text
诊断 CSV 存在
报告能回答 temporal performance drop 的至少 3 个可能机制
pytest 通过
```

## 4. Phase 2：路线晋级实验矩阵

### 目标

通过小而严谨的实验判断“Temporal OOD 方法路线”是否有资格成为论文主线。

### 实验组

必须优先跑 `temporal_balanced`，不是只跑 `class_balanced_khop`。

#### 4.1 基础对照

```text
MLP
GraphSAGE
EGS
```

#### 4.2 机制消融

```text
EGS w/o direction
EGS w/o edge_attr
EGS w/o temporal edge features
EGS w/o amount/frequency features
```

#### 4.3 轻量 OOD 原型

先实现轻量版本，不要一上来做完整 TGN。

候选：

```text
A. temporal_environment_reweight
   根据 train/val 时间分桶和类别分布进行样本重加权。

B. feature_structure_decoupled_head
   一个 head 只看 node feature，一个 head 看 graph message，两者可学习融合。

C. temporal_edge_filtering
   对过旧/过新的边进行衰减或过滤，避免时间不稳定邻居污染。

D. topology_aware_reweight
   根据未标注邻居比例、异配度、degree exposure 对节点 loss 或 message 权重重加权。
```

### 文件建议

```text
src/btcaml/models/ood_sage.py
src/btcaml/losses/reweighting.py
src/btcaml/evaluation/ranking.py
scripts/run_route_validation.py
scripts/summarize_route_validation.py
```

### 命令示例

```powershell
python scripts/run_route_validation.py --data data/processed/protocols/temporal_balanced.pt --models sage edge_gated_sage egs_no_temporal egs_no_direction egs_temporal_reweight --seeds 42 43 44 --device cpu
```

### 输出

```text
experiments/route_validation/temporal_ood_results.csv
experiments/route_validation/temporal_ood_results.md
experiments/route_validation/route_gate_decision.md
paper/tables/table_temporal_ood_gate.md
```

### 晋级标准

Temporal OOD 方法可成为主线，必须满足：

```text
1. temporal_balanced 3 seeds。
2. 相比 EGS，Macro-F1 mean >= +0.03。
3. Minority-F1 或 conservative_sensitive_AUPRC >= +0.03。
4. 至少一个难类 recall 有明显改善。
5. class_balanced_khop 不出现灾难性下降。
```

如果不满足：

```text
不要硬写方法主线。
转向 Benchmark + Mechanism Analysis 主线，并保留 OOD 原型为探索性结果。
```

## 5. Phase 3：Conservative Sensitive Ranking

### 目标

让风控应用指标更严谨。

### 风险集合

```python
HIGH_SENSITIVE = ["PONZI", "RANSOMWARE", "MIXER"]
EXTENDED_SENSITIVE = ["BET", "GAMBLING", "MARKETPLACE", "BRIDGE", "PONZI", "RANSOMWARE", "MIXER"]
```

不得把 `EXCHANGE` 或 `INDIVIDUAL` 默认放入 sensitive。

### 新增/更新文件

```text
src/btcaml/evaluation/ranking.py
scripts/evaluate_sensitive_ranking.py
tests/test_ranking.py
```

### 指标

```text
AUPRC
AUROC
Recall@1%
Recall@5%
Recall@10%
Precision@1%
Precision@5%
Precision@10%
Yield@Budget
```

### 输出

```text
experiments/summary/sensitive_ranking_conservative.csv
experiments/summary/sensitive_ranking_extended.csv
experiments/summary/sensitive_ranking_report.md
paper/tables/table_sensitive_ranking.md
```

### 验收标准

```text
conservative 与 extended 两套结果都存在
报告明确说明 extended 指标可能被 BET 等相对容易类抬高
```

## 6. Phase 4：节点分类边界与子图信号分析

### 目标

判断 MIXER / EXCHANGE、GAMBLING / EXCHANGE 混淆是否说明“某些类本质上需要 subgraph reasoning”。

### 新增脚本

```text
scripts/analyze_confusion_pairs.py
scripts/export_case_studies.py
```

### 分析对象

```text
MIXER -> EXCHANGE
EXCHANGE -> MIXER
GAMBLING -> EXCHANGE
MARKETPLACE -> EXCHANGE
RANSOMWARE -> INDIVIDUAL
```

### 输出

```text
experiments/diagnostics/confusion_pair_flow_stats.csv
experiments/diagnostics/confusion_pair_neighbor_stats.csv
paper/case_studies/mixer_exchange_boundary.md
paper/case_studies/gambling_exchange_boundary.md
paper/case_studies/ransomware_failure_cases.md
```

### 必须分析

```text
1. 1-hop / 2-hop 邻居标签分布
2. 入边 / 出边金额统计
3. 交易频率统计
4. recency / duration 统计
5. 是否存在高频小额流
6. 是否存在 EXCHANGE 中介邻居
7. 预测置信度与错误类型
```

### 验收标准

```text
至少生成 3 个成功案例和 3 个失败案例
报告说明哪些类适合节点分类，哪些类可能需要 subgraph reasoning
```

## 7. Phase 5：论文材料自动化

### 目标

把结果同步生成论文材料，避免最后手工整理崩盘。

### 输出目录

```text
paper/tables/
paper/figures/
paper/draft/
paper/case_studies/
```

### 必须生成表格

```text
table_dataset_protocols.md
table_main_results.md
table_temporal_ood_gate.md
table_ablation.md
table_multiseed.md
table_sensitive_ranking.md
table_diagnostics.md
```

### 必须生成图

```text
fig_model_comparison_cbk.png
fig_model_comparison_temporal.png
fig_per_class_f1_egs_vs_sage.png
fig_temporal_edge_heterophily.png
fig_unlabeled_neighbor_dilution.png
fig_confusion_matrix_egs_temporal.png
fig_sensitive_recall_at_k.png
```

### 必须生成草稿

```text
paper/draft/01_problem_definition.md
paper/draft/02_dataset_protocols.md
paper/draft/03_temporal_edge_heterophily.md
paper/draft/04_method_candidates.md
paper/draft/05_experiments.md
paper/draft/06_failure_analysis.md
paper/draft/07_limitations.md
```

## 8. 禁止事项

Codex 不得执行以下行为：

```text
1. 不得修改标签语义。
2. 不得把 -1 当成第 0 类。
3. 不得只在 class_balanced_khop 上涨分就宣布顶会方法成立。
4. 不得把 focal loss gamma=2.0 失败结果重复包装成有效。
5. 不得默认 EXCHANGE 是非法或敏感实体。
6. 不得恢复旧目录和旧接口兼容代码。
7. 不得一口气引入 TGN、GraphCL、PU learning、open-world、subgraph learning 等所有方向。
8. 不得没有 multi-seed 就宣称稳定提升。
9. 不得只报 Weighted-F1。
10. 不得在没有外部验证或公开协议的情况下夸大 benchmark 贡献。
```

## 9. 最终汇报格式

每个 Phase 完成后在聊天里输出：

```markdown
## Phase X 完成报告

### 代码改动
- ...

### 运行命令
```powershell
...
```

### 生成文件
- ...

### 核心结果
| metric | baseline | new | delta |
|---|---:|---:|---:|

### 是否满足晋级阈值
- 是 / 否
- 理由：

### 风险与问题
- ...

### 下一步建议
- ...
```
