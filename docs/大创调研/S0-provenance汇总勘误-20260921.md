# S0 provenance `assigned_cells` 汇总勘误

日期：2026-09-21。适用协议：Gate 3A v1.3，S0-only。本记录不修改预注册窗口、过滤器、抽样规则、完整性阈值或三态判据；原始审计产物保持不变。

## 缺陷与范围

`scripts/research/audit_aws_btc_s0_provenance.py` 原版本 SHA-256 为 `b72a05d60c59309af1f8431be4dfc02e3137820db0d7a97f3e3fbfa34a6b42f2`。原版本在事件选择、恢复和逐事件记录构造之后，计算 `assigned_cells` 时对 cell 字典直接执行 `"|".join(cell)`，并用该字典与选择结果中的 tuple 比较。故 `assigned_cells` 错误地成为 `{"window_id|cutoff|future|profile":0}`。该表达式不参与候选生成、两阶段分配、恢复或阈值判断。

原审计文件为 `experiments/diagnostics/aws_btc_s0_provenance_audit_v1_3_20260912/provenance.json`，SHA-256 为 `ff35f121ae3da16ccf2834f7f2d13b6c6aa1220cabf28ad58102e9a9e3aae4f0`。冻结提取摘要 SHA-256 为 `470a68dede7d9ad3cf6595f9dd961d929b919db6116d0b0bf28ad7e5056a0ca3`；源 manifest SHA-256 为 `e32ad2f33ecbc184eb04159f0adbb22dd2a4a1a47f1e280cbbca699432d67f3d`。

## 勘误核验

保留原 JSON，仅新增 `experiments/diagnostics/aws_btc_s0_provenance_correction_v1_20260921/correction.json`，SHA-256 为 `de19a57d92cfda0c9b043802c9a996867cc150167f31443aa65fa83a0a3a42e7`。它绑定原 JSON 与 `data/raw/aws_btc_prefix_v0_1_20260910/s0_state/provenance_audit_v1_3.sqlite` 的 SHA-256；后者为 `a6803cd5a6ade4ce25b6c8283d6de6ccb8475fa00db6db4daee231f832372bd9a`。八个 `(window_id, filter_profile)` 单元各有 125 个全局唯一事件，每单元 125 个均恢复，共 1000/1000，超过预注册的 995/1000 下限。

独立核验重新计算每条事件的 rank、两阶段分配顺序及 `selection_sha256`，与 checkpoint 的冻结绑定一致；逐条比较原 JSON 与 checkpoint 的事件 ID、单元、恢复标志和原因，均一致；checkpoint 的 `quick_check=ok`，父对象 1890 个、父行 34,731,184 行与原 JSON 一致。反方审查在补充这些证据后确认错误限于输出汇总，撤回了完整重跑优先的建议。勘误脚本与 finalizer 分别实施校验；finalizer 对缺失或不一致的勘误、checkpoint、两次评估一律拒绝，不会静默使用错误汇总。

## 决策与边界

选择不可变 sidecar，避免为纯输出汇总错误重扫 34,731,184 行；原 provenance 和 checkpoint 均不覆盖。原审计对冻结交易的恢复真实性、候选总体计算仍依赖既有脚本与来源链；本勘误不声称重新独立扫描原始交易，也不替代两次结构评估及图哈希一致性检查。当前 S0 最终 Go/No-Go 尚未决定；`labels_read=false`、`models_authorized=false`。即使 S0 后续为 Go，也只允许起草独立 S1 协议，不授权标签读取、模型训练、Kaggle 上传或正式测试集访问。
