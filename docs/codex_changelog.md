# Codex 变更记录

> 本文件记录 Codex 对项目代码的所有修改，便于与 GPT 同步。
> 每条记录包含：日期、文件、修改内容、原因。

---

## 2026-06-14

### 修改 1：修复 save_json 的 numpy 类型序列化问题

- **文件**：`src/btcaml/utils/io.py`
- **问题**：`audit_raw_labels.py` 运行时崩溃，报 `TypeError: Object of type int64 is not JSON serializable`。原因是 `audit_raw_database` 从 PostgreSQL 查询返回的整数经 pandas 传递后是 `numpy.int64` 类型，Python 标准库 `json.dumps` 无法序列化。
- **修改内容**：
  1. 新增 `_json_default(obj)` 函数，作为 `json.dumps` 的 `default` 回调，自动将 `numpy.integer` 转为 `int`，`numpy.floating` 转为 `float`，`numpy.ndarray` 转为 `list`。
  2. `save_json` 中的 `json.dumps` 调用增加 `default=_json_default` 参数。
- **影响范围**：所有调用 `save_json` 的地方（`audit_raw_labels.py`、`build_protocol_dataset.py` 等）均受益，无需单独修改。

### 修改 2：补充缺失依赖 tabulate

- **文件**：`requirements.txt`
- **问题**：`audit_raw_labels.py` 调用 `pandas.DataFrame.to_markdown()` 时报 `ModuleNotFoundError: No module named 'tabulate'`。`to_markdown()` 是 pandas 的可选功能，依赖 `tabulate` 包，但 `requirements.txt` 中遗漏了这个依赖。
- **修改内容**：在 `requirements.txt` 末尾增加 `tabulate`。
- **影响范围**：所有使用 `to_markdown()` 的地方（`raw_audit.py`、`compare_protocols.py`、`export_paper_tables.py`、`run_benchmark.py`）均受益。

### 修改 3：修复 stream_edges_between_selected 因临时表被提前删除导致崩溃

- **文件**：`src/btcaml/data/db.py`、`src/btcaml/data/build_graph.py`
- **问题**：`build_protocol_dataset.py` 运行时崩溃，报 `TypeError: 'NoneType' object is not iterable`，出错位置是 `db.py` 的 `stream_dataframe` 中 `cur.description` 为 `None`。根因是 `stream_dataframe` 使用 psycopg2 named cursor（服务端游标），当连接处于 autocommit 模式时，`DECLARE` 语句会开一个独立事务，事务结束后临时表（`ON COMMIT DROP`）即被删除，后续 `FETCH` 查询不到任何列信息。
- **修改内容**：
  1. 在 `db.py` 新增 `stream_dataframe_regular` 函数，使用普通客户端 cursor + `fetchmany` 流式读取，保证查询与临时表在同一事务内。
  2. 在 `build_graph.py` 的 `stream_edges_between_selected` 中将 `stream_dataframe` 调用替换为 `stream_dataframe_regular`，并在 import 中补充该函数。
- **影响范围**：所有依赖临时表做流式边查询的 `build_protocol_dataset` 流程。

### 修改 4：更新 .env 数据库密码

- **文件**：`.env`
- **问题**：用户已将 PostgreSQL 密码从 `cq20050919;`（含分号）改为 `66666666`，需要同步更新 `.env` 文件。
- **修改内容**：将 `BITCOIN_DB_URL` 中的密码更新为新密码。
- **影响范围**：所有通过 `os.environ['BITCOIN_DB_URL']` 读取数据库连接的脚本。

### 修改 5：为 build_protocol_dataset 添加进度条和步骤输出

- **文件**：`src/btcaml/data/build_graph.py`、`scripts/build_protocol_dataset.py`
- **问题**：`build_protocol_dataset` 运行全程无任何输出，用户无法判断程序是否在正常运行，尤其边流式读取阶段可能持续数十分钟。
- **修改内容**：
  1. 在 `build_graph.py` 的 `build_protocol_dataset` 函数中，将整个流程分为 7 个步骤，每步用 `tqdm.write` 输出步骤编号和描述。
  2. 边流式读取循环（最慢的步骤）用 `tqdm` 进度条包装，实时显示已处理的 chunk 数和累计边数。
  3. 在 `scripts/build_protocol_dataset.py` 中增加 `time.time()` 计时，最终输出总耗时。
- **影响范围**：所有 `build_protocol_dataset.py` 的调用（label_preserving / class_balanced_khop / temporal_balanced）。
### 修改 6：修复 stream_edges_between_selected JOIN 条件 bug

- **文件**：`src/btcaml/data/build_graph.py`
- **问题**：边流式查询的 JOIN 条件写错：`JOIN tmp_selected_aliases sb ON e.b = sa.alias` 应为 `e.b = sb.alias`。当前写法导致 `sb` 表的别名从未被使用，JOIN 结果不正确（可能返回零条边或重复边）。
- **修改内容**：将 `sa.alias` 修正为 `sb.alias`。
- **影响范围**：所有 `build_protocol_dataset` 流程中的边构建。

### 修改 7：为协议选择阶段添加进度输出

- **文件**：`src/btcaml/data/protocols.py`
- **问题**：`protocol.select_aliases(conn)` 内部的邻居扩展和背景节点选择均为多次数据库查询，耗时可达数分钟，但全程无输出，用户无法判断进度。
- **修改内容**：
  1. `_load_all_labeled` 输出查询到的标签节点数量。
  2. `_neighbors_for_labeled` 用 `tqdm` 包装，逐类显示当前处理的类别和新增邻居数。
  3. `_select_background_top_activity` 输出背景节点选择数量。
- **影响范围**：所有 `class_balanced_khop` 和 `temporal_balanced` 协议的选择阶段。
### 修改 8：修复 _neighbors_for_labeled 查询慢（OR 改 UNION）

- **文件**：`src/btcaml/data/protocols.py`
- **问题**：`_neighbors_for_labeled` 的 SQL 使用 `OR` 条件（`e.a = s.alias OR e.b = s.alias`），在 7.86 亿行边表上 PostgreSQL 无法同时利用 `a` 和 `b` 两列索引，导致每个类别都做两次全表扫描，11 个类共 22 次全表扫描，耗时数小时。
- **修改内容**：将 `OR` 改为 `UNION`（`SELECT e.b FROM ... WHERE e.a = s.alias UNION SELECT e.a FROM ... WHERE e.b = s.alias`），使每个分支独立走索引。同时将中间列名从 `alias` 改为 `neighbor` 以避免与子查询列名混淆。
- **影响范围**：`class_balanced_khop` 和 `temporal_balanced` 协议的邻居扩展阶段。
- **预期效果**：每个类别查询从数分钟降到数秒。