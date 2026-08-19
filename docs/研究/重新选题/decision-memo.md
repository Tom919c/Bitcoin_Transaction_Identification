# Research Direction Decision Memo

## 当前状态

**Decision: PENDING — Gate 1 未完成。**

现有 147 篇 deep-search 摘要提出“因果时间、跨数据集、有限调查预算下的风险排序基准”作为主方向，但该结论目前只视为待检验假设，不是项目决定。

独立反证检索和全文定位确认：`Mal26` 已直接覆盖 Elliptic++ 上的 transaction-to-address projection、native address queue、固定预算、严格时间协议、yield@budget、unknown burden、case fragmentation 与队列重叠；`Kha26` 已覆盖 Elliptic 的严格时间、Precision@k 与校准。因此，“单位一致的预算化队列评测”作为纯 benchmark/empirical 主方向暂列 **Provisional No-Go**，不再作为默认主方向。

此前保留的两个理论转向也已经完成红队审查：不完整/延迟标签下的效用识别被标准 PU、missing-data、selective-label 和 OPE 理论直接覆盖，判为 No-Go；严格时间化的地址聚类误差传播只在取得 union lineage、独立实体真值和真实高分尾部效应后才 Conditional Go。

只读可行性审计已经确认：当前 PostgreSQL 只有 `node_features` 与 `transaction_edges` 两张表；实体表仅保存聚合后的 `alias`、`cluster_size` 等字段，没有 address→entity mapping、聚类边、规则版本或历史 union events。仓库的数据构建代码也直接以 entity alias 为节点。因此，现有 252M 资产**不能重建** `H_t`，第二项已从“现有数据可做”降为“取得上游映射与可审计真值后才 Conditional Go”。这不是算力问题，而是信息已经在聚合时丢失。

独立理论红队进一步否决了第一个理论转向：MNAR 下观察等价、SCAR/SAR 恢复、propensity bounds 与基本部分识别区间均是成熟 PU/missing-data/selective-label/OPE 理论的直接应用。没有独立审计标签和调查日志时，它只能说明“公开标签不足”，不能构成新的理论主线，也不能识别真实调查效用。

新发现的“来源/同名实体捷径”也没有被直接升级为主方向。地址表审计确认 source-only accuracy 约 0.748，且随机地址切分中约 98.9% 的测试命名地址在训练集有同名实体；但当前发布资产缺失 `address→script→cluster/node` lineage，因此无法把地址行风险归因到最终 entity-node split。`Saf26` 已系统审计 Elliptic 的不透明特征与 split 隔离，`Real25` 已做未来日部署测试，`Dib26` 已做跨数据测试；只增加 source/group/time split 不足以形成顶会创新。CP-11 当前判为 Gate 2 No-Go，只有补齐 lineage、支持匹配和标签时间后才重审。

当前组合（仍非最终签字）：

- **主推荐**：暂缺。当前没有任何候选同时通过创新性、标签有效性和数据可行性三道 Gate。
- **替代方向一**：CP-02，时间化实体映射误差传播；只有另行取得原始 address→entity provenance、历史 mapping 和外部真值后才恢复 Conditional Go，当前资产不满足。
- **替代方向二**：CP-04，label-discovery-time 完整性与时间评测审计；前提是能恢复或可靠界定标签发现时间。
- **低风险 fallback**：CP-05，252M 实体类型标签的来源、噪声与严格时间/来源隔离审计；主张限定为 entity type。它目前适合作为数据质量论文或后续主线的前置工作，不应被包装成已经达到顶会强度的主方向。
- **明确放弃**：普通固定预算队列、单纯 MIH 指标比较、把 entity type 重新命名为 AML risk、没有新审计数据的通用 PU/MNAR 理论套用、缺少 node lineage 的来源捷径主张，以及没有统一真值的跨链迁移。

## 决策输入要求

- 现有 147 篇完成元数据和摘要初筛。
- 至少 60 篇一手来源完成来源核验。**已达到最低数，但仍按饱和规则扩展。**
- 至少 30 篇完成正文证据审计，并将最终关键证据定位到稳定页/节/表/图。**正文审计数已达到 30；其中 22 篇的正式 PDF 页码映射尚未全部完成。**
- 五组独立补充检索完成，并通过两轮主题饱和检查。
- 8–12 张候选问题卡完成。**已完成 11 张。**
- 排名前三方向完成多轮最近邻与同期工作反证搜索。
- Devil's Advocate 不存在未解决 Critical 问题。

## 最终输出槽位

- **推荐主方向**：待新一轮检索生成；CP-03 已被理论红队否决
- **替代方向一**：CP-02（blocked on new provenance/ground truth）
- **替代方向二**：CP-04（conditional）
- **低风险 fallback**：CP-05
- **明确放弃方向**：CP-01、CP-03、CP-10、CP-11；CP-09 在统一真值到位前 No-Go

## 已预先确定的放弃条件

- 把 11 类 entity type 直接宣传为 illicit activity 或 AML risk。
- 把 `-1` 未标注背景当作正常、负类或未知非法类。
- 只在随机 Elliptic 切分上提出新 GNN。
- 在测试集上反复选择阈值、模型或研究故事。
- 只有给定候选子图或纯合成数据上的 F1 改进，却声称真实 AML 部署价值。
- 无法说明预测时点、标签可得时间和图信息截止时间。
- 仅复现 `Mal26` 的交易/地址队列投影、固定预算指标或 Elliptic++ 协议。
- 仅重复评估 MIH 准确率，而没有严格时间、下游决策传播或非平凡性质。

## 用户确认 Gate

Research Director 给出最终推荐后，必须由用户确认主问题。确认前不冻结实验协议、不开发新模型、不升级到 252M 级全图实验。
