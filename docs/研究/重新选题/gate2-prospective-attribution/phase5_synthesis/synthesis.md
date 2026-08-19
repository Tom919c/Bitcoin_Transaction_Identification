# Gate 2 Phase 5：可识别性、创新性与可行性综合

## 1. 精确研究对象

对事件 `e` 和历史截止 `c`，令：

- `G^B_{<=c}`、`G^E_{<=c}`：截止 `c` 的 Bitcoin/Ethereum 公开链观测；
- `S_{e,c}`：在 `c` 前已公开且可存档的事件 seeds；
- `U_c`：在 `c` 前已出现并满足活动规则的候选地址全集；
- `Q_B(s; O_c)`：模型或规则根据 `O_c=(G^B_{<=c},G^E_{<=c},S_{e,c})` 输出的预算 `B` 队列；
- `Y^{pub}_{i,e}(c,h)`：地址 `i` 是否在 `(c,c+h]` 内首次获得满足来源独立规则的公开归因。

可评估目标是 `R@B(h)`、`case-recall@B(h)` 与 time-to-public-corroboration。它不等于潜在的真实非法状态 `Y^*`；公开证据只产生选择性、延迟且右删失的 `Y^{pub}`。

## 2. 创新性裁决

按直接匹配、组件匹配、相同应用、相同方法、同期 preprint 和 Devil's Advocate 六类检索，当前未发现同时具备以下五项的 exact prior：冻结 `U_c` 和全部输入；future first-public outcome；root-evidence/source-family 去依赖；延迟/删失；source-family-held-out 的 case-level budget evaluation。

最相似工作及重合：

| 近邻 | 已覆盖 | 未覆盖或未证明 |
|---|---|---|
| `Che23/Che25d` | early malicious address detection、asset path | future independent evidence、source dependency、censoring |
| `Gom22` | seed expansion、transaction tracing、operation oracle | 冻结历史候选全集、future first-public outcome |
| `Shi25` | future-day transfer、公开地址数据 | label first-public time；其 unlabeled 被采样为 benign |
| `Mal26/Kha26` | chronological split、budget queues、unknown burden、calibration | 独立未来归因与来源 held-out |
| `Fro19` | provenance/tag/cluster 数据模型与证据要求 | 前瞻 benchmark、依赖统计和预算评测 |
| `Gom24/Len26` | 报告污染、多源标签冲突 | root-evidence DAG + prospective recovery |
| `Dha26` 与 PU 理论 | reporting/delay/corruption 的识别条件 | 公开 OSINT 中强假设通常不成立；不提供事件 artifact |

**Novelty binary decision**：`novel`，置信度 `medium`，仅指上述组合 formulation；不是对方法模块或单个数学事实的判定。**Contribution decision**：当前 `No-Go`，因为没有三个满足协议的事件 artifact。新颖但不可执行，仍然不是一篇论文。

## 3. 可识别性边界

### 3.1 公开佐证只能给下界

令 `R_i=1` 表示地址在随访窗内获得合格公开佐证，`Y_i^*=1` 表示真实目标状态。若只假设公开佐证无假阳性，即 `R_i <= Y_i^*`，则对任意队列 `Q`：

`E[R_i | i in Q] <= E[Y_i^* | i in Q]`。

在没有来源覆盖率、报告 propensity 或审计负例的条件下，上界可达到 1，故真实 precision 不可识别。这个结果是标准 missing-outcome bound，**只作主张边界，不是新定理**。

### 3.2 首次公开时间是区间

对一条证据，令 `L` 为可验证的原始标注/发布日期下界，`U` 为最早不可篡改归档或版本化 feed capture；真实首次公开时间 `tau in [L,U]`。相对 cutoff `c`：

- `L > c` 才能认证为未来；
- `U <= c` 才能认证为当时已知；
- `L <= c < U` 时身份不可判，必须剔除或区间删失。

这是区间逻辑，不应包装为理论创新；贡献只能来自大规模可审计实现及其对结论的影响。

### 3.3 候选性质 A：跨链/VASP 隐边下的 target non-identifiability

**命题草案。** 若 ETH seed 与 BTC outputs 之间的 VASP allocation `Z` 完全不可观测，且至少两个不同 target sets `T_1 != T_2` 能与同一 `O_c` 相容，则 `T` 不能由 `O_c` 识别。对任何只依赖 `O_c` 的确定性 top-`B` ranking，两个世界给出相同队列；在候选全集足够大时，可选一个与该队列不相交的相容 target set，使 distribution-free worst-case recall 为 0。

**构造证明。** 固定完全相同的公开 ETH/BTC graphs 与 seed。世界 1 的隐藏 VASP 账本把 deposit 分配给 `T_1`，世界 2 分配给 `T_2`；公开观测不变。算法输出相同。选择相容但位于 top-`B` 外的集合即可得到零 recall。

**定位**：这是缺失 linkage 的 no-free-lunch 结果，可能是标准不可识别性在跨链取证中的实例。必须继续搜索 cross-chain tracing / linkage identifiability 最近邻；在发现更强、领域特有的可检验条件前，只能作 protocol lemma，不能作主理论贡献。

### 3.4 候选性质 B：URL-level split 的 root-evidence leakage

设同一 root evidence family `f` 产生 `m_f` 个转载/镜像 URL，各 URL 独立以概率 `p` 进入训练，其余进入测试。该 family 同时出现在训练和测试的概率为：

`1 - p^{m_f} - (1-p)^{m_f}`。

当 `m_f` 增大时该概率趋近 1。因此 URL-level random split 会系统性泄漏共同上游；source-family-held-out 才能阻断该特定路径。

**定位**：这是 grouped leakage 的直接组合公式，不是足够强的独立理论贡献。它可作为评测协议的 sanity proposition，并通过真实 report graph 测量泄漏幅度。

## 4. 数据可行性

14 个事件中 0 个完整 Go。BlackSuit/Royal、Upbit、Harmony、Twitter 只满足部分条件：

- BlackSuit 可能由金额/日期在链上唯一定位，但公开 address registry 与 DOJ 证据尚未建立直接映射；
- Upbit/Harmony 有未来 BTC 地址，却经过 ETH/VASP/隐私工具等不可观测隐边；
- Twitter 是纯 BTC 且法律材料较强，但规模小、窗口短，适合作 sanity case；
- 其他 10 个事件缺历史 seed、未来 address outcome、独立来源或许可。

本地 252M graph 是终态 entity graph：没有 address/txid/block hash/address-to-alias lineage，无法将法律文书中的新地址映射到节点，也无法生成地址级 `U_c`。使用它会造成任务单位错配。

## 5. 最小可执行协议

正式实验前只允许一个零模型 pilot：

1. 冻结一个 BlackSuit/Royal `c` 前版本的 Ransomwhere/Showing-the-Receipts；记录 commit/DOI/hash。
2. 用原始 Bitcoin block data 枚举 2023-04-04 的精确金额 `49.3120227 BTC` 匹配集合，保留全部候选。
3. 检查每个候选地址/tx 是否已出现在 `c` 前 seed registry；不得事后挑唯一目标。
4. 从 DOJ 公告继续追到 complaint/forfeiture/seizure 原文，要求出现可唯一映射的钱包、txid 或足够强的多字段组合。
5. 保存来源 URL、原文 hash、发布/归档时间区间和 root-evidence family。

**通过条件**：唯一或预注册规则可消歧的链上 target；`c` 前未知；`c` 后一手证据可独立定位；整个流程可从冻结输入重放。**失败条件**：多重匹配、目标已知、法律证据不定位、来源同根、许可不允许。失败即主方向 No-Go。

## 6. 当前研究决策

不开发 GNN，不构建训练集，不宣称 benchmark 已成立。Phase 6 应给出明确 No-Go 与一个限时 pilot，而不是把 Conditional Go 写成推荐主方向。若 pilot 失败，回到 Gate 1 替代路线：优先评估可由现有 252M graph 实际支持的 entity-type 标签/时间协议审计，或先取得新的 address-level lineage 数据再重新立项。
