代码框架创建完成。共创建了以下模块：  
 - config/ - 配置文件（default.yaml + README.md） - data/ - 数据处理模块（build_graph.py, features.py, utils.py）

- models/ - 6个模型（MLP, GCN, GAT, GraphSAGE, ResGraphSAGE, APPNP）+ 基类
- training/ - 训练器、评估器、工具函数
- interface/ - PyQt界面（main_window.py, data_loader.py）
- scripts/ - 3个便捷脚本（预处理、训练、启动界面）
- 根目录 - requirements.txt, README.md, .gitignore

所有接口均按照文档规范实现，模块间通过 data.pt 文件解耦。load_raw_data 函数需要根据实际数据库结构补充实现。

2026-03-25 APPNP 复现修复（阶段一）

- 评估口径统一到可配置标签集合，默认使用 5 个业务类：INDIVIDUAL、BET、GAMBLING、EXCHANGE、BRIDGE。
- 训练入口与训练器新增 APPNP + mini-batch 保护逻辑，默认自动切回全图训练。
- 训练损失新增训练集类别权重，缓解类别不平衡导致的少数类 F1 归零问题。
- 数据划分从随机切分升级为分层切分，并输出 train/val/test 各类别计数用于健康检查。
