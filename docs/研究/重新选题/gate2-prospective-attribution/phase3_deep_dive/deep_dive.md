# Gate 2 Phase 3：全文证据笔记

## 1. `Gom22` — Watch Your Back

- **任务/数据**：从公开报告给出的 cybercrime seeds 出发，使用 back-and-forth transaction exploration 识别资金关系和新的 signaling addresses；标签库融合 WalletExplorer、Bitcoin-OTC、ransomware 等来源，并处理 exchange owner 与 beneficiary 的双重所有权。
- **协议**：§4–§6 构建标签、exchange classifier 和 operation oracles；Table 2 的 exchange 数据集经 MI clustering 扩张，随机 80/20 切分；Table 3 含 lifetime、末次交易等全生命周期特征。探索从既有报告 seeds 启动，没有为每个历史 cutoff 冻结候选全集、标签 registry 和特征。
- **主要证据**：§6.1 报告 Pony 等案例发现的新 signaling addresses；Tables 5、8、14 比较 back-and-forth 与 forward-only。§8 承认标签覆盖有限，且公开 abuse reports 可用于通知交易所。
- **对本项目的约束**：必须纳入 back-and-forth/forward-only 作为强非学习基线；“找到 seed 附近新地址”本身不新颖。论文发现的地址由 operation oracle 或同一调查链验证，不是严格的未来、来源独立 outcome；历史 `c` 后的信息隔离也不是其评测对象。
- **风险**：MI clustering、全生命周期 features 和公共 tag 数据若回填到历史时点会泄漏；随机 exchange-classifier split 不能证明前瞻有效性。

## 2. `Fro19` — Safeguarding Evidential Value

- **任务/贡献**：分析 CoinJoin 对聚类的影响以及错误/恶意 attribution tag 的法律和技术风险，提出 tag/cluster 的 provenance sharing framework。
- **主要证据**：引言和 §3 明确 CoinJoin 可能把无关实体合并为 super-cluster，错误 tag 可导致对无辜者的怀疑。§5.1–§5.4 与 Figures 4–5 要求记录 source、agent/investigator、生成 action、工具/heuristic、时间、hash/signature 和分类词汇；Listings 1–2 给出 JSON-LD 示例。§6 要求在线来源本地永久保存、披露 heuristics、概率、生成过程和来源可靠性。
- **对本项目的约束**：当前拟定的 provenance DAG 不是无先例的数据模型创新；可创新部分必须是把依赖图、first-public 区间与 source-family-held-out 变成可执行前瞻评测，并证明它改变结论。
- **风险**：该论文不提供来源独立性统计判据或历史 benchmark；我们不能把其规范性框架误写成已经验证的 causal independence。

## 3. `Paq18` — Ransomware Payments

- **任务/数据**：§3.1 从 APWG 获得 7,037 个 Locky 地址，另从 Michael Gillespie 维护的线程得到 139 个，并从安全研究博客/组织网页等得到 46 个；合计 7,222 个 seeds、67 个 ransomware families。
- **扩张**：§3.3 先去除未出现在链上的 100 个地址，剩 7,122 个、38 个 families，再用预计算的 multiple-input clusters 扩张；后续追踪 outgoing relationships 并估算收入下界。
- **标签语义**：seed 是来源声称与某 ransomware family 相关的收款地址；cluster 扩张地址是 heuristic inference，不是新的独立标签。论文估计的是已知 seeds/扩张簇可见的 lower-bound payments，不是完整犯罪率。
- **对本项目的约束**：提供可审计的历史 ransomware seed 来源，但来源发布时间、页面快照和上游引用关系未被设计为预测协议。一个 source list 的扩张结果不能作为另一个独立 outcome。
- **风险**：APWG 与论坛/博客可能共享上游样本；MI 错误和家族映射错误会按簇放大。只有能恢复原始页面及其当时版本的 family 才可进入 pilot。

## 4. `Ama26` — Underground Forum Addresses

- **任务/数据**：CrimeBB/HackForums 快照覆盖至 2024-09；提取并做链上格式/存在性验证后得到 23,882 个 Bitcoin 地址。§3.4 用 LLM 筛选 2,606 个候选，再由一位专家逐帖审阅，确认 2,438 illicit、98 licit、70 excluded。
- **时间字段**：Table 5 报告 first/last forum appearance 与 first on-chain transaction；§4.1 区分发帖时间和末次链上交易时间。该结构比固定地址标签更适合历史 cutoff。
- **佐证定义**：§4.2/Table 6 将 2,061 个具名类别地址分为 self-advertised、多个 independent users reported、single mention；837 个有多上下文，其中 325 个被多个用户报告。
- **限制**：作者明确只有一位专家，不能报告 inter-rater reliability；只人工验证二元标签，类别沿用 LLM；LLM 未选中的 21,276 个地址只抽样 200 个估计 screening recall。论坛在 2022 后公开地址急降，覆盖机制随时间变化。
- **对本项目的约束**：这是最接近可用的 prospective artifact，但“不同用户”不等于独立 root evidence；同一论坛转载、sockpuppet 或共同上游必须合并。当前公开仓库缺核心数据/代码时不能作为主 pilot。

## 5. `Shi25` — Real-CATS / Sup-CATS

- **数据**：Real-CATS 声称包含 90,612 个 Bitcoin 与 12,591 个 Ethereum criminal addresses，来自真实 abuse reports；benign 地址来自 exchange hot-wallet outputs。提供统计 profiles 和 transaction records。
- **future-day 评测**：§4.3 的 Sup-CATS 扫描 2024-08-12 当日 Ethereum blocks，使用 Etherscan 标注的 3,147 个 criminal addresses，并以 1% 概率抽样当日 unlabeled addresses 作为 11,058 个 benign；Table 6 报告 Real-CATS 训练模型的转移结果。
- **关键反证**：这不是未来独立归因。标签在构造测试集时已存在；未标注抽样被当作 benign；positive 与 negative 的采样来源机制不同。所谓 real-world transfer 是未来日期上的固定标签分类，不处理 first-public time、来源依赖或 right censoring。
- **artifact**：Open Science 声称 GitHub 公开 7 个 Real-CATS 文件、1 个 Sup-CATS 文件和交易记录；Phase 4 必须核查实际内容、版本和许可。
- **对本项目的约束**：普通 future-day split 已被覆盖；本项目只能声称恢复“后来公开佐证”，不能声称更准确地识别所有 illicit addresses。

## 6. `Mal26` — Queue Granularity

- **协议**：Elliptic++ 按 timestep 1–34/35–39/40–49 分 train/validation/test。transaction 与 address 两个 RF 只用已标记 licit/illicit 样本训练；unknown 排除。Path A 按 horizon 聚合 `timestamp <= t` 的 incident transactions；address graph 无 edge timestamps，所以不使用 causal address-GNN。
- **行动单位/指标**：对相同 active address universe 比较 transaction-projected 与 native address queues；§3.6 定义 Jaccard@K、RBO、burden decomposition、yield@K、case fragmentation 和 novel-positive rate，Platt calibration 用 validation split。约 66% test actors 无标签。
- **限制**：§5.4 明确 actor 只是 address，不是真实实体；单一数据集、RF、投影敏感、全局静态 address features、无时间戳 address graph；known-label yield 不是完整调查效用。
- **对本项目的约束**：时间切分、固定预算、unknown burden、队列单位和 case fragmentation 已被直接覆盖。我们的方向若没有未来独立 outcome 与来源 held-out，就是重复工作。

## 7. `Dha26` — Sequential Label Recovery

- **形式化**：把 authorization、reporting、label maturity 作为三个选择门，估计潜在 fraud state；§3.6 定义条件 maturity propensity，§3.8 在 sequential positivity、ignorability、bounded outcome 与 consistency 下识别 marginal fraud rate；§5 扩展到已知/可估 corruption rates。
- **关键假设**：Assumptions 8–11 要求各门 propensity 有正下界，且潜在结果在相应 history 条件下独立于 authorization/reporting/maturity。§3.7.1 明确私有风险信号、按 fraud severity 报告、或高置信案件更快成熟都会破坏 ignorability。
- **理论结果**：§3.6 的 Jensen penalty 表明异质 maturity 由 `E[1/p(H)]` 而非 `1/E[p(H)]` 控制；Theorem 35 给出依赖 propensity 下界与 corruption scaling 的 Bernstein concentration。
- **对本项目的约束**：把通用 delayed/selective-label estimator 套到公开 crypto 数据不构成创新。公开 OSINT 中 source selection、报道概率和模型可见信号高度相关，且 propensity/腐败率未知，因此真实 illicit probability 通常不可识别。
- **保留用途**：可借其术语说明为什么我们只报告 future-public-corroboration 的观察下界，并对 follow-up horizon 做删失敏感性分析；不采用其强假设来制造“已校正真值”。

## 8. `Web19` — Elliptic 原始基准

- **数据/任务**：§2 定义约 203k Bitcoin transaction nodes、234k directed flows、49 个时间步和 166 个特征；交易的 licit/illicit 标签取决于其输入地址控制实体所属类别，unknown 大量存在。
- **特征与协议**：公开说明包含本地 transaction features 与邻域聚合 features；比较 LR、RF、MLP、GCN，RF 表现更强。论文使用时间序列但目标是对既有 Elliptic labels 的 transaction classification。
- **对本项目的约束**：Elliptic 标签是情报公司依据实体类别赋给交易的派生标签，不提供公开 root-evidence、label discovery time 或独立 future corroboration。它不能作为本候选问题的 outcome，也不能把 unknown 当 benign。
- **风险**：后续 `Saf26` 对数据透明度/错误提出直接质疑；若用 Elliptic，只能作旧基线说明，不能承载主结论。

## 跨论文综合

1. **最接近的方法已覆盖**：seed tracing、early detection、future-day classification、strict temporal split、budget queue 和 provenance schema 分别已有强工作。
2. **仍可能独立的组合**：历史候选全集冻结、future first-public interval、root-evidence source families、source-family-held-out、right-censored case-level budget recovery。
3. **统计主张上限**：公开资料只能支持“未来公开佐证的观测恢复率下界”，不能识别真实 illicit probability，也不能把未报告者判负。
4. **数据硬门槛**：至少三个事件家族必须有可复核 `c` 前 seed、`c` 后原始归因、独立 root evidence、永久快照、case/address 映射和合法可复用条件；否则组合创新没有可执行 artifact，主方向 No-Go。
