# 比特币交易图风险实体识别：研究级项目路线与论文推进方案 v2

> 面向目标：从当前“大创/课程项目式 GNN 模型对比”，升级为一条以**高质量学术论文**为最终目标的研究路线。  
> v2 版本在上一版基础上加入 Codex 对原始数据库与 `data.pt` 的 EDA 新发现，尤其是：**当前 TopK 子图严重改变原始标签空间，原始 11 类标签中有 6 类在当前子图中完全丢失**。  
> 这意味着项目主线应从“在现有 `data.pt` 上优化 GNN”升级为：
>
> **采样偏差发现 + 标签保持数据协议 + 边时序方向感知模型 + 11 类实体识别 + 敏感实体排序 + 可解释分析。**

---

## 0. 本文档和配套文档

本文档给你本人阅读，强调：

- 最终研究判断；
- 论文主线；
- 研究问题；
- 数据与任务重新定义；
- 阶段规划；
- 技术路线；
- 可探索分支；
- 科研工具链；
- 高质量论文产出策略。

配套工程执行文档：

```text
BTC_AML_Codex_Refactor_Spec_v2.md
```

那份给 Codex / 代码代理看，负责把本路线落成代码。

---

## 1. 上下文来源回顾：本方案继承了哪些已有结论

这份方案不是从零开始，而是融合了我们整个对话中的材料。

### 1.1 深度研究报告一：方向地图

第一份深度研究报告回答的是：

> 这个项目能变成什么？

核心结论：

1. 不能停留在“跑几个 GNN 模型做分数对比”。
2. 比特币交易图风险识别真正难点是：
   - 标注稀缺；
   - 类别长尾；
   - 图有向；
   - 边属性重要；
   - 时间语义重要；
   - 普通邻居聚合可能被超级节点稀释；
   - 存在异配/非同质邻居问题；
   - 金融合规场景需要可解释性。
3. 候选研究方向包括：
   - 边属性增强 GNN；
   - 时间感知图学习；
   - 长尾类别优化；
   - 异配/方向感知消息传递；
   - 主动学习与标签传播；
   - 自监督/对比学习；
   - 子图级 AML；
   - 可解释风险子图。

### 1.2 深度研究报告二：路线收敛

第二份深度研究报告回答的是：

> 在你的代码、数据、时间和目标约束下，最推荐走哪条路线？

它收敛出的主线是：

> **边属性 + 时间语义 + 长尾类别 + 异配/方向感知 + 可解释分析。**

关键判断：

1. 不建议继续堆普通 GNN。
2. 不建议一开始就做完整 TGN、复杂 active learning、复杂对比学习。
3. MLP 反超 GNN 不是失败，而是论文动机：
   > 普通 GNN 在比特币实体图中并不天然有效，只有显式建模边交易语义、时间、方向和长尾问题时，图模型才可能发挥优势。
4. 最稳路线是：
   - 先解决数据协议与边特征；
   - 再做方向/异配；
   - 再做长尾优化；
   - 最后做解释性和可视化。

### 1.3 代码审查结论

你的原始工程已经不是玩具项目，有较完整的：

- 数据预处理；
- PyG `Data` 构建；
- MLP / GCN / GAT / GraphSAGE / ResGraphSAGE / APPNP；
- Trainer；
- W&B；
- checkpoint；
- mini-batch 训练；
- GUI 雏形。

但关键问题也明显：

1. `edge_attr` 保存了但基本没用；
2. `NONE` 是未标注节点，不应当作为正常类；
3. 当前 `data.pt` 只有 5 个监督类别；
4. 训练/验证/测试是随机划分，不符合真实“用过去预测未来”；
5. 金额特征极端长尾，不能简单 Z-score；
6. MLP Macro-F1 高于 GraphSAGE，说明普通消息传递可能有问题；
7. BRIDGE 单类邻居增强可能导致类别偏置；
8. GUI 还不是完整可用系统；
9. 还缺多 seed、消融、协议对比和论文表格自动导出。

### 1.4 Codex 重构方案给出的启发

Codex 提出了工程层面的具体规划：

- 统一 `BaseModel.forward(x, edge_index, edge_attr=None, **kwargs)`；
- 新增 `EdgeMLPEncoder`、`TemporalEncoder`；
- 新增 `EdgeAwareGraphSAGE`、`HeteroGraphSAGE`、`MultiTaskSAGE`；
- 加 PR-AUC、Recall@Top-K、per-class report；
- 加 `run_benchmark.py`；
- 加 losses 模块；
- 加 GUI Top-K 风险展示。

这些有价值，但需要排序：

- 立刻吸收：接口统一、边编码、评估增强、benchmark、Top-K；
- 延后执行：MultiTaskSAGE、SupConLoss、完整 HeteroGraphSAGE；
- 必须修正：风险头不能默认把 `EXCHANGE` 当高风险。

### 1.5 Gemini 调研结果给出的启发

Gemini 更偏前沿论文想象力，强调：

- 子图级 AML；
- 超级节点特征稀释；
- 子图对比学习；
- 图小波 / 多尺度信号分解；
- 可解释资金链；
- PONZI / RANSOMWARE / MIXER 等强 AML 类别的局部拓扑模式。

它的启发是：

> 长远看，单节点分类不是终点。高水平方向可能是“种子节点中心的风险子图识别”或“多尺度资金流模式识别”。

但不建议第一阶段直接做完整“小波 + 子图对比学习”。它更适合作为第二篇论文或后续增强分支。

### 1.6 千问调研结果给出的启发

千问给出更综述式的领域图谱：

- Elliptic；
- Elliptic++；
- Elliptic2；
- BitcoinHeist；
- 自监督学习；
- 半监督学习；
- 动态图；
- 跨数据集迁移；
- 隐私技术干扰；
- 可解释性与监管需求。

它的启发是：

> 这篇论文不要只是单数据集单模型，而应该围绕“低标签、大规模、动态、有向、边属性丰富、类别长尾、采样偏差”建立研究问题。

### 1.7 新增 EDA 结果带来的重大调整

Codex 最近对原始数据库和 `data.pt` 做了 EDA，结果非常重要。

#### 1.7.1 原始数据库规模

原始数据库：

| 对象 | 规模 |
|---|---:|
| 原始节点 | 约 252,148,848 |
| 原始边 | 约 785,934,144 |
| `node_features` 磁盘 | 37 GB |
| `transaction_edges` 磁盘 | 80 GB |

当前 `data.pt`：

| 对象 | 规模 |
|---|---:|
| 子图节点 | 350,258 |
| 子图边 | 17,173,503 |
| 有标签节点 | 2,961 |
| 标签比例 | 0.845% |
| 子图节点占原始库 | 约 0.14% |

#### 1.7.2 原始库有 11 类，而当前子图只保留了 5 个监督类别

这是最重要的新发现。

原始数据库 11 类：

| 类别 | 原始数量 | 当前 data.pt 数量 | 保留情况 |
|---|---:|---:|---|
| INDIVIDUAL | 23,236 | 2,421 | 部分保留 |
| BET | 6,723 | 96 | 严重丢失 |
| GAMBLING | 1,410 | 179 | 部分保留 |
| EXCHANGE | 794 | 195 | 部分保留 |
| MINING | 724 | 0 | 完全丢失 |
| PONZI | 587 | 0 | 完全丢失 |
| RANSOMWARE | 234 | 0 | 完全丢失 |
| FAUCET | 125 | 0 | 完全丢失 |
| MARKETPLACE | 115 | 0 | 完全丢失 |
| MIXER | 80 | 0 | 完全丢失 |
| BRIDGE | 70 | 70 | 完全保留 |

这意味着当前 `data.pt` 不是原始数据集的中性代表，而是一个**强采样偏置子图**。

#### 1.7.3 EDA 对研究路线的影响

此前我们说：

> 当前 TopK-ZScore 可能有采样偏差。

现在可以升级为：

> 当前 TopK-ZScore 已经显著扭曲原始标签空间，使 11 类实体任务退化成 5 类任务，并丢失 PONZI、RANSOMWARE、MIXER 等 AML 关键类别。

这会直接改变论文主线：

- 当前 `data.pt` 不再作为最终主数据；
- 当前 `data.pt` 降级为 Protocol A baseline；
- 最终主实验应重新从原始数据库构建 label-preserving 子图；
- 任务从 5 类升级为 11 类；
- 增加 sensitive entity ranking。

---

## 2. 最终研究定位 v2

### 2.1 不推荐的旧题目

不建议继续使用：

> 基于图神经网络的比特币非法交易识别

问题：

1. 太泛；
2. “非法”定义不清；
3. `INDIVIDUAL`、`EXCHANGE`、`MINING` 不等于非法；
4. `NONE` 不是正常类；
5. 体现不出 EDA 新发现；
6. 体现不出数据协议贡献。

### 2.2 推荐中文题目

更推荐：

> **面向长尾比特币实体风险识别的采样感知边时序方向图学习方法研究**

或者更论文味：

> **采样偏差下低标签比特币实体图的边时序方向感知风险识别研究**

### 2.3 推荐英文题目

首选：

> **Sampling-Aware Edge-Temporal Directional Graph Learning for Long-Tailed Bitcoin Entity Risk Identification**

更有研究问题感的版本：

> **When Do Graph Neural Networks Help in Bitcoin Entity Risk Identification? A Study of Sampling Bias, Edge Semantics, and Directional Message Passing**

如果目标是更像顶会论文，我最推荐第二个，因为它不是单纯介绍方法名，而是提出一个研究问题。

---

## 3. 核心研究问题 v2

### RQ1：采样策略是否会改变比特币实体识别任务本身？

问题：

> 从 2.52 亿节点原始图抽取 35 万节点子图时，TopK-ZScore 是否会改变标签空间、类别分布和时间分布？

要证明：

- 当前 TopK 子图只保留了 5/11 个监督类别；
- BET 保留率极低；
- PONZI、RANSOMWARE、MIXER 等 AML 关键类完全丢失；
- 因此当前 `data.pt` 只能作为 activity-biased baseline，不应作为最终主数据。

### RQ2：标签保持与类别均衡子图协议能否提升模型可信度？

问题：

> 如果强制保留全部 11 类标签节点，并进行类别均衡邻域扩展，模型表现、少数类表现和时间泛化是否更可靠？

要做：

- Label-preserving sampling；
- Class-balanced k-hop；
- Supernode degree cap；
- Temporal coverage control；
- Protocol comparison。

### RQ3：为什么普通 GNN 在当前子图上不一定优于 MLP？

问题：

> 普通邻居聚合是否受到边语义缺失、方向混淆、异配邻居、超级节点稀释、标签长尾的影响？

要做：

- MLP vs GNN under different protocols；
- Homophily / heterophily analysis；
- Neighbor label distribution；
- Degree distribution；
- Supernode exposure analysis。

### RQ4：边时序方向建模是否能让图结构真正发挥作用？

问题：

> 加入交易金额、交易频率、时间近期性，并分别聚合入边和出边邻居后，是否能提升 11 类实体识别和敏感实体 Top-K 排序？

要做：

- Edge feature engineering；
- Temporal features；
- Directional in/out aggregation；
- ETD-GNN；
- Ablation。

### RQ5：哪些风险实体更适合节点分类，哪些更适合子图建模？

新 EDA 发现原始库中存在 PONZI / RANSOMWARE / MIXER，这些更像资金路径模式，不一定适合单节点分类。

这可以作为后续分支：

> 对 PONZI / RANSOMWARE / MIXER 做 seed-centered suspicious subgraph mining。

---

## 4. 论文主贡献设计 v2

### Contribution 1：采样偏差发现

揭示当前 TopK 子图构建会显著扭曲原始标签空间。

可以写成：

> We show that activity-biased TopK subgraph sampling can substantially distort the original Bitcoin entity label space, eliminating multiple AML-relevant classes such as Ponzi, ransomware, marketplace, faucet, mining, and mixer entities.

中文表达：

> 本文首先通过系统性 EDA 发现，现有 TopK 子图构建策略会显著改变原始比特币实体图的标签空间，使 11 类实体识别任务退化为 5 类任务，并完全丢失多个 AML 关键类别。

### Contribution 2：Label-Preserving Data Protocol

提出标签保持、类别均衡、时间感知的数据协议。

协议包括：

| Protocol | 名称 | 作用 |
|---|---|---|
| A | Original TopK-ZScore | 复现/负面对照 |
| B | Label-Preserving | 强制保留全部 11 类有标签节点 |
| C | Class-Balanced Label-Preserving k-hop | 缓解长尾和邻域上下文不公平 |
| D | Temporal Label-Preserving | 面向未来预测和时间泛化 |

### Contribution 3：11 类实体识别 + 敏感实体排序

主任务从 5 类升级为 11 类。

11 类：

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

辅助任务：

> Sensitive Entity Ranking

风险组不作法律意义上的非法定义，而作研究中的敏感排序定义。

建议分组：

| 组别 | 类别 |
|---|---|
| High-sensitive | PONZI, RANSOMWARE, MIXER |
| Medium-sensitive | BET, GAMBLING, MARKETPLACE, BRIDGE |
| Neutral / service / context | INDIVIDUAL, EXCHANGE, MINING, FAUCET |

注意：`EXCHANGE` 不默认当高风险。

### Contribution 4：ETD-GNN

提出边时序方向感知模型。

核心：

```text
自身通道 + 入边门控聚合 + 出边门控聚合 + 边时间语义
```

模型直觉：

- 资金流入和流出语义不同；
- 大额、高频、近期边更重要；
- 普通 GraphSAGE 把邻居混合，会丢失资金流方向；
- 方向感知能缓解异配和特征稀释。

### Contribution 5：机制分析与可解释案例

包括：

- Sampling bias study；
- Homophily / heterophily；
- Supernode dilution；
- Edge gate 权重解释；
- Top-K sensitive entity case study；
- PONZI / RANSOMWARE / MIXER 子图后续分析。

---

## 5. 数据层研究设计 v2

### 5.1 当前 `data.pt` 的新定位

当前 `data.pt` 不再是最终主数据。

它的新定位：

```text
Protocol A: Activity-biased TopK baseline
```

用途：

1. 复现已有结果；
2. 展示 TopK 采样偏差；
3. 作为负面对照；
4. 说明为什么必须重新构建数据协议。

### 5.2 新主数据：从原始数据库重新构建

最终主实验应基于：

```text
Protocol C / D: Label-preserving class-balanced temporal subgraph
```

目标：

- 保留全部 11 类有标签节点；
- 对每类统一扩展邻域；
- 控制超级节点；
- 控制时间覆盖；
- 保持可训练规模；
- 支持 random / temporal / class-wise temporal split。

### 5.3 采样协议细节

#### Protocol A：Original TopK-ZScore

复现当前方法：

```text
FinalScore = 0.3*Z(degree)
           + 0.2*Z(total_in)
           + 0.2*Z(total_out)
           + 0.3*Z(cluster_size)
```

问题：

- 偏高活跃实体；
- 丢失 6 个类别；
- BET 保留率极低；
- BRIDGE 因特殊增强被全部保留。

#### Protocol B：Label-Preserving

原则：

```text
1. selected = all labeled nodes from 11 classes
2. Add sampled context nodes
3. Build induced subgraph
4. Keep budget comparable to Protocol A
```

#### Protocol C：Class-Balanced k-hop

原则：

```text
1. 每个类别强制保留全部有标签节点；
2. 每类按 k-hop 扩展邻居；
3. 每类邻居预算相近；
4. 防止 INDIVIDUAL/EXCHANGE 吞没图；
5. 对超级节点设置 degree cap；
6. 保留一部分高 PageRank / 高交易量背景节点。
```

#### Protocol D：Temporal Label-Preserving

原则：

```text
1. 保留全部 11 类标签节点；
2. 按时间构建 train/val/test；
3. 控制未来边泄漏；
4. 保证每类在训练集中有最低样本数；
5. 必要时同时报告 global temporal 和 class-wise temporal。
```

### 5.4 时间划分要做两个版本

EDA 发现类别出现时间差异明显：例如 BRIDGE 出现很晚，MINING 更早，BET 活跃期非常短。因此不能只做一个简单 temporal split。

建议：

| 划分方式 | 含义 | 优点 | 缺点 |
|---|---|---|---|
| Random Split | 分层随机 | 方便对比 | 不真实，可能高估 |
| Class-wise Temporal Split | 每类内部按时间 60/20/20 | 每类 train/val/test 都有样本 | 部署真实性稍弱 |
| Global Temporal Split | 全体标签按时间 60/20/20 | 最接近真实未来预测 | 可能部分类别训练集缺失 |
| Leakage-Control Temporal Graph | 图边也按 cutoff 过滤 | 最严格 | 工程最难 |

最终论文可以将 Class-wise Temporal 作为主模型能力评估，将 Global Temporal 作为真实部署压力测试。

### 5.5 特征工程

金额类不能直接 Z-score。必须：

```text
log1p -> clip/winsorize -> train-only robust scaling
```

边特征扩展：

```text
log_total_sent
log_min_sent
log_max_sent
amount_range = log1p(max_sent - min_sent)
avg_sent = total_sent / total
duration = last_seen - reveal + 1
tx_frequency = total / duration
edge_recency = global_max_block - last_seen
```

节点特征扩展：

```text
log_total_sent / log_total_received
active_span_in = last_transaction_in - first_transaction_in
active_span_out = last_transaction_out - first_transaction_out
node_recency_in/out
in_out_degree_ratio
in_out_amount_ratio
```

---

## 6. 模型主线：ETD-GNN v2

### 6.1 为什么仍然需要 ETD-GNN

EDA 新结果没有推翻 ETD-GNN，反而加强了它：

- 边有 `reveal` / `last_seen`；
- 边有交易次数和金额；
- 资金流有方向；
- 金额极端长尾；
- 图中存在极强异配现象；
- MLP 反超普通 GNN；
- 当前图邻域中绝大多数邻居是 `NONE`。

所以模型仍应围绕：

```text
Edge-aware + Temporal-aware + Direction-aware + Long-tail-aware
```

### 6.2 模型结构

ETD-GNN：

```text
x_i: node features
edge_attr_ij: transaction semantics
edge_time_ij: reveal / last_seen / recency / duration
edge_index: directed fund flow
```

每层：

```text
h_self = W_self h_i

h_in  = Aggregate_{j -> i} gate_in(e_ji, t_ji)  * W_in h_j
h_out = Aggregate_{i -> k} gate_out(e_ik, t_ik) * W_out h_k

h_i' = MLP([h_self || h_in || h_out])
```

门控：

```text
gate(e, t) = sigmoid(MLP([edge_amount_features || edge_time_features]))
```

### 6.3 与 Codex 原方案的关系

保留：

- `EdgeMLPEncoder`；
- `TemporalEncoder`；
- `BaseModel` 新接口；
- `Top-K Recall`；
- `PR-AUC`；
- `run_benchmark.py`。

修改：

- `HeteroGraphSAGE` 暂时后置；
- `MultiTaskSAGE` 后置；
- `SupConLoss` 后置；
- 风险头不默认把 `EXCHANGE` 当正类；
- 先做 11 类实体识别，再做 sensitive ranking。

---

## 7. 实验设计 v2

### 7.1 Sampling Bias Study

这是 v2 新增核心实验。

| Protocol | Nodes | Edges | #Classes kept | #Labels kept | BET retained | AML classes retained | Notes |
|---|---:|---:|---:|---:|---:|---:|---|
| TopK-ZScore | 350K | 17M | 5/11 | 2,961 | 1.4% | Low | current data.pt |
| Label-Preserving | TBD | TBD | 11/11 | all | 100% | 100% | new |
| Balanced-khop | TBD | TBD | 11/11 | all | 100% | 100% | main |
| Temporal-balanced | TBD | TBD | 11/11 | all | 100% | 100% | final |

论文意义：

> 证明“如何从超大规模链上图中构建可训练子图”本身就是影响 AML 研究结论的关键变量。

### 7.2 Baseline 实验

模型：

```text
MLP
XGBoost
LightGBM
GCN
GAT
APPNP
GraphSAGE
ResGraphSAGE
EdgeTransformer
ETD-GNN
```

协议：

```text
Protocol A / B / C / D
```

划分：

```text
Random
Class-wise Temporal
Global Temporal
```

### 7.3 主要指标

不要只看 Weighted-F1。

必须有：

```text
Macro-F1
Weighted-F1
Per-class F1 / Precision / Recall
Minority Macro-F1
Sensitive Macro-F1
AUPRC
Recall@Top-K
Yield@Budget
```

建议定义：

```text
Sensitive Macro-F1 = mean(F1_PONZI, F1_RANSOMWARE, F1_MIXER, F1_BET, F1_GAMBLING)
```

如果某些类样本极少，可以同时报告 high-sensitive 与 medium-sensitive。

### 7.4 消融实验

| Variant | 验证目的 |
|---|---|
| w/o label-preserving protocol | 采样协议贡献 |
| w/o balanced k-hop | 类别均衡贡献 |
| w/o temporal features | 时间语义贡献 |
| w/o edge features | 边语义贡献 |
| w/o direction split | 资金流方向贡献 |
| w/o degree cap | 超级节点控制贡献 |
| CE vs weighted CE vs focal | 长尾损失贡献 |

### 7.5 机制分析

必须包括：

```text
1. 标签保留率分析
2. 类别分布漂移分析
3. 时间分布漂移分析
4. homophily / heterophily
5. neighbor label distribution
6. supernode degree exposure
7. edge gate 权重分布
8. case study
```

---

## 8. 后续研究分支 v2

### Branch A：自监督预训练

适合解决：标签稀缺。

方向：

```text
DGI
GraphCL
BGRL
edge reconstruction
temporal order prediction
```

后置，不进第一版主线。

### Branch B：PONZI / RANSOMWARE / MIXER 子图级 AML

由于 EDA 新发现原始库包含这些 AML 关键类，后续可以聚焦：

```text
seed-centered suspicious subgraph mining
supernode-truncated subgraph encoder
subgraph contrastive learning
```

这条线可对接 Gemini 的子图、小波、多尺度方向。

### Branch C：跨数据集迁移

目标：

```text
Schnoering -> Elliptic++
Schnoering -> BitcoinHeist
Schnoering -> Elliptic2
```

难点：节点定义、标签定义、特征维度不一致。

### Branch D：动态图 / 流式检测

目标：

```text
snapshot construction
incremental inference
future generalization
```

需要更强工程资源，暂不作为第一篇主线。

### Branch E：解释性风控系统

适合大创答辩和论文 case study：

```text
Top-K sensitive entities
local transaction subgraph
key edge explanation
fund-flow path visualization
risk explanation text
```

---

## 9. 时间规划 v2

### Phase 0：冻结现状与 EDA 归档，1 周

产出：

```text
eda_report
current_data_protocol_A_manifest
baseline_results
W&B project
DVC pipeline skeleton
```

### Phase 1：原始数据库标签审计与协议构建，2–3 周

重点：

```text
raw label inventory
11-class label map
label-preserving sampler
balanced-khop sampler
temporal split builder
protocol comparison report
```

这是最关键阶段。

### Phase 2：Protocol A/B/C/D 基线实验，2 周

模型：

```text
MLP / XGBoost / LightGBM / GraphSAGE
```

目标：

> 证明数据协议对结果影响巨大。

### Phase 3：ETD-GNN，3–4 周

实现：

```text
EdgeTemporalEncoder
DirectionalEdgeGateConv
ETD-GNN
```

跑主结果。

### Phase 4：消融与多 seed，2–3 周

输出：

```text
ablation tables
multi-seed mean±std
paper figures
```

### Phase 5：解释与论文包装，2–3 周

输出：

```text
case studies
local subgraph visualization
paper draft
slides
```

---

## 10. 工具链建议

### W&B

用于记录：

```text
config
seed
git commit
dataset protocol
label map
risk group definition
model
metrics
confusion matrix
PR curve
Top-K recall
checkpoint artifact
```

### DVC

用于管理：

```text
raw audit outputs
protocol datasets
processed data.pt
metrics.json
paper tables
```

### Hydra / OmegaConf

管理组合实验：

```bash
python scripts/train.py data=balanced_khop model=etd_sage split=classwise_temporal loss=focal seed=42
```

### Optuna

用于超参搜索：

```text
hidden_dim
num_layers
dropout
lr
weight_decay
edge_encoder_dim
gate_dim
focal_gamma
class_weight_power
neighbor fanout
degree cap
sampling budget
```

### pytest / ruff / black

必须测试：

```text
label map 是否正确
11 类是否全部保留
split 无重叠
temporal split 时间顺序正确
edge_attr 和 edge_index 对齐
NONE 不参与监督 loss
metrics 正确
model forward shape 正确
```

---

## 11. 论文结构建议 v2

```text
1. Introduction
   - 普通 GNN 为什么未必有效
   - TopK 采样导致标签空间偏移
   - 边语义、时间、方向的重要性

2. Related Work
   - Bitcoin AML datasets
   - GNN for transaction graphs
   - Sampling bias in graph learning
   - Temporal and edge-attributed GNN
   - Long-tailed / low-label graph learning

3. Dataset Audit and Problem Definition
   - Raw DB
   - Current TopK subgraph
   - 11 classes vs 5 classes
   - Sensitive ranking definition

4. Sampling-Aware Data Protocols
   - Protocol A/B/C/D
   - Label-preserving sampling
   - Balanced k-hop
   - Temporal split

5. Method: ETD-GNN
   - Edge temporal encoder
   - Directional gated aggregation
   - Training objective

6. Experiments
   - Sampling bias study
   - Baseline comparison
   - Main results
   - Ablation
   - Multi seed

7. Analysis and Case Studies
   - Homophily
   - Supernode dilution
   - Gate explanation
   - Sensitive entity cases

8. Limitations and Future Work
   - Self-supervised branch
   - Subgraph AML
   - Cross-dataset transfer
   - Dynamic/streaming detection

9. Conclusion
```

---

## 12. 最终主线一句话

v2 之后，这个项目的最终主线是：

> 通过原始数据库 EDA 揭示当前 TopK 子图构建严重扭曲比特币实体图的标签空间，使 11 类任务退化为 5 类任务并丢失多个 AML 关键类别；据此提出标签保持、类别均衡、时间感知的数据协议，并在此基础上设计边时序方向感知 GNN，用于 11 类实体识别和敏感实体 Top-K 排序，最终通过采样协议消融、时间泛化实验、边/时间/方向消融和局部子图解释，形成一篇可复现、可分析、可扩展的高质量学术论文。

---

## 13. 当前最优先行动

下一步不要先写新模型。

最优先是：

```text
1. 审计原始数据库 11 类标签；
2. 固化 raw_label_inventory.csv；
3. 实现 label-preserving sampler；
4. 构建 Protocol B/C/D 数据集；
5. 做 Protocol A/B/C/D 对比报告；
6. 再进入 ETD-GNN。
```

这一步做完，项目才真正从“模型优化工程”升级为“论文级研究项目”。
