# Gate 2 Phase 3：全文选择

## 选择准则

按四个维度选择全文：与候选问题的直接重合、证据/标签形成机制、统计可识别性、可复现 artifact。优先正式同行评审论文；近期 preprint 只在它已形成直接 novelty collision 或提供独有数据时纳入。

| key | 选择原因 | 角色 | 当前证据入口 |
|---|---|---|---|
| `Gom22` | 最强公开 seed-expansion / tracing 基线 | 直接方法邻居 | arXiv 全文 §4–§8、Tables 2–5、8、14 |
| `Fro19` | 直接规定 attribution tag、cluster、source 与证据链要求 | 证据治理 | arXiv 全文 §3、§5–§6、Figures 4–5、Listings 1–2 |
| `Paq18` | 公开 ransomware seeds 与 MI 扩张的奠基数据 | 事件数据 | arXiv 全文 §3.1–§3.5 |
| `Ama26` | 具论坛发帖时间和多用户提及的最新标签候选 | 新数据 / 最近邻 | arXiv 全文 §3.1–§3.4、§4.2–§4.3、Table 6 |
| `Shi25` | Real-CATS/Sup-CATS 直接声称 real-world future-day transfer | 最近数据集反证 | arXiv 全文 §3、§4.3、Table 6、Open Science |
| `Mal26` | 已覆盖 chronological + fixed-budget + unknown burden | 评测 novelty collision | arXiv 全文 §3.3–§3.7、§4、§5.4、appendices |
| `Dha26` | 延迟、报告和标签腐败的近期识别理论 | 理论反证 | arXiv 全文 §3.6–§3.8、§5、§8.5、§11.2 |
| `Web19` | Elliptic 标签/时间图和主流基准的原始说明 | 基准边界 | arXiv 全文 §2–§3 |

补充交叉核验：`Gom23, Gom24, Che23, Che25d, Hua18, Ara24, Hos20, Zhu20c, Saf26`。事件可行性由两个独立审计簇分别检查 ransomware 和 hacks/enforcement；其结论进入本阶段事件表。

## 阅读问题

每篇统一回答：任务与真实决策是什么；标签何时、从何处可见；候选全集是否在预测时点冻结；是否存在未来边/聚类/页面/标签泄漏；unknown 如何处理；来源是否独立；指标对应什么 estimand；数据/代码是否可复现；最可能推翻本候选方向的结论是什么。
