# Gate 3A 预注册协议 v1.3：严格按时可见实体图

日期：2026-09-12

状态：**已冻结，S0-only；效应计算前图与抽样消歧版**。本版取代 v1.2 作为 S0 评估协议，补冻 B/C 图的唯一展开与规范化哈希，以及 1,000-event provenance audit 的候选总体、跨 cell 去重和配额算法；数据字节、cutoff、窗口、horizon、过滤器、主要统计量、bootstrap、阈值和三态决策均未改变。仍不授权模型训练、标签读取、S1/S2、正式测试集读取或 2.52 亿节点全图重建。

研究分支：`asof-entity-graph-pilot`

冻结依据：

- 数据源 manifest：`configs/data/aws_btc_s0_source_manifest_v1_1.json`，SHA-256 `e32ad2f33ecbc184eb04159f0adbb22dd2a4a1a47f1e280cbbca699432d67f3d`；用途为私有内部 S0，公开再分发为 false。它显式取代 v1.0，只新增协议原本已经要求的 `inputs.index`，并要求读取 `inputs/outputs` 的列级投影只落到列出的 Parquet 叶字段。
- 全量交易语义：`experiments/diagnostics/aws_btc_transaction_semantic_full_v0_2_20260911/summary.json`，SHA-256 `7c8973b34921d77deefafe23ac07eecfd7d907dbec1fadb62677fb3a1b1c99b0`；独立验证文件 SHA-256 `f17c72cf9c421fbec6eb7219cd1e2615cd4ef0f068845bcc8862c0af6d7880f8`。
- 全量语义状态：`data/raw/aws_btc_prefix_v0_1_20260910/semantic_state/utxo_v0_2.sqlite`，SHA-256 `6cafc290b8e3b951417c85c5b6dd431e71c3d0c548ac45bdc6a7bdee4a34d924`；独立只读 `PRAGMA quick_check=ok`。
- 最近邻边界：[BitLINK 全文核验与主线边界](BitLINK全文核验与主线边界-20260911.md)。通用 temporal linkage／cluster-chain continuation 不作为创新；只检验固定支持上的 as-of 分区版本和图重写。
- 本 v1.1 冻结提交必须先于 union provenance logger 的正式数据运行提交；任何 S0 结果不得反向修改本协议。v1.0 没有启动过 S0，故本修正不涉及结果后见、test 重开或效应驱动修改。
- 本 v1.2 在 union provenance 提取运行期间、任何 `p_merge`、`p_rewrite` 或 bootstrap 输出产生前发布。提取器明确不计算效应或作 S0 决策；因此该修正不读取结果，也不改变已开始的提取 estimand。v1.2 的冻结提交必须先于 S0 评估器实现提交和首次效应运行。
- 本 v1.3 同样在任何效应、分区或 B/C 图输出产生前发布。独立反方审计指出 v1.2 对图展开／序列化和 provenance 抽样仍允许多个合规实现得到不同哈希或样本；本版只关闭这些执行歧义。已运行的 extractor 保存去重端点、交易总量、事件位置、过滤决策与原始对象定位，足以执行本版规则，无需修改或重启提取。

## 1. 决策问题与阶段边界

主问题是：在历史截止区块 `t` 可采取行动的实体类型识别中，只把实体分区从当时可重放的 `C_t` 替换为未来观察期形成的 `C_T`，是否会以稳定且具有实际量级的方式改变历史实体图，并进一步改变模型比较、概率校准和固定人工审查预算下的结果？

本协议不把“未来聚类知识可能回写历史”作为新发现。当前候选贡献是可重放、受控地测量这种分区版本差异及其下游传播。地址聚类只是启发式实体近似；`0–10` 是实体类型，`-1` 是未标注上下文，均不等于非法、欺诈或 AML 风险。

研究按三个不能越级的阶段执行：

| 阶段 | 问题 | 是否使用标签 | 解锁条件 |
|---|---|---|---|
| S0：结构数据 Gate | `C_t` 与 `C_T` 是否在固定地址支持和固定交易窗口上产生实质分区与图重写 | 否 | 本协议 `v1.3` 冻结且数据完整性门通过 |
| S1：回顾性实体类型敏感性 | 分区版本是否改变既有 11 类实体类型标签的可投影性、模型比较与决策 | 可以，但没有 `L_{<=t}` 时只能作回顾性敏感性分析 | S0 为 Go，标签来源、许可、冲突规则和快照哈希完整 |
| S2：历史部署评测 | 当时可得的标签与特征能否支撑历史决策 | 是，必须为 `L_{<=t}` | S0 为 Go，且每条标签有可核验的首次公开／发现／采集时间 |

本 `v1.3` 只授权 S0。S1 必须在 S0 为 Go 后另建协议版本，先冻结标签证据锚点、许可、B/C 配对 eligible set、冲突与未投影规则、模型预算和 test-once 记录；S2 只有取得 `L_{<=t}` 后才能另行预注册。S0 的通过不会自动授权模型训练，也不会把回顾性实体类型标签变成历史可得标签。

旧 `C1-预注册协议草案-20260901.md` 研究的是“两输出交易的未来关联揭示”，与本协议的实体分区版本效应不是同一任务。本协议只复用其主链顺序、块内信息截止、协作交易不确定性、聚簇重采样和 test-once 纪律；不继承其预测单位、竞争事件标签或 5 个百分点性能门槛。

## 2. 固定对象与对照

对第 `j` 个历史截止：

- `t_j`：历史截止区块；主分析在区块结束处截断。
- `H = 52,560` 个区块：主未来观察跨度，约等于按每日 144 块计算的一年；`T_j = t_j + H`。
- `W = 2,016` 个区块：历史评估窗口；`X_j` 为 `[t_j-W+1, t_j]` 的主链交易。
- `U_{<=t}`：不晚于 `t`、由冻结启发式和过滤配置生成的 union 事件。
- `C_t = DSU(U_{<=t})`：从空状态或经哈希验证的等价检查点按确定顺序重放所得分区。
- `V_j`：`X_j` 中所有输入 prevout 的 locking script，加上所有输出在**创建时**按冻结脚本规则判断为非 `provably-unspendable` 的 locking script，取其唯一 `script_id` 集合。是否在 `t_j`、`T_j` 或 tip 被花费、是否仍为 UTXO 都不参与定义。
- `C_{T_j}|V_j`：只将 `T_j` 时分区限制到同一支持 `V_j`；不得加入 `t_j` 后首次出现的标识。
- `G(C, X_j)`：仅用同一历史窗口 `X_j`、按分区 `C` 聚合的有向实体转移多重图。

对任一分区 `C`，稳定代表定义为 `r_C(v) = min {u in V_j : C(u) = C(v)}`。最小值只能在限制后的 `V_j` 内取；完整分量中 `V_j` 外的未来脚本可以作为 `C_{T_j}` 的连接路径，但不得成为支持、节点 ID、端点或分母。

S0 的主要配对对照为：

- B：`G(C_{T_j}|V_j, X_j)`，未来分区、历史交易窗口；
- C：`G(C_{t_j}|V_j, X_j)`，历史分区、同一历史交易窗口。

两者只允许分区版本不同。原始交易、支持集合、脚本解析、过滤配置、金额单位和图聚合代码必须完全相同。使用完整未来交易和特征的 A 条件只作 hindsight 诊断；聚类细化 D 条件是最近邻基线，S0 通过前不实施。

本协议把 `G(C, X_j)` 唯一操作化为不作金额归因的**有向实体端点多重图**。只使用 `X_j^nc`：节点集为 `r_C(V_j)`；对每笔交易 `q`，由已定义的去重排序端点集合 `I_C(q)` 与 `O_C(q)` 取笛卡尔积，每个 `(source, target)` 生成一条由 `(block_height, tx_index, txid, source, target)` 唯一标识的交易级边。自环保留；不同交易产生的同一实体对保持为不同边；任一端点集合为空时该交易不产生边，但仍保留在交易记录流中。不得把整笔输入、输出或 fee 总额复制、均分或推断为 pairwise 边金额；`input_sat`、`output_sat`、`fee_sat` 只作为交易级整数属性保存，因此本图不声称恢复 UTXO 的真实实体间金额流。

B/C 图的规范化 SHA-256 对一个 UTF-8、LF 结尾的 JSON Lines 字节流计算。每行固定使用 `ensure_ascii=true`、key 字典序、无额外空白的 `separators=(",", ":")`；script ID、txid 与 block hash 均编码为小写、定长十六进制，整数为 JSON 十进制整数。流顺序固定为：一条 `meta`；按 script ID 升序的全部 `node`；按 `(block_height, tx_index, txid)` 升序的全部非 coinbase `transaction`，其输入／输出代表列表内部升序且保留空列表；最后按 `(block_height, tx_index, txid, source, target)` 升序的全部 `edge`。四类记录的 key 集和字面量必须与下列 JSON 对象完全相同，禁止额外 key；省略号只表示运行时值，不是字面量：

```text
{"analysis_cutoff_height":...,"extractor_summary_sha256":"...","filter_profile":"F_pub|F_wide|F_none","horizon_blocks":...,"partition_cutoff_height":...,"partition_vintage":"B|C","record_type":"meta","schema_version":"asof-entity-endpoint-multigraph-v1","source_manifest_sha256":"...","window_id":"t..."}
{"record_type":"node","script_id":"..."}
{"block_hash":"...","block_height":...,"fee_sat":...,"input_entities":["..."],"input_sat":...,"output_entities":["..."],"output_sat":...,"record_type":"transaction","tx_index":...,"txid":"..."}
{"block_height":...,"record_type":"edge","source":"...","target":"...","tx_index":...,"txid":"..."}
```

`filter_profile` 使用当前 cell 的唯一字面量；`partition_vintage` 仅为 `B` 或 `C`，相应 `partition_cutoff_height` 分别为 `t_j+horizon_blocks` 或 `t_j`。三个交易金额字段对非 coinbase 记录都必须为整数，缺失即完整性失败。B/C 除端点代表、节点／边及两个 partition 字段外必须逐字段同源。规范化流本身可不持久化，但其 byte count、四类 record counts 和 SHA-256 必须保存在 cell manifest；这些 manifest 级计数不进入 JSONL `meta`，避免未定义字段改变图哈希。

## 3. 数据资格与窗口选择

### 3.1 数据硬门

S0 输入必须能提供或确定性恢复：主链 `block_hash` 与 `block_height`、区块内交易序号、`txid`、输入／输出序号、prevout、原始 locking script、金额、coinbase 标记和主链重组处理。若不能恢复交易顺序、prevout locking script 或唯一主链，数据源 No-Go。

数据 manifest 必须在任何效应统计前记录：来源、许可、访问日期、完整区块范围、tip hash、schema、行数、字节数、原始文件或分片 SHA-256、缺块／重复／重组处理、生成代码 revision 和 dirty 状态。外部查询还要记录查询文本、扫描字节上限、导出文件哈希和费用上限。

当前本地 2.52 亿节点聚合库、最终 alias 表和 Zenodo `10.5281/zenodo.22239038` 都未满足该硬门。2026-09-09 的只读盘点未在仓库、Windows 默认 Bitcoin Core 目录或受控候选路径发现 `blk*.dat`、原始 TXO 快照或 manifest，也未发现当前进程已设置 `BITCOIN_DB_URL` 或 Bitcoin RPC/BigQuery 连接环境变量；本机源因此仍未满足。

[Google BigQuery 公共数据说明](https://docs.cloud.google.com/bigquery/public-data)、[GoogleCloudPlatform knowledge catalog](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/bundles/crypto_bitcoin/viz.html) 和 [Bitcoin ETL schema](https://github.com/blockchain-etl/bitcoin-etl/blob/master/README.md#schema) 已确认：交易含 `block_hash`、`block_number`、块内 `index` 和 `is_coinbase`；input 含 `spent_transaction_hash` 与 `spent_output_index`；output 含作为 locking script 的 `script_hex`、金额和输出序号。字段层面可通过父交易哈希与输出序号连接 prevout locking script，而 input 自身的 `script_hex` 是 scriptSig，不能误用。该核验只把 BigQuery 提升为“schema 上可继续审计的候选”，不等于选定数据源；当前快照版本、唯一主链／重组语义、实际缺失率、许可适用、项目与账单授权、扫描字节和导出成本均未关闭，仍不得发起查询或写成已选数据源。

[Blockchain ETL 公共数据登记](https://github.com/blockchain-etl/public-datasets/blob/master/README.md)只报告 Bitcoin 数据相对链头滞后 3 块；[Bitcoin ETL 流式命令说明](https://github.com/blockchain-etl/bitcoin-etl/blob/master/README.md#stream)把设置 lag 描述为处理链重组的最简单办法，因为离链头越远越不易重组。该证据说明存在运行时缓冲策略，不证明公共表具有不可变历史版本、完整重组对账或唯一主链保证。当前审阅到的公开 ETL/Airflow 路径也没有提供可直接引用的历史快照标识。因此，本项目只能把一次带查询时点、表元数据、tip hash、完整性结果、外部区块哈希交叉核验和导出哈希的冻结导出视为候选输入；3 块 lag 本身不能关闭重组硬门。

2026-09-09 官方入口审计审阅了 Bitcoin ETL README、public-datasets README、[Bitcoin ETL streaming 文档](https://github.com/blockchain-etl/blockchain-etl-streaming)和公开架构说明。在已审官方文档中，未发现无需部署者凭证即可访问、带版本标识的历史 GCS 快照；streaming 部署关于 GCS 的说明要求使用者创建并配置自己的 GCS bucket，以保存 `last_synced_block.txt` 状态，未给出公开历史数据对象、manifest 或回放保证。已审文档把 Pub/Sub 描述为持续流式出口，并报告 Bitcoin lag 为 3 块，但未承诺公共 topic 可从创世块回放到冻结高度的完整、版本化前缀；当前没有独立冻结导出／快照和完整性审计，不能把它资格化为 S0 输入。在当前已审官方入口范围和本地资产条件下，待资格化候选暂收束为：(1) BigQuery 经授权 dry-run、资格查询、冻结导出；(2) 用户提供的 Bitcoin Core datadir 或 raw TXO snapshot，经版本、tip、hash、容量审计。该收束不表示已经穷尽其他可能满足硬门的原始链来源。

2026-09-10 的 [AWS 公共比特币数据源资格审计](AWS公共比特币数据源资格审计-20260910.md)最初只把 `s3://aws-public-blockchain/v1.0/btc/` 提升为候选。2026-09-11 完成的项目控制字节冻结与全量语义审计进一步关闭了私有内部 S0 的硬门：选定前缀包含 1,890 个 transaction 对象、53,659,133,189 字节和 1,897 个 block 对象、90,449,066 字节；覆盖主链高度 `0–290291`，tip hash 为 `00000000000000001296ee1fb5fdbbcf95f0519ad8c40c07414617d70dc16a38`。审计处理 290,292 个区块、34,731,184 笔交易、78,085,978 个输入和 87,704,214 个输出，精确识别两次 BIP30 历史覆盖，无语义失败，金额最大绝对残差为 0.0078125 聪。对象身份、schema、block preflight、交易语义 summary/verification 及引用代码哈希均由 source manifest 绑定。公开桶未启用 S3 Versioning、原对象 `VersionId=null`，且公开再分发许可仍未关闭；因此资格只适用于冻结本地字节上的私有内部 S0，原始数据不得公开发布，结论不得外推到 2014-03-12 之后。

候选源只有在实际 schema、主链／重组语义、快照可复现性和成本授权逐项核验后才可入选。即使存在名为 `spent_transaction_hash` 的字段，也必须以官方 schema 和固定样本核验它确为 `vin.prevout` 的父交易哈希，不能仅凭列名推断。BigQuery 适配还必须保存查询文本、项目与账单授权、最大扫描字节、费用上限、查询时点和导出分片哈希；这些条件未关闭前不得发起付费或大规模查询。

资格查询固定为 `scripts/research/qualify_bigquery_crypto_bitcoin_v0_1.sql`，记录模板固定为 `configs/data/bigquery_source_qualification_manifest_v0_1.json`。查询只检查从创世块到预先冻结末端的区块连续性、唯一位置、父 outpoint、locking script 和 tip，不计算 `p_merge`、`p_rewrite` 或任何标签／模型结果。必须先对同一查询和参数 dry-run，记录估算扫描字节，并在真实运行中设置不高于人工批准额度的 `maximum_bytes_billed`；未获项目与账单授权时保持 `pending_authorization`，不得执行。任何只从局部高度开始的检查只能算适配器 smoke，不能代替正式资格查询，因为 `C_t` 的共同输入 union 必须从创世块累计。

### 3.2 四个历史截止的确定规则

数据快照与可用末端 `h_max` 冻结后，先排除不能提供完整未来跨度的区块，即只保留 `0` 至 `h_max-H`。按该范围内的累计非 coinbase 交易数，取 20%、40%、60% 和 80% 四个分位首次达到的区块，再向下对齐到最近的 2,016 块边界，得到四个 `t_j`。若两个截止因对齐而重合，后一个顺延一个 2,016 块窗口；若因此越过 `h_max-H`，数据源 No-Go。

该规则只能读取区块级交易计数，不能读取聚类差异、标签或模型结果。`W`、`H` 与四个分位在 `v1.1` 后不得依据观察到的效应修改。主结论只适用于预注册的 `(W=2,016, H=52,560)` 设计，不能外推成所有时期或任意聚类延迟均稳定。

为暴露 horizon 依赖，预先保留 `H_short=13,140`（约三个月）与 `H_long=105,120`（约两年）两个完整报告的敏感性跨度，但它们不参与 S0 Go/No-Go。若原四个 cutoff 中某点没有足够 `H_long` 覆盖，按数据 manifest 标为结构性不可用，不重选 cutoff。每个 cutoff 都报告 UTC 日历时间、脚本/协议时代、窗口交易量和距数据 tip 的区块数；不得挑选最有利 horizon 作为主结果。

## 4. 脚本标识、主链顺序与 union 日志

基本标识不是地址字符串，而是 prevout 的原始 `scriptPubKey` 字节经 `SHA-256` 得到的稳定 `script_id`。这保留 P2PK、P2PKH、P2SH、SegWit、Taproot 和可解析但没有传统地址字符串的脚本。不可花费输出不进入分区；无法取得原始脚本的输入记为缺失并触发数据完整性统计，不能静默丢弃。

本协议把 `provably-unspendable` 冻结为一个窄的操作性规则：原始脚本首字节为 `OP_RETURN`（`0x6a`），或脚本长度严格大于 10,000 字节。空脚本、`OP_FALSE OP_RETURN`（`0x00 0x6a`）和其他不满足这两个条件的脚本不由该规则排除；这不是一般性的可花费性证明。`script_id` 必须直接对原始字节取 SHA-256 小写十六进制，禁止先转地址、反汇编、规范化或重新编码。纯标准库参考实现位于 `src/btcaml/data/script_identity.py`。

输入的 `scriptSig` 或 witness 只是花费交易携带的解锁材料，不是被引用 prevout 的 locking `scriptPubKey`，二者不得互换。数据适配层至少输出 `(block_hash, block_height, tx_index, txid, input_index, prev_txid, prev_vout, prevout_value, prevout_scriptPubKey, output_index, output_value, output_scriptPubKey, coinbase)`；缺列或字段语义未核验时不得进入 S0。

主启发式只采用共同输入所有权启发式：对每笔通过过滤、具有至少两个不同输入 `script_id` 的非 coinbase 交易，将字典序最小的 `script_id` 与其余唯一输入依次形成星形 union。它是可重放的启发式，不是真实共同控制权。change heuristic、外部人工合并和 GNN refinement 不进入 S0 主分析。

每个 union 事件至少记录：

```text
event_id, block_hash, block_height, txid, tx_index, event_index,
script_id_a, script_id_b, heuristic_id, heuristic_version,
filter_profile, filter_decision, evidence_json, source_manifest_sha256
```

排序键固定为 `(block_height, tx_index, event_index, script_id_a, script_id_b)`；一对脚本先按字典序规范化，提取层对重复事件保留首次事件并记录重复计数，参考重放层必须拒绝任何尚未去重的 `event_id`。并查集 root 选择必须由固定规则决定，不能依赖线程完成顺序。检查点只能作为加速手段；从空状态重放到同一 cutoff 的分区哈希必须与检查点路径一致。

## 5. 协作交易过滤

S0 至少运行两个预先冻结的过滤配置，并保留一个诊断条件：

- `F_pub`：采用 `BTCGraphConstruction` 固定 revision `3becbc44a951abbe1e85d374a66340a639059d1c` 的五个实际 mix detector 的 OR，排除命中 JoinMarket、Wasabi 1.0、Wasabi 1.1、Wasabi 2.0 或 Whirlpool mix 的交易。它是“固定实现 profile”，不是 CoinJoin 真值，也不声称逐式等同论文。Whirlpool Tx0 不进入此主过滤器。
- `F_wide`：在 `F_pub` 基础上，再排除 `n_inputs >= 2`、`n_outputs >= 3` 且至少三个输出金额完全相同的交易。它是更严格的操作性排除条件，可能排除普通批量支付；它既不是 CoinJoin 真值，也不构成真实共同控制关系或真实效应的上界／下界。
- `F_none`：不排除协作交易的历史 common-input 基线，只作诊断，不单独支持 Go。

PayJoin 与未被规则识别的协作交易记为“未判定”，不能当作非协作交易真值。两个主过滤配置都要报告排除率、未判定范围、按规则族命中数和 union 数；`F_none` 也必须完整报告，不能只在结果有利时展示。跨配置一致只表示对两个操作性 profile 稳健，不表示对真实非协作交易稳健。若未来获得独立 detector，只能在新协议版本中加入，不能替换本版结果。

### 5.1 `F_pub` 固定实现清单

以下函数名、默认参数与判定顺序来自 [`BTCGraphConstruction` 固定源码树](https://github.com/hugoschnoering2/BTCGraphConstruction/tree/3becbc44a951abbe1e85d374a66340a639059d1c)；本地实现不得根据论文文字静默改参数或修正上游行为：

| 规则族 | 固定函数 | 主 profile 参数 |
|---|---|---|
| JoinMarket | `is_coinjoin_joinmarket` | `min_num_participants=3` |
| Wasabi 1.0 | `is_coinjoin_wasabi_1_0` | `epsilon=1,000,000`；`max_inputs_per_participants=7`；`min_num_participants=5` |
| Wasabi 1.1 | `is_coinjoin_wasabi_1_1` | `epsilon=1,000,000`；`max_inputs_per_participants=7`；`min_num_participants=5`；`max_mixing_level=12` |
| Wasabi 2.0 | `is_coinjoin_wasabi_2` | 固定 denomination 集；`max_inputs_per_participants=10`；`min_num_inputs=50`；`min_input_value=5,000` |
| Whirlpool mix | `is_coinjoin_samourai` | `epsilon_max=20,000` |

本地纯标准库移植位于 `src/btcaml/data/coinjoin_filters.py`，固定上游 revision 常量与上述 commit 一致。审计时临时取得的上游 `coinjoin.py` 原始字节 SHA-256 为 `D181C90D19DEE0C477C55A1797ADFCFA44914B2C6A351B664954252E371D0C01`；以随机种子 `20260909` 生成 10,000 个合法交易特征样本，对五个函数的返回值／异常类型逐项差分，结果完全一致。合成测试另覆盖规则边界、稳定 tie/order、Tx0 不进入主过滤、`F_wide`、`D_wp100k` 和论文 Tx0 诊断。Ruff 检查和独立纯标准库 smoke 均以 exit 0 完成；定向 9 项与全套 35 项 pytest 都打印到 `[100%]`，但当前旧环境在 pytest 结束阶段不退出，人工中断后进程码为 1，因此只能记录“测试体已全部执行且未显示失败”，不能记录为干净的 pytest exit 0。

上游 `populate_coinjoins` 还调用 `is_tx0_samourai`，随后 `populate_alias(..., exclude_coinjoin=True)` 按 CoinJoin 表中的 `(block, position)` 整体排除交易。但固定源码中的 `TransactionFeatures.is_position_zero_in_output` 判断“输出下标 0 是否存在”，`is_tx0_samourai` 又在该属性为真时立即返回 `False`；这与论文要求“恰有一个金额为 0 的输出”不是同一谓词。正常非空输出序列包含下标 0，因此该实现不能作为论文 Tx0 规则的可信转录。

主 profile 明确不调用 Tx0 detector，原因有三项：论文把 Tx0 定义为进入 Whirlpool pool 前的 pre-mix 资金准备，尚未完成混合；论文最终 CoinJoin 总数明确排除 Tx0；本研究的过滤目标是阻断会破坏共同输入所有权假设的协作 mix，而不是把所有隐私工具相关交易都当成协作交易。该选择仍可能漏掉具有多方输入的异常 Tx0，不能解释为 common-input 必然正确。

### 5.2 实现—论文差异诊断

CoinJoin 原论文 PDF 固定为仓库内 `cp13_coinjoin.pdf`，SHA-256 为 `2DA3099D48A528E11C777FF08E59D1980049815CA04E1215DC084614E612DCB9`。全文核验得到：Tx0 条件包含恰一个零值输出；论文实验参数为 `a_max=70`、`eta_1=0.5`、`eta_2=3`、`epsilon_min=100`、`epsilon_max=100,000`；Whirlpool mix 的论文 `epsilon_max=100,000`。固定源码 Tx0 默认值分别为 `75/0.5/3/1/11,000`，Whirlpool mix 默认 `epsilon_max=20,000`。

这些差异预先作为诊断，不并入主 Go/No-Go profile：

- `D_wp100k`：只把 Whirlpool mix 的 `epsilon_max` 从固定实现的 `20,000` 改为论文的 `100,000`，其余 `F_pub` 条件不变；报告新增命中、被抑制 union 和两个主要统计量的差值。
- `D_tx0-paper`：按论文的零值输出语义和论文参数标记 Tx0 候选，只报告候选数、与五个主 detector/`F_wide` 的交集及其潜在 union 数；不自动阻断 union，不单独支持 Go。

若任一诊断尚未通过合成边界测试，只能标为未实现，不能从真实数据结果反推实现。若诊断差集足以使主结论越过 1% 判据或改变三态决定，最终解释必须降级为过滤器敏感，不能宣称对协作交易处理稳健。

## 6. S0 主要统计量

所有主要统计量在同一 `V_j` 和同一 `X_j` 上配对计算。比较等价关系时只统计 `V_j`，但允许 `V_j` 外脚本在全局 DSU 中作为连接中介；令 `X_j^nc` 为 `X_j` 中非 coinbase 交易：

1. **未来合并参与率 `p_merge`**：对每个 `v in V_j`，收集与 `v` 在 `C_{T_j}` 下同簇的 `V_j` 脚本，并计算它们在 `C_{t_j}` 下具有多少个不同代表；若至少为 2，则 `v` 受未来合并影响。`p_merge` 是受影响脚本数除以 `|V_j|`。
2. **交易端点重写率 `p_rewrite`**：对每个 `q in X_j^nc`，定义 `I_C(q)` 为其所有输入脚本经 `r_C` 映射后的去重、排序列表，`O_C(q)` 为其创建时非 `provably-unspendable` 输出脚本经 `r_C` 映射后的去重、排序列表。空列表保留为空；同一实体的重复端点只计一次。若 `(I_{C_T}(q), O_{C_T}(q)) != (I_{C_t}(q), O_{C_t}(q))`，则该交易被重写。`p_rewrite` 是被重写交易数除以 `|X_j^nc|`。

等价的实现公式为：

```text
p_merge = mean_v 1[ |unique{r_Ct(u): u in V_j and r_CT(u)=r_CT(v)}| >= 2 ]
p_rewrite = mean_q 1[ (I_CT(q), O_CT(q)) != (I_Ct(q), O_Ct(q)) ]
```

这里 `r_CT` 始终指 `C_{T_j}|V_j` 的限制后代表，`r_Ct` 指 `C_{t_j}|V_j` 的限制后代表。必须用至少一个“未来脚本只作连接中介”的合成链反例锁定该语义。

次要结构统计量包括：受未来合并影响的 `C_t|V_j` 实体节点比例、实体节点压缩率、原跨实体转移变为自环的交易比例、聚合边合并率、分量合并数量与规模分位数、按金额加权的端点重写率，以及可由 contingency table 精确计算的 variation of information。它们用于解释结构效应及与后续预算单位的距离，不能在主要量失败时替代 Go 判据，也不能证明 top-k 队列必然改变。

标签投影、标签冲突和未投影比例属于 S1；S0 不得因终态标签可用而提前读取或筛选窗口。S0 输入采用列级 allow-list，只允许原始区块、交易、prevout、locking script、金额、顺序、coinbase 标记、过滤器所需的交易局部字段和 provenance/manifest。禁止读取 `label`、`entity_type`、最终 `alias`、`ground_truth`、外部 attribution 表及其派生列；输入 schema hash、实际列清单和拒绝访问日志必须保存。

## 7. 完整性 Gate

任一过滤配置、任一 cutoff 必须同时满足：

1. 同一输入连续独立运行两次，union 日志、`C_t`、`C_{T_j}|V_j`、B 图和 C 图的规范化 SHA-256 全部一致。
2. 纳入的 union 事件必填 provenance 字段完整率为 100%，排序单调率为 100%，且 `C_t` 中晚于 `t` 的事件数为 0。
3. B/C 的 `V_j`、交易集合、交易字段与金额逐项一致；支持集合差异为 0。
4. B/C 导出的所有节点 ID 与端点代表都属于 `V_j`，域外代表数为 0；`V_j` 的构造不读取 spent/UTXO 状态或标签表。
5. provenance audit 只使用主 horizon 和两个主 profile，形成八个 `(window_id, filter_profile)` cell。某 cell 的候选总体是：在该 profile 下为 include、事件位置不晚于 `T_j=t_j+52,560`，且事件在 `C_{T_j}` 中所在完整分量至少含一个 `V_j` 成员的所有唯一 union event；因此历史事件和通过域外脚本连接支持的 future-only 中介事件都可进入审计。cell 顺序固定为 cutoff 升序，每个 cutoff 内 `F_pub` 后 `F_wide`；cell 内按 `SHA-256(event_id_bytes || UTF-8("asof-audit-v1"))`、再按原始 32-byte `event_id` 升序。第一阶段依 cell 顺序各分配前 100 个尚未被任何早期 cell 分配的 event；任一 cell 不足 100 个则完整性失败。第二阶段按同一 cell 顺序循环，每次给当前 cell 分配其下一个全局未选 event，直至全局恰有 1,000 个；所有 cell 都耗尽仍不足 1,000 则失败。故最终样本以 `event_id` 全局去重并保存唯一 cell assignment，每 cell 至少 100 个。对每个样本必须从冻结 object key 定位原交易，核对 block/tx 位置和 evidence_json；按记录的 input indices 恢复 parent txid/vout，在同一冻结主链源中定位唯一父输出，并验证其原始 locking script SHA-256 对应事件端点。规则证据用同一原始交易与 parent scripts 重新计算并与保存结果逐项比较。1,000 个事件中至少 995 个全部恢复成功；任何无法解释的未来事件进入 `C_t` 仍直接失败。
6. 缺失 prevout/script 的交易比例不高于 0.1%，且这些交易在 B/C 中使用同一排除规则；超过门槛则只允许修复数据源后重跑，不得插补。
7. 每个 input parent outpoint 必须能连接到同一主链快照中的唯一父输出，并分别记录 missing、orphan、reorg 和 duplicate 计数；主链选择或重组语义未核验时直接阻断。

完整性失败先停止效应解释。一次协议内允许修复确定性实现或数据缺失并从头重跑；若仍失败，S0 No-Go，不进入模型。

## 8. 数值 Go/No-Go 与不确定性

最小实际差异阈值预设为 `1.0%`：`p_merge >= 1.0%` 且 `p_rewrite >= 1.0%`。它是项目资源与复杂度门槛：若受影响的历史支持或交易低于这一量级，本项目不以复杂模型追逐更小的广泛结构效应。它不与 top 1% 实体队列建立数学映射，也不代表领域通用经济阈值；小而高度集中的结构变化仍可能影响队列，只能在 S1 用冻结评分函数直接检验。

每个窗口和过滤配置执行 10,000 次配对 circular moving-block bootstrap，主 block length 为 144 块。每个脚本唯一分配到其在 `X_j` 中首次出现的区块，每笔交易分配到所在区块，由此形成逐块 numerator/denominator 充分统计。每次 replicate 从 `W` 个区块位置中有放回抽取 14 个起点，每个起点取 144 个环形连续区块，拼接并截断为 `W`；重复抽到的区块按重复次数计权。B/C 使用同一重采样索引，分区保持由完整 `U_{<=t}` 与 `U_{<=T}` 冻结，只重算评估窗口的两个比率。边界使用 circular wrap，不跨入窗口外真实区块。

bootstrap 主种子固定为十进制整数 `20260911`。`window_id` 的唯一编码固定为小写 ASCII 字母 `t` 紧接 cutoff 高度的无前导零十进制表示，例如 `t181440`；`horizon_blocks` 与 `block_length` 同样使用无前导零十进制，`filter_profile` 只能为字面量 `F_pub`、`F_wide` 或 `F_none`。为使 cell 执行顺序不影响随机流，每个 `(window_id, horizon_blocks, filter_profile, block_length)` 的子种子固定为 UTF-8 编码的 `"20260911|" || source_manifest_sha256 || "|" || window_id || "|" || horizon_blocks || "|" || filter_profile || "|" || block_length` 的 SHA-256 前 8 字节按无符号大端整数解释；所有组成字符均在 ASCII 范围。该子种子初始化 Python 标准库 `random.Random`，每个起点由 `randrange(W)` 生成。两个主要统计量在同一 cell 内复用完全相同的区块 multiplicity。10,000 个 replicate 排序后，95% percentile CI 固定取 nearest-rank 的第 250 与第 9,750 个值，即零起始索引 `249` 和 `9749`；不使用插值。任何库版本不得静默改变这些规则。

报告点估计、逐 cell 95% percentile CI 和窗口间完整分布，并用 block length 72 与 288 块完整复跑为不参与决策的敏感性结果；敏感性 replicate 分别抽取 `ceil(W/72)` 与 `ceil(W/288)` 个起点并截断到 `W`。地址或交易行不能当作独立同分布样本；seed 方差也不能替代数据不确定性。这些 CI 只描述各 cutoff/filter cell 的窗口组成不确定性，不声称具有跨 16 个 cell 的同时 95% 覆盖，也不用于宽泛总体推断。本阶段不以显著性 `p` 值判定 Go。

三类结论固定为：

- **Go to S1**：完整性 Gate 全部通过；在 `F_pub` 和 `F_wide` 下，各至少 3/4 个窗口同时满足 `p_merge` 与 `p_rewrite` 的主 95% CI 下限均不低于 1.0%。若没有标签时间，只解锁回顾性 S1，不解锁 S2。
- **No-Go**：完整性重跑仍失败；或聚焦全文满足下述完整等价 checklist；或存在同一个 `m in {p_merge, p_rewrite}`，使 `F_pub` 与 `F_wide` 各至少 3/4 个窗口的该统计量 95% CI 上限低于 1.0%。不同统计量在不同窗口失败不能拼成此条 No-Go。此时停止以分区版本影响为核心的模型创新。
- **Inconclusive**：其余情况。只允许一次预注册确认性扩展：保持 cutoff、未来跨度、过滤器和统计量不变，另定义 `W=4,032` 的新 estimand 并从头重跑；原 `(W=2,016,H=52,560)` 结果保持不变、单独报告，不得被覆盖。扩展达到同一 Go 规则才解锁 S1；否则按资源停止线转为 No-Go，不增加新窗口或改阈值。

由于 `p_merge`、`p_rewrite` 是共同主要门槛，不再以多个单独假设检验挑选成功指标。次要统计量只解释机制并报告完整结果。

## 9. S1/S2 的标签、切分与模型纪律

S0 为 Go 后才能提交独立的模型执行附录；本节先固定不可违反的边界：

- 标签以原始地址／脚本证据为起点投影到 `C_t` 与 `C_{T_j}|V_j`；同一 cluster 内存在多个不同实体类型时记为冲突，不按多数票覆盖。`-1` 保持未标注，不作负类。
- 没有标签首次公开、发现或采集时间时，所有结果标为回顾性敏感性分析；不得使用“历史部署性能”“当时可识别”或风险概率措辞。
- 训练、验证、测试为连续、互不重叠的历史 cutoff 组；边界只按交易量、类别支持和协议时代在看模型结果前确定。训练期已见实体与未来新分量分别报告。
- 所有标准化、特征选择、阈值和校准只在训练／验证期拟合。测试集只在配置、manifest 和 decision log 锁定后打开一次；额外打开必须记录日期、原因、commit 和影响。
- 首轮只比较多数类、逻辑回归、一个树模型、MLP、现有 GraphSAGE 与 EGS。每个学习模型使用同一组五个种子 `[42, 3407, 1234, 2026, 8675309]`，最多 20 个验证集超参数配置；不新增 GNN 架构或预训练任务。
- 主要下游比较是同一模型在 B/C 下的配对差异和模型排名是否翻转；报告 Macro-F1、逐类 F1、macro one-vs-rest AUPRC、Brier、ECE、错误—覆盖曲线，以及固定 1% 和 5% 预算的队列 overlap 与已标注实体类型 yield。yield 不是非法活动命中率。
- 数据不确定性按时间块或实体簇重采样，五个 seed 的离散只报告优化不稳定性。无法形成足够独立时间块或类别支持时只作描述性结论。

S1 执行附录必须在运行前另行冻结：使用同一组 script-level label evidence anchors 建立 B/C 配对 eligible set；明确冲突、未投影和 `-1` 是移除、拒判还是仅作描述性统计，并固定每个分母；分别报告 node-level 与 script-anchor-weighted 配对指标；固定多类概率到单一审查优先级的函数、tie-break、B/C 实体匹配和队列去重规则。缺少任一项时，不得解释模型排名、校准或预算队列传播。

S1/S2 不得用测试表现反向改变 S0 阈值、窗口、过滤器、标签映射或模型预算。

## 10. 运行登记与不可变产物

单一 as-of 实验登记入口固定为 `experiments/experiment_registry.csv`。字段包括：`run_id`、`question_id`、`protocol_version`、`data_manifest_sha256`、`cutoff_height`、`window_blocks`、`horizon_blocks`、`filter_profile`、`code_revision`、`dirty_state`、`seed`、`budget`、`primary_metrics`、`secondary_metrics`、`decision_rule`、`started_at_utc`、`completed_at_utc`、`status`、`artifact_directory` 和 `notes`。当前文件已保留来源资格审计的 planned、failed 与 completed 状态；S0 正式运行必须另行先登记 planned 行，运行失败也必须更新而不能删除。

每次 S0 运行保存：原始数据 manifest、union 日志或其分片及哈希、cutoff 分区映射、B/C 图 manifest、抽样审计记录、原始统计、bootstrap 配置与输出、命令、环境和失败日志。结果表与图只能从这些产物生成。

数据来源记录还必须包含源 revision、快照或分区标识、schema manifest、原始与导出哈希、适配器 revision，以及适用的查询、授权和费用记录；只保存 URL 不构成可重放快照。

## 11. 最近邻完整等价 checklist

只有一项可取得全文的工作同时满足以下全部条件，才触发“完整等价评测”自动 No-Go：

1. 研究对象是 Bitcoin 地址／脚本聚类，并显式比较历史可见 `C_t` 与更晚形成的 `C_T`；
2. 在同一历史交易窗口与同一历史支持上只改变分区版本，并明确处理 future-only 脚本；
3. 提供可重放的时间化 cluster lineage，或给出等价的固定原始链、启发式版本和 cutoff 重建；
4. 定量报告分区与实体图结构变化；
5. 在实体类型这一相同预测单位上，至少同时评估模型比较、概率校准、选择性预测、固定预算队列中的两项；
6. 结论来自同行评审正文或稳定公开全文，而不是搜索摘要、宣传页或无法核验的二手转述。

未满足全部条件的近邻仍可分别否决组件级首创表述、收紧贡献或成为强基线，但不能事后被扩张为自动 No-Go。公开工件缺失不使已发表科学问题恢复新颖性；若科学问题等价但本项目仍有可复现 benchmark 增量，必须降级并重写贡献，而不是继续声称新问题。

## 12. `v1.3` 冻结清单

以下全部关闭后，本文件才能作为当前执行版 `v1.3`；截至 2026-09-12 已全部关闭：

1. 选定原始链来源并固定许可、schema、区块范围、tip hash、文件/导出哈希和资源上限；
2. 核验数据能恢复主链、块内顺序、prevout 和原始 locking script；
3. 固定 `F_pub` 的函数、参数、依赖、上游 revision 与本地等价性检查；
4. 用合成反例核验 `F_wide`、脚本标识、事件排序、并查集确定性和同区块未来边界；
5. 关闭 BitLINK 全文风险，或在 decision log 中记录全文不可得及禁止的创新措辞；
6. 建立数据与实验登记路径，并预先写入四个 cutoff 的确定规则、阈值和一次扩展规则；
7. `v1.3` 明确冻结为 S0-only；S1/S2 只能由后续独立协议版本授权；
8. 在任何效应计算前固定 bootstrap 主种子、顺序无关的 cell 子种子和无插值 percentile CI 索引；
9. 固定 B/C 有向实体端点多重图的交易展开、自环／空端点语义、无金额归因边界和 JSONL 哈希字节规范；
10. 固定八个 provenance audit cell 的候选总体、排序、全局去重、两阶段配额和逐事件恢复判据。

任何未填项都不能用 Pilot 或模型结果倒推补写。v1.1 已满足先于 union logger 正式数据运行提交；`v1.3` 冻结提交必须先于评估器实现与首次效应运行。

截至 2026-09-12，第 1、2 项由 AWS S0 source manifest、项目控制字节冻结、block preflight 和 v0.2 全量交易语义审计关闭；审计包含主链连续性、块内顺序、prevout locking script、整数聪转换和两次精确 BIP30 覆盖。第 3 项由固定 detector revision、本地实现和 10,000 样本差分关闭；第 4 项由 `F_wide`、脚本字节哈希／排除边界、事件排序、确定性并查集、同块 cutoff 和 future-only 中介的合成测试关闭；第 5 项由 BitLINK 官方学位论文全文核验关闭，通用 cluster linkage／cluster chain 首创表述已明确禁止；第 6 项的登记路径、cutoff、阈值和扩展规则已关闭；第 7 项冻结为 S0-only。v1.1 关闭嵌套字段最小投影；v1.2 关闭确定性 bootstrap 与 CI；第 9、10 项由本版的图与抽样规范关闭。真实 union provenance 提取已在无效应边界下启动，但 `p_merge`、`p_rewrite`、bootstrap、分区／图哈希和 S0 决策均尚未计算。因此本协议冻结为当前 S0 评估版 `v1.3`。

## 13. 决策记录

| 日期 | 决策 | 理由与反方意见 | 状态 |
|---|---|---|---|
| 2026-09-08 | S0 与旧 C1 交易标签任务拆开 | 两者预测单位和 estimand 不同；混合会使结构 Gate 读取标签并产生循环论证 | 已写入 |
| 2026-09-08 | S0 只用共同输入 union，禁止 change/GNN/人工合并 | 先隔离最小可重放机制；聚类细化已有直接近邻 | 已写入 |
| 2026-09-08 | 主设计固定 `W=2,016`、`H=52,560`，另完整报告三个月/两年 horizon 敏感性 | 一年不是领域真值，只是固定 vintage estimand；四个 cutoff 不能支持全时期泛化 | 2026-09-11 随 source manifest 冻结 |
| 2026-09-08 | 以 `p_merge`、`p_rewrite` 的 1% 作为共同资源门 | 阈值不等于 top-k 队列效用；真正队列影响必须在 S1 直接检验 | 2026-09-11 冻结 |
| 2026-09-08 | 独立反方提出固定支持、统计量唯一性、filter 伪真值、bootstrap 与三态逻辑问题 | 已把 `V_j` 改为创建时定义，限制实体代表到 `V_j`，形式化两个统计量，收紧过滤措辞与逐统计量停止线，并把扩大窗口定义为新 estimand | P0 已关闭；P1/P2 边界已写入，待 v1.0 实现核验 |
| 2026-09-09 | 在冻结数据源前只实现纯标准库参考语义与合成契约测试 | 该实现不解析原始块、不访问标签、不计算真实效应；用于提前锁定 cutoff、域外中介、固定支持和两个主要统计量 | 8 项定向测试通过；不构成 S0 Pilot 或 v1.0 冻结 |
| 2026-09-09 | BitLINK 论文正文仍未取得，但作者 22 页幻灯片已逐页核验 | 幻灯片明确研究 address flushing、用前后簇交叉验证桥接簇，并输出按时间延伸的 cluster chain；它不提供足以核验固定支持 `C_t/C_T`、可重放 union lineage 或下游决策传播的正文细节 | cluster-chain 组件碰撞已确认；完整等价风险保持 Unknown，冻结版禁止“BitLINK 未做 `C_t/C_T`”“首次 temporal cluster linkage/cluster chain”措辞 |
| 2026-09-09 | 通过 DataCite 与 Zenodo record API 核验数据集外层工件 | 已确认版本 `1.0`、CC BY 4.0、数据作者、三个 ZIP 的精确大小与 Zenodo MD5 声明，总压缩体积 15,199,299,781 字节；受限 Range 尝试未取得中央目录且按停止线未重试 | 外层 manifest 关闭；内部 schema、raw outpoint/script、主链语义与 lineage 未取得，作为 as-of 重放输入仍 No-Go |
| 2026-09-09 | 下载并核验最小 `1_training_dataset.zip`，只审计中央目录与 CSV 首行 | 410,978,944 字节文件的 Zenodo MD5 匹配，本地 SHA-256 已记录；header 显示 node/edge-style 字段与 `node_id,alias`，但没有 raw block/transaction/outpoint/script、coinbase 或 union provenance；列的精确语义仍未核验 | 缺失字段足以使该训练包确定 No-Go 为本协议 `C_t` 重放源；不读取 alias 数据行，不下载另外两个大包 |
| 2026-09-09 | `F_pub` 冻结为固定 revision 的五个实际 mix detector，不含 Tx0 | 论文第 12–14 页把 Tx0 定义为 pre-mix 准备，第 19 页的总 CoinJoin 统计明确排除 Tx0；固定源码又把输出位置 0 与零值输出混淆。机械纳入会掩盖实现缺陷，按论文“修好”则会静默改变固定实现 | 主语义、本地实现与合成／随机差分核验已关闭清单第 3 项 |
| 2026-09-09 | 论文—实现参数差异仅作预注册诊断 | 固定源码与论文的 Tx0、Whirlpool mix 参数不一致；`D_wp100k` 和 `D_tx0-paper` 用于报告差集，不能替代或事后改写主 profile | 合成边界实现完成；真实差集仍须等合格数据源，若改变 1% 三态决定则结论降级为过滤器敏感 |
| 2026-09-09 | 本机无可用原始链快照；BigQuery 仅保留为候选 | 默认 Bitcoin Core 目录和仓库数据目录无 `blk*.dat`/TXO manifest；Google 官方 schema 支持 prevout→output `script_hex` 连接，但未证明快照、主链／重组、缺失率和费用边界 | 数据硬门未关闭；不查询、不运行 S0 |
| 2026-09-09 | 固定 BigQuery 候选源资格查询与 manifest 模板，但不执行 | 资格查询从创世块累计并只读完整性；公开管线的 3 块 lag 是运行缓冲，不是不可变快照或完整重组证明；局部窗口不能替代 `C_t` 前缀 | 等待项目／账单授权、dry-run 字节上限、tip 外部核验与冻结导出哈希 |
| 2026-09-09 | 官方入口审计暂时收束待资格化数据候选 | 已审文档未给出无需部署者凭证即可访问、带版本标识的历史 GCS 快照，也未承诺公共 Pub/Sub topic 可回放完整、版本化的创世块前缀；当前已审范围和本地资产条件下，保留经授权 BigQuery dry-run／资格查询／冻结导出，或用户提供的 Bitcoin Core datadir/raw TXO snapshot，不排除以后以同一硬门审计其他原始链来源 | 数据硬门未关闭；不查询、不运行 S0 |
| 2026-09-09 | `v1.0` 仅授权无标签 S0；S1/S2 必须另行冻结 | 当前没有可审计标签时间与许可；把 S0 Go 自动扩张为模型授权会绕过标签、调参与 test-once Gate | 标签和模型均不进入当前协议执行范围 |
| 2026-09-09 | 冻结原始脚本字节标识和窄 `provably-unspendable` 规则 | 地址字符串和脚本规范化会合并或丢失标识；一般可花费性判断超出 S0 所需 | 参考实现与边界测试完成；与 as-of/CoinJoin 合计 23 项在禁用第三方 pytest 自动插件后干净通过 |
| 2026-09-10 | AWS Public Blockchain Data 进入待资格化候选，不冻结为数据源 | 匿名访问、创世覆盖、关键 Parquet 字段和指定 parent-output join 已做样本核验；但公开桶未启用 S3 Versioning，且样本对象 `VersionId=null`，全量 transaction 对象约 2,026.838 GiB，金额为 `double`，数据对象许可和完整快照均未关闭 | Gate 3A 仍为 v0.1；不登记正式运行、不启动 S0；早期完整前缀只能在效应读取前按资源规则另行预注册 |
| 2026-09-10 | AWS 50 GiB 早期前缀预检完成，仍不冻结数据源 | 纳入 1890 个 transaction objects/53,659,133,189 压缩 S3 transaction 对象字节，最后完整日 2014-03-12；额外读取至 2014-03-19 的区块元数据以识别边界，候选 `h_max=290291`，`eligible_end=237731`，非 coinbase 交易数 `18131019`；首次达到 `[183399,200724,216332,227188]`，对齐 `[181440,199584,215712,225792]`；独立只读实现重算匹配，效应指标未读取 | P1 许可、不可回溯快照、source provenance mapping 和实际执行 revision 未关闭；Gate 仍 v0.1，S0 不启动 |
| 2026-09-11 | BitLINK 官方学位论文全文核验关闭最近邻风险 | Chapter 4 明确覆盖 streaming cluster linkage、address flushing 和 cluster-chain continuation；未形成固定支持上只改变 `C_t/C_T` 并成对量化分区／实体图重写的完整等价设计 | 通用 linkage 方向 No-Go；窄 as-of 分区版本审计保留 |
| 2026-09-11 | 交易语义 v0.1 在高度 91842 拒绝历史 live txid overwrite | 失败来自真实 BIP30 历史例外，不可用放宽唯一性检查掩盖；状态安全回滚并保留失败产物 | v0.1 failed 如实登记；未读取效应 |
| 2026-09-11 | 交易语义 v0.2 只接受两次精确 BIP30 覆盖并全量重跑 | 高度、区块哈希、txid、旧高度、旧输出值和旧脚本全部白名单匹配；独立 SQLite quick check 与计数复核通过 | 来源交易语义资格关闭；不构成 S0 结果 |
| 2026-09-11 | 冻结 AWS 早期前缀为私有内部 S0 唯一输入 | source manifest 绑定对象清单、schema、block preflight、语义 summary/verification 与引用代码；公开再分发仍为 false，前缀只到 2014-03-12 | Gate 3A 第 1、2 项关闭；外推与发布边界保留 |
| 2026-09-11 | Gate 3A 升级为 v1.0，固定 cutoff `[181440,199584,215712,225792]`、`W=2016`、主 `H=52560`、1% 双指标阈值 | 七项冻结清单均已关闭；阈值是资源门，不是下游队列效用保证 | 只授权 S0；模型、标签、S1/S2 继续禁止 |
| 2026-09-11 | 在任何 S0 数据运行前发布 v1.1 列投影修正 | v1.0 allow-list 漏列协议本已要求的 `inputs.index`；顶层 struct 投影还会载入未列出的 scriptSig 等子字段。v1.1 只新增 `inputs.index` 并改为显式 Parquet 叶字段投影 | 数据、设计、阈值和授权边界均未变；v1.0 无结果可污染 |
| 2026-09-12 | 在任何效应计算前发布 v1.2 可复现性修正 | v1.1 已规定 10,000 次 bootstrap 与块长，但遗漏 RNG seed、cell 派生和 percentile 索引；若留给实现默认值会造成库／执行顺序依赖 | 固定主种子 `20260911`、SHA-256 cell 子种子和 nearest-rank 索引；数据、estimand、阈值和决策逻辑均未变，提取运行未产生效应结果 |
| 2026-09-12 | 在任何效应计算前发布 v1.3 图与 provenance 抽样消歧 | 独立反方指出“实体转移多重图”和“八 cell 合计至少 1,000 个唯一事件”允许多个合规实现产生不同哈希、样本和完整性结论 | 固定无金额归因的交易级端点笛卡尔边、JSONL 字节规范、支持相关候选总体和两阶段全局去重配额；主要 estimand 与三态判据不变 |
| 2026-09-21 | 对 provenance audit 的 `assigned_cells` 输出字段发布勘误，不新建协议版本、不重启提取或审计 | 该字段在事件选择、两阶段分配、恢复与阈值判定之后由 cell 字典拼接错误生成，其错误值不参与任何冻结规则；按 `events[].assigned_cell` 重新分组得到八个单元各 125 条且各自全部恢复。原 provenance 与 checkpoint 保持不变，另附绑定两者 SHA-256 的不可变 correction sidecar，由 finalizer 强制校验 | 数据字节、cutoff、窗口、horizon、过滤器、抽样规则、候选总体、1% 阈值与三态判据全部未变；本勘误只关闭输出汇总缺陷，不替代两次独立结构评估、图哈希一致性检查与最终 Go/No-Go。详见 `docs/大创调研/S0-provenance汇总勘误-20260921.md` |
