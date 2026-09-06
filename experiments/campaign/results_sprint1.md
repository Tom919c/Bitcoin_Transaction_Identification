# 冲刺一结果汇总（随实验推进更新）

判据来源：`experiments/campaign/sprint1_prereg.yaml`。所有屏显数字为 **val**（80ep 快筛 / 200ep 正式），test 只在 final-test 阶段打开。

## 快筛阶段（seed42，80ep，patience20，epoch-matched 对比）

| 变体 | val Macro-F1 | Δ vs A0 | GAMBLING | EXCHANGE | MARKETPLACE | BRIDGE | MIXER | 状态 |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| A0 = EGS（锚点） | **0.3818** | — | 0.101 | 0.078 | 0.205 | 0.159 | 0.000 | 完成（早停 ~epoch 60；queue.log 的 STEP_FAIL 为退出码日志缺陷，产物完整） |
| A1 = +self 残差 | **0.3958** | **+0.0141** | 0.210 | 0.046 | 0.228 | 0.528 | 0.068 | 完成（01:15）。弱正（低于 +0.020 晋级线）；BRIDGE +0.37、GAMBLING +0.11、MIXER 0→0.07，EXCHANGE −0.032（未触 0.05 守卫）。与"时间漂移下图邻域失真、自身特征作退路"的机制假设一致 |
| A2 = +门控 | **0.3892** | **+0.0074** | 0.095 | 0.039 | 0.257 | 0.444 | 0.131 | 完成（02:24）。弱正但低于 A1：门控未带来宏观增量；MIXER 0→0.131（当前最好）、MARKETPLACE 提升，GAMBLING 回落 |
| A3 = A2+V-REx λ0.1 | 运行中（02:24 起） | | | | | | | |

判据：A1/A2/A3 相对 A0 的 Δval：< −0.01 淘汰；正式晋级需三种子 val 平均 ≥ +0.020（且 watch 类守卫、conservative AUPRC 守卫）。

## 待跑

A2（+门控）→ A3（V-REx λ∈{0.1,0.3,1.0}）→ E0 EGS 三种子（200ep）→ GBDT → Dir-SAGE 三种子。

## 备注

- 历史冻结 temporal 0.2565 属于另一个协议（含时间边特征），只作背景，不与本表数字直接比较。
- 快筛只用于结构淘汰；headline 主张需三种子与最终 test。
