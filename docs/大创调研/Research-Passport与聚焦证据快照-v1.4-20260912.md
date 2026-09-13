# Research Passport 与聚焦证据快照 v1.4

日期：2026-09-12；增量核验至 2026-09-13

状态：Gate 0 的 S0 研究执行输入已关闭，正式任务书等行政输入和 S1 标签输入仍未关闭；Gate 1 的 BitLINK 聚焦全文核验已闭环；AWS 早期完整前缀已通过交易语义全量资格审计，可用于私有内部 S0，但公开再分发仍未获授权；Gate 3A v1.3 已冻结为 S0-only。union provenance 提取正在从已验证 checkpoint 恢复，尚未计算效应、分区／图哈希或 S0 决策；任何模型、标签投影、S1/S2 或正式测试集读取均未获授权。

研究分支：`asof-entity-graph-pilot`

本分支起点：`bc5703a650587643fca7140fc579310c6f09349e`

启动提交：`734fd098fb53c6d07a0e584381ab7b1bed155097`

## 0. 2026-09-11 增量裁决

本节取代本文件后文所有截至 2026-09-08 至 2026-09-10 的暂态描述；旧段落保留为审计轨迹，不再代表当前 Gate 状态。

- BitLINK 所在 UNM 学位论文官方 PDF 已取得并完成全文定位，文件为 `data/raw/literature/zhong-2024-online-temporal-data-mining-unm.pdf`，43,681,509 字节，SHA-256 为 `4d32451db62f0d04101db59a561ed499223410436ba03030c269e6c58258aa50`。Chapter 5 明确覆盖流式地址簇链接、address flushing 与 cluster-chain continuation，故“首次 temporal cluster linkage／cluster chain”以及通用 successor-cluster 预测均为 No-Go。全文未给出本项目预注册的固定历史支持 `V_j` 上只替换 `C_t`/`C_T`、成对测量实体图重写并向下游决策传播的完整等价设计；窄的 as-of 分区版本审计仍可证伪。详见[BitLINK 全文核验与主线边界](BitLINK全文核验与主线边界-20260911.md)。
- AWS 冻结早期前缀覆盖高度 `0–290291`。全量交易语义审计处理 290,292 个区块、34,731,184 笔交易、78,085,978 个输入和 87,704,214 个输出；独立只读 SQLite `PRAGMA quick_check` 为 `ok`，金额残差最大绝对值为 0.0078125 聪，且精确识别两次历史 BIP30 coinbase txid 覆盖，没有其他失败。交易语义状态哈希为 `6cafc290b8e3b951417c85c5b6dd431e71c3d0c548ac45bdc6a7bdee4a34d924`。这只关闭选定早期前缀的来源资格，不证明当前时期外推性。
- S0 数据源已由 `configs/data/aws_btc_s0_source_manifest_v1_1.json` 冻结；该 manifest 的 SHA-256 为 `e32ad2f33ecbc184eb04159f0adbb22dd2a4a1a47f1e280cbbca699432d67f3d`。用途限定为私有内部分析，公开再分发为 false。固定 cutoff 为 `[181440, 199584, 215712, 225792]`，`W=2016`，主 `H=52560`，敏感性 `H=[13140, 105120]`。
- v1.1 是正式 S0 前的列投影修正：v1.0 allow-list 漏列协议已经要求的 `inputs.index`，而顶层 `inputs/outputs` struct 投影会额外载入未列出的 scriptSig 等字段。修正版只新增 `inputs.index` 并要求显式读取必要 Parquet 叶字段；没有改变数据字节、窗口、horizon、过滤器、统计量、阈值或授权范围，也没有读取标签、效应或模型结果。
- union provenance logger 已提交并通过 38 项定向／相邻回归测试、uv 自检、真实 Parquet 最小叶字段抽样和独立只读审计。正式提取在高度 12000 主动暂停时 `quick_check=ok`，12,001 个区块各有三个 profile 统计，随后从同一 SQLite 状态恢复；该运行不计算 `p_merge`、`p_rewrite`、bootstrap 或 Go/No-Go。
- Gate 3A v1.2 在任何效应计算前补冻主 seed `20260911`、顺序无关的 SHA-256 cell 子种子和 nearest-rank percentile CI 索引。它不改变数据、窗口、horizon、过滤器、统计量、1% 阈值或三态规则。Gate 3A 仍只授权 S0；在 S0 Go 和独立 S1 协议冻结前，不训练模型。
- Gate 3A v1.3 在任何效应或图输出前关闭两个独立反方 P0：把 B/C 唯一操作化为无金额归因的交易级有向端点多重图并固定 JSONL 哈希；把 provenance audit 唯一化为八个主 cell、支持相关候选总体、全局 event ID 去重和两阶段配额。当前 extractor 已保留所需端点、交易总量、事件位置、过滤决策与 source 定位，不因本修订重启。

## 1. 当前裁决

项目方向保持为“严格按时可见实体图与可信识别”，但创新主张必须收紧：

> 在固定原始链前缀、固定历史截止点和可审计标签口径下，受控量化 final-vintage 地址聚类相对 point-in-time/as-of 地址聚类对预测单位、实体图、实体类型模型比较、概率决策和有限人工审查队列的影响。

本项目不再把“未来聚类知识会回写历史并产生 look-ahead bias”作为新发现。Glassnode 已在 2023 年的一手研究说明中明确描述该现象并给出 point-in-time 数据作为补救。当前未检出的是完整的学术端到端实验：固定历史信息集，只改变地址分区版本，再把差异传播到实体类型预测、校准、选择性预测和固定预算队列。

2026 年 9 月 1 日公开的预印本 *Refining Heuristic-Based Bitcoin Address Clustering with Graph Neural Networks* 已直接覆盖“用 GNN 表征细化启发式聚类、发现可疑错误合并、给出候选拆分”这一方法空间。因此，启动章程中的条件 D 只能作为最近邻基线或敏感性条件，不能预设为本项目的新方法贡献。

当前决策是：保留方向，停止宽泛的新颖性表述；Gate 3A v1.3 已冻结，进入无模型、可重放的 S0 数据机制审计。不训练新模型，不打开正式测试结果，不重建 2.52 亿节点全图。

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
| 实验可追溯模式 | 历史 SSL manifest 提供版本、依赖和产物哈希范式 | `experiments/experiment_registry.csv` 已用于登记 AWS 资格审计和 S0 提取；提取运行已先登记 planned，真实暂停后更新为 running | 既有 SSL 产物与 `experiments/` |
| AWS 冻结早期前缀 | 已保存项目控制的 transaction/block 字节、对象清单、schema、主链 preflight 和交易语义状态；覆盖高度 `0–290291` | 只授权私有内部 S0；公开再分发未授权；末端为 2014-03-12，不能代表当前时期 | `configs/data/aws_btc_s0_source_manifest_v1_1.json` 与绑定产物 |

`BITCOIN_DB_URL` 是外部敏感配置。本记录不保存连接串；任何诊断不得打印凭据。

BigQuery `crypto_bitcoin` 仍是候选，但字段语义已得到更强的一手核验。[Google BigQuery 公共数据说明](https://docs.cloud.google.com/bigquery/public-data)、[GoogleCloudPlatform knowledge catalog](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/bundles/crypto_bitcoin/viz.html) 与 [Bitcoin ETL schema](https://github.com/blockchain-etl/bitcoin-etl/blob/master/README.md#schema) 一致确认：交易记录含区块哈希、高度、块内 index 与 coinbase 标志；input 含 `spent_transaction_hash` 和 `spent_output_index`；output 含金额与 locking `script_hex`。因此可用父交易键连接到 output 恢复 prevout script；input 自身的 `script_hex` 是 scriptSig，不能替代 locking script。尚未关闭的是实际表版本／快照、唯一主链与重组处理、缺失／重复率、许可适用、查询成本与导出 hash，故仍不能计为已满足数据硬门。现有 raw-block parser 也只是局部解析片段。

公开管线层面的证据进一步收紧了这一判断。[Blockchain ETL 公共数据登记](https://github.com/blockchain-etl/public-datasets/blob/master/README.md)报告 Bitcoin lag 为 3 块，[Bitcoin ETL](https://github.com/blockchain-etl/bitcoin-etl/blob/master/README.md#stream)把 lag 称为处理重组的最简单方法；这只能说明链头缓冲，不能证明公共表提供不可变 vintage 或完整重组对账。已新增一份从创世块开始、只计算数据完整性的资格查询和一份不含凭据的 manifest 模板；两者当前均未执行。局部高度 smoke 不足以资格化正式 `C_t`，因为共同输入 union 依赖完整历史前缀。

2026-09-09 官方入口审计审阅了 Bitcoin ETL README、public-datasets README、[Bitcoin ETL streaming 文档](https://github.com/blockchain-etl/blockchain-etl-streaming)和公开架构说明。在已审官方文档中，未发现无需部署者凭证即可访问、带版本标识的历史 GCS 快照；streaming 部署关于 GCS 的说明要求使用者创建并配置自己的 GCS bucket，以保存 `last_synced_block.txt` 状态，未给出公开历史数据对象、manifest 或回放保证。已审文档把 Pub/Sub 描述为持续流式出口，并报告 Bitcoin lag 为 3 块，但未承诺公共 topic 可从创世块回放到冻结高度的完整、版本化前缀；当前没有独立冻结导出／快照和完整性审计，不能把它资格化为 S0 输入。在当前已审官方入口范围和本地资产条件下，待资格化候选暂收束为：(1) BigQuery 经授权 dry-run、资格查询、冻结导出；(2) 用户提供的 Bitcoin Core datadir 或 raw TXO snapshot，经版本、tip、hash、容量审计。该收束不表示已经穷尽其他可能满足硬门的原始链来源。

2026-09-10 至 2026-09-11 的增量审计选定了 AWS 早期完整前缀。AWS Open Data Registry 允许无账户匿名访问 `s3://aws-public-blockchain/v1.0/btc/`；固定对象清单与本地字节冻结覆盖 1,890 个 transaction 对象（53,659,133,189 字节）和 1,897 个 block 对象（90,449,066 字节）。全量审计从创世块顺序恢复主链、块内交易、prevout locking script 和整数聪语义，并对历史 BIP30 覆盖采用精确高度、区块哈希、txid、旧高度、旧输出值和旧脚本白名单；v0.1 的拒绝失败被保留，v0.2 修复后完整通过。选定来源的身份、schema、主链和交易语义现由 `configs/data/aws_btc_s0_source_manifest_v1_1.json` 及其哈希绑定，故私有内部 S0 的数据硬门关闭。公开桶未启用 S3 Versioning，原始对象 `VersionId=null`，Registry/条款也不由代理解释为公开再分发授权；本项目依靠已冻结的本地字节与校验清单保证本次内部重放，原始数据不得公开发布。该前缀终止于 2014-03-12，结论不得外推到当前时期。

### 2.4 算力、环境与预算

- 治理目标要求以 `pyproject.toml` 与 `uv.lock` 作为依赖真源并使用仓库级 `uv` 环境；`uv.lock` 已由提交 `9b92a52` 纳入版本控制，正式 S0 提取通过 `uv run` 执行。更早的 AWS 样本资格审计使用本机 Python 3.12.3 与 PyArrow 16.1.0，其结论仅用于来源资格；正式结果仍须绑定当前 lock、代码 revision 与运行环境清单。
- 当前隔离工作树未检测到可用的 `nvidia-smi`，不能宣称有 GPU。无模型数据 Gate 必须能在 CPU 和小窗口上完成。
- 2026-09-10 新增 [Kaggle 私有算力接入审计](Kaggle私有算力接入审计-20260910.md)。账号 `camellia99` 的 OAuth、额度查询、私有 T4 脚本提交、状态轮询和产物回收闭环已通过；版本 1 在 Python 3.12.13、PyTorch 2.10.0+cu128、CUDA 12.8 上实际完成一次 CUDA 张量运算，并看到两张 Tesla T4。该结果只把 Kaggle 提升为可选远端执行资源，不是数据源、正式实验环境或 Gate 证据；正式运行仍须冻结输入 manifest、环境、预算、checkpoint 和输出追溯，并遵守单次运行、持久空间和每周额度限制。
- 本机 2026-09-10 只读资源快照：`C:` 可用 125,963,497,472 字节，`D:` 可用 139,442,827,264 字节，物理内存 29,734,326,272 字节；未发现 Bitcoin Core 数据目录。当前 S0 不依赖 Bitcoin Core datadir 或 PostgreSQL；这份历史空间快照也不能推定任何全链方案可行。
- 不以工程工作量否决方向，但数据许可、可重放性、磁盘安全和可证伪性是硬门。
- 任何 BigQuery 或外部源试探都必须先取得项目与账单授权并预设扫描字节和费用上限；快照、schema、主链／重组语义与成本记录未齐备前，不发起付费或大规模查询、不冻结数据源、不运行正式 Pilot。
- BigQuery 资格查询必须先以完全相同的文件、参数做 dry-run，再把估算扫描字节、人工批准的 `maximum_bytes_billed`、查询时点、表元数据与查询哈希写入 manifest。局部窗口结果不允许支撑正式 Go/No-Go。

### 2.5 行政、伦理与许可

- 正式立项题名、任务书、项目编号、结题材料版本和成果承诺仍未进入当前分支的可核验输入，Gate 0 因此不能完全关闭。
- 公开链数据不等于可以对真实主体作风险指控。演示系统只能展示“实体类型识别结果”“不确定结果”和“待复核对象”。
- 现有标签含论坛、公开名单和外部来源，可能存在错误、时间漂移和选择偏差；没有发现/公开/采集时间时，不得用于严格历史部署训练。
- Zenodo 官方 record 已确认 CC BY 4.0、三个外层 ZIP 的文件名、大小和仓库声明 MD5；仅最小训练 ZIP 已下载并本地复算 MD5/SHA-256，其余两包未下载、内部成员清单与 checksum 未取得，因此不把整个 release 写成已可用本地数据。
- 不向外部模型或服务上传数据库内容、私有标签、未发表手稿、连接信息或凭据。

许可和伦理准入按来源分别处理，不以“公开可访问”替代许可判断：

| 来源／产物 | 当前允许用途 | 当前禁止或待审项 |
|---|---|---|
| AWS 早期 Bitcoin 前缀 | 冻结字节上的私有内部 S0 结构审计 | 原始对象公开再分发、上传 Kaggle、对主体作身份或风险指控 |
| Zenodo `22239038` | 按已核验 CC BY 4.0 做元数据与本地结构审计 | 不把该许可外推到本地数据库、外部标签源或未下载成员 |
| BitcoinTalk／交易所官网／外部名单标签 | 仅作公开来源与字段准备度核验 | 在逐记录许可、时间、置信度和投影 lineage 关闭前用于严格历史 S1/S2 或上传外部算力 |
| S0 汇总、哈希与审计日志 | 项目内可追溯决策 | 未经人工批准公开发布；不得包含地址标签、凭据或可识别主体指控 |

标签准入的字段级结论另见 [S1 标签可得时间准备度审计](S1标签可得时间准备度审计-20260913.md)。该审计把 BitcoinTalk 子集收紧为“上游可能重建”，没有解除 S1/S2 阻断。

### 2.6 目标会议候选与当前政策快照

核验日期为 2026-09-13；这里只冻结候选和当前官方状态，不授权投稿或提前套用模板。

| 候选 | 当前定位 | 官方状态与硬边界 |
|---|---|---|
| KDD 2027 Research Track，February cycle | 主候选；适配数据挖掘、聚类、图审计与可信评测 | [官方 Research CFP](https://kdd2027.kdd.org/research-track-call-for-papers/) 只公布第一周期日期；[官方 FAQ](https://kdd2027.kdd.org/frequently-asked-questions/) 明确 February cycle 接收 original submission，但精确截止仍为待确认。当前不得杜撰日期。主文 8 页、双盲等规则仅作为当前快照，正式提交前重核。 |
| KDD 2027 Datasets & Benchmarks Track | 条件候选，仅当形成可公开访问、文档完备的 benchmark/artifact | [官方 CFP](https://kdd2027.kdd.org/datasets-and-benchmarks-track-call-for-papers/) 把 accessibility、documentation、impact、ethics 列为核心标准；当前 AWS 原始对象不获再分发授权，故尚不满足 artifact 路线。 |
| The Web Conference 2027 Research Track | 范围条件候选，不是默认目标 | [官方 CFP](https://www2027.thewebconf.org/research-track-papers/) 的 full-paper 截止为 2026-10-25 AoE，并要求首页明确回答 Web-specific scientific challenge；仅使用区块链或 Web3 数据不够。当前在未形成可辩护 Web 相关性前为 No-Go。 |
| CIKM 2027 | 后备候选 | [CIKM 官方总入口](https://www.cikmconference.org/) 只确认 2027 在 Sydney 举办；本轮未定位 2027 CFP、track 或截止，不沿用 2026 规则。 |

投稿路由由证据决定：若最终贡献以可控测量、方法和可信评测为主，优先 KDD Research；若不能公开足够 artifact，不投 KDD Datasets & Benchmarks；若没有 Web 特有问题，不投 The Web Conference。任何作者、投稿、公开 artifact 或费用承诺仍需人工批准。

### 2.7 当前工程预算与停止线

| 阶段 | 冻结预算 | 停止／升级条件 |
|---|---|---|
| S0 本地提取 | 只使用已冻结 AWS 本地字节；单一正式提取状态；空闲磁盘低于 20 GiB 时主动停止；不发起付费查询 | 完成后先做来源抽样与 SQLite／哈希绑定，再运行评估；不得为提速重启或改变 checkpoint 语义 |
| S0 来源与效应审计 | 一次冻结 provenance audit、一次主 evaluation、一次确定性复跑比对；无超参数搜索、无标签、无模型 | 任一完整性硬门失败即停止并保留失败；结果分歧先审计实现，不追加试验“投票” |
| BigQuery／其他付费云 | 当前货币预算为 0，`maximum_bytes_billed=0`；只保留未执行备选 | 只有人工批准项目、账单和非零上限后才能新建版本化预算 |
| S1 Pilot 的 Kaggle 预留 | 仅在 S0 Go 和独立 S1 协议冻结后启用；private、Internet 默认关闭；单次不超过 6 小时、阶段累计不超过 12 小时；默认同时使用两张 T4，将独立 seed／配置分派到不同 GPU | 先做双卡可见性和吞吐 smoke；双卡无端到端收益则记录负结果并退回单卡，不用额外运行掩盖；单次平台上限仍为 12 小时 |
| Gate 4 | 尚未授权、预算未冻结 | 只有 S1 Pilot 达到预注册阈值后另行冻结多种子、存储和 GPU 预算 |

Kaggle 最后一次核验的账户快照是 30 GPU 小时／周、单次最多 12 小时、`/kaggle/working` 自动保存空间 20 GB；额度和机型会变化，正式提交前必须重新查询。远端输入另设白名单、总大小和 SHA-256 检查，不因预算尚有余额而上传未审计数据。

### 2.8 Skill、MCP、插件与工具选择记录

2026-09-13 执行 `scripts/update_skill_inventory.py --check` 后确认清单过期，已用同一生成器刷新并复核为 current；刷新后记录 559 个物理 manifest、325 个唯一 Skill 名称。运行时 Available Skills 仍是可调用性的唯一权威。

| 能力 | 本 Gate 的选择与用途 | 边界／未选理由 |
|---|---|---|
| 研究规划与协议 | `research-planning`、`experiment-design`／`experimental-design` | 只用于冻结 estimand、停止线和统计单位；协议后见结果不得静默改写 |
| 实验实现与审计 | `experiment-code`、`ponytail:ponytail`、本地 Git/pytest/uv | 最小实现与可失败检查；不为未晋级阶段搭框架 |
| 文献与引用 | Undermind 深检／全文问答；独立官方 Web、论文、仓库链；`literature-search`、`citation-management` | 两条链分别记账、按 DOI／标题去重；搜索摘要和模型回答不作最终证据 |
| 会议政策 | `venue-templates` + 官方 CFP／FAQ | 不把 Skill 内缓存或旧年度规则当当前官方政策 |
| 浏览器与下载 | `computer-use` 仅处理用户指定、已登录页面；Kaggle CLI／OAuth 仅处理私有算力通道 | 不操作其他浏览器内容；凭据不入仓库；UNM 论文由用户下载后本地验签 |
| 远端算力 | Kaggle 私有 Notebook，已完成双 T4 smoke | 当前只作后续算力；S0 不迁移；未经审计的数据和标签不上传 |
| 外部模型协作 | 只允许固定、已提交、非敏感的代码／公开证据做机械复核 | 不上传未发表正文、`data/`、数据库、私有标签或凭据；最终科学裁决由 Research Director 完成 |
| 新插件／依赖 | 本 Gate 未安装 | 已有仓库、标准库、Skill、Web 与 Kaggle 能覆盖当前需要，新增依赖没有必要 |

## 3. Gate 1 聚焦 decision corpus snapshot

### 3.1 快照范围

检索日期：2026-09-08；增量核验至 2026-09-11。

目标：寻找完整等价工作和反证，而不是扩大一般 Bitcoin AML 综述。纳入项必须至少触及下列一项：按时间更新的 Bitcoin 地址聚类、最终与历史分区差异、聚类误差真值、严格时间图评测、实体类型预测、概率校准或固定预算队列。

排除或降级：只在随机切分上刷分、只删除未来边但不改变实体分区、只做静态聚类准确率、只研究通用动态图、只有搜索摘要、无法确认预测单位或数据来源的工作。

### 3.2 两条独立检索链

链 A 为 Undermind 增量深检，工作区 `quan's workspace`，搜索路径 `/01 Discovery/As of Bitcoin Entity Identity Leakage Incremental`。目标查询完整限定了 `C_t/C_T`、固定地址支持、union 时间与 provenance、下游模型排序/校准/队列，以及 decisive No-Go。搜索返回 16 篇相关工作；摘要级综合未发现完整等价论文。随后对 `Mos21`、`Sch24c`、`Mul26`、`Sch24`、`Mag26`、`Mal26` 和 `Kha26` 做了全文定向问答；DOI lookup 另定位 `Zho24`，当时书目/摘要匹配但 PDF 状态为 X。2026-09-11 经已登录浏览器取得 UNM 官方学位论文 PDF，主代理完成 Chapter 5 全文定位并另存证据边界；因此 `Zho24` 的全文状态现已关闭。旧搜索 `/01 Discovery/Temporal Entity Resolution Error Propagation` 与 `/01 Discovery/Provenance Preserving Bitcoin Benchmark Reconstruction` 仅作为历史独立发现池，不重复计数。

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
| Zhong & Mueen, *BitLINK*, KDD 2024, DOI `10.1145/3637528.3672037` | UNM 官方学位论文 PDF 与 Chapter 5 全文定位，source-verified 与 interpretation-verified；另有作者 CV、主页和 22 页幻灯片交叉核验 | 正文明确定义 address flushing、cluster relationship prediction、streaming cluster linking 与 cluster-chain continuation；其实验对象和目标不是固定历史支持上只替换 `C_t/C_T` 的成对分区／图重写审计 | 直接否决通用 temporal linkage／cluster-chain 首创；未触发本协议六项完整等价 No-Go，但窄差异仍须由 S0 实证证明 |
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

### Gate 0：S0 研究执行输入已关闭；行政与 S1 输入未关闭

仓库资产、上游公开代码、运行环境、主要风险、目标会议候选、工程预算和工具选择已经盘点。S0 已选 AWS 冻结早期前缀，来源 manifest、对象清单、数据版本、最高资格高度、主链／交易语义状态和哈希均已绑定；本地提取使用受版本控制的 `uv.lock`，20 GiB 磁盘保留线是运行硬门。BigQuery 降为零预算备选，不再是 S0 的待选入口；PostgreSQL 容量不影响当前 S0。

仍缺失或只能保持 `partial` 的输入是：正式任务书／立项题名／项目编号等行政材料；逐标签来源、版本、许可、首次发现／公开／采集时间和地址到历史实体的投影 lineage；AWS 原始对象公开再分发授权；S1/Gate 4 的最终输入体积、峰值 RAM、远端存储与完整 GPU 预算。因此，Gate 0 不阻断已经预注册的私有内部 S0，但不授权标签、模型、历史部署主张、公开 artifact 或投稿。

### Gate 1：聚焦 BitLINK 风险已关闭；全域语料仍增量维护

双链检索、关键全文核验和独立反方审查已经完成。当前边界为：

1. BitLINK 所在 UNM 学位论文官方 PDF 已于 2026-09-11 取得并完整定位。Chapter 5 关闭了通用 temporal cluster linkage、address flushing、桥接簇和 cluster-chain continuation 的组件级新颖性；正文没有形成最近邻 checklist 的完整六项等价设计。禁止写“首次研究 temporal cluster linkage／cluster chain”，也不得把正文未使用本协议记号写成创新证据；只保留固定支持上的 as-of 分区版本与图重写配对审计。
2. Zenodo `22239038` 的 DataCite 与 record API 元数据、版本、许可、三个外层文件名、大小和 Zenodo MD5 声明已核验；最小训练包已经本地校验并完成中央目录／CSV header 审计，确认缺少本协议必需的 raw transaction/outpoint/script 与 union provenance 字段，作为 PIT 重建数据源 No-Go。node/edge/alias 列的精确语义及其余大包内部 schema 保持 Unknown，不因列名或文件名推断；
3. 2026 新预印本的官方代码仓已在 2026-09-09 冻结为空仓快照；后续只有新 decision snapshot 才能改变该状态；
4. 继续将其余纳入来源按 DOI/标题去重并补稳定 BibTeX 与页码定位；Yin 2019、BitLINK、Zhong 2024 学位论文、2026 GNN 聚类预印本、Glassnode PIT 与 Möser–Narayanan FC 2022 已作为相互独立版本写入 `references.bib`。学位论文现为全文 source-verified 与 interpretation-verified，具体边界记录于独立核验文档。

Yin et al. 2019 的剩余全文项已经关闭：其预测单位是专有地址簇，交易截止为区块 512,033（2018-03-04 23:58:21 UTC），采用 75/25 随机式切分和训练内三折交叉验证；全文没有 cluster lineage、label availability cutoff 或 `C_t/C_T` 对照。它是实体类型预测的 Critical 近邻，但不是已经核验的完整等价评测。

BitLINK 的当前证据边界是“组件碰撞已确认、完整等价未成立”。论文正文足以否决通用 cluster linkage、streaming continuation 与 cluster chain 的首创主张；当前未见其在固定历史交易窗口和固定支持上只替换 `C_t/C_T`，并成对量化分区与实体图重写或向实体类型决策传播。该差异是本项目待 S0 证伪的窄对象，不是已经证明的新颖贡献。

### Gate 2：方向保持，创新叙事已修订

用户对“严格按时可见实体图与可信识别系统”的方向确认继续有效；确认不等于批准宽泛的首创表述。核心创新从“发现未来聚类泄漏”改为“可审计、受控、可复现地测量其对实体类型预测与决策的影响”。

### Gate 3A：v1.3 已冻结，S0 提取正在运行

已形成[严格按时可见实体图预注册协议 v1.3](Gate3A-严格按时可见实体图预注册协议-v1.3-20260912.md)，预先写定 S0/S1/S2 分层、脚本单位、共同输入 union 日志、四窗口选择算法、主要结构统计量、1% 最小实际差异、时间块 bootstrap、确定性 seed／CI、B/C 图哈希、provenance 抽样、三态停止规则和 test-once 纪律。冻结协议内保留的旧章节号不静默改写；BitLINK 位置以[全文核验勘误](BitLINK全文核验勘误-20260912.md)为准，即 Chapter 5。`F_pub` 的科学语义、固定 revision、函数与参数已裁决；纯标准库实现已通过合成边界测试和固定种子 10,000 样本的上游函数差分核验。v1.1 在任何 S0 数据运行前关闭列投影，v1.2 在任何效应计算前关闭 bootstrap 随机流和 percentile 取点，v1.3 在任何效应或图输出前关闭图与抽样歧义。AWS 冻结早期前缀的 manifest、主链、prevout、locking script、金额与 BIP30 语义已经全量资格化，故允许继续 S0。该冻结不授权模型、标签读取、S1/S2 或正式测试集访问。

纯标准库参考实现 `src/btcaml/data/asof_replay.py` 已锁定事件规范排序、按位置 cutoff、确定性并查集、只从历史支持取代表、future-only 中介语义以及 `p_merge`/`p_rewrite`；8 项定向测试通过。该实现只消费合成的已提取事件和端点，不含 raw adapter、CoinJoin 过滤、bootstrap 或真实数据，因此只关闭实现语义的局部歧义，不关闭数据 Gate，也不构成实验结果。

`src/btcaml/data/script_identity.py` 已冻结原始 scriptPubKey 字节的 SHA-256 标识，以及“首字节为 `OP_RETURN` 或长度大于 10,000”这一窄排除规则；空脚本和 `OP_FALSE OP_RETURN` 不被该操作性规则排除。`experiments/experiment_registry.csv` 已先行登记 S0 提取并保留高度 12000 的真实暂停核验。v1.3 明确为 S0-only；S1 模型实验和 S2 历史部署评测均需 S0 Go 后另建协议版本。

标签时间目前是最高风险阻断项。若无法形成 `L_{<=t}`，第一阶段 Go/No-Go 只能依据不使用标签的 partition/graph 指标；实体类型模型实验必须降级为回顾性敏感性分析，不能宣称历史部署可信度。

## 6. 下一步验收顺序

1. 完成已登记的 union provenance 提取到高度 `286560`，核验摘要、SQLite、checkpoint 计数和 source/runner 绑定；不得改变 cutoff、窗口、horizon、过滤器或 1% 阈值。
2. 在 v1.3 冻结提交后实现独立评估器，复用 `asof_replay.py` 的确定性重放语义，并对 future-only 中介、图规范化、provenance 抽样、block bootstrap、CI 索引和三态聚合留下可失败检查。
3. 在 `experiments/experiment_registry.csv` 另行预登记效应运行；连续独立运行两次，保存 union、分区、B/C 图、抽样审计、bootstrap、失败和负结果的规范化哈希。
4. 依据 v1.3 的完整性 Gate、bootstrap 区间和三态规则作 Go／No-Go／Inconclusive 决策；不得因结果修改协议。
5. 只有 S0 Go 后才起草并冻结 S1 标签／模型协议；未取得 `L_{<=t}` 时只允许回顾性实体类型敏感性，不得表述为历史部署或 AML 风险识别。

本快照是决策证据，不是实验协议，不授权全量处理、模型训练或外部发布。
