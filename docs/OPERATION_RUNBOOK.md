# BTC AML 项目运行顺序与产物归档

## 当前主线

1. 原始库审计：确认 11 类标签与时间分布。
2. 协议数据集构建：`label_preserving`、`class_balanced_khop`、`temporal_balanced`。
3. 数据集检查：确认 `-1=UNLABELED`，`0~10=11类`，split 无重叠，temporal split 合理。
4. 第一轮模型实验：先跑 `MLP` 与 `GraphSAGE`，不要先堆复杂模型。
5. 后续再跑 `ETD-SAGE` / edge-aware ablation。

## 命令顺序

```powershell
python scripts/audit_raw_labels.py --config configs/data/raw_db.yaml
python scripts/build_protocol_dataset.py --config configs/data/label_preserving.yaml
python scripts/build_protocol_dataset.py --config configs/data/class_balanced_khop.yaml
python scripts/build_protocol_dataset.py --config configs/data/temporal_balanced.yaml
python scripts/compare_protocols.py --data-dir data/processed/protocols
python scripts/inspect_protocol_dataset.py --data-dir data/processed/protocols
```

第一轮 smoke test：

```powershell
python scripts/run_benchmark.py --data data/processed/protocols/class_balanced_khop.pt --models mlp --smoke --device cpu
```

第一轮正式 baseline：

```powershell
python scripts/run_benchmark.py --data data/processed/protocols/class_balanced_khop.pt --models mlp sage --device cpu
python scripts/run_benchmark.py --data data/processed/protocols/label_preserving.pt --models mlp sage --device cpu
python scripts/run_benchmark.py --data data/processed/protocols/temporal_balanced.pt --models mlp sage --device cpu
```

## 产物归档规则

- 稳定结果：`experiments/results/...`
- 时间戳归档：`experiments/runs/YYYYMMDD_HHMMSS_task/...`
- 最近一次结果副本：`experiments/latest/<task>/...`
- 数据集旁路元数据：`data/processed/protocols/*.metadata.json`

## 标签规则

新协议数据集：

```text
-1 = UNLABELED，不参与训练和评估
0~10 = 11 个监督类别
```

旧 `data.pt`：

```text
0 = NONE
1~5 = 旧 5 类监督标签
```

所以新主线优先使用 `src/btcaml/...` 和 `scripts/run_benchmark.py`。旧入口 `scripts/train_model.py` 仅保留兼容。
