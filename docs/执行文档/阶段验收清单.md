# Codex 阶段验收清单

## Phase 0：环境与代码完整性检查

- [ ] `python -m pytest -q` 通过
- [ ] 三套协议数据存在：
  - [ ] `data/processed/protocols/label_preserving.pt`
  - [ ] `data/processed/protocols/class_balanced_khop.pt`
  - [ ] `data/processed/protocols/temporal_balanced.pt`
- [ ] 检查无旧标签逻辑：
  - [ ] 不存在 `ignore_index=0`
  - [ ] 不存在用 `y != 0` 当监督 mask 的逻辑
  - [ ] 不存在用 `label > 0` 当监督 mask 的逻辑
- [ ] 更新 `docs/EXPERIMENT_STATUS.md`
- [ ] 更新 `docs/DECISION_LOG.md`

## Phase 1：详细评估与 baseline 汇总

- [ ] 检查历史 run 是否有 checkpoint
- [ ] 若有 checkpoint，运行 `scripts/export_detailed_eval.py`
- [ ] 若无 checkpoint，重新运行三套协议 MLP / SAGE benchmark
- [ ] 生成每个 run 的：
  - [ ] `test_per_class.csv`
  - [ ] `test_confusion_matrix.csv`
  - [ ] `test_confusion_matrix_norm_true.csv`
  - [ ] `test_predictions.csv`
- [ ] 生成：
  - [ ] `experiments/summary/baseline_protocol_comparison.csv`
  - [ ] `experiments/summary/baseline_protocol_comparison.md`
  - [ ] `experiments/summary/baseline_protocol_analysis.md`
- [ ] 更新 `docs/EXPERIMENT_STATUS.md`
- [ ] 更新 `docs/DECISION_LOG.md`

## Phase 2：协议诊断与 temporal 性能下降分析

- [ ] 新增或更新 `scripts/analyze_protocol_diagnostics.py`
- [ ] 生成：
  - [ ] `experiments/diagnostics/protocol_diagnostics.csv`
  - [ ] `experiments/diagnostics/protocol_diagnostics.md`
  - [ ] `experiments/diagnostics/class_split_stats.csv`
  - [ ] `experiments/diagnostics/class_degree_stats.csv`
  - [ ] `experiments/diagnostics/neighbor_label_stats.csv`
  - [ ] `experiments/diagnostics/temporal_shift_stats.csv`
  - [ ] `experiments/diagnostics/diagnostics_report.md`
- [ ] 报告必须回答：
  - [ ] 为什么 `class_balanced_khop` 比 `label_preserving` 更适合 GNN？
  - [ ] 为什么 `temporal_balanced` 明显更难？
  - [ ] 哪些类别是主要失败来源？
  - [ ] 后续 EdgeGatedSAGE / ETD-SAGE 应优先解决什么？
- [ ] 更新 `docs/EXPERIMENT_STATUS.md`
- [ ] 更新 `docs/DECISION_LOG.md`

## Phase 3：最小普通 GNN 补充基线，可选

- [ ] 判断是否已有低成本 GCN / GAT / APPNP / ResGraphSAGE 实现
- [ ] 只在 `class_balanced_khop` 上补最小必要 baseline
- [ ] 不为普通 GNN 阻塞主线
- [ ] 生成 `experiments/summary/model_baseline_comparison.md`

## Phase 4：EdgeGatedSAGE

- [ ] 实现 `EdgeMLPEncoder`
- [ ] 实现 `EdgeGatedSAGE`
- [ ] 接入 `run_benchmark.py`
- [ ] smoke test 通过
- [ ] 跑：
  - [ ] `class_balanced_khop`
  - [ ] `temporal_balanced`
- [ ] 对比 GraphSAGE，生成结果表
- [ ] 根据提升情况决定是否进入 Phase 5

## Phase 5：ETD-SAGE

- [ ] 实现 edge feature preprocessing
- [ ] 实现 temporal feature construction
- [ ] 实现入边 / 出边方向分离聚合
- [ ] 支持 ablation：
  - [ ] w/o edge_attr
  - [ ] w/o temporal
  - [ ] w/o direction
- [ ] smoke test 通过
- [ ] 跑主协议与 temporal 协议
- [ ] 决定 ETD-SAGE 是否作为主方法

## Phase 6：长尾优化

- [ ] 只在当前最优模型上测试
- [ ] 尝试 weighted CE / focal / class-balanced focal
- [ ] 重点看 Macro-F1、Minority Macro-F1、Sensitive Macro-F1
- [ ] 不只看 Weighted-F1

## Phase 7：消融实验

- [ ] 生成 `experiments/summary/ablation_results.csv`
- [ ] 生成 `experiments/summary/ablation_results.md`
- [ ] 生成 `paper/tables/table_ablation.md`

## Phase 8：multi-seed

- [ ] 只跑关键模型
- [ ] 优先 3 seeds，时间允许再 5 seeds
- [ ] 生成 `experiments/summary/multiseed_results.md`
- [ ] 生成 `paper/tables/table_multiseed.md`

## Phase 9：sensitive ranking

- [ ] 定义 sensitive score
- [ ] 计算 Recall@K / Precision@K / AUPRC
- [ ] 不把 EXCHANGE 默认当高风险

## Phase 10：case study

- [ ] 选择正确识别案例
- [ ] 选择误报案例
- [ ] 选择漏报案例
- [ ] 选择 temporal 失败案例
- [ ] 输出 Markdown case studies

## Phase 11：论文材料整理

- [ ] `paper/tables/`
- [ ] `paper/figures/`
- [ ] `paper/draft/`
- [ ] `paper/case_studies/`
- [ ] 不夸大结论
- [ ] 不写未经验证的 SOTA claim
