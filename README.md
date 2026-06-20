# BTC-AML: 比特币交易图实体风险识别

> 面向国际顶会的研究项目：在大规模有向比特币实体交易图上，构建采样感知基准协议，分析方向异配与时间漂移机制，并验证方向感知图学习方法。

## 项目概述

- **任务**：11类长尾比特币实体识别 + 敏感实体风险排名
- **数据**：252M+ 原始节点，785M+ 边，34,098 个标注实体
- **方法**：方向感知边门控 GraphSAGE（EdgeGatedSAGE, EGS）
- **主结果**：CBK Macro-F1 0.6505，保守敏感排名 AUPRC 0.748

## 标签说明

- `-1` = 未标注背景节点（不参与训练和评估）
- `0~10` = 11个监督类别：INDIVIDUAL(0), BET(1), GAMBLING(2), EXCHANGE(3), MINING(4), PONZI(5), RANSOMWARE(6), FAUCET(7), MARKETPLACE(8), MIXER(9), BRIDGE(10)

## 项目目录结构

```
BTC_Transaction_Identification/
├── src/btcaml/                     # 核心包
│   ├── data/                       #   数据加载、标签映射、协议构建
│   ├── models/                     #   MLP, GraphSAGE, EdgeGatedSAGE
│   ├── training/                   #   训练器与损失函数
│   ├── evaluation/                 #   指标计算、排名评估
│   └── utils/                      #   随机种子等工具
│
├── scripts/                        # 实验脚本
│   ├── run_benchmark.py            #   主实验入口（MLP/SAGE/EGS）
│   ├── run_multiseed.py            #   多seed验证
│   ├── run_ood_single.py           #   OOD单实验（支持checkpoint恢复）
│   ├── run_ood_lite.py             #   OOD批量调度器
│   ├── verify_experiments.py       #   实验验证/复现脚本
│   ├── task_a_ranking.py           #   敏感实体排名计算
│   ├── task_b_temporal_analysis.py #   时间特征漂移分析
│   ├── task_c_confusion_study.py   #   混淆案例研究
│   ├── analyze_temporal_edge_heterophily.py  # 时间边异配分析
│   ├── export_paper_tables.py      #   论文表格导出
│   └── ...
│
├── tests/                          # 单元测试（pytest）
├── configs/                        # 配置文件
│
├── data/processed/protocols/       # 三套协议数据集
│   ├── class_balanced_khop.pt      #   主训练集（242K节点，1.2M边）
│   ├── temporal_balanced.pt        #   时间泛化测试集
│   ├── label_preserving.pt         #   标签保持对照集
│   └── *.metadata.json             #   元信息
│
├── experiments/
│   ├── summary/                    #   跨实验汇总（基线、消融、多seed）
│   ├── ood_lite/                   #   OOD门控实验结果
│   ├── ranking/                    #   敏感排名指标
│   ├── diagnostics/                #   协议诊断（异配、漂移、度数）
│   ├── case_studies/               #   混淆对案例分析
│   ├── route_validation/           #   路线决策文档
│   ├── paper_ready/                #   产物清单manifest
│   ├── experiment_registry.csv     #   所有实验索引（36条）
│   └── archive/                    #   历史实验归档（含checkpoint）
│
├── paper/                          # 论文素材
│   ├── tables/                     #   6张表格（md格式）
│   ├── figures/                    #   7张图表（png格式）
│   └── draft/                      #   5篇章节草稿
│
├── docs/                           # 项目文档（全部中文）
│   ├── 项目目录索引.md              #   全局导航
│   ├── 执行文档/                    #   Codex执行指南与任务规范
│   ├── 顶会研究规划/                #   研究规划文档包
│   ├── 研究/                        #   深度研究报告、路线评估
│   └── 迭代交接文档/                #   交接材料
│
├── .env                            # 环境变量（不提交）
├── .gitignore
├── Makefile                        # 常用命令
├── pyproject.toml
├── requirements.txt
└── README.md                       # 本文件
```

## 快速开始

```powershell
conda activate MCM
python -m pytest -q                           # 验证环境
python scripts/verify_experiments.py --smoke  # smoke验证关键实验
```

## 复现关键实验

```powershell
# 主实验（CBK，EGS，seed42）
python scripts/run_benchmark.py --data data/processed/protocols/class_balanced_khop.pt --models edge_gated_sage --seed 42 --run-name paper_egs_s42

# 多seed（3 seeds）
python scripts/run_multiseed.py --data data/processed/protocols/class_balanced_khop.pt --models edge_gated_sage --seeds 42 3407 1234

# 时间泛化
python scripts/run_benchmark.py --data data/processed/protocols/temporal_balanced.pt --models edge_gated_sage --seed 42 --run-name paper_temporal_s42

# 消融：无方向分离
python scripts/run_benchmark.py --data data/processed/protocols/class_balanced_khop.pt --models edge_gated_sage --seed 42 --run-name paper_no_dir --no-direction
```

## 核心实验结果

### 主结果（class_balanced_khop，3 seeds）

| 模型 | Macro-F1 | Minority-F1 | Weighted-F1 |
|---|---|---|---|
| MLP | 0.408 ± 0.001 | 0.441 ± 0.008 | 0.734 ± 0.002 |
| GraphSAGE | 0.579 ± 0.010 | 0.612 ± 0.009 | 0.895 ± 0.001 |
| **EGS** | **0.651 ± 0.014** | **0.667 ± 0.016** | **0.924 ± 0.004** |

### 消融（class_balanced_khop）

| 变体 | Macro-F1 | 说明 |
|---|---|---|
| GraphSAGE | 0.587 | 基线 |
| EGS（无方向） | 0.584 | 边门控单独无效 |
| **EGS（完整）** | **0.666** | 方向分离是核心（+0.082） |

### 时间泛化（temporal_balanced）

| 模型 | Macro-F1 | 说明 |
|---|---|---|
| MLP | 0.126 | |
| GraphSAGE | 0.190 | |
| EGS | 0.252 | 时间泛化仍是开放问题 |

### 敏感排名（保守：PONZI/RANSOMWARE/MIXER）

| 指标 | 值 |
|---|---|
| AUPRC | 0.748 ± 0.022 |
| Recall@1% | 0.346 ± 0.007 |
| Recall@5% | 0.827 ± 0.007 |
| AUROC | 0.987 ± 0.001 |

## 论文定位

**Benchmark + Mechanism + Direction-aware EGS + Conservative Ranking**

- 成立：采样偏差发现、11类协议、方向异配机制分析、EGS方法、保守排名
- 限制：时间OOD未解决、MIXER节点分类边界、扩展排名被简单类抬高
- 详见：`experiments/route_validation/final_route_after_phase4.md`


