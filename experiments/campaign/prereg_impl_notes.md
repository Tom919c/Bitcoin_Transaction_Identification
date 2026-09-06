# 冲刺一实现说明（sprint1_prereg.yaml 的实现层补充）

日期：2026-09-06。预注册 YAML 本体不改动；本文件记录实现层的资源优化及其等价性证据。

## 背景

原全批量训练（`btcaml.training.trainer.Trainer`）在本协议（约 24.2 万节点 / 124 万边、hidden=128、3 层）上单进程峰值 commit 约 23.6GB（消息张量 `(1.24M,128)`×2 方向×3 层 + 反向传播保存的激活 + 分配器碎片）。本机（27.7GB RAM + 页面文件，总虚拟约 46.7GB）在训练与日常应用并存时会耗尽系统 commit 导致死机（2026-09-06 两次实锤，watchdog 与任务日志留痕）。

## 变更：逐层梯度检查点训练循环（`run_sprint1.py: _forward_ckpt` + `train_full_batch_lean` / `train_vrex`）

- 探针实测（`scripts/_probe_mem.py`，一次完整 train step 的 Windows 工作集/commit）：
  - plain：forward 后 WS 22.2GB，峰值 commit 23.6GB；
  - 整模型单段 checkpoint：forward 仅 5.6GB，但 backward 重算整段又达峰值 23.2GB——**单大段无效**；
  - **逐层 checkpoint（采用）**：forward 峰值 6.9GB，backward 峰值 12.8GB，稳态 commit 约 13.4GB（−43%）。
- 每层一个 checkpoint 段，`use_reentrant=False`，`preserve_rng_state` 默认开启 → dropout 掩码在重算时一致，**计算结果与普通前向数学等价**；
- EGS/DirSAGE 在 runner 内按 frozen 文件的层结构组合实现（不改 frozen 文件）；DGResEGS 的 backbone 循环同理；层间 norm/relu/dropout 保持在外层图中；
- 其余语义与 `Trainer.train_full_batch` 逐项镜像：全局类权重 weighted_ce、Adam(lr=1e-3, wd=5e-4)、grad clip 1.0、每 epoch val macro_f1 评估、早停、best.pt 原子保存格式、history JSON/CSV；
- 冻结超参数（hidden/layers/dropout/lr/wd/loss/epochs/patience/seeds）零改动；
- 代价：每 epoch 计算量约 ×2（重算），换取峰值内存 −43% 且不再耗尽系统 commit。

## 等价性证据（2026-09-06）

2-epoch smoke（EGS、seed42、temporal_balanced_no_temporal、4 线程）：

| 指标 | 原 Trainer（smoke_all_models） | 整模型 ckpt（smoke_lean_equivalence） | 逐层 ckpt（smoke_perlayer_equivalence） |
|---|---|---|---|
| epoch1 loss | 2.5484 | 2.5484 | 2.5484 |
| epoch1 val macro-F1 | 0.1876 | 0.1876 | 0.1876 |
| 2-epoch val macro-F1 | 0.1876 | 0.1876 | 0.1876 |

三者逐位一致。

## 纪律不变项

- val-first、test-once、`--final-test` 门控不变；
- 全部 Go/No-Go 阈值以 `sprint1_prereg.yaml` 为准；
- 严格串行（一次一个训练进程）、BelowNormal 优先级、看门狗监控（watchdog.log，LOW_MEM/STALLED/NO_PROC 告警）。

## 资源规则（用户指令 2026-09-06）

禁止并行实验；一个一个跑。队列由 `scripts/campaign_queue.ps1` 驱动，单步失败记录后继续，4 线程 + BelowNormal 优先级。

