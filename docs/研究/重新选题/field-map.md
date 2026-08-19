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

其中 `Web19`、`Elm23`、`Bel24`、`Sch24`、`Son24`、`Kha26`、`Mag26`、`Mul26` 已完成首轮全文定位；其他条目仍需逐项核验规模、标签来源、时间可用性和限制。

## 替代检索新增的反证邻居

- `Mal26`：直接研究 transaction-level 与 actor-level AML 队列在固定预算下是否一致；与“单位一致的预算化评测”高度重合，必须全文反证。
- `2603.04328`（Algorithmic Compliance and Regulatory Loss in Digital Assets）：声称前向/滚动评估下静态分类指标高估监管效果；目前仅为检索摘要，需核验协议和独立性。
- `1906.12221`（Safeguarding the Evidential Value of Forensic Cryptocurrency Investigations）：从司法证据角度审视聚类启发式和 attribution tags；可约束实体解析方向的主张边界。
- `2403.00523`（Assessing the Efficacy of Heuristic-Based Address Clustering for Bitcoin）：直接评估聚类启发式；与下游误差传播方向构成最近邻。

这些条目由 Firecrawl/Tavily 发现，尚未因摘要而升入核心结论。

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
