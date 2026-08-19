# Candidate Research Problem Cards

> 状态：Gate 1 进行中。候选必须从已核验证据产生，不从旧 EGS 叙事反推。

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
| 1 | CP-05 252M 实体类型标签审计 | 3 | 4 | 4 | 48 | 低风险 fallback；不足以单独支撑顶会主线 |
| 2 | CP-04 label-discovery-time 完整性审计 | 4 | 3 | 2 | 24 | Conditional；标签时间尚不可恢复 |
| 3 | CP-06 PU 条件下的主动调查 | 4 | 2 | 3 | 24 | 数据到位前暂缓 |
| 4 | CP-02 时间化实体映射误差的下游传播与认证 | 5 | 4 | 1 | 20 | 理论窗口存在，但当前数据门槛失败 |
| 5 | CP-07 事件种子后的严格时间前向发现 | 4 | 2 | 2 | 16 | 暂缓 |
| 6 | CP-08 开放世界的可拒识告警 | 4 | 2 | 2 | 16 | 暂缓 |
| — | CP-03 选择性/延迟标签下 top-k 效用的部分识别 | 5 | 5 | 1 | 25 | **标准理论覆盖，当前硬 No-Go** |
| — | CP-11 来源/同名实体捷径与评测有效性 | 4 | 5 | 1 | 20 | **推断桥缺失，当前 Gate 2 No-Go** |
| — | CP-09 跨链迁移失败 taxonomy | 4 | 2 | 1 | 8 | 当前 No-Go |
| — | CP-01 普通固定预算队列 | 4 | 5 | 5 | 100 | **直接重合，硬 No-Go** |
| — | CP-10 单纯聚类准确率比较 | 3 | 5 | 4 | 60 | **直接重合，硬 No-Go** |

硬重合和理论直接覆盖优先于乘积分数；高分但已有标准结论或缺失必要数据的方向不能进入推荐组合。当前没有通过全部 Gate 的主方向。

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

## CP-04 — Label-discovery-time 完整性的时间评测审计

- **RQ / hypothesis**：区分事件时间 `t_e`、标签发现/公开时间 `t_l` 和采集时间 `t_c` 后，现有 chronological benchmark 的有效训练集和模型排序是否改变？
- **Operational unit**：沿每个数据集的原生交易/地址/子图单位，不跨数据集混写标签。
- **Nearest work / gap**：`Kha26`、`Mag26` 已审计图和特征的时间可见性；仅当 `t_l` 审计尚未被覆盖且能恢复实际时间或可靠区间时，本卡才独立。
- **Minimum experiment**：至少两个数据集分别运行作者原协议、edge-only cutoff 和 label-aware cutoff；报告可用标签比例、Kendall `tau`、胜者重排和结论可认证状态。
- **Data / feasibility**：瓶颈是标签来源 archive 与时间 provenance，不是算力；若不能恢复也不能界定 `t_l`，No-Go。
- **Contribution / rejection**：data/protocol audit；最强拒稿理由是“只换切分重跑 Kha26/Mag26”。
- **Score / decision**：4×3×2=24；备选 2，Conditional Go。

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

## CP-07 — 事件种子后的严格时间前向发现

- **RQ / hypothesis**：给定在 `t_0` 已确认的事件种子，只用 `t_0` 前可见信息扩展未来关联单位时，现有候选子图/推荐方法的收益是否显著下降？
- **Operational unit**：地址、交易或事件子图三选一；表述为 seed-conditioned expansion，不是未知犯罪预测。
- **Nearest work / gap**：`Bel24`、`Son24` 使用已构造候选；`Paq18`、`Wu24` 从已知事件种子追踪。缺口仅可能在可部署 candidate universe 与严格 seed-time cutoff。
- **Minimum experiment**：重建候选生成时间，比较原协议与 strict `t_0` 协议；基线为规则扩展、temporal walk 和 time-restricted link model。
- **Metrics**：Recall@B、独立 case coverage、首次发现延迟、候选泄漏率。
- **Failure / rejection**：种子、标签或候选由未来生成即停止；最强拒稿理由是“换切分重跑 Elliptic2，仍无 open-world ground truth”。
- **Score / decision**：4×2×2=16；暂缓。

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
