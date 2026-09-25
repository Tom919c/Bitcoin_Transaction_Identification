# S0 定案记录（Gate 3A v1.3）

定案日期：2026-09-25。执行方式：全部在实验室服务器 `A100_chenquan` 上完成。
执行人：WorkBuddy（受 quan 委托）。

## 1. 结论

**`outcome: Go`，`status: finalized`，`final_integrity: passed`。**

S0 结构评估通过冻结决策规则，允许开始起草**另行冻结的 S1 协议**。本次定案**不**授权任何模型、训练、
标签读取或对外发布。

| 字段 | 值 |
| --- | --- |
| `protocol_version` | `Gate3A-v1.3-20260912` |
| `schema_version` | `aws-btc-s0-final-decision-v1` |
| `outcome` | **Go** |
| `status` | finalized |
| `final_integrity` | passed |
| `s1_protocol_drafting_allowed` | **true** |
| `models_authorized` | false |
| `labels_read` | false |
| `effect_metrics_read` | true |
| `effect_metrics_read`（finalizer 自记） | true |
| `runner_sha256` | `35b07642310ca9fe95031c1f2f4aa32fbc403011845666285adff223261b752c` |
| `final.json` sha256 | `8a6558087ba5ab8ed5fd71e1615d2a9316bc3705d00fe6c0f8949d4b6743efcd` |

## 2. 两次评估的哈希一致性

Gate 3A v1.3 要求两次连续独立评估在文件哈希、输入绑定、每个 cell 指标、候选决定与边界字段上全部一致。

| 项 | 值 |
| --- | --- |
| run01 `evaluation.json` sha256 | `179327f6944f973f05132c4630d082c83435248302f6e1d9a5487280d83f01ac` |
| run02 `evaluation.json` sha256 | `179327f6944f973f05132c4630d082c83435248302f6e1d9a5487280d83f01ac` |
| 字节比对 `cmp` | 逐字节完全相同 |
| 文件大小 | 两边均 31,708,638 字节 |
| cell 数 | 27 / 27，key 集合相同 |
| 差异 cell | 0 |
| 比对脚本判定 | **`AGREE`** |

比对脚本 `compare_s0_evaluations.py` 逐字段核对以下 13 个顶层字段，全部 `identical`：
`protocol_version`、`extractor_summary_sha256`、`source_manifest_sha256`、`union_log_sha256`、`seed`、
`runner_sha256`、`environment`、`inputs`、`effect_metrics_read`、`labels_read`、`models_authorized`、
`integrity`、`decision`。

本机与服务器**分别独立**运行比对脚本，两边结论一致（服务器产出
`/workspace/chenquan/s0_evaluation_comparison.json`，本机产出 `D:\tmp\asofx\s0_evaluation_comparison.json`）。

## 3. 为什么两次运行必须在同一台机器

`evaluation.json` 内嵌 `environment = {"python": "3.12.14", "sqlite": "3.53.1"}`，且
`secondary.variation_of_information` 使用 `math.log`。跨解释器版本与跨 libm 实现不保证逐位一致，
因此跨主机不可能通过 finalizer 的哈希一致性检查。两次权威运行都在服务器上串行完成。

作为对照：本机 Python 3.12.3 / sqlite 3.49.1 与服务器 3.12.14 / 3.53.1 不同，本机 run01 的
`evaluation.json` sha256 是 `ee893a0e25e3d40e415de5c3d8c7261514c4d8060a427cadb6b57787902fa63e`，
与服务器的 `179327f6…` 不同 —— 这正是必须同机的原因，已在 registry 中记为 `superseded`。

## 4. 溯源绑定（finalizer 校验通过）

`bindings` 四项全部匹配冻结值：

| 绑定 | 值 | 状态 |
| --- | --- | --- |
| `extraction_summary_sha256` | `470a68dede7d9ad3cf6595f9dd961d929b919db6116d0b0bf28ad7e5056a0ca3` | 匹配 |
| `source_manifest_sha256` | `e32ad2f33ecbc184eb04159f0adbb22dd2a4a1a47f1e280cbbca699432d67f3d` | 匹配 |
| `state_db_sha256` | `1f1bf354519af4dcc1e0cc3ae3da0c670d057bd5897db6bf806e3442bc078205` | 匹配 |
| `union_log_sha256` | `1235ca54b23fcaf2fd2441dd5449eafe7c2962788b36f380e106ec4de73a3584` | 匹配 |

finalizer 的五个输入文件哈希：

| 输入 | sha256 |
| --- | --- |
| `provenance.json` | `ff35f121ae3da16ccf2834f7f2d13b6c6aa1220cabf28ad58102e9a9e3aae4f0` |
| `evaluation`（run01） | `179327f6944f973f05132c4630d082c83435248302f6e1d9a5487280d83f01ac` |
| `evaluation2`（run02） | `179327f6944f973f05132c4630d082c83435248302f6e1d9a5487280d83f01ac` |
| `correction.json` | `de19a57d92cfda0c9b043802c9a996867cc150167f31443aa65fa83a0a3a42e7` |
| `provenance_audit_v1_3.sqlite`（checkpoint） | `a6803cd5a6ade4ce25b6c8283d6de6ccb8475fa00db6db4daee231f832372bd9` |

## 5. integrity 采样

| 项 | 值 |
| --- | --- |
| `sample_target` | 1000 |
| `sampled_unique_events` | 1000 |
| `minimum_required` | 995 |
| `fully_recovered` | 1000 |
| `threshold_passed` | **true** |
| 八个 cell 的恢复数 | 各 125（`t181440|F_pub`、`t181440|F_wide`、`t199584|F_pub`、`t199584|F_wide`、`t215712|F_pub`、`t215712|F_wide`、`t225792|F_pub`、`t225792|F_wide`） |
| `correction_scope` | `assigned_cells_only` |

## 6. 27 个 cell 的候选指标（bootstrap 长度 144，10000 次重采样）

p_merge 与 p_rewrite 的 95% 置信区间：

| window | profile | horizon | p_merge (L, U) | p_rewrite (L, U) |
| --- | --- | --- | --- | --- |
| t181440 | F_none | 13140 | (0.31632, 0.44382) | (0.12301, 0.29913) |
| t181440 | F_none | 52560 | (0.34104, 0.47014) | (0.14096, 0.32078) |
| t181440 | F_none | 105120 | (0.34645, 0.47737) | (0.15042, 0.32994) |
| t181440 | F_pub | 13140 | (0.31753, 0.44237) | (0.12480, 0.29731) |
| t181440 | F_pub | 52560 | (0.34135, 0.47008) | (0.14086, 0.31989) |
| t181440 | F_pub | 105120 | (0.34693, 0.47481) | (0.15004, 0.32764) |
| t181440 | F_wide | 13140 | (0.31655, 0.44142) | (0.12119, 0.29412) |
| t181440 | F_wide | 52560 | (0.34035, 0.46892) | (0.13859, 0.31637) |
| t181440 | F_wide | 105120 | (0.34486, 0.47636) | (0.14601, 0.32657) |
| t199584 | F_none | 13140 | (0.32743, 0.35119) | (0.16598, 0.22411) |
| t199584 | F_none | 52560 | (0.35693, 0.38151) | (0.19274, 0.25162) |
| t199584 | F_pub | 13140 | (0.32676, 0.35000) | (0.16340, 0.21986) |
| t199584 | F_pub | 52560 | (0.35518, 0.37903) | (0.19040, 0.24939) |
| t199584 | F_wide | 13140 | (0.32578, 0.34918) | (0.16291, 0.22062) |
| t199584 | F_wide | 52560 | (0.35411, 0.37848) | (0.19002, 0.24839) |
| t215712 | F_none | 13140 | (0.31693, 0.35458) | (0.17725, 0.23544) |
| t215712 | F_none | 52560 | (0.33110, 0.37568) | (0.19254, 0.25217) |
| t215712 | F_pub | 13140 | (0.31425, 0.35360) | (0.17777, 0.23569) |
| t215712 | F_pub | 52560 | (0.32741, 0.37481) | (0.19303, 0.25214) |
| t215712 | F_wide | 13140 | (0.31319, 0.35272) | (0.17860, 0.23628) |
| t215712 | F_wide | 52560 | (0.32760, 0.37387) | (0.19306, 0.25256) |
| t225792 | F_none | 13140 | (0.29340, 0.34090) | (0.10106, 0.14320) |
| t225792 | F_none | 52560 | (0.32040, 0.36541) | (0.12015, 0.16013) |
| t225792 | F_pub | 13140 | (0.29281, 0.34022) | (0.10070, 0.14253) |
| t225792 | F_pub | 52560 | (0.32022, 0.36345) | (0.11979, 0.15941) |
| t225792 | F_wide | 13140 | (0.29163, 0.33860) | (0.10403, 0.14597) |
| t225792 | F_wide | 52560 | (0.31914, 0.36213) | (0.12352, 0.16247) |

注：`t181440` 的三个窗口有 105120 三个 horizon，其余窗口只有 13140 与 52560，合计 9 + 6 + 6 + 6 = 27。

## 7. 运行耗时实测

| 运行 | 开始（UTC） | 完成（UTC） | 耗时 |
| --- | --- | --- | --- |
| 服务器 run01 | 2026-09-23T23:46:53 | 2026-09-24T01:02:36 | 1h15m43s |
| 服务器 run02（首次尝试，失败） | 2026-09-24T01:02:37 | 2026-09-25T01:33（人工停止） | 16h44m16s，仅约 2732s CPU |
| 服务器 run02（重跑，成功） | 2026-09-24T18:01:13 | 2026-09-25T01:19:45 | 7h18m32s |
| finalizer | 2026-09-25T04:42:45 | 2026-09-25T04:42:45 | 瞬时 |

首次 run02 失败与重跑的经过见 `服务器run02重跑记录-20260925.md`。

## 8. limitations（finalizer 自记，原文）

- S0 finalization does not authorize models or training.
- A Go only permits drafting a separately frozen S1 protocol.
- The experiment registry is not modified automatically.
- Original provenance assigned_cells is defective; the bound correction repairs only that summary field.
- The correction does not re-scan source transactions or independently recompute candidate selection.

第 3 条已由本次操作补足：registry 三行已更新（见 §9）。第 4、5 条为遗留限制，不因本次定案而消失。

## 9. 产物落位

服务器（`/workspace/chenquan/asof-entity-graph/`）：

| 产物 | 路径 | sha256 |
| --- | --- | --- |
| run01 评估 | `experiments/diagnostics/aws_btc_s0_structure_eval_v1_3_20260924_server_run01/evaluation.json` | `179327f6…` |
| run02 评估 | `experiments/diagnostics/aws_btc_s0_structure_eval_v1_3_20260924_server_run02_retry/evaluation.json` | `179327f6…` |
| run02 失败现场 | `experiments/diagnostics/aws_btc_s0_structure_eval_v1_3_20260924_server_run02/`（空 `run.log`） | — |
| 定案 | `experiments/diagnostics/aws_btc_s0_final_v1_3_20260925/final.json` | `8a655808…` |
| 比对报告 | `/workspace/chenquan/s0_evaluation_comparison.json` | — |

本机（`D:\Code\VSCode\Bitcoin_Transaction_Identification_asof\`）：上述最终产物三件已回迁存档，
哈希与服务器逐一相同（已用 `sha256sum` 与 `cmp` 复核）。

registry 更新（`experiments/experiment_registry.csv`，12 行）：

| run_id | 变更 |
| --- | --- |
| `aws-btc-s0-structure-eval-v1.3-20260924-server-run01` | running → **completed**，补 `completed_at_utc=2026-09-24T01:02:36+00:00` 与评估哈希 |
| `aws-btc-s0-structure-eval-v1.3-20260924-server-run02` | planned → **completed**，artifact 指向 `…_server_run02_retry`，notes 记录首次失败与重跑 |
| `aws-btc-s0-final-decision-v1.3-20260921` | planned → **completed**，artifact 指向 `aws_btc_s0_final_v1_3_20260925`，notes 记录 `final_sha256` 与 Go |

服务器仓库版本：`35af3ac9c2c480a52d2e5bc41561597f09e69c49`（分支 `asof-entity-graph-pilot`）。

## 10. 下一步

1. **S1 协议起草**（已获授权）。S1 必须**另行冻结**，不能沿用 S0 的阈值或决策规则。
2. **Research Passport 刷新**：算力路线改记实验室 A100、补本次数据迁移与校验、更新已过期的状态描述。
3. **决策日志更新**：记入 S0 Go 及本次定案的证据链。
4. 仍**未**授权：读取标签、训练或推理模型、打开正式测试集、对外发布、在 A100 上运行新模型。
