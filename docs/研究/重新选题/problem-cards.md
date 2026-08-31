# Candidate Research Problem Cards

> 状态：Gate 2 第三轮候选反证中。CP-13 完成 detector-v2 原样本诊断复算；规模信号仍存在，跨市场语义、独立 prevout 核验和传播效应硬门开放。v1 数字仅保留为已纠正的历史结果。

## 问题卡结构

### CP-XX — 候选问题名称

- **Research question**：
- **Falsifiable hypothesis**：
- **Operational decision and stakeholder**：
- **Prediction unit and graph unit**：
- **Ground truth and label availability time**：
- **Why it matters**：
- **Nearest prior work**：
- **Actual gap rather than implementation gap**：
- **Minimum decisive experiment**：
- **Strong baselines and heuristics**：
- **Primary and secondary metrics**：
- **Data availability**：
- **Single-machine feasibility and engineering cost**：
- **Contribution type**：benchmark、empirical、data/label、method、workflow 或必要组合
- **Failure condition**：
- **Ethics and misuse risk**：
- **Strongest reviewer rejection argument**：
- **Evidence status**：

## 评分

| 维度 | 分值 |
|---|---|
| 问题重要性 | 1–5 |
| 证据质量 | 1–5 |
| 可行性 | 1–5 |
| 基础得分 | 三项乘积 |

以下不计分，直接 No-Go：

- 标签不能支撑主张。
- 存在无法消除的未来信息泄漏。
- 与已有工作高度或完全重合。
- 只是模型模块堆叠或随机切分刷分。
- 没有可信评测、强基线或最小可判别实验。

## 当前组合排序

| 排名 | 候选 | 重要性 | 证据质量 | 可行性 | 乘积 | 当前决定 |
|---:|---|---:|---:|---:|---:|---|
| 1 | CP-13 Ordinals/数字资产市场协作式结算对地址聚类的系统性污染 | 5 | 3 | 4 | 60 | **首要候选；修正复算完成，真值与传播门开放** |
| — | CP-04 + CP-07 未来独立公开归因的前瞻恢复 | 5 | 4 | 1 | 20 | **BlackSuit/Royal 完整 pilot No-Go；方向关闭** |
| 2 | CP-05 252M 实体类型标签审计 | 3 | 4 | 4 | 48 | 低风险 fallback；不足以单独支撑顶会主线 |
| 3 | CP-12 可追溯、严格时点的 Bitcoin 实体图 benchmark 重建 | 5 | 5 | 1 | 25 | 当前 No-Go；CP-04 关闭后不单独建设 |
| 4 | CP-06 PU 条件下的主动调查 | 4 | 2 | 3 | 24 | 数据到位前暂缓 |
| 5 | CP-02 时间化实体映射误差的下游传播与认证 | 5 | 4 | 1 | 20 | 理论窗口存在，但当前数据门槛失败 |
| 6 | CP-07 事件种子后的严格时间前向发现 | 4 | 2 | 2 | 16 | 已并入 CP-04，不独立推进 |
| 7 | CP-08 开放世界的可拒识告警 | 4 | 2 | 2 | 16 | 暂缓 |
| — | CP-03 选择性/延迟标签下 top-k 效用的部分识别 | 5 | 5 | 1 | 25 | **标准理论覆盖，当前硬 No-Go** |
| — | CP-11 来源/同名实体捷径与评测有效性 | 4 | 5 | 1 | 20 | **推断桥缺失，当前 Gate 2 No-Go** |
| — | CP-09 跨链迁移失败 taxonomy | 4 | 2 | 1 | 8 | 当前 No-Go |
| — | CP-01 普通固定预算队列 | 4 | 5 | 5 | 100 | **直接重合，硬 No-Go** |
| — | CP-10 单纯聚类准确率比较 | 3 | 5 | 4 | 60 | **直接重合，硬 No-Go** |

硬重合和理论直接覆盖优先于乘积分数；高分但已有标准结论或缺失必要数据的方向不能进入推荐组合。CP-04+CP-07 的 BlackSuit/Royal target-construction 虽在 ±1 日保持唯一，但公开法律材料遮盖 txid/address，来源独立性不可核验，完整 pilot No-Go。CP-13 修正复算保留规模信号，但还不是正式 Go；在跨市场真值和聚类传播效应完成前，不得开始新模型开发。

## 创新性反证协议

排名前三的方向至少执行三轮、最多十轮搜索：

1. exact formulation/direct match
2. component match
3. same application with different methods
4. same method in adjacent applications
5. concurrent 2024–2026 peer-reviewed work and preprints

任一最近邻达到 High 或 Exact overlap 时，默认判为 not novel；除非贡献类型在数据、评测或可证伪发现上存在实质差异，并能经独立反方审查。

## CP-01 — 预算化 AML 队列与行动单位一致性

- **Research question**：交易级风险分数投影到地址级行动队列后，固定调查预算下的队列组成和收益是否保持？
- **Nearest prior work**：`Mal26` 已在 Elliptic++ 上直接比较 transaction projection 与 native address scoring，使用严格时间段、固定预算、yield@budget、unknown burden、case fragmentation 和队列重叠；`Kha26` 已覆盖交易级严格时间、Precision@k 与校准。
- **Current decision**：**Provisional No-Go**。仅重复“单位不一致 + 预算指标 + 严格时间”属于高度或完全重合。
- **Only defensible pivot**：研究标签观察不完全、标签延迟和聚类误差下，真实队列效用是否可识别，以及在何种假设下可给出界或排序保持条件。
- **Strongest rejection argument**：地址不是 beneficial owner 或真实案件单位；公开标签 unknown 比例高；没有独立结案标签时，observed yield 不能证明 operational utility。
- **Evidence status**：`Mal26`、`Kha26` 全文定位；现实工作流来源仍需继续全文核验。

## CP-03 — 选择性、延迟标签下预算队列效用的可识别性

- **Research question**：在公开链上标签稀疏、延迟或选择性披露时，固定预算 top-k 队列的真实正例率或案件收益何时可识别，何时只能给出条件性区间？
- **Falsifiable hypothesis**：可构造相同观测分布、但真实队列收益或方法排序相反的两个完整数据世界；因此 observed-label yield 不能无条件证明 operational utility。
- **Operational decision and unit**：分析员从地址、交易或案件中选择预算为 `k` 的队列；每个实验只允许一种行动单位。
- **Nearest prior work**：`Mal26` 覆盖严格时间、固定预算、transaction→address projection、yield/unknown burden/case fragmentation；`Kha26` 覆盖 causal features、Precision@k 和 calibration。新缺口必须是效用 estimand 的可识别性，而非新模型或指标。
- **Objects**：对单位 `i`，令 `Y_i∈{0,1}` 为目标结果，`R_i∈{0,1}` 为截至决策时点标签是否可见，`S_i` 为排序分数，`X_i` 为可见协变量，`Q_k(S)` 为预算队列；观测量为 `O_i=(X_i,S_i,R_i,R_iY_i)`，目标为 `U_k=E[Y_i | i∈Q_k]`。
- **Baseline sharp bounds without assumptions**：`E[R Y | Q_k] ≤ U_k ≤ E[R Y | Q_k] + P(R=0 | Q_k)`。这是直接的缺失结果界，只能作基线，不应宣称为新定理。
- **Non-identifiability construction**：在 `Q_k` 内存在未观测标签时，保持所有 `R=1` 单位不变；分别令未观测单位的 `Y=0` 或 `Y=1`，即可得到相同 `O` 而不同 `U_k`。对两个队列在各自未观测质量足够大时，可进一步构造真实排序反转。
- **Possible recovery assumptions**：SCAR/SAR、已知或有界 propensity、外部随机审计样本、单调选择、延迟分布上界或 sensitivity parameter；每项都必须说明在公开链场景中如何检验或为何只能假设。
- **Minimum decisive experiment**：在 Elliptic 与 Elliptic++ 原生任务内分别比较 naive yield、SCAR/IPW、Manski/单调性界和敏感性曲线，报告哪些方法对能被认证排序；不得合并不同数据集标签。
- **Metrics**：识别区间宽度、可认证支配比例、排序可反转率、随预算和假设强度变化的 sensitivity frontier。
- **Data and feasibility**：不需要运行 252M 全图，单机可行；但没有外部审计样本时只能给条件性/部分识别结论。
- **Contribution type**：理论性质 + evaluation protocol + empirical sensitivity audit。
- **Failure condition**：组件级搜索发现已有工作已给同一 estimand、观察机制和 sharp bounds；或所有可辩护假设下区间都宽到无法产生决策结论。
- **Ethics**：区间不等于真实犯罪率；不得把选择性标签修正结果用于个体归因。
- **Strongest reviewer rejection argument**：只是 textbook missing-data/PU 理论换了应用名。必须证明 crypto AML 的行动单位、公开标签披露和时间语义产生了新的可检验结构或新的 benchmark finding。
- **Independent theory red-team**：MNAR 下观察等价、SCAR/SAR 恢复、propensity bounds 和队列支配证书都属于成熟 PU/missing-data/selective-label/OPE 理论的直接应用；仅替换成 Bitcoin 名词不是理论创新。若目标改成调查潜在结果 `Y(1)`，还需要 action/logging propensity 与稳定调查流程，现有公开标签更不支持。
- **Current decision**：**No-Go as theory main direction**。只有新建带标签来源、首次可得时间、独立盲审和预注册调查 outcome 的数据资源后，才可作为 data/benchmark 贡献重新评估。

## CP-02 — 时间化实体解析不确定性下的队列稳定性

- **Research question**：在严格信息截止和地址到实体映射不确定性下，何时实体级 top-k 调查队列可被认证为稳定？
- **Falsifiable hypothesis**：使用终态聚类、只报告有标签地址上的 pairwise 指标或忽略高优先级簇的异质误差，会系统性低估实体级标签、split 和 top-k 队列的不确定性。
- **Nearest prior work**：`Mul26` 已用 7 家 CASP ground truth 证明 MIH 的 label-restricted pairwise 指标与完整簇指标差异显著；`Mos21` 研究 change ground truth 与 cluster collapse；`Fro19` 研究 CoinJoin 导致的法证误解释；`Sch24c`（arXiv:2403.00523）评估多种 heuristic 与时间演化。现有工作尚未直接给出严格时间化的下游 queue propagation 与认证条件。
- **Actual gap**：不是再次评测 MIH，而是把可审计的 clustering uncertainty、future merge、风险分数间隔与 decision stability 连接起来。
- **Minimum decisive experiment**：先核查 252M 数据是否保留 address→entity provenance 和历史 union events；再在至少一套外部 ground truth 上重建 `H_t` 与终态 `H_T`，测 post-cutoff merge、跨 split overlap、label contamination 和 top-k 反转。
- **Strong baselines**：address-level no-clustering、MIH/change heuristic、CoinJoin-aware variants、终态聚类、时间截断聚类、随机/最坏情况扰动。
- **Metrics**：full-cluster per-entity precision/recall、post-cutoff merge rate、top-k Jaccard、case coverage 区间、ranking regret、按 score/cluster-size 分层的误差与 CVaR。
- **Feasibility gate**：必须能得到时间化映射或重建 union events，并取得至少一套可审计 ground truth；否则 No-Go。只读审计已确认当前数据库和 73.6 GB dump 都仅含聚合后的 `node_features`、`transaction_edges`，没有 mapping/union lineage；`addresses.csv` 也没有 cluster alias 或 union height。因此当前资产未过 Gate。
- **Contribution type**：理论性质 + evaluation protocol + empirical stress test；不是新 GNN。
- **Strongest rejection argument**：Mul26 已覆盖聚类可靠性；若没有真实下游标签、公开 ground truth 或非平凡理论，只是把误差注入现有模型。
- **Current decision**：**Conditional Go only if new upstream data are obtained**，尚未进入实验；不得把重建成本误写成“已有数据可行”。

### TP-02 — 标签受限聚类可靠性的不可识别性

- **Candidate**：只在有 ground truth 的地址子集 `S` 上评价 partition `H` 时，可构造在 `S` 上完全相同、但对未标注地址 `U` 的真实归属不同的两个世界，使完整簇污染与下游 queue precision 从接近 1 变到接近 0。
- **Recovery condition**：完整簇真值，或独立分层抽样并知道标签缺失机制。
- **Observable implication**：仅报告 label-restricted pairwise score 不能认证实体风险队列；必须做按簇、分数和簇大小分层的审计与敏感性区间。
- **Novelty status**：与 `Mul26` 的完整簇审计高度邻近；本命题本身不足以成为主定理，只能服务于 decision-conditioned empirical finding。

### TP-03 — 终态聚类用于历史预测的非预见性

- **Candidate**：单调 union-find 聚类中，若地址在时点 `t` 分离、但在终态 `T` 因 `t` 后交易合并，则任何用终态 partition `H_T` 聚合历史时点 `t` 的实体特征、标签或 split 都可能包含未来信息。
- **Exception**：不使用实体聚合，或能证明所有相关合并均发生在 cutoff 前。
- **Observable implication**：比较 `H_t` 与 `H_T`，报告 post-cutoff merges、跨 split 实体重合和队列变化。
- **Novelty status**：这是时间可测性的直接推论，属于协议正确性要求，不是可单独投稿的理论贡献。终态 grouping 若只用于构造更严格且不进入训练/特征的 split，不一定构成泄漏。

### TP-04 — 聚类污染下 top-k 排名稳定的充分条件

- **Candidate**：若单地址特征范数有界为 `B`，实体均值特征的污染比例为 `eta`，评分函数为 `L`-Lipschitz，则分数扰动可由 `2LB eta` 控制；若第 `k` 与 `k+1` 名真实分数间隔 `gamma > 4LB eta`，top-k 可保持不变。
- **Boundary**：max/sum 等无界聚合、分裂误差或无界特征可破坏该界；一般 top-k margin lemma 本身不是创新，贡献必须来自可审计 cluster contamination 与真实协议的连接。
- **Status**：标准 robust-ranking/margin diagnostic，不能作为主定理。唯一可能更有价值的理论种子是：即使全局 pairwise F1 任意接近 1，少量集中在高分尾部的错误 merge 仍可让真实与估计 top-k 完全不相交；但该构造仍需真实 Bitcoin 高杠杆 merge 证据才能形成贡献。

## CP-04 — 未来独立公开归因的前瞻恢复

- **Research question**：在历史时点 `t0` 冻结链上图、种子和候选全集后，模型能否在有限预算内，把后来由独立原始证据公开归因的地址/实体排到前列？
- **Falsifiable hypothesis**：相对只按 seed 邻近性的 temporal BFS/规则基线，至少一种不使用 `t0` 后信息的方法能稳定提高 `independent-confirmations@B` 或提前量；如果优势只来自同一报告的延迟转载、未来候选生成或把未确认样本当负类，本假设失败。
- **Formal target**：`C(e,t0)=g(e,G≤t0,X≤t0)` 为在 `t0` 已存在且由冻结规则产生的候选全集；只有候选 `i` 在 `(t0,t0+H]` 获得与 seed、候选生成路径和训练标签**没有共同原始证据**的时间锚定公开确认时，`Y_i^ind(t0,H)=1`。未确认候选保持 unlabeled/right-censored。
- **Operational decision and unit**：给定已知事件/家族 seed 后的地址或 as-of entity 调查队列；严格表述为 `prospective recovery of independently corroborated public attributions`，不是预测未来犯罪或未知事实。
- **Nearest prior work**：`Gom22`/Watch Your Back 已从已知 campaign seed 做双向资金关系扩展；`Che23`/Evolve Path Tracer 与 intention-discovery 工作覆盖早期恶意地址方法；`Real25` 提供未来日 Sup-CATS；`Ama26` 提供论坛证据标签候选。当前两条独立检索链未发现同时固定 `t0` 候选全集、审计原始证据独立性并以未来确认作有限预算评测的公开工作。
- **Actual gap**：不是再做 chronological split，而是把 `event time / first-public time / collection time / source-dependency` 与 candidate generation 一并冻结；贡献应是可复核的事件档案、独立性判据、right-censored/PU 评测和一个经强规则基线检验的 benchmark finding。
- **Minimum Gate 2 pilot**：先选至少 3 个不同历史事件家族，不训练模型；每个必须有冻结 seed、`t0` 链上快照、候选生成日志、至少一条未来独立原始证据及其传播链。只有档案门槛通过后，才比较 temporal BFS/规则、非图 tabular 打分和一个简单 link model。
- **Metrics**：`independent-confirmations@B`、Recall@B、unknown burden、lead time、case/source diversity、候选集合覆盖和 right-censoring sensitivity；不得把 unlabeled 当 false positive 计算普通 precision。
- **Data and feasibility**：当前最大风险是证据可得性。HackForums 论文声称发布时间元数据和 pipeline，但仓库截至核验时只有 README/TODO；ChainAbuse、Ransomwhere、法院/执法公告和 Wayback 记录需逐 claim 审计，URL 不同不等于来源独立。
- **Contribution type**：dataset/benchmark + evaluation protocol + empirical finding；若不能构建独立未来证据 artifact，则 No-Go。普通标签延迟、PU/MNAR 或时间切分理论不计创新。
- **Failure / No-Go**：没有可核验首见时间；未来标签是 seed attribution 的复制；seed/候选/未来标签来自同一标签包；少于 3 个独立事件家族；无法冻结 `C(e,t0)`；或强 temporal BFS 已解释全部收益。
- **Ethics**：只使用已公开且可追溯的原始证据；公开确认不等于法律定罪；对个人地址避免新增去匿名化，不对未确认项作无罪或低风险判断。
- **Strongest rejection**：所谓 future label 只是原有 seed 的延迟转载；候选由 seed 邻域生成，模型只学习邻近性，未确认又不是负类，因此“发现”和 precision 主张均不成立。
- **Score / decision**：5×4×1=20；**完整 pilot No-Go，方向关闭**。只有新的公开一手 txid/address 和可核验独立 root evidence 到位才可重审。

## CP-05 — 252M 实体类型标签的来源、噪声与时间审计

- **RQ / hypothesis**：11 类 entity-type 标签的来源链、证据时间和类别相关噪声是否足以支持有限的实体类型分类主张？随机 node split 是否夸大未来/来源外泛化？
- **Operational unit**：heuristic entity；明确不是 illicit、fraud 或 AML risk。
- **Nearest work / gap**：`Sch24` 已构建数据和原始分类任务；唯一可辩护差异是可复查的 provenance/time/noise audit，不是再加 GNN。
- **Minimum experiment**：按来源与类别分层抽样追溯，做独立复核；比较随机、严格时间和来源隔离切分，加入置信度过滤与 abstention。
- **Metrics**：证据可追溯覆盖率、分层一致性、噪声区间、模型排名变化。
- **Feasibility / failure**：现有资产可用，成本低至中；若原始来源和处理记录不可重建，贡献只能是局限性报告。
- **Ethics / rejection**：避免重新识别论坛个人；最强拒稿理由是“只是 dataset documentation”。
- **Score / decision**：3×4×4=48；低风险 fallback。

## CP-06 — PU 条件下的主动调查与 outcome logging

- **RQ / hypothesis**：只有被调查单位才获得 outcome 时，忽略选择 propensity 的主动策略是否在机制变化后过度自信并降低未来 yield？
- **Operational unit**：有调查动作、时间、结案结果和标签延迟的序列案件；不能把 unknown 当负例。
- **Nearest work / gap**：`Lor20` 是标注预算而非调查结果预算；`Mal26` 是单轮队列。真正差异必须来自 logged outcomes 与 sequential selection bias。
- **Minimum experiment**：先取得合格日志，再做 prequential replay，比较 random、greedy、uncertainty、PU、propensity-aware 与 doubly robust 策略。
- **Feasibility / failure**：当前没有确认的公开数据；用纯仿真冒充真实 AML 即 No-Go。
- **Score / decision**：4×2×3=24；数据到位前暂缓。

## CP-07 — 事件种子后的严格时间前向发现（并入 CP-04）

- **RQ / hypothesis**：给定在 `t_0` 已确认的事件种子，只用 `t_0` 前可见信息扩展未来关联单位时，现有候选子图/推荐方法的收益是否显著下降？
- **Operational unit**：地址、交易或事件子图三选一；表述为 seed-conditioned expansion，不是未知犯罪预测。
- **Nearest work / gap**：`Bel24`、`Son24` 使用已构造候选；`Paq18`、`Wu24` 从已知事件种子追踪。缺口仅可能在可部署 candidate universe 与严格 seed-time cutoff。
- **Minimum experiment**：重建候选生成时间，比较原协议与 strict `t_0` 协议；基线为规则扩展、temporal walk 和 time-restricted link model。
- **Metrics**：Recall@B、独立 case coverage、首次发现延迟、候选泄漏率。
- **Failure / rejection**：种子、标签或候选由未来生成即停止；最强拒稿理由是“换切分重跑 Elliptic2，仍无 open-world ground truth”。
- **Score / decision**：4×2×2=16；不再独立推进，其 candidate-generation 部分作为 CP-04 的强基线与失败检查。

## CP-08 — 开放世界风险告警的可拒识与不确定性陈述

- **RQ / hypothesis**：在 unknown 既非负类也非“未知非法”的条件下，能否对只在证据充分时输出的选择性预测给出可靠 coverage-risk 结论？
- **Nearest work / gap**：现有 crypto open-world 命中多是 held-out known class 或 seed tracing；真正 delayed independent confirmation set 尚未确认。
- **Minimum experiment**：取得有时间戳的独立裁决样本，比较 threshold、selective classifier 和 conformal/abstention；报告 coverage、selective risk 和校准。
- **Failure / ethics**：无独立后验真值即 No-Go；“拒识”不能被解释为低风险。
- **Score / decision**：4×2×2=16；暂缓，且可能与 CP-03 重叠。

## CP-09 — 跨链迁移失败 taxonomy

- **RQ / hypothesis**：Bitcoin 与 account-based chains 之间的失败是否主要由标签、行动单位、图语义和时间差异解释，而不是模型容量？
- **Minimum gate**：先证明至少两套数据的标签含义、时间与行动单位可比；当前没有合格统一真值。
- **Experiment if gate passes**：单链、无迁移和 domain-generalization 基线；按 label/unit/time/graph 分解失败，报告跨时间和跨链性能与校准。
- **Failure / rejection**：异质标签硬对齐后把性能下降称为“泛化失败”没有科学意义。
- **Score / decision**：4×2×1=8；当前 No-Go。

## CP-10 — 单纯 MIH 或聚类准确率比较

- **RQ**：某启发式是否比 MIH 更准确？
- **Direct overlap**：`Mul26` 已用 7 家 CASP ground truth 评估 MIH；`Mos21`、`Sch24c` 也覆盖启发式、change ground truth 与时间演化。
- **Why no pivot here**：增加一个聚类指标、CoinJoin filter 或 GNN 仍是增量工作；它只能作为 CP-02 的前置诊断。
- **Strongest rejection**：exact overlap，且 ground truth 受限。
- **Score / decision**：3×5×4=60；硬 No-Go。

## CP-11 — 标签来源、同名实体复用与评测有效性

- **Research question**：在严格切断地址到脚本再到聚类节点的标签迁移链、同一现实命名实体、标签来源和标签可得时间后，252M 实体图上 GNN 相对 feature-only GBC 的增益是否仍存在？
- **Falsifiable hypothesis**：原始地址表的随机切分会被来源和同名实体复用显著抬高；但该现象是否传递到最终 34,098 个 labeled nodes，必须依赖可审计 lineage 才能检验。
- **Verified pilot**：103,581 个非空类别地址中，source-only 随机切分 accuracy 为 0.748、macro-F1 为 0.381；39,047 个带类别且有命名实体的地址只对应 697 个名称，随机 40/30/30 下测试命名地址在训练集出现同名实体的比例约 0.989，name lookup accuracy 约 0.987。另有 1,986 个精确重复地址组和 14 个类别冲突地址组。
- **Critical boundary**：这些数值只证明 `addresses.csv` 的地址行级风险。当前没有 `address → script → cluster/node` 映射、union lineage、冲突丢弃日志或 node-level source 字段，不能据此声称原论文的 random node split 已被证实泄漏，也不能声称 GNN 直接使用了 source。
- **Support violation**：6/8 个来源只覆盖单一类别，INDIVIDUAL、BET、GAMBLING、PONZI、FAUCET、BRIDGE 各只出现于一个来源；直接整源留出会让部分测试类在训练中没有支持，不能把这种失败解释成一般 OOD 能力。
- **Nearest prior work**：`Saf26` 已对 Elliptic 的不透明特征构造与 split 隔离做系统审计；GOOD/OGB/TGB 已覆盖通用图 OOD、重复与时间评测；`Real25` 已提供未来日 Sup-CATS；`Dib26` 已做 Real-CATS→Elliptic++ 跨数据测试。仅提出 group/source/time split 不新。
- **Minimum decisive experiment if lineage is obtained**：在 34k labeled nodes 上预注册 random、identity-disjoint、support-matched source-disjoint 和 label-availability temporal 四协议，比较 GBC/Logistic、label propagation 与原论文 GNN，并检验 `Δ = Macro-F1(GNN) - Macro-F1(GBC)` 是否翻转。
- **Go conditions**：取得不可变标签迁移 lineage、每个 node 的原始来源/规范化名称/冲突日志/标签时间，并补充使训练来源覆盖测试类别的独立标签。
- **Strongest rejection**：从无法与最终 node 对齐的 raw address 表推断实体图 GNN 泄漏；source holdout 还违反类别支持；纯 audit 已被 2026 年 Elliptic 审计覆盖。
- **Score / decision**：4×5×1=20；**当前 Gate 2 No-Go**。补齐 lineage 后才可作为 data/benchmark 贡献重审，理论仅有初等 exposure/support 性质，不足以作主贡献。

## CP-12 — 可追溯、严格时点的 Bitcoin 实体图 benchmark 重建

- **Research question**：在保存 `raw evidence → address → locking script → as-of cluster → entity node` 全链路、标签来源/冲突/首次可得时间，并执行 identity-disjoint、support-matched source-disjoint 和 temporal splits 后，252M 实体图上的模型增益、类别覆盖和模型排序是否仍成立？
- **Falsifiable hypothesis**：原始随机 node split 与终态聚类协议会高估至少一类结论；在可追溯协议下，部分标签覆盖率、GNN 相对 tree baseline 的增益或模型排序将显著改变。如果 pilot 不出现可复现且具有实际量级的变化，本方向停止。
- **Operational decision and unit**：以严格时点的 heuristic entity 为预测单位，任务只称 `entity-type classification`；规范主键必须从 raw block/transaction/outpoint 与 `scriptPubKey` 开始，地址只是部分标准脚本的可选编码，不能假定地址与脚本一一对应。
- **Ground truth and label time**：每个 entity label 必须回溯到原始地址证据、来源、冲突处理与首次可得时间；终态 cluster 只能用于描述或更严格的分组，不能进入历史时点特征/标签聚合。
- **Nearest prior work**：`Sch24` 是直接数据对象；`Saf26` 已审计 Elliptic 的不透明特征与 split 隔离；`Len26` 已构建 32,059,886 条多源地址标签并处理地址/cluster 标签冲突；`Coq25`/ORBITAAL 发布最终用户的地址列表与多尺度时间图，但其聚类代码不可复现；`Jal25` 发布保留 script/transaction/block 和 block-height 的高保真异构图；OGB/GOOD/TGB 已使通用 group/OOD/temporal split 本身不再新。
- **Actual gap rather than implementation gap**：候选贡献不是“再做一次数据清洗”或“添加一种 split”，而是发布可重放的 as-of union log、证据与标签迁移 DAG、冲突/丢弃清单、支持匹配协议和统一复算结果，证明这些不可见选择是否改变已有科学结论。当前检索未找到将这五部分同时用于公开 Bitcoin entity benchmark 的工作。
- **Minimum decisive Gate 2 pilot**：只重建一个预注册的连续区块窗口和一个可审计标签子集；生成逐次 union 的 block height、heuristic/version/reason，映射原始标签并保留冲突；比较 random、identity-disjoint、support-matched source-disjoint、as-of temporal 四协议下 Logistic/GBC、label propagation 与一个原论文 GNN，检验 `Δ=Macro-F1(GNN)-Macro-F1(GBC)`、coverage 和模型排名是否改变。
- **Strong baselines and metrics**：Logistic、GBC/XGBoost、label propagation、原论文 GCN/GraphSAGE；macro/classwise F1、coverage、Kendall `tau`、`Δ` 的 bootstrap CI、post-cutoff merge rate、跨 split entity exposure、provenance completeness。
- **Data availability**：原 252M 发布物只有聚合节点/边；它不能反推出逐 union 历史或每条标签首次公开时间。开源构建仓库可帮助从公开链重新计算，但不能补回原始运行时决策。ORBITAAL 提供最终 address pool 但没有可复现构建代码；`Jal25` 的 script-level temporal graph可作为不依赖实体聚类的上游参照。`Len26` 已公开全文但是否发布可复用标签库/代码仍未确认。
- **Single-machine feasibility and engineering cost**：完整重建为高成本；Gate 2 pilot 应先在受控区块窗口和 34k 标签链路上验证结论，只有效应通过才扩大。算力不是首要风险，磁盘、I/O、确定性重放和发布许可才是。
- **Contribution type**：data/benchmark + reproducible workflow + empirical benchmark finding；理论只作协议性质与失败条件，不把“终态信息不可用于历史预测”或普通 top-k margin lemma 包装成新定理。
- **Go conditions**：能确定性重放 lineage；标签及构建产物可合法发布或由脚本复取；source×class 支持可匹配；pilot 显示非平凡的 coverage/排名/增益变化；与 `Saf26`、`Len26` 的差异可由 artifact 和实验证明。
- **No-Go conditions**：无法重建或发布关键 lineage；只能得到终态映射；类别支持无法修复；pilot 的变化很小或只来自训练未见类别；`Saf26`/`Len26` 的全文已覆盖等价 artifact 与结论。
- **Ethics and misuse risk**：发布可追溯链路可能增强去匿名化；公开物应最小化真实个人身份，保留公开证据引用而不额外扩散敏感映射，并明确 heuristic entity 不是法律上的个人或受益所有人。
- **Strongest reviewer rejection argument**：这是工程化数据清洗；评测卫生原则已由 OGB/GOOD/TGB 与 `Saf26` 覆盖，且没有新的任务、理论或足够大的模型排名反转。
- **Independent Devil's Advocate**：Sch24、ORBITAAL、`Jal25`、`Len26`、`Saf26` 与 OGB/GOOD/TGB 已覆盖实体时间图、原始时序 ETL、多源冲突和通用评测规范的大部分组件；当前缺少的历史 union/claim-time 信息无法从最终资产补录。将其作为主线会面临“已有资产再提取 + 常规 split”的直接拒稿。
- **Score / decision**：5×5×1=25；**当前 No-Go as main direction**。CP-04 关闭后不单独建设；只有逐 claim/union lineage 可发布且新 pilot 显示跨 cutoff 稳定的实质模型选择变化，才可重审为 Datasets & Benchmarks 方向。

## CP-13 — Ordinals 市场协作式 PSBT 对地址聚类的系统性污染

> 最新裁决（2026-08-31）：`parked pending semantic ground truth`。第二实现有界取证未过，暂停主线扩展。下文历史“严格 msigner 默认模板”措辞被源码审计覆盖：103 条只是部分布局特征匹配，其中仅 49 条满足默认 output 1 的 10,000 sat 条件；两者均不构成平台归属或成交真值。

> 2026-08-31 审计覆盖说明：以下 v1 计数暂时隔离，不能作为已通过硬门的最终证据。旧 scanner 将任意形状相似的 65-byte witness 项识别为 Schnorr，又把以 `0xc0/0xc1` 开头的合法签名误当 control block；未充分处理 annex、prevout 类型和实际签名消费位置。修正必须保留 v1，另产出 detector-v2 复算与差异清单；重复使用同一组区块只算诊断复算，不算独立验证。

- **Research question**：Ordinals 市场使用协作式 PSBT 完成 inscription 销售时，卖家以 `SIGHASH_SINGLE | SIGHASH_ANYONECANPAY` 预签资产输入，买家再加入付款输入。这类协议级多方交易会产生多少不满足共同控制假设的 common-input unions？错误 union 在全局地址/实体图中传播多远？基于链上签名角色与 inscription 转移的过滤器能否在不明显损失合法聚类 recall 的条件下阻断污染？
- **Falsifiable hypothesis**：标准 common-input ownership heuristic 与只识别等额输出 CoinJoin 的过滤器会把至少两个独立签名主体的输入合并；该现象跨多个 Ordinals 市场稳定存在，并造成非平凡的 cluster merge、标签传播或图统计变化。若交易量很小、现有过滤器已覆盖、独立主体无法操作化或下游变化可忽略，则假设失败。
- **Operational decision and stakeholder**：对象是链上分析管线中的“是否允许本交易生成地址 union 边”。利益相关者包括学术 Bitcoin 图数据集维护者、取证分析系统和使用实体图进行经济/网络研究的研究者。论文不声称识别非法交易，也不把实体标签解释为 AML 风险。
- **Prediction and graph unit**：检测单位为 confirmed transaction、input signature role 和候选 union edge；影响单位为 union-find component、entity graph edge 与预先登记的下游统计。PSBT 文件本身不上链，必须从最终交易的 witness、spent output、inscription index 和交易结构恢复可观测信号。
- **Ground truth**：第一层真值来自公开市场的官方交易构造、开源签名实现和官方示例 tx；第二层以人工核验的跨市场交易样本评估检测 precision。`SIGHASH_SINGLE | ANYONECANPAY` 证明协作签名能力与输入承诺范围，不单独证明卖家、买家一定是不同现实所有者；wash trade、自成交和共同托管必须作为不确定或排除项。
- **Verified mechanism evidence**：ORD.NET 官方文档明确卖家用 `SIGHASH_SINGLE | SIGHASH_ANYONECANPAY`、买家完成 sale，并给出确认交易 `0f2f22ed557359039a80620bb5d559f3bc2b982f1b03ddfc771668d115a1ce40`。该交易同时包含平台 anchor、2-of-2 passthrough 和买家付款输入；Taproot witness 中可见一条附加 `0x83` 的签名以及默认/`SIGHASH_ALL` 签名。OrdinalsBot 官方示例和 Magic Eden 开源 `msigner` 也采用卖家 `SINGLE|ANYONECANPAY`、买家 `DEFAULT/ALL` 的组合，说明机制不是单一平台特例。该证据只证明协议模式存在，尚未证明总体规模和污染效应。
- **Nearest prior work**：既有研究已系统讨论 common-input heuristic、CoinJoin/协作交易例外、PayJoin、change heuristic、聚类准确率与 unconfirmed transaction clustering；Ordinals 研究主要分析 inscription 机制、区块空间、费用和网络活动。Müller et al. 2026 在 854,144,149 笔交易上评估 MIH，并明确保留 CoinJoin/mixing 交易；其七个服务的 full-cluster precision/recall 仅约 0.36/0.44，但没有识别 Ordinals PSBT 这一机制或提出相应过滤。2026-08-30 的 Undermind focused deep search 返回 22 篇近邻；最接近者是 BRC-20 PSBT sniping、PayJoin UIH、MIH 可靠性和协议型 CoinJoin detection，均未测量 Ordinals/数字资产市场 PSBT 对 CIOH 的污染。两条独立检索链目前均未找到 exact prior；这是检索快照结论，不表述为“首次”。
- **Actual gap**：潜在贡献不是“发现多方交易会破坏 CIOH”这一已知常识，而是识别一个 2023 年后出现、可由链上密码学签名角色高精度检测、未被常用 CoinJoin 规则覆盖的规模化交易族；量化其 union cascade 和公开数据集偏差；发布可复查 detector、污染清单与修正后的图统计。
- **Minimum decisive experiment**：先选三个具有公开构造或开源实现的市场，各收集官方示例和一个连续区块/交易样本；解析 ECDSA/Taproot sighash、spent output、inscription movement 和 input/output role。不得用“witness 元素最后一字节为 `0x83`”作粗字符串匹配：ECDSA 必须验证 DER signature 结构与尾部 hash type，Taproot 必须区分 64-byte default 和 65-byte explicit hash type，并结合 key/script-path witness 位置。比较未过滤 CIOH、已发表协议型 CoinJoin rules、BlockSci-style filter、删除全部 `ANYONECANPAY` 的粗基线和 protocol-aware filter。只报告交易数、候选错误 union、component merge 增量、cascade size、现有过滤器召回和人工核验 precision；暂不训练 GNN。
- **Strong baselines**：无过滤 CIOH；BlockSci/GraphSense/ORBITAAL 风格 common-input pipeline；等额输出与结构型 CoinJoin filters；删除所有 `ANYONECANPAY` 交易的高 recall 低 precision 基线；人工市场模板规则。
- **Zero-model feasibility result（v1 历史结果）**：第一步在 ORD.NET 官方示例所在区块 947353 做目的性 smoke，2,856 笔交易中检出 17 笔结构合法的显式 `0x83` 候选并命中官方示例。第二步严格排除该区块，按事先冻结的 SHA-256 规则抽取四个时期共 24 个区块，扫描 65,545 笔交易，得到 Tier 0 838 笔、Tier 1 662 笔；六个 control 区块为 0，early-marketplace、post-Runes、recent 分别为 491、144、27。Tier 1 覆盖全部 18 个后期样本区块、123 个结构指纹，其中 86 笔含多个匹配的 `0x83` inputs。该结果通过预设规模、跨时期与模板多样性门，但 Tier 1 仍不等于 inscription sale、市场归属或独立所有者真值。
- **Published-filter check（v1 历史结果）**：Schnoering–Vazirgiannis 2023 的 JoinMarket、Wasabi 1.0/1.1/2.0 与 Whirlpool 规则均要求输出脚本互异或固定协议结构；662 个 Tier 1 中有 636 个存在重复 output script，因此可由规则条件直接判定这些已发表规则必然漏检，保守下界为 96.1%。代表样本也未触发 BlockSci 官方 `isCoinjoin`、`isCoinjoinExtra` 或 `isPossibleCoinjoin`，其聚类调用链随后会 union 所有 inputs。该下界只针对明确复现的公开规则，不代表所有商业过滤器，也不声称停止维护的原始 BlockSci 已能端到端解析现代 Taproot。
- **Implementation-family evidence（v1 历史结果）**：662 个 Tier 1 中有 101 个匹配 `msigner` 的部分布局特征（源码复核后更正）：seller signature/input index 为 2、两个 580–1000 sat 同脚本 dummy inputs、对应 buyer output 覆盖 dummy 总额，且 outputs 4/5 为同脚本 600 sat dummy outputs。它们只能称为 `msigner-compatible`，不能在缺少平台或资产索引证据时直接归属 Magic Eden。
- **Primary metrics**：人工核验 precision/recall；被标准过滤器漏掉的 protocol-incompatible union 比例；新增合并 component 数与地址数；最大/分位 cascade size；过滤前后 cluster-size distribution 与预注册图统计效应量。下游标签或模型结果仅在 union 影响足够大且标签语义合法时作为次要分析。
- **Data and feasibility**：原 252M 终态图不含 txid/witness/union lineage，不能直接做检测。Gate 2 pilot 可使用官方 txids、公开 explorer API、官方 `ord` index 和小区块窗口；完整测量可从 2023 年后的区块流式扫描标准签名，再与 inscription input/transfer 索引相交，不必依赖不透明的 marketplace sale 标签。当前磁盘不足以无条件保存完整 Bitcoin Core 与全量解析副本，因此只有小样本通过后才申请外部存储、远程节点或流式扫描。任何第三方“公开 sales endpoint、许可和历史覆盖”必须逐项核对官方文档，不能采用搜索代理生成但无法定位的接口。
- **Theory property card**：在明确存在两个独立签名主体的交易中，对全部输入执行 CIOH union 必然违反单一控制假设；一个错误 bridge union 会不可逆地合并其连接的既有 components。两者目前属于直接性质，只能支撑检测正确性和传播量定义，不能当主定理。理论升级必须得到非平凡的可检测充分条件、污染传播界或在部分可观测签名下的可识别性结果，并通过反例审查。
- **Go conditions**：至少两个独立市场存在可复现的高精度检测；公开样本量与时间跨度足够；标准 CoinJoin filters 大量漏检；污染对 component 或预注册图结论具有稳定、非平凡影响；与最近邻没有 High/Exact overlap。
- **No-Go conditions**：效果只限单一新平台；`SINGLE|ANYONECANPAY` 不能可靠区分市场交易与其他协作用途；自成交/托管使不同主体无法操作化；标准过滤器已移除超过 95%；过滤前后 component 和下游统计变化很小；贡献只剩十几行 ETL 规则。
- **Ethics and misuse risk**：目标是减少错误合并与错误归因，原则上改善隐私和科学有效性。发布样本应避免额外标注真实个人，只公开已在链上和官方文档可定位的交易结构；不把 cluster 当法律身份。
- **Strongest reviewer rejection**：协作交易破坏 CIOH 早已已知；Ordinals 只是一个显然的新实例，检测规则过于简单，缺少独立实体真值，规模或下游影响不足以形成顶会贡献。
- **Corrected diagnostic result**：detector-v2 只把支持的脚本上下文中的目标签名计入 Tier 1。24 区块复算为 845 个字节形状候选、832 个上下文通过交易、666 个 Tier 1；原 662 个全部保留，新增 4 个合法 `0xc0/0xc1` 前缀 key-path 签名交易。公开结构规则漏检下界为 640/666（96.1%），`msigner` 部分布局特征匹配为 103/666（15.5%，源码复核后更正）。这不是独立验证；当前 API prevout 信任和不支持脚本路径的边界必须保留。
- **Raw semantic audit**：预先固定 11 笔分层子样本，复核 43 笔原始父交易，11 个目标 prevout 全部匹配。7 笔含支持范围内的直接 simple reveal，6 个 BRC-20 transfer 声明、1 个 image/webp；按限定 FIFO 规则，其内容承载首 sat 均移至不同脚本的 output 1。七个 reveal 所在区块的 header、txid Merkle root、BIP141 witness commitment 及目标 raw witness 一致性均通过。主链 hash 锚点信任 Blockstream，不等同全节点共识验证。其余 4 笔未决；不估计总体 precision，不把声明当有效代币转移，不把不同脚本当不同所有人。
- **Known coverage counterexample**：ORD.NET 官方示例 `0f2f22ed557359039a80620bb5d559f3bc2b982f1b03ddfc771668d115a1ce40` 使用平台和卖方 2-of-2 Taproot script path，输入为 P2TR、对应卖方收款为 P2WPKH。当前上下文支持范围与同脚本 Tier 1 条件均会漏掉它。冻结 24 区块内没有匹配官方平台公钥的该模板。不得把官方示例、模板相似和样本资产语义拼成已通过的跨平台 precision 证据；扩大检测范围须另立版本并使用独立样本。
- **Score / decision**：历史评分 5×3×4=60 不再代表可晋级。**当前暂停：第二实现语义证据未满足，停止 component 与 detector 扩展。** 官方 msigner 固定源码只提供机制、signet fixture 与占位测试，没有闭合主网成交工件；官方同一份构造又揭示旧模板计数解释过强。固定子样本的原始来源和 witness 完整性通过仍有效，但不足以补上该缺口。只有新增可直接连接的第二实现证据才重开；投入工程量和密码学完整性检查不计作论文创新。
