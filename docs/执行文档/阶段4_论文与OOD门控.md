请阅读当前项目已有全部文档与实验产物，尤其是：

1. BTC_AML_FULL_DOCUMENTS_MERGED.md
2. experiments/route_validation/phase3_evidence_report.md
3. experiments/route_validation/next_route_recommendation.md
4. experiments/ranking/sensitive_ranking_summary.md
5. experiments/diagnostics/temporal_feature_failure_report.md
6. experiments/case_studies/node_classification_boundary_report.md
7. experiments/diagnostics/temporal_edge_heterophily_report.md
8. experiments/summary/current_result_manifest.md
9. experiments/summary/ablation_results.md

本轮任务是 Phase 4：论文证据包整理 + 轻量 OOD 原型门控实验。

你必须注意：你是实验执行器，不是研究路线裁决者。不要擅自改变研究主线，不要把探索性结果包装成最终结论。

当前总裁决如下：

1. 已成立的主线：

   * Sampling-aware benchmark
   * 11-class label-preserving protocol
   * Directed heterophily / unlabeled-neighbor dilution / hub exposure mechanism analysis
   * Direction-aware EGS method evidence
   * Conservative sensitive ranking application contribution

2. 已发现但不能夸大的问题：

   * Temporal OOD gap 仍未解决
   * Raw temporal edge features 不能作为方法贡献
   * MIXER node-level classification 可能不足，但样本太少，不能立即做 subgraph GNN
   * Extended ranking 被 BET/GAMBLING 抬高，必须同时报告 conservative ranking

3. 本轮只允许做：

   * Paper evidence package
   * 一个非常轻量、受控的 temporal OOD prototype gate

严禁事项：

* 不要修改标签语义
* 不要把 -1 当类别
* 不要把 INDIVIDUAL=0 当未标注
* 不要把 EXCHANGE 默认定义为非法或高风险
* 不要实现 TGN
* 不要实现 causal GNN
* 不要实现 graph foundation model
* 不要实现 open-world / PU learning
* 不要实现 subgraph GNN
* 不要继续尝试 focal loss gamma=2
* 不要直接写最终投稿论文
* 不要生成最终 LaTeX 论文
* 不要删除已有实验结果
* 不要覆盖已有 Phase 0–3 文档

============================================================
Task 1: Paper Evidence Package
==============================

目标：
把当前已经成立的证据整理成论文级材料，但不要写最终论文结论。

请生成以下目录和文件：

paper/tables/
paper/figures/
paper/draft/
experiments/paper_ready/

必须生成以下表格：

1. paper/tables/table_dataset_protocols.md
   内容：

   * label_preserving
   * class_balanced_khop
   * temporal_balanced
   * nodes
   * edges
   * labeled nodes
   * supervised classes
   * split type
   * protocol purpose

2. paper/tables/table_main_results.md
   内容：

   * MLP / SAGE / EGS
   * class_balanced_khop
   * temporal_balanced
   * Macro-F1
   * Minority-F1
   * Weighted-F1
   * mean ± std where available

3. paper/tables/table_ablation.md
   内容：

   * GraphSAGE
   * EGS full
   * EGS no-direction
   * EGS no-temporal-edge
   * EGS focal gamma=2
   * CBK and temporal results where available

4. paper/tables/table_conservative_ranking.md
   内容：

   * conservative_sensitive
   * extended_sensitive
   * AUPRC
   * AUROC
   * Recall@1/5/10%
   * Precision@1/5/10%
   * Yield@1/5/10%
   * mean ± std

5. paper/tables/table_temporal_feature_drift.md
   内容：

   * temporal edge feature name or index
   * train mean
   * test mean
   * standardized shift
   * KS statistic
   * Wasserstein distance
   * CBK vs temporal comparison

6. paper/tables/table_case_study_summary.md
   内容：

   * MIXER->EXCHANGE
   * GAMBLING->EXCHANGE
   * RANSOMWARE->INDIVIDUAL
   * PONZI->EXCHANGE
   * MARKETPLACE->EXCHANGE
   * #misclassified
   * #correct
   * avg degree
   * avg unlabeled ratio
   * avg same-label ratio
   * conclusion

必须生成以下图表：

1. paper/figures/fig_main_results_cbk.png

   * MLP / SAGE / EGS Macro-F1, Minority-F1, Weighted-F1

2. paper/figures/fig_temporal_gap.png

   * CBK vs temporal for SAGE and EGS
   * 强调 temporal gap

3. paper/figures/fig_ablation_direction_temporal.png

   * EGS full vs no-direction vs no-temporal-edge

4. paper/figures/fig_conservative_vs_extended_ranking.png

   * AUPRC and Recall@K comparison

5. paper/figures/fig_temporal_feature_drift.png

   * KS statistic for edge features under temporal split

6. paper/figures/fig_heterophily_unlabeled_ratio.png

   * per-class same-label ratio and unlabeled neighbor ratio

7. paper/figures/fig_case_study_confusion_counts.png

   * misclassified vs correct counts for key confusion pairs

请注意：

* 使用 matplotlib，不要使用 seaborn
* 每张图单独保存，不要做复杂子图网格
* 图表标题和轴标签使用英文，便于后续论文使用
* 不要随意指定花哨颜色
* 所有图必须可复现，生成脚本保存为 scripts/generate_paper_artifacts.py

必须生成以下草稿文件：

1. paper/draft/problem_definition.md
   写清楚任务不是非法二分类，而是 11 类 Bitcoin entity identification + sensitive risk ranking。

2. paper/draft/main_claims.md
   分成：
   A. 可以强 claim 的内容
   B. 只能作为 challenge / limitation 的内容
   C. 仍需下一轮实验验证的内容

3. paper/draft/experiment_summary.md
   总结 Phase 0–3 实验结果。

4. paper/draft/failure_analysis.md
   重点写：

   * temporal OOD gap
   * temporal feature drift / pseudo-correlation
   * MIXER node-level boundary
   * extended ranking inflated by easy classes

5. paper/draft/case_study_notes.md
   总结：

   * RANSOMWARE 方向成功案例
   * MIXER/EXCHANGE 边界
   * GAMBLING/EXCHANGE 混淆
   * PONZI/EXCHANGE 混淆

完成后输出：

experiments/paper_ready/paper_artifact_manifest.md

manifest 必须列出所有生成文件、输入来源、生成命令。

============================================================
Task 2: Lightweight Temporal OOD Prototype Gate
===============================================

目标：
只做一个受控轻量实验，用来判断 temporal OOD 方法是否有资格进入下一阶段主贡献。

当前强基线：

* EGS full temporal Macro-F1 = 0.2565
* EGS no-temporal-edge temporal Macro-F1 = 0.2675
* EGS no-temporal-edge CBK Macro-F1 = 0.6643

本轮只允许实现以下两个轻量候选中的一个或两个：

Option A: Topology-aware Reweighting Lite

思想：
根据训练节点的邻域难度调整 loss 权重，而不是引入复杂 OOD 模型。

允许使用的节点难度特征：

* unlabeled_neighbor_ratio
* same_label_neighbor_ratio，只能在 train 节点上用真实标签计算
* in_degree
* out_degree
* total_degree
* supernode exposure
* in/out heterophily score

注意：
不能在 val/test 上用真实标签构造训练特征，避免泄漏。

建议权重形式：

base_weight = existing_class_weight
difficulty_weight = clipped function of unlabeled_neighbor_ratio and heterophily
final_weight = base_weight * difficulty_weight

权重必须 clip，例如 [0.5, 2.0] 或 [0.5, 3.0]，避免训练崩溃。

Option B: Temporal Edge Filtering Lite

思想：
既然 raw temporal edge features 在 temporal split 中漂移严重，就不要直接使用它们。
在 EGS no-temporal-edge 的基础上，尝试对边消息进行轻量过滤。

允许策略：

1. drop or downweight edges with extreme drifted temporal feature values
2. use train-time quantile thresholds only
3. do not include raw temporal features in message MLP
4. filtering 只作为 edge mask / edge weight，不作为预测特征

必须避免：

* 不能用 test 统计量定阈值
* 不能把 test temporal distribution 用于训练
* 不能重新引入 raw temporal feature 作为普通 edge_attr

实验矩阵：

必须跑：

1. temporal_balanced:

   * EGS no-temporal-edge baseline
   * EGS no-temporal-edge + topology-aware reweighting
   * EGS no-temporal-edge + temporal edge filtering，如果实现
   * 3 seeds: 42, 43, 44

2. class_balanced_khop:

   * 只跑最优候选和 baseline
   * 至少 seed 42
   * 用于检查 CBK 是否灾难性下降

可选但推荐：

* conservative ranking on temporal or CBK for best candidate
* per-class F1 delta, especially PONZI, RANSOMWARE, MIXER

晋级门槛：

轻量 OOD 原型只有满足以下条件之一，才可以被建议进入方法主贡献：

A. Strong temporal pass:

* temporal Macro-F1 >= 0.2975
* 即相对当前最强 no-temporal baseline 0.2675 提升 >= +0.03

B. Conservative ranking pass:

* Conservative Recall@1% 从约 0.35 提升到 >= 0.50
* 且 Conservative AUPRC 不下降超过 0.03

同时必须满足：

* CBK Macro-F1 下降不超过 0.02
* 训练没有明显不稳定
* 3 seed 方向一致
* 不牺牲 PONZI/RANSOMWARE/MIXER 的整体表现

如果没有达到门槛：

必须写明：
“Lightweight OOD prototype does not pass the method-contribution gate. Temporal OOD remains an open challenge / limitation.”

不要为了小幅提升强行包装方法贡献。

输出文件：

* experiments/ood_lite/ood_lite_results.csv
* experiments/ood_lite/ood_lite_multiseed_summary.md
* experiments/ood_lite/ood_lite_per_class_delta.csv
* experiments/ood_lite/ood_lite_ranking_summary.md，如果计算 ranking
* experiments/ood_lite/ood_lite_gate_decision.md

ood_lite_gate_decision.md 必须包含：

1. 实现了哪个 prototype
2. 使用了哪些特征或过滤规则
3. 是否存在标签泄漏风险
4. temporal Macro-F1 是否达到 0.2975
5. Conservative Recall@1% 是否达到 0.50
6. CBK 是否显著下降
7. 是否建议进入论文方法主贡献
8. 如果失败，如何写进 limitation

============================================================
Task 3: Update Route Decision
=============================

完成 Task 1 和 Task 2 后，更新：

experiments/route_validation/final_route_after_phase4.md

该文件必须由以下结构组成：

## 1. Evidence Now Established

列出可以写入论文主贡献的内容。

## 2. Evidence Still Weak

列出不能夸大的内容。

## 3. OOD Prototype Gate Result

明确写：

* PASS
* WEAK PASS
* FAIL

## 4. Final Recommended Paper Positioning

只能从以下三个定位中选择：

A. Benchmark + Mechanism + Direction-aware EGS + Conservative Ranking
B. Benchmark + Mechanism + Direction-aware EGS + Conservative Ranking + Lightweight OOD Method
C. Benchmark + Mechanism + Direction-aware EGS only, Temporal OOD as limitation

## 5. What Codex Must Not Do Next

必须列出：

* 不要做 TGN
* 不要做 causal GNN
* 不要做 graph foundation model
* 不要做 subgraph GNN
* 不要做 open-world / PU learning
* 不要继续 focal gamma=2

============================================================
完成后停止
=====

完成以上任务后必须停止，不要继续写最终论文。

最后回复必须包含：

1. pytest 是否通过
2. 新增/修改文件列表
3. Paper artifacts 路径
4. OOD lite 结果摘要
5. 是否通过 OOD gate
6. 下一步是否建议进入论文正文生成

再次强调：
你只负责执行和产出证据，不负责最终研究裁决。
