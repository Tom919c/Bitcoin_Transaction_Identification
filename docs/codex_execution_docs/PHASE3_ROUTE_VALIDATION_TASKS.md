请阅读当前项目已有文档与实验结果，尤其是：

1. docs/btc_aml_codex_next_stage_docs/ 下的执行指南
2. experiments/route_validation/route_gate_decision.md
3. FULL_WORK_REPORT_CN.md
4. experiments/summary/current_result_manifest.md
5. experiments/summary/ablation_results.md
6. experiments/diagnostics/temporal_edge_heterophily_report.md

本轮任务不是继续扩展最终论文，也不是直接实现复杂 OOD 模型。你现在只执行“路线裁决补证阶段”，完成后必须停止。

请严格遵守以下总原则：

- 不要修改标签语义：
  - -1 = 未标注背景节点，不参与 loss 和 metrics
  - 0~10 = 11 个监督类别
  - INDIVIDUAL=0 是监督类别，不能当作未标注
- 不要把 EXCHANGE 默认定义为非法或高风险类
- 不要把当前结果包装成已经解决 temporal OOD
- 不要擅自实现 TGN、causal GNN、graph foundation model、open-world、PU learning 或子图模型
- 不要直接生成最终论文
- 不要进入完整 Phase 5
- 完成本轮任务后输出分析报告并停止

本轮只执行以下三个任务：

============================================================
Task A: Conservative Sensitive Ranking
============================================================

目标：
验证当前模型的风险排序能力是否真正适用于高敏感 AML 类，而不是被 BET 等容易类别抬高。

请定义两个风险集合：

1. conservative_sensitive:
   - PONZI
   - RANSOMWARE
   - MIXER

2. extended_sensitive:
   - BET
   - GAMBLING
   - MARKETPLACE
   - BRIDGE
   - PONZI
   - RANSOMWARE
   - MIXER

注意：
- EXCHANGE 不进入 sensitive 集合
- INDIVIDUAL 不进入 sensitive 集合
- MINING 和 FAUCET 默认不进入 sensitive 集合，除非报告中另行作为 neutral/service/context 说明

请基于已有 EGS multi-seed 结果或重新读取预测结果，计算：

- AUROC
- AUPRC
- Precision@1%
- Precision@5%
- Precision@10%
- Recall@1%
- Recall@5%
- Recall@10%
- Yield@Budget@1%
- Yield@Budget@5%
- Yield@Budget@10%

如果现有预测文件不足以计算 ranking，请先检查各 run 目录下是否有 test_predictions.csv / logits / probabilities / checkpoint。
如果没有，请不要伪造结果，应重新运行必要的 eval/export 脚本生成预测分数。

敏感分数定义优先级：

1. 如果有 softmax probability：
   sensitive_score = sum(probabilities of sensitive classes)

2. 如果只有 logits：
   先 softmax，再求 sensitive_score

3. 如果只有 predicted label：
   不能计算 AUPRC/AUROC，必须重新导出概率或 logits

输出文件：

- experiments/ranking/conservative_sensitive_ranking.csv
- experiments/ranking/extended_sensitive_ranking.csv
- experiments/ranking/sensitive_ranking_summary.md

summary.md 必须包含：

1. conservative vs extended 的结果对比
2. 是否存在 BET 主导 extended ranking 的风险
3. conservative ranking 是否足以支撑 AML 应用价值
4. 如果 conservative 表现明显差，应明确写出：
   “当前模型对高敏感 AML 类排序能力仍不足，不应夸大应用效果。”
5. 如果 conservative 表现仍较强，应明确写出：
   “风险排序可以作为应用贡献，但仍需结合 case study 验证。”

============================================================
Task B: Temporal Feature Failure Analysis
============================================================

目标：
解释为什么 EGS no-temporal-edge 在 class_balanced_khop 和 temporal_balanced 上反而优于完整 EGS。

请对比：

- EGS full
- EGS no-temporal-edge

至少分析以下内容：

1. class_balanced_khop 上 per-class Precision / Recall / F1 差异
2. temporal_balanced 上 per-class Precision / Recall / F1 差异
3. 哪些类别因为去掉 temporal edge features 变好
4. 哪些类别因为去掉 temporal edge features 变差
5. temporal edge features 的 train / val / test 分布漂移

如果可读取 edge_attr 的语义，请按语义分析，例如：

- reveal
- last_seen
- duration
- frequency
- recency
- total / amount related features

如果无法确认 edge_attr 语义，请按 feature index 分析，但必须在报告中声明：

“当前 Data 对象未提供明确 edge feature names，以下分析按 edge_attr index 进行。”

请计算每个 temporal edge feature 的：

- train mean / std
- val mean / std
- test mean / std
- train-test absolute mean shift
- train-test standardized mean shift
- KS statistic
- Wasserstein distance，如果实现成本低

同时检查：

- temporal features 与 label 的相关性或类别分布关系
- temporal features 是否在 random split 中可能形成伪相关
- temporal features 在 temporal split 中是否出现明显不可外推漂移

输出文件：

- experiments/diagnostics/temporal_feature_drift.csv
- experiments/diagnostics/temporal_feature_class_correlation.csv
- experiments/diagnostics/full_vs_no_temporal_per_class_delta_cbk.csv
- experiments/diagnostics/full_vs_no_temporal_per_class_delta_temporal.csv
- experiments/diagnostics/temporal_feature_failure_report.md

failure_report.md 必须回答：

1. 时间边特征为什么没有提升？
2. 是噪声问题、漂移问题、编码方式问题，还是伪相关问题？
3. 是否还能把 temporal features 作为方法贡献来写？
4. 后续是否有必要做 temporal OOD 方法？
5. 如果要做，应该做什么轻量原型？

注意：
如果证据不足，不要强行下结论。可以写：
“当前证据支持 temporal feature 可能存在漂移或伪相关，但还不足以证明因果关系。”

============================================================
Task C: Node Classification Boundary / Confusion Case Study
============================================================

目标：
判断 MIXER、GAMBLING、RANSOMWARE 等类别的错误是否暴露了节点分类边界，是否需要引入子图 reasoning 作为后续候选路线。

重点分析以下混淆对：

1. MIXER -> EXCHANGE
2. GAMBLING -> EXCHANGE
3. RANSOMWARE -> INDIVIDUAL
4. MARKETPLACE -> EXCHANGE，如果样本足够
5. PONZI -> INDIVIDUAL / EXCHANGE，如果样本足够

请从测试集预测中找出：

- true label
- predicted label
- prediction confidence
- top-3 predicted classes
- node id
- split
- model run / seed

对每类至少选取：

- 3 个典型误分类案例
- 3 个正确分类案例，如果 support 允许

对每个案例抽取或统计：

1. 1-hop 入边邻居标签分布
2. 1-hop 出边邻居标签分布
3. 2-hop 邻居标签分布，如果计算成本可接受
4. 未标注邻居比例
5. 同类邻居比例
6. in-degree / out-degree
7. total degree
8. 入边金额统计
9. 出边金额统计
10. 交易频率 / duration / recency 统计，如果 edge_attr 支持
11. 是否连接到 supernode
12. 是否主要连接到 EXCHANGE / INDIVIDUAL 背景节点

输出文件：

- experiments/case_studies/confusion_cases.csv
- experiments/case_studies/mixer_exchange_cases.md
- experiments/case_studies/gambling_exchange_cases.md
- experiments/case_studies/ransomware_individual_cases.md
- experiments/case_studies/node_classification_boundary_report.md

boundary_report.md 必须回答：

1. MIXER 被误分为 EXCHANGE 的主要原因是什么？
2. GAMBLING 和 EXCHANGE 是否存在结构/边特征混淆？
3. RANSOMWARE 是否被 INDIVIDUAL 背景邻居稀释？
4. 当前节点分类设定是否足够？
5. 哪些类别更可能需要 subgraph reasoning？
6. 子图路线是否应该进入下一阶段候选？只给建议，不要直接实现。

============================================================
最终汇总报告
============================================================

完成 Task A/B/C 后，生成：

- experiments/route_validation/phase3_evidence_report.md
- experiments/route_validation/next_route_recommendation.md

phase3_evidence_report.md 包含：

1. 本轮任务完成情况
2. 所有输出文件路径
3. 关键数字摘要
4. 对原 route_gate_decision.md 的修正或补充
5. 哪些证据增强了当前主线
6. 哪些证据削弱了当前主线
7. 哪些问题仍未解决

next_route_recommendation.md 必须按照以下格式给出路线建议：

A. 已成立，可以写入论文主贡献的内容
B. 已发现但不能夸大，只能写为 challenge / limitation 的内容
C. 需要下一轮实验才能决定的内容
D. 暂停或不建议继续投入的内容

最终判断必须在以下候选中选择一个或多个，但不能自造大方向：

1. Benchmark + Mechanism Analysis 主线
2. Direction-aware EGS 方法实证主线
3. Temporal OOD 轻量方法扩展
4. Conservative Risk Ranking 应用贡献
5. Node-to-Subgraph Boundary / Future Work

请特别注意：

- 如果 conservative ranking 很强，可以建议把 risk ranking 加入主贡献。
- 如果 conservative ranking 很弱，必须建议降低应用 claim。
- 如果 temporal feature drift 证据强，可以建议下一步做轻量 OOD 原型。
- 如果 temporal feature 只是噪声且无规律，不要建议复杂 temporal GNN。
- 如果 MIXER/EXCHANGE 混淆有明显局部子图模式，可以建议子图路线作为下一阶段候选。
- 如果只是 support 太少、信号不稳定，则只作为 limitation。

============================================================
停止条件
============================================================

完成以上输出后必须停止，不要继续：

- 不要写最终论文
- 不要生成投稿版 LaTeX
- 不要实现复杂 OOD 模型
- 不要实现子图 GNN
- 不要修改数据协议
- 不要改标签逻辑
- 不要把本轮结果自动包装成最终结论

最后在终端或回复中给出：

1. pytest 是否通过
2. 本轮新增/修改文件列表
3. 关键结果摘要
4. 是否建议进入下一轮 OOD 原型
5. 是否建议进入论文材料整理