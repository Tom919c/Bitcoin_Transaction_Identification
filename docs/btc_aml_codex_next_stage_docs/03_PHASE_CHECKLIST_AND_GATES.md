# Phase Checklist 与路线晋级门控

## 总览

| Phase | 名称 | 目的 | 是否允许跳过 |
|---|---|---|---|
| 0 | Freeze & Manifest | 冻结当前结果和代码状态 | 不允许 |
| 1 | Temporal Edge Heterophily Diagnostics | 量化 temporal 失败机制 | 不允许 |
| 2 | Route Validation Experiments | 判断主线是否能走 Temporal OOD | 不允许 |
| 3 | Conservative Sensitive Ranking | 严谨化风控排序指标 | 不允许 |
| 4 | Node/Subgraph Boundary Analysis | 判断 MIXER 等难类是否需要子图推理 | 可延后，不建议跳过 |
| 5 | Paper Artifact Generation | 同步生成论文材料 | 不允许 |

---

## Phase 0 Checklist

```text
[ ] python -m pytest -q 通过
[ ] 三套协议数据存在
[ ] 当前 run 汇总表生成
[ ] current_result_manifest.md 写入
[ ] EXPERIMENT_STATUS.md 更新
[ ] DECISION_LOG.md 更新
[ ] 标签逻辑检查完成：-1 ignored, 0~10 supervised
```

停止条件：

```text
如果 pytest 不通过，停止。
如果数据协议缺失，停止。
如果发现 label 0 被忽略，停止。
```

---

## Phase 1 Checklist

```text
[ ] analyze_temporal_edge_heterophily.py 可运行
[ ] same_label_ratio_in/out 输出
[ ] unlabeled_neighbor_ratio_in/out 输出
[ ] class directional compatibility matrix 输出
[ ] temporal feature drift 输出
[ ] degree exposure 输出
[ ] MIXER / EXCHANGE / GAMBLING 重点分析输出
[ ] tests/test_temporal_heterophily.py 通过
[ ] temporal_edge_heterophily_report.md 生成
```

晋级条件：

```text
至少识别出 3 个可验证机制：
1. 时间分布漂移
2. 方向邻居兼容性变化
3. 未标注邻居稀释
4. 高异配
5. supernode exposure
6. edge time / amount drift
```

---

## Phase 2 Checklist

```text
[ ] temporal_balanced 3 seeds 结果生成
[ ] EGS baseline 复现或读取
[ ] no_temporal ablation 完成
[ ] no_direction ablation 完成
[ ] no_edge_attr ablation 完成
[ ] 至少 2 个 OOD 原型完成
[ ] route_gate_decision.md 生成
```

Temporal OOD 方法晋级阈值：

```text
[ ] temporal Macro-F1 相对 EGS +0.03
[ ] Minority-F1 或 conservative_sensitive_AUPRC +0.03
[ ] 至少一个难类 recall 明显提升
[ ] class_balanced_khop 不灾难性下降
[ ] 3 seeds 结果方向一致
```

如果未满足：

```text
[ ] 记录 OOD 方法未晋级
[ ] 论文主线转向 Benchmark + Mechanism Analysis
[ ] 方法作为探索性结果
```

---

## Phase 3 Checklist

```text
[ ] conservative_sensitive 定义为 PONZI/RANSOMWARE/MIXER
[ ] extended_sensitive 定义不包含 EXCHANGE/INDIVIDUAL
[ ] AUPRC 输出
[ ] Recall@1/5/10 输出
[ ] Precision@1/5/10 输出
[ ] sensitive_ranking_report.md 生成
```

晋级判断：

```text
如果 conservative ranking 仍显著优于随机排序，则可以强化“风控应用价值”。
如果 conservative ranking 明显下降，则必须把结论写谨慎：当前模型主要擅长 extended sensitive，不充分解决高敏感类发现。
```

---

## Phase 4 Checklist

```text
[ ] confusion_pair_flow_stats.csv 生成
[ ] MIXER->EXCHANGE 案例分析生成
[ ] GAMBLING->EXCHANGE 案例分析生成
[ ] 至少 3 个正确案例和 3 个失败案例
[ ] 判断是否进入 subgraph route
```

Subgraph route 晋级阈值：

```text
[ ] 局部流特征能显著区分 MIXER 与 EXCHANGE
[ ] 关键混淆对明显减少
[ ] 不依赖人工挑选案例
```

如果未满足：

```text
[ ] 子图路线暂作 future work
```

---

## Phase 5 Checklist

```text
[ ] paper/tables 下所有主表生成
[ ] paper/figures 下关键图生成
[ ] paper/draft 下章节草稿生成
[ ] README 或 OPERATION_RUNBOOK 更新
[ ] DECISION_LOG 写入最终路线选择
```

---

## 最终路线选择规则

### 选择 Temporal OOD Method 作为主线

条件：

```text
Phase 2 晋级阈值满足。
Phase 1 诊断能解释提升机制。
Phase 3 ranking 不明显退化。
```

### 选择 Benchmark + Mechanism Analysis 作为主线

条件：

```text
Phase 2 未稳定提升，但 Phase 1 诊断强、协议和评估闭环完整。
```

### 选择 Hybrid 主线

条件：

```text
Phase 1 诊断强；
Phase 2 有中等提升但不够压倒性；
Benchmark 贡献和 OOD 原型都可讲。
```

推荐默认：

```text
Hybrid = Benchmark foundation + temporal OOD robust direction-aware method
```

但必须由结果支持。
