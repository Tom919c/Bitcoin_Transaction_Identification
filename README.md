# 比特币交易节点分类系统

基于图神经网络的比特币交易节点分类项目。

## 项目结构

```
project/
├── config/                 # 配置文件
├── data/                   # 数据处理模块
├── models/                 # 模型定义模块
├── training/               # 训练与评估模块
├── interface/              # 可视化界面模块
├── experiments/            # 实验记录
├── scripts/                # 便捷脚本
├── requirements.txt        # 依赖库
└── README.md               # 项目说明
```

## 安装依赖

```bash
pip install -r requirements.txt
```

## 使用方法

### 1. 数据预处理

```bash
python scripts/run_preprocessing.py --config config/default.yaml
```

### 2. 模型训练

```bash
# 全图训练
python scripts/train_model.py --config config/default.yaml

# Mini-batch训练
python scripts/train_model.py --config config/default.yaml --mini-batch

# 从已有checkpoint继续训练（断点续训）
python scripts/train_model.py --config config/default.yaml --resume-checkpoint experiments/checkpoints/final_model.pt
```

### 2.1 使用 W&B 记录训练过程

1) 安装依赖：

```bash
pip install -r requirements.txt
```

2) 在 `config/default.yaml` 中开启：

```yaml
wandb:
  enabled: true
  project: "bitcoin-transaction-identification"
  entity: null
  run_name: null
  mode: "online"   # 无网环境可改为 offline
  watch_model: false
```

3) 直接运行训练命令（全图或 mini-batch 均可），训练过程中会按 epoch 上报 loss/F1/lr。

### 3. 启动界面

```bash
python scripts/launch_interface.py
```

## 标签说明

| 编码 | 标签 | 说明 |
|------|------|------|
| 0 | NONE | 未知类型 |
| 1 | INDIVIDUAL | 个人用户 |
| 2 | BET | 博彩 |
| 3 | GAMBLING | 赌博 |
| 4 | EXCHANGE | 交易所 |
| 5 | BRIDGE | 桥接服务 |

## 支持的模型

- MLP: 多层感知机
- GCN: 图卷积网络
- GAT: 图注意力网络
- GraphSAGE: 图采样聚合
- ResGraphSAGE: 残差GraphSAGE
- APPNP: 近似个性化传播
