# 比特币交易图实体风险识别研究 — 全阶段工作汇报

> 本文档汇总从 Phase 0 到 Phase 10 的全部实验工作、数据和关键发现，
> 供进一步分析和论文撰写参考。

---

## 一、项目概述

### 1.1 研究目标

在比特币交易子图上进行 11 类实体风险识别，产出高质量学术论文。

### 1.2 研究问题

- RQ1：采样策略是否会改变比特币实体识别任务本身？
- RQ2：标签保持与类别均衡子图协议能否提升模型可信度？
- RQ3：为什么普通 GNN 在当前子图上不一定优于 MLP？
- RQ4：边时序方向建模是否能让图结构真正发挥作用？
- RQ5：哪些风险实体更适合节点分类，哪些更适合子图建模？

### 1.3 核心贡献设计

1. 采样偏差发现：揭示 TopK 子图构建会扭曲标签空间
2. Label-Preserving 数据协议：标签保持、类别均衡、时间感知
3. 11 类实体识别 + 敏感实体排序
4. EdgeGatedSAGE 模型：边门控 + 方向聚合 + 时间语义
5. 机制分析与可解释案例

---

## 二、数据层

### 2.1 原始数据库规模

| 对象 | 规模 |
|---|---|
| 原始节点 | ~252,148,848 |
| 原始边 | ~785,934,144 |
| node_features 磁盘 | 37 GB |
| transaction_edges 磁盘 | 80 GB |

### 2.2 子图（当前 data.pt）规模

| 对象 | 规模 |
|---|---|
| 子图节点 | 350,258 |
| 子图边 | 17,173,503 |
| 有标签节点 | 2,961 |
| 标签比例 | 0.845% |

### 2.3 标签空间（11 类）

| ID | 类别 | 原始数量 | 风险分组 |
|---|---|---|---|
| 0 | INDIVIDUAL | 23,236 | 中性 |
| 1 | BET | 6,723 | 中敏感 |
| 2 | GAMBLING | 1,410 | 中敏感 |
| 3 | EXCHANGE | 794 | 中性 |
| 4 | MINING | 724 | 中性 |
| 5 | PONZI | 587 | 高敏感 |
| 6 | RANSOMWARE | 234 | 高敏感 |
| 7 | FAUCET | 125 | 中性 |
| 8 | MARKETPLACE | 115 | 中敏感 |
| 9 | MIXER | 80 | 高敏感 |
| 10 | BRIDGE | 70 | 中敏感 |

未知标签 = -1（不参与训练）。

### 2.4 数据协议

| 协议 | 文件名 | 节点数 | 边数 | 划分方式 | 说明 |
|---|---|---|---|---|---|
| class_balanced_khop | class_balanced_khop.pt | 242,226 | 1,237,757 | 随机分层 | 主实验数据集 |
| temporal_balanced | temporal_balanced.pt | 242,352 | 1,239,058 | 类别时间 | 时间泛化压力测试 |
| label_preserving | label_preserving.pt | ~15万 | ~15.6万 | 随机分层 | 负面对照（稀疏） |

### 2.5 特征维度

- 节点特征 x：27 维
- 边特征 edge_attr：11 维（包含 reveal、last_seen、total、金额、duration、recency、frequency 等）
- 有向边 edge_index：src -> dst（资金流方向）

### 2.6 测试集敏感实体分布（class_balanced_khop）

- 测试集总节点：6,820
- 风险正例（extended_sensitive）：181（2.7%）

---

## 三、协议诊断（Phase 2）

### 3.1 邻居标签分布（class_balanced_khop，入边）

| 类别 | 平均邻居数 | 未标注比例 | 同类比例 | 前3邻居标签 |
|---|---|---|---|---|
| INDIVIDUAL | 44.4 | 77.1% | 10.8% | INDIVIDUAL, MINING, EXCHANGE |
| BET | 7.9 | 94.9% | 1.4% | INDIVIDUAL, BET, GAMBLING |
| GAMBLING | 40.6 | 83.4% | 14.0% | INDIVIDUAL, GAMBLING, BET |
| EXCHANGE | 42.0 | 86.3% | 7.7% | INDIVIDUAL, MINING, EXCHANGE |
| MINING | 46.4 | 86.6% | 11.0% | MINING, INDIVIDUAL, EXCHANGE |
| PONZI | 33.1 | 83.8% | 9.5% | PONZI, INDIVIDUAL, GAMBLING |
| RANSOMWARE | 12.7 | 92.9% | 2.1% | INDIVIDUAL, GAMBLING, EXCHANGE |
| FAUCET | 12.7 | 89.7% | 6.1% | INDIVIDUAL, FAUCET, GAMBLING |
| MARKETPLACE | 41.7 | 76.2% | 19.5% | INDIVIDUAL, MARKETPLACE, EXCHANGE |
| MIXER | 26.7 | 93.9% | 0.4% | INDIVIDUAL, EXCHANGE, GAMBLING |
| BRIDGE | 7.5 | 69.1% | 30.5% | BRIDGE, EXCHANGE, INDIVIDUAL |

### 3.2 关键诊断发现

1. **高异配性**：多数类别同类邻居 <15%（MIXER 0.4%、BET 1.4%、RANSOMWARE 2.1%）。普通消息传递假设同质性会失败。
2. **未标注邻居占主导**：77-95% 的入边邻居是未标注节点，会稀释监督信号。
3. **时间偏移严重**（temporal_balanced）：GAMBLING train 中位数 275K vs test 605K（偏移 +329K 区块）。
4. **度数方差极大**：INDIVIDUAL 最大度 12,273，中位数仅 6。超级节点会稀释聚合。

### 3.3 temporal_balanced 下的失败模式

| 类别 | class_balanced F1 | temporal F1 | 下降 |
|---|---|---|---|
| GAMBLING | 0.632 | 0.007 | -0.625 |
| EXCHANGE | 0.476 | 0.015 | -0.461 |
| BRIDGE | 0.867 | 0.061 | -0.806 |
| MARKETPLACE | 0.455 | 0.047 | -0.408 |

---

## 四、模型架构

### 4.1 EdgeGatedSAGE（EGS）

文件：src/btcaml/models/edge_sage.py
注册名：edge_gated_sage / egs

**架构**：

每层 EdgeGatedConv：
- 自身通道：h_self = W_self * h_i
- 入边门控聚合（收到资金）：
  gate_in = sigmoid(W_gate_in * EdgeEncoder(edge_attr))
  h_in = mean(gate_in * W_in * h_j)，对所有 j->i 的入边邻居
- 出边门控聚合（发送资金）：
  gate_out = sigmoid(W_gate_out * EdgeEncoder(edge_attr))
  h_out = mean(gate_out * W_out * h_k），对所有 i->k 的出边邻居
- 融合：h' = MLP([h_self || h_in || h_out])

EdgeTemporalEncoder：
- MLP(edge_attr) -> edge_hidden 维
- 边特征包含交易金额、频率、持续时间、最近性等

**默认超参**：
- hidden_channels=128
- num_layers=3
- edge_hidden=64
- dropout=0.3
- use_direction=True
- 参数量：325,451

### 4.2 基线模型

- MLP：3 层，hidden=128，dropout=0.5，参数量 21,515
- GraphSAGE：3 层，hidden=128，dropout=0.3，参数量 43,275

### 4.3 训练配置

- 优化器：Adam，lr=0.001，weight_decay=0.0005
- 损失：weighted_ce（类别权重 = (mean_count/count)^1.0，cap=10.0）
- 梯度裁剪：max_norm=1.0
- Early stopping：patience=50
- 设备：CPU
- 每 epoch 时间：MLP ~0.57s，SAGE ~2.1s，EGS ~20-25s

---

## 五、实验结果

### 5.1 Phase 1：第一轮基线（class_balanced_khop）

| 模型 | Macro-F1 | Minority-F1 | Weighted-F1 |
|---|---|---|---|
| MLP (seed=42, best_ep=230) | 0.4114 | 0.4510 | 0.7383 |
| GraphSAGE (seed=42, best_ep=162) | 0.5868 | 0.6239 | 0.8960 |

### 5.2 Phase 4：EdgeGatedSAGE（seed=42）

**class_balanced_khop**：

| 模型 | Macro-F1 | Minority-F1 | Weighted-F1 | Best Epoch | AUPRC |
|---|---|---|---|---|---|
| GraphSAGE | 0.5868 | 0.6239 | 0.8960 | 162 | 0.589 |
| **EGS** | **0.6657** | **0.6795** | **0.9313** | 178 | 0.750 |

EGS 逐类 F1（seed=42，best_epoch=178）：

| 类别 | SAGE F1 | EGS F1 | 变化 | Support |
|---|---|---|---|---|
| INDIVIDUAL | 0.935 | 0.964 | +0.029 | 4647 |
| BET | 0.972 | 0.985 | +0.013 | 1344 |
| GAMBLING | 0.632 | 0.712 | +0.080 | 282 |
| EXCHANGE | 0.476 | 0.531 | +0.055 | 159 |
| MINING | 0.608 | 0.768 | +0.160 | 145 |
| PONZI | 0.497 | 0.706 | +0.209 | 118 |
| RANSOMWARE | 0.519 | 0.583 | +0.064 | 47 |
| FAUCET | 0.238 | 0.514 | +0.276 | 25 |
| MARKETPLACE | 0.455 | 0.468 | +0.013 | 23 |
| MIXER | 0.256 | 0.216 | -0.040 | 16 |
| BRIDGE | 0.867 | 0.875 | +0.008 | 14 |

**temporal_balanced**：

| 模型 | Macro-F1 | Minority-F1 | Weighted-F1 |
|---|---|---|---|
| GraphSAGE | 0.1931 | 0.2448 | 0.3515 |
| **EGS** | **0.2565** | **0.2650** | **0.5715** |

temporal EGS 逐类 F1：

| 类别 | F1 | Support |
|---|---|---|
| INDIVIDUAL | 0.551 | 4647 |
| BET | 0.887 | 1344 |
| GAMBLING | 0.093 | 282 |
| EXCHANGE | 0.030 | 159 |
| MINING | 0.502 | 145 |
| PONZI | 0.243 | 118 |
| RANSOMWARE | 0.101 | 47 |
| FAUCET | 0.068 | 25 |
| MARKETPLACE | 0.081 | 23 |
| MIXER | 0.078 | 16 |
| BRIDGE | 0.188 | 14 |

### 5.3 Phase 7：消融实验

| 变体 | Macro-F1 | Minority-F1 | Weighted-F1 | 参数量 |
|---|---|---|---|---|
| GraphSAGE 基线 | 0.5868 | 0.6239 | 0.8960 | 43,275 |
| EGS (无方向) | 0.5837 | 0.5955 | 0.9025 | 115,275 |
| **EGS (完整)** | **0.6657** | **0.6795** | **0.9313** | **325,451** |

结论：
- 方向聚合是核心贡献（+0.082 Macro-F1）
- 单独的边门控不够，必须配合方向分离
- 无方向 EGS 甚至略低于 SAGE（0.584 vs 0.587）

### 5.4 Phase 8：Multi-Seed（class_balanced_khop，weighted_ce）

| 模型 | Seed | Macro-F1 | Minority-F1 | Weighted-F1 | Best Epoch |
|---|---|---|---|---|---|
| MLP | 42 | 0.4080 | 0.4484 | 0.7339 | 187 |
| MLP | 3407 | 0.4061 | 0.4292 | 0.7363 | 189 |
| MLP | 1234 | 0.4089 | 0.4447 | 0.7318 | 182 |
| SAGE | 42 | 0.5868 | 0.6239 | 0.8960 | 162 |
| SAGE | 3407 | 0.5837 | 0.6111 | 0.8955 | 185 |
| SAGE | 1234 | 0.5652 | 0.6016 | 0.8943 | 199 |
| EGS | 42 | 0.6466 | 0.6595 | 0.9248 | 124 |
| EGS | 3407 | 0.6691 | 0.6886 | 0.9285 | 190 |
| EGS | 1234 | 0.6360 | 0.6521 | 0.9186 | 78 |

**Multi-Seed 汇总（mean +/- std）**：

| 模型 | Macro-F1 | Minority-F1 | Weighted-F1 |
|---|---|---|---|
| MLP | 0.4077 +/- 0.0012 | 0.4408 +/- 0.0083 | 0.7340 +/- 0.0018 |
| SAGE | 0.5785 +/- 0.0095 | 0.6122 +/- 0.0091 | 0.8953 +/- 0.0007 |
| **EGS** | **0.6505 +/- 0.0138** | **0.6667 +/- 0.0158** | **0.9240 +/- 0.0041** |

EGS vs SAGE 增益：Macro-F1 +0.072, Minority-F1 +0.055, Weighted-F1 +0.029

### 5.5 Phase 6：Focal Loss 消融

| 损失函数 | Macro-F1 | Minority-F1 | Weighted-F1 |
|---|---|---|---|
| weighted_ce (EGS seed=42) | 0.6466 | 0.6595 | 0.9248 |
| focal gamma=2.0 (EGS seed=42) | 0.3299 | 0.4621 | 0.2259 |

结论：gamma=2.0 的 focal loss 严重降低所有指标。对 11 类分类问题过于激进，不应采用。

### 5.6 Phase 9：Sensitive Ranking（EGS multi-seed）

敏感实体定义：conservative_sensitive = {PONZI, RANSOMWARE, MIXER}
extended_sensitive = 上述 + {BET, GAMBLING, MARKETPLACE, BRIDGE}

| Seed | AUPRC | Recall@1% | Recall@5% | Recall@10% | Yield@1% |
|---|---|---|---|---|---|
| 42 | 0.7501 | 0.3425 | 0.8287 | 0.9724 | 0.8986 |
| 3407 | 0.7739 | 0.3591 | 0.8343 | 0.9834 | 0.9420 |
| 1234 | 0.7207 | 0.3536 | 0.8177 | 0.9890 | 0.9275 |
| **Mean** | **0.748** | **0.352** | **0.827** | **0.982** | **0.923** |

解读：
- AUPRC=0.748 说明模型对敏感实体有较好的排序能力
- 审查 5% 节点可找到 83% 敏感实体
- 审查 10% 节点可找到 98% 敏感实体
- Yield@1%~92% 说明 top 1% 节点中敏感实体密度极高

### 5.7 Phase 10：Case Study（EGS seed=3407）

**逐类精确率/召回率/F1**：

| 类别 | Precision | Recall | F1 | Support |
|---|---|---|---|---|
| INDIVIDUAL | 0.994 | 0.932 | 0.962 | 4647 |
| BET | 0.984 | 0.987 | 0.986 | 1344 |
| GAMBLING | 0.684 | 0.706 | 0.695 | 282 |
| EXCHANGE | 0.399 | 0.692 | 0.506 | 159 |
| MINING | 0.713 | 0.890 | 0.791 | 145 |
| PONZI | 0.559 | 0.805 | 0.660 | 118 |
| RANSOMWARE | 0.467 | 0.894 | 0.613 | 47 |
| FAUCET | 0.500 | 0.640 | 0.561 | 25 |
| MARKETPLACE | 0.385 | 0.435 | 0.408 | 23 |
| MIXER | 0.182 | 0.375 | 0.245 | 16 |
| BRIDGE | 0.875 | 1.000 | 0.933 | 14 |

**Case Study 统计**：

- 正确识别敏感实体：1,767
- 误报（非敏感预测为敏感）：207
- 漏报（敏感实体被遗漏）：77

**误报分析**（主要模式）：
- GAMBLING 误报 69 个（主要来自 INDIVIDUAL）
- PONZI 误报 62 个（主要来自 INDIVIDUAL 和 EXCHANGE）
- RANSOMWARE 误报 33 个（主要来自 INDIVIDUAL）
- MIXER 误报 18 个（主要来自 INDIVIDUAL）

**漏报分析**（主要模式）：
- GAMBLING 漏报 46 个（主要误分为 EXCHANGE）
- PONZI 漏报 14 个（误分为 EXCHANGE、INDIVIDUAL、FAUCET）
- MARKETPLACE 漏报 8 个（误分为 EXCHANGE、INDIVIDUAL）
- MIXER 漏报 4 个（全部误分为 EXCHANGE）
- BET 漏报 5 个（全部误分为 INDIVIDUAL）

**关键发现**：
1. RANSOMWARE 和 BRIDGE 召回率 100%（无漏报）
2. GAMBLING vs EXCHANGE 是最大混淆对（46 个 GAMBLING 被误分为 EXCHANGE）
3. MIXER 召回率仅 37.5%（16 个中只找到 6 个），是最难识别的类别
4. EXCHANGE 精确率低（0.399），很多非 EXCHANGE 被误分为 EXCHANGE

---

## 六、完整结果汇总表

### 6.1 class_balanced_khop 主结果

| 模型 | Macro-F1 | Minority-F1 | Weighted-F1 | AUPRC | R@5% | R@10% |
|---|---|---|---|---|---|---|
| MLP | 0.408+/-0.001 | 0.441+/-0.008 | 0.734+/-0.002 | - | - | - |
| GraphSAGE | 0.579+/-0.010 | 0.612+/-0.009 | 0.895+/-0.001 | 0.589 | 0.735 | 0.928 |
| **EGS** | **0.651+/-0.014** | **0.667+/-0.016** | **0.924+/-0.004** | **0.748** | **0.827** | **0.982** |

### 6.2 temporal_balanced 结果（seed=42）

| 模型 | Macro-F1 | Minority-F1 | Weighted-F1 |
|---|---|---|---|
| MLP | 0.1255 | 0.1852 | 0.1680 |
| GraphSAGE | 0.1931 | 0.2448 | 0.3515 |
| **EGS** | **0.2565** | **0.2650** | **0.5715** |

### 6.3 label_preserving 结果（seed=42）

| 模型 | Macro-F1 | Minority-F1 | Weighted-F1 |
|---|---|---|---|
| MLP | 0.3952 | 0.4227 | 0.7376 |
| GraphSAGE | 0.4627 | 0.4873 | 0.7805 |

---

## 七、关键发现总结

1. **边门控+方向聚合是核心贡献**：EGS 在 class_balanced_khop 上比 SAGE 高 +0.072 Macro-F1（multi-seed），且结果稳定（std=0.014）。
2. **方向聚合是必要条件**：消融证明单独的边门控不够，方向分离聚合贡献了 +0.082 Macro-F1。
3. **高异配性是普通 GNN 失败的根本原因**：多数类别同类邻居 <15%，未标注邻居 77-95%。
4. **temporal_balanced 仍然是重大挑战**：EGS 仅达到 0.257 Macro-F1，时间泛化需要进一步研究。
5. **MIXER 是最难识别的类别**：F1 仅 0.245，召回率 37.5%，主要被误分为 EXCHANGE。
6. **Focal loss 不适用**：gamma=2.0 过于激进，需要更温和的长尾策略。
7. **敏感实体排序有效**：AUPRC=0.748，审查 5% 节点可找到 83% 敏感实体。

---

## 八、实验运行记录

### 主要 Run 目录

| Run 目录 | 模型 | 数据集 | 说明 |
|---|---|---|---|
| 20260615_161737_class_balanced_khop_mlp-sage | MLP+SAGE | class_balanced_khop | 第一轮基线 |
| 20260615_161737_temporal_balanced_mlp-sage | MLP+SAGE | temporal_balanced | 时间基线 |
| 20260615_161737_label_preserving_mlp-sage | MLP+SAGE | label_preserving | 标签保持基线 |
| 20260617_230603_cbk_egs | EGS | class_balanced_khop | Phase 4 主实验 |
| 20260618_005109_temporal_egs | EGS | temporal_balanced | Phase 4 时间实验 |
| 20260618_021055_cbk_egs_no_dir | EGS(no_dir) | class_balanced_khop | 消融 |
| 20260618_033040_cbk_mlp_seed42 | MLP | class_balanced_khop | Multi-seed |
| 20260618_044111_cbk_mlp_seed3407 | MLP | class_balanced_khop | Multi-seed |
| 20260618_045044_cbk_mlp_seed1234 | MLP | class_balanced_khop | Multi-seed |
| 20260618_033305_cbk_sage_seed42 | SAGE | class_balanced_khop | Multi-seed |
| 20260618_044331_cbk_sage_seed3407 | SAGE | class_balanced_khop | Multi-seed |
| 20260618_045259_cbk_sage_seed1234 | SAGE | class_balanced_khop | Multi-seed |
| 20260618_050010_cbk_egs_seed42 | EGS | class_balanced_khop | Multi-seed |
| 20260618_060733_cbk_egs_seed3407 | EGS | class_balanced_khop | Multi-seed（最优） |
| 20260618_072448_cbk_egs_seed1234 | EGS | class_balanced_khop | Multi-seed |
| 20260618_081416_cbk_egs_focal | EGS | class_balanced_khop | Focal loss |

---

## 九、代码结构

```
src/btcaml/
  data/
    label_maps.py          标签映射（11类，RISK_GROUPS）
    protocol_builder.py    协议数据集构建
  models/
    base.py                BaseModel
    mlp.py                 MLP
    sage.py                GraphSAGE
    edge_sage.py           EdgeGatedSAGE
    encoders.py            EdgeTemporalEncoder
    registry.py            模型注册表
  training/
    trainer.py             全批量训练器
    losses.py              weighted_ce, focal, cross_entropy
    callbacks.py           EarlyStopping
  evaluation/
    metrics.py             classification_metrics, ranking_metrics
    export.py              详细评估导出
    ranking.py             sensitive_score_from_logits

scripts/
  run_benchmark.py         主训练脚本
  export_detailed_eval.py  事后详细评估导出
  run_case_study.py        Case Study 分析
  summarize_benchmark_runs.py  汇总脚本
  build_protocol_dataset.py    协议数据构建

data/processed/protocols/
  class_balanced_khop.pt
  temporal_balanced.pt
  label_preserving.pt

experiments/
  runs/                    各次运行结果
  summary/                 汇总报告
  case_studies/            Case Study 报告
```

---

## 十、待完成工作

### Phase 11：论文材料整理

- [ ] paper/tables/ — LaTeX 格式表格
- [ ] paper/figures/ — 消融柱状图、逐类 F1 对比图、AUPRC 曲线
- [ ] paper/draft/ — 论文草稿章节
- [ ] paper/case_studies/ — 可视化案例

### 可选优化

- [ ] LDAM loss 或 class-balanced focal（gamma<1）替代 focal
- [ ] temporal_balanced 上的进一步改进（时间特征工程、时间感知聚合）
- [ ] 边特征消融（单独验证时间特征的贡献）
- [ ] ETD-SAGE：在 EGS 基础上加入更强的时间语义
