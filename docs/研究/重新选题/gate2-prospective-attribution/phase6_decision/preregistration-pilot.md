# BlackSuit/Royal 零模型可行性 pilot 预注册草案

## 目的与边界

目的仅是判断能否从冻结的 `c` 前标签 registry 与 `c` 后一手法律证据，构造一个唯一、独立、可重放的 Bitcoin address/tx outcome。该 pilot 不训练模型、不评价犯罪预测、不估计真实 precision。

## 冻结时间与输入

- `c = 2024-10-27`：Ransomwhere v1.1.0 Zenodo snapshot 的发布日期/版本锚点。
- `t1 = 2025-08-11`：DOJ BlackSuit/Royal disruption 公告日期。
- `c` 前 registry：Ransomwhere v1.1.0 `ransomwhere.json`；Showing the Receipts 在 `c` 前的 Git commit 快照（若无精确 commit，则该源不参与未知性判定）。
- 链上输入：Bitcoin genesis 至 `c` 的原始 blocks/确定性索引；输出必须记录 block hash、height、txid、vout、value、script type 和地址编码。
- 未来证据：DOJ 公告以及能追溯到的 complaint、forfeiture、seizure warrant 或 court filing 原文。

模型或排序器不得使用 `t1` 信息。`t1` 的金额/日期只用于离线构造 outcome，类似测试标签，不进入任何未来正式模型特征。

## 预注册 target 规则

法律材料当前给出候选事实：Royal 受害者在 2023-04-04 支付 `49.3120227 BTC`。

1. 在 UTC 2023-04-04 对所有 Bitcoin transaction outputs 做**精确 satoshi 值**匹配。
2. 不使用 change heuristic、地址聚类、交易图邻近性或事后人工偏好消歧。
3. 若恰有一个 output 命中，则得到 provisional target `(txid,vout,address)`。
4. 若命中数为 0 或大于 1，pilot 立即失败；只有未来法律原文直接给出 txid/wallet，才允许以该一手字段重启一次预注册，而不是临时扩大金额/日期容差。
5. 检查 provisional target 是否已存在于所有 `c` 前 registry；若已存在，则它不是 future-unknown outcome，pilot 失败。

## 证据独立性规则

建立 `document -> claim -> address/tx -> upstream evidence` DAG。至少需要：

- 一个 `c` 前 seed/registry family；
- 一个 `t1` 后法律/执法 family；
- 两者没有可见的共同 root artifact，或明确标记“独立性不可判”。

组织不同只作为弱证据。若 DOJ 材料的地址只引用同一学术/众包列表，不能算独立；若公开材料无法判断依赖关系，核心分析按不独立处理，敏感性分析才可列为 unknown。

## 输出 artifact

- 输入文件和页面的 SHA-256、版本/commit/DOI。
- `first_public_lower`、`first_archive_upper` 与区间状态。
- 全部金额匹配候选，不只保留最终命中。
- tx/block 原始定位与可重放查询。
- source-family DAG、人工审计理由、失败日志。
- 一个不含新增个人身份推断的 case card。

## Go/No-Go

**Pilot Go**：精确唯一链上 target；`c` 前 registry 未知；`t1` 一手法律材料可独立定位；来源与链上查询可完全重放；许可允许保存必要证据元数据。

**Pilot No-Go**：任一条件不满足，包括多重/零匹配、目标在 `c` 前已知、法律文件不定位、来源同根/不可判、无法永久存档、或只能依赖 heuristic clustering。

Pilot Go 只解锁“再审计两个事件”，不解锁模型训练。三个合格事件齐备后，才另写正式实验预注册。
