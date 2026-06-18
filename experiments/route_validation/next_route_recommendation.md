# Next Route Recommendation

## A. 已成立，可以写入论文主贡献的内容

1. **Benchmark + Mechanism Analysis**：三套协议、完整 baseline 矩阵（MLP/SAGE/EGS x 3 seeds）、方向消融、时间特征消融、多 seed 稳定性验证、temporal edge heterophily 诊断——全部完成且可复现。
2. **Direction-aware EGS 方法实证**：方向分离在 CBK 上 +0.082 Macro-F1、temporal 上 +0.093，3 seed 一致，证据扎实。
3. **Conservative Risk Ranking 应用贡献**：Conservative AUPRC=0.75、AUROC=0.99、Recall@5%=0.83。对高敏感 AML 类（PONZI/RANSOMWARE/MIXER）的排序能力已确认，可以作为应用贡献写入论文。
4. **Temporal edge heterophily 量化指标**：同类邻居 <15%（MIXER 0.4%）、未标注邻居 77-95%、方向入出差异——这些指标本身就是 benchmark 级贡献。

## B. 已发现但不能夸大，只能写为 challenge / limitation 的内容

1. **Temporal OOD 未解决**：最优 temporal Macro-F1=0.2675，与 random 的 0.65 差距 0.38，当前方法无法弥合。
2. **MIXER 节点分类边界**：0.4% 同类邻居、16 个测试节点，节点级分类可能根本不够，但样本太少无法验证子图方法。
3. **Extended ranking 可能被 BET 抬高**：Extended AUPRC=0.99 vs Conservative AUPRC=0.75，差距 0.24，说明 BET 等容易类主导了排序信号。论文中应区分报告 conservative 和 extended。
4. **时间边特征的伪相关**：temporal_balanced 上 KS=0.57 的特征漂移说明 random split 中的时间特征可能是伪相关，不能作为方法贡献。

## C. 需要下一轮实验才能决定的内容

1. **Temporal OOD 轻量原型**：topology-aware reweighting 或 temporal edge filtering——如果能在 temporal 上稳定提升 +0.03，可以成为方法贡献；否则只能作为探索性实验。
2. **Conservative ranking 的 Recall@1% 优化**：当前 Recall@1%=0.35，如果通过更好的 loss 或 reweighting 能提升到 0.5+，应用价值会显著增强。
3. **RANSOMWARE/PONZI 的定向资金流模式分析**：RANSOMWARE->INDIVIDUAL 混淆为 0，说明方向特征非常有效——值得深入分析这个成功案例。

## D. 暂停或不建议继续投入的内容

1. **子图 GNN / Subgraph reasoning**：MIXER 仅 16 个测试节点，无法进行有意义的子图方法评估。建议作为 Future Work。
2. **Focal Loss / 高级损失**：gamma=2 已经失败（Macro-F1 降至 0.33），不建议继续尝试。
3. **TGN / Causal GNN / Graph Foundation Model**：复杂度过高，与当前数据规模和问题定义不匹配。
4. **Open-world / PU Learning**：当前 -1 节点是背景上下文，不等价于未知类，任务定义不成立。

## 最终路线建议（多选）

按优先级排序：

1. **Benchmark + Mechanism Analysis 主线**（必须）：所有材料已就绪，直接进入论文材料生成。
2. **Direction-aware EGS 方法实证主线**（必须）：消融实验完整，方向聚合的价值已被证明。
3. **Conservative Risk Ranking 应用贡献**（推荐）：AUPRC=0.75 足以支撑应用 claim，但需配合 case study 验证。
4. **Temporal OOD 轻量原型**（可选，需验证）：如果实现 topology-aware reweighting 并在 temporal 上获得 +0.03 提升，可升级为方法贡献。否则降为 limitation。
5. **Node-to-Subgraph Boundary / Future Work**（仅写入论文 Future Work 章节）：MIXER 子图问题留待后续研究。