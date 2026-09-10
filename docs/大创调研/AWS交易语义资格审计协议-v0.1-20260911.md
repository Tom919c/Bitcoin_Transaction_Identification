# AWS Bitcoin 交易语义资格审计协议 v0.1

日期：2026-09-11

状态：**执行前冻结**。本协议只资格化 Gate 3A 候选数据源，不是 Gate 3A v1.0，不授权 S0、标签读取、模型训练或 `p_merge`/`p_rewrite` 计算。

## 1. 审计对象与固定输入

审计范围是冻结清单 `experiments/diagnostics/aws_btc_prefix_listing_v0_1_20260910.json` 中的 1890 个 transaction objects；清单 SHA-256 固定为：

```text
c237f1abc1c9cc220dc54112931481818a6d986f71b1e5f8d634b6d4dd1530f0
```

区块主链与交易计数以项目私有缓存的 1897 个 block objects 重放结果为准。重放产物是 `experiments/diagnostics/aws_btc_prefix_preflight_v0_1_project_cache_20260911.json`，SHA-256 固定为：

```text
c5301f8a43c5b270759df5fb936812ecdab63572d64364d542fcce7c515cc8e
```

交易字节冻结产物、schema 审计产物和执行脚本 SHA-256 必须在运行记录中绑定。任何输入对象缺失、长度或对象身份不一致、冻结产物未完成，均在读取交易行前失败。

## 2. 全局链序

AWS 日分区内的交易行没有顺序保证，区块分区日期也存在相邻日期回退，因此不得按文件顺序更新状态。先从已核验 block objects 建立 `height -> (block_hash, transaction_count, partition_date)` 映射，并为按日期排列的 transaction partitions 计算剩余分区最小高度。读取一个分区后，只有高度严格小于所有尚未读取分区最小高度的交易才允许按 `(block_height, transaction_index)` 排序并提交；其余交易保留在缓冲区。最后一个分区读取后清空缓冲区。

每个高度必须恰好出现 block manifest 声明的交易数，块内 index 必须构成 `0..transaction_count-1` 的排列；index 0 必须是 coinbase，其他位置不得是 coinbase。每笔交易的 block hash 和 partition date 必须与区块映射一致。

## 3. 标识与历史重复 txid

`txid`、witness `hash` 和 `block_hash` 必须是 32 字节十六进制值，但 `txid` 不假设全局唯一。Bitcoin 早期存在 BIP30 历史重复 coinbase txid；把 `(txid, vout)` 建成全历史唯一键会错误拒绝合法主链。

审计器按链序维护**实时未花费输出集合**，键为 `(txid_bytes, vout)`：

1. 非 coinbase 输入必须引用集合中当前存在的唯一 live outpoint；同一交易内不得重复引用，同一 live outpoint 被消费后立即删除。
2. 创建输出时若同键仍在 live 集合中，立即失败；只有旧实例输出已经全部消费后，历史重复 txid 的新实例才可按主链语义进入集合。
3. parent 的 `(block_height, transaction_index)` 必须严格早于当前交易；同块花费只允许引用更小的 transaction index。
4. 输入自带的 `script_hex` 是 scriptSig，不用于 parent locking script。parent locking script 必须来自 live outpoint 记录的原始 output `script_hex`。

该规则只验证冻结主链的 outpoint 语义，不把共同输入启发式解释为真实实体所有权。

## 4. BTC double 到整数聪的冻结规则

对每个 output value、input value、交易级 input/output value 与非 coinbase fee，执行同一转换：

1. 值必须是有限 IEEE 754 double，且不小于 0。
2. 计算 `scaled = value * 100_000_000`，`satoshi = round(scaled)`。
3. 要求 `abs(scaled - satoshi) < 0.5` 聪；严格不等号排除恰好半聪的舍入歧义。
4. `satoshi` 必须位于 `[0, 2_100_000_000_000_000]`。交易输入和输出总额也不得超过该上限。
5. 全量记录最大残差、越界数、非有限数和首个失败位置。任何失败均阻断，不得静默取整、截断或更换阈值。

Python `round` 的半偶数规则不会影响通过项，因为半聪及以上残差已经被拒绝。该阈值来自整数聪唯一恢复条件，不依据后续分区效应选择。

## 5. 逐交易一致性

每笔交易必须满足：

- `input_count`/`output_count` 等于实际嵌套列表长度；输入、输出 index 分别为从 0 开始的无缺口排列；每笔交易至少一个输出。
- 输出 `script_hex` 非空时必须是偶数字符、可还原为原始字节；空 locking script 允许保留，不得误当缺失。
- 非 coinbase 的每个 input value 与 live parent output 的整数聪完全相等。
- 非 coinbase 满足 `sum(inputs) = sum(outputs) + fee`；顶层 `input_value`、`output_value` 和 `fee` 转换后分别与重算值一致。
- coinbase 不做普通输入守恒，但其 input count 必须为 0；输出与交易级 output value 仍按相同整数聪规则核验。
- `date` 必须等于对象路径的 UTC partition date；任何 null、重复位置、缺块、未知 block hash、缺 parent、已消费 parent 或前向 parent 均立即失败。

## 6. 实现、恢复与资源边界

允许使用仓库已锁定的 Python 3.12、PyArrow 16.1.0 和标准库 SQLite。不得新增依赖。SQLite 只保存 live UTXO 与恢复元数据，位于 Git 忽略目录；键使用 32 字节 txid 与整数 vout，value 使用整数聪，script 保存原始字节。

事务只在完整区块核验后提交。恢复点必须绑定 listing SHA、transaction-freeze SHA、block-preflight SHA、脚本 SHA 和最后完整高度；任一绑定变化都拒绝续跑。中断恢复可以重新扫描原始分区并跳过已提交高度，但不得从半个区块继续。

启动前至少保留 20 GiB 空闲空间；运行中若预计写入会突破保留线，安全提交最后完整区块后停止。不得删除原始冻结缓存换取运行空间，也不得把临时 UTXO 数据库提交到 Git。

## 7. 输出与停止线

成功产物至少记录：所有输入 SHA、脚本与环境版本、开始/结束时间、对象/区块/交易/input/output 数、schema 变体、最大金额残差、BIP30 重复 txid 实例数、live outpoint 峰值和最终值、失败计数、恢复次数、SQLite 大小与最终状态。

只有以下条件全部满足，AWS 早期前缀才通过 transaction semantic source qualification：

- 1890/1890 transaction objects 与 1897/1897 block objects 绑定一致；
- 区块高度、hash、交易位置和 coinbase 结构全量一致；
- 所有非 coinbase prevout 可由实时 UTXO 状态唯一恢复，且不存在未解释的 live-key 冲突；
- 所有金额通过冻结转换，parent value 与交易守恒全量一致；
- 运行可从冻结输入与提交代码重放，且未读取标签、分区效应或模型结果。

任一条件失败均保持 Gate 3A v0.1 和 S0 未授权。成功也只关闭数据源语义硬门；Gate 3A v1.0 仍需把最终 manifest、资源实测、过滤器输入映射和 S0 执行入口另行冻结。
