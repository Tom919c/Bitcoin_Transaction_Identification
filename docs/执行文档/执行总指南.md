# BTC-AML 项目后续执行总指南

## 0. Codex 的角色边界

你是本项目的工程与实验执行代理，不是完全自主的研究负责人。你的任务是按照本文档分阶段推进代码实现、实验运行、结果整理、诊断分析和论文材料草稿生成。你可以根据实验结果提出下一步建议，但不能私自推翻项目主线、修改标签语义、夸大实验结论或把项目改成无关方向。

本项目当前目标不是“继续堆普通 GNN 模型”，而是围绕以下主线推进：

```text
采样偏差发现
→ 标签保持 / 类别均衡 / 时间泛化数据协议
→ 完整 11 类长尾比特币实体识别
→ MLP / GraphSAGE 强基线
→ 边属性、时间语义、资金流方向感知模型
→ 消融实验、多 seed、论文材料整理
```

当前项目是进行中的科研项目。每个阶段都必须生成可检查产物，阶段完成后再决定是否进入下一阶段。

---

## 1. 不可推翻的项目结论

以下结论已经确定，不允许重新推翻，除非用户明确要求重新做 EDA 或发现代码/数据严重错误。

### 1.1 数据与任务主线

原始数据库规模约为：

```text
nodes: 252M+
edges: 785M+
labeled nodes: 34,098
label space: 11 classes
```

旧 `data.pt` 来自 TopK / Z-score 活跃实体采样，只保留约：

```text
350,258 nodes
17,173,503 edges
2,961 labeled nodes
5 supervised classes
```

旧 `data.pt` 丢失了多个 AML 关键类别：

```text
MINING
PONZI
RANSOMWARE
FAUCET
MARKETPLACE
MIXER
```

因此旧 `data.pt` 只能作为 activity-biased / TopK baseline，不能作为最终主数据集。

### 1.2 当前三套新协议

已经构建的新协议数据集：

```text
data/processed/protocols/label_preserving.pt
data/processed/protocols/class_balanced_khop.pt
data/processed/protocols/temporal_balanced.pt
```

协议定位：

```text
label_preserving:
    标签保持验证协议 / 采样偏差对照组
    保留全部 11 类标签，但图结构较稀疏，不作为最终主训练图。

class_balanced_khop:
    第一主训练数据集
    保留全部 11 类标签，提供更丰富邻域上下文，作为主结果数据集。

temporal_balanced:
    classwise temporal 泛化实验数据集
    用于验证模型从较早实体泛化到较晚实体的能力。
```

### 1.3 标签逻辑绝对不能改错

所有训练、评估、损失函数、指标、报告、可视化都必须遵守：

```text
-1 = UNLABELED / 背景节点，不参与监督训练和评估
0~10 = 11 个监督类别
num_classes = 11
ignore_index = -1
supervised_mask = y >= 0
```

错误逻辑严禁出现：

```python
y != 0
label > 0
ignore_index = 0
num_classes = 10
```

尤其注意：`INDIVIDUAL = 0` 是监督类别，必须参与训练和评估，不能被当成未标注。

当前 11 类标签顺序必须统一为：

```text
0  INDIVIDUAL
1  BET
2  GAMBLING
3  EXCHANGE
4  MINING
5  PONZI
6  RANSOMWARE
7  FAUCET
8  MARKETPLACE
9  MIXER
10 BRIDGE
```

### 1.4 风险类别表述

不要说：

```text
EXCHANGE 是非法类别
INDIVIDUAL 是非法类别
UNLABELED/NONE 是正常类别
旧 data.pt 是完整原始数据的随机子图
当前任务只是 5 类分类
```

建议说：

```text
UNLABELED 是背景上下文节点，不作为监督类别
EXCHANGE 是服务型实体，不默认等同于非法风险
PONZI / RANSOMWARE / MIXER / MARKETPLACE 是 AML 敏感类别
旧 data.pt 是 activity-biased sampled subgraph
当前主任务是完整 11 类长尾比特币实体识别
```

---

## 2. 当前已经获得的实验结果

第一轮 MLP / GraphSAGE baseline 已完成。

### 2.1 label_preserving

```text
MLP:
    Macro-F1 = 0.395237
    Minority Macro-F1 = 0.422689
    Weighted-F1 = 0.737611

GraphSAGE:
    Macro-F1 = 0.462693
    Minority Macro-F1 = 0.487311
    Weighted-F1 = 0.780458
```

### 2.2 class_balanced_khop

```text
MLP:
    Macro-F1 = 0.411421
    Minority Macro-F1 = 0.451027
    Weighted-F1 = 0.738288

GraphSAGE:
    Macro-F1 = 0.586779
    Minority Macro-F1 = 0.623872
    Weighted-F1 = 0.895973
```

### 2.3 temporal_balanced

```text
MLP:
    Macro-F1 = 0.125540
    Minority Macro-F1 = 0.185208
    Weighted-F1 = 0.168033

GraphSAGE:
    Macro-F1 = 0.193079
    Minority Macro-F1 = 0.244769
    Weighted-F1 = 0.351454
```

### 2.4 当前实验含义

必须保留以下阶段性结论：

```text
1. GraphSAGE 在三套新协议上均超过 MLP，说明合理协议下图结构信息确实有用。
2. class_balanced_khop 是目前最强主训练协议。
3. label_preserving 能保留标签，但图结构太稀疏，不适合作为主训练图。
4. temporal_balanced 明显更难，说明时间泛化是后续模型的重要难点。
5. 后续模型应优先围绕 edge_attr、temporal features 和 direction-aware aggregation 展开。
```

不要把当前结果写成“达到 SOTA”。当前只是项目内部第一轮 baseline。

---

## 3. 当前代码状态假设

项目应以最新清理后的代码为准，主结构应尽量保持：

```text
src/btcaml/
scripts/
configs/
tests/
docs/
experiments/
paper/
```

不要恢复旧的顶层旧接口目录，例如：

```text
models/
training/
interface/
config/
data/*.py
```

Git 已负责历史版本管理，代码层面不需要保留旧接口兼容。后续只保留最新主线代码。

如果发现项目里仍有旧目录，请先判断是否仍被当前主入口引用：

```text
scripts/run_benchmark.py
scripts/build_protocol_dataset.py
scripts/audit_raw_labels.py
scripts/compare_protocols.py
scripts/inspect_protocol_dataset.py
scripts/export_detailed_eval.py
scripts/summarize_benchmark_runs.py
```

若未引用，优先删除或移入明确的 archive 目录；但不要删除：

```text
data/processed/protocols/*.pt
experiments/runs/*
.env
.env.example
configs/data/*.yaml
```

---

## 4. 总体执行原则

### 4.1 每阶段必须可验收

每个阶段必须输出：

```text
1. 代码改动摘要
2. 运行命令
3. 关键输出路径
4. 是否通过 pytest
5. 结果表格
6. 下一步建议
```

每阶段结束后更新：

```text
docs/EXPERIMENT_STATUS.md
docs/DECISION_LOG.md
```

### 4.2 每次重要改动必须测试

最低测试：

```powershell
python -m pytest -q
```

如果修改了数据构建、标签逻辑、模型 forward、指标计算、实验脚本，必须加或更新测试。

### 4.3 先 smoke，再正式跑

所有新模型或新脚本必须先 smoke test：

```powershell
python scripts/run_benchmark.py --data data/processed/protocols/class_balanced_khop.pt --models <model> --smoke --device cpu
```

smoke 通过后再跑正式实验。

### 4.4 不要暴力跑实验矩阵

不要默认跑：

```text
3 datasets × 8 models × 5 seeds × 300 epochs
```

这会浪费时间。必须先单 seed 判断方向，再对关键模型做 multi-seed。

### 4.5 不要追求短期刷分

如果模型在 temporal_balanced 或 minority/sensitive 类上有效，即使 overall weighted-F1 没有明显提升，也可能有研究价值。

主要指标优先级：

```text
Macro-F1
Minority Macro-F1
Sensitive Macro-F1
Per-class Precision / Recall / F1
Temporal balanced performance
Weighted-F1
```

Weighted-F1 不能作为唯一指标。

---

## 5. 推荐生成的文档和目录

请创建或维护以下文件：

```text
docs/CODEX_EXECUTION_GUIDE.md
    本指南。只在用户允许时更新。

docs/EXPERIMENT_STATUS.md
    当前实验状态表。每阶段结束必须更新。

docs/DECISION_LOG.md
    记录每次路线选择原因，例如是否继续 ETD-SAGE、是否做 focal loss。

docs/KNOWN_ISSUES.md
    记录发现的问题、错误、未解决事项和处理方式。

experiments/summary/
    存放跨 run 汇总表。

experiments/diagnostics/
    存放协议诊断、时间漂移、邻居结构分析。

paper/tables/
    存放论文表格 CSV / Markdown / LaTeX。

paper/figures/
    存放可视化图。

paper/draft/
    存放论文初稿章节草稿。
```

不建议一开始把执行指南拆成很多文件。主指南保持一个文件，执行过程中的状态和结果再拆分。

---

# Phase 0：环境与代码完整性检查

## 目标

确认项目能运行、路径清楚、数据存在、标签逻辑没坏。

## 任务

1. 检查项目结构。
2. 检查三套协议数据是否存在。
3. 运行测试。
4. 检查当前 benchmark 脚本是否支持：
   - `mlp`
   - `sage`
   - 后续要加入的 `edge_gated_sage`
   - 后续要加入的 `etd_sage`
5. 检查是否能导出 per-class、confusion matrix 和 predictions。
6. 更新 `docs/EXPERIMENT_STATUS.md`。

## 命令

```powershell
python -m pytest -q
```

```powershell
Test-Path data/processed/protocols/label_preserving.pt
Test-Path data/processed/protocols/class_balanced_khop.pt
Test-Path data/processed/protocols/temporal_balanced.pt
```

## 成功标准

```text
pytest 通过
三套协议数据存在
run_benchmark.py 可正常 import
没有旧标签逻辑
```

## 如果失败

### pytest 失败

先修测试，不要跑实验。

### 数据不存在

不要重新写模型。先提示用户：

```text
缺少协议数据，请先运行 build_protocol_dataset.py 或提供 data/processed/protocols/*.pt。
```

### CUDA 不可用

使用 CPU 跑 smoke 和小规模正式实验。必要时降低 epochs 或使用 `--smoke`。

---

# Phase 1：补齐详细评估与 baseline 汇总

## 目标

把现有 MLP / GraphSAGE 第一轮结果整理成可写论文的材料。

## 必须产出

```text
experiments/summary/baseline_protocol_comparison.csv
experiments/summary/baseline_protocol_comparison.md

每个正式 run 下：
mlp/evaluation/test_per_class.csv
mlp/evaluation/test_confusion_matrix.csv
mlp/evaluation/test_confusion_matrix_norm_true.csv
mlp/evaluation/test_predictions.csv

sage/evaluation/test_per_class.csv
sage/evaluation/test_confusion_matrix.csv
sage/evaluation/test_confusion_matrix_norm_true.csv
sage/evaluation/test_predictions.csv
```

## 任务 A：确认历史 run 是否有 checkpoint

执行：

```powershell
Get-ChildItem experiments\runs -Recurse | Where-Object { $_.Name -match "best|checkpoint|\.pt|\.pth" }
```

### 如果有 checkpoint

对已有 run 直接补导出：

```powershell
python scripts/export_detailed_eval.py --run-dir experiments/runs/20260615_000802_label_preserving_mlp-sage --data data/processed/protocols/label_preserving.pt --models mlp sage --device cpu
```

```powershell
python scripts/export_detailed_eval.py --run-dir experiments/runs/20260615_000734_class_balanced_khop_mlp-sage --data data/processed/protocols/class_balanced_khop.pt --models mlp sage --device cpu
```

```powershell
python scripts/export_detailed_eval.py --run-dir experiments/runs/20260615_000816_temporal_balanced_mlp-sage --data data/processed/protocols/temporal_balanced.pt --models mlp sage --device cpu
```

### 如果没有 checkpoint

不能从 `results.csv` 还原混淆矩阵。必须重新跑 benchmark：

```powershell
python scripts/run_benchmark.py --data data/processed/protocols/label_preserving.pt --models mlp sage --device cpu --run-name lp_mlp_sage_stage2
```

```powershell
python scripts/run_benchmark.py --data data/processed/protocols/class_balanced_khop.pt --models mlp sage --device cpu --run-name cbk_mlp_sage_stage2
```

```powershell
python scripts/run_benchmark.py --data data/processed/protocols/temporal_balanced.pt --models mlp sage --device cpu --run-name temporal_mlp_sage_stage2
```

## 任务 B：汇总 baseline

```powershell
python scripts/summarize_benchmark_runs.py --runs-dir experiments/runs --out experiments/summary/baseline_protocol_comparison.csv
```

## 任务 C：生成简短分析

新增或更新：

```text
experiments/summary/baseline_protocol_analysis.md
```

内容包括：

```text
1. 三套协议结果总表
2. SAGE 相比 MLP 的提升
3. class_balanced_khop 为什么是主协议
4. temporal_balanced 为什么是时间泛化难点
5. 哪些类别需要进一步查看 per-class 指标
```

## 成功标准

```text
baseline_protocol_comparison.md 存在
每个正式 run 有 test_per_class.csv
每个正式 run 有 test_confusion_matrix.csv
docs/EXPERIMENT_STATUS.md 更新
```

---

# Phase 2：协议诊断与 temporal 性能下降分析

## 目标

解释为什么：

```text
class_balanced_khop 上 GraphSAGE 表现强
temporal_balanced 上 GraphSAGE 明显下降
```

不是只看分数，而要找到结构和时间上的原因。

## 新增脚本

建议新增：

```text
scripts/analyze_protocol_diagnostics.py
```

可选拆分：

```text
scripts/analyze_temporal_shift.py
scripts/analyze_label_neighbors.py
scripts/analyze_class_degree.py
```

但如果代码量不大，优先写成一个主脚本，避免脚本碎片化。

## 输入

```text
data/processed/protocols/label_preserving.pt
data/processed/protocols/class_balanced_khop.pt
data/processed/protocols/temporal_balanced.pt
```

## 输出

```text
experiments/diagnostics/protocol_diagnostics.csv
experiments/diagnostics/protocol_diagnostics.md
experiments/diagnostics/class_split_stats.csv
experiments/diagnostics/class_degree_stats.csv
experiments/diagnostics/neighbor_label_stats.csv
experiments/diagnostics/temporal_shift_stats.csv
experiments/diagnostics/diagnostics_report.md
```

## 必须分析

### 2.1 每类样本分布

```text
class_name
train_count
val_count
test_count
total_count
```

### 2.2 每类时间分布

如果数据中有时间字段或可用的 split temporal summary，输出：

```text
class_name
split
time_min
time_p25
time_median
time_mean
time_p75
time_max
```

### 2.3 每类度数分布

```text
class_name
degree_mean
degree_median
degree_p90
degree_max
in_degree_mean
out_degree_mean
```

### 2.4 邻居标签分布

对每个监督类别统计 1-hop 邻居：

```text
class_name
avg_neighbors
avg_labeled_neighbors
avg_unlabeled_neighbors
same_label_neighbor_ratio
unlabeled_neighbor_ratio
top_neighbor_labels
```

### 2.5 temporal shift

比较 temporal_balanced 中 train / val / test 的节点特征分布：

```text
feature_mean_train
feature_mean_test
absolute_shift
relative_shift
```

如果特征名不可用，至少按 feature index 输出。

## 诊断报告必须回答

```text
1. class_balanced_khop 为什么比 label_preserving 更适合 GNN？
2. temporal_balanced 为什么比 class_balanced_khop 难？
3. 哪些类别是主要失败来源？
4. 是特征漂移、邻域漂移、类别样本过少，还是图结构问题？
5. 后续 EdgeGatedSAGE / ETD-SAGE 应优先解决什么？
```

## 成功标准

```text
diagnostics_report.md 存在
能指出至少 3 个具体观察
不夸大因果，只写“可能解释”或“支持以下推测”
```

## 如果无法读取时间字段

不要阻塞。报告中写明：

```text
当前 Data 对象中未找到明确时间字段，因此 temporal shift 仅基于 split 和节点特征统计；若后续需要严格时间边过滤，需在数据构建阶段保存 node_time / edge_time。
```

---

# Phase 3：补充最小普通 GNN 基线

## 目标

不要大规模堆模型，只补最小必要基线，证明 GraphSAGE 是合理强基线。

## 推荐模型

优先只在 `class_balanced_khop` 上补：

```text
gcn
gat
appnp
res_sage
```

如果这些模型当前已经实现且接入成本低，可以跑；如果没有实现，不要为了普通 baseline 耗太久。

## 命令示例

```powershell
python scripts/run_benchmark.py --data data/processed/protocols/class_balanced_khop.pt --models gcn gat appnp res_sage --device cpu --run-name cbk_extra_baselines
```

如 CPU 太慢，先 smoke：

```powershell
python scripts/run_benchmark.py --data data/processed/protocols/class_balanced_khop.pt --models gcn --smoke --device cpu
```

## 成功标准

```text
class_balanced_khop 上至少补 2 个普通 GNN baseline
输出结果进入 experiments/summary/model_baseline_comparison.md
```

## 如果普通 GNN 实现成本高

跳过，不要阻塞主线。记录到 `DECISION_LOG.md`：

```text
普通 GNN 补充基线暂缓，原因：接入成本高 / 当前主线更需要 edge-temporal model。
```

---

# Phase 4：EdgeGatedSAGE / Edge-aware GraphSAGE

## 目标

验证交易边属性是否能帮助实体识别，尤其是 temporal_balanced 和 minority/sensitive 类。

## 模型优先级

先实现轻量模型，不要一开始做复杂 TGN。

建议实现：

```text
EdgeMLPEncoder
EdgeGatedSAGE
```

核心思想：

```text
edge_attr -> MLP -> gate
message = gate * neighbor_embedding
```

如果 PyG MessagePassing 实现复杂，可以先实现简化版。必须保证：

```text
支持 x, edge_index, edge_attr
没有 edge_attr 时给出明确错误或退化为普通 SAGE
模型输出 shape = [num_nodes, 11]
```

## 文件建议

```text
src/btcaml/models/edge_sage.py
src/btcaml/models/__init__.py
scripts/run_benchmark.py
tests/test_models.py
```

如已有模型注册机制，按现有风格接入，不要另起一套训练入口。

## 运行顺序

### Smoke

```powershell
python scripts/run_benchmark.py --data data/processed/protocols/class_balanced_khop.pt --models edge_gated_sage --smoke --device cpu
```

### 正式单 seed

```powershell
python scripts/run_benchmark.py --data data/processed/protocols/class_balanced_khop.pt --models sage edge_gated_sage --device cpu --run-name cbk_edge_gated_sage
```

```powershell
python scripts/run_benchmark.py --data data/processed/protocols/temporal_balanced.pt --models sage edge_gated_sage --device cpu --run-name temporal_edge_gated_sage
```

## 指标关注

```text
Macro-F1
Minority Macro-F1
Sensitive Macro-F1
Per-class F1 / Recall
temporal_balanced improvement
```

## 决策规则

### 如果 EdgeGatedSAGE 在 temporal_balanced 上提升明显

满足任一条件：

```text
Macro-F1 提升 >= 0.02
Minority Macro-F1 提升 >= 0.02
Sensitive Macro-F1 提升 >= 0.02
至少两个 AML 敏感类别 recall 提升明显
```

则进入 Phase 5：ETD-SAGE。

### 如果只在 class_balanced_khop 上提升，temporal 不提升

继续 Phase 5，但优先加强 temporal feature engineering，并在报告中明确：

```text
Edge information improves static/random-like protocol but does not fully solve temporal generalization.
```

### 如果 EdgeGatedSAGE 不如 GraphSAGE

不要继续盲目堆更复杂模型。先检查：

```text
edge_attr 是否存在
edge_attr 是否与 edge_index 对齐
edge_attr 是否需要 log1p / clip / normalize
是否过拟合
是否 gate 饱和
是否学习率不合适
```

然后尝试最多两个轻量修复：

```text
1. edge_attr log1p + standardization
2. dropout / weight_decay 调整
```

若仍无提升，记录负结果。不要把失败藏起来。

---

# Phase 5：ETD-SAGE / Edge-Temporal-Directional SAGE

## 目标

实现论文主方法候选：边属性 + 时间语义 + 资金流方向分离。

## 模型思想

每个节点更新由三部分组成：

```text
h_self = self transform
h_in   = aggregate incoming neighbors with edge/time gate
h_out  = aggregate outgoing neighbors with edge/time gate
h_new  = MLP([h_self, h_in, h_out])
```

## 需要支持的特征

从 edge_attr 中尽量构造：

```text
amount features
frequency features
duration = last_seen - reveal + 1
recency = global_max_time - last_seen
amount_range = max_sent - min_sent
avg_sent = total_sent / total
```

金额类建议：

```text
log1p
clip / winsorize
standardize
```

如果当前 Data 中没有明确 edge feature names，先按列索引实现，并在 report 中记录假设。

## 文件建议

```text
src/btcaml/models/etd_sage.py
src/btcaml/features/edge_features.py
src/btcaml/models/__init__.py
scripts/run_benchmark.py
tests/test_models.py
tests/test_edge_features.py
```

## 必须有 ablation 开关

ETD-SAGE 至少支持：

```text
use_edge_attr = true/false
use_temporal = true/false
use_direction = true/false
```

或通过不同 model name 注册：

```text
edge_gated_sage
edge_temporal_sage
directional_sage
etd_sage
```

选择一种最简洁、最少改动的实现方式。

## 实验

优先跑：

```powershell
python scripts/run_benchmark.py --data data/processed/protocols/class_balanced_khop.pt --models sage edge_gated_sage etd_sage --device cpu --run-name cbk_etd_sage
```

```powershell
python scripts/run_benchmark.py --data data/processed/protocols/temporal_balanced.pt --models sage edge_gated_sage etd_sage --device cpu --run-name temporal_etd_sage
```

## 决策规则

### 如果 ETD-SAGE 明显优于 GraphSAGE

进入 Phase 6 消融和多 seed。ETD-SAGE 作为主方法。

### 如果 ETD-SAGE 只在 minority/sensitive 上优于 GraphSAGE

仍然有研究价值。论文表述为：

```text
ETD-SAGE improves long-tailed / sensitive entity identification, even when overall weighted metrics are not always higher.
```

### 如果 ETD-SAGE 不优于 GraphSAGE

不要硬写成主方法。论文主线调整为：

```text
采样协议贡献 + 时间泛化困难 + 边时序模型负结果分析
```

ETD-SAGE 作为探索性改进或未来工作。

---

# Phase 6：损失函数与长尾优化

## 目标

在 GraphSAGE / EdgeGatedSAGE / ETD-SAGE 的基础上改善长尾类。

## 候选方法

按优先级：

```text
1. class-weighted cross entropy
2. focal loss
3. class-balanced focal loss
4. balanced softmax
```

不要一开始做复杂 supervised contrastive learning 或 pseudo-label，除非前面模型已经稳定。

## 实验规则

只在当前最优模型上做，不对所有模型做。

例如：

```text
GraphSAGE + CE
GraphSAGE + weighted CE
BestEdgeModel + CE
BestEdgeModel + focal
BestEdgeModel + class-balanced focal
```

## 决策规则

如果 focal loss 提升 minority/sensitive，但降低整体 Macro-F1，需要报告 trade-off，不要只挑最好看的指标。

---

# Phase 7：消融实验

## 目标

证明每个模块是否真的有贡献。

## 最小消融表

如果 ETD-SAGE 是主方法，至少跑：

```text
Full ETD-SAGE
w/o edge_attr
w/o temporal features
w/o direction split
GraphSAGE baseline
MLP baseline
```

如果长尾 loss 有贡献，再加：

```text
w/o long-tail loss
```

## 输出

```text
experiments/summary/ablation_results.csv
experiments/summary/ablation_results.md
paper/tables/table_ablation.md
```

## 解释规则

消融实验不要只写“下降了多少”。必须解释：

```text
edge_attr 对哪些类有帮助？
temporal 对 temporal_balanced 是否有帮助？
direction 对资金流类 / AML 敏感类是否有帮助？
long-tail loss 是否改善小类 recall？
```

---

# Phase 8：关键实验 multi-seed

## 目标

把结果从“单次看起来有效”变成“可写论文/答辩可信”。

## 不要全量 multi-seed

只跑关键组合：

```text
Datasets:
    class_balanced_khop
    temporal_balanced

Models:
    MLP
    GraphSAGE
    BestEdgeModel
    ETD-SAGE or final selected model
```

Seeds：

```text
优先 3 seeds
时间允许再 5 seeds
```

## 输出

```text
experiments/summary/multiseed_results.csv
experiments/summary/multiseed_results.md
paper/tables/table_multiseed.md
```

表格格式：

```text
dataset
model
metric
mean
std
num_seeds
```

必须包括：

```text
Macro-F1
Minority Macro-F1
Sensitive Macro-F1
Weighted-F1
```

## 如果时间不够

至少对主协议 `class_balanced_khop` 跑 3 seed：

```text
MLP
GraphSAGE
最终模型
```

temporal 可以先保留 single seed，但在报告中说明计算资源限制。

---

# Phase 9：Sensitive Ranking 与 Top-K 评估

## 目标

把任务从单纯分类扩展到风控更关心的“高风险实体优先发现”。

## 风险组定义

不要把 EXCHANGE 默认当高风险。

建议：

```text
High-sensitive:
    PONZI
    RANSOMWARE
    MIXER

Medium-sensitive:
    BET
    GAMBLING
    MARKETPLACE
    BRIDGE

Neutral / service / context:
    INDIVIDUAL
    EXCHANGE
    MINING
    FAUCET
```

如果某些类样本过少，可以合并报告：

```text
Sensitive = High-sensitive + Medium-sensitive
```

## 指标

```text
Sensitive Macro-F1
Recall@K
Precision@K
Yield@Budget
AUPRC for sensitive-vs-rest
```

## 输出

```text
experiments/summary/sensitive_ranking.csv
experiments/summary/sensitive_ranking.md
paper/tables/table_sensitive_ranking.md
```

## 如果模型输出只有 11 类 logits

可以将 sensitive score 定义为：

```text
sum(probabilities of sensitive classes)
```

或者：

```text
max(probabilities of sensitive classes)
```

必须在报告中说明选择。

---

# Phase 10：案例分析与可解释材料

## 目标

为答辩和论文分析提供直观案例。

## 任务

对最终模型选择若干测试节点：

```text
正确识别的 PONZI / RANSOMWARE / MIXER / BET / GAMBLING / BRIDGE
误报案例
漏报案例
temporal 中失败案例
```

为每个案例导出：

```text
node_id
true_label
pred_label
confidence
top_neighbors
top_edges
edge_attr summary
1-hop / 2-hop local subgraph stats
```

## 输出

```text
paper/case_studies/case_ponzi_001.md
paper/case_studies/case_ransomware_001.md
paper/case_studies/case_mixer_001.md
paper/case_studies/case_temporal_failure_001.md
```

## 不要过早做 GUI

除非用户明确要求，不要优先恢复 PyQt GUI。先生成静态 case study Markdown 和图表。GUI 是答辩展示增强，不是当前主线核心。

---

# Phase 11：论文材料整理

## 目标

把实验材料整理成论文/大创报告可用草稿。

## 目录

```text
paper/draft/
paper/tables/
paper/figures/
paper/case_studies/
```

## 需要生成的表

```text
table_raw_label_audit.md
table_protocol_comparison.md
table_baseline_results.md
table_main_results.md
table_ablation.md
table_multiseed.md
table_sensitive_ranking.md
```

## 需要生成的图

```text
fig_label_distribution.png
fig_protocol_edges_nodes.png
fig_per_class_f1.png
fig_confusion_matrix_cbk_sage.png
fig_confusion_matrix_temporal_sage.png
fig_temporal_shift.png
fig_model_comparison.png
```

## 需要生成的草稿章节

```text
paper/draft/01_introduction_notes.md
paper/draft/02_dataset_audit.md
paper/draft/03_sampling_protocols.md
paper/draft/04_method_etd_sage.md
paper/draft/05_experiments.md
paper/draft/06_analysis.md
paper/draft/07_limitations.md
```

## 草稿写作原则

不要夸大：

```text
不要说达到 SOTA
不要说识别非法交易，除非任务确实是非法二分类
不要说 EXCHANGE 是非法
不要说 UNLABELED 是正常
不要说 temporal 结果好，如果它明显低
```

可以说：

```text
本文发现 activity-biased sampling 会严重扭曲标签空间。
class_balanced_khop 显著增强 GraphSAGE 的结构利用能力。
temporal_balanced 揭示静态 GNN 在时间泛化下仍面临困难。
边时序方向建模用于缓解普通邻居聚合无法利用交易语义的问题。
```

---

# 12. 所有可能事件与处理方式

## 情况 A：历史 run 没有 checkpoint

处理：

```text
不能生成 confusion matrix。
重新跑 benchmark。
未来 run_benchmark 必须保存 best checkpoint 和 test_predictions.csv。
```

## 情况 B：重新跑结果和历史结果略有差异

处理：

```text
检查 seed 是否一致。
检查代码版本是否改变。
检查数据文件是否一致。
在 EXPERIMENT_STATUS.md 中记录新旧结果。
以最新 clean code 结果为准。
```

## 情况 C：GraphSAGE 或新模型训练很慢

处理：

```text
先 smoke。
降低 epochs 做调试。
正式结果保留原 epochs。
优先跑 class_balanced_khop 和 temporal_balanced。
暂缓 label_preserving 上的新模型。
```

## 情况 D：CUDA 不可用

处理：

```text
使用 CPU。
减少普通基线数量。
保留关键模型。
不要跑全量 multi-seed。
```

## 情况 E：显存不足

处理：

```text
降低 hidden_dim。
降低 num_layers。
使用 CPU。
检查是否一次性复制了过多 tensor。
不要改变数据协议。
```

## 情况 F：edge_attr 不存在

处理：

```text
先确认 Data 对象字段。
如果没有 edge_attr，EdgeGatedSAGE 无法进行。
记录为数据问题。
不要伪造 edge_attr。
```

## 情况 G：edge_attr 维度和 edge_index 不一致

处理：

```text
立即停止训练。
修 build_graph / dataset loading。
添加测试：edge_attr.size(0) == edge_index.size(1)
```

## 情况 H：EdgeGatedSAGE 不如 GraphSAGE

处理：

```text
先检查 edge feature preprocessing。
尝试 log1p / normalize。
最多做两轮轻量修复。
仍不提升则记录负结果，不继续强行堆复杂模型。
```

## 情况 I：ETD-SAGE 不如 EdgeGatedSAGE

处理：

```text
保留 EdgeGatedSAGE 作为主方法。
ETD-SAGE 作为复杂模型负结果或未来工作。
```

## 情况 J：temporal_balanced 结果很差

处理：

```text
不要把它当失败。
这是时间泛化难点。
重点分析哪些类在时间上漂移、哪些类训练样本不足。
```

## 情况 K：某些小类 F1 为 0

处理：

```text
检查 support。
检查是否该类样本极少。
报告 per-class 结果。
可尝试 class-balanced loss。
不要隐瞒。
```

## 情况 L：weighted-F1 很高但 macro-F1 很低

处理：

```text
说明多数类主导。
论文主指标应强调 Macro-F1 和 Minority/Sensitive Macro-F1。
```

## 情况 M：Codex 想引入新大方向

例如：

```text
TGN
active learning
self-supervised contrastive learning
Elliptic2
GUI
```

处理：

```text
除非当前阶段已完成且用户同意，否则不要进入。
先完成 EdgeGatedSAGE / ETD-SAGE / 消融 / multi-seed。
```

---

# 13. 阶段性停止点

以下情况必须停止继续扩展，并向用户汇报：

```text
1. 标签逻辑出现不确定。
2. 数据文件缺失。
3. edge_attr 无法确认。
4. 新模型结果全面差于 GraphSAGE 且原因不明。
5. temporal 结果与预期严重不一致。
6. 需要重新构建大规模数据库协议。
7. 需要引入外部数据集。
8. 需要修改论文主线。
```

---

# 14. 推荐执行顺序总表

```text
Phase 0: 环境与代码完整性检查
Phase 1: per-class / confusion matrix / baseline 汇总
Phase 2: 协议诊断与 temporal 失败分析
Phase 3: 最小普通 GNN 补充基线，可选
Phase 4: EdgeGatedSAGE
Phase 5: ETD-SAGE
Phase 6: 长尾 loss 优化
Phase 7: 消融实验
Phase 8: multi-seed
Phase 9: sensitive ranking
Phase 10: case study
Phase 11: 论文材料整理
```

当前最优先执行：

```text
Phase 0
Phase 1
Phase 2
```

不要跳过 Phase 1 / Phase 2 直接写 ETD-SAGE。

---

# 15. 每阶段完成后必须写入 DECISION_LOG

格式：

```markdown
## YYYY-MM-DD Phase X Decision

### Completed
- ...

### Key Results
- ...

### Interpretation
- ...

### Decision
- Continue to ...
- Stop / postpone ...

### Risks
- ...

### Next Commands
```powershell
...
```
```

---

# 16. 最终交付物清单

项目推进到论文材料阶段时，应至少包含：

```text
1. 可运行代码
2. 三套协议数据说明
3. 第一轮 baseline 总表
4. per-class 指标
5. 混淆矩阵
6. 协议诊断报告
7. EdgeGatedSAGE / ETD-SAGE 主结果
8. 消融实验
9. multi-seed 结果
10. sensitive ranking 结果
11. case studies
12. paper draft sections
13. README / OPERATION_RUNBOOK
```

如果时间不足，最低可交付版本是：

```text
1. 采样偏差发现
2. 三套标签保持协议
3. MLP / GraphSAGE baseline
4. per-class 与 temporal 诊断
5. EdgeGatedSAGE 尝试
6. 消融或负结果分析
7. 大创报告材料
```

---

# 17. 最重要的提醒

本项目真正价值不是“某个模型分数最高”，而是：

```text
1. 发现旧 TopK 采样会扭曲原始标签空间。
2. 构建保留完整 11 类长尾标签的数据协议。
3. 证明 class_balanced_khop 能让 GraphSAGE 显著利用图结构。
4. 揭示 temporal 泛化明显更难。
5. 探索边属性、时间语义、资金流方向是否能进一步提升长尾风险实体识别。
```

如果后续模型没有明显提升，也不能算失败。此时论文主线应调整为：

```text
采样协议贡献 + 时间泛化挑战 + 图学习机制分析 + 边时序模型探索性结果
```

不要为了追求“正结果”破坏实验可信度。
