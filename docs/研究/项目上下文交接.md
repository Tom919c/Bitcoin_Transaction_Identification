# BTC AML / Bitcoin Transaction Identification 项目上下文迁移文档

> 用法：在本项目下新建对话时，把本文档或其中“新对话开场提示词”复制给 ChatGPT。本文档用于迁移项目背景、已有证据、代码状态、研究方向和下一步任务。  
> 注意：不要在新对话中粘贴真实数据库密码。数据库连接串统一用占位符表示。

---

## 0. 新对话开场提示词

你现在要继续协助我推进一个比特币交易/实体风险识别研究项目。请先完整阅读以下项目背景，不要急着重新规划方向，也不要把它当作普通课程设计。这个项目现在目标是做成一篇尽可能高质量的学术论文，而不是简单跑模型或做 GUI。

我的身份与偏好：我是电子科技大学计算机/网安方向本科生 zhx。希望你用中文回答，风格要务实、直接、研究导向。需要你能帮我做研究路线判断、代码调试、数据协议设计、实验规划、论文叙事和答辩准备。不要只给空泛建议。

项目主题：基于图神经网络的比特币实体识别 / AML 风险相关实体分析。已有原始数据库非常大：约 2.52 亿节点、7.86 亿边，节点表 `node_features`，边表 `transaction_edges`。当前重点已经从“在旧 data.pt 上比较 GNN 模型”转为“研究采样偏差、构建标签保持的数据协议，并做 11 类长尾实体识别 + 敏感实体排序”。

最重要的最新发现：原始数据库标签审计已经跑通，确认原始库有 11 类标签、34,098 个有标签实体；但旧的 `data.pt` 只有 2,961 个有标签节点、只保留 5 类，直接丢掉了 MINING、PONZI、RANSOMWARE、FAUCET、MARKETPLACE、MIXER 这 6 类。其中 PONZI / RANSOMWARE / MIXER / MARKETPLACE 对 AML/风险识别非常重要。因此旧 `data.pt` 不能再作为最终主数据集，只能作为 TopK 偏差 baseline / negative control。

原始标签计数如下：INDIVIDUAL 23,236；BET 6,723；GAMBLING 1,410；EXCHANGE 794；MINING 724；PONZI 587；RANSOMWARE 234；FAUCET 125；MARKETPLACE 115；MIXER 80；BRIDGE 70。原始图拓扑：median degree=3，p95=12，p99=38，但 max degree=23,804,263，说明超级节点非常严重，后续 k-hop 采样必须做 degree cap / neighbor cap。

现在正式研究主线应是：Sampling-Aware Edge-Temporal Directional Graph Learning for Long-Tailed Bitcoin Entity Risk Identification。中文可写成：面向长尾比特币实体风险识别的采样感知边时序方向图学习方法研究。

核心贡献应该围绕：
1. 采样偏差发现：证明旧 TopK/Z-score 子图改变了标签空间和类别分布；
2. 标签保持数据协议：从原始大图构建保留 11 类标签、受控规模、支持 temporal split 的训练子图；
3. 11 类实体识别：NONE/unlabeled 只作为上下文，不作为普通监督类别；
4. 敏感实体排序：高敏感可设 PONZI/RANSOMWARE/MIXER，中敏感可设 BET/GAMBLING/MARKETPLACE/BRIDGE，EXCHANGE 不应默认当作非法/高风险；
5. ETD-GNN / ETD-SAGE：利用边属性、时间属性和资金流方向，做 edge-temporal-directional message passing；
6. 长尾评估和真实划分：Macro-F1、Minority Macro-F1、per-class F1、AUPRC、Recall@K、Yield@Budget、多随机种子均值±标准差，并比较 random split、global temporal split、class-wise temporal split；
7. 机制分析：homophily/heterophily、supernode dilution、特征冗余、edge gate 权重、局部子图案例解释。

已有旧工程和 refactor 状态：我有一个本地项目 `D:\Code\VSCode\Bitcoin_Transaction_Identification`，Conda 环境名是 `MCM`。之前生成过一个研究版代码包 `Bitcoin_Transaction_Identification_research_v2_1.zip`。它包含 raw DB audit、11-class label map、label-preserving/class-balanced/temporal protocol 骨架、ETD-SAGE 模型骨架、benchmark/ablation/multiseed 脚本和测试。`python -m pytest -q` 需要先安装 pytest；已经发现 `raw_db.yaml` 中 `${BITCOIN_DB_URL}` 不会被 PyYAML 自动展开，`.env` 也不会自动变成 Windows 环境变量。实际运行时已经通过直接配置真实连接串或设置环境变量解决了连接问题。不要在回答里暴露真实密码。

已经成功运行的命令：
`python scripts/audit_raw_labels.py --config configs/data/raw_db.yaml`

输出确认：node_table=node_features，edge_table=transaction_edges，nodes_estimate=252219007，edges_estimate=785954737，并输出了上述 11 类标签统计和 temporal summary。

下一步最优先任务：不要急着训练模型。先构建新的协议数据集。优先运行：
`python scripts/build_protocol_dataset.py --config configs/data/raw_db.yaml --protocol label_preserving`
目标是验证 11 类是否全部保留、34,098 个有标签节点是否尽量全保留、PONZI/RANSOMWARE/MIXER 是否进入新 data.pt、节点数/边数是否可控、是否发生超级节点爆炸。之后运行协议对比：`python scripts/compare_protocols.py`。如果 label_preserving 爆炸，则需要改成 label_preserving_capped：所有有标签节点保留；每个有标签节点最多采样 N 个 1-hop 邻居；默认 N=50 或 100；度数超过 5000 的超级节点只保留节点或边，不继续扩展；先把总节点数控制在 50万~100万、边数控制在 1000万~3000万左右。

推荐的数据协议顺序：
Protocol A current_topk：已有旧 data.pt，用来证明 TopK 偏差；
Protocol B label_preserving：保留 11 类，当前马上做；
Protocol C class_balanced_khop：每类统一预算扩展，解决长尾；
Protocol D temporal_balanced：支持 class-wise temporal split 和 global temporal split，作为论文主协议。

模型实验顺序：等新数据集生成后，第一轮只跑 MLP 和 GraphSAGE，先回答新协议下 MLP 是否仍强、普通 GNN 是否仍不如 MLP、11 类任务难度如何、PONZI/RANSOMWARE/MIXER 是否能识别。不要一上来跑 8 个模型。之后再加入 EdgeTransformer / ETD-SAGE / ablation。

重要原则：不要继续只堆 vanilla GNN；不要把 NONE 当成普通 benign 类；不要把 EXCHANGE 默认视为非法；不要把旧 5 类 data.pt 当最终主实验；不要急着做 MultiTaskSAGE、SupCon、复杂 HeteroGraphSAGE、wavelet、TGN。先把数据协议做扎实。

请基于以上状态继续帮我推进。你后续回答时，要优先解决当前工程运行和实验决策问题。如果我发报错，请用最少输出给可执行修复；如果我发实验结果，请先判断它对研究路线意味着什么，再给下一步。

---

## 1. 项目背景

### 1.1 用户与目标

- 用户：zhx，电子科技大学计算机/网络空间安全方向本科生。
- 项目：比特币交易/实体识别、AML 风险相关实体分析、GNN。
- 当前目标：从课程/大创式项目升级为尽可能高质量的学术论文。
- 希望助手能力：研究路线设计、代码调试、数据协议、实验设计、论文叙事、答辩准备。

### 1.2 原始项目资料

已用过的关键资料包括：

- `Identification of Illicit Bitcoin Transactions Based on Graph Neural Network.pdf`
- `PROJECT_CONTEXT.md`
- `Bitcoin_Transaction_Identification-chenquan.zip`
- `Bitcoin_Transaction_Identification_refactored_v1.zip`
- `# 项目重构计划：边-时序-异配感知的多任务风险识别.md`
- `gemini调研结果.md`
- `qwen调研结果1.md`
- `qwen调研结果2.md`
- `full_eda_report.txt`
- `raw_report_supplement.txt`
- `report.txt`
- `Bitcoin_Transaction_Identification_research_v2_1.zip`

---

## 2. 原始数据与旧数据集

### 2.1 原始数据库规模

Raw PostgreSQL 数据库：

- node table: `node_features`
- edge table: `transaction_edges`
- nodes estimate: `252,219,007`
- edges estimate: `785,954,737`

旧报告/项目中也曾描述过类似规模：约 252M 节点、785M 边、13 年比特币交易数据。

### 2.2 旧 `data.pt`

当前旧 `data.pt`：

- nodes: `350,258`
- edges: `17,173,503`
- labeled nodes: `2,961`
- unlabeled nodes: `347,297`
- labeled ratio: `0.845%`
- node features: `19`
- edge features: `6`
- train/val/test: `1,779 / 591 / 591`

旧 label map：

- 0 NONE
- 1 INDIVIDUAL
- 2 BET
- 3 GAMBLING
- 4 EXCHANGE
- 5 BRIDGE

旧 `data.pt` 保留标签：

- INDIVIDUAL 2,421
- BET 96
- GAMBLING 179
- EXCHANGE 195
- BRIDGE 70

旧数据问题：

- 只保留 5 个监督类。
- 丢弃 MINING、PONZI、RANSOMWARE、FAUCET、MARKETPLACE、MIXER。
- 旧 TopK/Z-score 子图不是原始图的公平缩小版，而是明显偏向高活跃/高连接/高金额节点。
- 旧 `data.pt` 以后应作为 Protocol A / current_topk baseline，而不是主数据集。

---

## 3. Raw Label Audit 最新结果

已成功运行：

```bash
python scripts/audit_raw_labels.py --config configs/data/raw_db.yaml
```

输出：

```text
# Raw Database Label Audit

## Scale
- node_table: node_features
- edge_table: transaction_edges
- nodes_estimate: 252219007
- edges_estimate: 785954737
```

### 3.1 原始标签计数

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

总有标签节点数：`34,098`。

### 3.2 Per-class temporal summary

| label | avg_fi | avg_li | avg_fo | avg_lo | dur_in | dur_out | n |
|---|---:|---:|---:|---:|---:|---:|---:|
| BET | 390967 | 391207 | 391085 | 391257 | 240 | 172 | 6723 |
| BRIDGE | 667628 | 689617 | 670896 | 683549 | 21989 | 5242 | 70 |
| EXCHANGE | 425556 | 498389 | 434501 | 486108 | 72833 | 47122 | 794 |
| FAUCET | 436424 | 472396 | 439021 | 468597 | 35972 | 29340 | 125 |
| GAMBLING | 332995 | 361184 | 333496 | 358478 | 28189 | 24646 | 1410 |
| INDIVIDUAL | 377599 | 435011 | 384395 | 447574 | 57385 | 59655 | 23236 |
| MARKETPLACE | 520467 | 579876 | 528103 | 579426 | 59408 | 49984 | 115 |
| MINING | 318069 | 481350 | 335530 | 493841 | 158319 | 156124 | 724 |
| MIXER | 524200 | 558745 | 522655 | 551475 | 34545 | 26658 | 80 |
| PONZI | 356689 | 386862 | 358729 | 393304 | 30173 | 34458 | 587 |
| RANSOMWARE | 469705 | 493150 | 479164 | 495614 | 23445 | 15114 | 234 |

重要解释：

- BET 活跃时间极短。
- BRIDGE 很晚出现。
- MINING 时间跨度很长。
- RANSOMWARE、MIXER、MARKETPLACE 偏后期。
- 因此不能只做一个粗暴 global temporal split；需要同时做 class-wise temporal split 与 global temporal split。

### 3.3 Raw topology

```text
- degree_min: 1.0
- degree_avg: 6.2142926504391784
- degree_med: 3.0
- degree_p95: 12.0
- degree_p99: 38.0
- degree_max: 23804263.0
- degree_in_max: 17591957.0
- degree_out_max: 7934034.0
```

重要解释：

- 绝大多数节点度很小。
- 极少数超级节点度极大。
- 后续 k-hop / neighbor expansion 必须做 degree cap / neighbor cap，否则数据集会爆炸。

---

## 4. 研究路线结论

### 4.1 旧方向的问题

原先只是：

```text
在现有 data.pt 上比较 MLP、GCN、GAT、GraphSAGE 等模型。
```

这个方向不够高级，而且已经发现：

- MLP 在旧数据上很强。
- 普通 GNN 未必优于 MLP。
- 旧数据本身丢失 6 类，不能支撑真正 AML 论文。

### 4.2 新主线

英文题目候选：

```text
Sampling-Aware Edge-Temporal Directional Graph Learning for Long-Tailed Bitcoin Entity Risk Identification
```

中文题目候选：

```text
面向长尾比特币实体风险识别的采样感知边时序方向图学习方法研究
```

### 4.3 核心贡献

1. **Sampling Bias Discovery / Study**  
   发现旧 TopK/Z-score 子图严重扭曲标签空间，只保留 5/11 类，丢弃 AML 关键类。

2. **Label-Preserving Data Protocol**  
   从 2.52 亿节点、7.86 亿边原始图中构建保留 11 类、有受控规模、可复现的数据协议。

3. **11-class Entity Identification**  
   识别 INDIVIDUAL、BET、GAMBLING、EXCHANGE、MINING、PONZI、RANSOMWARE、FAUCET、MARKETPLACE、MIXER、BRIDGE。NONE/unlabeled 只作为上下文，不作为普通监督类。

4. **Sensitive Entity Ranking**  
   敏感实体排序，而不是简单“非法/正常”二分类。  
   高敏感：PONZI、RANSOMWARE、MIXER。  
   中敏感：BET、GAMBLING、MARKETPLACE、BRIDGE。  
   中性/服务：INDIVIDUAL、EXCHANGE、MINING、FAUCET。  
   注意：EXCHANGE 不应默认当作非法/高风险。

5. **ETD-GNN / ETD-SAGE**  
   Edge-Temporal-Directional GNN，利用交易边属性、时间属性、资金流方向。

6. **Long-tail and Temporal Evaluation**  
   使用 Macro-F1、Minority Macro-F1、per-class F1、AUPRC、Recall@K、Yield@Budget、多随机种子 mean±std。

7. **Mechanism / Explanation**  
   分析 homophily/heterophily、supernode dilution、edge gate 权重、局部子图案例。

---

## 5. 数据协议设计

### Protocol A: `current_topk`

- 已有旧 `data.pt`。
- 用途：复现实验、证明 TopK 偏差、作为 negative control。
- 不作为最终主数据集。

### Protocol B: `label_preserving`

当前最优先任务。

目标：

- 保留所有 11 类。
- 尽量保留全部 34,098 个 labeled nodes。
- 加入有限 context nodes。
- 防止超级节点爆炸。

需要验证：

- 11 类是否全部保留。
- PONZI/RANSOMWARE/MIXER/MARKETPLACE 是否进入新 data.pt。
- 节点数、边数是否可控。
- max degree 是否被控制。

### Protocol C: `class_balanced_khop`

- 在 Protocol B 成功后进行。
- 每个类别统一预算扩展 k-hop 邻域。
- 对长尾类进行均衡上下文保留。
- 不再只强化 BRIDGE。

### Protocol D: `temporal_balanced`

- 论文主协议候选。
- 支持：
  - global temporal split
  - class-wise temporal split
- 目的：避免 temporal leakage，同时处理类别出现时间差异。

### 如果数据爆炸

使用 `label_preserving_capped` 规则：

- 所有有标签节点必须保留。
- 每个有标签节点最多采样 N 个一跳邻居，N 可先设 50 或 100。
- 度数超过 5000 的超级节点只保留节点或少量边，不继续扩展。
- 第一版控制规模：
  - nodes: 50万 ~ 100万
  - edges: 1000万 ~ 3000万

---

## 6. 特征设计

### 6.1 Edge raw features

边表字段：

- `a`
- `b`
- `reveal`
- `last_seen`
- `total`
- `min_sent`
- `max_sent`
- `total_sent`

训练用 edge features 不包括 a/b。

### 6.2 Edge derived features

建议：

- `log_total_sent`
- `log_min_sent`
- `log_max_sent`
- `amount_range = log1p(max_sent - min_sent)`
- `avg_sent = total_sent / max(total, 1)`
- `duration = last_seen - reveal + 1`
- `tx_frequency = total / duration`
- `edge_recency = global_max_time - last_seen`

### 6.3 Node features

旧节点特征约 19 个。原始节点表有更多字段，包括：

- alias
- degree, degree_in, degree_out
- total_transactions_in/out
- min/max/total_sent/received
- cluster_size
- first/last_transaction_in/out
- cluster_num_edges/cc/nodes_in_cc
- label

建议派生：

- log total in/out sent/received
- active span in/out
- node recency
- in/out ratio
- degree in/out ratio

### 6.4 变换规则

- 对 amount/count 类特征使用 `log1p`。
- clip/winsorize at 99% or 99.5%。
- train-only normalization，避免数据泄漏。
- 保留 raw 和 transformed feature names 到 metadata。

---

## 7. 模型与实验计划

### 7.1 第一阶段不要跑很多模型

新协议数据集出来后，第一轮只跑：

- MLP
- GraphSAGE

目的：

- 判断 MLP 在新协议下是否仍然很强。
- 判断普通 GNN 是否仍不如 MLP。
- 判断 11 类任务难度。
- 判断 PONZI/RANSOMWARE/MIXER 是否能识别。

### 7.2 第二阶段模型

之后再加入：

- GCN
- GAT
- APPNP
- EdgeTransformer
- ETD-SAGE / ETD-GNN

### 7.3 ETD-SAGE 核心思想

- self channel
- incoming channel
- outgoing channel
- edge temporal gate
- amount/frequency/recency/duration/range features
- direction-aware aggregation

### 7.4 暂缓内容

暂时不要作为主线：

- MultiTaskSAGE
- SupConLoss
- 复杂 HeteroGraphSAGE
- wavelet
- full TGN
- active learning

这些可以作为后续扩展，不要抢主线。

---

## 8. 评估指标

必须有：

- Macro-F1
- Weighted-F1
- per-class Precision / Recall / F1
- Minority Macro-F1
- AUPRC / Macro PR-AUC
- Recall@Top-K
- Yield@Budget
- Confusion Matrix
- multi-seed mean ± std

对长尾类重点看：

- PONZI
- RANSOMWARE
- MIXER
- MARKETPLACE
- BRIDGE

---

## 9. 旧模型结果

旧 `data.pt` 上的结果：

- MLP 2-layer: weighted-F1 0.8691, macro-F1 0.6933
- MLP 4-layer: weighted-F1 0.8706, macro-F1 0.7020
- GCN: weighted-F1 0.7443, macro-F1 0.4222
- GAT: weighted-F1 0.7641, macro-F1 0.4071
- APPNP: weighted-F1 0.7465, macro-F1 0.5548
- GraphSAGE: weighted-F1 0.8020, macro-F1 0.6725

GraphSAGE per-class roughly：

- INDIVIDUAL 0.8545
- BRIDGE 0.8750
- BET 0.7059
- EXCHANGE 0.5773
- GAMBLING 0.3497

解释：

- 普通 GNN 未明显战胜 MLP。
- 旧图的图结构贡献存疑。
- 但旧数据本身有严重采样偏差，因此这些结果只能作为 baseline。

---

## 10. 工程状态

### 10.1 本地环境

- Windows
- VSCode
- Conda env: `MCM`
- 项目路径：`D:\Code\VSCode\Bitcoin_Transaction_Identification`

### 10.2 依赖安装

测试命令：

```bash
python -m pytest -q
```

如果报 `No module named pytest`：

```bash
python -m pip install pytest
```

安装 requirements：

```bash
python -m pip install -r requirements.txt
```

### 10.3 数据库连接问题

曾遇到错误：

```text
invalid dsn: missing "=" after "${BITCOIN_DB_URL}" in connection info string
```

原因：

- `configs/data/raw_db.yaml` 中的 `${BITCOIN_DB_URL}` 被 PyYAML 当成普通字符串。
- `.env` 文件不会自动变成 Windows 环境变量。
- `python-dotenv` 只是库，不会让 `echo %BITCOIN_DB_URL%` 自动有值。

解决方式：

- 临时最快：在 `configs/data/raw_db.yaml` 中直接填写真实连接串。
- 更正确：在代码里加载 `.env` 并展开 `${VAR}`。
- 不要在新对话中暴露真实数据库密码。

### 10.4 已成功命令

```bash
python scripts/audit_raw_labels.py --config configs/data/raw_db.yaml
```

下一步命令：

```bash
python scripts/build_protocol_dataset.py --config configs/data/raw_db.yaml --protocol label_preserving
```

随后：

```bash
python scripts/compare_protocols.py
```

---

## 11. 重要代码包/文档

已经生成或使用过：

- `Bitcoin_Transaction_Identification_research_v2_1.zip`
  - 研究版代码包。
  - 包含 raw audit、11-class label map、protocol skeleton、ETD-SAGE skeleton、benchmark/ablation/multiseed scripts。

- `BTC_AML_Research_Roadmap_for_User_v2.md`
  - 研究路线文档。

- `BTC_AML_Codex_Refactor_Spec_v2.md`
  - 给 Codex 的重构规范。

- `BTC_AML_Project_Docs_Index_v2.md`
  - 文档索引。

---

## 12. 后续最优先任务清单

### 当前马上做

1. 确认 raw audit 文件保存：

```bash
dir experiments\results\raw_audit
```

2. 构建 label-preserving dataset：

```bash
python scripts/build_protocol_dataset.py --config configs/data/raw_db.yaml --protocol label_preserving
```

3. 若报错，优先修复 sampler / SQL / memory / degree cap。

4. 生成 protocol comparison：

```bash
python scripts/compare_protocols.py
```

### 数据集构建成功后

1. 跑 MLP 和 GraphSAGE：

```bash
python scripts/run_benchmark.py --config configs/experiment/baseline_label_preserving.yaml --models mlp sage
```

2. 分析 11 类 per-class F1。

3. 若 GNN 仍弱于 MLP，进一步分析：

- 图同配/异配性
- supernode dilution
- edge feature 是否有效
- temporal split 难度

### 论文结构候选

1. Introduction
2. Related Work
3. Dataset and Sampling Bias Study
4. Label-Preserving Temporal Graph Construction
5. Edge-Temporal Directional GNN
6. Experiments
7. Analysis and Case Studies
8. Conclusion

---

## 13. 必须坚持的判断

- 旧 `data.pt` 不是最终主数据集。
- 当前项目最有论文价值的是“采样偏差 + 标签保持协议 + 边时序方向模型”。
- 不要只讲“我提出了一个新 GNN”，要讲“旧采样协议会丢失 AML 关键类，我提出更合理的数据协议，并在此基础上建模”。
- NONE/unlabeled 不能简单当作 benign。
- EXCHANGE 不能默认当作非法。
- 先做数据协议，再做模型。
- 先跑少量关键 baseline，再扩展模型矩阵。

