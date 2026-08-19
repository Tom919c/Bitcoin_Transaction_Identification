# Candidate Research Problem Cards

> 状态：Gate 1 进行中。候选必须从已核验证据产生，不从旧 EGS 叙事反推。

## 问题卡结构

### CP-XX — 候选问题名称

- **Research question**：
- **Falsifiable hypothesis**：
- **Operational decision and stakeholder**：
- **Prediction unit and graph unit**：
- **Ground truth and label availability time**：
- **Why it matters**：
- **Nearest prior work**：
- **Actual gap rather than implementation gap**：
- **Minimum decisive experiment**：
- **Strong baselines and heuristics**：
- **Primary and secondary metrics**：
- **Data availability**：
- **Single-machine feasibility and engineering cost**：
- **Contribution type**：benchmark、empirical、data/label、method、workflow 或必要组合
- **Failure condition**：
- **Ethics and misuse risk**：
- **Strongest reviewer rejection argument**：
- **Evidence status**：

## 评分

| 维度 | 分值 |
|---|---|
| 问题重要性 | 1–5 |
| 证据质量 | 1–5 |
| 可行性 | 1–5 |
| 基础得分 | 三项乘积 |

以下不计分，直接 No-Go：

- 标签不能支撑主张。
- 存在无法消除的未来信息泄漏。
- 与已有工作高度或完全重合。
- 只是模型模块堆叠或随机切分刷分。
- 没有可信评测、强基线或最小可判别实验。

## 创新性反证协议

排名前三的方向至少执行三轮、最多十轮搜索：

1. exact formulation/direct match
2. component match
3. same application with different methods
4. same method in adjacent applications
5. concurrent 2024–2026 peer-reviewed work and preprints

任一最近邻达到 High 或 Exact overlap 时，默认判为 not novel；除非贡献类型在数据、评测或可证伪发现上存在实质差异，并能经独立反方审查。

