# Codex 执行版：比特币交易图风险识别项目重构细节方案 v2

> 本文档给 Codex / 代码代理使用。  
> v2 在上一版基础上加入最新 EDA 结论：当前 `data.pt` 是 activity-biased TopK 子图，只保留 5/11 个监督类别，且 PONZI / RANSOMWARE / MIXER / MINING / FAUCET / MARKETPLACE 等原始类别完全丢失。  
> 所以工程优先级调整为：
>
> **先重构 raw DB -> protocol dataset builder，再做 ETD-GNN。**

---

## 0. 总体原则 v2

### 0.1 研究主线

从：

```text
在当前 data.pt 上优化 GNN
```

升级为：

```text
Sampling-Aware + Label-Preserving + Edge-Temporal-Directional Graph Learning
```

即：

1. 审计原始数据库标签；
2. 揭示 TopK 采样偏差；
3. 构建标签保持、类别均衡、时间感知的协议数据集；
4. 在新协议上训练基线和 ETD-GNN；
5. 输出论文级实验表格和分析。

### 0.2 最新 EDA 必须吸收的事实

原始数据库：

```text
node_features: ~252,148,848 rows, 37GB
transaction_edges: ~785,934,144 rows, 80GB
```

当前 `data.pt`：

```text
nodes: 350,258
edges: 17,173,503
labeled: 2,961
label ratio: 0.845%
node features: 19
edge features: 6
```

原始库 11 类：

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

当前 `data.pt` 仅保留：

```text
INDIVIDUAL
BET
GAMBLING
EXCHANGE
BRIDGE
```

完全丢失：

```text
MINING
PONZI
RANSOMWARE
FAUCET
MARKETPLACE
MIXER
```

必须将当前 `data.pt` 定义为：

```text
Protocol A: Activity-biased TopK baseline
```

不得作为最终主数据。

### 0.3 执行优先级

必须按以下顺序执行，不要跳到复杂模型：

| 优先级 | 模块 | 说明 |
|---|---|---|
| P0 | raw label audit | 审计 11 类标签与时间分布 |
| P1 | protocol dataset builder | 从原始 DB 构建 B/C/D 数据集 |
| P2 | protocol comparison | 输出采样偏差报告 |
| P3 | baseline benchmark | MLP/XGBoost/LightGBM/GraphSAGE |
| P4 | ETD-GNN | 边时序方向模型 |
| P5 | ablation + multiseed | 论文结果 |
| P6 | explanation / GUI | 展示增强 |
| Optional | MultiTask / SupCon / HeteroGraphSAGE | 后置 |

---

## 1. 新版本目标与版本边界

### v2.1：Raw Audit + Protocol Framework

目标：把原始 DB 和当前 `data.pt` 的差异固化为可复现报告。

必须完成：

```text
scripts/audit_raw_labels.py
scripts/audit_current_data.py
scripts/compare_label_coverage.py
src/btcaml/data/raw_schema.py
src/btcaml/data/label_map.py
src/btcaml/data/protocols/base.py
```

输出：

```text
experiments/eda/raw_label_inventory.csv
experiments/eda/current_data_inventory.csv
experiments/eda/label_retention_report.csv
experiments/eda/protocol_A_manifest.json
```

### v2.2：Protocol Dataset Builder

目标：重新从原始 DB 构建 B/C/D 三套数据集。

必须完成：

```text
Protocol A: current TopK baseline, read existing data.pt
Protocol B: label_preserving
Protocol C: class_balanced_khop
Protocol D: temporal_label_preserving
```

输出：

```text
data/processed/protocol_A_topk.pt
data/processed/protocol_B_label_preserving.pt
data/processed/protocol_C_balanced_khop.pt
data/processed/protocol_D_temporal_balanced.pt
```

### v2.3：Baseline Benchmark

目标：先证明数据协议比模型更关键。

模型：

```text
MLP
XGBoost
LightGBM
GCN
GAT
GraphSAGE
ResGraphSAGE
APPNP
```

输出：

```text
experiments/results/protocol_benchmark.csv
experiments/results/sampling_bias_table.csv
experiments/paper_tables/table_sampling_bias.md
```

### v2.4：ETD-GNN

目标：实现核心论文模型。

新增：

```text
src/btcaml/models/encoders.py
src/btcaml/models/etd_sage.py
src/btcaml/models/edge_transformer.py
```

### v2.5：Ablation + Paper Export

目标：输出论文级结果。

新增：

```text
scripts/run_ablation.py
scripts/run_multiseed.py
scripts/export_paper_tables.py
scripts/export_paper_figures.py
```

### v2.6：Explanation + Demo

目标：答辩和论文 case study。

新增：

```text
src/btcaml/explain/subgraph_extractor.py
src/btcaml/explain/edge_gate_explainer.py
src/btcaml/explain/case_study.py
```

---

## 2. 推荐目录结构 v2

```text
Bitcoin_Transaction_Identification/
├── README.md
├── pyproject.toml
├── requirements.txt
├── .env.example
├── Makefile
├── dvc.yaml
│
├── configs/
│   ├── db/
│   │   └── postgres.yaml
│   ├── data/
│   │   ├── protocol_A_topk.yaml
│   │   ├── protocol_B_label_preserving.yaml
│   │   ├── protocol_C_balanced_khop.yaml
│   │   └── protocol_D_temporal_balanced.yaml
│   ├── split/
│   │   ├── random.yaml
│   │   ├── classwise_temporal.yaml
│   │   ├── global_temporal.yaml
│   │   └── leakage_control.yaml
│   ├── model/
│   │   ├── mlp.yaml
│   │   ├── sage.yaml
│   │   ├── edge_transformer.yaml
│   │   └── etd_sage.yaml
│   ├── train/
│   │   ├── default.yaml
│   │   ├── focal.yaml
│   │   └── multiseed.yaml
│   └── experiment/
│       ├── protocol_benchmark.yaml
│       ├── paper_main.yaml
│       └── ablation_etd.yaml
│
├── src/
│   └── btcaml/
│       ├── data/
│       │   ├── db.py
│       │   ├── raw_schema.py
│       │   ├── label_map.py
│       │   ├── label_inventory.py
│       │   ├── feature_engineering.py
│       │   ├── transforms.py
│       │   ├── splits.py
│       │   ├── degree_cap.py
│       │   ├── sampling_budget.py
│       │   └── protocols/
│       │       ├── __init__.py
│       │       ├── base.py
│       │       ├── topk_zscore.py
│       │       ├── label_preserving.py
│       │       ├── balanced_khop.py
│       │       └── temporal_balanced.py
│       │
│       ├── models/
│       │   ├── base.py
│       │   ├── registry.py
│       │   ├── mlp.py
│       │   ├── sage.py
│       │   ├── gcn.py
│       │   ├── gat.py
│       │   ├── appnp.py
│       │   ├── edge_transformer.py
│       │   ├── encoders.py
│       │   └── etd_sage.py
│       │
│       ├── training/
│       │   ├── trainer.py
│       │   ├── losses.py
│       │   ├── callbacks.py
│       │   └── optim.py
│       │
│       ├── evaluation/
│       │   ├── metrics.py
│       │   ├── evaluator.py
│       │   ├── ranking.py
│       │   ├── confusion.py
│       │   └── tables.py
│       │
│       ├── analysis/
│       │   ├── sampling_bias.py
│       │   ├── homophily.py
│       │   ├── supernode.py
│       │   ├── temporal_drift.py
│       │   └── error_analysis.py
│       │
│       ├── explain/
│       │   ├── subgraph_extractor.py
│       │   ├── edge_gate_explainer.py
│       │   └── case_study.py
│       │
│       └── utils/
│           ├── seed.py
│           ├── logging.py
│           ├── io.py
│           └── config.py
│
├── scripts/
│   ├── audit_raw_labels.py
│   ├── audit_current_data.py
│   ├── compare_label_coverage.py
│   ├── build_protocol_dataset.py
│   ├── compare_protocols.py
│   ├── train.py
│   ├── evaluate.py
│   ├── run_benchmark.py
│   ├── run_ablation.py
│   ├── run_multiseed.py
│   └── export_paper_tables.py
│
├── experiments/
│   ├── eda/
│   ├── checkpoints/
│   ├── results/
│   ├── logs/
│   ├── paper_tables/
│   └── paper_figures/
│
├── notebooks/
│   ├── 01_raw_label_audit.ipynb
│   ├── 02_protocol_comparison.ipynb
│   ├── 03_homophily_analysis.ipynb
│   └── 04_case_study.ipynb
│
├── tests/
│   ├── test_label_map.py
│   ├── test_protocols.py
│   ├── test_splits.py
│   ├── test_feature_engineering.py
│   ├── test_models_forward.py
│   └── test_metrics.py
│
└── paper/
    ├── figures/
    ├── tables/
    ├── notes/
    └── draft.md
```

---

## 3. 标签体系与风险分组

### 3.1 11 类 Label Map

新增 `src/btcaml/data/label_map.py`：

```python
LABELS_11 = [
    "INDIVIDUAL",
    "BET",
    "GAMBLING",
    "EXCHANGE",
    "MINING",
    "PONZI",
    "RANSOMWARE",
    "FAUCET",
    "MARKETPLACE",
    "MIXER",
    "BRIDGE",
]

LABEL_TO_ID_11 = {name: idx for idx, name in enumerate(LABELS_11)}
ID_TO_LABEL_11 = {idx: name for name, idx in LABEL_TO_ID_11.items()}

UNLABELED_VALUE = -1
```

注意：

- 新任务不再用 `0=NONE` 当分类输出；
- 未标注节点统一映射为 `-1`；
- 分类头输出 `num_classes=11`；
- loss / metric 只在 `labeled_mask` 上计算。

### 3.2 兼容旧 5 类任务

保留旧任务用于 Protocol A 复现：

```python
LABELS_5 = ["INDIVIDUAL", "BET", "GAMBLING", "EXCHANGE", "BRIDGE"]
```

旧 `data.pt` 可转换为：

```text
y_original: 0..5
y_mapped_5: -1 or 0..4
```

### 3.3 Sensitive Entity Ranking 分组

新增：

```python
SENSITIVE_GROUPS = {
    "high_sensitive": ["PONZI", "RANSOMWARE", "MIXER"],
    "medium_sensitive": ["BET", "GAMBLING", "MARKETPLACE", "BRIDGE"],
    "neutral_or_service": ["INDIVIDUAL", "EXCHANGE", "MINING", "FAUCET"],
}
```

`EXCHANGE` 不默认高风险。

生成：

```python
risk_label_conservative = 1 if label in high_sensitive else 0
risk_label_extended = 1 if label in high_sensitive + medium_sensitive else 0
```

用于 ranking，不作为法律意义上的非法分类。

---

## 4. Raw DB 审计模块

### 4.1 `scripts/audit_raw_labels.py`

功能：

1. 查询原始 `node_features` 的 label 分布；
2. 查询每类时间范围；
3. 查询每类特征均值/分位数；
4. 输出 `raw_label_inventory.csv`。

输出字段：

```text
label
count
avg_first_in
avg_last_in
avg_first_out
avg_last_out
duration_in
duration_out
degree_median
degree_p95
```

### 4.2 `scripts/audit_current_data.py`

功能：

1. 读取当前 `data.pt`；
2. 输出当前类别分布；
3. 输出当前时间范围；
4. 输出 edge_attr 分布；
5. 输出 neighborhood composition。

### 4.3 `scripts/compare_label_coverage.py`

功能：

比较 raw vs current：

```text
raw_count
current_count
retention_ratio
missing_flag
```

必须输出：

```text
experiments/eda/label_retention_report.csv
experiments/eda/label_retention_report.md
```

表格模板：

| label | raw_count | current_count | retention_ratio | status |
|---|---:|---:|---:|---|
| INDIVIDUAL | 23236 | 2421 | 10.4% | kept |
| BET | 6723 | 96 | 1.4% | underrepresented |
| PONZI | 587 | 0 | 0% | missing |
| RANSOMWARE | 234 | 0 | 0% | missing |

---

## 5. Protocol Dataset Builder

### 5.1 Base Protocol 接口

`src/btcaml/data/protocols/base.py`

```python
class DataProtocol:
    name: str

    def select_labeled_nodes(self, db, config):
        raise NotImplementedError

    def select_context_nodes(self, db, labeled_nodes, config):
        raise NotImplementedError

    def build_edges(self, db, selected_nodes, config):
        raise NotImplementedError

    def build_features(self, db, selected_nodes, edges, config):
        raise NotImplementedError

    def build_splits(self, data, config):
        raise NotImplementedError

    def save_manifest(self, data, output_dir):
        raise NotImplementedError
```

### 5.2 Protocol A：TopK-ZScore

文件：

```text
src/btcaml/data/protocols/topk_zscore.py
```

实现：

- 读取现有 `data.pt`；
- 生成 manifest；
- 不重建。

用途：复现 baseline。

### 5.3 Protocol B：Label-Preserving

文件：

```text
src/btcaml/data/protocols/label_preserving.py
```

流程：

```text
1. selected_labeled = all nodes whose label in LABELS_11
2. selected_context = sampled unlabeled/context nodes
3. selected = selected_labeled ∪ selected_context
4. build induced edges
5. transform features
6. build splits
```

配置示例：

```yaml
protocol:
  name: label_preserving
  target_num_nodes: 350000
  keep_all_labeled: true
  labels: all_11
  context_sampling:
    strategy: mixed
    degree_budget_ratio: 0.4
    pagerank_budget_ratio: 0.3
    random_budget_ratio: 0.3
```

### 5.4 Protocol C：Class-Balanced k-hop

文件：

```text
src/btcaml/data/protocols/balanced_khop.py
```

流程：

```text
1. For each label c in 11 classes:
   seed_c = all labeled nodes of c
2. Sample k-hop neighbors around seed_c
3. Apply per-class neighbor budget
4. Apply degree cap for supernodes
5. Merge all categories
6. Add global background nodes
7. Build induced graph
```

配置示例：

```yaml
protocol:
  name: balanced_khop
  keep_all_labeled: true
  target_num_nodes: 500000
  hops:
    default: 1
    PONZI: 2
    RANSOMWARE: 2
    MIXER: 2
    BRIDGE: 2
  per_class_neighbor_budget: 30000
  supernode_degree_cap: 10000
  background:
    strategy: degree_pagerank_temporal
    budget: 100000
```

### 5.5 Protocol D：Temporal Label-Preserving

文件：

```text
src/btcaml/data/protocols/temporal_balanced.py
```

流程：

```text
1. Build label-preserving selected nodes
2. Build temporal splits
3. Optionally filter train/val/test graph by cutoff
4. Save separate masks or separate Data objects
```

配置示例：

```yaml
split:
  type: classwise_temporal
  train_ratio: 0.6
  val_ratio: 0.2
  test_ratio: 0.2
  time_key: first_transaction_in

leakage_control:
  enabled: false
  edge_time_key: reveal
```

注意：

- `classwise_temporal` 保证每类都有训练样本；
- `global_temporal` 用于真实部署压力测试；
- `leakage_control` 后续再启用。

---

## 6. Feature Engineering

文件：

```text
src/btcaml/data/feature_engineering.py
```

### 6.1 金额特征处理

所有金额类：

```python
x = np.log1p(x)
x = np.clip(x, p01, p995)  # or p99
x = robust_or_zscore_fit_on_train(x)
```

必须 train-only fit：

```text
fit scaler on train/labeled train or train time window
apply to val/test
```

### 6.2 Edge derived features

从原始边：

```text
reveal, last_seen, total, min_sent, max_sent, total_sent
```

派生：

```text
log_min_sent
log_max_sent
log_total_sent
amount_range = log1p(max_sent - min_sent)
avg_sent = total_sent / max(total, 1)
duration = last_seen - reveal + 1
frequency = total / duration
recency = global_max_block - last_seen
```

输出：

```text
data.edge_attr_raw
data.edge_attr
edge_attr_columns
```

### 6.3 Node derived features

```text
active_span_in = last_transaction_in - first_transaction_in
active_span_out = last_transaction_out - first_transaction_out
node_recency_in = global_max_block - last_transaction_in
node_recency_out = global_max_block - last_transaction_out
in_out_degree_ratio = degree_in / max(degree_out, 1)
in_out_amount_ratio = total_received / max(total_sent, 1)
```

---

## 7. Splits

文件：

```text
src/btcaml/data/splits.py
```

支持：

```text
random_stratified
classwise_temporal
global_temporal
leakage_control_temporal
```

### 7.1 `random_stratified`

用于和旧结果对齐。

### 7.2 `classwise_temporal`

每类内部排序：

```text
train 60%, val 20%, test 20%
```

保证每类有样本。

### 7.3 `global_temporal`

全体 labeled nodes 排序，模拟真实未来预测。

注意：需要检测是否有某些类别训练集为空。

### 7.4 `leakage_control_temporal`

后续严格版本：

```text
train graph: edge_time <= train_cutoff
val graph: edge_time <= val_cutoff
test graph: edge_time <= test_cutoff
```

可先不作为默认。

---

## 8. Model Interface

### 8.1 BaseModel

`src/btcaml/models/base.py`

```python
class BaseModel(nn.Module):
    def forward(
        self,
        x,
        edge_index,
        edge_attr=None,
        node_time=None,
        edge_time=None,
        batch=None,
        return_embeddings=False,
        return_explanations=False,
    ):
        raise NotImplementedError
```

旧模型必须兼容 `edge_attr=None`。

### 8.2 EdgeTemporalEncoder

`src/btcaml/models/encoders.py`

```python
class EdgeTemporalEncoder(nn.Module):
    def __init__(self, edge_in_dim, hidden_dim, out_dim, dropout=0.0):
        ...

    def forward(self, edge_attr):
        return edge_emb
```

### 8.3 ETD-SAGE

`src/btcaml/models/etd_sage.py`

结构：

```text
self channel
in-neighbor gated aggregation
out-neighbor gated aggregation
fusion MLP
classifier
```

第一版可以不用 MessagePassing 自定义，先用 `scatter_mean` 实现，方便调试。

伪代码：

```python
src, dst = edge_index
edge_emb = edge_encoder(edge_attr)

msg = node_proj(x[src])
gate = sigmoid(gate_mlp(edge_emb))
weighted_msg = gate * msg

h_in = scatter_mean(weighted_msg, dst, dim=0, dim_size=num_nodes)
h_out = scatter_mean(weighted_msg, src, dim=0, dim_size=num_nodes)
h_self = self_proj(x)

h = fusion(torch.cat([h_self, h_in, h_out], dim=-1))
logits = classifier(h)
```

注意：

- `h_in` 聚合 `j -> i` 到 dst；
- `h_out` 以 src 为中心聚合“从 i 出去的交易边”；
- 可做两套 gate：`gate_in` 和 `gate_out`；
- 必须支持 mini-batch。

---

## 9. Evaluation

### 9.1 Classification Metrics

文件：

```text
src/btcaml/evaluation/metrics.py
```

必须支持：

```text
accuracy
macro_f1
weighted_f1
per_class_precision
per_class_recall
per_class_f1
minority_macro_f1
sensitive_macro_f1
```

### 9.2 Ranking Metrics

文件：

```text
src/btcaml/evaluation/ranking.py
```

实现：

```text
AUPRC
Recall@TopK
Precision@TopK
Yield@Budget
```

`risk_score` 可以先用：

```python
risk_score = sum(prob[:, sensitive_class_ids])
```

不要一开始训练风险头。

### 9.3 Protocol Comparison Tables

输出：

```text
sampling_bias_table.csv
protocol_results.csv
main_results.csv
ablation_results.csv
multiseed_results.csv
```

---

## 10. Training

### 10.1 Trainer forward

必须统一：

```python
out = model(
    batch.x,
    batch.edge_index,
    edge_attr=getattr(batch, "edge_attr", None),
)
```

### 10.2 Loss

第一阶段只做：

```text
cross_entropy
weighted_ce
focal
balanced_softmax optional
```

不要先做：

```text
SupConLoss
MultiTask risk head
```

### 10.3 Early stopping

默认：

```text
val_macro_f1
```

可选：

```text
0.7 * macro_f1 + 0.3 * sensitive_macro_f1
```

---

## 11. Scripts

### 11.1 Audit

```bash
python scripts/audit_raw_labels.py --config configs/db/postgres.yaml
python scripts/audit_current_data.py --data data/processed/data.pt
python scripts/compare_label_coverage.py
```

### 11.2 Build Protocol Dataset

```bash
python scripts/build_protocol_dataset.py --config configs/data/protocol_B_label_preserving.yaml
python scripts/build_protocol_dataset.py --config configs/data/protocol_C_balanced_khop.yaml
python scripts/build_protocol_dataset.py --config configs/data/protocol_D_temporal_balanced.yaml
```

### 11.3 Compare Protocols

```bash
python scripts/compare_protocols.py \
  --protocols protocol_A_topk protocol_B_label_preserving protocol_C_balanced_khop protocol_D_temporal_balanced
```

### 11.4 Benchmark

```bash
python scripts/run_benchmark.py --config configs/experiment/protocol_benchmark.yaml
```

### 11.5 Main Model

```bash
python scripts/train.py data=protocol_C_balanced_khop model=etd_sage split=classwise_temporal train=focal seed=42
```

### 11.6 Ablation

```bash
python scripts/run_ablation.py --config configs/experiment/ablation_etd.yaml
```

### 11.7 Paper Tables

```bash
python scripts/export_paper_tables.py --results experiments/results
```

---

## 12. Config 示例

### 12.1 Protocol C

```yaml
protocol:
  name: class_balanced_khop
  target_num_nodes: 500000
  keep_all_labeled: true
  labels: all_11
  per_class_neighbor_budget: 30000
  supernode_degree_cap: 10000
  hops:
    default: 1
    PONZI: 2
    RANSOMWARE: 2
    MIXER: 2
    BRIDGE: 2
  background:
    enabled: true
    budget: 100000
    strategy: mixed_degree_pagerank_temporal

features:
  amount_transform: log1p_clip
  clip_quantile: 0.995
  scaler: robust
  fit_on: train
  edge_derived: true
  node_derived: true

split:
  type: classwise_temporal
  train_ratio: 0.6
  val_ratio: 0.2
  test_ratio: 0.2
  time_key: first_transaction_in
```

### 12.2 ETD-SAGE

```yaml
model:
  name: etd_sage
  params:
    hidden_channels: 128
    num_layers: 2
    dropout: 0.3
    edge_encoder_dim: 64
    gate_hidden_dim: 64
    aggregation: mean
    use_in_channel: true
    use_out_channel: true
    use_self_channel: true
```

---

## 13. Tests

必须新增：

```text
tests/test_label_map.py
tests/test_protocols.py
tests/test_splits.py
tests/test_feature_engineering.py
tests/test_models_forward.py
tests/test_metrics.py
```

### 13.1 Label map tests

检查：

```text
11 classes exactly
NONE mapped to -1
EXCHANGE not high_sensitive
PONZI/RANSOMWARE/MIXER high_sensitive
```

### 13.2 Protocol tests

检查：

```text
Protocol B/C/D keep all 11 labeled classes
No missing labeled category
selected nodes unique
edge_index endpoints all selected
```

### 13.3 Split tests

检查：

```text
train/val/test no overlap
classwise temporal order valid
global temporal order valid
no unlabeled nodes in supervised masks
```

### 13.4 Model tests

检查：

```text
MLP forward shape [N, 11]
GraphSAGE forward shape [N, 11]
ETD-SAGE forward shape [N, 11]
edge_attr optional compatibility
```

---

## 14. W&B / DVC / Hydra

### 14.1 W&B fields

每次实验必须 log：

```text
git_commit
protocol_name
protocol_manifest_hash
label_map_version
num_classes
num_nodes
num_edges
num_labeled
label_distribution
split_type
model_name
loss_name
seed
metrics
confusion_matrix
per_class_f1
ranking_metrics
```

### 14.2 DVC pipeline

最小 `dvc.yaml`：

```yaml
stages:
  audit_raw:
    cmd: python scripts/audit_raw_labels.py --config configs/db/postgres.yaml
    outs:
      - experiments/eda/raw_label_inventory.csv

  build_protocol_C:
    cmd: python scripts/build_protocol_dataset.py --config configs/data/protocol_C_balanced_khop.yaml
    deps:
      - src/btcaml/data/
      - configs/data/protocol_C_balanced_khop.yaml
    outs:
      - data/processed/protocol_C_balanced_khop.pt
      - data/processed/protocol_C_balanced_khop_manifest.json

  benchmark:
    cmd: python scripts/run_benchmark.py --config configs/experiment/protocol_benchmark.yaml
    deps:
      - data/processed/protocol_C_balanced_khop.pt
      - src/btcaml/
    metrics:
      - experiments/results/protocol_benchmark_metrics.json
```

---

## 15. 验收标准

### v2.1 完成标准

```text
1. raw_label_inventory.csv 存在
2. current_data_inventory.csv 存在
3. label_retention_report.csv 存在
4. 能明确输出 11 类 raw counts 与当前保留率
5. 当前 data.pt 被标记为 Protocol A
```

### v2.2 完成标准

```text
1. Protocol B/C/D 至少成功生成一个
2. 新 dataset 至少保留全部 11 类
3. manifest 记录采样参数、label distribution、time range
4. feature transforms 完整记录
```

### v2.3 完成标准

```text
1. MLP/XGBoost/GraphSAGE 可在 Protocol A/B/C 上跑通
2. 输出 protocol comparison table
3. 能证明 TopK 采样与 label-preserving 采样差异
```

### v2.4 完成标准

```text
1. ETD-SAGE forward 通过测试
2. ETD-SAGE 可训练
3. 与 GraphSAGE / EdgeTransformer 对比完成
4. 至少完成 edge/time/direction 三个消融
```

### v2.5 完成标准

```text
1. multi-seed 结果完成
2. paper tables 自动导出
3. W&B runs 完整
4. case study 至少 3 个
```

---

## 16. 禁止事项

不要：

```text
1. 不要直接把当前 data.pt 当最终主数据
2. 不要继续只做 5 类任务而忽略原始 11 类
3. 不要把 EXCHANGE 默认当高风险
4. 不要先做 MultiTaskSAGE
5. 不要先做 SupConLoss
6. 不要先做完整 HeteroGraphSAGE
7. 不要只报告 Weighted-F1
8. 不要只做 random split
9. 不要没有 manifest 就生成数据
10. 不要没有 multi-seed 就声称模型显著提升
```

---

## 17. Codex 当前下一步任务

请按顺序执行：

```text
Task 1: 新建 v2 目录结构中的 data audit 模块
Task 2: 实现 11 类 label map 和 risk group config
Task 3: 实现 audit_raw_labels.py / audit_current_data.py / compare_label_coverage.py
Task 4: 实现 DataProtocol base class
Task 5: 实现 Protocol B label_preserving
Task 6: 实现 Protocol C balanced_khop
Task 7: 实现 protocol manifest 和 comparison report
Task 8: 跑 Protocol B/C 小规模 dry-run
Task 9: 再进入模型改造
```

如果遇到性能问题，先做小规模 dry-run：

```text
target_num_nodes = 50,000
per_class_neighbor_budget = 2,000
```

通过后再扩大。

---

## 18. 最终工程目标

工程最终要支持以下论文命令：

```bash
make audit
make build-protocols
make benchmark
make train-main
make ablation
make multiseed
make paper-tables
```

最终输出：

```text
sampling_bias_table.md
main_results_table.md
ablation_table.md
multiseed_table.md
case_study_figures/
protocol_manifests/
wandb_report_link.txt
```

这才是论文服务型工程，而不是单次训练脚本。
