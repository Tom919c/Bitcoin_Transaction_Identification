# Gate 2 Go/No-Go 报告

## 执行结论

**Decision: NO-GO for formal research direction and model development.**

“未来独立公开归因的前瞻恢复”作为完整 formulation 暂具中等置信度的新颖性，但当前没有可执行的数据基础。14 个事件/家族中没有一个同时满足历史 seed、冻结候选全集、未来 address/tx 级归因、独立 root evidence、可验证 first-public time 和合法可重放 artifact。不能以新颖性替代 ground truth。

只保留一个 **last-chance feasibility pilot**：BlackSuit/Royal 的零模型链上唯一匹配与证据依赖审计。它不是正式实验，不授权训练模型；失败即关闭 CP-04+CP-07。

## Gate 2 证据规模

- Phase 1：17 篇直接前沿/最近邻。
- Phase 2：51 篇去重 paper/source database。
- Phase 3：8 篇全文证据笔记；14 个事件/家族的一手来源审计。
- Phase 4：5 个外部仓库/数据发布 + 1 个本地 252M artifact。
- 独立创新性反证：至少 6 类检索轮次；未发现 exact combination，但发现大量组件级强重合。
- Undermind 参与 discovery/deep-search；本轮 PDF 接口两次发生传输/额度故障，关键结论均由论文原文、Firecrawl/Tavily 与官方一手材料交叉核验，未把检索摘要升级为正式证据。

## No-Go 的决定性原因

1. **未来证据不可稳定映射到链上对象**：多数 DOJ/FBI 公告只证明组织、事件、金额或扣押，不给钱包/txid；事件级归因不能成为地址标签。
2. **来源独立性不可证明**：Ransomwhere、报道、受害方和执法材料可能共享调查上游；不同 URL 不是独立证据。
3. **时间锚点不足**：众包条目的 `createdAt`、网页显示日期和 90 天延迟发布都不能单独确定 first-public time。
4. **跨链/VASP 隐边**：Upbit、Harmony 的 ETH seed 到 BTC outputs 经过不可观测的交易所/隐私工具路由，纯公共链无法识别 target mapping。
5. **本地数据单位不匹配**：252M 资产是聚合 entity aliases，无 address/txid/block hash 或 address-to-alias union lineage，不能用于 address-level 法律证据回填。
6. **最近邻已覆盖普通贡献**：early detection、seed tracing、future-day split、budget queues、PU/delayed labels、provenance schema 都已有强工作；只加时间切分、P@K 或 GNN 不新。

## 候选方向更新

| 方向 | Gate 2 后决定 | 说明 |
|---|---|---|
| CP-04 + CP-07：未来独立公开归因 | **No-Go now**；仅保留一次零模型 pilot | 0/14 完整合格事件；不足以建 benchmark |
| CP-02：时间化实体映射误差传播 | **Blocked / Conditional** | 本地无 union lineage、独立 entity ground truth 或 address→alias 映射 |
| CP-12：严格时点 provenance benchmark | **No-Go as main** | 多组件已有工作，且原始 lineage 无法从终态资产恢复 |
| CP-05：252M entity-type 标签审计 | **Feasible fallback** | 可做、主张诚实；单独贡献大概率不足顶会，除非发现可复现的大规模协议/模型排序反转 |
| 跨链隐边不可识别性 | **Protocol lemma only** | no-free-lunch 直觉有价值，但尚非足够新理论 |

## 顶会水平判断

当前研究**尚未达到可以正式写一篇高质量顶会论文的水平**。缺的不是更复杂模型或更多算力，而是可发布、可复核且与主张一致的数据/证据链。若现在写论文，审稿人最可能以 ground truth 不成立、未来标签同源、任务单位错配、不可复现和组件创新不足拒稿。

## 唯一获准的下一步

执行 `preregistration-pilot.md`：对 BlackSuit/Royal 做确定性、零模型、可失败的 target construction test。成功后也只说明一个事件可用；仍需再找到两个独立事件才能重开正式 benchmark Gate。失败后关闭该方向，回到新一轮问题生成，优先寻找能由现有 252M entity-type 数据或可获取的新 address-level provenance 数据真实支撑的问题。

## 禁止事项

- 不启动 GNN/LLM/排序模型训练。
- 不把未确认地址标为 benign。
- 不把未来法律公告用于构造 `c` 时模型输入。
- 不用本地终态实体图假装历史 address graph。
- 不把 Upbit/Harmony 写成纯 Bitcoin seed tracing。
- 不因事件不足而把验收门槛从 3 降到 1。
