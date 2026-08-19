# Gate 2 重新进入记录

## 决策目标

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

Zotero item key 与 BibTeX citation key 是两套标识；后续同步 `references.bib` 时以 citation key 为 Git 侧主键。
