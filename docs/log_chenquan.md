 代码框架创建完成。共创建了以下模块：     
                                                                                                                                                              - config/ - 配置文件（default.yaml + README.md）                                                                                                            - data/ - 数据处理模块（build_graph.py, features.py, utils.py）
  - models/ - 6个模型（MLP, GCN, GAT, GraphSAGE, ResGraphSAGE, APPNP）+ 基类                                                                                
  - training/ - 训练器、评估器、工具函数                                                                                                                    
  - interface/ - PyQt界面（main_window.py, data_loader.py）
  - scripts/ - 3个便捷脚本（预处理、训练、启动界面）
  - 根目录 - requirements.txt, README.md, .gitignore

  所有接口均按照文档规范实现，模块间通过 data.pt 文件解耦。load_raw_data 函数需要根据实际数据库结构补充实现。



  (MCM) D:\Code\VSCode\Bitcoin_Transaction_Identification>python d:\Code\VSCode\Bitcoin_Transaction_Identification\scripts\run_preprocessing.py
开始数据预处理...
配置文件: config/default.yaml
输出路径: ./data/processed/data.pt
阶段1/5: 统计全图特征分布并收集 BRIDGE 节点...
DECLARE CURSOR
阶段2/5: 计算 FinalScore 并筛选 TopK 节点...
DECLARE CURSOR
阶段3/5: 执行 BRIDGE 邻居增强...
TopK节点: 350000, BRIDGE节点: 70, BRIDGE邻居: 444
最终选中节点总数: 350258
阶段4/5: 读取选中节点特征与标签...
阶段5/5: 读取选中子图边并构建 edge_index...
数据已保存到: ./data/processed/data.pt
节点数: 350258, 边数: 17173503, 特征维度: 4
有标签节点数: 2961, train/val/test: 2961/592/592
数据预处理完成!

输出路径: ./data/processed/data.pt
阶段1/5: 统计全图特征分布并收集 BRIDGE 节点...
阶段2/5: 计算 FinalScore 并筛选 TopK 节点...
阶段3/5: 执行 BRIDGE 邻居增强...
TopK节点: 350000, BRIDGE节点: 70, BRIDGE邻居: 444
最终选中节点总数: 350258
阶段4/5: 读取选中节点特征与标签（保留全部节点特征）...
阶段5/5: 读取选中子图边（保留全部边特征）并构建 edge_index...
数据已保存到: ./data/processed/data.pt
节点数: 350258, 边数: 17173503, 节点特征维度: 19, 边特征维度: 6
有标签节点数: 2961, train/val/test: 2961/592/592
数据预处理完成!




  完成项：

   - models\sage.py：实现固定 3 层 GraphSAGE；前两层 LayerNorm -> ReLU -> Dropout(0.3)；forward(self, x, edge_index)
  返回 logits。
   - models\res_sage.py：实现共享残差 X_res 版本；第1/2层各自 SAGEConv -> LayerNorm -> ReLU -> +X_res -> 
  Dropout；第3层输出 logits（不加残差）。
   - training\trainer.py：CrossEntropyLoss(ignore_index=0)；默认 neighbor_sizes=[25,10,5]；mini-batch 仅对有标签
  seed（y!=0）计算损失；默认 lr 与配置对齐为 1e-3。
   - training\evaluator.py：评估时过滤 NONE=0；macro-F1 按业务类（1~num_classes-1）计算。
   - config\default.yaml：更新为 hidden_channels=128、dropout=0.3、lr=0.001、neighbor_sizes=[25,10,5]，并固定
  processed_data_path=D:\Code\VSCode\Bitcoin_Transaction_Identification\data\processed\data.pt。
   - scripts\train_model.py：默认数据路径同步为上述固定路径。
   - 已更新 plan.md，补充“当前进度（已完成/阻塞）”。


GraphSAGE:
训练完成! 最终评估:
Accuracy: 0.9409
Macro F1: 0.8773
Micro F1: 0.9409
Weighted F1: 0.9357

各类别指标:
类别           F1         Precision  Recall
------------------------------------------
NONE         0.0000     0.0000     0.0000
INDIVIDUAL   0.9666     0.9427     0.9917
BET          1.0000     1.0000     1.0000
GAMBLING     0.6780     0.8696     0.5556
EXCHANGE     0.7792     0.9375     0.6667
BRIDGE       0.9630     0.9286     1.0000



● 根因基本在代码里能对上（training/trainer.py、data/utils.py）：

   - BET 召回为 0：你用的是无权重 CrossEntropyLoss(ignore_index=0)，类别不平衡时模型会偏向大类（INDIVIDUAL），常见结果就是几乎不预测
  BET。
   - Loss 波动大：固定 lr=0.001、默认无 scheduler/梯度裁剪，再叠加 dropout，出现明显震荡是常见现象。
   - 还有个关键点：train_mask = labels != 0，而 val/test 从同一批有标签节点抽样，导致 train 与 val/test
  重叠（数据泄漏），指标会偏乐观且不稳定。

  如果你愿意，我可以直接帮你改成“互斥划分 + 分层抽样 + 类别权重/焦点损失 + LR 调度”。


  ● 已改完了：我已经落地了“互斥分层划分 + 类别不平衡损失 + 梯度裁剪 + 掩码自动修复”。

  你不一定要重新数据筛选。旧 data.pt 也能直接训练，因为 Trainer 现在会检测并自动修复 train/val/test 重叠掩码。

  如果你想把新划分持久化写回 data.pt，跑一次预处理即可（会复用现有阶段缓存）：

   python scripts/run_preprocessing.py --config config/default.yaml

  确保 preprocessing.resume_enabled: true、force_recompute: false。

  如果要“从某阶段开始重算”，删除该阶段及后续缓存文件（data\processed\checkpoints\stage_*.pt）再跑。仅改掩码时通常无需删 1~5
  阶段缓存。


开始数据预处理...
配置文件: config/default.yaml
输出路径: D:\Code\VSCode\Bitcoin_Transaction_Identification\data\processed\data.pt
阶段1/5: 统计全图特征分布并收集 BRIDGE 节点...
阶段1命中缓存: BRIDGE节点 70
阶段2/5: 计算 FinalScore 并筛选 TopK 节点...
阶段2命中缓存: TopK节点 350000
阶段3/5: 执行 BRIDGE 邻居增强...
阶段3命中缓存: 选中节点 350258
阶段4/5: 读取选中节点特征与标签（保留全部节点特征）...
阶段4命中缓存: 节点行数 350258
阶段5/5: 读取选中子图边（保留全部边特征）并构建 edge_index...
阶段5命中缓存: 边行数 17173503
数据已保存到: D:\Code\VSCode\Bitcoin_Transaction_Identification\data\processed\data.pt
节点数: 350258, 边数: 17173503, 节点特征维度: 19, 边特征维度: 6
有标签节点数: 2961, train/val/test: 1779/591/591
数据预处理完成!


GraphSAGE:
开始训练...
Epoch 10/300 | Loss: 1.0420 | Val F1: 0.4484
Epoch 20/300 | Loss: 0.8396 | Val F1: 0.5179
Epoch 30/300 | Loss: 0.7181 | Val F1: 0.5404
Epoch 40/300 | Loss: 0.6139 | Val F1: 0.5816
Epoch 50/300 | Loss: 0.5641 | Val F1: 0.5979
Epoch 60/300 | Loss: 0.5102 | Val F1: 0.6144
Epoch 70/300 | Loss: 0.4701 | Val F1: 0.6479
Epoch 80/300 | Loss: 0.4418 | Val F1: 0.6519
Epoch 90/300 | Loss: 0.4199 | Val F1: 0.6491
Epoch 100/300 | Loss: 0.4198 | Val F1: 0.6705
Epoch 110/300 | Loss: 0.4106 | Val F1: 0.6702
Epoch 120/300 | Loss: 0.3837 | Val F1: 0.6836
Epoch 130/300 | Loss: 0.3871 | Val F1: 0.6814
早停于 epoch 137

训练完成! 最终评估:
Accuracy: 0.7648
Macro F1: 0.6725
Micro F1: 0.7648
Weighted F1: 0.8020

各类别指标:
类别           F1         Precision  Recall
------------------------------------------
NONE         0.0000     0.0000     0.0000
INDIVIDUAL   0.8545     0.9787     0.7583
BET          0.7059     0.5625     0.9474
GAMBLING     0.3497     0.2315     0.7143
EXCHANGE     0.5773     0.4828     0.7179
BRIDGE       0.8750     0.7778     1.0000