# 给 Codex 的启动提示词

请阅读并严格遵守以下文件：

```text
docs/01_NEXT_WORKPLAN_面向顶会.md
docs/02_CODEX_EXECUTION_GUIDE.md
docs/03_PHASE_CHECKLIST_AND_GATES.md
docs/05_PAPER_AND_ARTIFACT_SPEC.md
```

从 Phase 0 开始执行，不要跳阶段。

本阶段不是直接开发最终模型，而是进行“路线验证”。你需要先冻结当前结果，再量化 temporal edge heterophily，然后运行路线晋级实验，最后根据阈值决定是否把 Temporal OOD 方法作为主线。

绝对禁止修改以下标签语义：

```text
-1 = UNLABELED / 背景节点，不参与监督训练和评估
0~10 = 11 个监督类别
num_classes = 11
ignore_index = -1
INDIVIDUAL = 0，必须参与训练和评估
```

绝对禁止使用：

```text
y != 0
label > 0
ignore_index = 0
num_classes = 10
```

请先执行：

```powershell
python -m pytest -q
```

然后创建或更新：

```text
docs/EXPERIMENT_STATUS.md
docs/DECISION_LOG.md
docs/KNOWN_ISSUES.md
experiments/summary/current_result_manifest.md
```

每完成一个 Phase，输出：

```text
1. 代码改动摘要
2. 运行命令
3. 生成文件
4. 核心结果
5. 是否满足晋级阈值
6. 下一步建议
```

不要一口气做到论文结束。先完成 Phase 0、Phase 1、Phase 2。
