 代码框架创建完成。共创建了以下模块：     
                                                                                                                                                              - config/ - 配置文件（default.yaml + README.md）                                                                                                            - data/ - 数据处理模块（build_graph.py, features.py, utils.py）
  - models/ - 6个模型（MLP, GCN, GAT, GraphSAGE, ResGraphSAGE, APPNP）+ 基类                                                                                
  - training/ - 训练器、评估器、工具函数                                                                                                                    
  - interface/ - PyQt界面（main_window.py, data_loader.py）
  - scripts/ - 3个便捷脚本（预处理、训练、启动界面）
  - 根目录 - requirements.txt, README.md, .gitignore

  所有接口均按照文档规范实现，模块间通过 data.pt 文件解耦。load_raw_data 函数需要根据实际数据库结构补充实现。