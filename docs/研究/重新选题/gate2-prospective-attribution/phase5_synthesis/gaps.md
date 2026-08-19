# Gate 2 Phase 5：缺口与放弃清单

## P0：不解决就不能立项

1. **三个合格事件不存在**：当前 14 个事件中 0 个完整满足协议。
2. **BlackSuit target 尚未唯一定位**：金额/日期只是检索条件，不是地址真值。
3. **source provenance 不完整**：Ransomwhere/Showing the Receipts 缺逐条原始证据和 first-public time。
4. **本地图单位不匹配**：252M entity aliases 无 public address/tx lineage。
5. **历史网页状态不可复核**：没有连续 archive/feed snapshots 时，标签首次公开时间不可识别。

## P1：pilot 通过后才解决

1. 定义 `U_c` 的 activity、地址类型、dust 和 exchange/service 排除规则。
2. 预注册 purged temporal folds、source-family-held-out 和 case/address/cluster 去重。
3. 对 right censoring 使用固定 horizon、行政删失和 block/bootstrap confidence intervals。
4. 建立 root-evidence DAG 的人工双审与 disagreement protocol。
5. 选择 raw Bitcoin parser，并验证按 block height 重放的确定性与成本。

## P2：不能当作现成创新

- 未标注不是负例、confirmed yield 是下界：标准 PU/missing-data 事实。
- 终态信息不能用于历史预测：标准 temporal leakage。
- URL 转载必须按 group split：标准 grouped leakage 的领域实现。
- 不可观测跨链/VASP linkage 导致 target 不可识别：当前只是 no-free-lunch 草案，需最近邻理论检索。
- 给 provenance JSON/图加 hash/signature：`Fro19` 已提出。
- 新 GNN/path module：`Che23/Che25d/Gom22` 已把门槛抬高，且当前不是模型问题。

## 明确放弃

- 用 Elliptic/Elliptic++ 的固定标签宣称 future independent attribution。
- 把 entity type、abuse report、taint 扩张或论坛单次提及统一称为 illicit truth。
- 把未确认地址计为 benign 并报告 ROC/AUC/绝对 precision。
- 用相同 DOJ/FBI 调查生态的先后公告制造“独立验证”。
- 用 Upbit/Harmony 的 ETH seed 声称纯 Bitcoin 图可追踪到 BTC outputs。
- 用现有 252M 终态实体图回填历史 address-level outcome。
- 在 artifact Gate 失败时继续堆模型或降低事件数量门槛。

## 解锁条件

只有 BlackSuit 零模型 pilot 通过，且再找到至少两个互补事件满足同级证据标准，才进入预注册和基线实验。否则 Gate 2 关闭，转向可由现有数据真实支撑的新问题。
