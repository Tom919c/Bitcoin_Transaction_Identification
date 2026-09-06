# As-of 实体图重建：数据需求说明（冲刺一只记录，不实施）

日期：2026-09-06。状态：设计说明（deferred，按 packet btc-expcampaign-20260906-01 第 9 项）。
背景：2026-09-04 审计确认官方流水线 `populate_alias.py` 用 Union-Find 产出**最终** alias，不记录每次 union 的区块高度与规则来源；本地 252M 库无地址表与 union 历史，无法逆推 as-of 分区。

## 未来实施时必须记录的字段（union provenance logger）

每次地址合并事件追加一行：

```text
(address_a, address_b,
 block_height,
 intra_block_order,
 heuristic_type,
 heuristic_version,
 evidence_metadata)
```

## as-of 重建必须满足的协议要求

1. 任意 cutoff t 只重放 `t_j <= t` 的 union 得到当时分区 C_t = DSU({union_j : t_j <= t})；
2. 用 C_t 重新映射**过去**交易构造实体边与节点属性，而不是把 final cluster ID 套回历史；
3. 记录每个节点的首次可见时间（node observation cutoff）；
4. 记录 train/val/test cutoff 与构图截止的一致性；
5. 统计被 future cutoff 删除的边数；
6. 统计 clustering 回填所使用的时间范围（跨时合并率、分量合并前后规模变化）；
7. 检查 test-era transaction 是否参与 train node representation（构成 B−C 泄漏差）。

## 四条件因子设计（与 Result 一致，供后续冲刺/论文使用）

| 条件 | Entity identity | 边/特征截止 | 含义 |
|---|---|---|---|
| A | Final cluster | 全期 | 传统静态上界（非部署协议） |
| B | Final cluster | 截止 t | 仍存在 identity 未来泄漏 |
| C | As-of cluster | 截止 t | 严格历史可见构图 |
| D | As-of cluster + cluster-confidence | 截止 t | 本项目新方法 |

关键比较：B−C 的 F1/ECE/AUPRC 差与 TopKOverlap(B,C)（同预算下审查优先级变化）。

## 冲刺一不做的原因

- 无原始链时间数据接口与 as-of 构图代码；
- 混入数据工程变化会破坏两周内"模型变化"的最小判别；
- 当前冲刺一结论只能表述为"当前 temporal protocol 下更鲁棒"，不得表述为真实部署 as-of 性能。
