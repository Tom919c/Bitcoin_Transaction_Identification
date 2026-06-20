# BTC-AML 下一阶段研究与 Codex 执行文档包

生成日期：2026-06-18

本压缩包用于把当前 BTC-AML 项目从“已有 EGS 实验结果”推进到“面向高水平论文的研究验证阶段”。

## 文件清单

```text
docs/00_README_如何使用.md
docs/01_NEXT_WORKPLAN_面向顶会.md
docs/02_CODEX_EXECUTION_GUIDE.md
docs/03_PHASE_CHECKLIST_AND_GATES.md
docs/04_CODEX_START_PROMPT.md
docs/05_PAPER_AND_ARTIFACT_SPEC.md
docs/06_DECISION_LOG_TEMPLATE.md
paper/draft/.gitkeep
paper/tables/.gitkeep
paper/figures/.gitkeep
```

## 建议使用方式

1. 把 `docs/` 目录复制到项目根目录。
2. 让 Codex 先阅读 `docs/04_CODEX_START_PROMPT.md`。
3. Codex 执行时必须以 `docs/02_CODEX_EXECUTION_GUIDE.md` 为准。
4. 每完成一个阶段，更新：
   - `docs/EXPERIMENT_STATUS.md`
   - `docs/DECISION_LOG.md`
5. 不要让 Codex 一口气做到论文结束。先完成 Phase 0–2，也就是：
   - 当前结果冻结；
   - temporal edge heterophily 量化；
   - 路线晋级实验矩阵。

## 当前推荐策略

不要直接把 EGS 当成最终答案。当前更高价值的研究问题是：

> 比特币实体风险识别不是普通静态节点分类，而是 directed temporal entity graph 上的 temporal edge heterophily + OOD risk identification 问题。

下一阶段要做的不是盲目堆模型，而是用一组可证伪实验判断哪条路线真正值得成为论文主线。
