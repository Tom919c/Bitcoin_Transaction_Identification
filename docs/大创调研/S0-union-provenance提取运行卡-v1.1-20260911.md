# S0 union provenance 提取运行卡（Gate 3A v1.1）

日期：2026-09-11  
状态：planned；尚未读取效应、标签、模型输出或正式测试结果。

## 1. 冻结绑定

- 协议：`docs/大创调研/Gate3A-严格按时可见实体图预注册协议-v1.1-20260911.md`
- source manifest：`configs/data/aws_btc_s0_source_manifest_v1_1.json`
- manifest SHA-256：`e32ad2f33ecbc184eb04159f0adbb22dd2a4a1a47f1e280cbbca699432d67f3d`
- 提取器 revision：`accd68ef75cee008f9a62643c848048832566b47`
- 目标高度：`286560`
- cutoff：`[181440, 199584, 215712, 225792]`
- `W=2016`；`H=[13140, 52560, 105120]`；`F_pub/F_wide/F_none` 共用同一 union provenance。

本运行只生成可恢复的 S0 SQLite 状态和提取摘要。`p_merge`、`p_rewrite`、bootstrap 与 Go/No-Go 由后续独立、冻结的评估运行计算；本运行不得做效应解释。

## 2. 产物

- 状态库：`data/raw/aws_btc_prefix_v0_1_20260910/s0_state/s0_union_v1_1.sqlite`
- 摘要：`experiments/diagnostics/aws_btc_s0_union_extract_v1_1_20260911/summary.json`
- 实验登记：`experiments/experiment_registry.csv` 的 `aws-btc-s0-union-extract-v1.1-20260911`

原始 AWS 对象与 SQLite 状态均为忽略的私有本地资产，不提交、不公开再分发。

## 3. 两段式执行

第一段在完整区块 `12000` 后主动暂停，用真实 Parquet 验证端到端列投影、prevout script、union provenance、checkpoint 原子性和空间增长。预期退出码为 `4`（`resumable_operator_pause`）；其他非零退出视为失败并保留状态与日志。

```powershell
uv run python scripts/research/extract_aws_btc_s0_events.py --transaction-cache-dir data/raw/aws_btc_prefix_v0_1_20260910/transactions --block-cache-dir data/raw/aws_btc_prefix_v0_1_20260910/blocks --state-db data/raw/aws_btc_prefix_v0_1_20260910/s0_state/s0_union_v1_1.sqlite --output experiments/diagnostics/aws_btc_s0_union_extract_v1_1_20260911/summary.json --reserve-gib 20 --batch-size 8192 --checkpoint-blocks 2016 --pause-after-height 12000
```

暂停后必须验证 SQLite `quick_check=ok`、提交高度/计数一致、三个 profile 的逐块统计完整、输出摘要尚不存在且可用空间仍高于 20 GiB。全部通过才用同一命令删除 `--pause-after-height 12000` 恢复到高度 `286560`。

## 4. 停止条件

- manifest、冻结工件、引用代码或 runner SHA 不匹配；
- 不允许列出现、prevout 缺失、块内序号/主链绑定失败或 BIP30 审计失败；
- checkpoint/SQLite `quick_check` 或 S0 计数不一致；
- 剩余空间低于 20 GiB；
- 任何标签、实体类型、alias、外部 attribution、模型输出或既有效应指标进入读取路径。

失败记录不得删除或覆盖。确定性实现缺陷可按 Gate 3A 规则修复并从头重跑，但必须新增版本和决策记录。
