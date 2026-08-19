# 领域地图

> 状态：v0，发现级地图。用于组织检索，不代表已经完成全文核验或形成最终结论。

## 现有发现池审计

- 论文结果：147 篇；其中 146 篇元数据可正常解析。
- PDF：88 篇可用，59 篇不可用。
- `Han23` 标题元数据损坏，需要按 DOI 或正式页面修复。
- `Xia22` 与 `Xia22b` 疑似 BABD 预印本/正式版。
- `Sho26` 与 `Sho26b` 疑似同一 TMRugPull 记录。
- 2025–2026 年条目占比较高，preprint 和近期未知 venue 必须优先核验，不能因“新”自动提高权重。

## 核心任务轴

1. **实体类型识别**：预测 exchange、individual、mixer 等类别；不能自动解释为 illicit activity 或 AML risk。
2. **licit/illicit 分类**：以交易、地址或实体为单位进行监督风险分类。
3. **可疑子图与资金流**：识别 laundering pattern、flow、motif 或给定候选子图。
4. **调查队列与风险排序**：在有限人工调查预算下优化 Precision@k、Recall@k、case coverage 和 calibration。
5. **早期与开放世界发现**：在未知类型、标签延迟和行为漂移下识别新型风险。
6. **实体解析与地址聚类**：研究地址到实体的聚类误差及其对标签、切分和 AML 决策的影响。
7. **跨时间、跨数据集与跨链泛化**：验证模型排序、特征价值和图增益是否能迁移。

## 图与预测单位

- transaction node
- address node
- clustered entity node
- transaction/address interaction
- subgraph or laundering pattern
- investigation case or alert queue

同一指标在不同预测单位之间不可直接比较。候选问题必须明确预测单位、图单位、决策时点和 ground truth。

## 初始数据资源簇

- Elliptic transaction graph：`Web19`
- Elliptic++ address and transaction graphs：`Elm23`
- Elliptic2 labeled subgraphs：`Bel24`、`Son24`
- Schnoering–Vazirgiannis Bitcoin entity graph：`Sch24`（官方发表年份为 2025；工作区 cite key 保留旧年份编码）
- BABD address behavior data：`Xia22b`
- Ethereum heist、ransomware 与多链资源：`Wu24`、`Ara24`
- synthetic AML data and transaction generators：`Alt23`
- Real-CATS 与未来日 Sup-CATS：`Real25`
- ChainAbuse→Elliptic++ 跨数据测试与地址拓扑模型：`Dib26`
- 10M 多链地址标签数据：`Mba26`（5.3M 为启发式推断标签，不能与 4.7M validated labels 混写）
- HackForums 证据支持的 Bitcoin 非法地址：`Ama26`
- ORBITAAL 最终 entity-address pool 与多尺度时间图：`Coq25`
- 高保真 script/transaction/block 时序异构图：`Jal25`
- 32M 多源地址标签与冲突消解：`Len26`

当前已有 37 篇完成面向本研究问题的正文证据审计，详见 `dataset-task-evaluation-matrix.md`。其中 8 篇为 Undermind PDF 逐篇定位，29 篇为 Firecrawl 索引全文、出版社 HTML 或官方 PDF 的定向内文核验；后者在进入最终主张前仍须映射到稳定 PDF 页码。

## 替代检索新增的反证邻居

- `Mal26`：直接研究 transaction-level 与 address-level AML 队列在固定预算下是否一致；论文虽使用 actor 一词，其行动单位仍是 blockchain address，不是已解析的真实实体。与“单位一致的预算化评测”高度重合，已完成全文反证。
- `2603.04328`（Algorithmic Compliance and Regulatory Loss in Digital Assets）：声称前向/滚动评估下静态分类指标高估监管效果；目前仅为检索摘要，需核验协议和独立性。
- `Fro19` / `1906.12221`（Safeguarding the Evidential Value of Forensic Cryptocurrency Investigations）：从司法证据角度审视聚类启发式和 attribution tags；可约束实体解析方向的主张边界。
- `Sch24c` / `2403.00523`（Assessing the Efficacy of Heuristic-Based Address Clustering for Bitcoin）：直接评估聚类启发式；与下游误差传播方向构成最近邻。该键不得与 Scientific Data 数据集论文 `Sch24` 混用。
- `Sch23cj` / `2311.12491` 与 `Sto21` / `2109.10229`：CoinJoin 识别依赖协议实现、少量手工交易或启发式一致性，没有覆盖所有协议的完整真值；因此“CoinJoin-aware”只是一种误差缓解，不能作为实体映射无误的证明。
- `Coq25` / ORBITAAL：发布每个最终用户的地址列表、stream graph 和多尺度 snapshots，但其用户是对全时段共同输入图求连通分量后再与 WalletExplorer 合并；作者明确构建代码因硬件定制而不可复现。因此它能提供终态映射参照，不能直接提供 as-of union lineage。
- `Jal25`：NeurIPS 2025 数据集保留 Script、Tx、Block 节点和 block-height 边，避免先验实体聚合；可作为 CP-12 的上游重建底座，但论文没有提供 off-chain labels 或实体解析 benchmark。
- `Len26`：已直接覆盖多源地址标签冲突，构建 32,059,886 条标签并结合 truth discovery 与 MIH 处理地址/cluster 冲突；未评测严格时点的标签迁移、下游 split 或模型排名。CP-12 必须超越“冲突消解”本身。

上述条目均已回到正文内文；其中仍为 preprint 的工作必须保留出版状态，且最终数值主张需用正式 PDF 页码复核。

## 评测风险轴

- random split 与 chronological split 的模型排序差异
- 预测时点之后的边、特征或聚合统计
- 同一实体、同一案件或相关地址跨 split
- 选择性标签披露和未标注样本语义
- 闭集假设与容易负样本
- 极端类别不平衡和只报告 accuracy/F1
- 缺少 tabular、tree、rule 和 heuristic baselines
- 测试集调参、校准或阈值选择
- synthetic-to-real 与 cross-dataset 迁移缺失
- 候选子图已给定造成的任务简化

## 当前候选问题簇，仅用于补检索

- 严格时间、单位一致、有限预算的调查队列评测。
- 地址聚类不确定性如何传播到标签、切分和 top-k 风险队列。
- 标签公开延迟下的事件种子前向发现，而非“未知犯罪预测”。
- 保持 PU 语义的时序主动调查。
- 跨链迁移失败的任务、标签和图语义 taxonomy。

这些不是最终推荐。摘要级审计显示 `Mal26`、`Kha26`、`Pha26` 等近期工作可能已经覆盖首个方向的大块内容；若跨数据集、label-time 和 case-action 单位不能形成实质差异，该方向应被否决。

## 当前证据缺口

- 首轮 147 篇来自一个综合检索，存在单一提示词锚定和确认偏差。
- 尚未证明有限预算风险排序具有可获得的真实 ground truth。
- 需要寻找图方法在严格协议下仍有独立增益的反证，而非只寻找失败案例。
- 需要建立正式版本与 preprint 的去重映射。
- Undermind PDF 阅读曾出现传输错误；失败不能被误记为完成全文核验。

## 理论组件反证结果

- `Bek18sar` 与 `Bek19` 已分别形式化 SAR 和超越 SCAR 的 biased-PU 学习；`Fur22` 进一步讨论 posterior 与 propensity 的联合可识别条件。由此，选择性公开标签下的 SCAR/SAR 恢复、propensity 修正和基本不可识别性不能作为新的 Bitcoin 理论贡献。
- `Noc21` 已从一般监督学习角度研究 record-linkage error 对下游学习的影响及 margin 缓冲。因此，实体解析方向不能声称“首次研究 linkage error 对 ML 的影响”；唯一可能的差异是 as-of Bitcoin partition、错误集中于高优先级尾部、以及真实队列稳定性证据的联合。
- 当前两个理论 pivot 均已降级：CP-03 为 No-Go；CP-02 只有在取得可重建 union lineage、独立 entity truth 和真实高分尾部效应后才 Conditional Go。
- 普通 benchmark hygiene 也不是理论创新：终态 partition 的非预见性、类别支持缺失和平均误差不控制尾部决策均可作为协议检查，但不能单独充当顶会定理。CP-12 的成立依赖可发布 artifact 与改变既有结论的实证 finding。

## 标签来源与同名实体反证

- 本地 `addresses.csv` 的 103,581 个非空类别地址中，source-only 随机切分准确率约 0.748，但 macro-F1 仅约 0.381；来源是强 coverage/selection signal，不等于模型已经直接读取来源特征。
- 39,047 个带类别且有实体名称的地址只对应 697 个名称；地址行随机切分下约 98.9% 的测试命名地址可在训练集找到同名实体。该结果证明 raw-address 评测的 identity lookup 风险，不能外推为 34,098 个 entity nodes 已泄漏。
- 当前缺失 `address→script→cluster/node` lineage、冲突丢弃日志和 node-level source/time 字段；这是从地址表诊断到实体图结论之间不可省略的推断桥。
- `Saf26` 已对 Elliptic 做透明度与 split 隔离审计；`Real25` 已构造未来日 Sup-CATS；`Dib26` 已做跨数据测试。因此 CP-11 只有在发布可审计 lineage、support-matched source/identity/time splits 并复算模型排名时才可能恢复新颖性，当前为 No-Go。
- CP-11 的诊断、CP-02 的 as-of clustering 和 CP-05 的标签审计现合并为 CP-12；组合后的增量必须由同一可重放 lineage artifact 支撑，不能把三个普通审计简单拼接成贡献。

## 独立反方审查后的条件主方向

- CP-12 经反方审查降为当前主线 No-Go：Sch24、ORBITAAL、`Jal25`、`Len26`、`Saf26` 与 OGB/GOOD/TGB 已覆盖绝大多数组件，当前发布资产又不能反推出历史 union 与逐 claim 首次公开时间。它只保留为最小 provenance 支撑层。
- CP-04+CP-07 升为条件主方向：在 `t0` 冻结 seed、链上快照和候选全集，以未来且与 seed/候选生成无共同原始证据的公开归因作为 right-censored positive，衡量有限预算下的前瞻恢复。
- `Gom22`/Watch Your Back、`Che23`/Evolve Path Tracer、`Real25` 和 `Ama26` 分别覆盖 seed 扩张、早期检测、未来日测试和证据标签，但当前检索未发现把候选历史冻结、来源依赖审计和未来独立确认合为同一 protocol 的工作。
- 最大风险不是模型，而是证据独立性：不同 URL 可能复制同一原始报告；未来公开时间可能只是旧事实的延迟转载。Gate 2 必须先通过至少 3 个事件家族的档案与传播链审计，不能先训练模型。
