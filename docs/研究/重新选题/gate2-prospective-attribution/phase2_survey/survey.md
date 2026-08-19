# Gate 2 Phase 2：跨领域证据地图

## 范围与语料

本阶段将 Phase 1 的 17 篇直接邻居，与 Gate 1 已核验的 Bitcoin/crypto transaction-graph 文献，以及 OSINT 来源依赖、延迟/选择性标签、取证标签传播和可复现基础设施文献合并。`paper_db.jsonl` 共收录 51 篇去重记录；同行评审状态、DOI 和版本按可定位的一手元数据记录。摘要只用于筛选，Phase 3 的结论必须定位到全文页、节、表、图或原始 artifact。

研究 estimand 暂定为：在历史时点 `c` 冻结候选全集和全部输入后，有限预算排序对未来时间窗 `h` 内“后来获得独立公开佐证”的 case/address 的恢复率。它不是未知犯罪率，也不是 AML 告警 precision。

## A. 前瞻/早期检测与种子扩张

`Che23`、`Che25d`、`Gom22`、`Oli21`、`Elo21`、`Dib26` 和 `Wan24b` 已覆盖 temporal path、seed expansion、streaming feedback、拓扑分类和 ransomware transaction relations。它们把方法创新门槛抬得很高：仅设计新的 GNN、路径采样器或时间切分不能构成主贡献。

当前候选问题的差异只能来自评测对象和证据形成过程：候选全集在 `c` 时已存在；种子在 `c` 前公开；输入不能包含 `c` 后的地址、边、聚类合并、页面或标签；结果是在 `c` 后首次出现且来源独立的公开佐证。Phase 3 必须核验近邻论文是否已同时满足这些条件。

## B. 报告、标签 provenance 与来源依赖

`Gom24`、`Gom23`、`Cho22b`、`Fro19`、`Deu22`、`Len26`、`Lia16b`、`Hos20`、`Kan15` 和 `Zhu20c` 共同说明：URL 数量不等于独立证据数量；转载、共同上游、标签传播和来源相关性会制造伪多数或伪未来标签。必须把报告组织为 source family，并追踪到 root evidence。

最低证据结构是有向依赖图：`report -> claimed address/case -> upstream evidence`。转载、镜像、共同数据导入、相同交易列表和明确引用同一调查的页面合并为一个 source family。候选 outcome 要求至少两个无共同 root evidence 的 family，且至少一个是原始或权威证据链；这个阈值仍需在 Phase 3 由事件审计验证，而不是预设为真理。

## C. PU、延迟标签、删失与选择机制

`Luo23`、`Bek18sar`、`Bek19`、`Fur22` 和 `Dha26` 约束统计主张：未标注单位不是负例，公开报告是选择性观察机制，标签延迟和腐败可能与模型可见信号共同驱动。因而真实 illicit probability 通常不可由公开标签识别。

可防守的结果应降级为未来公开佐证的观测下界。`Precision@B` 只能称为 confirmed-yield lower bound；未确认地址不得计为 false positive。随访不足需按行政删失或区间删失处理，并报告时间窗 `h`、风险集和敏感性界。若事件档案无法重建 first-public 时间区间，则核心 estimand 不可识别，方向 No-Go。

## D. 时间泄漏与有限预算评测

`Kha26`、`Mag26`、`Mal26`、`Web19`、`Elm23`、`Lor20`、`Edd21` 和 `Car22` 已覆盖严格时间协议、inductive/transductive 差异、固定预算队列、unknown burden、case fragmentation、主动学习或真实告警语境的重要部分。特别是 `Mal26` 已使“单位一致 + 固定预算 + 时间切分”失去独立新颖性。

若 Gate 2 继续，主指标应是 `R@B(h)`、`case-recall@B(h)`、`first-hit@B`、time-to-public-corroboration、case/source diversity、seed redundancy 与计算/调查负担。必须做 purged temporal folds、case/address/cluster 三层去重和 source-family-held-out；没有完整审计负例时不报告 ROC/AUC、绝对 precision 或犯罪概率校准。

## E. 事件数据与标签语义

`Hua18`、`Paq18`、`Ara24`、`Shi25`、`Xia24` 和 `Ama26` 是当前事件家族候选；`Mba26`、`Bel24`、`Son24`、`Sch24`、`Coq25` 与 `Jal25` 提供多链、子图或大图参照。每个数据集都必须区分：地址/实体类型、abuse report、已知事件 seed、taint 扩展、司法/执法归因和真实 illicit outcome。它们不可互换。

Phase 3 的首要任务不是追求事件数量，而是检查至少三个事件家族是否同时具备：`c` 前种子、可冻结的当时候选全集、`c` 后首次公开归因、独立 root evidence、可存档原文、明确 case ID 和允许研究使用的来源条件。

## F. 实体解析与可复现基础设施

`Mul26`、`Mos21`、`Sch23cj`、`Sto21` 和 `Noc21` 表明地址聚类/record linkage 误差会传播到实体标签、切分和队列。历史实验只能使用 `c` 前可构造的 partition；终态聚类回填历史会引入未来合并信息。若无法重建动态地址到实体映射，核心评测先保持 address/case 单位，实体级结果只能作为敏感性分析。

`Saf26`、`Kal17` 和 `Bos18` 提醒 artifact 透明度、标签 registry 与链上解析版本必须进入可复现协议。每个 cutoff 的候选清单、块高、边、特征、种子、来源 registry 和归因图都需要版本号与哈希。

## Phase 2 暂定判断

六轮独立语义反证与两条 Undermind deep search 尚未发现同时满足以下组合的 exact prior：

1. 冻结历史时点的候选地址全集及全部输入；
2. 用未来首次出现的公开归因作为 outcome；
3. 对上游证据做 source-family 去依赖；
4. 显式处理报告延迟、区间时间和 right censoring；
5. 做 source-family-held-out 与有限预算 case-level 评测。

这只说明组合层面暂未撞题，不等于已经证明创新性。普通“temporal split + `P@K` + public labels”已经高度拥挤。该方向能否成为顶会问题完全取决于 Phase 3/4 能否找到至少三个可复核事件家族和可冻结 artifact；缺任一核心条件即 No-Go。

## Phase 3 全文优先级

- 直接近邻：`Che23, Che25d, Gom22, Gom23, Gom24`。
- 事件与证据：`Hua18, Paq18, Ara24, Fro19, Ama26`。
- 方法反证：`Hos20, Zhu20c, Luo23, Dha26, Mal26`。
- artifact：`Shi25, Saf26, Kal17, Bos18`。

Phase 3 至少完成 8 篇全文笔记，并把每个关键判断定位到具体证据位置；同时等待两组事件家族独立审计结果。
