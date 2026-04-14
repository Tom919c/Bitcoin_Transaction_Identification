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
- `resume_enabled`: 是否启用断点续跑（默认 `true`，优先复用缓存）
- `checkpoint_dir`: 预处理阶段缓存目录（保存各阶段中间结果）
- `force_recompute`: 是否强制全量重算（`true` 时忽略缓存）
- `zscore_params`: Z-score标准化参数
- `max_nodes`: 最大节点数量
- `val_ratio`: 从有标签节点中抽取验证集比例（分层抽样，且与 train/test 互斥）
- `test_ratio`: 从有标签节点中抽取测试集比例（分层抽样，且与 train/val 互斥）

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
- `loss`: 损失函数类型（`cross_entropy` / `weighted_ce` / `focal`）
- `focal_gamma`: Focal Loss 的 gamma 参数（仅 `focal` 生效）
- `class_weight_power`: 类别权重指数，按 `((mean_count / class_count) ** power)` 计算
- `class_weight_cap`: 类别权重上限，抑制极端小类权重过大
- `grad_clip_norm`: 梯度裁剪阈值，`0` 表示关闭
- `scheduler`: 学习率调度器类型（`null` / `step` / `cosine` / `plateau`）
- `scheduler_factor`: `plateau` 学习率衰减系数
- `scheduler_patience`: `plateau` 等待轮数
- `early_stopping_patience`: 早停耐心值
- `checkpoint_dir`: 检查点保存目录
- `log_dir`: 日志保存目录

### eval 评估配置
- `macro_f1_average`: F1计算方式

### tuning 调参配置
- `strategy`: 搜索策略（`random` / `grid`）
- `max_trials`: 最大候选组合数量
- `use_mini_batch`: 调参是否使用 mini-batch（若环境无 `pyg-lib/torch-sparse`，会自动回退 full-batch）
- `resume`: 是否启用调参断点续跑
- `progress_file`: 调参进度文件路径（为空则默认 `output_dir/sage_tuning_progress.json`）
- `start_trial`: 本次执行起始 trial 序号（1-based，可用于分段跑）
- `end_trial`: 本次执行结束 trial 序号（1-based）
- `seeds`: 本次执行使用的随机种子列表（可临时改为单种子提速）
- `seed`: 随机采样候选配置的随机种子
- `output_dir`: 调参结果输出目录
- `space`: 超参数搜索空间（支持离散列表，如 `lr`, `dropout`, `hidden_channels`, `neighbor_sizes`, `loss` 等）
