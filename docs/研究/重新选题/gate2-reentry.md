# Gate 2 重新进入记录

## 决策目标

最新状态（2026-08-31）：CP-13 有界第二实现取证未通过，暂停主线晋级；当前没有满足全部硬门的主方向。下文保留各阶段历史判断，最新依据见文末“第二实现证据包结果”。

在不继承旧 EGS/GNN 叙事、也不复活已被反证方向的前提下，重新生成并比较可由现有资产或可合法获得的新数据直接证伪的研究问题。最终仍只输出一个主方向、两个替代方向和一个低风险 fallback；用户确认前不进入协议冻结或模型开发。

## 冻结边界

- 核心领域：Bitcoin/cryptocurrency transaction graph；相邻领域仅用于方法、理论或评测参照。
- 现有资产：约 252M 节点的终态 heuristic-entity graph；`0..10` 是 entity type，`-1` 是未标注上下文。
- 已知缺口：终态资产没有 address/txid/block hash、address-to-entity mapping 或 union lineage。
- 可扩展边界：允许引入可合法获取、可复查许可与时间语义的新公开数据。
- 资源：单机多 GPU 与较强工程投入；先做最小判别实验，不为未晋级方向搭建系统。
- 科学边界：entity type 不等于 illicit activity、fraud 或 AML risk；unknown 不当负类；随机切分不代表未来部署。

## 候选评价准则

所有候选在看到本轮新增文献前先独立生成，再用文献核验。评分采用“问题重要性 × 证据质量 × 可行性”，但以下任一项直接 No-Go：

1. ground truth 不能支持研究主张；
2. 预测时点存在不可消除的未来信息；
3. 与已有论文 High/Exact overlap；
4. 仅换模型模块、组合常规组件或在旧随机切分刷分；
5. 没有强基线、可信评测或最小可判别实验；
6. 理论只是教科书结果改名、装饰性命题或不能导出可测推论。

候选进入前三名前必须明确：RQ、可证伪假设、决策/预测/图单位、标签来源与可得时间、最近邻、真正差异、最小实验、强基线、资源与许可、失败条件、伦理风险和最强 reviewer 拒稿理由。

## 本轮独立生成协议

- 三名互不共享结论的 Research Analyst 分别从现有资产、新公开数据和理论机制生成 pre-literature proposals。
- 生成阶段不读取既有问题卡、不联网、不判断 novelty；结果只作为检索假设，不作为研究发现。
- Research Director 在汇总后先去重、剔除已关闭方向，再为每个新簇设计直接匹配、组件匹配、相同应用、相同方法和同期工作的反证检索。

## 检索链状态

| 日期 | 链路 | 动作 | 状态 |
|---|---|---|---|
| 2026-08-19 | Undermind | 调用 orientation，准备复用既有 workspace 并增量深检 | HTTPS transport error；不据此推断无文献，等待恢复后补检 |
| 2026-08-19 | Undermind | 恢复后以不同措辞并行搜索 Bitcoin completion certificate 与 uncertain-graph robustness，各 20 篇 | 已完成 discovery；命中 uncertain graph、robust influence/centrality、Lightning balance uncertainty 等邻域，未把摘要升级为关键证据 |
| 2026-08-19 | 独立链 | 官方论文/代码/数据页面、GitHub、Web 学术检索与引用追踪 | 已完成第一轮 direct/component/application/concurrent 反证；正文结论只采用全文或官方入口 |

## 已关闭方向的继承规则

BlackSuit/Royal 前瞻归因、普通预算化队列、通用 PU/MNAR 效用界、单纯 MIH 比较、无 lineage 的 shortcut audit、无统一真值的跨链迁移和当前形态的 provenance benchmark 不得仅换名称重新入池。只有出现新的必要数据或实质不同的 estimand/贡献时，才能作为新候选重新审查。

## 盲生成后的候选池（2026-08-19 快照）

分数为 `问题重要性 × 证据质量 × 可行性`，每项 1–5。分数不能覆盖硬 No-Go；`条件保留` 只表示值得继续反证，不表示方向已冻结。

| ID | 候选问题 | 分数 | 当前裁决 | 核心理由 |
|---|---|---:|---|---|
| N1 | 账本兼容 flow completions 下的图任务敏感性证书 | 4×3×4=48 | 条件保留，创新性复核中 | 原始 input-output 归属不可点识别已有大量工作；可能的新切口仅是单点完成对下游 ML/图结论制造的假确定性 |
| N2 | 实体解析不确定性下的有限预算 confirmed-service/case coverage | 4×3×2=24 | 条件保留，数据硬阻塞 | 次模/greedy 和 ER 误差传播均非新；仅 decision-level partial identification/regret 尚可能有空间 |
| N3 | claim-source-onchain-object 冲突证据图与后续独立佐证 | 3×2×2=12 | 观察名单 | 现实意义存在，但来源独立性、版本历史和 outcome 规模尚未证明可构建 |
| N4 | 标签延迟下动态图 blind-window regret 与结构先行信号 | 4×3×2=24 | 暂缓/倾向 No-Go | delayed-feedback 下界高度标准；本项目缺真实标签公开时间，除非找到稳定先行信号与公开数据 |
| N5 | 来源依赖披露下的排序迁移/PU 部分识别 | 4×4×2=32 | No-Go | 与既有 selection/PU 理论和上一轮 CP07 高重合，且缺独立审计样本 |
| N6 | 由 11 类 entity type 推断 unknown-illicit 的不可识别性 | 4×4×5=80 | 主方向 No-Go；边界保留 | 这是必须遵守的主张边界，不是足够的新论文；只能评估 known-type novelty，不能命名为 illicit risk |
| N7 | transportation polytope 的 UTXO 来源区间/精确归因 | 4×5×4=80 | No-Go（NOT_NOVEL，0.90） | Maurer 2017、Boltzmann、Gavenda et al. 2025 已覆盖更强的可行映射、概率和约束枚举；LP 区间是标准结果 |
| N8 | address clone/refinement invariance 的实体级不可能性 | 3×4×2=24 | 独立主问题 No-Go | two-world 不可识别性过于直接；图粗化、复制、ER 不确定性均有成熟邻域；仅可作为 N2 边界 |
| N9 | 事件种子到未来公开归因的前瞻发现 | 4×5×1=20 | No-Go（已关闭） | BlackSuit/Royal Pilot 已证明公开材料不能提供足量、可独立验证的未来地址真值 |
| N10 | entity-type 的时间/来源有效性 benchmark | 3×4×5=60 | 低风险 fallback | 现有资产可做，但贡献必须限定为 entity type 与协议审计；不能包装成 AML，也需证明结果超越数据清理 |
| N11 | 跨链案件足迹检索 | 4×3×1=12 | No-Go | 公开材料中的 VASP/兑换隐边不可观测，案件级隔离后样本与真值不足 |

### N1 问题卡：flow-completion-sensitive graph claims

- **RQ**：给定预测时点可得的 UTXO 账本和一个明确 source set，某个图统计、路径、排序或分类结论是否对所有账本兼容的 input-output completions 都成立？
- **可证伪假设**：比例/Haircut、FIFO 等单点 completion 会在非平凡比例的多入多出交易或局部子图上改变下游排序/标签；identified-set certificate 能识别稳定结论并对不稳定结论 abstain。
- **单位**：观测单位是 outpoint–transaction–outpoint 二部/超图；不确定对象是交易内部 source mass 分配；输出单位是 source-conditioned 统计、路径或候选排序，不是 entity risk。
- **最近邻与差异**：Maurer 2017、Boltzmann、Gavenda et al. 2025 已覆盖 CoinJoin 可行映射和概率；Tironsakkul et al. 2019 已显示 taint 规则结论分歧；EBA 2025 使用 complete bipartite proportional completion。唯一待证差异是**面向下游 ML/图主张的 completion sensitivity certificate、稳定输出和 abstention 协议**。
- **最小实验**：受控/模拟 CoinJoin 的已知隐藏 mapping，加小型真实 Core 子图；比较 proportional、FIFO、TIHO/LIFO、可行集上下界。主要量为 top-k flip、rank interval、coverage–abstention、错误确定率与计算成本；未知项不作负例。
- **强基线**：EBA proportional completion、FIFO/Haircut、Boltzmann link probability、Gavenda mapping enumerator、仅使用原始二部图的无投影基线。
- **理论边界**：transportation-polytope 维数、LP 上下界和阈值可识别判据只能作为标准工具，不能声称新定理。新理论若存在，必须绑定实际下游任务的可计算证书或复杂度界。
- **可行性**：Bitcoin Core 顺序扫描 100 blocks smoke，再决定是否扩到 10,000 blocks；合成真值可行。EBA 全量 1.17 TB/731 GB 非当前 Pilot 前提，且其 v1 排除输入和输出均超过 20 的交易。
- **失败条件**：robust/uncertain graph 文献已有等价证书；单点 completion 很少改变任何决策；证书几乎总 abstain；真实/模拟 mapping 无法合法复现；贡献只剩教科书 LP。
- **最强拒稿理由**：已知 CoinJoin 歧义的重新包装，没有新的算法/理论或任务级实证后果。

### N2 问题卡：partition-uncertain budgeted coverage

- **RQ**：在外部证据约束、按时间可得的多个 address-to-entity partitions 下，选择预算为 `k` 的链上对象时，confirmed service/case coverage 的期望、保守下界和 partition-induced regret 能否被可靠估计与优化？
- **可证伪假设**：单一 heuristic partition 的 top-k 会重复命中同一真实服务或受错误合并影响；显式 partition uncertainty 会改变选择集合或保守 coverage。
- **单位与真值**：选择单位是地址/线索，效用单位是独立证据确认的 service/case 首次覆盖；不得用 11 类 entity type 或 `-1` 代替案件真值。
- **最近邻与差异**：ER uncertainty propagation、resolution-aware aggregate bounds、ICDE 2020 的 ER question-selection submodularity、robust submodular optimization、Müller 2026 MIH 审计均覆盖核心组件。可争取差异仅是 Bitcoin forensic decision-level coverage/regret，不能把 `1-1/e` 当新理论。
- **最小实验**：至少两套有证据依据的时间化 partitions 与一个独立 address-to-service/case 验证子集；比较 address top-k、单一 cluster top-k、scenario/partial-identification 选择，报告 coverage interval 和 decision flip。
- **可行性硬门**：当前 252M 终态实体图没有 address/txid/union lineage，不能直接使用。若无法合法获得独立真值、多 partition/union 谱系和时间元数据，立即停止。
- **最强拒稿理由**：把成熟 ER/robust-submodular 方法搬到 Bitcoin，且不确定 partitions 是人为扰动、调查效用只是代理。

### N3 问题卡：source-dependent evidence claims

- **RQ**：在保留引用关系和共同上游证据的 claim–source–onchain-object 图上，能否预测一个已公开 claim 会被后续独立来源佐证、修订或撤回，并比简单来源等级/独立 root 数规则更可靠？
- **可证伪假设**：域名数量和重复转载会系统性夸大证据强度；去除共同 root 后，复杂图模型只有在版本外测试仍超过规则基线才成立。
- **单位与标签**：行动单位是待复核 claim；标签是后续独立佐证/修订，不是地址非法性。来源独立性按共同 root-evidence component 判定。
- **最小实验**：冻结历史页面版本，按 claim family 和时间切分；规则、文本/元数据、证据图传播三类基线；报告 source-family-held-out 的 calibration、PR@k 和 abstention。
- **失败条件**：无法恢复版本时间或来源 DAG；后续佐证不是可辩护 outcome；数据规模不足；简单规则持平或更好。
- **最强拒稿理由**：网页整理数据集，和 Bitcoin 图研究关系弱，且“后续报道”不等于真实性。

## 第一轮关键反证结论

1. **原始 N7 已关闭**：UTXO 内部 input-output mapping 不唯一并非新发现；更强的离散 CoinJoin mapping、约束枚举和 link probability 已存在。
2. **EBA 不是简单的“错误数据”靶子**：公开实现保留 `Script -> Transaction -> Script` 账本边；其 transaction-to-transaction transfer 由被消费 UTXO 汇总。论文另定义了 input-script 与 output-script 间的比例完全二部资金流边。N1 只能审计从观测二部关系到 source-conditioned flow completion 的推断，不得声称基础账本 ETL 错误。
3. **N2 的算法骨架不新**：期望 coverage 的次模性和 greedy `1-1/e` 是标准推论；可发表空间只能来自可审计的 Bitcoin 决策 estimand、数据和非平凡 partial-identification/regret 结果。
4. **现有 252M 资产对 N1/N2 均非直接输入**：它是终态实体聚合图，缺少 outpoint 级结构和 union lineage。N1 的最小原始数据应由 Bitcoin Core 局部重建；N2 则尚无满足硬门的数据。

## Gate 状态

Gate 2 继续开放。当前没有足够证据冻结主方向：N1 已完成第一轮 robust/uncertain graph 独立反证，仍只是条件候选；N2 当前数据硬门不满足；N3 停止实施。未得到用户确认前，不向 Gate 3A 晋级，也不启动模型训练。

## 独立红队结论

红队没有批准任何主方向，建议继续 Gate 2；该结论覆盖分数排名：

- **N1 仅为条件性第一名**：只批准 raw-UTXO、小窗口、少量公开 source 的 certificate 可用性与创新性判别，不批准 GNN 训练或 AML/非法识别叙事。全局多跳上下界必须保持交易间相关性，不能把逐跳区间独立相乘。
- **N2 当前 No-Go**：没有可发布的 as-of partitions、独立 entity truth 和真实 case/service outcome；现有资产也无 union lineage。它不是当前第二实施方向。
- **N3 当前 No-Go**：数据对象、来源独立性和 outcome 均需新建，且容易把后续转载误作事实佐证。
- **N4 当前 No-Go**：没有 action、propensity、结案 outcome 和 delay/censoring 日志，`regret` 没有可验证的 operational referent。
- **N10 仅作 fallback 决策测试**：known-type OOD/abstention 可以约束主张，但单独贡献接近数据文档和常规基线，不能包装成 AML benchmark。

N1 的最强停止条件是：在预先定义的合理阈值下，几乎所有 endpoint/排序都无法认证，或 certificate 只复现既有 taint-policy comparison 而没有新的任务级结论。若触发，返回 Gate 2 继续寻找问题，不用模型复杂度掩盖失败。

## N1 独立创新性反证结果

四轮反证覆盖 exact Bitcoin/UTXO、uncertain/robust graph、partial identification/robust ranking 和 2024–2026 并发工作。当前未核验到 exact prior，但这不是“首次”证明：

- Tironsakkul et al. 2019/2022 已明确比较 Haircut、Poison、FIFO、LIFO、TIHO 并证明追踪集合随规则显著改变；N1 不能只复现规则差异。
- Arafat et al. 2024 已对独立边概率的 possible-world graph 估计网络量/ML 输出不确定性；Chen et al. 2016、Wang et al. 2021 等已覆盖 robust graph decision 与结构扰动证书。N1 的可能差异仅是 **UTXO 守恒导致的耦合 completion set**，不是泛化的“图不确定性”。
- Al-Sowadi 2025 通过新增 sub-range UTXO、Verkle tree 和 KZG proof 实现 satoshi provenance；N1 必须明确研究的是**不修改协议时的历史账本可识别性**，不是首次精确追踪。
- 美国专利 US20200167791A1/US11257089B2 已覆盖 wallet-level proportional-flow risk propagation 与阈值处置。N1 禁用 wallet risk/quarantine 叙事，公开实现前需独立 IP 审核。

当前最小非重叠主张只能是：对预注册的 source-conditioned 下游量，在所有账本兼容 completions 上计算 exact 或 provably sound identified set；只有 path、threshold sign 或 pairwise ranking margin 对全体 completions 稳定才输出，否则标记 `unresolved under ledger-only provenance`。transportation polytope、LP 上下界、generic robust ranking 和 uncertainty head 都不是新贡献。

独立审计给出的暂定判断为：没有 exact prior 的置信度 0.65（非证明性）；固定到 ledger-derived coupled ambiguity 与 decision certificate 仍可能形成非重叠贡献的置信度 0.75。只有一个不含 GNN 的极小 certificate pilot 能证明它是否产生非平凡、可解释的稳定结论；在此之前不能称为推荐主方向。

## Zotero 增量

已在本机 Zotero 去重后导入并加标签 `Bitcoin Evidence Research 2026`：

| 论文 | Zotero item key | citation key | 用途 |
|---|---|---|---|
| Jalili 2025, *The Temporal Graph of Bitcoin Transactions* | `FHEWU8PH` | `jalili2025temporal` | N1 的 ML 图表征应用对象 |
| Gavenda et al. 2025, *Analysis of Input-Output Mappings…* | `XVWA7QGV` | `gavenda2025mappings` | 原始 N7 的致命最近邻 |
| Maurer et al. 2017, *Anonymous CoinJoin Transactions…* | `ZY9V86UE` | `maurer2017anonymous` | arbitrary-value CoinJoin mapping 先行工作 |
| Tironsakkul et al. 2019, *Probing the Mystery…* | `JRVXPK6Q` | `tironsakkul2019probing` | taint rules 与经验分歧基线 |
| Albrecht and Karame 2026, *On the Effectiveness of Mempool-based Transaction Auditing* | `DF2ZPIDJ` | `Alb26` | M1 最近邻与 16 节点公开 artifact |
| Arnold et al. 2024, *Insights and Caveats from Mining Local and Global Temporal Motifs…* | `B5EL7T7F` | `Arn24` | M2 的直接同块顺序反证 |
| He et al. 2026, *MBAL: A 10-Million Annotated Crypto Address Dataset…* | `7J99D9ZI` | `He26MBAL` | M5 核心数据论文；数据结构与原随机地址切分来源 |
| Lin et al. 2019, *An Evaluation of Bitcoin Address Classification…* | `FFVQ8FAU` | `Lin19AddressEntity` | M5 的 address/entity 双任务直接组件反证 |
| Yin et al. 2019, *Regulating Cryptocurrencies…* | `DXV3YET5` | `Yin19Regulating` | Bitcoin cluster/entity 分类直接先行工作 |
| Zola et al. 2022, *Attacking Bitcoin Anonymity…* | `DQU849FC` | `Zola22GANEntity` | 大规模 Bitcoin entity 分类近邻 |

Zotero item key 与 BibTeX citation key 是两套标识；后续同步 `references.bib` 时以 citation key 为 Git 侧主键。

当前 connector 只能导入到 Zotero 根文库，不能创建 collection；新增条目用 `Bitcoin Evidence Research 2026` 及 `btgr:*` 标签隔离。collection 创建能力接通后再移动，不直接修改 Zotero 数据库。

## 2026-08-24：N1 A1 证据更新（覆盖先前“条件性第一名”判断）

N1 的 48-instance locked synthetic 已在预运行 commit `0aa54ad` 上完成：exact oracle mismatch 为 0，说明当前小图 solver 没有被正确性反例击穿；但 `mixed` 16/16 的 threshold CDR 与 pair CDR 均为 0，median normalized width 为 1。只有按构造不存在混合歧义的 `unique` 族取得点识别，对称族则按预期全部拒证。

该证据不允许外推“真实 Bitcoin CDR 为 0”，但已经击中 N1 当前研究论点的核心机制：一旦 source 与 clean value 发生普通两层混合，仅靠 ledger-compatible completions 可能得到完整而非局部的不确定区间。独立 Devil's Advocate 因此将 N1 从“条件性第一名”降级为 `negative conditional / parked`；不批准 B1、模型扩展或论文主线。

唯一获批的后续工作是一个低成本、预冻结的 B0 structural falsification screen。它只能检验现实两跳结构中非退化证书是否足够常见；不能作为 N1 Go 或现实统计证据。若 B0 接近全 abstain，N1 直接 No-Go，研究回到 Gate 2 比较其余候选方向。

## 2026-08-30：第二轮新候选与第一道硬门

N1 的负向结果触发了新的独立候选生成。候选先由资产、理论和反方三个互不共享结论的视角提出，再启动 Undermind 与独立官方来源检索。当前排序不是最终选题。

### M1：多观察点 mempool 分歧下的校准结果预测

- **RQ**：对预测时点已被若干独立 Bitcoin 节点观察到的交易，多观察点的覆盖、首次接收时间分歧和地理/策略视图，是否能在严格时间外与 observer-held-out 评测中，提高一定时间窗内确认结果的概率校准和选择性覆盖？
- **主张边界**：当前只允许研究 confirmation-within-horizon。公开 artifact 没有原始交易、输入输出、手续费、RBF 冲突或 eviction 事件，不能把问题扩写为 replacement、package 或 eviction prediction。
- **最近邻**：Albrecht and Karame 2026 用 16 个全球观察点审计交易集合/顺序一致性和 displacement/censorship 判定；其 Bitcoin 主测量持续 196 小时，记录约 313 万笔交易。Kim et al. 2020 比较四个 mempool 的 Jaccard 相似度。Koops 2018 与 Aronoff et al. 2026 提供单视图排队/延迟强基线。
- **真正待证差异**：最近邻没有把 observer disagreement 用于经过时间外和 held-out observer 检验的 confirmation probability calibration；但“没有检出”不是首次性证明。
- **数据硬门**：Albrecht artifact 仅发布交易哈希和 16 个首次接收时间，许可为 CC BY-NC 4.0。它可以与最终链上确认状态连接，但对未确认交易无法恢复预测时本应可见的手续费与完整交易内容，因而无法公平运行 fee/package 强基线。若不能获得原始交易或重新开展多节点采集，M1 No-Go。
- **最小判别实验**：先只读审计 artifact 的覆盖期、缺失模式、链上连接率和 outcome 删失；不训练新模型。只有能构造无 outcome-dependent feature missingness 的 fee/age/queue baseline，才冻结 chronological、congestion-stratified 和 observer-held-out 协议。
- **指标**：Brier score、log loss、reliability、coverage–risk、不同拥堵区间的 calibration；accuracy 不是主要指标。
- **理论性质候选**：研究 private relay 与 observer-specific policy 下 outcome probability 的可识别边界，以及 observer-set permutation/metadata 条件下的预测不变性。该方向目前只是理论问题卡；若只得到标准的“增加信息不提高 Bayes risk”或普通 missing-data 界，不作为贡献。
- **最强拒稿理由**：数据只支持一次短期网络测量；增益来自更多时间戳而非新问题；手续费强基线缺失；2026 审计论文已覆盖多观察点主要现象。
- **当前裁决**：`high-upside alternative / new-measurement-gated`。重要性 4、证据质量 3、当前数据可行性 1，乘积 12；只有获得包含预测时可见手续费、交易内容、冲突/替换状态和多观察点时间戳的数据，或获批重新开展数周多节点采集，才重新评分。

### M2：合法同块线性扩展下的结论稳定性

- **RQ**：对只有区块级时间、但被实现赋予区块内总序的 Bitcoin temporal graph，沿所有依赖保持的线性扩展改变事件顺序，是否会改变特征、嵌入、预测或模型排名？
- **直接反证**：Arnold et al. 2024 已明确指出同块内只有 UTXO 依赖带来的拓扑顺序保证，并已随机化同块顺序；其 temporal motif count 最大偏差约 3%。通用 temporal graph 文献也已讨论 ties、batching、reachability 和 event-order sensitivity。
- **剩余差异**：模型预测/排名与严格依赖保持的线性扩展尚未被当前检索完全覆盖；但单纯把 motif 审计换成 TGN 审计仍高度增量。
- **当前裁决**：`main-track No-Go / method component only`。只有先证明常用模型结论出现实质翻转，并形成非平凡的 ledger-semantic invariance 方法或界，才允许重新入池。

### M3–M4：反证后降级

- **M3 audit-query-preserving sampling**：Undermind 检出 75 篇相关工作。需求对 reachability/distance/flow preservers、temporal spanners、streaming lower bounds 和区块链索引已有成熟理论；Bitcoin 系统也已覆盖摄取、遍历、时间分区和大图采样。当前没有冻结的真实 audit query family，也没有 Bitcoin 特有且不能由通用 preserver 覆盖的保证，因此裁决为 `main-track No-Go / theory-dependent reserve`。
- **M4 service-label lifecycle**：Undermind 检出 73 篇相关工作，已存在 abuse-report 污染、multi-source conflict resolution、dataset opacity 和 attribution reliability 的直接近邻。公开 MBAL 虽提供 `source`，但没有标签获取时间、有效时间、撤销记录或冲突 outcome；其 `source` 只是 `ground_truth / heuristic / external` 三档。当前裁决为 `No-Go as lifecycle study / merge into evaluation audit`。

### M5：实体暴露感知的加密货币地址分类评测

- **RQ**：当训练集和测试集按现实服务/实体严格隔离，而不是只保证地址字符串不重复时，地址类别分类的性能、校准和模型排名是否显著下降或翻转？随机地址切分到底估计“已见实体的新地址”，还是“未见实体的泛化”？
- **现实决策**：研究对象是 `entity/service type classification`，不是 illicit、fraud 或 AML 风险识别。部署含义限定为：面对训练时未出现的服务实体，模型能否根据地址行为特征预测其服务类别。
- **直接数据机会**：MBAL 发布 1000 万地址、62/63 个类别、933 个实体和三档来源；master 表包含 `chain / address / categories / entity / source`，Bitcoin 与 Ethereum 实验表分别包含地址、类别及 144/207 个特征。官方 Kaggle 说明表明原实验按地址行随机抽取测试样本，而非按实体分组。
- **第一性问题**：若一个实体拥有多个地址，随机地址切分会让同一实体同时进入训练和测试。测试风险可以分解为已见实体风险和未见实体风险；只报告混合风险不能回答 unseen-entity 部署问题。该分解本身是标准 grouped evaluation 思想，不能单独作为理论贡献。
- **本地先验证据**：现有公开地址标签中，39,047 个同时有类别和实体名的地址只对应 697 个规范化实体；一次 40/30/30 随机切分中，约 98.9% 的具名测试地址所属实体已在训练集出现，实体名查表准确率约 0.987。这是泄漏风险信号，不是 MBAL 的最终结果，也不能外推 252M 节点图。
- **最近邻与反证**：StableAML 的“wallet-level split”只保证唯一地址行不重复，其节点本身是 wallet address，并未证明同一现实服务/实体不会跨分区。更强反证来自既有实体级分类：Lin et al. 2019 已在 26,313 个具名地址和 1,353 个实体上分别执行 address-based 与 entity-based classification；Yin et al. 2019 以 957 个已识别 Bitcoin clusters 为分类样本；Sforzin et al. 2022 则在 327 个 WalletExplorer 实体、约 1600 万地址上采用地址随机切分。它们没有完成 M5 所要求的同任务 random-address vs unseen-entity 模型排名/校准对照，但已经覆盖“实体是独立预测单位”和“随机地址切分会混入同实体地址”两个核心组件。
- **最小判别实验**：不下载完整 4.8GB 特征前，先核验 master 表中 Bitcoin/Ethereum 的 entity 覆盖、每实体地址数、类别纯度、source 分布，以及实验地址能否稳定连接回 master。通过后，对原作者随机地址 split、entity-disjoint split、entity-and-source stratified split 使用同一特征和同一调参预算，比较查表诊断、logistic regression、random forest、XGBoost 与论文模型。
- **主要指标**：macro-F1、per-class recall、Brier/ECE、模型排名相关性及随机切分相对 entity-disjoint 的效应量；必须报告无实体名地址和小实体类别的支持度，不用 accuracy 掩盖类别坍缩。
- **理论审计**：随机地址 split 中测试地址已见同实体的概率 `1-(1-p)^(n_e-1)`、seen/unseen 风险混合、cluster bootstrap 和按实体 GroupKFold 均属于成熟 grouped evaluation/domain generalization 范畴。该分解不适用于 macro-F1/ECE 的线性校正，IPW 也不能把随机训练模型变成 entity-held-out 模型；这些性质可约束协议，但不能作为顶会理论主贡献。
- **创新硬门**：至少满足以下一项才允许重新竞争主方向：跨 Bitcoin 与 Ethereum 复现稳定的大幅性能/校准变化；强模型排名翻转；`source × entity` 双重隔离揭示仅按实体 GroupKFold 仍不能消除的可验证机制；或有限预算决策发生稳定而实质的改变。若只是“换成 GroupKFold 后分数下降”，立即 No-Go。
- **最强拒稿理由**：分组切分是常识；只审计一个刚发布数据集；三分之二地址缺实体名；实体字段本身可能由标签源推导并存在误归属；没有时间戳，不能声称时间部署有效。
- **当前裁决**：`main-track No-Go as currently formulated / low-cost rescue screen only`。重要性 4、证据质量 5、可行性 4，表面乘积 80；但直接组件覆盖和标准方法学硬门优先于分数。仅允许先做 master→experiment join 与支持度审计；只有它预示可执行的跨链 `source × entity` 对照，才可预注册一个低成本 rescue pilot。

### 当前董事判断

第二轮没有产生可直接冻结的主方向。M1 有较高研究上限，但公开数据缺关键预测特征，必须重新开展多节点测量；M5 具备低成本可证伪性，但当前问题退化为标准 grouped evaluation，主线 No-Go；M2、M3 不作为主方向，M4 的静态来源信息只可作为 M5 的 rescue component。下一步进入第三轮候选生成，硬约束为：不依赖现有 11 类标签支撑 AML、不以普通 split 修正或模型堆叠作为创新、公开数据能执行最小判别实验，并优先寻找 ledger-specific 的新性质。

## 2026-08-30：第三轮候选与协议机制核验

第三轮独立生成先剔除了两个伪新方向：比例 UTXO-to-entity graph 的可识别性与 N1 等价；单条聚类 bridge/error certificate 与 CP-02 的错误传播问题等价，且仍缺独立真值与 union lineage。两者不重新编号、不换名复活。

### M6：Ordinals 市场协作式 PSBT 对 common-input clustering 的污染

- **核心机制**：Ordinals 市场为实现非托管原子交换，常让卖家对 inscription input 使用 `SIGHASH_SINGLE | SIGHASH_ANYONECANPAY`，买家随后加入付款 input 并完成交易。当不同签名角色确属不同控制者时，对全部 inputs 执行 common-input ownership union 会产生错误合并；链上角色结构本身不证明这个所有权前提。
- **跨平台证据**：ORD.NET 官方 sale construction、OrdinalsBot 官方 marketplace 示例、Magic Eden 开源 `msigner` 和 OrdinalsWallet 技术说明均给出该组合；因此不是单一网站的偶发现象。PSBT 只是协调格式，最终链上只保留交易和签名；可观测检测必须解析 ECDSA/Taproot signature hash type、spent output 和 inscription movement。
- **链上锚点**：ORD.NET 官方示例交易 `0f2f22ed557359039a80620bb5d559f3bc2b982f1b03ddfc771668d115a1ce40` 包含平台 anchor、seller/platform 2-of-2 passthrough 和 buyer funding inputs。公开原始交易显示 Taproot witness 中同时存在附加 `0x83` 的 `SINGLE|ANYONECANPAY` 签名、默认签名和其他 `SIGHASH_ALL` inputs。该样本证明协议模式可从链上恢复，不证明总体规模。
- **文献反证**：Undermind focused deep search 已完成，返回 22 篇近邻；最接近的是 BRC-20 PSBT sniping、PayJoin UIH、MIH 可靠性、协议型 CoinJoin detection 和 Ordinals 网络影响。八篇关键 PDF 的定向全文核验仍未发现直接测量 Ordinals/数字资产市场 PSBT 对 CIOH cluster contamination 的工作。独立 exact/component 搜索得到同一结论；这只支持“当前检索快照未见 exact prior”，不能写成首次。
- **潜在新贡献**：不是重复“多方交易破坏 CIOH”，而是识别一个 2023 年后规模化、可由密码学签名角色和 inscription 语义高精度检测、可能绕过常见等额输出 CoinJoin filter 的交易族；量化其错误 union、component cascade 和公开 entity graph 偏差，并提供 protocol-aware filter 与修正清单。
- **构造效度边界**：`SINGLE|ANYONECANPAY` 证明该 input 的承诺范围，不证明签名者属于不同现实所有者。wash trade、自成交、共同托管和平台共签必须单列；当前允许的主张是 `protocol-incompatible common-input union`，只有独立证据支持时才称为 false ownership merge。
- **最小硬门**：三个市场的官方/开源模板与人工核验样本；比较未过滤 CIOH、常见 CoinJoin filter、删除全部 `ANYONECANPAY` 的粗基线和 protocol-aware filter。先测 detector precision、标准过滤器漏检、交易量、component merge/cascade；不训练 GNN，不接 11 类 AML 叙事。
- **零模型 smoke**：标准库 raw-block scanner 在区块 947353 的 2,856 笔交易中检出 17 笔结构合法的显式 `0x83` 候选，并命中官方示例。该区块只验证解析器和机制，已从估计样本排除。
- **现有过滤器复核**：Schnoering–Vazirgiannis 2023 的 JoinMarket/Wasabi/Whirlpool 规则和 BlockSci 官方 CoinJoin predicates 均不标记代表交易 `1f533fce…0abe6f`；BlockSci 的共同输入聚类调用链因此会执行 union。该结果支持“已发表公开规则存在漏口”，不覆盖私有商业规则，也不证明不同现实所有者。
- **资源边界**：现有 252M 图缺 txid、witness 和 union lineage，不能直接执行。Gate 2 只用官方 txid、公开 explorer/ord index 和小窗口；小样本通过后才考虑外部存储、远程节点或流式全链扫描。
- **硬停止条件**：只存在单一平台；高精度检测不可复现；现有过滤器已去除超过 95%；规模或 component 效应很小；独立主体无法操作化；最近邻已有等价测量；最终只剩简单 ETL 规则。
- **理论判断**：多签名主体交易下 CIOH 不可靠、错误 bridge 使 union-find component 不可逆合并均为直接性质，不作为主定理。只有得到非平凡可检测充分条件、部分可观测下的污染界或可检验传播保证，理论才能升级为贡献。
- **当前裁决**：`conditional lead / input-provenance, ground-truth and effect gates open`。重要性 5、证据质量 3、可行性 4，乘积 60。detector-v2 诊断复算保留规模信号，但独立 prevout 核验、跨市场语义真值和聚类传播效应尚未完成，仍不是正式推荐主方向。

### CP-13 零模型抽样协议 v1（结果查看前冻结）

- **As-of boundary**：只使用不晚于区块 947352 的确认交易；已查看的区块 947353 完全排除出估计样本，只保留为机制和解析器 smoke。
- **Deterministic sampling**：以 `SHA256("CP13-pilot-v1|2026-08-30|stratum|counter")` 的前 8 bytes 对区间长度取模，每层无放回选择 6 个区块。四层共 24 个区块：pre-inscription control `700000–759999` 取 `722970, 727123, 732002, 738810, 741953, 750002`；early marketplace `780000–839999` 取 `789561, 815344, 820955, 824355, 827471, 830004`；post-Runes `840000–899999` 取 `847310, 848410, 848594, 877986, 887012, 888771`；recent `900000–947352` 取 `901077, 902343, 918143, 918573, 939796, 943404`。区间名称只表示时间层，不预先假设每笔候选的资产协议。
- **Tier 0 detector**：结构合法的 ECDSA 或 Schnorr witness signature 显式携带 `0x83`；Taproot script/control-block 项必须排除。Tier 0 只测候选召回入口，不等同市场交易。
- **Tier 1 structural candidate**：存在 `0x83` input `j`；`vout[j]` 存在并回到该 input prevout 的 script；同一交易至少还有一个不同 input script；`vout[j]` value 大于该 prevout value。该规则表达 `SIGHASH_SINGLE` 卖方输入与同 index 收款的可观测结构，不证明 inscription、市场归属或不同受益所有人。
- **Tier 2 validated settlement**：除 Tier 1 外，还须由官方/开源 marketplace template、官方示例、可信 ord index 的 asset movement 或可核验平台模板至少一项确认交易语义。平台名称、资产类型和独立交易方只在相应证据存在时记录。
- **Published-filter comparison**：逐笔复现 Schnoering–Vazirgiannis 的 JoinMarket/Wasabi/Whirlpool 条件和 BlockSci CoinJoin predicates；不把“代码搜索未命中”当 filter 结果。
- **Primary outputs**：各层 transaction count、Tier 0/1/2 数与 block-level distribution；Tier 1 中已发表 filters 漏检率；独立 input-script union 数；可重复 template fingerprint 数；control 与后三层的差异。单块内交易不作为独立总体样本；区间比较以 block 为采样单位并同时报告原始计数。
- **Advance rule**：24 个区块合计至少 20 个 Tier 1，覆盖至少两个非相邻时间层，并出现至少两个可区分 template fingerprints；已发表 filters 对 Tier 1 的漏检率至少 50%；至少两个公开实现/市场能进入 Tier 2。满足前三项但 Tier 2 暂缺时只允许补 ground-truth，不允许直接晋级。
- **Stop rule**：Tier 1 少于 10 个、只集中于一个区块/单一模板、过滤器漏检低于 5%、或人工检查显示大多数为非市场协作用途，则 CP-13 main track No-Go。介于 Advance 与 Stop 之间只允许一次扩大到 60 个按同算法生成的区块；不得改 detector 追逐结果，规则变更必须作为 v2 并在新样本评估。

### CP-13 零模型抽样协议 v1 结果

> 2026-08-31 复核标记：本节为 detector-v1 历史输出，解析器发现 witness 上下文错误，晋级结论暂停。原始产物不覆盖；修正后另保存 detector-v2 复算。样本不变的修正复算仅用于排错，不能替代后续独立样本检验。

#### Detector-v2 修正协议（复算前记录）

不改变冻结的 24 区块样本和 Tier 1 同 index、同 script、正 value 增量条件。原始扫描只产生字节形状候选，必须在 API prevout 富集后核对脚本上下文：P2TR 按 BIP341 先排除 annex，只接受 key-path 单项显式 `0x83`；native/nested P2WPKH 核对公钥 HASH160、嵌套 redeemScript HASH160、签名位置与 strict-DER 编码。P2WSH、Taproot script path 和其他未解释的脚本路径列为未决，不计入上下文核验后的 Tier 1。API vout 必须逐项等于 raw transaction 的 value/script；当前 prevout 仍依赖 API，未完成逐个原始父交易重算，所以“上下文核验”不是独立密码学验证。旧文件不覆盖，新文件使用 `cp13_pilot_v1_detector_v2.json`；任何新增或删除候选均须报告。

#### Detector-v1 历史计数（已被修正版本替代）

- **规模与时间分布**：24 个冻结区块共 65,545 笔交易，Tier 0 为 838，Tier 1 为 662。六个 control 区块共 13,948 笔交易，Tier 0/Tier 1 均为 0；early-marketplace、post-Runes、recent 三层的 Tier 1 分别为 491、144、27。Tier 1 分布在全部 18 个后期样本区块，覆盖 123 个结构指纹；86 笔含多个匹配 `0x83` inputs。
- **公开过滤器下界**：636/662（96.1%）Tier 1 存在重复 output script，因而必然不满足 Schnoering–Vazirgiannis 所列 JoinMarket、Wasabi 和 Whirlpool 公开结构规则。该数字是针对这些已发表规则的保守漏检下界，不外推到私有商业过滤器。
- **公开实现兼容性**：101/662（15.3%）匹配 `msigner` 的部分 dummy-input/output 与 seller-index 布局（源码复核后更正，非严格默认模板），只能记为实现家族兼容，不能直接认定平台归属。ORD.NET、OrdinalsBot 与 `msigner` 已证明至少三个公开实现采用相同协作签名机制，但尚未逐笔验证样本资产语义。
- **协议裁决**：预设的 Tier 1 数量、非相邻时间层、多个指纹和公开 filter 漏检率四项规模/结构条件均通过。第五项“至少两个公开实现/市场进入 Tier 2”未完成，因此不扩大到 60 区块，也不进入模型开发，只补 ground truth 和传播效应。
- **当前阻塞**：Magic Eden 官方 block-activity API 的匿名请求连续返回 HTTP 503；这不能解释为样本中没有 inscription transfer。下一步优先使用可审计的官方/开源交易模板、恢复后的官方索引或本地/可信 ord index 交叉验证。

#### Detector-v2 诊断复算与独立复审

2026-08-31 复算结果：同一组 24 区块共 65,545 笔交易，845 个 witness 字节形状候选中有 832 笔在支持的签名上下文通过检查，666 笔满足 Tier 1 条件。control/early-marketplace/post-Runes/recent 的 Tier 1 为 0/494/145/27；全部 18 个后期样本区块均有候选。87 笔有多个匹配 inputs。公开结构规则漏检下界为 640/666（96.1%）；`msigner` 部分布局特征匹配为 103/666（15.5%，源码复核后更正）。未通过上下文检查的 13 个交易不计入 Tier 1，不能统一称为假阳性，因为未实现脚本路径中也可能包含真实签名。

与 v1 比较：原 662 个 Tier 1 全部保留，新增 4 个、删除 0 个；新增者均包含被旧代码误删的 `0xc0/0xc1` 前缀单项 Taproot key-path 签名。新增 txids 为 `a23c33ac6c9b5cd4176deed72a08357a143ab2dc821df31403be8adf8d099ada`、`5f2a7a3d22c59563df97a79dfc8b5d9137be629a8e26649bb292c5c2f71398fa`、`eb2bcc3ca006716a6c2417c3d21976d7ababe35750891675547ebcaa7211b7c7`、`740f31e25e2ae0ca42e9945d50d8cbe744e360d03a633ac530c90881eeeefd3b`。字节形状候选总共新增 7 个；另外 3 个新增交易为不支持的 script path，没有进入 Tier 1。

独立只读复审核对了新旧集合、代码与产物 hash、annex 排除、script-path 未决规则以及 native/nested P2WPKH 上下文；未发现当前支持范围内的新关键分类错误。两个脚本的 self-test 通过。所有“验证”仅指 context screening，仍依赖确认链有效性与 API prevout 正确性，不是重新执行 ECDSA/Schnorr 密码学验签。官方规则依据为 [BIP141](https://github.com/bitcoin/bips/blob/master/bip-0141.mediawiki)、[BIP341](https://github.com/bitcoin/bips/blob/master/bip-0341.mediawiki)、[BIP342](https://github.com/bitcoin/bips/blob/master/bip-0342.mediawiki)。

复算命令（本地缓存目录可替换，原始内容须匹配产物中 hash）：

```powershell
uv --cache-dir .uv-cache run --no-sync python scripts/research/run_cp13_pilot_v1.py --block-dir "$env:TEMP\btc_cp13_v1_blocks" --cache-dir "$env:TEMP\btc_cp13_v1_txjson_blockchain" --api-base https://blockchain.info --workers 4 --output experiments/diagnostics/cp13_pilot_v1_detector_v2.json
```

产物 SHA-256 为 `3F517032CF15D35E56F28A5E5F0A2AE4184BDCC437B3334403A5E9FDE96A779F`；scanner 为 `9BE81CF2603B635FDDD9D07B22BE8DB346AF7248CF772A3F168F8DCF71F5E8F2`；runner 为 `D06262421B9C23F7DAC84E054F5ECF53CB6A301173D9B864C5D79B4B5446F7B6`。源代码在 `3573cec` 基线上带本次显式修正 diff 运行。旧产物保持原 hash；同样本复算不作为独立重复验证。

后续只推进输入来源与语义真值硬门：核验原始父交易及 outpoint；取得至少两个实现家族的可审计资产结算语义；不把当前 UTXO 快照当历史 transfer 真值，不把失败请求当无转移。2026-08-31 ordinals.com 单个公开 output 查询返回 HTTP 403，Undermind 同步两次出现 connector transport error；本地证据已保留，远端同步待恢复。

### CP-13 原始父交易与直接 reveal 审计 v1（执行前冻结）

目的为验证语义证据获取是否可行，不估计总体比例或 detector precision。以 detector-v2 的 666 个 Tier 1 为固定输入，按三个后期时间层与 `msigner-compatible` 布尔值形成六个单元，每单元取 `SHA256("CP13-semantic-v1|txid")` 最小的两笔；不足两笔不补选。共 11 笔，直接父交易去重后 36 笔；不得按 reveal 是否容易解析替换样本。

核验规则：由公开 raw hex 重新计算父交易 txid，按 child raw outpoint 提取 value/script，与已记录的 Tier 1 prevout 比对；所有输入均从父交易取值，以复算独立脚本数和 ordinal FIFO 输出落点。直接 reveal 只接受一输入一输出、一个标准 Taproot `CHECKSIG` 后单 envelope、仅 content-type 字段、无 pointer 的简单情形，并核验其 commit outpoint 是 P2TR。其他情况一律未决，不视为无 inscription。只保留 MIME、body hash 和必要的 BRC-20 声明字段，不复制图片内容。BRC-20 transfer 声明不等于已核验有效余额或 token transfer；资产脚本变化不证明平台归属或不同现实所有人。

两笔先前手工探查样例（`00e2b4e4…89f009` 与 `88851136…0b8be2`）只用于设计此最小解析范围，不纳入这 11 笔的新样本结果。raw witness 与父交易元数据来自同一公开提供者；txid 复算约束非 witness 序列化，但没有重新验证区块 witness commitment。因此不得把该步骤称为完整密码学独立验证。执行入口为 `scripts/research/audit_cp13_parent_semantics.py`，产物另存 `experiments/diagnostics/cp13_parent_semantics_v1.json`。

#### 语义审计 v2 完整性补充（执行前记录）

v1 固定样本得到 7 个直接 simple-reveal-shaped witness；独立审查强调 txid 不承诺 witness，因此全部七个都要核验，不筛选成功案例。v2 保留同一样本与识别规则，另从 Blockstream 取得各 reveal 所在高度的区块 hash，再从 Blockchain.com 获取该 hash 的完整 raw block；重算 header hash、txid Merkle root、wtxid Merkle root、coinbase witness reserved value 和最高 output index 的 BIP141 witness commitment，并要求目标父交易的原始序列化逐字节 hash 匹配。全部成功才将这七条 payload 记为 anchored-block witness evidence；失败或缺失保留未核验。该步骤信任 Blockstream 的主链 hash 锚点，不等同完整 Bitcoin Core 共识与 PoW 链验证。新产物为 `cp13_parent_semantics_v2.json`，不得覆盖 v1。

#### 语义与完整性审计结果（2026-08-31）

固定选择得到 11 笔交易、36 笔直接父交易；为核对 reveal 的 commit outpoint 再取 7 笔父交易，共 43 笔。11 个 Tier 1 匹配输入的原始 prevout value/script 全部一致，11 笔交易各涉及两个不同 input scripts。7 笔符合事先限定的单输入、单输出、无 pointer 的 simple-reveal 规则；其余 4 笔超出直接 reveal 范围，保留未决，不递归追踪到出现正例为止。

7 个 payload 中，6 个含 BRC-20 `op=transfer` 声明，1 个为 532-byte image/webp。它们的内容承载首 sat 按限定 FIFO 规则均进入 child output 1，且该脚本不同于卖方输入脚本。逐交易 outpoint、MIME、body SHA-256、声明字段与目标输出见 `cp13_parent_semantics_v2.json` 的 `records`。该结果只确认简单内容与 sat 路径，不核验 BRC-20 余额、合法铸造/转移状态，也不替代完整 Ordinals 索引、真实成交或现实所有权真值。

全部 7 个 reveal 的完整 raw witness 已核验到区块 `820951, 824153, 847510, 873887, 888412, 918139, 918533`。每个区块均核对 Blockstream 高度→hash 锚点、Blockchain.com raw block、header hash、txid Merkle root、零 coinbase wtxid 叶子的 witness Merkle root、coinbase reserved value、最高索引 commitment output，以及目标交易 raw SHA-256。七项全部成功；验证范围与信任边界保存在 `block_proofs` 和 `limitations`。独立只读复审未发现会改变结论的字节序、奇数 Merkle 叶复制或 commitment 选择错误；包含变异 witness root 拒绝检查的 self-test 通过。

复现命令（输出不得覆盖历史版本，重复核验时使用新的临时路径）：

```powershell
uv --cache-dir .uv-cache run --no-sync python scripts/research/audit_cp13_parent_semantics.py --cache-dir "$env:TEMP\btc_cp13_parent_hex_v1" --verify-witness-blocks --output experiments/diagnostics/cp13_parent_semantics_v2.json
uv --cache-dir .uv-cache run --no-sync python scripts/research/audit_cp13_parent_semantics.py --self-test
uv --cache-dir .uv-cache run --no-sync python scripts/scan_block_sighash.py --self-test
```

版本与内容追溯：

- 输入 detector-v2 快照仍为 `6d0e23d` 所记录的 666 个 Tier 1，不重新筛选样本。
- `cp13_parent_semantics_v1.json` SHA-256：`E192E587D8E66DB451A5DF5906B24FFB26C2E2761981F197972F0B4B684F38F2`；缺少 witness commitment 的历史限制保留。
- `cp13_parent_semantics_v2.json` SHA-256：`2E75DFC081A4E14D739D59DD66869AB20561F945DA99DEF8EBE9F04E20DD4A6F`。
- v2 audit 脚本 SHA-256：`806DA59921A7DC7CB3804C4F82DB7ABBD7F0E9E3AC5D71CCCA4AFAD4E1D285F5`；scanner SHA-256：`024E3F457631CB582685DF046575E69900203CADA66D4E1CD1FD40282723DED7`。
- scanner 本次只增加可选 `retain_witnesses`，默认候选扫描逻辑不变；旧 pilot 的代码 hash 不回填为当前 hash。v2 在 `6d0e23d` 加显式工作区 diff 上运行，代码和产物在本里程碑一起保留。

#### 公开实现覆盖反证与当前裁决

[ORD.NET 官方构造](https://docs.ord.net/technicals/sale-psbt-construction/) 的 `Sale path`、`Passthrough Tapscript` 与链接示例说明：卖方签名为 `SINGLE|ANYONECANPAY`，平台签名为 DEFAULT，成交走 `multi_a(2, seller, platform)` script path。官方示例 `0f2f22ed557359039a80620bb5d559f3bc2b982f1b03ddfc771668d115a1ce40` 的 input 2 有四项 witness，script 内平台公钥为 `d2dc3222298e2a5f4e1c7d702fae2bcf7821cc0a095a478b95c62195b0df7398`；其 prevout 为 `ff46c2aa8f80eb4ce1083ffc167ab6506741bbf4f93e1765ccb51302a18a7dea:0`，对应 output 2 为 99,330 sat 的 P2WPKH，而非输入 P2TR 脚本。

这给出了当前 detector 的两个独立漏检原因：未支持 script path，以及 Tier 1 要求输入和付款输出脚本相同。官方目的性示例本来就排除在 24 区块样本外；对 845 个字节形状候选检查该平台公钥的精确 2-of-2 模板，命中为 0。该数不估计市场活动量或召回率。后续若支持该协议，必须冻结新版本、独立评估，不静默修改原样本的成功条件。

[Ordinals Wallet 官方解释](https://ordinalswallet.com/learn/how-psbt-settlement-works) 及 OrdinalsBot SDK/文档提供了第二实现的文本级机制，但本轮没有取得可逐字节连接的第二平台主网成交链。`msigner-compatible` 仍不等于 Magic Eden 归属。当前结论为：固定子样本的来源/内容完整性通过；跨实现 Tier 2、独立所有权语义与传播效应门开放。不会因已投入解析器工程而降低创新性和效应标准。Undermind 本轮再次出现 transport error，尚未完成远端同步；本地记录是当前版本。

回归核验使用已有区块和 API 缓存，把当前 scanner 的输出另存临时路径；`summary`、24 个 `blocks` 和全部 845 个 `candidates` 与冻结 detector-v2 快照逐字段一致。变化只有记录代码版本的 hash，不把缓存复算当新观测。

#### 第二实现证据包：有界取证协议（执行前记录）

独立反方建议先完成第二实现证据，再做 component 敏感性；主代理接受这一顺序。锁定 `me-foundation/msigner` 和其官方直接链接的文档/示例，不新增市场或任意交易窗口。本次使用 `github-research` 的实际源码阅读与结构对照方法；用户任务是验证既定实现，因此不执行该技能面向全生态的 50–200 仓库发现、打分和框架集成。

输入为 ORD.NET 官方锚点、冻结 666 个 Tier 1 和本轮 11 笔语义子样本。先固定官方仓库 revision，再完整核对 README、结算相关源码、测试与 fixtures；只读、不运行签名/广播代码、不调用钱包。寻找由官方来源直接提供的可解码 PSBT、交易 fixture 或 confirmed mainnet txid；要求能定位 seller input、对应收款 output、资产 outpoint/去向、签名路径与 hash type、dummy/padding 布局，并区分模拟 fixture 与主网事实。

输出为一张双实现证据卡，记录 revision、精确文件/行/交易位置、支持项和缺失项。代码证明构造可能性，不单独证明曾经成交；模拟 PSBT 不计作主网量或市场归属真值。若完成该官方材料包仍无法得到闭合的第二实现语义链，停止当前扩展并将 CP-13 标为数据/取证条件未满足，不用模板相似或任意扩大搜索补齐。该停止只说明当前公开证据和资源未过门，不证明第二实现不存在；Research Director 再据此与其他候选比较。

#### 第二实现证据包结果：机制成立，主网语义链未闭合

通过 GitHub connector 读取并固定 `me-foundation/msigner` commit `30499e1a8b352b8e4b6007450932be1a15b92955`（提交日期 2023-07-10）。核对该 revision 的完整目录、README、`src/signer.ts`、`src/constant.ts`、`src/interfaces.ts`、`src/util.ts`、feeprovider/fullnoderpc、package 配置、唯一测试 `test/signer.spec.ts` 及唯一文档示意图。只读源码，未安装或执行其测试、签名、广播和钱包操作。

| 证据项 | ORD.NET 官方示例 | msigner 固定源码/示例 |
|---|---|---|
| 卖方签名与路径 | 2-of-2 script path，卖方 0x83、平台 DEFAULT | `src/signer.ts:48` listing 构造，`:76` 0x83；Taproot internal-key 路径与其他地址分支 |
| 卖方 input/output | 官方主网 tx input/output 2；输入与收款脚本不同 | `src/constant.ts:2` index 2；`src/signer.ts:412` 加入 seller input/output |
| 资产落点 | 官方说明和主网交易结构，仍须独立索引核对具体 inscription | `src/signer.ts:394–406` output 0 吸收双 dummy 与已知 offset，output 1 收资产 |
| dummy 与输出值 | 平台 anchor 与 passthrough，不是同一双 dummy 模板 | 两个买方 dummy；默认 580–1000 sat、重建 600 sat、资产 postage 10,000 sat |
| 可直接核验的成交工件 | 官方给出 mainnet tx `0f2f22ed…ce40` | 唯一 fixture 为 `btc-signet`，没有完整签名 PSBT 或 mainnet sale txid |
| 可支持结论 | 此官方协议确实采用不同签名角色，旧 detector 会漏 | 第二套构造代码存在；不能单独证明本样本归属或主网成交 |

稳定来源：[msigner signer.ts](https://github.com/me-foundation/msigner/blob/30499e1a8b352b8e4b6007450932be1a15b92955/src/signer.ts)、[constants](https://github.com/me-foundation/msigner/blob/30499e1a8b352b8e4b6007450932be1a15b92955/src/constant.ts)、[tests](https://github.com/me-foundation/msigner/blob/30499e1a8b352b8e4b6007450932be1a15b92955/test/signer.spec.ts)。测试第 22 行明确是 signet，第 98–100 行的测试体只有 `true;`，并不运行或断言交易构造。README 没有主网成交链接，示意图没有 PSBT/txid；图 SHA-256 为 `4B607E8EE446254A632D5D549AC3D1CDA1B79F65D1C058219F27434CCB451BC3`。

**必须修正的旧解释**：本地 `msigner_default_template` 谓词只核对了双 dummy、部分 index/value/script，没有检查官方默认 `ORDINALS_POSTAGE_VALUE=10000`、真实资产 offset 或平台费用来源；同脚本 Tier 1 也比官方允许不同收款地址的实现更窄。固定 103 个匹配者中，output 1 为 10,000 sat 的仅 49 个，另外 54 个不是该默认参数的完整匹配。10,000 sat 条件也是必要而非充分条件，不能把 49 个重写为严格平台样本。参数可配置意味着另 54 个也不能断定不来自该软件。原始 JSON 和谓词保留用于复现；字段仅解释为“部分布局特征匹配”，历史“严格默认模板兼容”论断作废，不静默改计数。

复算方法：读取冻结 `cp13_pilot_v1_detector_v2.json`，筛选 `msigner_default_template == true`，按 `outputs[1].value` 分组；103 条中值为 10,000 的 49 条。该诊断不改变原先 11 条语义样本，不重抽，不作为新 detector 或 precision 估计。

独立只读复审再次重算得到相同的 103/49/54 分组，核对源码构造与验证侧常量，确认旧“严格默认模板”措辞过强。审查支持暂停裁决，同时明确不否定已经核验的结构与 witness 证据。历史文字中的模板解释已作显式更正，旧计数及冻结 JSON 不变。

**Research Director 裁决**：有界材料包没有补齐预定的第二实现闭合主网语义链，触发停止条件。CP-13 改为 `parked pending semantic ground truth`；保留机制、666 个结构候选、7 个已锚定 reveal 和反例证据，停止扩大样本、过滤器工程和 component 效应实验。该决定是当前证据/资源条件下的选择，不是证明机制无价值、没有市场活动或文献已经完全解决问题。若未来出现可直接连接的第二实现官方工件或可审计历史资产索引，才重开；否则继续比较其他数据已可用的候选，不因已有投入降低门槛。
