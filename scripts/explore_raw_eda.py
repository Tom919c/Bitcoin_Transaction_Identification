"""
Bitcoin Raw Dataset (PostgreSQL) -- Exploratory Data Analysis

Explores the ORIGINAL 2.52B-node / 786M-edge database directly,
produces a comprehensive report + figures.

Usage:
    conda activate MCM
    python scripts/explore_raw_eda.py

Output:
    visualization/eda/raw_report.txt
    visualization/eda/figures/raw_*.png
"""
import os, sys, warnings, time
from collections import Counter, defaultdict
from datetime import datetime
from typing import List, Tuple
import numpy as np
import pandas as pd
import psycopg2
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats as sp_stats

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
OUT_DIR = os.path.join(ROOT, "visualization", "eda")
FIG_DIR = os.path.join(OUT_DIR, "figures")
RPT_PATH = os.path.join(OUT_DIR, "raw_report.txt")
DB = "postgresql://postgres:cq20050919;@localhost/bitcoin_db"
NT, ET = "node_features", "transaction_edges"

sns.set_theme(style="whitegrid", font_scale=1.1)
plt.rcParams.update({"figure.dpi":140,"savefig.dpi":140,"savefig.bbox":"tight","figure.figsize":(10,6)})
warnings.filterwarnings("ignore")

# ── DB connection with statement_timeout ─────────────────────
def get_conn(timeout_ms=600000):
    """Connect with configurable statement timeout (ms)."""
    conn = psycopg2.connect(DB)
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute(f"SET statement_timeout = {timeout_ms}")
    cur.close()
    return conn

# ── Report ───────────────────────────────────────────────────
class Rpt:
    def __init__(self): self.L: List[str] = []; self.start = time.time()
    def sec(self, t):
        elapsed = time.time() - self.start
        self.L.append(f"\n{'='*72}\n  {t}  [elapsed: {elapsed:.1f}s]\n{'='*72}\n")
        print(f"  [{t}]")
    def sub(self, t): self.L.append(f"\n--- {t} ---\n"); print(f"    {t}")
    def p(self, t=""): self.L.append(str(t))
    def save(self, path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f: f.write("\n".join(self.L))
        print(f"Report saved: {path}")

def sf(fig, name):
    p = os.path.join(FIG_DIR, f"{name}.png")
    fig.savefig(p); plt.close(fig); print(f"  saved: {name}.png")

def query(conn, sql, timeout_ms=None):
    """Execute query, return DataFrame. Optionally override timeout."""
    cur = conn.cursor()
    if timeout_ms:
        cur.execute(f"SET statement_timeout = {timeout_ms}")
    cur.execute("RESET statement_timeout")
    return pd.read_sql_query(sql, conn)

def query_direct(conn, sql, timeout_ms=600000):
    """Execute and return raw rows."""
    cur = conn.cursor()
    cur.execute(f"SET statement_timeout = {timeout_ms}")
    cur.execute(sql)
    cols = [d[0] for d in cur.description] if cur.description else []
    rows = cur.fetchall()
    cur.close()
    return cols, rows

def human(n):
    if n>=1e9: return f"{n/1e9:.2f}B"
    if n>=1e6: return f"{n/1e6:.2f}M"
    if n>=1e3: return f"{n/1e3:.1f}K"
    return str(n)

def desc_arr(arr):
    s = arr[~np.isnan(arr)]
    if len(s)==0: return {}
    return dict(n=len(s), mu=float(np.mean(s)), sd=float(np.std(s)),
        mn=float(np.min(s)), p1=float(np.percentile(s,1)),
        p5=float(np.percentile(s,5)), p25=float(np.percentile(s,25)),
        med=float(np.median(s)), p75=float(np.percentile(s,75)),
        p95=float(np.percentile(s,95)), p99=float(np.percentile(s,99)),
        mx=float(np.max(s)), sk=float(pd.Series(s).skew()),
        ku=float(pd.Series(s).kurtosis()), zpct=float((s==0).sum()/len(s)*100))

# ====================================================================
# 1. Schema & Scale
# ====================================================================
def s01(conn, rpt):
    rpt.sec("1. Database Schema & Scale")
    # Row counts from pg_class (instant, no scan)
    cols, rows = query_direct(conn, """
        SELECT relname, reltuples::bigint, pg_size_pretty(pg_total_relation_size(relid))
        FROM pg_class c JOIN pg_namespace n ON n.oid = relnamespace
        WHERE relname IN ('node_features','transaction_edges')
        ORDER BY relname
    """)
    rpt.p("Table size estimates (from pg_class, instant):")
    for r in rows:
        rpt.p(f"  {r[0]:25s} ~{r[1]:>15,} rows  disk={r[2]}")

    # Column info (fast, schema-level)
    for table in [NT, ET]:
        cols2, rows2 = query_direct(conn, f"""
            SELECT column_name, data_type, is_nullable,
                   character_maximum_length, numeric_precision
            FROM information_schema.columns
            WHERE table_name = '{table}' ORDER BY ordinal_position
        """)
        rpt.sub(f"{table} columns ({len(rows2)} columns)")
        rpt.p(f"  {'column':30s} {'type':20s} {'nullable':8s}")
        rpt.p(f"  {'-'*60}")
        for r in rows2:
            rpt.p(f"  {str(r[0]):30s} {str(r[1]):20s} {str(r[2]):8s}")

    # Indexes
    cols3, rows3 = query_direct(conn, """
        SELECT indexname FROM pg_indexes
        WHERE tablename IN ('node_features','transaction_edges')
        ORDER BY tablename, indexname
    """)
    rpt.sub("Indexes")
    for r in rows3: rpt.p(f"  {r[0]}")
    if not rows3: rpt.p("  (none)")


# ====================================================================
# 2. Label Distribution (full scan with GROUP BY)
# ====================================================================
def s02(conn, rpt):
    rpt.sec("2. Label Distribution (full table)")
    cols, rows = query_direct(conn, f"""
        SELECT COALESCE(NULLIF(TRIM(UPPER(label)),''), '(empty)') AS label, COUNT(*) AS cnt
        FROM {NT}
        GROUP BY label
        ORDER BY cnt DESC
    """)
    rpt.p("All labels (GROUP BY on full table):")
    rpt.p(f"  {'label':20s} {'count':>15s} {'pct':>8s}")
    rpt.p(f"  {'-'*45}")
    total = sum(r[1] for r in rows)
    for r in rows:
        pct = r[1]/total*100 if total else 0
        rpt.p(f"  {r[0]:20s} {r[1]:>15,} {pct:>7.3f}%")
    rpt.p(f"\n  Total nodes: {total:,}")

    # Bar chart
    fig, ax = plt.subplots(figsize=(12,5))
    labels = [r[0][:12] for r in rows[:20]]
    counts = [r[1] for r in rows[:20]]
    bars = ax.bar(labels, counts, color=sns.color_palette("Set2", min(len(rows),20)).as_hex(), edgecolor="none")
    ax.set_yscale("log"); ax.set_ylabel("Count (log)"); ax.set_title("Full DB Label Distribution (top 20)")
    ax.tick_params(axis="x", rotation=45)
    fig.tight_layout(); sf(fig, "raw_01_labels")


# ====================================================================
# 3. Node Feature Distributions (sampled)
# ====================================================================
def s03(conn, rpt):
    rpt.sec("3. Node Feature Distributions (TABLESAMPLE BERNOULLI)")
    # Use BERNOULLI for uniform sampling
    cols, rows = query_direct(conn, f"""
        SELECT degree, degree_in, degree_out,
               total_transactions_in, total_transactions_out,
               min_sent, max_sent, total_sent,
               min_received, max_received, total_received,
               cluster_size,
               first_transaction_in, last_transaction_in,
               first_transaction_out, last_transaction_out,
               cluster_num_edges, cluster_num_cc, cluster_num_nodes_in_cc,
               COALESCE(NULLIF(TRIM(UPPER(label)),''), '') AS label
        FROM {NT} TABLESAMPLE BERNOULLI(0.01)
    """, timeout_ms=1200000)
    df = pd.DataFrame(rows, columns=cols)
    rpt.p(f"Sampled {len(df):,} rows (BERNOULLI 0.01%)")

    feat_cols = [c for c in df.columns if c != "label"]

    # Descriptive stats
    rpt.sub("3.1 Descriptive Stats")
    for c in feat_cols:
        s = pd.to_numeric(df[c], errors="coerce").dropna()
        if len(s)==0: continue
        rpt.p(f"[{c}] n={len(s)} mu={s.mean():.2f} sd={s.std():.2f} "
              f"min={s.min():.2f} p25={s.quantile(.25):.2f} med={s.median():.2f} "
              f"p75={s.quantile(.75):.2f} p95={s.quantile(.95):.2f} p99={s.quantile(.99):.2f} "
              f"max={s.max():.2f} skew={s.skew():.2f} z%={( s==0).sum()/len(s)*100:.1f}%")

    # Feature distributions (amount cols get log1p)
    groups = [
        ("degree_count", ["degree","degree_in","degree_out","total_transactions_in","total_transactions_out","cluster_size"]),
        ("amount", ["min_sent","max_sent","total_sent","min_received","max_received","total_received"]),
        ("block_height", ["first_transaction_in","last_transaction_in","first_transaction_out","last_transaction_out"]),
        ("cluster", ["cluster_num_edges","cluster_num_cc","cluster_num_nodes_in_cc"]),
    ]
    for gn, fc in groups:
        n = len(fc); nc = 3; nr = (n+nc-1)//nc
        fig, axes = plt.subplots(nr, nc, figsize=(5*nc, 4*nr)); axes = np.atleast_2d(axes)
        for k, c in enumerate(fc):
            ax = axes[k//nc, k%nc]
            s = pd.to_numeric(df[c], errors="coerce").dropna()
            if gn == "amount":
                s = np.log1p(s.clip(lower=0)); ax.set_xlabel(f"log1p({c})")
            ax.hist(s, bins=80, edgecolor="none", alpha=0.85)
            ax.set_title(c, fontsize=9)
        for k in range(n, nr*nc): axes[k//nc, k%nc].set_visible(False)
        fig.suptitle(f"Full DB Feature Dist: {gn} (sampled)")
        fig.tight_layout(); sf(fig, f"raw_02_{gn}")

    # Correlation heatmap
    rpt.sub("3.2 High Correlations |r|>0.5")
    X = df[feat_cols].apply(pd.to_numeric, errors="coerce").fillna(0).values
    corr = np.corrcoef(X.T)
    pairs = []
    for i in range(len(feat_cols)):
        for j in range(i+1, len(feat_cols)):
            if abs(corr[i,j]) > 0.5:
                pairs.append((feat_cols[i], feat_cols[j], corr[i,j]))
    pairs.sort(key=lambda x: -abs(x[2]))
    for a,b,v in pairs[:30]: rpt.p(f"  {a} <-> {b}: r={v:.4f}")

    fig, ax = plt.subplots(figsize=(14,12))
    mask = np.triu(np.ones_like(corr, dtype=bool), k=1)
    sns.heatmap(pd.DataFrame(corr, index=feat_cols, columns=feat_cols),
                mask=mask, annot=True, fmt=".2f", cmap="RdBu_r", center=0,
                square=True, ax=ax, annot_kws={"size":7})
    ax.set_title("Full DB Node Feature Correlation (sampled)")
    sf(fig, "raw_03_corr")

    return df  # return for later use


# ====================================================================
# 4. Per-Class Feature Differences
# ====================================================================
def s04(conn, rpt):
    rpt.sec("4. Per-Class Feature Differences (sampled)")
    # Sample with class info
    cols, rows = query_direct(conn, f"""
        SELECT degree, degree_in, degree_out,
               total_transactions_in, total_transactions_out,
               total_sent, total_received, cluster_size,
               COALESCE(NULLIF(TRIM(UPPER(label)),''), '') AS label
        FROM {NT} TABLESAMPLE BERNOULLI(0.02)
        WHERE label IS NOT NULL AND TRIM(label) != ''
    """, timeout_ms=1200000)
    df = pd.DataFrame(rows, columns=cols)
    rpt.p(f"Sampled {len(df):,} labeled rows (BERNOULLI 0.02%, filtered)")

    TARGETS = ["INDIVIDUAL","BET","GAMBLING","EXCHANGE","BRIDGE"]
    feat_cols = [c for c in df.columns if c != "label"]

    # Per-class stats
    rpt.sub("4.1 Mean/Median by Class")
    for c in feat_cols:
        rpt.p(f"[{c}]")
        for lbl in TARGETS:
            s = pd.to_numeric(df[df["label"]==lbl][c], errors="coerce").dropna()
            if len(s)==0: continue
            rpt.p(f"  {lbl:12s} mu={s.mean():12.2f} med={s.median():12.2f} sd={s.std():12.2f} n={len(s)}")
        rpt.p()

    # Kruskal-Wallis
    rpt.sub("4.2 Kruskal-Wallis Test")
    for c in feat_cols:
        gs = [pd.to_numeric(df[df["label"]==l][c], errors="coerce").dropna().values for l in TARGETS]
        gs = [g for g in gs if len(g)>0]
        if len(gs)>=2:
            st, p = sp_stats.kruskal(*gs)
            sig = "***" if p<0.001 else "**" if p<0.01 else "*" if p<0.05 else "n.s."
            rpt.p(f"  {c:30s} H={st:12.2f} p={p:.2e} {sig}")

    # Boxplots
    n = len(feat_cols); nc = 4; nr = (n+nc-1)//nc
    fig, axes = plt.subplots(nr, nc, figsize=(5*nc, 4*nr)); axes = np.atleast_2d(axes)
    for k, c in enumerate(feat_cols):
        ax = axes[k//nc, k%nc]
        plot_data = df[df["label"].isin(TARGETS)].copy()
        plot_data[c] = pd.to_numeric(plot_data[c], errors="coerce")
        if c in ("total_sent","total_received","min_sent","max_sent"):
            plot_data[c] = np.log1p(plot_data[c].clip(lower=0))
            c_label = f"log1p({c})"
        else:
            c_label = c
        sns.boxplot(data=plot_data, x="label", y=c, ax=ax, order=TARGETS,
                    palette="Set2", showfliers=False)
        ax.set_title(c_label, fontsize=9)
        ax.tick_params(labelsize=7, axis="x", rotation=30)
    for k in range(n, nr*nc): axes[k//nc, k%nc].set_visible(False)
    fig.suptitle("Full DB Features by Class (sampled, labeled only)")
    fig.tight_layout(); sf(fig, "raw_04_class_box")

    # PCA + t-SNE
    rpt.sub("4.3 PCA + t-SNE (sampled labeled nodes)")
    from sklearn.decomposition import PCA
    from sklearn.manifold import TSNE
    from sklearn.preprocessing import StandardScaler

    for c in feat_cols: df[c] = pd.to_numeric(df[c], errors="coerce")
    labeled = df.dropna(subset=feat_cols).copy()
    # Sample per class
    sampled = labeled.groupby("label", group_keys=False).apply(
        lambda x: x.sample(min(len(x), 300), random_state=42))
    X = StandardScaler().fit_transform(sampled[feat_cols].values)
    y = sampled["label"].values
    yi = np.array([TARGETS.index(l) if l in TARGETS else -1 for l in y])
    valid = yi >= 0
    X, yi = X[valid], yi[valid]

    pca = PCA(n_components=2, random_state=42); Xp = pca.fit_transform(X)
    fig, ax = plt.subplots(figsize=(8,6))
    sc = ax.scatter(Xp[:,0], Xp[:,1], c=yi, cmap="Set2", s=10, alpha=0.6, edgecolors="none")
    h,_ = sc.legend_elements(); ax.legend(h, TARGETS, title="Class", fontsize=8)
    ax.set_xlabel(f"PC1 ({pca.explained_variance_ratio_[0]:.1%})")
    ax.set_ylabel(f"PC2 ({pca.explained_variance_ratio_[1]:.1%})")
    ax.set_title("PCA of Node Features (full DB, labeled, sampled)")
    sf(fig, "raw_05_pca")

    perp = min(30, max(5, len(X)//10))
    Xt = TSNE(n_components=2, perplexity=perp, random_state=42, max_iter=1000).fit_transform(X)
    fig, ax = plt.subplots(figsize=(8,6))
    sc = ax.scatter(Xt[:,0], Xt[:,1], c=yi, cmap="Set2", s=10, alpha=0.6, edgecolors="none")
    h,_ = sc.legend_elements(); ax.legend(h, TARGETS, title="Class", fontsize=8)
    ax.set_title("t-SNE of Node Features (full DB, labeled, sampled)")
    sf(fig, "raw_06_tsne")


# ====================================================================
# 5. Edge Feature Distributions (sampled)
# ====================================================================
def s05(conn, rpt):
    rpt.sec("5. Edge Feature Distributions (sampled)")
    cols, rows = query_direct(conn, f"""
        SELECT reveal, last_seen, total, min_sent, max_sent, total_sent
        FROM {ET} TABLESAMPLE BERNOULLI(0.01)
    """, timeout_ms=1200000)
    df = pd.DataFrame(rows, columns=cols)
    rpt.p(f"Sampled {len(df):,} edges (BERNOULLI 0.01%)")

    rpt.sub("5.1 Descriptive Stats")
    for c in cols:
        s = pd.to_numeric(df[c], errors="coerce").dropna()
        if len(s)==0: continue
        rpt.p(f"[{c}] n={len(s)} mu={s.mean():.2f} sd={s.std():.2f} "
              f"min={s.min():.2f} p25={s.quantile(.25):.2f} med={s.median():.2f} "
              f"p75={s.quantile(.75):.2f} p95={s.quantile(.95):.2f} p99={s.quantile(.99):.2f} "
              f"max={s.max():.2f} skew={s.skew():.2f} z%={( s==0).sum()/len(s)*100:.1f}%")

    rpt.sub("5.2 Derived Features")
    for c in cols: df[c] = pd.to_numeric(df[c], errors="coerce")
    df["avg_sent"] = df["total_sent"] / df["total"].clip(lower=1)
    df["amount_range"] = df["max_sent"] - df["min_sent"]
    df["duration"] = (df["last_seen"] - df["reveal"]).clip(lower=0)
    df["tx_freq"] = df["total"] / (df["duration"] + 1)
    df["edge_recency"] = df["last_seen"].max() - df["last_seen"]
    for c in ["avg_sent","amount_range","duration","tx_freq","edge_recency"]:
        s = df[c].dropna()
        rpt.p(f"[{c}] mu={s.mean():.2f} med={s.median():.2f} p95={s.quantile(.95):.2f} sk={s.skew():.2f}")

    # Corr
    rpt.sub("5.3 Correlations")
    corr = df[cols].astype(float).corr()
    for i, a in enumerate(cols):
        for j, b in enumerate(cols):
            if i<j: rpt.p(f"  {a}<->{b}: r={corr.loc[a,b]:.4f}")

    # Distributions
    fig, axes = plt.subplots(2, 3, figsize=(15,8))
    for i, c in enumerate(cols):
        ax = axes[i//3, i%3]; s = df[c].dropna()
        if c in ("min_sent","max_sent","total_sent"):
            s = np.log1p(s.clip(lower=0)); ax.set_xlabel(f"log1p({c})")
        ax.hist(s, bins=80, edgecolor="none", alpha=0.85); ax.set_title(c, fontsize=9)
    fig.suptitle("Full DB Edge Features (sampled)"); fig.tight_layout()
    sf(fig, "raw_07_edge_dist")

    fig, ax = plt.subplots(figsize=(8,6))
    sns.heatmap(corr, annot=True, fmt=".2f", cmap="RdBu_r", center=0, ax=ax)
    ax.set_title("Full DB Edge Feature Correlation"); sf(fig, "raw_08_edge_corr")


# ====================================================================
# 6. Graph Topology (degree stats)
# ====================================================================
def s06(conn, rpt):
    rpt.sec("6. Graph Topology")
    # Degree stats via SQL aggregation on full table (fast with index)
    rpt.sub("6.1 Degree Distribution (full table aggregation)")
    cols, rows = query_direct(conn, f"""
        SELECT
            MIN(degree) AS min_d, MAX(degree) AS max_d,
            AVG(degree) AS avg_d, PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY degree) AS med_d,
            PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY degree) AS p95_d,
            PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY degree) AS p99_d
        FROM {NT}
    """, timeout_ms=1200000)
    rpt.p("Degree (full table):")
    rpt.p(f"  min={rows[0][0]}  max={rows[0][1]}  mean={rows[0][2]:.2f}  median={rows[0][3]}  p95={rows[0][4]}  p99={rows[0][5]}")

    for field in ["degree_in", "degree_out"]:
        cols2, rows2 = query_direct(conn, f"""
            SELECT MIN({field}), MAX({field}),
                   AVG({field}), PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY {field}),
                   PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY {field}),
                   PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY {field})
            FROM {NT}
        """, timeout_ms=1200000)
        rpt.p(f"  {field}: min={rows2[0][0]} max={rows2[0][1]} avg={rows2[0][2]:.2f} med={rows2[0][3]} p95={rows2[0][4]} p99={rows2[0][5]}")

    # Degree histogram (sampled)
    rpt.sub("6.2 Degree Histogram (sampled)")
    cols3, rows3 = query_direct(conn, f"""
        SELECT degree, degree_in, degree_out
        FROM {NT} TABLESAMPLE BERNOULLI(0.1)
    """, timeout_ms=1200000)
    ddf = pd.DataFrame(rows3, columns=cols3)
    fig, axes = plt.subplots(1, 3, figsize=(15,4))
    for i, c in enumerate(["degree","degree_in","degree_out"]):
        ax = axes[i]; s = pd.to_numeric(ddf[c], errors="coerce").dropna(); s = s[s>0]
        ax.hist(np.log10(s), bins=80, edgecolor="none", alpha=0.85)
        ax.set_xlabel(f"log10({c})"); ax.set_title(f"{c} (log, sampled)")
    fig.tight_layout(); sf(fig, "raw_09_degree")

    # Edge direction stats
    rpt.sub("6.3 Edge Direction (SQL aggregate)")
    cols4, rows4 = query_direct(conn, f"""
        SELECT
            COUNT(*) AS total_edges,
            COUNT(DISTINCT ROW(a,b)) AS unique_pairs,
            SUM(CASE WHEN a = b THEN 1 ELSE 0 END) AS self_loops
        FROM {ET}
    """, timeout_ms=1200000)
    rpt.p(f"  Total edges: {rows4[0][0]:,}")
    rpt.p(f"  Unique (src,dst) pairs: {rows4[0][1]:,}")
    rpt.p(f"  Self-loops: {rows4[0][2]:,}")


# ====================================================================
# 7. Temporal Patterns
# ====================================================================
def s07(conn, rpt):
    rpt.sec("7. Temporal Patterns")
    rpt.sub("7.1 Block Height Ranges (full table)")
    for field in ["first_transaction_in","last_transaction_in","first_transaction_out","last_transaction_out"]:
        cols, rows = query_direct(conn, f"""
            SELECT MIN({field}), MAX({field}), AVG({field}),
                   PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY {field})
            FROM {NT} WHERE {field} IS NOT NULL
        """, timeout_ms=1200000)
        rpt.p(f"  {field}: min={rows[0][0]} max={rows[0][1]} avg={rows[0][2]:.0f} med={rows[0][3]}")

    rpt.sub("7.2 Edge Temporal Ranges")
    cols, rows = query_direct(conn, f"""
        SELECT MIN(reveal), MAX(reveal), AVG(reveal),
               MIN(last_seen), MAX(last_seen), AVG(last_seen)
        FROM {ET}
    """, timeout_ms=1200000)
    rpt.p(f"  reveal:    min={rows[0][0]} max={rows[0][1]} avg={rows[0][2]:.0f}")
    rpt.p(f"  last_seen: min={rows[0][3]} max={rows[0][4]} avg={rows[0][5]:.0f}")

    rpt.sub("7.3 Per-Class Avg Block Height (sampled)")
    cols2, rows2 = query_direct(conn, f"""
        SELECT
            COALESCE(NULLIF(TRIM(UPPER(label)),''),'') AS label,
            AVG(first_transaction_in) AS afi,
            AVG(last_transaction_in) AS ali,
            AVG(first_transaction_out) AS afo,
            AVG(last_transaction_out) AS alo,
            AVG(last_transaction_in - first_transaction_in) AS dur_in,
            AVG(last_transaction_out - first_transaction_out) AS dur_out,
            COUNT(*) AS cnt
        FROM {NT}
        WHERE label IS NOT NULL AND TRIM(label) != ''
        GROUP BY label
        ORDER BY cnt DESC
    """, timeout_ms=1200000)
    rpt.p(f"  {'label':15s} {'avg_fi':>8s} {'avg_li':>8s} {'avg_fo':>8s} {'avg_lo':>8s} {'dur_in':>8s} {'dur_out':>8s} {'n':>8s}")
    for r in rows2:
        rpt.p(f"  {str(r[0]):15s} {r[1]:>8.0f} {r[2]:>8.0f} {r[3]:>8.0f} {r[4]:>8.0f} {r[5]:>8.0f} {r[6]:>8.0f} {r[7]:>8,}")


# ====================================================================
# 8. Summary
# ====================================================================
def s08(conn, rpt):
    rpt.sec("8. Key Findings")
    for l in [
        "",
        "=== DATASET IDENTITY ===",
        "  Name: Bitcoin Research with a Transaction Graph Dataset",
        "  Paper: Schnoering & Vazirgiannis, 2024 (arXiv:2411.10325)",
        "  DB size: ~252M nodes, ~786M edges",
        "  Subgraph (data.pt): 350K nodes, 17M edges (TopK 0.14%)",
        "",
        "=== CRITICAL OBSERVATIONS ===",
        "  1. Raw dataset is 1000x larger than current subgraph",
        "  2. Subgraph selection via TopK scoring may introduce severe bias",
        "  3. Many nodes with low activity (degree_in/out ~0) exist",
        "  4. Amount features have extreme long-tail (skew >> 100)",
        "  5. Block height ranges suggest multi-year activity span",
        "  6. Edge temporal info (reveal, last_seen) enables time-aware modeling",
        "",
        "=== RESEARCH IMPLICATIONS ===",
        "  - Current TopK selection may filter out important low-activity malicious nodes",
        "  - Class-balanced sampling should consider activity level, not just TopK score",
        "  - Temporal split is feasible using block heights as timestamps",
        "  - Edge directionality (a->b) carries fund-flow semantics",
        "  - Feature engineering from raw amounts needs log1p + robust scaling",
    ]: rpt.p(l)


# ====================================================================
# Main
# ====================================================================
def main():
    os.makedirs(FIG_DIR, exist_ok=True)
    conn = get_conn(timeout_ms=600000)
    rpt = Rpt()
    t0 = datetime.now()
    rpt.p(f"Raw DB EDA: {t0:%Y-%m-%d %H:%M:%S}")
    rpt.p(f"Database: {DB}")

    steps = [
        ("1.Schema&Scale", s01),
        ("2.Labels", s02),
        ("3.NodeFeatures", s03),
        ("4.ClassDiff", s04),
        ("5.EdgeFeatures", s05),
        ("6.Topology", s06),
        ("7.Temporal", s07),
        ("8.Summary", s08),
    ]
    for name, fn in steps:
        print(f"\n[{name}] ...", flush=True)
        try:
            fn(conn, rpt)
            print(f"[{name}] OK")
        except Exception as e:
            rpt.p(f"\n** ERROR {name}: {e} **")
            import traceback; rpt.p(traceback.format_exc())
            print(f"[{name}] FAIL: {e}")

    elapsed = datetime.now() - t0
    rpt.p(f"\n\nTotal: {elapsed}")
    rpt.save(RPT_PATH)
    conn.close()
    print(f"\nDone! {elapsed}")
    print(f"Report: {RPT_PATH}")
    print(f"Figures: {FIG_DIR}/")

if __name__ == "__main__": main()
