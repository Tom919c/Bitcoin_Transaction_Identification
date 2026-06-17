# Codex 启动提示词

请先完整阅读 `docs/CODEX_EXECUTION_GUIDE.md`，并从 Phase 0 开始执行。

执行要求：

1. 不要跳阶段。
2. 不要修改标签语义。
3. 每完成一个 Phase，必须更新：
   - `docs/EXPERIMENT_STATUS.md`
   - `docs/DECISION_LOG.md`
4. 所有训练、评估、指标、报告必须遵守：
   - `-1 = UNLABELED / 背景节点，忽略`
   - `0~10 = 11 个监督类别`
   - `INDIVIDUAL = 0` 必须参与训练和评估
   - `num_classes = 11`
   - `ignore_index = -1`
5. 不要把旧 TopK `data.pt` 当作最终主数据集，它只能作为 activity-biased baseline。
6. 当前最优先执行：
   - Phase 0：环境与代码完整性检查
   - Phase 1：per-class / confusion matrix / baseline 汇总
   - Phase 2：协议诊断与 temporal 性能下降分析
7. 每个阶段结束后停下来给出结果摘要、风险和下一步建议，不要直接一口气做到论文结束。
