# 项目状态：第一轮基线实验后

## 已完成的实验结果

| 数据集 | MLP Macro-F1 | SAGE Macro-F1 | SAGE 增益 | MLP Minority-F1 | SAGE Minority-F1 | SAGE 增益 |
|---|---:|---:|---:|---:|---:|---:|
| label_preserving | 0.3952 | 0.4627 | +0.0675 | 0.4227 | 0.4873 | +0.0646 |
| class_balanced_khop | 0.4114 | 0.5868 | +0.1754 | 0.4510 | 0.6239 | +0.1728 |
| temporal_balanced | 0.1255 | 0.1931 | +0.0675 | 0.1852 | 0.2448 | +0.0596 |

## 当前结论

第一轮基线实验已完成。下一步不是盲目训练更多普通 GNN，而是导出详细逐类结果并诊断时间/泛化失败原因。

## 本包中的代码更新

本包现在支持：

1. 逐类精确率 / 召回率 / F1 导出
2. 分类报告导出
3. 原始和归一化混淆矩阵导出
4. 节点级预测 CSV 导出
5. 从已有 checkpoint 进行事后详细评估
6. 从 experiments/runs/*/results.csv 生成基准汇总表
7. 移除旧的顶层模块和 GUI 代码

## 立即可用的本地命令

如果你之前的运行目录包含 checkpoint：

\\\powershell
python scripts/export_detailed_eval.py --run-dir experiments/runs/<目录名> --data data/processed/protocols/<协议>.pt --models mlp sage --device cpu
python scripts/summarize_benchmark_runs.py --runs-dir experiments/runs --out experiments/summary/baseline_protocol_comparison.csv
\\\

## 获得新详细数据后的下一步

在逐类表格和混淆矩阵可用后：

1. 识别 temporal_balanced 下哪些类别失败最严重。
2. 分析 PONZI / RANSOMWARE / MIXER / BRIDGE 是否与 INDIVIDUAL、EXCHANGE 或 BET 混淆。
3. 对比 class_balanced_khop vs temporal_balanced 各类别表现。
4. 然后实现 EdgeGatedSAGE / ETD-SAGE，明确目标：改善时间和少数类失败情况。
