# 中期报告可视化

本目录用于生成 `docs/中期可视化.md` 要求的论文图，统一导出为 **PDF**。

## 生成命令

```bash
python visualization/generate_midterm_figures.py --config config/default.yaml
```

如需指定数据文件：

```bash
python visualization/generate_midterm_figures.py --data-path data/processed/data.pt
```

如需强制用示意拓扑图（不从 data.pt 抽样）：

```bash
python visualization/generate_midterm_figures.py --force-synthetic-topology
```

如需进一步降低拓扑图密度（推荐论文排版）：

```bash
python visualization/generate_midterm_figures.py --max-topology-nodes 45 --max-topology-edges 70
```

## 输出文件

默认输出到 `visualization/output/`：

- `fig_model_performance_by_class.pdf`
- `fig_model_summary_metrics.pdf`
- `fig_topology_patterns.pdf`

## 当前真实子图抽样逻辑

1) 在真实 `data.pt` 中选取两类 **典型 seed** 节点（不是单纯总度最高）：
- 正常流：优先 `EXCHANGE/INDIVIDUAL/BRIDGE`，倾向“入出度较平衡”的枢纽型节点。
- 可疑流：优先 `GAMBLING/BET`，倾向“出度明显大于入度”的扩散型节点（更接近 peeling-like 结构）。

2) 以 seed 做 `k-hop` 子图抽样（默认 2-hop）。

3) 若节点过多，按“离 seed 的距离 + 节点度”裁剪到 `--max-topology-nodes`。

4) 若边过多，保留代表性边：
- seed 直接相关边
- BFS 主干边
- 再按结构距离和节点度补齐，直到 `--max-topology-edges`。

5) 绘图布局不再用纯弹簧布局：
- 正常子图：径向层次布局（更像“中心-辐射”）
- 可疑子图：分层链式布局（更像“逐层剥离”）

这样可以显著减少外围长边，让两类拓扑一眼可区分。

