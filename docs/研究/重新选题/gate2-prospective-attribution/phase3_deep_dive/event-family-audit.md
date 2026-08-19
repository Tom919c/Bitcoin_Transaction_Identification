# Gate 2 Phase 3：事件家族可行性审计

## 判定标准

一个事件只有同时满足以下条件才可进入正式 benchmark：`c` 前公开且可存档的 seed；可按 `c` 冻结的候选全集和输入；`c` 后首次公开的 address/tx/case 级归因；与 seed 无共同 root evidence 的独立来源；可验证 first-public 时间区间；公开链上对象可唯一映射；数据许可和伦理边界可接受。事件级“某组织实施攻击”不能替代地址级 outcome。

## 审计结果（14 个事件/家族）

| 事件/家族 | `c` 前 seed | `c` 后一手证据 | 主要断点 | 判定 |
|---|---|---|---|---|
| BlackSuit/Royal | 2024-09-05 Showing the Receipts 或 2024-10-27 Ransomwhere 快照 | 2025-08-11 DOJ 公告给出 2023-04-04、49.3120227 BTC 与扣押事实 | Ransomwhere 条目缺逐条来源；DOJ 公告未直接给唯一钱包；需由金额/日期匹配且排除 t0 已知 | **Conditional Go：零模型唯一匹配 pilot** |
| ALPHV/BlackCat | Ransomwhere 有条目 | 2025-12-30 DOJ 说明 Bitcoin 勒索 | 无钱包/txid/精确金额日期组合；seed provenance 不足 | No-Go |
| Phobos/8Base | Ransomwhere 有条目 | 2025-02-10 DOJ 说明 affiliates 使用独立钱包 | 不公开具体地址/交易；来源独立性不可审计 | No-Go |
| Robbinhood | 未找到合格历史公开地址 | 2025-05-27 DOJ 与 indictment | 无 `c` 前 seed | No-Go |
| Qakbot 相关活动 | 未找到独立历史地址 seed | DOJ 2023/2025 扣押与没收 | 先后 DOJ 披露属于同一调查生态，不能制造独立验证 | No-Go |
| SamSam | 2018 ransomware 数据库含 seed/source URL | 2018-11-28 DOJ 与 indictment | 数据仓库无许可证；来源多为第三方；文书不定位对应 seed 钱包/tx | No-Go |
| Upbit 2019 | 2019-11-27 Upbit 公告公开 342k ETH seed | 2020-03-02 DOJ civil complaint 把 Exchange 3 资金经 VASP 转成 18 个 BTC clusters/约 200 地址 | ETH→VASP→BTC 隐边不可由公共链观察；正例仅子集；独立性仍可能共享调查输入 | **Conditional Go：仅跨链 provenance 事件卡** |
| Harmony Horizon | 2022-06-24 Harmony 报告公开 ETH seed | 2023-01-23/02-06 FBI 归因并列剩余 BTC wallets | Railgun/VASP/跨链路径不可见；FBI 不是终局裁判 | **Conditional Go：多链补充案例** |
| Twitter 2020 scam | 2020-07-15 被劫账号公开 BTC 收款地址 | 2020-07-30/31 DOJ complaint/affidavit 给出地址、12.86 BTC、426 笔转入及线下证据 | 目标规模小、窗口短；后续地址不全；需保存原始平台快照 | **Conditional Go：微型 sanity case** |
| DMM Bitcoin | 事件与金额公开 | FBI/DC3/NPA 后续 actor attribution | 未找到 `c` 前 address seed 或 `c` 后地址清单 | No-Go |
| Bitfinex 2016 | 事件公开，未见当时钱包映射 | 2022-02-07 DOJ affidavit 公开后续钱包 | 地址真值首次在 `c` 后出现，不能倒灌为 seed | No-Go |
| Silk Road / Individual X | 盗窃事件已知 | 2020-11-05 DOJ complaint 首次公开 54 笔交易与 69,370 BTC 扣押 | wallet-level seed 也是 `c` 后才公开 | No-Go |
| Colonial Pipeline / DarkSide | 公开事件，无合格地址 seed | 2021-06-07 FBI 披露扣押 63.7 BTC | 不存在公开 `c` 前 seed → 独立 `c` 后地址 outcome 的顺序 | No-Go |
| KuCoin 2020 | KuCoin 公告公开多枚 BTC 地址 | 未找到独立法院/执法材料归因这些具体地址 | 公司自己的后续更新不独立 | No-Go |

## 关键一手来源

- BlackSuit/Royal：[Showing the Receipts](https://github.com/cablej/showing-the-receipts)、[Ransomwhere v1.1.0](https://doi.org/10.5281/zenodo.13999026)、[DOJ 2025-08-11](https://www.justice.gov/opa/pr/justice-department-announces-coordinated-disruption-actions-against-blacksuit-royal)。
- Upbit：[Upbit 2019-11-27](https://upbit.com/service_center/notice?id=1085)、[DOJ complaint](https://www.justice.gov/opa/press-release/file/1253491/dl)。
- Harmony：[Harmony incident report](https://medium.com/harmony-one/harmonys-horizon-bridge-hack-1e8d283b6d66)、[FBI attribution](https://www.fbi.gov/news/press-releases/fbi-confirms-lazarus-group-cyber-actors-responsible-for-harmonys-horizon-bridge-currency-theft)。
- Twitter：[DOJ complaint](https://www.justice.gov/opa/press-release/file/1300246/dl?inline=)、[affidavit](https://www.justice.gov/opa/press-release/file/1300261/dl?inline=)。
- SamSam：[ransomware dataset](https://github.com/behas/ransomware-dataset)、[DOJ/indictment](https://www.justice.gov/d9/press-releases/attachments/2018/11/28/savandi_and_mansouri_indictment_11.26.18_2_0.pdf)。

## Phase 3 结论

14 个案例没有一个满足完整 Go；只有 BlackSuit/Royal、Upbit、Harmony、Twitter 值得进入 Phase 4 的零模型 artifact/pilot 核验。它们仍不能共同组成合格 benchmark：BlackSuit 缺唯一公开钱包映射，Upbit/Harmony 有不可观测跨链/VASP 隐边，Twitter 规模太小。

因此禁止启动模型训练。Phase 4 只验证三个问题：

1. BlackSuit 的金额/日期条件能否在原始 Bitcoin 链上唯一定位，且目标未进入 `c` 前标签集；
2. Upbit/Harmony 的法院或执法附件能否形成版本化 address-level outcome registry，同时明确把隐边作为不可识别部分；
3. Twitter 的原始社交平台内容和后续法律文书能否稳定归档并通过 source-family 去依赖。

任一 pilot 可失败；若不能得到至少三个具互补证据链且可重放的事件，当前主方向整体 No-Go，而不是降低验收标准。
