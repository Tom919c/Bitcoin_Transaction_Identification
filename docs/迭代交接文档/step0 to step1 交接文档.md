# BTC-AML 项目新对话交接文档：论文线 + 代码线

> 用途：在本项目下新建 ChatGPT 对话时，把本文档作为上下文迁移材料。  
> 当前阶段：数据协议阶段已经基本完成，准备进入模型实验阶段。  
> 核心主线：**采样偏差发现 + 标签保持数据协议 + 11 类长尾比特币实体识别 + 边-时序-方向图学习模型**。

---

## 0. 新对话开场提示词

新建对话时，可以直接复制下面这段：

```text
这是 BTC-AML/GNN 项目的交接上下文。请先阅读并继承本文档，不要重新推翻已有结论。

项目当前主线不是继续堆普通 GNN，而是：
1. 证明旧 TopK 子图采样会严重扭曲原始比特币实体图的标签空间；
2. 构建 label-preserving / class-balanced-khop / temporal-balanced 三类新数据协议；
3. 在完整 11 类长尾标签空间上做实体识别；
4. 用 class_balanced_khop 作为第一主训练数据集；
5. 用 temporal_balanced 作为 classwise temporal 泛化实验数据集；
6. 后续再推进边-时序-方向感知模型 ETD-SAGE。

重要标签约定：
- -1 = UNLABELED / 背景节点，不参与监督训练和评估；
- 0~10 = 11 个监督类别；
- 不能再使用 y != 0、ignore_index=0、label > 0 这类旧逻辑；
- 正确逻辑是 y >= 0 为监督节点，loss ignore_index=-1，num_classes=11。

请优先保证任务逻辑正确、代码同步一致、命令行输出简洁直观、日志结果自动归档、并兼顾大规模 PostgreSQL 数据处理性能。
```

---

## 1. 项目研究目标的当前版本

### 1.1 题目方向

当前建议论文方向：

**Sampling-Aware Edge-Temporal Directional Graph Learning for Long-Tailed Bitcoin Entity Identification**

中文可写为：

**面向长尾比特币实体识别的采样感知边时序方向图学习方法研究**

或者更偏 AML：

**面向比特币反洗钱场景的采样感知边时序方向图学习实体风险识别方法**

### 1.2 当前研究问题

原始问题不是“哪个 GNN 准确率更高”，而是：

> 在 2.5 亿级节点、7.8 亿级边的比特币实体图中，如何构建不扭曲标签空间、适合低标签长尾学习的训练子图，并进一步利用交易边、时间和资金流方向进行实体识别与敏感实体排序？

---

## 2. 已经得到的核心结论

### 2.1 原始数据库标签审计结论

已成功运行：

```powershell
python scripts/audit_raw_labels.py --config configs/data/raw_db.yaml
```

原始数据库规模：

```text
nodes_estimate: 252,219,007
edges_estimate: 785,954,737
```

原始数据库有标签节点共：

```text
34,098
```

原始数据库包含 **11 类标签**：

| label | count |
|---|---:|
| INDIVIDUAL | 23,236 |
| BET | 6,723 |
| GAMBLING | 1,410 |
| EXCHANGE | 794 |
| MINING | 724 |
| PONZI | 587 |
| RANSOMWARE | 234 |
| FAUCET | 125 |
| MARKETPLACE | 115 |
| MIXER | 80 |
| BRIDGE | 70 |

### 2.2 旧 `data.pt` 的问题

旧数据集来自 TopK / Z-score 活跃实体采样，原本只有：

```text
350,258 nodes
17,173,503 edges
2,961 labeled nodes
5 supervised classes
```

旧数据集丢掉了 6 类：

```text
MINING
PONZI
RANSOMWARE
FAUCET
MARKETPLACE
MIXER
```

其中 `PONZI / RANSOMWARE / MIXER / MARKETPLACE` 对 AML/风险识别非常关键。

因此，旧 `data.pt` 不能再作为最终主数据集，只能作为：

```text
Protocol A: current_topk_baseline
```

它的论文价值是：

> 作为采样偏差对照组，证明活动强度驱动的 TopK 子图会严重改变原始标签空间。

---

## 3. 新数据协议已经完成的结果

目前已成功构建三个协议数据集。

运行过的命令：

```powershell
python scripts/build_protocol_dataset.py --config configs/data/label_preserving.yaml
python scripts/build_protocol_dataset.py --config configs/data/class_balanced_khop.yaml
python scripts/build_protocol_dataset.py --config configs/data/temporal_balanced.yaml
python scripts/compare_protocols.py --data-dir data/processed/protocols
```

### 3.1 协议对比结果

| dataset | nodes | edges | labeled | label_space | covered_classes |
|---|---:|---:|---:|---:|---:|
| label_preserving | 184,098 | 156,586 | 34,098 | 11 | 11 |
| class_balanced_khop | 242,226 | 1,237,757 | 34,098 | 11 | 11 |
| temporal_balanced | 242,352 | 1,239,058 | 34,098 | 11 | 11 |

三个协议都完整保留了 34,098 个有标签节点和 11 类标签空间。

### 3.2 三个协议的定位

#### Protocol B：label_preserving

结果：

```text
nodes: 184,098
edges: 156,586
labeled: 34,098
```

定位：

```text
标签保持验证协议 / 采样偏差对照组
```

特点：

- 保留全部 11 类标签；
- 图结构较稀疏；
- 不适合作为最终主训练图；
- 适合放在论文里证明“只要改采样协议，原始标签空间就能保住”。

#### Protocol C：class_balanced_khop

结果：

```text
nodes: 242,226
edges: 1,237,757
labeled: 34,098
```

定位：

```text
第一主训练数据集
```

特点：

- 保留全部 11 类标签；
- 相比 `label_preserving`，边数从 15.6 万提升到 123.8 万；
- 图结构上下文更丰富；
- 节点和边规模仍然可控；
- 没有发生超级节点爆炸；
- 适合第一轮 MLP vs GraphSAGE baseline 实验。

#### Protocol D：temporal_balanced

结果：

```text
nodes: 242,352
edges: 1,239,058
labeled: 34,098
```

定位：

```text
classwise temporal 泛化实验数据集
```

已补充 `split temporal summary` 后确认：

```text
temporal_balanced 确实是 classwise temporal split，不是 random split。
```

关键证据：

```text
split | count | time_min | time_p25 | time_median | time_mean | time_p75 | time_max
train | 20458 | 0        | 358192   | 388116      | 371668    | 400652   | 699636
val   | 6820  | 327868   | 417240   | 446573      | 451329    | 477165   | 699817
test  | 6820  | 404706   | 504507   | 562131      | 565289    | 654524   | 700000
```

整体上：

```text
train 更早
val 居中
test 更晚
```

示例类别：

```text
PONZI:
train median 355422
val   median 403802
test  median 470683

RANSOMWARE:
train median 446874
val   median 542101
test  median 560279
```

BRIDGE 只有 70 个样本且时间高度集中，所以 val/test 存在大量相同时间点，这是数据本身的问题，不是 split 逻辑错误。

---

## 4. 当前标签体系和训练逻辑

### 4.1 新标签编码

新协议数据集统一使用：

```text
-1 = UNLABELED / 背景节点
0  = INDIVIDUAL
1  = BET
2  = GAMBLING
3  = EXCHANGE
4  = MINING
5  = PONZI
6  = RANSOMWARE
7  = FAUCET
8  = MARKETPLACE
9  = MIXER
10 = BRIDGE
```

### 4.2 训练代码必须遵守

错误旧逻辑：

```python
y != 0
ignore_index = 0
label > 0
num_classes = 10
```

正确新逻辑：

```python
supervised_mask = data.y >= 0
loss = F.cross_entropy(logits[mask], data.y[mask], ignore_index=-1)
num_classes = 11
```

尤其需要关注：

```text
trainer.py
evaluator.py
metrics.py
losses.py
run_benchmark.py
```

---

## 5. 当前代码线状态

### 5.1 当前最新代码包

最新交付代码包：

```text
Bitcoin_Transaction_Identification_research_v2_2.zip
```

它是在用户当前代码基础上继续推进的 v2.2 工程版。

### 5.2 v2.2 主要改动

#### 1. 修正训练标签逻辑

统一支持：

```text
-1 = UNLABELED
0~10 = 11 supervised classes
```

重点文件：

```text
src/btcaml/training/trainer.py
src/btcaml/training/losses.py
src/btcaml/evaluation/metrics.py
scripts/run_benchmark.py
```

旧兼容目录也同步加了 ignore_index 逻辑：

```text
training/trainer.py
training/evaluator.py
```

目的：避免新旧入口混用时把 `INDIVIDUAL=0` 当成未标注。

#### 2. 改进大规模数据处理性能

修复 PyTorch warning：

```text
Creating a tensor from a list of numpy.ndarrays is extremely slow
```

边张量构造改为：

```text
numpy.vstack -> torch.from_numpy
```

相关文件：

```text
src/btcaml/data/build_graph.py
```

#### 3. 改善命令行体验

对长时间步骤加了明确提示，例如：

```text
Streaming edges from DB (slowest step; first chunk can take several minutes)
```

避免用户不知道程序是卡住还是正在运行。

#### 4. 修复环境变量占位符问题

`BITCOIN_DB_URL` 的 `${...}` 占位符现在在数据库连接层也能兜底解析。

相关文件：

```text
src/btcaml/data/db.py
```

#### 5. 移除真实数据库密码

旧配置中的真实数据库连接串应避免提交。

保留：

```text
.env.example
```

真实凭据放本地 `.env`，不要进 git。

#### 6. 加入日志和结果归档

重要任务输出保存到：

```text
experiments/runs/时间戳_任务名/
```

同时最近一次结果保存到：

```text
experiments/latest/
```

涉及脚本：

```text
scripts/audit_raw_labels.py
scripts/build_protocol_dataset.py
scripts/compare_protocols.py
scripts/inspect_protocol_dataset.py
scripts/run_benchmark.py
```

#### 7. 增强 benchmark 入口

支持直接命令行跑 smoke test 和 baseline。

示例：

```powershell
python scripts/run_benchmark.py --data data/processed/protocols/class_balanced_khop.pt --models mlp --smoke --device cpu
```

正式第一轮：

```powershell
python scripts/run_benchmark.py --data data/processed/protocols/class_balanced_khop.pt --models mlp sage --device cpu --run-name cbk_mlp_sage
```

temporal 泛化：

```powershell
python scripts/run_benchmark.py --data data/processed/protocols/temporal_balanced.pt --models mlp sage --device cpu --run-name temporal_mlp_sage
```

结果保存：

```text
experiments/runs/xxxx_benchmark_xxx/results.csv
experiments/runs/xxxx_benchmark_xxx/results.md
experiments/latest/benchmark/results.csv
```

#### 8. 新增运行说明文档

新增：

```text
docs/OPERATION_RUNBOOK.md
```

记录项目当前正确运行顺序。

---

## 6. 当前本地运行情况

### 6.1 已经成功运行

```powershell
python scripts/audit_raw_labels.py --config configs/data/raw_db.yaml
python scripts/build_protocol_dataset.py --config configs/data/label_preserving.yaml
python scripts/build_protocol_dataset.py --config configs/data/class_balanced_khop.yaml
python scripts/build_protocol_dataset.py --config configs/data/temporal_balanced.yaml
python scripts/compare_protocols.py --data-dir data/processed/protocols
```

### 6.2 数据构建耗时参考

`class_balanced_khop`：

```text
nodes: 242,226
edges: 1,237,757
labeled: 34,098
elapsed: 738.0s / 12.3min
```

`temporal_balanced`：

```text
nodes: 242,352
edges: 1,239,058
labeled: 34,098
elapsed: 674.5s / 11.2min
```

### 6.3 已验证 inspect

用户已补充并运行：

```powershell
python -m compileall scripts\inspect_protocol_dataset.py
conda run -n MCM python scripts\inspect_protocol_dataset.py --path data\processed\protocols\temporal_balanced.pt
```

确认 `temporal_balanced` 是 classwise temporal split。

---

## 7. 论文线当前可写内容

### 7.1 已经能写进论文的发现

当前已经有一条非常强的论文主线：

> 原始数据库包含 34,098 个有标签实体，覆盖 11 类比特币实体。旧 TopK 子图只保留 2,961 个标签并丢失 6 个类别。本文提出 label-preserving、class-balanced-khop 和 temporal-balanced 三种采样协议，均完整保留 11 类标签空间。其中 class-balanced-khop 在保持全部标签的同时，将边数从 156,586 提升到 1,237,757，显著增强图结构上下文；temporal-balanced 进一步提供 classwise temporal 泛化评估。

### 7.2 论文贡献建议

当前论文贡献可以写成：

1. **采样偏差发现**  
   发现活动强度驱动的 TopK 子图构建会显著扭曲原始标签空间，导致多个 AML 关键类别完全丢失。

2. **标签保持数据协议**  
   提出 label-preserving / class-balanced-khop / temporal-balanced 三类协议，在控制图规模的同时完整保留 11 类监督标签。

3. **长尾 11 类实体识别基准**  
   将任务从旧的 5 类子图分类升级为完整 11 类长尾比特币实体识别。

4. **时间泛化评估**  
   构建 classwise temporal split，验证模型从早期实体泛化到后期实体的能力。

5. **边-时序-方向图学习模型**  
   后续实现 ETD-SAGE，利用交易金额、频率、持续时间、最近性以及入/出方向结构提升长尾类别识别。

### 7.3 论文中要避免的说法

不要说：

```text
EXCHANGE 是非法类别
NONE 是正常类别
旧 data.pt 是完整原始数据的随机子图
当前任务只是 5 类分类
```

建议说：

```text
UNLABELED 是背景上下文节点，不作为监督类别
EXCHANGE 是服务型实体，不默认等同于非法风险
PONZI / RANSOMWARE / MIXER / MARKETPLACE 是 AML 敏感类别
旧 data.pt 是 activity-biased sampled subgraph
```

---

## 8. 代码线下一步任务

### 8.1 立即下一步：安装 v2.2 后先做测试

解压覆盖 v2.2 后：

```powershell
python -m pytest -q
```

如果通过，再跑 smoke test：

```powershell
python scripts/run_benchmark.py --data data/processed/protocols/class_balanced_khop.pt --models mlp --smoke --device cpu
```

### 8.2 第一轮正式 baseline

先只跑两个模型：

```text
MLP
GraphSAGE
```

#### class_balanced_khop

```powershell
python scripts/run_benchmark.py --data data/processed/protocols/class_balanced_khop.pt --models mlp sage --device cpu --run-name cbk_mlp_sage
```

#### label_preserving

```powershell
python scripts/run_benchmark.py --data data/processed/protocols/label_preserving.pt --models mlp sage --device cpu --run-name lp_mlp_sage
```

#### temporal_balanced

```powershell
python scripts/run_benchmark.py --data data/processed/protocols/temporal_balanced.pt --models mlp sage --device cpu --run-name temporal_mlp_sage
```

### 8.3 第一轮实验要回答的问题

1. 新 11 类任务下，MLP 是否仍然很强？
2. GraphSAGE 是否明显利用到了图结构？
3. `class_balanced_khop` 是否优于 `label_preserving`？
4. `temporal_balanced` 是否明显更难？
5. 小类 `PONZI / RANSOMWARE / MIXER / BRIDGE` 的 F1 / recall 是否可用？

### 8.4 后续模型推进顺序

不要一开始跑一堆模型。推荐顺序：

```text
Stage 1: MLP vs GraphSAGE
Stage 2: GCN / GAT / APPNP / ResGraphSAGE 补充基线
Stage 3: Edge-aware model
Stage 4: ETD-SAGE
Stage 5: ablation：无 edge_attr / 无 temporal / 无 direction / 无 class-balanced protocol
```

---

## 9. 需要特别注意的代码同步问题

用户特别强调：各个文件必须同步更新，不能一个入口改了另一个入口没改。

重点同步点：

### 9.1 标签逻辑同步

所有训练、评估、损失、指标、可视化都必须统一：

```text
-1 ignored
0~10 supervised
num_classes=11
```

需要同步检查：

```text
src/btcaml/training/trainer.py
src/btcaml/training/losses.py
src/btcaml/evaluation/metrics.py
scripts/run_benchmark.py
training/trainer.py
training/evaluator.py
interface/*
```

### 9.2 标签名称同步

所有报告、confusion matrix、per-class metrics、GUI 显示都必须使用：

```text
INDIVIDUAL
BET
GAMBLING
EXCHANGE
MINING
PONZI
RANSOMWARE
FAUCET
MARKETPLACE
MIXER
BRIDGE
```

不要再用旧 5 类 label map。

### 9.3 数据路径同步

当前主协议路径：

```text
data/processed/protocols/class_balanced_khop.pt
data/processed/protocols/label_preserving.pt
data/processed/protocols/temporal_balanced.pt
```

旧数据：

```text
data/processed/data.pt
```

只作为 old/topk baseline。

### 9.4 配置同步

重点配置：

```text
configs/data/raw_db.yaml
configs/data/label_preserving.yaml
configs/data/class_balanced_khop.yaml
configs/data/temporal_balanced.yaml
```

`temporal_balanced.yaml` 已加入大库采样参数：

```text
max_neighbors_per_seed
seed_batch_size
seed_degree_cap
query_timeout_ms
```

### 9.5 日志同步

所有重要脚本应同时输出：

```text
控制台简洁摘要
experiments/runs/时间戳_任务名/
experiments/latest/任务名/
```

不要只打印到命令行，避免结果丢失。

---

## 10. 大规模数据处理经验教训

### 10.1 不能一次性扫全表

原始库：

```text
252M nodes
786M edges
```

不能用 naive 全表加载。

需要：

```text
利用数据库已有索引
按 selected node set 查询
分块 streaming edges
限制 supernode
邻居扩展加 cap
长步骤加进度条
```

### 10.2 必须有友好进度提示

之前问题：

```text
程序长时间无输出，用户不知道是卡住还是运行中
```

后续所有耗时任务都应具备：

```text
步骤编号
当前阶段说明
tqdm 进度条
已处理 chunk 数
已收集边数/节点数
预计慢步骤提醒
```

示例输出风格：

```text
[5/7] Streaming edges from DB (slowest step; first chunk can take several minutes) ...
edges: 7 chunks [08:49, 75.63s/chunk, edges=1,237,757]
```

### 10.3 输出要简洁但可追踪

命令行只输出必要信息：

```text
protocol
nodes
edges
labeled
elapsed
output path
```

详细结果保存到 markdown/csv/json。

---

## 11. 当前最重要的下一步

### 第一步：确认 v2.2 代码覆盖成功

```powershell
python -m pytest -q
```

### 第二步：跑 smoke test

```powershell
python scripts/run_benchmark.py --data data/processed/protocols/class_balanced_khop.pt --models mlp --smoke --device cpu
```

### 第三步：把 smoke test 输出发给新对话

新对话应优先检查：

```text
num_classes 是否为 11
ignore_index 是否为 -1
train/val/test 是否只覆盖 34,098 supervised nodes
metrics 是否排除了 -1
INDIVIDUAL=0 是否参与训练和评估
```

### 第四步：跑第一轮 baseline

```powershell
python scripts/run_benchmark.py --data data/processed/protocols/class_balanced_khop.pt --models mlp sage --device cpu --run-name cbk_mlp_sage
```

---

## 12. 当前状态一句话总结

项目目前已经完成从旧 5 类 TopK 子图向新 11 类标签保持数据协议的关键转向：

```text
旧路线：在旧 data.pt 上堆 GNN，解释力弱，标签空间不完整。
新路线：先揭示 TopK 采样偏差，再构建标签保持与时间泛化协议，最后在完整 11 类长尾任务上比较 MLP、GraphSAGE 和 ETD-SAGE。
```

当前最紧迫任务：

```text
进入模型实验前，确保 v2.2 训练代码完全遵守 -1 ignored / 0~10 supervised / num_classes=11 的新标签逻辑。
```
