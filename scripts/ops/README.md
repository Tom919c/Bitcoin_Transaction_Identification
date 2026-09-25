# scripts/ops — 运维脚本（非冻结产物）

本目录放**可修改的运维脚本**：数据搬运、校验、评估对执行、结果比对。

与 `scripts/research/` 的区别：那里是**冻结产物**，改动任何一个都会使已有 S0 产物失效并需重新走版本化
流程。本目录的脚本可以随时改，不参与任何哈希绑定。

## 脚本清单

### `run_frozen_s0_pair.sh`

在实验室服务器上**串行**执行冻结的 Gate 3A 评估对（run01 + run02）。

关键约束（脚本头部注释有完整说明）：

- **两次运行必须在同一台机器**。`evaluation.json` 内嵌 `environment = {python, sqlite}`，且
  `secondary.variation_of_information` 用 `math.log`，跨解释器/跨 libm 不保证逐位一致，跨主机不可能
  通过 finalizer 的哈希一致性检查。
- **不得并发**。协议要求两次连续独立运行。
- **runner 跑到结束才落盘**，无进度日志、无部分输出。被杀或卡住的运行无法续跑，只能从头重来。

启动（**不要**在 ssh 命令里追加 `& sleep N`，详见下方"事故记录"）：

```bash
setsid nohup ./run_frozen_s0_pair.sh > pair.out 2>&1 < /dev/null
```

实测耗时（服务器，机械 `/dev/sdb`，安静机器）：

| 运行 | 耗时 | 说明 |
| --- | --- | --- |
| run01 | 1h15m43s | 紧跟在 21 GB 状态库传输之后，数据仍在页缓存中 |
| run02 | 7h18m32s | 冷缓存，4 KB 随机读，受机械盘寻道限制 |

**冷缓存运行可以比热缓存慢约 6 倍，而结果仍逐字节相同。**

### `compare_s0_evaluations.py`

逐字段比对两次 `evaluation.json`。

```bash
python compare_s0_evaluations.py <evaluation_run01.json> <evaluation_run02.json>
```

核对 27 个 cell 的全字段与 13 个顶层字段，输出判定 `AGREE` 或 `STOP_AND_AUDIT`，报告写到脚本同目录的
`s0_evaluation_comparison.json`。退出码 0 = AGREE，1 = STOP_AND_AUDIT。

**应在两台机器上分别独立运行**（本机 + 服务器），结论一致才继续。

### `verify_dataset_transfer.py`

服务器侧数据集验收校验器，输出两组判据：

- `correct::*` — 逐对象 SHA-256（transactions 对 byte freeze、blocks 与边车对本机清单、utxo 与状态库对冻结全文件哈希）
- `usable::*` — SQLite `quick_check`、三表行数与 `metadata.last_committed_height` 对 extractor summary、抽样 parquet 可被 pyarrow 打开

末尾给出 `acceptance: PASS/FAIL` 与失败项清单。**只有 PASS 才进入删除本机数据阶段。**

## 完整定案流程

S0 定案的完整顺序（2026-09-25 已走通一遍）：

1. 服务器：`run_frozen_s0_pair.sh` 跑完 run01 + run02，各自产出 `evaluation.json`
2. 服务器与本机：分别跑 `compare_s0_evaluations.py`，两边都须 `AGREE`
3. 服务器：核对 finalizer 五个输入文件的哈希（provenance、两次 evaluation、correction、checkpoint），
   全部匹配冻结值后运行 `scripts/research/finalize_aws_btc_s0.py`
4. 回迁 `final.json` 与两个 `evaluation.json` 到本机，用 `sha256sum` 与 `cmp` 复核
5. 更新 `experiments/experiment_registry.csv`（该文件被 `.gitignore` 忽略，提交须 `git add -f`）
6. 写定案记录、刷新 Research Passport 与决策日志

## 事故记录（务必读）

### ssh 启动后台任务会累积并行实例

用 ssh 前台命令启动服务器后台任务时，命令里含 `setsid nohup … & sleep N` 这类组合会被沙箱
**SIGTERM**（表现为 exit 1、无输出），但**服务器侧进程其实已经起来了**。

2026-09-25 连续四次"失败"的启动累积出**四个并行实例**，互抢同一个状态库的 I/O 并写同一个
`evaluation.json`。

正确做法：

1. 发起后**立即返回**，不在同一条命令里 `sleep` 等待；
2. 隔一段时间用**独立命令**核对进程，必须 `grep -c` / `pgrep -cf` **计数**——只看 `head -3` 会在
   四实例时漏判；
3. 清理分两步：先杀父脚本，再杀 `setsid` 脱离会话的 python 子进程
   （`pgrep -f "[e]valuate_aws_btc_s0"`，方括号技巧避免匹配到自己的 ssh 命令行）。

### 不要用启动初期的短窗口采样外推完成时间

2026-09-25 曾在 run02 启动约 5 分钟时采样，见 CPU 利用率约 1%，据此外推"要 100+ 小时"。
实际只用了 7h18m32s。**冷启动阶段在做索引预热，I/O 特征与稳态差异巨大。**

### 页面缓存压力的归因要谨慎

首次 run02 停在 `folio_wait_bit_common`、CPU 利用率 4.5%，初判归因于 ComfyUI 争抢页缓存。停掉
ComfyUI 后重跑，启动速度仍是约 1%，说明该归因不完整。

真正原因是：run01 紧跟 21 GB 状态库传输之后、数据仍在页缓存中，而 run02 从冷缓存开始、做 4 KB 随机
读，机械盘寻道成为瓶颈（稳态 `rchar` 约 2.4 MB/s，远低于顺序吞吐 87–92 MB/s）。

判断内存是否真的紧张，看 **`MemAvailable`** 而不是 `MemFree`。Linux 把空闲内存用作页缓存是正常且
有益的；`MemFree` 低不代表资源不足。
