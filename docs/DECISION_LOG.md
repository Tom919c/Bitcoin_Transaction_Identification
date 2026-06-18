# 决策日志

## 2026-06-17 Phase 0 决策

### 已完成
- 环境检查：pytest 9/9 通过
- 协议数据验证：label_preserving.pt、class_balanced_khop.pt、temporal_balanced.pt
- 代码中无旧标签逻辑
- 4 个历史 run 均有 best.pt checkpoint
- 脚本功能正常

### 决策
- 继续 Phase 1

## 2026-06-17 Phase 1 决策

### 已完成
- 导出所有 3 个 run 的详细逐类指标（6 个模型评估）
- 生成 baseline_protocol_comparison.csv/.md
- 生成 baseline_protocol_analysis.md

### 关键结果
- class_balanced_khop：SAGE Macro-F1=0.5868，比 MLP 高 +0.1754
- temporal_balanced：SAGE Macro-F1=0.1931，时间崩溃严重

### 决策
- 继续 Phase 2 协议诊断

## 2026-06-17 Phase 2 决策

### 已完成
- 计算 class_balanced_khop 和 temporal_balanced 的逐类度数统计
- 分析入边邻居标签分布（每类采样 200 节点）
- 分析所有 11 类的时间偏移
- 诊断报告：experiments/summary/protocol_diagnostics_report.md

### 关键结果
- 高异配性：MIXER 同类比例 0.4%，BET 1.4%，RANSOMWARE 2.1%
- 77-95% 入边邻居未标注
- temporal_balanced：GAMBLING train 中位数 275K vs test 605K（偏移 +329K 区块）
- 边特征可用：11 维，包含 reveal、last_seen、total、金额、duration、recency、frequency

### 解读
- 边门控消息传递对过滤异配邻居至关重要
- 方向（入/出）聚合可利用资金流非对称性
- 边特征中的时间信号可帮助缩小时间差距
- 需要类别均衡损失处理 MIXER（80）、BRIDGE（70）样本

### 决策
- 跳过 Phase 3（额外 GNN 基线），直接进入 Phase 4 EdgeGatedSAGE
- EdgeGatedSAGE 是最高优先级模型

## 2026-06-18 Phase 4 决策

### 已完成
- 实现 EdgeGatedSAGE（src/btcaml/models/edge_sage.py）
- 注册到模型注册表（edge_gated_sage、egs）
- smoke test 通过
- class_balanced_khop 完整训练（200 epochs，best epoch 178）
- temporal_balanced 完整训练（200 epochs，best epoch 177）
- 导出两个 run 的详细逐类指标

### 关键结果

class_balanced_khop：
- EGS test macro=0.6657 vs SAGE 0.5868（+0.0789）
- 最大提升：FAUCET +0.276、PONZI +0.209、MINING +0.160
- 唯一下降：MIXER -0.040

temporal_balanced：
- EGS test macro=0.2565 vs SAGE 0.1931（+0.0634）
- EGS test weighted=0.5715 vs SAGE 0.3515（+0.2200）
- 最大提升：INDIVIDUAL +0.310、MINING +0.224、BRIDGE +0.127
- 下降：PONZI -0.101

### 解读
- EdgeGatedSAGE 在两个协议上均有显著提升，验证了边门控和方向聚合的有效性
- class_balanced_khop 上的提升集中在 AML 敏感小类（PONZI、FAUCET、RANSOMWARE）
- temporal_balanced 上 INDIVIDUAL 和 MINING 大幅提升，但 PONZI 下降
- MIXER 在两个协议上均未提升，可能需要专门的长尾损失

### 决策
- EdgeGatedSAGE 作为当前最优模型，进入 Phase 7 消融实验
- 消融目标：验证边属性、方向聚合各自的贡献
- 同时在 class_balanced_khop 上尝试 focal loss 改善 MIXER

### 下一步命令
- 消融：去掉方向（use_direction=False）
- 消融：去掉边门控（退化为普通 SAGE）
- 尝试 focal loss
