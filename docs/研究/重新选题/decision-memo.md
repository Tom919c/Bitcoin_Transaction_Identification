# Research Direction Decision Memo

## 当前状态

**Decision: CONDITIONAL — Gate 1 已形成条件主方向，等待用户确认是否进入 Gate 2 证据可得性试验。**

现有 147 篇 deep-search 摘要提出“因果时间、跨数据集、有限调查预算下的风险排序基准”作为主方向，但该结论目前只视为待检验假设，不是项目决定。

独立反证检索和全文定位确认：`Mal26` 已直接覆盖 Elliptic++ 上的 transaction-to-address projection、native address queue、固定预算、严格时间协议、yield@budget、unknown burden、case fragmentation 与队列重叠；`Kha26` 已覆盖 Elliptic 的严格时间、Precision@k 与校准。因此，“单位一致的预算化队列评测”作为纯 benchmark/empirical 主方向暂列 **Provisional No-Go**，不再作为默认主方向。

此前保留的两个理论转向也已经完成红队审查：不完整/延迟标签下的效用识别被标准 PU、missing-data、selective-label 和 OPE 理论直接覆盖，判为 No-Go；严格时间化的地址聚类误差传播只在取得 union lineage、独立实体真值和真实高分尾部效应后才 Conditional Go。

只读可行性审计已经确认：当前 PostgreSQL 只有 `node_features` 与 `transaction_edges` 两张表；实体表仅保存聚合后的 `alias`、`cluster_size` 等字段，没有 address→entity mapping、聚类边、规则版本或历史 union events。仓库的数据构建代码也直接以 entity alias 为节点。因此，现有 252M 资产**不能重建** `H_t`，第二项已从“现有数据可做”降为“取得上游映射与可审计真值后才 Conditional Go”。这不是算力问题，而是信息已经在聚合时丢失。

独立理论红队进一步否决了第一个理论转向：MNAR 下观察等价、SCAR/SAR 恢复、propensity bounds 与基本部分识别区间均是成熟 PU/missing-data/selective-label/OPE 理论的直接应用。没有独立审计标签和调查日志时，它只能说明“公开标签不足”，不能构成新的理论主线，也不能识别真实调查效用。

新发现的“来源/同名实体捷径”也没有被直接升级为主方向。地址表审计确认 source-only accuracy 约 0.748，且随机地址切分中约 98.9% 的测试命名地址在训练集有同名实体；但当前发布资产缺失 `address→script→cluster/node` lineage，因此无法把地址行风险归因到最终 entity-node split。`Saf26` 已系统审计 Elliptic 的不透明特征与 split 隔离，`Real25` 已做未来日部署测试，`Dib26` 已做跨数据测试；只增加 source/group/time split 不足以形成顶会创新。CP-11 当前判为 Gate 2 No-Go，只有补齐 lineage、支持匹配和标签时间后才重审。

新增深检和独立来源核验又提供了三项决定性证据。第一，ORBITAAL 公开最终用户的地址列表与多尺度时间图，但用户 ID 来自对全时段共同输入图求连通分量并合并 WalletExplorer，且作者明确其构建代码不可复现；它不能提供历史 as-of union lineage。第二，NeurIPS 2025 的高保真 Bitcoin 时序异构图保留 Script、Transaction、Block 和 block-height 边，为从上游重建提供了可行参照。第三，`Len26` 已用 32,059,886 条多源地址标签直接研究地址与 cluster 标签冲突；因此“多源冲突消解”也不能单独作为新贡献。

独立 Devil's Advocate 随后否决了把上述组件拼成 CP-12 主线：Sch24、ORBITAAL、`Jal25`、`Len26`、`Saf26` 与 OGB/GOOD/TGB 已分别覆盖实体时间图、原始时序 ETL、多源冲突、透明度审计和通用评测规范；当前最终资产又无法反推出历史 union 和逐标签首次公开时间。CP-12 当前只能作为支撑层，不能靠“换 split 后重跑模型”获得顶会创新。

综合创新性、证据与可行性后，当前组合为：

- **条件主方向**：CP-04 与 CP-07 的组合——未来独立公开归因的前瞻恢复。研究在历史 `t0` 冻结图、seed 与候选全集后，有限预算排序能否提前找回后来被**独立原始证据**公开归因的单位。它只获准先做至少 3 个事件家族的档案、首见时间和来源依赖性 pilot；不得先训练模型，也不得称“未来犯罪预测”。
- **替代方向一**：CP-02，时间化实体映射误差传播与 decision-conditioned 稳定性；前提仍是可重建 union lineage、独立实体真值和真实高分尾部效应。
- **替代方向二**：CP-12，可追溯、严格时点的 entity benchmark；当前 No-Go as main direction，仅作为 CP-04 所需的最小 provenance 支撑层。只有 artifact 可发布且产生跨 cutoff 稳定的实质模型选择变化后才重审。
- **低风险 fallback**：CP-05，252M 实体类型标签的来源、噪声与严格时间/来源审计；主张限定为 entity type。若 CP-12 的重建或发布许可失败，则退回此方向，但它单独不足以支撑高质量顶会主线。
- **明确放弃**：普通固定预算队列、单纯 MIH 指标比较、把 entity type 重命名为 AML risk、没有新审计数据的通用 PU/MNAR 理论套用、缺失 lineage 时直接声称来源/同名实体泄漏，以及没有统一真值的跨链迁移。

## 决策输入要求

- 现有 147 篇完成元数据和摘要初筛。
- 至少 60 篇一手来源完成来源核验。**已达到最低数，但仍按饱和规则扩展。**
- 至少 30 篇完成正文证据审计，并将最终关键证据定位到稳定页/节/表/图。**正文审计数已达到 37；其中 29 篇的正式 PDF 页码映射尚未全部完成。**
- 五组独立补充检索完成；另完成“未来独立证据”和“provenance-preserving 重建”两组针对性深检。Undermind 与 Firecrawl/Tavily 两条独立检索链未发现同时固定历史候选全集、审计原始证据独立性并用未来确认做预算评测的公开工作；`Gom22`、`Che23`、`Real25`、`Ama26` 是 CP-04 的关键最近邻。CP-12 则被 `Saf26`、`Len26`、ORBITAAL、`Jal25` 与通用 benchmark 工作显著覆盖。
- 8–12 张候选问题卡完成。**已完成 12 张。**
- 排名前三方向完成多轮最近邻与同期工作反证搜索。
- Devil's Advocate 已否决 CP-03 和当前形态的 CP-12，把 CP-02 降为 Conditional，并将 CP-04+CP-07 列为优先的 Conditional Go；其未关闭风险是未来证据是否真正独立、首见时间是否可核验以及候选全集能否历史冻结。

## 最终输出槽位

- **推荐主方向**：CP-04 + CP-07（conditional；仅进入 Gate 2 archive/independence pilot）
- **替代方向一**：CP-02（blocked on new provenance/ground truth）
- **替代方向二**：CP-12（当前主线 No-Go；仅作 provenance 支撑，满足严格 artifact 门槛后再审）
- **低风险 fallback**：CP-05
- **明确放弃方向**：CP-01、CP-03、CP-10、CP-11；CP-09 在统一真值到位前 No-Go；CP-12 当前形态不得作为主线

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

Research Director 建议用户先确认是否允许 CP-04+CP-07 进入 Gate 2 archive/independence pilot。确认只授权至少 3 个事件家族的历史档案、证据传播链、首次公开时间、冻结 seed/候选全集与许可审计；在该门槛通过前，不训练模型、不冻结完整实验协议、不升级到 252M 级全图实验。CP-12 只实现 pilot 必需的最小 provenance，不单独启动全量重建。
