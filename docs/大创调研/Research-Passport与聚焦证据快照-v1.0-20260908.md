# Research Passport 与聚焦证据快照 v1.0

日期：2026-09-08

状态：Gate 0 条件未关闭；Gate 1 聚焦增量审计已完成第一轮，Yin 2019 已全文闭环，BitLINK 作者幻灯片已核验但论文正文仍未闭环；Zenodo 最小训练包已核验并对 PIT 重放作 No-Go，其他大包及内部语义保持 Unknown；AWS 公共比特币数据已完成匿名入口、对象清单、样本 schema 与 50 GiB 早期前缀候选预检，并关闭 block-metadata selected-set 映射与执行脚本 revision 两项原型 P1；许可证据支持私有内部冻结，但公开再分发、项目控制的 transaction 字节冻结和全量交易完整性仍未关闭；Gate 3A 已形成 v0.1 待冻结草案

研究分支：`asof-entity-graph-pilot`

本分支起点：`bc5703a650587643fca7140fc579310c6f09349e`

启动提交：`734fd098fb53c6d07a0e584381ab7b1bed155097`

## 1. 当前裁决

项目方向保持为“严格按时可见实体图与可信识别”，但创新主张必须收紧：

> 在固定原始链前缀、固定历史截止点和可审计标签口径下，受控量化 final-vintage 地址聚类相对 point-in-time/as-of 地址聚类对预测单位、实体图、实体类型模型比较、概率决策和有限人工审查队列的影响。

本项目不再把“未来聚类知识会回写历史并产生 look-ahead bias”作为新发现。Glassnode 已在 2023 年的一手研究说明中明确描述该现象并给出 point-in-time 数据作为补救。当前未检出的是完整的学术端到端实验：固定历史信息集，只改变地址分区版本，再把差异传播到实体类型预测、校准、选择性预测和固定预算队列。

2026 年 9 月 1 日公开的预印本 *Refining Heuristic-Based Bitcoin Address Clustering with Graph Neural Networks* 已直接覆盖“用 GNN 表征细化启发式聚类、发现可疑错误合并、给出候选拆分”这一方法空间。因此，启动章程中的条件 D 只能作为最近邻基线或敏感性条件，不能预设为本项目的新方法贡献。

当前决策是：保留方向，停止宽泛的新颖性表述；先完成无模型、可重放的数据机制审计。Gate 3A 冻结前不训练新模型，不打开正式测试结果，不重建 2.52 亿节点全图。

## 2. Research Passport

### 2.1 研究问题与用途

历史决策时钟以 Bitcoin 主链区块高度 `t` 表示。目标不是事后取证，而是模拟在 `t` 时可获得的信息下进行实体类型识别和人工复核排序。若研究问题改为事后归因，使用最终分区 `C_T` 可以是合法的 hindsight 信息，此时不能称为部署泄漏。

预测标签为仓库已有的 11 类实体类型 `0–10`；`-1` 是未标注图上下文。实体类型不等于非法活动、欺诈或 AML 风险，任何二元风险任务都需要另行定义和取得可核验标签。

### 2.2 形式对象

- `X_{<=t}`：主链中区块高度不晚于 `t` 的原始交易、输入、输出和脚本记录。
- `U_{<=t}`：只由 `X_{<=t}` 和版本冻结的启发式规则产生的地址/脚本合并事件；每个事件必须保留区块高度、区块内顺序、规则、版本和证据。
- `V_t`：在 `X_{<=t}` 中已经出现的地址或脚本标识集合。
- `C_t = DSU(U_{<=t})`：从空状态按确定顺序重放得到的 as-of 分区。
- `C_T|V_t`：完整观察期 `T` 的最终分区限制到同一地址支持 `V_t`；不得把 `T` 后才出现的地址加入比较。
- `G(C, X_{<=t})`：在相同交易前缀上用分区 `C` 聚合得到的实体图。
- `L_{<=t}`：发现、公开或采集时间不晚于 `t` 的标签版本。若无法获得标签可得时间，标签只能作为回顾性评价或结构诊断，不能支撑历史部署主张。

主要因果对照是 `G(C_T|V_t, X_{<=t})` 与 `G(C_t, X_{<=t})`。两者必须共享原始交易前缀、地址支持、过滤规则、标签规则和模型预算；否则差异不能归因于分区版本。

### 2.3 当前数据与代码资产

| 资产 | 已核验能力 | 当前限制 | 证据位置 |
|---|---|---|---|
| 本地 2.52 亿节点实体图接口 | 可流式读取 `node_features` 与 `transaction_edges`；节点含最终 `alias`、统计特征和实体类型标签，边含首次/末次出现区块及聚合金额 | 没有地址/脚本表、单笔交易输入分组、合并事件、规则版本和合并证据；不能逆推出 `C_t` | `src/btcaml/data/db.py`、`src/btcaml/data/schema.py`、`configs/data/raw_db.yaml` |
| 协议数据构建 | 可从最终实体图生成处理数据；标准化在训练期拟合 | 继承最终 alias；不是 as-of 重放 | `scripts/build_protocol_dataset.py`、`src/btcaml/data/build_graph.py` |
| 上游公开构图代码 | 能从 Bitcoin Core 原始块解析 TXO，逐区块运行多种启发式，并以 Union-Find 合并 | 只写最终 `Alias(node_id, alias)`；`UnionFind.union` 不记录时间、规则或证据；需审计每个启发式的未来可见性 | `hugoschnoering2/BTCGraphConstruction` 的 `steps/populate_alias.py`、`clustering/unionFind.py` |
| 协作交易过滤 | 已核验固定 revision `3becbc44a951abbe1e85d374a66340a639059d1c` 的五个实际 mix detector、Tx0 detector、特征定义和聚类排除调用链 | 是规则检测结果，不是真值；源码 Tx0 条件与论文不等价，参数也有差异；PayJoin 仍未判定 | 上游 `blockchain/special_transactions/coinjoin.py`、`blockchain/models/transaction.py`、`steps/populate_coinjoin.py`、`steps/populate_alias.py`、`database/utils.py` |
| 本地原始块解析片段 | 可解析部分原始块、交易和脚本结构 | 不是完整、已验证的全链索引与 prevout 管线 | `scripts/scan_block_sighash.py` |
| 资金流证书代码 | 可检查局部 DAG 与价值守恒性质 | 与地址聚类重放不是同一任务，只可复用检查模式 | `src/btcaml/analysis/flow_certificate.py` |
| 实验可追溯模式 | 历史 SSL manifest 提供版本、依赖和产物哈希范式 | `experiments/experiment_registry.csv` 已创建且只有冻结表头，尚无实验行；正式运行前必须登记 planned 行 | 既有 SSL 产物与 `experiments/` |
| 当前工作树与本机原始链 | `data/README.md` 存在；已检查仓库与受控的 Windows 默认 Bitcoin Core 路径 | 仓库 `data/` 为空；未发现 `blk*.dat`、原始 TXO/manifest 或 Bitcoin Core datadir；当前进程也未设置数据连接变量 | 本地只读检查，2026-09-09 |

`BITCOIN_DB_URL` 是外部敏感配置。本记录不保存连接串；任何诊断不得打印凭据。

BigQuery `crypto_bitcoin` 仍是候选，但字段语义已得到更强的一手核验。[Google BigQuery 公共数据说明](https://docs.cloud.google.com/bigquery/public-data)、[GoogleCloudPlatform knowledge catalog](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/bundles/crypto_bitcoin/viz.html) 与 [Bitcoin ETL schema](https://github.com/blockchain-etl/bitcoin-etl/blob/master/README.md#schema) 一致确认：交易记录含区块哈希、高度、块内 index 与 coinbase 标志；input 含 `spent_transaction_hash` 和 `spent_output_index`；output 含金额与 locking `script_hex`。因此可用父交易键连接到 output 恢复 prevout script；input 自身的 `script_hex` 是 scriptSig，不能替代 locking script。尚未关闭的是实际表版本／快照、唯一主链与重组处理、缺失／重复率、许可适用、查询成本与导出 hash，故仍不能计为已满足数据硬门。现有 raw-block parser 也只是局部解析片段。

公开管线层面的证据进一步收紧了这一判断。[Blockchain ETL 公共数据登记](https://github.com/blockchain-etl/public-datasets/blob/master/README.md)报告 Bitcoin lag 为 3 块，[Bitcoin ETL](https://github.com/blockchain-etl/bitcoin-etl/blob/master/README.md#stream)把 lag 称为处理重组的最简单方法；这只能说明链头缓冲，不能证明公共表提供不可变 vintage 或完整重组对账。已新增一份从创世块开始、只计算数据完整性的资格查询和一份不含凭据的 manifest 模板；两者当前均未执行。局部高度 smoke 不足以资格化正式 `C_t`，因为共同输入 union 依赖完整历史前缀。

2026-09-09 官方入口审计审阅了 Bitcoin ETL README、public-datasets README、[Bitcoin ETL streaming 文档](https://github.com/blockchain-etl/blockchain-etl-streaming)和公开架构说明。在已审官方文档中，未发现无需部署者凭证即可访问、带版本标识的历史 GCS 快照；streaming 部署关于 GCS 的说明要求使用者创建并配置自己的 GCS bucket，以保存 `last_synced_block.txt` 状态，未给出公开历史数据对象、manifest 或回放保证。已审文档把 Pub/Sub 描述为持续流式出口，并报告 Bitcoin lag 为 3 块，但未承诺公共 topic 可从创世块回放到冻结高度的完整、版本化前缀；当前没有独立冻结导出／快照和完整性审计，不能把它资格化为 S0 输入。在当前已审官方入口范围和本地资产条件下，待资格化候选暂收束为：(1) BigQuery 经授权 dry-run、资格查询、冻结导出；(2) 用户提供的 Bitcoin Core datadir 或 raw TXO snapshot，经版本、tip、hash、容量审计。该收束不表示已经穷尽其他可能满足硬门的原始链来源。

2026-09-10 的增量审计新增 [AWS 公共比特币数据源资格审计](AWS公共比特币数据源资格审计-20260910.md)。AWS Open Data Registry 允许无账户匿名访问 `s3://aws-public-blockchain/v1.0/btc/`；实际 Parquet 样本包含 block hash/height/prevhash、块内交易 index、coinbase、input prevout 和 parent output locking `script_hex` 等必要字段，指定现代交易也与独立 Blockstream API 一致。该证据只把 AWS 提升为 schema 与访问方式已做样本核验的候选。50 GiB 候选预检现已由冻结清单、脚本哈希、1897 个 block object 身份/本地 SHA、首跑和零下载复跑支撑，两个成功结果在忽略缓存状态与输出路径后逐字段相等；这关闭了原型 selected-set 映射和执行 revision 两项 P1。一次沙箱写入限制导致的失败已经如实登记，脚本随后增加 stage 2 前输出探针并通过合成自测；该保护未被表述为第三次全量数据复跑。固定 Registry 元数据、MIT-0 文本和 2025-09-11 版 AWS Open Data Sponsorship Program 条款共同支持当前匿名对象的私有内部冻结与分析，但不由代理解释为公开再分发授权。清单时点的 transaction 对象约 2,026.838 GiB，远超本机可用空间；桶未启用 S3 Versioning，且样本对象 `VersionId=null`，历史对象可被替换；金额实际为 `double`。由项目控制且可复查的 transaction 字节冻结、全量交易／prevout 完整性、整数聪转换、正式环境和公开 artifact 许可仍为 pending，所以不关闭数据硬门，也不启动 S0。若以后采用早期完整前缀，末端必须在读取效应前只按资源规则预注册，并从创世块完整处理到每个 `T_j`；其结论不得外推到当前时期。

### 2.4 算力、环境与预算

- 治理目标要求以 `pyproject.toml` 与 `uv.lock` 作为依赖真源并使用仓库级 `uv` 环境；已提交历史中仍没有受版本控制的 `uv.lock`，当前隔离工作树出现一个来源与一致性均未审计的未跟踪 `uv.lock`，不能视为依赖真源。AWS 样本审计使用的是未纳入锁文件的本机 Python 3.12.3 与 PyArrow 16.1.0，只能算资格检查，不能冒充正式可复现运行环境。
- 当前隔离工作树未检测到可用的 `nvidia-smi`，不能宣称有 GPU。无模型数据 Gate 必须能在 CPU 和小窗口上完成。
- 2026-09-10 新增 [Kaggle 私有算力接入审计](Kaggle私有算力接入审计-20260910.md)。账号 `camellia99` 的 OAuth、额度查询、私有 T4 脚本提交、状态轮询和产物回收闭环已通过；版本 1 在 Python 3.12.13、PyTorch 2.10.0+cu128、CUDA 12.8 上实际完成一次 CUDA 张量运算，并看到两张 Tesla T4。该结果只把 Kaggle 提升为可选远端执行资源，不是数据源、正式实验环境或 Gate 证据；正式运行仍须冻结输入 manifest、环境、预算、checkpoint 和输出追溯，并遵守单次运行、持久空间和每周额度限制。
- 本机 2026-09-10 只读资源快照：`C:` 可用 125,963,497,472 字节，`D:` 可用 139,442,827,264 字节，物理内存 29,734,326,272 字节；未发现 Bitcoin Core 数据目录。尚未核验 PostgreSQL 实例容量，也不能据剩余空间推定任何全链方案可行。
- 不以工程工作量否决方向，但数据许可、可重放性、磁盘安全和可证伪性是硬门。
- 任何 BigQuery 或外部源试探都必须先取得项目与账单授权并预设扫描字节和费用上限；快照、schema、主链／重组语义与成本记录未齐备前，不发起付费或大规模查询、不冻结数据源、不运行正式 Pilot。
- BigQuery 资格查询必须先以完全相同的文件、参数做 dry-run，再把估算扫描字节、人工批准的 `maximum_bytes_billed`、查询时点、表元数据与查询哈希写入 manifest。局部窗口结果不允许支撑正式 Go/No-Go。

### 2.5 行政、伦理与许可

- 正式立项题名、任务书、项目编号、结题材料版本和成果承诺仍未进入当前分支的可核验输入，Gate 0 因此不能完全关闭。
- 公开链数据不等于可以对真实主体作风险指控。演示系统只能展示“实体类型识别结果”“不确定结果”和“待复核对象”。
- 现有标签含论坛、公开名单和外部来源，可能存在错误、时间漂移和选择偏差；没有发现/公开/采集时间时，不得用于严格历史部署训练。
- Zenodo 官方 record 已确认 CC BY 4.0、三个外层 ZIP 的文件名、大小和仓库声明 MD5；仅最小训练 ZIP 已下载并本地复算 MD5/SHA-256，其余两包未下载、内部成员清单与 checksum 未取得，因此不把整个 release 写成已可用本地数据。
- 不向外部模型或服务上传数据库内容、私有标签、未发表手稿、连接信息或凭据。

## 3. Gate 1 聚焦 decision corpus snapshot

### 3.1 快照范围

检索日期：2026-09-08；增量核验至 2026-09-09。

目标：寻找完整等价工作和反证，而不是扩大一般 Bitcoin AML 综述。纳入项必须至少触及下列一项：按时间更新的 Bitcoin 地址聚类、最终与历史分区差异、聚类误差真值、严格时间图评测、实体类型预测、概率校准或固定预算队列。

排除或降级：只在随机切分上刷分、只删除未来边但不改变实体分区、只做静态聚类准确率、只研究通用动态图、只有搜索摘要、无法确认预测单位或数据来源的工作。

### 3.2 两条独立检索链

链 A 为 Undermind 增量深检，工作区 `quan's workspace`，搜索路径 `/01 Discovery/As of Bitcoin Entity Identity Leakage Incremental`。目标查询完整限定了 `C_t/C_T`、固定地址支持、union 时间与 provenance、下游模型排序/校准/队列，以及 decisive No-Go。搜索返回 16 篇相关工作；摘要级综合未发现完整等价论文。随后对 `Mos21`、`Sch24c`、`Mul26`、`Sch24`、`Mag26`、`Mal26` 和 `Kha26` 做了全文定向问答；DOI lookup 另定位 `Zho24`，书目/摘要匹配但 PDF 状态为 X（未取得 PDF），不按全文计入。旧搜索 `/01 Discovery/Temporal Entity Resolution Error Propagation` 与 `/01 Discovery/Provenance Preserving Bitcoin Benchmark Reconstruction` 仅作为历史独立发现池，不重复计数。

链 B 由主负责人和一名不继承结论的反方审查者独立执行，查询包括：

- `"temporal address clustering" Bitcoin entity resolution`
- `"dynamic address clustering" Bitcoin`
- `Bitcoin address clustering "as of" time`
- `Bitcoin address clustering "look-ahead" bias`
- `"future transactions" "address clustering" Bitcoin`
- `Bitcoin entity type prediction address clusters supervised learning`
- `temporal graph leakage future information evaluation`
- `Bitcoin entity classification address clustering temporal evaluation`
- exact-title/DOI 查询：`BitLINK: Temporal Linkage of Address Clusters in Bitcoin Blockchain`、`Online Temporal Data Mining and Learning: Pursuing Enhanced Efficiency and Robust Algorithms`、`10.1145/3637528.3672037`；以及作者名与 `site:digitalrepository.unm.edu`/UNM domain 定向查询

链 B 只把论文原文、出版社页面、作者/机构正式页面、官方数据仓库和官方代码作为主张证据。搜索摘要只用于发现。

### 3.3 关键来源与碰撞表

| 来源 | 状态 | 已核验事实 | 对当前方向的影响 |
|---|---|---|---|
| Glassnode, *Introducing Point-in-Time Data* (2023) | 官方全文，source-verified 与 interpretation-verified | 地址聚类知识会随时间扩展并触发历史指标重算；将可回写聚类指标用于机器学习会产生未来聚类知识的 look-ahead bias；PIT 数据冻结历史版本 | 对“发现泄漏现象”构成 Critical collision；不是同行评审论文，不能单独证明本项目的学术增量已被覆盖 |
| Möser & Narayanan, *Resurrecting Address Clustering in Bitcoin*, FC 2022, DOI `10.1007/978-3-031-18283-9_19` | Undermind 全文核验 | 未来地址重用和多输入关系可揭示过去 change 输出；增强聚类使两项纵向分析发生约 11.9% 与 13.8% 的变化 | 证明未来交易可改变历史归并与下游统计；未做 `C_t/C_T` 实体类型预测、校准和队列审计 |
| Schnoering et al., *Assessing the Efficacy...*, arXiv `2403.00523` | Undermind 全文核验 | 从平凡分区开始逐区块更新聚类，报告不同启发式聚类率的时间演化 | 已覆盖增量 `C_t` 构造和时间统计；未对照 final-vintage 分区，也未传播到下游预测 |
| Schnoering & Vazirgiannis, *Bitcoin research with a transaction graph dataset*, DOI `10.1038/s41597-025-04684-8` | 出版社全文与 Undermind 全文核验 | 对前 700,000 个区块先形成约 2.52 亿最终 alias，再发布聚合节点/边；标签被投影到最终 cluster，冲突 cluster 不标注 | 现有图适合作为 final-vintage 条件，但公开聚合表不足以重建 `C_t` |
| Müller et al., *How Reliable Is the MIH...*, arXiv `2607.07414` | Undermind 全文核验 | 受监管服务商真值上的静态评估显示，考虑完整 cluster 时 per-wallet precision/recall 约为 0.36/0.44，实体间差异大 | 强制将聚类误差和敏感性纳入协议；未做纵向或下游预测 |
| Maganti, *When Graph Structure Becomes a Liability*, arXiv `2604.19514` | Undermind 全文核验；预印本 | 严格归纳设置只让编码器看到训练期子图；其主要差异来自未来测试节点/边和全图统计；报告 RF 与 GNN 排名差异并评估校准 | 证明严格时间协议可改变模型结论；预测单位是交易，不涉及实体分区版本 |
| Khaleghpour & McKinney, *Leakage Safe Graph Features...*, arXiv `2603.06632` | Undermind 全文核验；预印本 | 用 `G_{<=t}` 计算因果图特征，评估 Brier/校准和 Precision@K | 校准与预算队列不是本项目可单独主张的新指标；仍未改变地址实体分区 |
| Malik, *Do Transaction-Level and Actor-Level AML Queues Agree?*, arXiv `2604.23494` | Undermind 全文核验；预印本 | 固定 1% 预算比较交易级与地址级队列；文中 actor 明确定义为地址，不是真实解析实体 | 与队列粒度效应直接相邻；未研究聚类版本，要求本项目报告固定预算与单位映射 |
| Zhong & Mueen, *BitLINK*, KDD 2024, DOI `10.1145/3637528.3672037` | 官方作者 CV、主页、22 页作者幻灯片与 UNM 学位论文元数据/摘要核验；正文 PDF 未取得 | UNM 记录列出 Sheng Zhong 学位论文及摘要中的 BitLINK；作者幻灯片明确把 address flushing 定义为旧簇被放弃后很快生成新簇，并将任务表述为连接 cluster-chain fragments；桥接簇可由前后簇交叉验证 | 直接否决“首次研究 temporal cluster linkage/cluster chain”措辞；学位论文 PDF 未取得，不能关闭论文正文 checklist，也不能据此判定 `C_t/C_T` 固定支持或可重放 union lineage |
| Yin, Mukkamala & Vatrapu, *Regulating Cryptocurrencies...*, JMIS 2019, DOI `10.1080/07421222.2018.1550550` | 出版社元数据与作者公开全文核验 | 以 Chainalysis 提供的 957 个已分类地址簇作多类预测；数据截至区块 512,033，采用 75/25 随机式切分与训练内三折交叉验证；聚类含共同花费、外部情报和人工合并，未提供 lineage 或标签可得时间 | 否决“首次做 Bitcoin 实体簇类型预测”；不能断言其使用截止块后的未来分区，但其不透明终态聚类与随机切分是本项目必须控制的近邻风险 |
| Schnoering et al., *Refining Heuristic-Based Bitcoin Address Clustering with GNNs*, arXiv `2609.01942` | 官方 arXiv HTML 全文核验；预印本 | 以启发式 cluster 为训练标签，用对比式 GNN 表征和层次聚类检测可疑合并；训练/验证/测试来自不重叠区块区间；发布的地址图字段是聚合节点、边和 cluster 映射 | 对“聚类置信度/细化 GNN”构成直接方法碰撞；其非重叠交易切分不等于 cutoff-specific identity；正文所称代码仓库当前为空，复现性仍需核验 |
| `BTCGraphConstruction` 官方代码 | 官方 GitHub 源码核验 | `populate_alias.py` 按区块收集合并并更新 `UnionFind`，最终只落 `node_id -> alias`；没有 union-event logger | 为小窗口重放提供最接近上游实现，但不能直接把其最终 alias 当作历史分区 |

补充反证中，正式文献已经覆盖未来交易揭示过去 change、动态聚类、按日期截断数据和时间图严格评测等组成部分。当前结论只能写成“截至本快照未检出完整等价工作”，不能写成“全球首次”。

### 3.4 新预印本的数据工件审计

arXiv `2609.01942` 报告三个训练图、一个验证图和一个测试图来自不重叠区块区间，并声明 Zenodo DOI `10.5281/zenodo.22239038`、CC BY 4.0。附录公开字段包括节点、地址级聚合边和 cluster 映射；正文没有给出逐 union 事件日志。

官方 `hugoschnoering2/btc-graph-hc` 仓库在 2026-09-08 的 GitHub 元数据显示大小为 0；2026-09-09 再次读取官方仓库页，页面仍明确显示 “This repository is empty.”。本 decision snapshot 因而把代码状态冻结为“截至 2026-09-09 未公开可读实现”，但不外推未来仍为空。`BTCGraphConstruction` 仓库可读，README 为空，源码保留原始块解析和最终 alias 构建。

2026-09-09 的 DataCite 官方 DOI 注册记录已确认 Zenodo `10.5281/zenodo.22239038` 的标题为 *Bitcoin transaction graphs: training, labelled entities, and CoinJoins*，版本 `1.0`，issued date 为 2026-09-01，creators 为 Hugo Pierre Philippe Schnoering 与 Michalis Vazirgiannis，许可为 CC BY 4.0，并以 `IsVersionOf` 指向概念 DOI `10.5281/zenodo.22239037`。注册元数据的 deposited description 列出 `1_training_dataset.zip`、`2_labels_eval_dataset.zip` 和 `3_coinjoin_eval_dataset.zip`，并声称标注／CoinJoin 图目录含 `node_features.parquet`、`edge_features.parquet`、`clustering.parquet` 与 `metadata.json`。

Zenodo 官方 record API 随后恢复可读。取得的 record JSON 创建时间为 `2026-09-01T22:34:47.018801+00:00`、更新时间为 `2026-09-01T22:34:47.335246+00:00`，原始响应 SHA-256 为 `674F70DAFCD5DAEABC154A209862D6B45A2CE6E1A55E4D189A25AF84B5223D1D`。API 给出的三项文件元数据为：`1_training_dataset.zip`，410,978,944 字节，`md5:ff69c727f0a63bece2c524adb97090a9`；`2_labels_eval_dataset.zip`，2,520,167,227 字节，`md5:f65536cd4f67311678dc67eea1c02195`；`3_coinjoin_eval_dataset.zip`，12,268,153,610 字节，`md5:ab3624eb568d796acc2e1b32045561da`。总压缩体积为 15,199,299,781 字节。MD5 是 Zenodo 声明值，尚未由本地完整下载独立复算。

为避免无审计地下载约 15.20 GB，中央目录探测设置了 64 MiB 总响应体硬上限，并要求每次请求必须返回有效 `Content-Range`；唯一一次 Range-only 尝试没有生成可用响应，按预先停止线未重试、未读取成员、未下载 ZIP。因此只关闭“外层文件名、大小与 Zenodo checksum 声明”，内部成员路径、压缩／解压大小、CRC、实际 schema、raw transaction/outpoint/script、主链／重组信息和 union lineage 仍为 Unknown。该 release 继续 No-Go 为当前 `C_t/C_T` 重放输入；是否下载任一完整文件必须在独立磁盘预算和数据价值审查后决定。

经明确的 410,978,944 字节上限后，只下载最小的 `1_training_dataset.zip` 到系统临时目录。文件 MD5 与 Zenodo 声明 `ff69c727f0a63bece2c524adb97090a9` 一致，本地 SHA-256 为 `7A1E0E1B76F5D9FF487DF0B005BC3E24E1A73464A25AABB7FB73AF9CF0413BC4`。ZIP 有 24 个成员，压缩成员合计 410,974,640 字节、未压缩合计 2,411,465,040 字节；没有 README、metadata、manifest 或 schema 文件。五组 `train/{0,1,2}`、`valid/0`、`test/0` 各只有三个 CSV，首行在所有组完全一致：

- `node_features.csv`：`node_id,degree_in,degree_out,total_transactions_in,total_transactions_out,first_transaction_in,last_transaction_in,first_transaction_out,last_transaction_out,min_sent,max_sent,total_sent,min_received,max_received,total_received`；
- `edge_features.csv`：`a,b,reveal,last_seen,total,min_sent,max_sent,total_sent`；
- `clustering.csv`：`node_id,alias`。

CSV header 只确认 node-style feature 字段、edge-style 的 `a,b,reveal,last_seen,...` 字段和 `node_id,alias` 映射；没有 metadata 或数据行证据独立说明 `a/b`、`reveal/last_seen` 的精确语义，也不能仅凭列名断言 alias 的 vintage。即便如此，header 明确没有 `block_hash`、块内交易位置、`txid`、input/output index、prevout、原始 locking script、coinbase 或 union-event provenance；`reveal/last_seen/alias` 无法补出输入分组和原始脚本。因此它不能从创世块确定性重放本协议的共同输入 `C_t`，该训练包对 Gate 3A 数据硬门为确定 No-Go。检查只读取 ZIP 中央目录和每个 CSV 首行，没有读取 `clustering.csv` 数据行、标签、效应或模型结果。其余 2.52 GB/12.27 GB 包未下载；这不证明其内部 schema 相同，但在没有 raw-chain 证据前不继续扩大下载。

### 3.5 CoinJoin 过滤器源码—论文核验

2026-09-09 已逐项读取 `BTCGraphConstruction` 固定 revision `3becbc44a951abbe1e85d374a66340a639059d1c` 的 detector、交易特征、CoinJoin 表写入、alias 构建和 SQL 排除路径。上游 `populate_coinjoins` 对 JoinMarket、Wasabi 1.0/1.1/2.0、Whirlpool mix 与 Whirlpool Tx0 六个标志取 OR；`populate_alias(..., exclude_coinjoin=True)` 随后按 CoinJoin 表中的区块和交易位置整体排除，因此命中的 Tx0 也会阻断共同输入 union。

仓库内原论文 `cp13_coinjoin.pdf` 的 SHA-256 为 `2DA3099D48A528E11C777FF08E59D1980049815CA04E1215DC084614E612DCB9`。论文第 12–14 页把 Tx0 描述为进入 pool 前、尚未混合的 pre-mix 准备交易，并以“恰一个金额为 0 的输出”为必要条件；第 19 页的最终 CoinJoin 汇总明确排除 Tx0。固定源码却以“输出下标 0 是否存在”实现首个 Tx0 检查，并在存在时直接返回 `False`，同时其 Tx0 与 Whirlpool mix 默认参数也不同于论文实验参数。

据此，Gate 3A 主 `F_pub` 不机械继承上游六标志 OR，也不把论文规则静默改写进固定实现，而是冻结为五个实际 mix detector 的固定实现 OR，明确排除 Tx0 detector。论文参数差异进入预注册诊断 `D_wp100k` 与 `D_tx0-paper`；二者不是 ground truth，不单独支持 Go。独立反方指出的剩余风险是：异常或多方 Tx0 仍可能破坏共同输入假设，且五个 detector 的假阳性、假阴性未知；因此必须报告诊断差集、`F_wide` 和 `F_none`，结论只能表述为对已定义操作性 profile 的稳健性。

## 4. 贡献边界与反方结论

### 4.1 已被覆盖的主张

- 地址聚类会随新增交易或标签知识改变。
- 用后来修订的聚类数据回测过去可能形成 look-ahead bias。
- 应使用 point-in-time/as-of 数据避免该偏差。
- 未来边、全图消息传递或全图统计会破坏严格时间评测。
- 地址聚类误差可能显著影响下游统计。
- GNN 可以被用于细化启发式 cluster 或标记可疑合并。

这些内容只能作为问题动机和最近邻，不作为本项目独立创新。

### 4.2 尚可证伪的窄贡献

在同一 Bitcoin 原始链前缀、同一地址支持、同一过滤与标签规则下，首次在本数据与任务上受控回答：

1. final-vintage 分区相对 `C_t` 造成多少 partition drift、实体节点变化、边重写和标签投影变化；
2. 这些变化是否跨窗口、跨合理 CoinJoin 过滤条件稳定，而不是某个启发式偶然性；
3. 在完全相同的训练和调参预算下，模型排名、概率校准、选择性风险—覆盖率以及固定预算 top-k 队列是否发生可重复变化；
4. 变化能否被分解为 partition drift、cluster-quality drift、label-vintage drift 和普通特征时间漂移。

贡献上限是可复现 benchmark、数据 lineage、评测偏差归因和决策层实证。除非后续理论卡得到非平凡证明和反例审查，不预设理论贡献；除非条件 D 实质上超越 2026 新预印本，不预设新聚类模型贡献。

### 4.3 最强反论与控制

| 反论 | 必须控制 |
|---|---|
| `C_T` 对事后取证是合法信息 | 明确部署时钟；仅对当时可行动预测使用“泄漏”措辞 |
| cluster 不是真实实体 | 同时报分区变化与聚类可靠性；加入保守/宽松过滤敏感性；不作真实所有权断言 |
| 标签本身也会回写 | 冻结 `L_{<=t}`；若没有标签时间，则只作回顾性结构/评价，不作部署训练 |
| B/C 支持集合不同造成伪差异 | 固定 `V_t`，将 `C_T` 限制到 `V_t`，所有交易和特征只来自 `X_{<=t}` |
| 结构变化不必然改变模型或决策 | 将图、预测、校准、拒判和队列视为不同 estimand，分别预注册，不从一个结果外推另一个 |
| 差异来自单一过滤器或 cluster collapse | 至少两种合理 CoinJoin 过滤；报告启发式与过滤条件交互；保留负结果 |

## 5. Gate 状态与阻断项

### Gate 0：条件未关闭

已完成仓库资产、上游公开代码、环境和主要风险盘点。本机受控路径没有可用 Bitcoin Core 数据目录，仓库没有原始链快照；BigQuery 已完成字段与公开管线语义审计，并已准备资格查询及 manifest，但尚无项目／账单授权、dry-run 费用记录和可复现导出。以下输入仍缺失：正式任务书/立项题名；已选原始链入口；数据版本、tip 与哈希；内存和数据库容量；外部标签的获取和许可记录。

### Gate 1：第一轮聚焦快照完成，仍未完全关闭

双链检索、关键全文核验和独立反方审查已经完成。关闭前仍需：

1. 核验 BitLINK 全文是否包含可重放 cluster lineage；2026-09-09 已定位 UNM 学位论文官方元数据与摘要（Sheng Zhong，*Online Temporal Data Mining and Learning: Pursuing Enhanced Efficiency and Robust Algorithms*，2024-05-11），摘要列出 BitLINK；UNM direct download 遇 Cloudflare challenge，ACM DOI／正文入口返回 HTTP 403，两者均未取得 PDF。作者主页幻灯片已取得并完整读取（22 页，19,771,433 字节，SHA-256 `1DB891F815154C5E4E8BF49F9FE1AACEDFE0CD6A30EECCFE428A76AAC642CFCA`），但不能关闭论文正文 checklist。最近邻 checklist 第 1、2、4、5 项仍为 Unknown；第 3 项只确认概念级有序簇链，未确认可重放 lineage；禁止写“BitLINK 未做 `C_t/C_T`”“本项目首次研究 temporal cluster linkage”或“本项目首次连接 cluster chain”；
2. Zenodo `22239038` 的 DataCite 与 record API 元数据、版本、许可、三个外层文件名、大小和 Zenodo MD5 声明已核验；最小训练包已经本地校验并完成中央目录／CSV header 审计，确认缺少本协议必需的 raw transaction/outpoint/script 与 union provenance 字段，作为 PIT 重建数据源 No-Go。node/edge/alias 列的精确语义及其余大包内部 schema 保持 Unknown，不因列名或文件名推断；
3. 2026 新预印本的官方代码仓已在 2026-09-09 冻结为空仓快照；后续只有新 decision snapshot 才能改变该状态；
4. 继续将其余纳入来源按 DOI/标题去重并补稳定 BibTeX 与页码定位；Yin 2019、BitLINK、Zhong 2024 学位论文、2026 GNN 聚类预印本、Glassnode PIT 与 Möser–Narayanan FC 2022 已作为相互独立版本写入 `references.bib`。学位论文仅为元数据/摘要 source-verified，全文仍未取得。

Yin et al. 2019 的剩余全文项已经关闭：其预测单位是专有地址簇，交易截止为区块 512,033（2018-03-04 23:58:21 UTC），采用 75/25 随机式切分和训练内三折交叉验证；全文没有 cluster lineage、label availability cutoff 或 `C_t/C_T` 对照。它是实体类型预测的 Critical 近邻，但不是已经核验的完整等价评测。

BitLINK 的当前证据边界不是“完整等价已排除”，而是“风险仍未关闭”。作者幻灯片足以证明它显式研究 address flushing、前后簇桥接和按时间延伸的 cluster chain，因此这些对象不能作为本项目独立创新；但幻灯片不足以证明或否定本协议的固定历史窗口、`C_t/C_T` 固定支持对照、可重放共同输入 union lineage 和下游决策传播设计。无法访问正文不能当作论文没有报告这些内容，幻灯片中的特定服务归属和金额也不进入本项目事实主张。

### Gate 2：方向保持，创新叙事已修订

用户对“严格按时可见实体图与可信识别系统”的方向确认继续有效；确认不等于批准宽泛的首创表述。核心创新从“发现未来聚类泄漏”改为“可审计、受控、可复现地测量其对实体类型预测与决策的影响”。

### Gate 3A：v0.1 待冻结

已形成[严格按时可见实体图预注册协议 v0.1](Gate3A-严格按时可见实体图预注册协议-v0.1-20260908.md)，预先写定 S0/S1/S2 分层、脚本单位、共同输入 union 日志、四窗口选择算法、主要结构统计量、1% 最小实际差异、时间块 bootstrap、三态停止规则和 test-once 纪律。`F_pub` 的科学语义、固定 revision、函数与参数已裁决；纯标准库本地实现已通过合成边界测试和固定种子 10,000 样本的上游函数差分核验。此前默认环境中的 pytest 测试体打印至 100% 后在结束阶段挂起；关闭第三方 pytest 自动插件后，as-of、CoinJoin 与脚本标识三组共 23 项测试以 exit 0 干净通过，说明挂起来自外部插件加载路径而非这些测试体。协议仍不是 `v1.0`：原始链来源及完整 schema/hash 未关闭，不能运行正式 Pilot。

纯标准库参考实现 `src/btcaml/data/asof_replay.py` 已锁定事件规范排序、按位置 cutoff、确定性并查集、只从历史支持取代表、future-only 中介语义以及 `p_merge`/`p_rewrite`；8 项定向测试通过。该实现只消费合成的已提取事件和端点，不含 raw adapter、CoinJoin 过滤、bootstrap 或真实数据，因此只关闭实现语义的局部歧义，不关闭数据 Gate，也不构成实验结果。

`src/btcaml/data/script_identity.py` 已冻结原始 scriptPubKey 字节的 SHA-256 标识，以及“首字节为 `OP_RETURN` 或长度大于 10,000”这一窄排除规则；空脚本和 `OP_FALSE OP_RETURN` 不被该操作性规则排除。`experiments/experiment_registry.csv` 已建立唯一 20 字段表头，但没有实验行。计划中的 `v1.0` 明确为 S0-only；S1 模型实验和 S2 历史部署评测均需 S0 Go 后另建协议版本，不能由本文件提前授权。

标签时间目前是最高风险阻断项。若无法形成 `L_{<=t}`，第一阶段 Go/No-Go 只能依据不使用标签的 partition/graph 指标；实体类型模型实验必须降级为回顾性敏感性分析，不能宣称历史部署可信度。

## 6. 下一步验收顺序

1. 补齐 Gate 1 的三项全文/工件核验并冻结去重后的聚焦来源表。
2. 同步当前已审入口收束：AWS 50 GiB 预检已关闭 block-metadata selected-set 映射与执行 revision，但仍只提供早期资源边界；必须继续关闭许可、项目控制的 transaction 字节冻结、全量交易／prevout／金额完整性与正式环境。正式入口须从经授权 BigQuery、用户提供的 Bitcoin Core/raw TXO snapshot，或完成同一硬门的 AWS 冻结前缀中选择一条，不能直接进入正式适配。
3. Gate 3A 的窗口、过滤器、脚本单位、1% 数值门、登记字段和 S0-only 范围已预先写定；原始链来源与完整性 blocker 关闭后才能升级为 v1.0。
4. 冻结前仅维护不访问真实数据的参考语义与合成契约测试；协议升级为 v1.0 后，再实现 union provenance logger、已选数据源适配器和正式运行检查。
5. 运行小窗口无模型数据 Gate，由 Research Director 根据预注册阈值作 Go/No-Go；只有 Go 才进入模型、校准、拒判和系统接入。

本快照是决策证据，不是实验协议，不授权全量处理、模型训练或外部发布。
