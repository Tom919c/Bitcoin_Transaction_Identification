# BlackSuit/Royal 零模型可行性 pilot 结果

## 决策

**Target-construction 子测试通过；完整 Pilot No-Go。**

冻结规则得到一个 provisional chain candidate，且它在两个 `c` 前 registry 中均不存在；相邻两日也没有第二个等额输出。但公开 DOJ 法律材料遮盖了 Ransom Address/txid，全文日期又按 `on or about` 理解，因此不能把候选升级为 source-verified legal target。来源独立性只能判为 unknown；按预注册核心规则，unknown 不能当作独立。CP-04+CP-07 不解锁事件扩展、benchmark 或模型训练。

## 链上判别结果

- 冻结日期：`2023-04-04 UTC`。
- 冻结金额：`49.3120227 BTC = 4,931,202,270 sat`。
- 扫描边界：区块 `783816–783977`；前一块时间为 `2023-04-03T23:58:21Z`，后一块时间为 `2023-04-05T00:02:53Z`。
- 扫描规模：162 个区块、421,130 笔交易、1,182,309 个输出。
- 精确命中数：1；Blockchain.com 扫描与 Mempool.space 独立复核在金额、script、地址、block height 和 block hash 上一致。
- 唯一命中是 `v0_p2wpkh` output。因法律材料主动遮盖该字段且尚无直接一手确认，tracked artifact 不公开完整 txid/address。
- 主结果文件 SHA-256：`7c33267b0a5e5aba03e61d46f230a333fb1845bafa5de1a427841129dbcbca37`。

探索性敏感性检查不修改主规则：

| UTC 日期 | 区块 | 交易 | 输出 | 等额命中 | 结果 SHA-256 |
|---|---:|---:|---:|---:|---|
| 2023-04-03 | 131 | 332,870 | 959,432 | 0 | `e0830fca3731d8e731d321771a22ac9e8898ec0699dc5c6451c4db2e41164c39` |
| 2023-04-04 | 162 | 421,130 | 1,182,309 | 1 | `7c33267b0a5e5aba03e61d46f230a333fb1845bafa5de1a427841129dbcbca37` |
| 2023-04-05 | 139 | 346,885 | 1,013,087 | 0 | `1e2b6d6918c8c230723d3be133e8b763fb537951eb012903c39b33f7720cf95e` |
| 合计 | 432 | 1,100,885 | 3,154,828 | 1 | — |

三日唯一性增强了金额/日期链接，但不能替代法律材料对 txid/address 的直接确认。

## `c` 前 registry 审计

`c = 2024-10-27`。

1. Ransomwhere v1.1.0：Zenodo record `13999026`；官方 MD5 `8a7bff74ab0dea4186232bc131c5d40f`，下载 SHA-256 `5c939f3f0d390813f78e649cdd5cd50dcac6ac286e8c9ba52206b273f761082d`。快照含 11,178 个地址记录、134 个 family 值和 21,790 条交易记录；provisional candidate 的地址和 txid 均出现 0 次。
2. Showing the Receipts：`c` 前最后一个 commit `1e7e9d800a7f15f45de136a496b09565c05b9171`（`2024-09-05T09:28:28-07:00`）；`addresses.csv` blob `93536dd7987414500c888bfb102b2b835a9ee242`，共 1,013 行；candidate 出现 0 次。

两份 registry 可能共享上游，不能把两次 absence 当作两个独立 family。结论仅为“候选不在这两个冻结 registry 中”，不是“此前无人知道”。

## 未来法律材料与首见区间

DOJ seizure-warrant affidavit（case `24-sz-27`）第 16–18 页记录：New Jersey Victim 1 在 `on or about April 4, 2023` 向 Royal 支付精确的 `49.3120227 BTC`；CS-1 协助付款并向 HSI 提供 Royal ransom note。公开 PDF 将 Ransom Address 遮盖。

- 最早可能公开时间：`2025-07-29`，即 PDF 页眉 filing date；文件仍带 sealed 标记，不能证明当天已可访问。
- 可验证公开上界：`2025-08-11`，DOJ 新闻稿宣布 unsealing、再次给出日期和金额并链接法律材料。
- 当前首见区间：`[2025-07-29, 2025-08-11]`；缺 docket/unsealing order，不能进一步收窄。
- affidavit SHA-256：`f92787a1bd408add9b1eec9d440cc5b75e1cdeb24ed48061cb2162438218739d`。
- DOJ 新闻稿 HTML SHA-256：`c972e6a00a96e7dc1df0f651b39d52a9e5c3b2edb06e9d8e38cb5abf9083d505`。

## 来源 DAG 与独立性

```text
public-registry family
  ├─ Showing the Receipts snapshot ─┐
  └─ Ransomwhere v1.1.0 ────────────┴─ candidate absent at c

law-enforcement family
  CS-1 + victim payment + ransom note
      └─ HSI / IRS-CI + commercial blockchain analysis
          └─ sealed warrant affidavit
              └─ DOJ unsealing announcement
                  └─ redacted exact date/value ─ inferred chain candidate
```

DOJ 新闻稿与 affidavit 是同一 family。CS-1 身份及商业工具上游不可审计，无法排除其与公开 registry 共享 root artifact。因此状态是 `independence unknown`，核心分析按不独立处理。

## Gate 审计

| 条件 | 结果 | 证据/限制 |
|---|---|---|
| 精确唯一链上 candidate | 通过 | 主日唯一；±1 日合计 3,154,828 个输出仍唯一 |
| `c` 前 registry 未知 | 通过 | 两个冻结 registry 均为 0；只限 registry 范围 |
| `t1` 法律材料直接定位 | **失败** | txid/address 被遮盖，日期声明为近似；当前链接仍是推断 |
| 来源独立 | **unknown → 失败** | CS-1 与商业工具上游不可审计 |
| 可重放 | 条件通过 | 固定脚本、block range、精确 satoshi 规则与 block manifest 已有；动态 API 不是永久镜像 |
| 永久 artifact | **失败** | 原始法律/registry 输入只有本地缓存和哈希，尚无长期证据镜像 |
| 伦理 | 条件通过 | 不公开完整 candidate，不称 Royal-confirmed address，不做 wallet/entity 扩张 |

## 独立反方意见与最终裁决

最强 reviewer reject reason 是：研究把“精确金额在研究者窗口内唯一”升级为“法律证据确认该地址”，但 affidavit 明确把日期视为近似并遮盖地址。这是 construct-validity 与伦理问题，不是模型或置信区间能修复。

Research Director 接受该反证。定向检索没有找到公开的一手 txid、未遮盖 Ransom Address 或可核验的独立 root evidence。三日唯一性只保留为负结果/方法学证据，不用于恢复该方向。

## 下一步

关闭 CP-04+CP-07，返回 Gate 2 重新比较研究问题。只有以后获得直接公开 txid/address、可核验来源 DAG 与长期证据镜像，才允许重审本事件；继续禁止模型训练。

## 官方来源

- DOJ warrant affidavit: <https://www.justice.gov/usao-dc/media/1410771/dl?inline=>
- DOJ unsealing announcement: <https://www.justice.gov/opa/pr/justice-department-announces-coordinated-disruption-actions-against-blacksuit-royal>
- Ransomwhere v1.1.0: <https://doi.org/10.5281/zenodo.13999026>
- Showing the Receipts: <https://github.com/cablej/showing-the-receipts>
