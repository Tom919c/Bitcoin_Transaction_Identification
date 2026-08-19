# Gate 2 Phase 1：前沿与直接邻居

## 研究问题

在历史时点 `t0` 冻结链上图、已知事件种子和候选全集后，能否用 `t0` 前可见信息，对后来由独立原始公开证据归因的 Bitcoin 地址或实体进行有限预算排序？目标是 `prospective recovery of independently corroborated public attributions`，不是预测未来犯罪，也不把未确认单位当负类。

## 检索方法

- Undermind 专项深检：`Prospective Discovery with Delayed Independent Evidence`，51 篇。
- Firecrawl 论文索引三组查询：ransomware public attribution、delayed/future confirmation、seed-based forensic expansion。
- 官方 DOI、arXiv、出版社和数据仓库用于元数据与 artifact 核验。
- 本机 `paper_finder` 的示例路径属于另一运行环境，未执行；配置文件保留检索意图，实际结果来自上述可用工具。
- 搜索摘要只用于发现；进入 Phase 3 的核心主张必须回到全文或原始事件证据。

## 前沿清单（17 篇）

| key | 年份/状态 | 作用 | 对本问题的即时约束 |
|---|---|---|---|
| `Ama26` | 2026 preprint | 地下论坛证据支持标签 | 声称有时间元数据，但当前仓库缺数据与代码，不能直接进入 pilot |
| `Shi25` | 2025 preprint | Real-CATS 与未来日 Sup-CATS | 已覆盖普通未来日测试；正负来源机制不同 |
| `Che25d` | 2025 journal | 资产路径与早期恶意地址检测 | 最强近期方法邻居；需核验标签首次可得时间与候选集合 |
| `Gom24` | 2025 journal | abuse-report pollution | 不同报告页面可能污染、重复或错误，直接约束“独立证据”定义 |
| `Ara24` | 2024 conference | Ransomwise 数据集 | 多来源 ransomware labels 与时间协议，是事件家族 pilot 候选 |
| `Wan24b` | 2024 journal | ransomware transaction relations | 抬高“只做交易关系检测”的方法新颖性门槛 |
| `Xia24` | 2024 preprint | dark-web abuse campaigns | 可能提供跨论坛/链上证据，但出版状态与时间语义需核验 |
| `Gom23` | 2023 ACM CCS | seed coverage 与收入估计 | 证明 seed 覆盖会实质改变测量结论；候选全集不能由未来 seeds 扩张 |
| `Che23` | 2023 ACM KDD | Evolve Path Tracer | 直接覆盖早期地址检测；新工作必须是证据/评测贡献而非新路径网络 |
| `Luo23` | 2023 IEEE ICBC | PU illicit-node detection | 约束 unknown 语义；未确认样本不得作为 benign |
| `Gom22` | 2022 ACM CCS | 双向 seed 扩张 | 必须作为强规则/图搜索基线；候选生成不等于独立发现 |
| `Cho22b` | 2022 journal | public abuse reports | 提供大规模报告与聚类参照；需审计报告复制关系和发布时间 |
| `Elo21` | 2021 ACSAC | streaming classification | 提供在线/反馈评测参照，但不等于独立未来证据 |
| `Oli21` | 2021 preprint | GuiltyWalker | seed 距离与 temporal walk 强基线 |
| `Fro19` | 2019 journal | 法证证据价值与 attribution tags | 约束证据强度、可追溯性和法证主张边界 |
| `Paq18` | 2019 journal | ransomware payments/campaign seeds | 多来源 ransomware seed 与时间过滤的奠基数据来源 |
| `Hua18` | 2018 IEEE S&P | ransomware end-to-end tracing | 事件种子、支付识别和资金流追踪的强同行评审参照 |

## Phase 1 观察，不构成最终结论

1. 最新方法集中在 early detection、path tracing、streaming 和 abuse-report 数据；“未来确认”通常只是固定测试标签或未来日样本，不等于来源独立的后续归因。
2. 最可能的贡献类型是数据/评测 artifact：冻结 `t0`、候选生成日志、原始证据依赖图、首次公开时间、right-censoring 与固定预算指标。
3. 最强反证是：未来页面只是原 seed 报告的转载；如果成立，`Y^ind` 不存在，方向直接 No-Go。
4. Phase 2 必须扩展到 OSINT provenance、web archive 时间、duplicate-report/source-dependence、delayed labels/right censoring 和事件级 sampling，而不能只搜 crypto detector。

## Phase 2 纳入优先级

- Tier A：`Gom24, Gom23, Gom22, Che25d, Che23, Fro19, Paq18, Hua18, Ara24, Ama26`。
- 方法参照：PU/right censoring、来源依赖、重复报道检测、历史网页存档和 selective labels。
- 数据/工具参照：Ransomwhere、ChainAbuse、GraphSense TagPacks、Internet Archive/Wayback、法院或执法原始公告。
