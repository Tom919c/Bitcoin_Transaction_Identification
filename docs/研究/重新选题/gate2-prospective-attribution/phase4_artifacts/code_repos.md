# Gate 2 Phase 4：代码、数据与档案 artifact 核验

核验日期：2026-08-19。这里的“可访问”只表示文件/仓库能定位和版本化，不表示它足以支持候选研究问题。

## 1. `cablej/showing-the-receipts`

- **位置/版本**：[GitHub](https://github.com/cablej/showing-the-receipts)，public，default branch `main`；`addresses.csv` 当前 blob SHA `93536dd7987414500c888bfb102b2b835a9ee242`。
- **许可**：仓库 `LICENSE` 为 CC BY 4.0。
- **内容核验**：README 声称 1,013 个 likely ransomware payment addresses、近 7 亿美元 payments。公开 CSV 的固定 schema 只有 `address,type,amountReceivedUSD,amountReceivedBTC`。
- **可复现价值**：地址和金额列表可下载、可哈希、可按 commit 冻结，可作为候选 seed pool 或与链上数据做一致性检查。
- **硬缺口**：没有 ransomware family、原始报告 URL、提交者、first-public time、case ID 或 source family。无法从公开 CSV 判断某个地址属于 BlackSuit/Royal，也无法证明它在 `c` 前已知或未知。
- **判定**：**部分可用**；不能单独构成 prospective provenance benchmark。

## 2. Ransomwhere 数据与代码

- **数据**：[Zenodo v1.1.0](https://doi.org/10.5281/zenodo.13999026)，`ransomwhere.json` 5.6 MB，记录页给出 MD5 `8a7bff74ab0dea4186232bc131c5d40f`，CC BY 4.0。
- **代码**：[cablej/ransomwhere](https://github.com/cablej/ransomwhere)，public `main`；README blob `19ef409f82b4d041763cfb4f2c949b98747a5384`，MIT license blob `c1863c14c25dba5c3b775144d9e7055b1ef43987`。前端静态站点、后端 Serverless；公开 API 声称可导出历史交易。
- **内容核验**：Zenodo 说明包含 payment addresses、transactions 和 ransomware family；网站明确地址在提交后延迟 90 天公开，并承认 Showing the Receipts 的许多 payments 没有公开 family label。
- **可复现价值**：版本化快照、许可、交易和 family 字段优于普通网页列表，可作为 `c` 前 seed registry 候选。
- **硬缺口**：公开数据缺逐条原始报告/证据 URL 与可验证 first-public time；`createdAt`/公开日期受 90 天策略影响，不能直接当事件发生时间或首次外部可见时间。众包审核和多报告规则不等于 root-evidence 独立。
- **判定**：**Conditional**；必须另建来源 DAG 与 archive time interval。

## 3. `sjdseu/Real-CATS`

- **位置/版本**：[GitHub](https://github.com/sjdseu/Real-CATS)，public，default branch `master`；README blob `31ce7432d188f267b56e6284ca1f4922d07292dc`。
- **许可**：根目录没有 `LICENSE`（GitHub API 404）；在许可澄清前不可把仓库数据重新发布进我们的 artifact。
- **内容核验**：README 当前列出 40,032 Bitcoin criminal、86,583 Bitcoin benign、12,561 Ethereum criminal、15,595 Ethereum benign；另有 50k+ 无交易地址。详细交易记录指向 Kaggle。README 同时说明许多地址与 WatchYourBack/GraphSense TagPacks 重合。
- **不一致**：论文正文声称的地址总量与当前 README 表格并不一致，必须锁定论文对应 commit/data release 才能复现；positive 来自 abuse reports，benign 来自 exchange hot-wallet outputs，来源机制不同。
- **判定**：**不适合作为核心 outcome**；可作 source-shift/label-audit 对照。

## 4. `behas/ransomware-dataset`

- **位置/版本**：[GitHub](https://github.com/behas/ransomware-dataset)，public，default branch `master`；README blob `024eab0c75054822dd4c323f3d8c3f1d3dccf77f`。
- **内容核验**：包含 `data/seed_addresses.csv` 与基于 GraphSense v0.3.1 的 Scala 扩张程序；运行需要已部署的 Spark、至少两个 Cassandra 节点、HDFS 和预计算 GraphSense 数据。完整扩张数据链接到 Zenodo。
- **许可**：仓库无 `LICENSE`（GitHub API 404）。
- **可复现价值**：可以复核原始 seeds 和历史扩张逻辑，适合审计 `Paq18`。
- **硬缺口**：运行栈陈旧且重；原始 source URL 混合第三方页面；无清晰重用许可。不能作为可自由再发布的 future-outcome registry。
- **判定**：**只读审计可用，正式 benchmark No-Go**。

## 5. `citp/BlockSci`

- **位置/版本**：[GitHub](https://github.com/citp/BlockSci)，public，default branch `master`，GPL-3.0；当前可见最新 commit `14ccc9358443b2eb5730bb2902c4b11ab7928abf`，日期 2020-11-13。
- **能力**：从原始 Bitcoin blockchain 构建可查询分析结构，适合按 block height 重建历史链和验证金额/日期/地址交易。
- **限制**：项目多年未更新；现代 Bitcoin Core/编译环境兼容性和当前链解析必须先做小规模 smoke test。它也不提供网页/执法证据 provenance。
- **判定**：**链上重放候选**；若维护成本高，优先原生 Bitcoin Core RPC/现有数据库查询，而不是为工具本身付出研究工程成本。

## 6. 本地 252M 实体图 artifact

- **物理内容**：`bitcoin-dataset/dataset/dataset/3617.dat` 约 46.6 GB，`3618.dat` 约 27.0 GB，PostgreSQL 15.4 custom dump；`toc.dat` 可定位 schema。
- **schema**：`transaction_edges(a,b,reveal,last_seen,total,min_sent,max_sent,total_sent)`；`node_features(alias,...,first/last_transaction_*,cluster_*,label)`。图有实体 alias 和边的 reveal/last_seen，但没有原始 address、txid、block hash 或 address-to-alias union lineage。
- **标签旁表**：`bitcoin-dataset/addresses.csv` 有 103,812 行、12 类、8 个来源；39,275 行的 `entity` 是人类可读服务/家族名，不是图中数值 alias 映射。
- **结论**：该 artifact 可支撑原 11 类 entity-type 研究，却不能把 DOJ/FBI 公布的新地址稳定映射到 252M 图节点，也不能重建地址级历史候选全集或动态聚类。它不满足当前主方向的数据单位要求。

## Phase 4 验收与判断

已核验 5 个外部仓库/数据发布和 1 个本地 artifact，超过“至少 3 个”要求；但“可访问”不等于“可用于主问题”。

- 可稳定版本化：Showing the Receipts、Ransomwhere、Real-CATS、历史 ransomware dataset、BlockSci。
- 具明确数据重用许可：Showing the Receipts、Ransomwhere；Real-CATS 和旧 ransomware repo 根目录无 LICENSE。
- 具 address + family/transaction：Ransomwhere；但缺逐条来源和 first-public provenance。
- 能按链上时间重放：BlockSci/Bitcoin Core 或新建地址级索引；本地 252M 实体图不能替代。
- 能直接支持三个独立未来归因事件：**0**。

因此 Phase 4 的实质结果仍是 **No-Go for formal benchmark now**。唯一允许的后续工程是最小 BlackSuit/Royal 零模型唯一匹配测试与法律文书附件 registry；在它成功前，不建立新训练管线。
