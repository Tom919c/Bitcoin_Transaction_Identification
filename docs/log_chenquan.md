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