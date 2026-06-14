"""
Bitcoin Transaction Graph - EDA (from data.pt)
Usage: conda activate MCM && python scripts/explore_data.py
Output: visualization/eda/report.txt + figures/*.png
"""
import os, sys, warnings
from collections import Counter, defaultdict
from datetime import datetime
import numpy as np, pandas as pd, torch
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt, seaborn as sns
from scipy import stats as sp_stats

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
EDA_DIR = os.path.join(ROOT, "visualization", "eda")
FIG_DIR = os.path.join(EDA_DIR, "figures")
RPT_PATH = os.path.join(EDA_DIR, "report.txt")
DATA_PT = os.path.join(ROOT, "data", "processed", "data.pt")
LABELS = ["NONE","INDIVIDUAL","BET","GAMBLING","EXCHANGE","BRIDGE"]
TARGETS = LABELS[1:]
sns.set_theme(style="whitegrid", font_scale=1.1)
plt.rcParams.update({"figure.dpi":140,"savefig.dpi":140,"savefig.bbox":"tight","figure.figsize":(10,6)})
warnings.filterwarnings("ignore")

class R:
    def __init__(self): self.L = []
    def sec(self, t): self.L.append(f"\n{'='*72}\n  {t}\n{'='*72}\n")
    def sub(self, t): self.L.append(f"\n--- {t} ---\n")
    def p(self, t=""): self.L.append(str(t))
    def save(self, path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f: f.write("\n".join(self.L))
        print(f"Report: {path}")

def sf(fig, name):
    p = os.path.join(FIG_DIR, f"{name}.png")
    fig.savefig(p); plt.close(fig); print(f"  fig: {name}.png")

def desc(arr):
    s = arr[~np.isnan(arr)]
    if len(s)==0: return {}
    ps = lambda q: float(np.percentile(s, q))
    sk = float(pd.Series(s).skew()); ku = float(pd.Series(s).kurtosis())
    return dict(n=int(len(s)),mu=float(np.mean(s)),sd=float(np.std(s)),
        min=float(np.min(s)),p1=ps(1),p5=ps(5),p25=ps(25),med=ps(50),
        p75=ps(75),p95=ps(95),p99=ps(99),max=float(np.max(s)),
        sk=sk,ku=ku,zpct=float((s==0).sum()/len(s)*100))

def human(n):
    if n>=1e6: return f"{n/1e6:.2f}M"
    if n>=1e3: return f"{n/1e3:.1f}K"
    return str(n)

def load():
    print(f"Loading {DATA_PT} ...")
    d = torch.load(DATA_PT, map_location="cpu", weights_only=False)
    if isinstance(d, dict):
        return dict(x=d["x"].numpy(), ei=d["edge_index"].numpy(),
            ea=d["edge_attr"].numpy() if d["edge_attr"].numel()>0 else np.empty((d["edge_index"].shape[1],0)),
            y=d["y"].numpy(), tm=d["train_mask"].numpy(), vm=d["val_mask"].numpy(),
            tsm=d["test_mask"].numpy(),
            fc=list(d.get("feature_columns",[])), ec=list(d.get("edge_attr_columns",[])))
    return dict(x=d.x.numpy(), ei=d.edge_index.numpy(),
        ea=d.edge_attr.numpy() if d.edge_attr.numel()>0 else np.empty((d.edge_index.shape[1],0)),
        y=d.y.numpy(), tm=d.train_mask.numpy(), vm=d.val_mask.numpy(),
        tsm=d.test_mask.numpy(),
        fc=list(getattr(d,"feature_columns",[])), ec=list(getattr(d,"edge_attr_columns",[])))

# 1 Overview
def s01(r,D):
    r.sec("1. Dataset Overview")
    N,E = D["x"].shape[0], D["ei"].shape[1]
    r.p(f"Nodes: {human(N)} ({N:,})  Edges: {human(E)} ({E:,})  Avg deg: {E/N:.2f}")
    r.p(f"Node feats: {D['x'].shape[1]}  Edge feats: {D['ea'].shape[1]}")
    r.p(f"Labeled (y!=0): {(D['y']!=0).sum():,}  Unlabeled: {(D['y']==0).sum():,}")
    r.p(f"Train/Val/Test: {D['tm'].sum():,}/{D['vm'].sum():,}/{D['tsm'].sum():,}")
    r.p(f"Feat cols: {D['fc']}")
    r.p(f"Edge cols: {D['ec']}")
    r.sub("1.1 DB Info")
    try:
        import psycopg2
        conn = psycopg2.connect("postgresql://postgres:cq20050919;@localhost/bitcoin_db")
        cur = conn.cursor()
        cur.execute("SELECT relname,reltuples::bigint FROM pg_class WHERE relname IN ('node_features','transaction_edges')")
        for row in cur.fetchall(): r.p(f"  {row[0]}: ~{row[1]:,} rows (full DB)")
        conn.close()
    except Exception as e: r.p(f"  DB: {e}")

# 2 Node features
def s02(r,D):
    r.sec("2. Node Feature Analysis")
    X,cols = D["x"],D["fc"]
    r.sub("2.1 NaN")
    for i,c in enumerate(cols):
        n=int(np.isnan(X[:,i]).sum()); r.p(f"  {c:30s} NaN={n:>8,} ({n/len(X)*100:.2f}%)")
    r.sub("2.2 Stats")
    for i,c in enumerate(cols):
        d=desc(X[:,i])
        if not d: continue
        r.p(f"[{c}] n={d['n']} mu={d['mu']:.4f} sd={d['sd']:.4f} min={d['min']:.4f} p1={d['p1']:.4f} p5={d['p5']:.4f} p25={d['p25']:.4f} med={d['med']:.4f} p75={d['p75']:.4f} p95={d['p95']:.4f} p99={d['p99']:.4f} max={d['max']:.4f} sk={d['sk']:.2f} ku={d['ku']:.2f} z%={d['zpct']:.1f}")
    r.sub("2.3 High Corr |r|>0.5")
    Xc = np.nan_to_num(X,nan=0.0); corr = np.corrcoef(Xc.T)
    pairs = [(cols[i],cols[j],corr[i,j]) for i in range(len(cols)) for j in range(i+1,len(cols)) if abs(corr[i,j])>0.5]
    pairs.sort(key=lambda x:-abs(x[2]))
    for a,b,v in pairs: r.p(f"  {a} <-> {b}: r={v:.4f}")
    fig,ax=plt.subplots(figsize=(14,12)); mask=np.triu(np.ones_like(corr,dtype=bool),k=1)
    sns.heatmap(pd.DataFrame(corr,index=cols,columns=cols),mask=mask,annot=True,fmt=".2f",cmap="RdBu_r",center=0,square=True,ax=ax,annot_kws={"size":7})
    ax.set_title("Node Feature Correlation"); sf(fig,"01_node_corr")
    grps=[("deg_cnt",[0,1,2,3,4,11]),("amount",list(range(5,11))),("blk",list(range(12,16))),("clst",list(range(16,min(19,len(cols)))))]
    for gn,idxs in grps:
        vi=[i for i in idxs if i<len(cols)]; n=len(vi); nc=3; nr=(n+nc-1)//nc
        fig,axes=plt.subplots(nr,nc,figsize=(5*nc,4*nr)); axes=np.atleast_2d(axes)
        for k,i in enumerate(vi):
            ax=axes[k//nc,k%nc]; s=X[:,i]; s=s[~np.isnan(s)]
            if gn=="amount": s=np.log1p(np.clip(s,0,None)); ax.set_xlabel(f"log1p({cols[i]})")
            ax.hist(s,bins=80,edgecolor="none",alpha=0.85); ax.set_title(cols[i],fontsize=9)
        for k in range(n,nr*nc): axes[k//nc,k%nc].set_visible(False)
        fig.suptitle(f"Distribution: {gn}"); fig.tight_layout(); sf(fig,f"02_{gn}")

# 3 Labels
def s03(r,D):
    r.sec("3. Label Distribution")
    y=D["y"]; total=len(y); lc=Counter(y.tolist()); lab=int((y!=0).sum())
    r.sub("3.1 Counts")
    for lid,lname in enumerate(LABELS):
        cnt=lc.get(lid,0); pct=cnt/total*100
        extra=f"  ({cnt/lab*100:.2f}% of labeled)" if lid>0 and lab>0 else ""
        r.p(f"  {lname:12s} id={lid}: {cnt:>10,}  {pct:>8.3f}%{extra}")
    r.p(f"\n  Total: {total:,}  Labeled: {lab:,} ({lab/total*100:.3f}%)")
    tc={LABELS[i]:lc.get(i,0) for i in range(1,6)}
    mx,mn=max(tc,key=tc.get),min(tc,key=tc.get)
    r.p(f"  Imbalance: {mx}({tc[mx]}) vs {mn}({tc[mn]}) = {tc[mx]/max(tc[mn],1):.0f}x")
    r.sub("3.2 Split")
    for sn,m in [("train",D["tm"]),("val",D["vm"]),("test",D["tsm"])]:
        sy=y[m]; sl=int((sy!=0).sum()); r.p(f"  {sn}: {m.sum():,} nodes ({sl} labeled)")
        for lid in range(1,6):
            c=int((sy==lid).sum())
            if c>0: r.p(f"    {LABELS[lid]:12s}: {c}")
    fig,axes=plt.subplots(1,2,figsize=(14,5))
    al=["(unlabeled)"]+TARGETS; ac=[total-lab]+[tc[l] for l in TARGETS]
    cl=["#cccccc"]+sns.color_palette("Set2",len(TARGETS)).as_hex()
    bars=axes[0].bar(al,ac,color=cl,edgecolor="none"); axes[0].set_yscale("log"); axes[0].set_title("All (log)")
    for b,c in zip(bars,ac): axes[0].text(b.get_x()+b.get_width()/2,c*1.1,human(c),ha="center",va="bottom",fontsize=8)
    bars=axes[1].bar(TARGETS,[tc[l] for l in TARGETS],color=sns.color_palette("Set2",len(TARGETS)).as_hex(),edgecolor="none")
    axes[1].set_title("Labeled Only")
    for b,l in zip(bars,TARGETS): axes[1].text(b.get_x()+b.get_width()/2,tc[l]*1.02,str(tc[l]),ha="center",va="bottom",fontsize=9)
    fig.tight_layout(); sf(fig,"03_labels")

# 4 Edge features
def s04(r,D):
    r.sec("4. Edge Feature Analysis")
    Ea,cols=D["ea"],D["ec"]
    if Ea.shape[1]==0: r.p("No edge features"); return
    n=len(Ea)
    if n>500000:
        idx=np.random.RandomState(42).choice(n,500000,replace=False); Ea_s=Ea[idx]; r.p(f"Sampled {len(Ea_s):,}/{n:,}")
    else: Ea_s=Ea
    r.sub("4.1 Stats")
    for i,c in enumerate(cols):
        d=desc(Ea_s[:,i])
        if not d: continue
        r.p(f"[{c}] mu={d['mu']:.2f} med={d['med']:.2f} p95={d['p95']:.2f} max={d['max']:.2f} sk={d['sk']:.2f} z%={d['zpct']:.1f}")
    r.sub("4.2 Corr")
    corr=np.corrcoef(Ea_s.T)
    for i in range(len(cols)):
        for j in range(i+1,len(cols)): r.p(f"  {cols[i]}<->{cols[j]}: r={corr[i,j]:.4f}")
    r.sub("4.3 Derived")
    ci={c:cols.index(c) for c in cols}
    if "total_sent" in ci and "total" in ci:
        avg=Ea_s[:,ci["total_sent"]]/np.clip(Ea_s[:,ci["total"]],1,None); d=desc(avg); r.p(f"[avg_sent] mu={d['mu']:.2f} med={d['med']:.2f} p95={d['p95']:.2f} sk={d['sk']:.2f}")
    if "max_sent" in ci and "min_sent" in ci:
        rng=Ea_s[:,ci["max_sent"]]-Ea_s[:,ci["min_sent"]]; d=desc(rng); r.p(f"[range] mu={d['mu']:.2f} med={d['med']:.2f} p95={d['p95']:.2f}")
    if "last_seen" in ci and "reveal" in ci:
        dur=np.clip(Ea_s[:,ci["last_seen"]]-Ea_s[:,ci["reveal"]],0,None); d=desc(dur); r.p(f"[dur] mu={d['mu']:.2f} med={d['med']:.2f} p95={d['p95']:.2f}")
        if "total" in ci:
            freq=Ea_s[:,ci["total"]]/(dur+1); d=desc(freq); r.p(f"[freq] mu={d['mu']:.2f} med={d['med']:.2f} p95={d['p95']:.2f}")
    fig,axes=plt.subplots(2,3,figsize=(15,8))
    for i,c in enumerate(cols[:6]):
        ax=axes[i//3,i%3]; s=Ea_s[:,i]
        if c in("min_sent","max_sent","total_sent"): s=np.log1p(np.clip(s,0,None)); ax.set_xlabel(f"log1p({c})")
        ax.hist(s,bins=80,edgecolor="none",alpha=0.85); ax.set_title(c,fontsize=9)
    fig.suptitle("Edge Features"); fig.tight_layout(); sf(fig,"04_edge_dist")
    fig,ax=plt.subplots(figsize=(8,6))
    sns.heatmap(pd.DataFrame(corr,index=cols,columns=cols),annot=True,fmt=".2f",cmap="RdBu_r",center=0,ax=ax)
    ax.set_title("Edge Corr"); sf(fig,"05_edge_corr")

# 5 Topology
def s05(r,D):
    r.sec("5. Graph Topology")
    ei=D["ei"]; N=D["x"].shape[0]
    out_d=np.bincount(ei[0],minlength=N); in_d=np.bincount(ei[1],minlength=N); tot_d=out_d+in_d
    r.sub("5.1 Degree")
    for nm,arr in [("degree",tot_d),("in",in_d),("out",out_d)]:
        d=desc(arr.astype(float)); r.p(f"[{nm}] mu={d['mu']:.2f} med={d['med']:.2f} max={d['max']:.0f} p99={d['p99']:.2f} z%={d['zpct']:.1f}")
    fig,axes=plt.subplots(1,3,figsize=(15,4))
    for i,(nm,arr) in enumerate([("degree",tot_d),("in",in_d),("out",out_d)]):
        ax=axes[i]; s=arr[arr>0].astype(float)
        ax.hist(np.log10(s),bins=80,edgecolor="none",alpha=0.85); ax.set_xlabel(f"log10({nm})"); ax.set_title(f"{nm} (log)")
    fig.tight_layout(); sf(fig,"06_degree")
    sl=int((ei[0]==ei[1]).sum()); r.p(f"\n  Self-loops: {sl:,}")
    r.sub("5.2 Direction")
    es=set(zip(ei[0].tolist(),ei[1].tolist())); bi=sum(1 for s,d in es if (d,s) in es)//2
    r.p(f"  Edges: {len(ei[0]):,}  Unique pairs: {len(es):,}  Bidirectional: {bi:,}")

# 6 Class diff
def s06(r,D):
    r.sec("6. Per-Class Feature Differences")
    X,y,cols=D["x"],D["y"],D["fc"]
    r.sub("6.1 Stats")
    for i,c in enumerate(cols):
        r.p(f"[{c}]")
        for lid in range(1,6):
            s=X[y==lid,i]; s=s[~np.isnan(s)]
            if len(s)==0: continue
            r.p(f"  {LABELS[lid]:12s} mu={np.mean(s):12.4f} med={np.median(s):12.4f} sd={np.std(s):12.4f} n={len(s)}")
        r.p()
    r.sub("6.2 Kruskal-Wallis")
    for i,c in enumerate(cols):
        gs=[X[y==lid,i] for lid in range(1,6)]; gs=[g[~np.isnan(g)] for g in gs]; gs=[g for g in gs if len(g)>0]
        if len(gs)>=2:
            st,p=sp_stats.kruskal(*gs); sig="***" if p<0.001 else "**" if p<0.01 else "*" if p<0.05 else "n.s."
            r.p(f"  {c:30s} H={st:12.2f} p={p:.2e} {sig}")
    kf=["degree","degree_in","degree_out","total_transactions_in","total_transactions_out","total_sent","total_received","cluster_size"]
    ki=[cols.index(c) for c in kf if c in cols]; n=len(ki); nc=4; nr=(n+nc-1)//nc
    fig,axes=plt.subplots(nr,nc,figsize=(5*nc,4*nr)); axes=np.atleast_2d(axes)
    for k,i in enumerate(ki):
        ax=axes[k//nc,k%nc]; data=[X[y==lid,i] for lid in range(1,6)]
        bp=ax.boxplot(data,tick_labels=TARGETS,showfliers=False,patch_artist=True)
        for patch,col in zip(bp["boxes"],sns.color_palette("Set2",5)): patch.set_facecolor(col)
        ax.set_title(cols[i],fontsize=9); ax.tick_params(labelsize=7,axis="x",rotation=30)
    for k in range(n,nr*nc): axes[k//nc,k%nc].set_visible(False)
    fig.suptitle("Features by Class"); fig.tight_layout(); sf(fig,"08_class_box")
    r.sub("6.3 PCA + t-SNE")
    from sklearn.decomposition import PCA; from sklearn.manifold import TSNE; from sklearn.preprocessing import StandardScaler
    si=[]
    for lid in range(1,6):
        ci=np.where(y==lid)[0]; rng=np.random.RandomState(42); si.extend(rng.choice(ci,min(len(ci),200),replace=False).tolist())
    si=np.array(si); Xs=np.nan_to_num(X[si],nan=0.0); ys=y[si]; Xs=StandardScaler().fit_transform(Xs); yi=ys-1
    pca=PCA(n_components=2,random_state=42); Xp=pca.fit_transform(Xs)
    fig,ax=plt.subplots(figsize=(8,6)); sc=ax.scatter(Xp[:,0],Xp[:,1],c=yi,cmap="Set2",s=12,alpha=0.7,edgecolors="none")
    h,_=sc.legend_elements(); ax.legend(h,TARGETS,title="Class",fontsize=8)
    ax.set_xlabel(f"PC1 ({pca.explained_variance_ratio_[0]:.1%})"); ax.set_ylabel(f"PC2 ({pca.explained_variance_ratio_[1]:.1%})")
    ax.set_title("PCA (labeled)"); sf(fig,"09_pca")
    Xt=TSNE(n_components=2,perplexity=min(30,max(5,len(si)//10)),random_state=42,max_iter=1000).fit_transform(Xs)
    fig,ax=plt.subplots(figsize=(8,6)); sc=ax.scatter(Xt[:,0],Xt[:,1],c=yi,cmap="Set2",s=12,alpha=0.7,edgecolors="none")
    h,_=sc.legend_elements(); ax.legend(h,TARGETS,title="Class",fontsize=8); ax.set_title("t-SNE (labeled)"); sf(fig,"10_tsne")

# 7 Inter-class edges
def s07(r,D):
    r.sec("7. Inter-Class Edge Patterns")
    ei,y=D["ei"],D["y"]; lm=y!=0
    sl=y[ei[0]]; dl=y[ei[1]]; bl=lm[ei[0]]&lm[ei[1]]; nb=int(bl.sum())
    r.p(f"Both-endpoint labeled edges: {nb:,}/{len(ei[0]):,}")
    if nb==0: r.p("No labeled-labeled edges"); return
    src_l=sl[bl]; dst_l=dl[bl]
    r.sub("7.1 Matrix")
    cross=np.zeros((6,6),dtype=int)
    for s,d in zip(src_l,dst_l): cross[int(s),int(d)]+=1
    r.p("src\\dst  " + "  ".join(f"{l:>12s}" for l in LABELS))
    for i in range(6): r.p(f"{LABELS[i]:>10s} " + "  ".join(f"{cross[i,j]:>12d}" for j in range(6)))
    fig,ax=plt.subplots(figsize=(8,6))
    sns.heatmap(np.log1p(cross[1:,1:]),annot=cross[1:,1:],fmt="d",cmap="YlOrRd",xticklabels=TARGETS,yticklabels=TARGETS,ax=ax)
    ax.set_xlabel("Dest"); ax.set_ylabel("Src"); ax.set_title("Inter-class Edges"); sf(fig,"11_inter_class")
    r.sub("7.2 Homophily")
    for lid in range(1,6):
        m=src_l==lid
        if m.sum()==0: continue
        same=int((dst_l[m]==lid).sum()); tot=int(m.sum())
        r.p(f"  {LABELS[lid]:12s}: {same}/{tot} ({same/tot*100:.1f}%) same-class edges")

# 8 Temporal
def s08(r,D):
    r.sec("8. Temporal Analysis")
    X,y,cols=D["x"],D["y"],D["fc"]
    tc={c:cols.index(c) for c in ["first_transaction_in","last_transaction_in","first_transaction_out","last_transaction_out"] if c in cols}
    if not tc: r.p("No temporal columns"); return
    r.sub("8.1 Ranges")
    for c,i in tc.items():
        v=X[:,i]; v=v[~np.isnan(v)]; r.p(f"  {c}: {v.min():.0f} ~ {v.max():.0f}")
    r.sub("8.2 Per-Class")
    for lid in range(1,6):
        parts=[]
        for c,i in tc.items():
            v=X[y==lid,i]; v=v[~np.isnan(v)]; parts.append(f"{c}={np.mean(v):.0f}" if len(v)>0 else f"{c}=N/A")
        r.p(f"  {LABELS[lid]:12s}: {', '.join(parts)}")
    r.sub("8.3 Duration")
    if "last_transaction_in" in tc and "first_transaction_in" in tc:
        d=X[:,tc["last_transaction_in"]]-X[:,tc["first_transaction_in"]]
        r.p("[in_duration]")
        for lid in range(1,6):
            v=d[y==lid]; v=v[~np.isnan(v)]
            if len(v)>0: r.p(f"  {LABELS[lid]:12s}: mu={np.mean(v):.0f} med={np.median(v):.0f}")
    if "last_transaction_out" in tc and "first_transaction_out" in tc:
        d=X[:,tc["last_transaction_out"]]-X[:,tc["first_transaction_out"]]
        r.p("[out_duration]")
        for lid in range(1,6):
            v=d[y==lid]; v=v[~np.isnan(v)]
            if len(v)>0: r.p(f"  {LABELS[lid]:12s}: mu={np.mean(v):.0f} med={np.median(v):.0f}")
    Ea,ecols=D["ea"],D["ec"]
    if Ea.shape[1]>0 and "last_seen" in ecols and "reveal" in ecols:
        r.sub("8.4 Edge Temporal")
        li=ecols.index("last_seen"); ri=ecols.index("reveal")
        ls=Ea[:,li]; rv=Ea[:,ri]; dur=np.clip(ls-rv,0,None)
        d=desc(dur); r.p(f"[edge_dur] mu={d['mu']:.2f} med={d['med']:.2f} p95={d['p95']:.2f}")
        d2=desc(ls); r.p(f"[edge_ls] mu={d2['mu']:.2f} med={d2['med']:.2f} range={d2['min']:.0f}~{d2['max']:.0f}")
        fig,ax=plt.subplots(figsize=(10,4)); s=ls[~np.isnan(ls)]
        if len(s)>200000: s=np.random.RandomState(42).choice(s,200000,replace=False)
        ax.hist(s,bins=100,edgecolor="none",alpha=0.85); ax.set_xlabel("last_seen (block)"); ax.set_title("Edge last_seen"); sf(fig,"12_edge_ls")

# 9 Neighborhood
def s09(r,D):
    r.sec("9. Neighborhood Composition")
    ei,y=D["ei"],D["y"]; lm=y!=0
    cn=defaultdict(lambda: Counter())
    src,dst=ei[0],ei[1]
    for i in range(len(src)):
        s,d=int(src[i]),int(dst[i])
        if lm[s]: cn[int(y[s])][int(y[d])]+=1
        if lm[d]: cn[int(y[d])][int(y[s])]+=1
    r.sub("9.1 Distribution")
    hdr="class     " + "  ".join(f"{l:>12s}" for l in LABELS); r.p(hdr)
    for lid in range(1,6):
        if lid not in cn: continue
        tot=sum(cn[lid].values())
        r.p(f"{LABELS[lid]:>10s} " + "  ".join(f"{cn[lid].get(nl,0):>5d}({cn[lid].get(nl,0)/tot*100:.1f}%)" if tot else "0" for nl in range(6)))
    r.sub("9.2 Homophily")
    for lid in range(1,6):
        if lid not in cn: continue
        tot=sum(cn[lid].values()); same=cn[lid].get(lid,0)
        r.p(f"  {LABELS[lid]:12s}: {same/tot*100 if tot else 0:.1f}% same ({same}/{tot})")
    fig,ax=plt.subplots(figsize=(10,5)); bot=np.zeros(5); pal=sns.color_palette("Set2",6)
    for nlid in range(6):
        vals=[cn[lid].get(nlid,0)/sum(cn[lid].values())*100 if lid in cn and sum(cn[lid].values()) else 0 for lid in range(1,6)]
        ax.bar(TARGETS,vals,bottom=bot,label=LABELS[nlid],color=pal[nlid],edgecolor="none"); bot+=np.array(vals)
    ax.set_ylabel("%"); ax.set_title("1-hop Neighbor Labels"); ax.legend(title="Nbr",bbox_to_anchor=(1.02,1),loc="upper left",fontsize=8)
    fig.tight_layout(); sf(fig,"13_nbr")

# 10 Summary
def s10(r,D):
    r.sec("10. Key Findings")
    y=D["y"]; tc={LABELS[i]:int((y==i).sum()) for i in range(1,6)}
    for l in [
        "",
        "=== DATASET ===",
        f"  Subgraph: {D['x'].shape[0]:,} nodes, {D['ei'].shape[1]:,} edges",
        f"  Node feats: {D['x'].shape[1]}d, Edge feats: {D['ea'].shape[1]}d",
        f"  Full DB: ~252M nodes, ~786M edges",
        "",
        "=== FINDING 1: EXTREME IMBALANCE ===",
        f"  {', '.join(f'{k}={v}' for k,v in tc.items())}",
        f"  Ratio: {tc['INDIVIDUAL']/max(tc['BRIDGE'],1):.0f}x",
        "  => focal loss / class weighting / balanced sampling",
        "",
        "=== FINDING 2: LABEL SPARSITY ===",
        f"  {(y!=0).sum():,}/{len(y):,} = {(y!=0).sum()/len(y)*100:.3f}%",
        "  => semi-supervised / pseudo-label / contrastive learning",
        "",
        "=== FINDING 3: RICH EDGE FEATURES (UNUSED) ===",
        "  6-dim + derivable: avg_sent, range, duration, freq, recency",
        "  => edge-aware message passing",
        "",
        "=== FINDING 4: TEMPORAL INFO ===",
        "  Nodes: first/last_transaction_in/out (block height)",
        "  Edges: reveal, last_seen",
        "  => recency encoding + temporal split",
        "",
        "=== FINDING 5: DIRECTED ===",
        "  a->b = fund flow direction",
        "  => direction-aware aggregation",
        "",
        "=== FINDING 6: GNN < MLP ===",
        "  GraphSAGE F1~0.67 < MLP~0.70",
        "  => research opportunity",
    ]: r.p(l)

def main():
    os.makedirs(FIG_DIR, exist_ok=True)
    D=load(); rpt=R()
    t0=datetime.now(); rpt.p(f"EDA: {t0:%Y-%m-%d %H:%M:%S}"); rpt.p(f"Data: {DATA_PT}")
    for nm,fn in [("1.Overview",s01),("2.Nodes",s02),("3.Labels",s03),("4.Edges",s04),
        ("5.Topo",s05),("6.ClassDiff",s06),("7.InterClass",s07),("8.Temporal",s08),
        ("9.Nbr",s09),("10.Summary",s10)]:
        print(f"[{nm}] ...")
        try: fn(rpt,D); print(f"[{nm}] OK")
        except Exception as e:
            rpt.p(f"\n** ERROR {nm}: {e} **")
            import traceback; rpt.p(traceback.format_exc()); print(f"[{nm}] FAIL: {e}")
    rpt.p(f"\nTotal: {datetime.now()-t0}"); rpt.save(RPT_PATH)
    print(f"\nDone! {datetime.now()-t0}\nReport: {RPT_PATH}\nFigs: {FIG_DIR}/")

if __name__=="__main__": main()
