# N1 Flow Certificate Gate-2 Pilot v0.2

## 状态与目的

本协议是 Gate 2 的选题判别，不是 Gate 3A 预注册，也不表示 N1 已成为主方向。唯一目标是判断：在不引入地址所有权、实体聚类或风险标签时，Bitcoin UTXO 账本守恒约束是否允许对 source-conditioned 下游量给出非平凡、可复查的稳定性证书。

本 Pilot 不训练 GNN，不评价 illicit/fraud/AML，不把未标注对象当负类，也不声称恢复真实 satoshi 历史、支付意图或主体控制关系。

## 研究问题与 estimand

给定互不重叠的 source UTXO 集合、固定交易 DAG 和观察边界，令 `completion` 表示满足以下条件的 fractional source-mass 分配：

1. 每笔交易输入、输出与手续费按 satoshi 守恒；
2. source mass 非负且不超过对应 UTXO 容量；
3. 输入 source mass 可以在本交易所有输出及 fee sink 间任意分割；
4. fee sink 为终端；窗口边界的未花费输出为 right-censored 终端；
5. 不加入 change、ownership、CoinJoin 参与者或地址聚类假设。

对预先指定的线性量 `g`，identified interval 为：

```text
[min_completion g, max_completion g]
```

threshold `g >= tau` 的证书规则固定为：

- 下界 `>= tau`：`certified_true`；
- 上界 `< tau`：`certified_false`；
- 其他：`unresolved_under_ledger_only_provenance`。

pairwise ranking 必须联合优化 `g_a - g_b`，不得把两个独立 marginal interval 当成 exact ranking interval。严格下界 `> 0` 才认证 `a > b`；存在平局时保持 unresolved。

## 标准数学结果的边界

以下仅作为工具，不列为创新：transportation polytope、整数边际下的 totally-unimodular 极点、单交易 sharp source-mass interval、min-cost flow/LP 上下界、generic threshold/ranking robustness。

单交易总输入为 `V`、source mass 为 `A`、目标输出容量为 `y` 时，标准 sharp interval 是：

```text
[max(0, A + y - V), min(A, y)]
```

可能的论文贡献只能来自：交易间耦合 completion set 上的任务级证书、可解释的可识别结构条件，以及相对 deterministic taint rules 的非平凡决策差异。

## 分阶段数据协议

### A0 — 手工合成自检

锁定三个不可调例子：

1. `S=6, clean=4 -> X=7, Y=2, fee=1`：`X=[3,6]`、`Y=[0,2]`；
2. `S=10 -> X=9, fee=1`：`X=[9,9]`；
3. `A=1, clean=1 -> P=1,Q=1; P->D; Q->E`：`D,E` 各为 `[0,1]`，但联合量 `D+E=[1,1]`。

任何断言失败都属于实现错误，不能进入真实数据。

### A1 — locked synthetic

独立生成 48 个小型 ledger instance：`unique-00..15`、`mixed-00..15`、`symmetric-00..15` 三族各 16 个。实例由 `SHA256("N1-A1-v1|family|index|field|slot")` 确定参数，不使用运行时随机数、拒绝采样或按结果替换实例。每个实例固定一个 source boundary UTXO、六个 depth-2 终端 `D0..D5`、四笔严格有向交易；共同评估全部六个终端。

三族的角色不同，必须分开报告：

1. `unique`：source 经单输入分拆，预期六个终端均为点区间；用于检查守恒、DAG 和目标边实现；
2. `mixed`：source 与 clean boundary inputs 在两层中混合；允许出现任意 certified rate，只用于观察非退化行为；
3. `symmetric`：对称等值混合，预期所有终端为完整歧义区间且严格排序均 unresolved；用于检查算法是否会错误强制归因。

因此，对称族的低 certified-decision rate 是正确拒证，不是研究 No-Go。A1 只验证 solver 正确性、保守性与退化条件，不估计现实 Bitcoin utility。开发例不得进入这 48 个实例，三族不得 pooled 后解释成现实发生率。

主 threshold 固定为 `tau=ceil(source_value/100)`。实例级指标固定为：

```text
threshold CDR = 六个终端中 certified_true/false 的比例
normalized width(d) = (upper-lower) / min(source_value, value(d))
pair CDR = 30 个有序终端对中严格次序被认证的比例
```

独立 oracle 按交易顺序枚举所有有界整数 source-mass compositions，不能调用 `FlowCertificate`、NetworkX 或复用候选求解图；它对所有终端 interval、`t=0..source_value` 的 threshold 状态和 30 个有序 pairwise difference interval 给出真值。A1 不实现 strict Top-3，明确记录为 `not_implemented`，不得计入通过率。

A1 在 satoshi 整数格上枚举；由于该单商品网络流约束在整数容量下具有整数极点，其线性 extrema 与前述 fractional LP 相同。枚举设置预先固定的 completion 资源护栏；触发即 hard failure 且不写部分结果，不得跳过或替换实例。

### B0 — 单窗工程 smoke

一个 100-block 连续窗口只验证解析、守恒、运行时间和错误处理；统计独立单位为 1，不能支持选题晋级。公共 API 只允许用于该 smoke，并保存 URL、block hash、响应 hash 与获取时间；不能替代 Bitcoin Core 重放。

### B1 — Gate-2 现实判别

至少 8 个互不重叠、彼此相距至少 10,000 blocks 的 100-block 窗口，覆盖至少 4 个历史时期。正式入口必须能由 Bitcoin Core/raw blocks 重放，保留 Core 版本、区块 hash 与 manifest。

每窗 source 选择冻结为：前 20 blocks 产生、在第 21–90 blocks 首次花费、非 coinbase、正值且 `>=1,000,000 sat` 的标准可花费 UTXO；按 `SHA256(window_id || outpoint)` 取前 50 个。不得按路径有趣程度、标签或 solver 成功选择。

固定 `H=2` transaction transitions，`tau_s=ceil(value_s/100)`，候选排名 `K=10`。窗口外历史/未来、解析缺失、solver 超时或非最优一律输出 unknown，不能输出稳定否定。

v0.2 尚不授权执行 B1。真实窗口前必须在新版本冻结：每个 source 的候选终端全集、参考排序及 outpoint tie-break、strict Top-10 集合判据、reachability 的 endpoint/path 语义，以及 source-conditioning comparator 的 feasible set、共同分母和 timeout 处理。冻结前，B1 的相关数值门槛不可执行或解释。

## Baselines

1. observed UTXO spend graph，不补 latent input-output allocation；
2. proportional/Haircut point completion；
3. FIFO point completion；
4. 不使用 source-conditioned DAG 缩紧的局部/源无关 bound；
5. 小组件 exact oracle，用于 correctness control，不作为竞争方法。

任何有限 taint-rule 集合都不能冒充“all compatible completions”。

## 主要指标

- false-certificate rate；
- certified-decision rate；
- normalized certificate width；
- source-conditioning 对 certified rate 的增益和 width 降幅；
- strict Top-10 set stability；
- stable yes / stable no / unknown mass-reachability 比例；
- runtime、timeout rate 与 unknown 原因。

真实数据以窗口为独立单位，报告每窗结果与中位数/范围；不得把同窗 source、UTXO、path 或 solver seed 当独立样本。

## 预先固定的停止与晋级门槛

### 硬 No-Go

- exact oracle 发现任一 false threshold、ranking 或 reachability certificate；
- 非最优、超时、解析缺失或边界截断被转成确定答案；
- A1 任一实例不守恒、无法完整枚举，或 oracle 与候选 solver 的 interval、任一 threshold 或 pairwise difference 不一致；
- `unique` 任一终端不是点区间，或 `symmetric` 任一终端/严格排序被错误认证；
- 8 个真实窗中至少 7 个在任一核心证书上的 certified rate `<10%`；
- source-conditioning 的中位 certified-rate 增益 `<10` percentage points，且 width 降幅 `<20%`；
- 只有单一 100-block 真实窗；此时最多保留 engineering smoke，不得晋级；
- 结果退化为局部 transportation interval 或既有 taint-rule comparison；
- 结论需要真实 ownership/illicit truth 才能成立。

### 最低条件 Go

- A1 exact oracle 为 0 false certificates，全部 48 个实例完整枚举且满足各族预期；该结果只允许进入真实数据 smoke，不能单独使 N1 晋级；
- 至少 6/8 真实窗口同时满足：threshold certified rate `>=25%`、strict Top-10 stability `>=20%`、stable reachability `>=30%`、source-conditioning `+15 pp` 且 width `-25%`、solver timeout/unknown `<=5%`。

即使达到 Go，也只允许进入更大现实审计与理论性质卡，不支持部署、犯罪归因或 AML 主张。

## 当前资源判断

- 仓库的 252M 终态 entity graph 与 PostgreSQL dump 缺少 txid/outpoint/raw block，不能用于本 Pilot；
- 本机当前没有 `bitcoind` 或 `bitcoin-cli`；
- 已安装 NetworkX 与 SciPy，不新增求解依赖；
- 现有 `scripts/research/scan_exact_bitcoin_outputs.py` 可复用公共 API 获取与自检逻辑，但只能服务工程 smoke；
- Stage A0 采用整数容量的 NetworkX min-cost flow，依靠网络流整数性避免把浮点 gap 当证书。

## 2026-08-24 执行记录

- A0：通过。三个锁定手工例均满足预期，另用独立整数穷举 oracle 检查单交易不同 source mass 下的上下界；
- 实现：`src/btcaml/analysis/flow_certificate.py`，只包含当前 A0 所需的账本校验、联合线性上下界、阈值/严格排序证书和 Haircut 点估计；
- 验证：定向测试与仓库全量测试均通过，静态检查通过；
- B0：未执行。公共区块 API 已确认具有输入、输出和值字段，但缺少本地 Bitcoin Core/raw-block 可重放链路；即使完成一个窗口也只能视为 parser/engineering smoke；
- Gate 状态：N1 仍为 conditional candidate，尚未 Go。A1 的 48 个锁定 synthetic 和 B1 的 8 个跨时期窗口均未完成，不能据此声称真实 Bitcoin 上证书非平凡或方向值得晋级。

## v0.2 修订说明（A1 执行前）

v0.1 将三族统一施加 certified-rate 门槛，和 `symmetric adversarial` 作为正确拒证控制的目的冲突。v0.2 在尚未生成或查看 A1 结果时修正该问题，冻结确定性实例 ID、参数哈希、共同 targets、独立 oracle、指标和族特定断言。B1 的现实效用门槛保持不变，但其 target、ranking、reachability 与 comparator 定义仍须在执行前另行冻结。
