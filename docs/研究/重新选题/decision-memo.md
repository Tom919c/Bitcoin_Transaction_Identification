# Research Direction Decision Memo

## 当前状态

**Decision: GATE 2 HOLD — CP-13 仍是首要候选，但 2026-08-31 解析器审查发现 witness 上下文错误，规模/结构晋级暂停；先修正复算，再检查跨市场真值与传播效应。**

下面列出的 838/662 等数值为保留的 detector-v1 历史结果，不得作为最终实证结论。已确认的错误包括合法 Taproot 签名与 control block 的外形碰撞，以及缺少 prevout/annex/脚本执行上下文核验。原始产物保持不变；修正后产物单独编号，同样本复算不宣称独立重复验证。

截至 2026-08-31，CP-13 的预注册 24 区块零模型 pilot 扫描 65,545 笔交易，得到 Tier 0 838 笔、Tier 1 662 笔；六个 control 区块为 0，后三个时期分别为 491、144、27。Tier 1 覆盖 123 个结构指纹；636/662（96.1%）因重复 output script 必然绕过已发表的 JoinMarket、Wasabi 与 Whirlpool 结构规则，101/662（15.3%）严格符合 Magic Eden Foundation `msigner` 默认模板。该结果通过预设的规模、跨时期、多模板与公开规则漏检门。

这仍不是论文结论。Tier 1 只表示链上结构与协作式 `SINGLE|ANYONECANPAY` 结算相容，不证明 inscription/Runes/其他资产类型、平台归属、独立现实所有人或真实 sale。Magic Eden 官方 block-activity API 当前连续返回 HTTP 503，不能据此把未验证记录计为无转移。CP-13 只有在至少两个公开实现中建立可审计的 Tier 2 语义，并显示非平凡 component/union 传播效应后，才可请求用户冻结为主方向。

BlackSuit/Royal 的精确链上 target-construction 子测试成功：原定 UTC 日内 1,182,309 个输出只有一个等额 candidate，±1 日三日合计 3,154,828 个输出仍只有该候选；两个冻结 `c` 前 registry 均不包含它。但 DOJ 公开材料遮盖 txid/address，日期按 `on or about` 理解，CS-1 和商业工具上游不可审计。独立 Devil's Advocate 因 construct validity、来源独立性 unknown、永久 artifact 与伦理风险判定完整 pilot No-Go，Research Director 接受该反证。详见 `gate2-prospective-attribution/phase6_decision/black-suit-pilot/pilot-result.md`。

Gate 2 已完成 51 篇去重证据库、8 篇全文深读、14 个事件/家族审计，以及 5 个外部 artifact 和本地 252M 图核验。结果为 0 个完整 Go 事件；BlackSuit/Royal、Upbit、Harmony、Twitter 仅 Conditional，其中前三个分别受目标映射或跨链/VASP 隐边限制，Twitter 规模过小。现有 252M 终态 entity graph 又缺 address/txid/block hash/address-to-alias lineage，不能承载地址级法律证据回填。因此 CP-04+CP-07 当前不得进入正式 benchmark 或模型开发。完整证据见 `gate2-prospective-attribution/phase6_decision/gate2-report.md`。

现有 147 篇 deep-search 摘要提出“因果时间、跨数据集、有限调查预算下的风险排序基准”作为主方向，但该结论目前只视为待检验假设，不是项目决定。

独立反证检索和全文定位确认：`Mal26` 已直接覆盖 Elliptic++ 上的 transaction-to-address projection、native address queue、固定预算、严格时间协议、yield@budget、unknown burden、case fragmentation 与队列重叠；`Kha26` 已覆盖 Elliptic 的严格时间、Precision@k 与校准。因此，“单位一致的预算化队列评测”作为纯 benchmark/empirical 主方向暂列 **Provisional No-Go**，不再作为默认主方向。

此前保留的两个理论转向也已经完成红队审查：不完整/延迟标签下的效用识别被标准 PU、missing-data、selective-label 和 OPE 理论直接覆盖，判为 No-Go；严格时间化的地址聚类误差传播只在取得 union lineage、独立实体真值和真实高分尾部效应后才 Conditional Go。

只读可行性审计已经确认：当前 PostgreSQL 只有 `node_features` 与 `transaction_edges` 两张表；实体表仅保存聚合后的 `alias`、`cluster_size` 等字段，没有 address→entity mapping、聚类边、规则版本或历史 union events。仓库的数据构建代码也直接以 entity alias 为节点。因此，现有 252M 资产**不能重建** `H_t`，第二项已从“现有数据可做”降为“取得上游映射与可审计真值后才 Conditional Go”。这不是算力问题，而是信息已经在聚合时丢失。

独立理论红队进一步否决了第一个理论转向：MNAR 下观察等价、SCAR/SAR 恢复、propensity bounds 与基本部分识别区间均是成熟 PU/missing-data/selective-label/OPE 理论的直接应用。没有独立审计标签和调查日志时，它只能说明“公开标签不足”，不能构成新的理论主线，也不能识别真实调查效用。

新发现的“来源/同名实体捷径”也没有被直接升级为主方向。地址表审计确认 source-only accuracy 约 0.748，且随机地址切分中约 98.9% 的测试命名地址在训练集有同名实体；但当前发布资产缺失 `address→script→cluster/node` lineage，因此无法把地址行风险归因到最终 entity-node split。`Saf26` 已系统审计 Elliptic 的不透明特征与 split 隔离，`Real25` 已做未来日部署测试，`Dib26` 已做跨数据测试；只增加 source/group/time split 不足以形成顶会创新。CP-11 当前判为 Gate 2 No-Go，只有补齐 lineage、支持匹配和标签时间后才重审。

新增深检和独立来源核验又提供了三项决定性证据。第一，ORBITAAL 公开最终用户的地址列表与多尺度时间图，但用户 ID 来自对全时段共同输入图求连通分量并合并 WalletExplorer，且作者明确其构建代码不可复现；它不能提供历史 as-of union lineage。第二，NeurIPS 2025 的高保真 Bitcoin 时序异构图保留 Script、Transaction、Block 和 block-height 边，为从上游重建提供了可行参照。第三，`Len26` 已用 32,059,886 条多源地址标签直接研究地址与 cluster 标签冲突；因此“多源冲突消解”也不能单独作为新贡献。

独立 Devil's Advocate 随后否决了把上述组件拼成 CP-12 主线：Sch24、ORBITAAL、`Jal25`、`Len26`、`Saf26` 与 OGB/GOOD/TGB 已分别覆盖实体时间图、原始时序 ETL、多源冲突、透明度审计和通用评测规范；当前最终资产又无法反推出历史 union 和逐标签首次公开时间。CP-12 当前只能作为支撑层，不能靠“换 split 后重跑模型”获得顶会创新。

综合创新性、证据与可行性后，当前组合为：

- **首要候选**：CP-13，Bitcoin 数字资产市场协作式结算对 common-input clustering 的系统性污染；文献与规模/结构门已通过，只允许继续跨市场真值与传播效应测量，不允许训练新模型。
- **已关闭方向**：CP-04 与 CP-07 的组合——未来独立公开归因的前瞻恢复。唯一获准的 BlackSuit/Royal pilot 无法取得公开一手 txid/address 或可核验独立 root evidence，触发预先写明的 No-Go；未来只有获得新的直接公开证据才可重审。
- **替代方向一**：CP-02，时间化实体映射误差传播与 decision-conditioned 稳定性；前提仍是可重建 union lineage、独立实体真值和真实高分尾部效应。
- **替代方向二**：M1，多观察点 mempool 分歧下的校准结果预测；研究上限较高，但必须先取得含预测时可见交易内容、费率、冲突/替换状态和多观察点时间戳的数据，或获批重新采集。现有公开 artifact 不足以公平比较强基线。
- **支撑层而非替代主线**：CP-12，可追溯、严格时点的 entity benchmark；当前 No-Go as main direction。CP-04 关闭后不再为其单独建设 provenance 支撑层。
- **低风险 fallback**：CP-05，252M 实体类型标签的来源、噪声与严格时间/来源审计；主张限定为 entity type。若 CP-12 的重建或发布许可失败，则退回此方向，但它单独不足以支撑高质量顶会主线。
- **明确放弃**：普通固定预算队列、单纯 MIH 指标比较、把 entity type 重命名为 AML risk、没有新审计数据的通用 PU/MNAR 理论套用、缺失 lineage 时直接声称来源/同名实体泄漏，以及没有统一真值的跨链迁移。

## 决策输入要求

- 现有 147 篇完成元数据和摘要初筛。
- 至少 60 篇一手来源完成来源核验。**已达到最低数，但仍按饱和规则扩展。**
- 至少 30 篇完成正文证据审计，并将最终关键证据定位到稳定页/节/表/图。**正文审计数已达到 37；其中 29 篇的正式 PDF 页码映射尚未全部完成。**
- 五组独立补充检索完成；另完成“未来独立证据”和“provenance-preserving 重建”两组针对性深检。Undermind 与 Firecrawl/Tavily 两条独立检索链未发现同时固定历史候选全集、审计原始证据独立性并用未来确认做预算评测的公开工作；`Gom22`、`Che23`、`Real25`、`Ama26` 是 CP-04 的关键最近邻。CP-12 则被 `Saf26`、`Len26`、ORBITAAL、`Jal25` 与通用 benchmark 工作显著覆盖。
- CP-13 focused deep search 已完成 22 篇近邻发现与 8 篇关键全文定向核验；独立 exact/component 检索未发现直接测量该交易族对 CIOH 污染的工作。该 absence 判断只绑定 2026-08-30 检索快照，不写成“首次”。
- 8–12 张候选问题卡完成。**已完成 12 张。**
- 排名前三方向完成多轮最近邻与同期工作反证搜索。
- Devil's Advocate 已否决 CP-03、当前形态的 CP-12 和 BlackSuit/Royal 完整 pilot，把 CP-02 降为 Conditional。CP-04+CP-07 因未来证据不能直接定位、来源独立性 unknown 和长期 artifact 不成立而关闭。CP-13 尚需在 Tier 2 与传播效应结果冻结后接受一次不继承当前推荐的独立反方审查。

## 最终输出槽位

- **首要候选（未冻结）**：CP-13（规模/结构门已通过；跨市场真值与传播效应门开放）
- **替代方向一**：CP-02（blocked on new provenance/ground truth）
- **替代方向二**：M1（blocked on prediction-time-complete multi-observer data or new measurement）
- **低风险 fallback**：CP-05
- **支撑层/明确放弃方向**：CP-12 当前形态不得作为主线；CP-01、CP-03、CP-10、CP-11 放弃；CP-09 在统一真值到位前 No-Go

## 已预先确定的放弃条件

- 把 11 类 entity type 直接宣传为 illicit activity 或 AML risk。
- 把 `-1` 未标注背景当作正常、负类或未知非法类。
- 只在随机 Elliptic 切分上提出新 GNN。
- 在测试集上反复选择阈值、模型或研究故事。
- 只有给定候选子图或纯合成数据上的 F1 改进，却声称真实 AML 部署价值。
- 无法说明预测时点、标签可得时间和图信息截止时间。
- 仅复现 `Mal26` 的交易/地址队列投影、固定预算指标或 Elliptic++ 协议。
- 仅重复评估 MIH 准确率，而没有严格时间、下游决策传播或非平凡性质。
- 只把通用 group/source/time split、终态信息不可用于历史预测或标准排名 margin lemma 当作理论创新。
- 无法发布/脚本复取完整 lineage，或小规模 pilot 不改变 coverage、模型排序和 `GNN−tree` 增益中的任何一项。
- 把不同 URL 当作独立证据，而没有追踪其共同原始报告、转载关系和首次公开时间。
- 把未来公开归因写成未来犯罪事实，把未确认候选当 benign，或让 `t0` 后信息进入候选全集。

## 用户确认 Gate

CP-04+CP-07 的人工确认 Gate 已执行并得到 No-Go。CP-13 现为唯一首要候选，但用户尚未被要求冻结主问题：下一步只授权补齐至少两个公开实现的 Tier 2 语义真值，并测量未过滤与 protocol-aware 过滤下的 union/component 传播差异。若任一硬门失败，CP-13 No-Go 并返回 CP-02、M1 或 CP-05；若两门通过并完成独立反方审查，再提交用户确认。此前不训练模型、不冻结完整实验协议、不升级到 252M 级全图实验。
