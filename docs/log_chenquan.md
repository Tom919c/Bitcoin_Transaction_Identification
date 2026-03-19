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