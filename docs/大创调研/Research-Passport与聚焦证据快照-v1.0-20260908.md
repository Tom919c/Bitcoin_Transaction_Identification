# Research Passport 与聚焦证据快照 v1.0

日期：2026-09-08

状态：Gate 0 条件未关闭；Gate 1 聚焦增量审计已完成第一轮，Yin 2019 已全文闭环，BitLINK 与 Zenodo 工件仍未闭环；Gate 3A 已形成 v0.1 待冻结草案

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
| 实验可追溯模式 | 历史 SSL manifest 提供版本、依赖和产物哈希范式 | 本分支未发现章程所述 `experiments/experiment_registry.csv`；正式运行前必须建立或恢复唯一登记入口 | 既有 SSL 产物与 `experiments/` |
| 当前工作树与本机原始链 | `data/README.md` 存在；已检查仓库与受控的 Windows 默认 Bitcoin Core 路径 | 仓库 `data/` 为空；未发现 `blk*.dat`、原始 TXO/manifest 或 Bitcoin Core datadir；当前进程也未设置数据连接变量 | 本地只读检查，2026-09-09 |

`BITCOIN_DB_URL` 是外部敏感配置。本记录不保存连接串；任何诊断不得打印凭据。

BigQuery `crypto_bitcoin` 仍是候选，但字段语义已得到更强的一手核验。[Google BigQuery 公共数据说明](https://docs.cloud.google.com/bigquery/public-data)、[GoogleCloudPlatform knowledge catalog](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/bundles/crypto_bitcoin/viz.html) 与 [Bitcoin ETL schema](https://github.com/blockchain-etl/bitcoin-etl/blob/master/README.md#schema) 一致确认：交易记录含区块哈希、高度、块内 index 与 coinbase 标志；input 含 `spent_transaction_hash` 和 `spent_output_index`；output 含金额与 locking `script_hex`。因此可用父交易键连接到 output 恢复 prevout script；input 自身的 `script_hex` 是 scriptSig，不能替代 locking script。尚未关闭的是实际表版本／快照、唯一主链与重组处理、缺失／重复率、许可适用、查询成本与导出 hash，故仍不能计为已满足数据硬门。现有 raw-block parser 也只是局部解析片段。

公开管线层面的证据进一步收紧了这一判断。[Blockchain ETL 公共数据登记](https://github.com/blockchain-etl/public-datasets/blob/master/README.md)报告 Bitcoin lag 为 3 块，[Bitcoin ETL](https://github.com/blockchain-etl/bitcoin-etl/blob/master/README.md#stream)把 lag 称为处理重组的最简单方法；这只能说明链头缓冲，不能证明公共表提供不可变 vintage 或完整重组对账。已新增一份从创世块开始、只计算数据完整性的资格查询和一份不含凭据的 manifest 模板；两者当前均未执行。局部高度 smoke 不足以资格化正式 `C_t`，因为共同输入 union 依赖完整历史前缀。

### 2.4 算力、环境与预算

- 依赖真源为 `pyproject.toml` 与 `uv.lock`；新研究运行使用仓库级 `uv` 环境。
- 当前隔离工作树未检测到可用的 `nvidia-smi`，不能宣称有 GPU。无模型数据 Gate 必须能在 CPU 和小窗口上完成。
- 本机 2026-09-09 只读容量快照：`C:` 可用约 131.5 GB，`D:` 可用约 145.9 GB；未发现 Bitcoin Core 数据目录。尚未核验可用内存和 PostgreSQL 实例容量，也不能据剩余空间推定任何全链方案可行。
- 不以工程工作量否决方向，但数据许可、可重放性、磁盘安全和可证伪性是硬门。
- 任何 BigQuery 或外部源试探都必须先取得项目与账单授权并预设扫描字节和费用上限；快照、schema、主链／重组语义与成本记录未齐备前，不发起付费或大规模查询、不冻结数据源、不运行正式 Pilot。
- BigQuery 资格查询必须先以完全相同的文件、参数做 dry-run，再把估算扫描字节、人工批准的 `maximum_bytes_billed`、查询时点、表元数据与查询哈希写入 manifest。局部窗口结果不允许支撑正式 Go/No-Go。

### 2.5 行政、伦理与许可

- 正式立项题名、任务书、项目编号、结题材料版本和成果承诺仍未进入当前分支的可核验输入，Gate 0 因此不能完全关闭。
- 公开链数据不等于可以对真实主体作风险指控。演示系统只能展示“实体类型识别结果”“不确定结果”和“待复核对象”。
- 现有标签含论坛、公开名单和外部来源，可能存在错误、时间漂移和选择偏差；没有发现/公开/采集时间时，不得用于严格历史部署训练。
- 新预印本称其 Zenodo 数据集采用 CC BY 4.0；当前尚未独立取得该记录的文件清单、大小和哈希，因此不把它写成已可用本地数据。
- 不向外部模型或服务上传数据库内容、私有标签、未发表手稿、连接信息或凭据。

## 3. Gate 1 聚焦 decision corpus snapshot

### 3.1 快照范围

检索日期：2026-09-08。

目标：寻找完整等价工作和反证，而不是扩大一般 Bitcoin AML 综述。纳入项必须至少触及下列一项：按时间更新的 Bitcoin 地址聚类、最终与历史分区差异、聚类误差真值、严格时间图评测、实体类型预测、概率校准或固定预算队列。

排除或降级：只在随机切分上刷分、只删除未来边但不改变实体分区、只做静态聚类准确率、只研究通用动态图、只有搜索摘要、无法确认预测单位或数据来源的工作。

### 3.2 两条独立检索链

链 A 为 Undermind 增量深检，工作区 `quan's workspace`，搜索路径 `/01 Discovery/As of Bitcoin Entity Identity Leakage Incremental`。目标查询完整限定了 `C_t/C_T`、固定地址支持、union 时间与 provenance、下游模型排序/校准/队列，以及 decisive No-Go。搜索返回 16 篇相关工作；摘要级综合未发现完整等价论文。随后对 `Mos21`、`Sch24c`、`Mul26`、`Sch24`、`Mag26`、`Mal26` 和 `Kha26` 做了全文定向问答。旧搜索 `/01 Discovery/Temporal Entity Resolution Error Propagation` 与 `/01 Discovery/Provenance Preserving Bitcoin Benchmark Reconstruction` 仅作为历史独立发现池，不重复计数。

链 B 由主负责人和一名不继承结论的反方审查者独立执行，查询包括：

- `"temporal address clustering" Bitcoin entity resolution`
- `"dynamic address clustering" Bitcoin`
- `Bitcoin address clustering "as of" time`
- `Bitcoin address clustering "look-ahead" bias`
- `"future transactions" "address clustering" Bitcoin`
- `Bitcoin entity type prediction address clusters supervised learning`
- `temporal graph leakage future information evaluation`
- `Bitcoin entity classification address clustering temporal evaluation`

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
| Zhong & Mueen, *BitLINK*, KDD 2024, DOI `10.1145/3637528.3672037` | 官方作者 CV 与主页、UNM 学位论文记录核验；正文未取得 | 作者主页只确认其用 temporal patterns 链接 Bitcoin 地址 cluster；学位论文记录确认 BitLINK 属于 blockchain address identification | 动态实体解析近邻；是否执行 `C_t/C_T`、固定历史支持、lineage、实体类型／校准／预算队列评测均为 Unknown |
| Yin, Mukkamala & Vatrapu, *Regulating Cryptocurrencies...*, JMIS 2019, DOI `10.1080/07421222.2018.1550550` | 出版社元数据与作者公开全文核验 | 以 Chainalysis 提供的 957 个已分类地址簇作多类预测；数据截至区块 512,033，采用 75/25 随机式切分与训练内三折交叉验证；聚类含共同花费、外部情报和人工合并，未提供 lineage 或标签可得时间 | 否决“首次做 Bitcoin 实体簇类型预测”；不能断言其使用截止块后的未来分区，但其不透明终态聚类与随机切分是本项目必须控制的近邻风险 |
| Schnoering et al., *Refining Heuristic-Based Bitcoin Address Clustering with GNNs*, arXiv `2609.01942` | 官方 arXiv HTML 全文核验；预印本 | 以启发式 cluster 为训练标签，用对比式 GNN 表征和层次聚类检测可疑合并；训练/验证/测试来自不重叠区块区间；发布的地址图字段是聚合节点、边和 cluster 映射 | 对“聚类置信度/细化 GNN”构成直接方法碰撞；其非重叠交易切分不等于 cutoff-specific identity；正文所称代码仓库当前为空，复现性仍需核验 |
| `BTCGraphConstruction` 官方代码 | 官方 GitHub 源码核验 | `populate_alias.py` 按区块收集合并并更新 `UnionFind`，最终只落 `node_id -> alias`；没有 union-event logger | 为小窗口重放提供最接近上游实现，但不能直接把其最终 alias 当作历史分区 |

补充反证中，正式文献已经覆盖未来交易揭示过去 change、动态聚类、按日期截断数据和时间图严格评测等组成部分。当前结论只能写成“截至本快照未检出完整等价工作”，不能写成“全球首次”。

### 3.4 新预印本的数据工件审计

arXiv `2609.01942` 报告三个训练图、一个验证图和一个测试图来自不重叠区块区间，并声明 Zenodo DOI `10.5281/zenodo.22239038`、CC BY 4.0。附录公开字段包括节点、地址级聚合边和 cluster 映射；正文没有给出逐 union 事件日志。

官方 `hugoschnoering2/btc-graph-hc` 仓库在 2026-09-08 的 GitHub 元数据显示大小为 0，虽有默认分支名，但当前没有可读取实现。`BTCGraphConstruction` 仓库可读，README 为空，源码保留原始块解析和最终 alias 构建。

2026-09-09 的 DataCite 官方 DOI 注册记录已确认 Zenodo `10.5281/zenodo.22239038` 的标题为 *Bitcoin transaction graphs: training, labelled entities, and CoinJoins*，版本 `1.0`，issued date 为 2026-09-01，creators 为 Hugo Pierre Philippe Schnoering 与 Michalis Vazirgiannis，许可为 CC BY 4.0，并以 `IsVersionOf` 指向概念 DOI `10.5281/zenodo.22239037`。注册元数据的 deposited description 列出 `1_training_dataset.zip`、`2_labels_eval_dataset.zip` 和 `3_coinjoin_eval_dataset.zip`，并声称标注／CoinJoin 图目录含 `node_features.parquet`、`edge_features.parquet`、`clustering.parquet` 与 `metadata.json`。

这关闭了书目、版本和许可核验，不等于核验实际文件。Zenodo record/API 本轮仍返回超时，DataCite 的 `sizes`、`formats` 为空且 `contentUrl` 为 `null`；因此文件 manifest、逐文件大小与 checksum、实际 schema、raw transaction/outpoint/script、主链／重组信息和 union lineage 仍为 Unknown。该 release 继续 No-Go 为当前 `C_t/C_T` 重放输入；若 Zenodo 恢复可访问，须先保存 record JSON、文件 manifest 与 checksum，再判断是否具备 union event 或足够原始链数据。

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

1. 核验 BitLINK 全文是否包含可重放 cluster lineage；2026-09-09 的独立核验已尝试 ACM landing/PDF、作者主页与 slides、UNM 学位论文记录与下载入口，但 ACM 返回 403、slides 无法由当前文本链读取、学位论文下载遇到 Cloudflare challenge，未取得可逐页核验正文。最近邻 checklist 第 1–5 项保持 Unknown，第 6 项只确认同行评审出版身份；禁止写“BitLINK 未做 `C_t/C_T`”或“本项目首次研究 temporal cluster linkage”；
2. Zenodo `22239038` 的 DataCite 注册元数据、版本和许可已核验；仍需取得 Zenodo record JSON、文件 manifest、checksum 与实际 schema。当前明确 No-Go 为 PIT 重建数据源；
3. 对 2026 新预印本的代码空仓状态和后续版本做一次冻结快照；
4. 继续将其余纳入来源按 DOI/标题去重并补稳定 BibTeX 与页码定位；Yin 2019、BitLINK、2026 GNN 聚类预印本、Glassnode PIT 与 Möser–Narayanan FC 2022 已作为相互独立版本写入 `references.bib`。

Yin et al. 2019 的剩余全文项已经关闭：其预测单位是专有地址簇，交易截止为区块 512,033（2018-03-04 23:58:21 UTC），采用 75/25 随机式切分和训练内三折交叉验证；全文没有 cluster lineage、label availability cutoff 或 `C_t/C_T` 对照。它是实体类型预测的 Critical 近邻，但不是已经核验的完整等价评测。

BitLINK 的当前证据边界不是“完整等价已排除”，而是“风险仍未关闭”。作者级来源足以证明它与 temporal cluster linkage 高度相邻，却不足以证明或否定本协议的固定历史窗口、固定支持和下游决策传播设计；无法访问正文不能当作论文没有报告这些内容。

### Gate 2：方向保持，创新叙事已修订

用户对“严格按时可见实体图与可信识别系统”的方向确认继续有效；确认不等于批准宽泛的首创表述。核心创新从“发现未来聚类泄漏”改为“可审计、受控、可复现地测量其对实体类型预测与决策的影响”。

### Gate 3A：v0.1 待冻结

已形成[严格按时可见实体图预注册协议 v0.1](Gate3A-严格按时可见实体图预注册协议-v0.1-20260908.md)，预先写定 S0/S1/S2 分层、脚本单位、共同输入 union 日志、四窗口选择算法、主要结构统计量、1% 最小实际差异、时间块 bootstrap、三态停止规则和 test-once 纪律。`F_pub` 的科学语义、固定 revision、函数与参数已裁决；纯标准库本地实现已通过合成边界测试和固定种子 10,000 样本的上游函数差分核验。此前默认环境中的 pytest 测试体打印至 100% 后在结束阶段挂起；关闭第三方 pytest 自动插件后，as-of、CoinJoin 与脚本标识三组共 23 项测试以 exit 0 干净通过，说明挂起来自外部插件加载路径而非这些测试体。协议仍不是 `v1.0`：原始链来源及完整 schema/hash 未关闭，不能运行正式 Pilot。

纯标准库参考实现 `src/btcaml/data/asof_replay.py` 已锁定事件规范排序、按位置 cutoff、确定性并查集、只从历史支持取代表、future-only 中介语义以及 `p_merge`/`p_rewrite`；8 项定向测试通过。该实现只消费合成的已提取事件和端点，不含 raw adapter、CoinJoin 过滤、bootstrap 或真实数据，因此只关闭实现语义的局部歧义，不关闭数据 Gate，也不构成实验结果。

`src/btcaml/data/script_identity.py` 已冻结原始 scriptPubKey 字节的 SHA-256 标识，以及“首字节为 `OP_RETURN` 或长度大于 10,000”这一窄排除规则；空脚本和 `OP_FALSE OP_RETURN` 不被该操作性规则排除。`experiments/experiment_registry.csv` 已建立唯一 20 字段表头，但没有实验行。计划中的 `v1.0` 明确为 S0-only；S1 模型实验和 S2 历史部署评测均需 S0 Go 后另建协议版本，不能由本文件提前授权。

标签时间目前是最高风险阻断项。若无法形成 `L_{<=t}`，第一阶段 Go/No-Go 只能依据不使用标签的 partition/graph 指标；实体类型模型实验必须降级为回顾性敏感性分析，不能宣称历史部署可信度。

## 6. 下一步验收顺序

1. 补齐 Gate 1 的三项全文/工件核验并冻结去重后的聚焦来源表。
2. 取得原始链入口授权：若采用 BigQuery，先 dry-run 已冻结资格查询并由人工确认扫描上限，再核验 tip、主链、父 outpoint、脚本与冻结导出哈希；若改用 Bitcoin Core/TXO 快照，则提供其版本、许可、tip、manifest、哈希与容量。两条路线只选一条进入正式适配。
3. Gate 3A 的窗口、过滤器、脚本单位、1% 数值门、登记字段和 S0-only 范围已预先写定；原始链来源与完整性 blocker 关闭后才能升级为 v1.0。
4. 冻结前仅维护不访问真实数据的参考语义与合成契约测试；协议升级为 v1.0 后，再实现 union provenance logger、已选数据源适配器和正式运行检查。
5. 运行小窗口无模型数据 Gate，由 Research Director 根据预注册阈值作 Go/No-Go；只有 Go 才进入模型、校准、拒判和系统接入。

本快照是决策证据，不是实验协议，不授权全量处理、模型训练或外部发布。
