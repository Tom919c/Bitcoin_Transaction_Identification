# DECISION_LOG 模板

每个 Phase 结束后复制下面模板填写。

```markdown
## YYYY-MM-DD Phase X: <phase name>

### 1. Completed

- [ ] Code implemented:
- [ ] Experiments run:
- [ ] Tables generated:
- [ ] Figures generated:
- [ ] Tests passed:

### 2. Commands

```powershell
python -m pytest -q
...
```

### 3. Key Outputs

| artifact | path | status |
|---|---|---|
| ... | ... | generated / missing |

### 4. Key Results

| metric | baseline | new | delta |
|---|---:|---:|---:|
| temporal Macro-F1 | | | |
| Minority-F1 | | | |
| conservative AUPRC | | | |

### 5. Interpretation

- What did we learn?
- Which hypothesis was supported?
- Which hypothesis was rejected?
- What remains uncertain?

### 6. Gate Decision

Choose one:

- [ ] Continue Temporal OOD method route
- [ ] Switch to Benchmark + Mechanism Analysis
- [ ] Keep Hybrid route
- [ ] Defer Subgraph route
- [ ] Stop and ask user for decision

Reason:

### 7. Risks

- ...
- ...

### 8. Next Commands

```powershell
...
```
```
