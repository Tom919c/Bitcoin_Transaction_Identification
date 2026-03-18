# 配置文件说明

## default.yaml

默认配置文件，包含以下配置项：

### data 数据配置
- `raw_db`: 原始数据库连接字符串
- `node_table`: 节点特征表名（默认 `node_features`）
- `edge_table`: 交易边表名（默认 `transaction_edges`）
- `processed_data_path`: 处理后的data.pt文件路径
- `num_classes`: 分类数量（6类）
- `label_map`: 标签映射文件路径

### preprocessing 预处理配置
- `target_labels`: 目标标签列表
- `chunk_size`: 数据库分块读取大小
- `zscore_params`: Z-score标准化参数
- `max_nodes`: 最大节点数量
- `val_ratio`: 从有标签节点中抽取验证集比例
- `test_ratio`: 从有标签节点中抽取测试集比例

### model 模型配置
- `name`: 模型名称（mlp/gcn/gat/sage/res_sage/appnp）
- `params`: 模型参数

### train 训练配置
- `seed`: 随机种子
- `device`: 训练设备
- `epochs`: 训练轮数
- `lr`: 学习率
- `weight_decay`: 权重衰减
- `batch_size`: 批次大小
- `neighbor_sizes`: 邻居采样数量
- `early_stopping_patience`: 早停耐心值
- `checkpoint_dir`: 检查点保存目录
- `log_dir`: 日志保存目录

### eval 评估配置
- `macro_f1_average`: F1计算方式
