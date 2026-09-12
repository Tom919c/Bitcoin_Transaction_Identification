#!/usr/bin/env python3
"""Evaluate frozen, label-free Gate 3A v1.3 S0 extraction output."""
import argparse
import hashlib
import json
import random
import sqlite3
import os
import platform
import math
from collections import defaultdict
from pathlib import Path

PROTOCOL_VERSION = "Gate3A-v1.3-20260912"
SEED = 20260911
REPLICATES = 10_000
PRIMARY_HORIZON = 52560
BLOCK_LENGTHS = (144, 72, 288)
PROFILES = ("F_pub", "F_wide", "F_none")
UNION_HASH_PROFILES = tuple(sorted(PROFILES))
EXPECTED_MANIFEST = "e32ad2f33ecbc184eb04159f0adbb22dd2a4a1a47f1e280cbbca699432d67f3d"


def _sha(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
def _json(obj): return json.dumps(obj, sort_keys=True, ensure_ascii=True, separators=(",", ":"))
def _bytes(value, name):
    if not isinstance(value, bytes) or len(value) != 32: raise ValueError(f"invalid {name}")
    return value
def _hex(value, name): return _bytes(value, name).hex()
def _ids(blob):
    if len(blob) % 32: raise ValueError("packed script IDs have invalid length")
    ids = tuple(bytes(blob)[i:i + 32] for i in range(0, len(blob), 32))
    if ids != tuple(sorted(set(ids))): raise ValueError("packed script IDs must be sorted and unique")
    return ids

def _hash_records(records):
    digest = hashlib.sha256()
    for record in records:
        digest.update(_json(record).encode("ascii") + b"\n")
    return digest.hexdigest()


def _union_where(profile):
    return {"F_pub": "exclude_f_pub=0", "F_wide": "exclude_f_wide=0", "F_none": "1"}[profile]


def _union_hash(con):
    """Hash complete provenance records from indexed raw events, never profile view."""
    digest = hashlib.sha256()
    version, manifest = con.execute("SELECT heuristic_version,source_manifest_sha256 FROM run_context WHERE context_id=1").fetchone()
    # Preserve the committed view hash's lexical profile-major byte order.
    for profile in UNION_HASH_PROFILES:
        query = "SELECT event_id,block_hash,height,txid,tx_index,event_index,script_id_a,script_id_b,exclude_f_pub,exclude_f_wide,evidence_json FROM union_events ORDER BY height,tx_index,event_index,script_id_a,script_id_b,event_id"
        for event_id, block_hash, height, txid, tx_index, event_index, left, right, pub, wide, evidence in con.execute(query):
            record = {"event_id": _hex(event_id, "event_id"), "block_hash": _hex(block_hash, "block_hash"),
                      "block_height": height, "txid": _hex(txid, "txid"), "tx_index": tx_index,
                      "event_index": event_index, "script_id_a": _hex(left, "script_id_a"),
                      "script_id_b": _hex(right, "script_id_b"), "filter_profile": profile,
                      "filter_decision": "exclude" if (profile == "F_pub" and pub) or (profile == "F_wide" and wide) else "include", "exclude_f_pub": pub, "exclude_f_wide": wide,
                      "evidence_json": evidence, "heuristic_id": "common-input",
                      "heuristic_version": version, "source_manifest_sha256": manifest,
                      "profile_view_version": "s0-profile-view-v1"}
            digest.update(_json(record).encode("ascii") + b"\n")
    return digest.hexdigest()

def _atomic_new(path, payload):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists(): raise FileExistsError("refusing to overwrite output")
    temporary = path.with_name(path.name + ".tmp")
    try:
        with open(temporary, "xb") as handle: handle.write(payload)
        # Hard-link creation is atomic and refuses an already-created destination.
        os.link(temporary, path)
    finally:
        if temporary.exists(): temporary.unlink()


class DSU:
    def __init__(self): self.p = {}
    def find(self, x):
        self.p.setdefault(x, x)
        while x != self.p[x]:
            self.p[x] = self.p[self.p[x]]; x = self.p[x]
        return x
    def union(self, a, b):
        a, b = self.find(a), self.find(b)
        if a != b: self.p[max(a, b)] = min(a, b)
    def root(self, x):
        return self.find(x) if x in self.p else x


def _restricted_representatives(dsu, support):
    minimum = {}
    for script in support:
        root = dsu.root(script)
        if root not in minimum or script < minimum[root]:
            minimum[root] = script
    return {script: minimum[dsu.root(script)] for script in support}


def _representatives(events, cutoff, support):
    d = DSU()
    for e in events:
        if e[0] <= cutoff: d.union(e[3], e[4])
    return _restricted_representatives(d, support)


def iter_partition_cells(con, windows, support_by_window, horizons, instrumentation=None, target_height=286560):
    """Yield Ct/CT maps at T, retaining Ct only until a window's final T."""
    for profile in PROFILES:
        available = [(window, horizon) for window in windows for horizon in horizons
                     if window["cutoff_height"] + horizon <= target_height]
        required = sorted({(window["cutoff_height"], window["window_id"], 0)
                           for window, _ in available} |
                          {(window["cutoff_height"] + horizon, window["window_id"], horizon)
                           for window, horizon in available})
        dsu = DSU()
        if instrumentation is not None:
            instrumentation["dsu_cursors"] = instrumentation.get("dsu_cursors", 0) + 1
            instrumentation.setdefault("dsu_profiles", []).append(profile)
        cursor = iter(con.execute("SELECT height,script_id_a,script_id_b FROM union_events WHERE " + _union_where(profile) + " ORDER BY height,tx_index,event_index,script_id_a,script_id_b,event_id"))
        event = next(cursor, None)
        ct_maps = {}
        last_horizon = {window["window_id"]: max(h for candidate, h in available
                                                  if candidate["window_id"] == window["window_id"])
                        for window in windows}
        for boundary, window_id, horizon in required:
            while event is not None and event[0] <= boundary:
                _, left, right = event
                dsu.union(_bytes(left, "script_id_a"), _bytes(right, "script_id_b"))
                event = next(cursor, None)
            support = support_by_window[window_id]
            representatives = _restricted_representatives(dsu, support)
            if not horizon:
                ct_maps[window_id] = representatives
                if instrumentation is not None:
                    instrumentation["max_live_ct_maps"] = max(instrumentation.get("max_live_ct_maps", 0), len(ct_maps))
                continue
            yield profile, window_id, horizon, ct_maps[window_id], representatives
            if horizon == last_horizon[window_id]:
                del ct_maps[window_id]


def secondary_statistics(records, representatives_t, representatives_T):
    """Frozen descriptive structure statistics; never used by Go/No-Go."""
    support = representatives_t
    ct_sizes = defaultdict(int)
    for script in support:
        ct_sizes[representatives_t[script]] += 1
    ct_roots_by_T = defaultdict(set)
    for script in support: ct_roots_by_T[representatives_T[script]].add(representatives_t[script])
    merge_groups = [roots for roots in ct_roots_by_T.values() if len(roots) >= 2]
    affected = set().union(*merge_groups) if merge_groups else set()
    cross_transactions = became_loop_transactions = rewritten_weight = total_weight = 0
    old_edges, new_edges = set(), set()
    contingency = defaultdict(int)
    for script in support:
        contingency[(representatives_t[script], representatives_T[script])] += 1
    for row in records:
        if row[6]:
            continue
        old_in = tuple(sorted({representatives_t[x] for x in row[4]}))
        old_out = tuple(sorted({representatives_t[x] for x in row[5]}))
        new_in = tuple(sorted({representatives_T[x] for x in row[4]}))
        new_out = tuple(sorted({representatives_T[x] for x in row[5]}))
        changed = (old_in, old_out) != (new_in, new_out)
        weight = row[8]
        total_weight += weight
        rewritten_weight += weight * changed
        crosses = False
        became_loop = False
        for left in old_in:
            for right in old_out:
                old_edges.add((left, right))
                if left != right:
                    crosses = True
                    became_loop |= representatives_T[left] == representatives_T[right]
        for left in new_in:
            for right in new_out:
                new_edges.add((left, right))
        cross_transactions += crosses
        became_loop_transactions += crosses and became_loop
    n = len(support); p_t = {key: value / n for key, value in ct_sizes.items()}
    ct_T = defaultdict(int)
    for script in support: ct_T[representatives_T[script]] += 1
    p_T = {key: value / n for key, value in ct_T.items()}
    vi = -2 * sum((count / n) * math.log(count / n) for count in contingency.values())
    vi += sum(p * math.log(p) for p in p_t.values()) + sum(p * math.log(p) for p in p_T.values())
    percentile = lambda values, q: values[min(len(values) - 1, math.ceil(q * len(values)) - 1)] if values else 0
    group_components = sorted(map(len, merge_groups))
    group_scripts = sorted(sum(ct_sizes[root] for root in roots) for roots in merge_groups)
    return {"affected_ct_entity_fraction": len(affected) / len(ct_sizes),
            "node_compression_fraction": (len(ct_sizes) - len(ct_T)) / len(ct_sizes),
            "cross_entity_to_self_loop_fraction": became_loop_transactions / cross_transactions if cross_transactions else 0.0,
            "cross_entity_to_self_loop_transaction_counts": {"numerator": became_loop_transactions, "denominator": cross_transactions, "definition": "noncoinbase transaction with a Ct cross-entity endpoint pair; numerator has at least one such pair merged in CT"},
            "edge_aggregation_fraction": (len(old_edges) - len(new_edges)) / len(old_edges) if old_edges else 0.0,
            "merged_ct_component_group_count": len(merge_groups),
            "merged_ct_components_per_group_quantiles": {"p50": percentile(group_components, .5), "p90": percentile(group_components, .9)},
            "merged_support_scripts_per_group_quantiles": {"p50": percentile(group_scripts, .5), "p90": percentile(group_scripts, .9)},
            "amount_weighted_endpoint_rewrite_fraction": rewritten_weight / total_weight if total_weight else 0.0,
            "amount_weight_definition": "output_sat",
            "variation_of_information": vi}


def _seed(manifest, window_id, horizon, profile, length):
    text = f"{SEED}|{manifest}|{window_id}|{horizon}|{profile}|{length}".encode("ascii")
    return int.from_bytes(hashlib.sha256(text).digest()[:8], "big")


def _bootstrap_samples(blocks, manifest, window_id, horizon, profile, length, replicates=REPLICATES):
    width = len(blocks)
    if not width: raise ValueError("empty window")
    draws = -(-width // length); rng = random.Random(_seed(manifest, window_id, horizon, profile, length))
    prefixes = [[0] for _ in range(4)]
    for block in blocks * 2:
        for column, value in enumerate(block): prefixes[column].append(prefixes[column][-1] + value)
    samples = [[], []]; index_hash = hashlib.sha256()
    for _ in range(replicates):
        mnum = mden = rnum = rden = 0
        starts = [rng.randrange(width) for _ in range(draws)]
        index_hash.update(_json(starts).encode() + b"\n")
        taken = 0
        for start in starts:
            segment_length = min(length, width - taken)
            a, b, c, d = (prefix[start + segment_length] - prefix[start] for prefix in prefixes)
            mnum += a; mden += b; rnum += c; rden += d
            taken += length
        if not mden or not rden: raise ValueError("bootstrap replicate has zero denominator")
        samples[0].append(mnum / mden); samples[1].append(rnum / rden)
    return samples, index_hash


def _bootstrap(blocks, manifest, window_id, horizon, profile, length):
    samples, index_hash = _bootstrap_samples(blocks, manifest, window_id, horizon, profile, length)
    merge_samples, rewrite_samples = sorted(samples[0]), sorted(samples[1])
    return {"cell_seed": _seed(manifest, window_id, horizon, profile, length), "replicates": REPLICATES,
            "block_length": length, "resample_indices_sha256": index_hash.hexdigest(),
            "p_merge": {"sorted_replicates": merge_samples, "lower": merge_samples[249], "upper": merge_samples[9749]},
            "p_rewrite": {"sorted_replicates": rewrite_samples, "lower": rewrite_samples[249], "upper": rewrite_samples[9749]}}


def _graph(records, reps, meta):
    digest = hashlib.sha256(); byte_count = 0
    counts = {"meta": 0, "node": 0, "transaction": 0, "edge": 0}
    def write(record):
        nonlocal byte_count
        raw = _json(record).encode("ascii") + b"\n"
        digest.update(raw); byte_count += len(raw); counts[record["record_type"]] += 1
    write(meta)
    nodes = sorted(set(reps.values()))
    for node in nodes: write({"record_type": "node", "script_id": node.hex()})
    previous = None
    for r in records:
        h, bh, idx, txid, ins, outs, coinbase, insat, outsat, fee = r
        key = (h, idx, txid)
        if previous is not None and key <= previous: raise ValueError("transactions must be strictly ordered")
        previous = key
        if coinbase: continue
        inp, out = sorted({reps[x] for x in ins}), sorted({reps[x] for x in outs})
        tx = {"block_hash": bh.hex(), "block_height": h, "fee_sat": fee, "input_entities": [x.hex() for x in inp],
              "input_sat": insat, "output_entities": [x.hex() for x in out], "output_sat": outsat,
              "record_type": "transaction", "tx_index": idx, "txid": txid.hex()}
        write(tx)
    for h, _, idx, txid, ins, outs, coinbase, _, _, _ in records:
        if coinbase: continue
        for source in sorted({reps[x] for x in ins}):
            for target in sorted({reps[x] for x in outs}):
                write({"block_height": h, "record_type": "edge", "source": source.hex(), "target": target.hex(), "tx_index": idx, "txid": txid.hex()})
    return {"sha256": digest.hexdigest(), "bytes": byte_count, "record_counts": counts}


def validate(summary, db):
    if summary.get("status") != "s0_union_extraction_complete" or not summary.get("s0_extraction_complete"):
        raise ValueError("extractor summary is not completed")
    if any(summary.get(k) is not False for k in ("labels_read", "effect_metrics_read", "models_authorized")):
        raise ValueError("summary violates label/model/effect boundary")
    if summary.get("source_manifest_sha256") != EXPECTED_MANIFEST or summary.get("target_height") != 286560 or summary.get("last_complete_height") != 286560:
        raise ValueError("summary violates frozen manifest or target")
    uri = f"file:{Path(db).resolve().as_posix()}?mode=ro"
    con = sqlite3.connect(uri, uri=True)
    try:
        con.execute("PRAGMA query_only=ON")
        if con.execute("PRAGMA quick_check").fetchone()[0] != "ok": raise ValueError("SQLite quick_check failed")
        ctx = con.execute("SELECT source_manifest_sha256, runner_sha256, target_height, design_json FROM run_context WHERE context_id=1").fetchone()
        if not ctx: raise ValueError("missing run context")
        if ctx[0] != summary.get("source_manifest_sha256") or ctx[1] != summary.get("runner_sha256") or ctx[2] != summary.get("last_complete_height"):
            raise ValueError("summary/database binding mismatch")
        if json.loads(ctx[3]) != summary.get("design"): raise ValueError("design binding mismatch")
        expected = {"cutoff_heights": [181440,199584,215712,225792], "window_blocks": 2016,
                    "primary_horizon_blocks": 52560, "profiles": ["F_pub","F_wide"],
                    "sensitivity_horizon_blocks": [13140,105120], "bootstrap_replicates": 10000,
                    "bootstrap_block_lengths": [144,72,288]}
        if any(summary["design"].get(k) != v for k,v in expected.items()): raise ValueError("frozen design mismatch")
        expected_windows = [{"window_id": f"t{cutoff}", "cutoff_height": cutoff,
                             "win_start_height": cutoff - 2015, "win_end_height": cutoff,
                             "window_blocks": 2016} for cutoff in expected["cutoff_heights"]]
        if summary.get("windows") != expected_windows:
            raise ValueError("frozen windows mismatch")
        horizon_cells = summary.get("horizon_cells")
        expected_cells = [{"cutoff_height": cutoff, "horizon_blocks": horizon,
                           "future_end_height": cutoff + horizon,
                           "available": cutoff + horizon <= 286560}
                          for cutoff in expected["cutoff_heights"] for horizon in (13140, 52560, 105120)]
        if horizon_cells != expected_cells:
            raise ValueError("frozen horizon cells mismatch")
        metadata = {key: json.loads(value) for key,value in con.execute("SELECT key,value FROM metadata")}
        if metadata.get("last_committed_height") != 286560 or metadata.get("counters") != summary.get("transaction_counters") or metadata.get("s0_counters") != summary.get("s0_counters"):
            raise ValueError("checkpoint metadata mismatch")
        for table, key in (("union_events", "union_events"), ("window_transactions", "window_transactions"), ("window_support", "window_support")):
            if con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] != summary["s0_counters"][key]: raise ValueError(f"{table} count mismatch")
        block_rows = con.execute("SELECT filter_profile,COUNT(*),COUNT(DISTINCT height),MIN(height),MAX(height) FROM block_profile_stats GROUP BY filter_profile ORDER BY filter_profile").fetchall()
        if sorted(block_rows) != sorted((profile, 286561, 286561, 0, 286560) for profile in PROFILES) or sum(row[1] for row in block_rows) != summary["s0_counters"].get("block_profile_stat_rows"):
            raise ValueError("block profile stats count mismatch")
        return con, ctx[0], summary["design"], summary["windows"]
    except Exception:
        con.close(); raise


def _window_support(con, window):
    wid = window["window_id"]
    first_height = {_bytes(script, "support"): height for script, height in con.execute("SELECT script_id,first_height FROM window_support WHERE window_id=?", (wid,))}
    support = set(first_height)
    if not support or len(first_height) != len(support): raise ValueError("invalid support")
    if any(not isinstance(h, int) or not window["win_start_height"] <= h <= window["win_end_height"] for h in first_height.values()): raise ValueError("support first height outside window")
    return support, first_height


def _window_records(con, window, support):
    wid = window["window_id"]
    records = []
    for r in con.execute("SELECT height,block_hash,tx_index,txid,input_script_ids,output_script_ids,is_coinbase,input_sat,output_sat,fee_sat FROM window_transactions WHERE window_id=? ORDER BY height,tx_index,txid", (wid,)):
        h,bh,idx,txid,ins,outs,coinbase,insat,outsat,fee=r
        if not window["win_start_height"] <= h <= window["win_end_height"]: raise ValueError("transaction outside window")
        input_ids, output_ids, is_coinbase = _ids(ins), _ids(outs), bool(coinbase)
        if any(script not in support for script in input_ids + output_ids): raise ValueError("transaction endpoint outside support")
        if not isinstance(outsat, int) or (not is_coinbase and (not isinstance(insat, int) or not isinstance(fee, int))): raise ValueError("transaction amount must be integer")
        records.append((h,_bytes(bh,"block_hash"),idx,_bytes(txid,"txid"),input_ids,output_ids,is_coinbase,insat,outsat,fee))
    return records


def _cell(window, profile, horizon, support, first_height, records, rt, rT, manifest, summary_hash):
    first_ct_root, merged_future_roots = {}, set()
    for script in support:
        future_root, current_root = rT[script], rt[script]
        if future_root in first_ct_root and first_ct_root[future_root] != current_root:
            merged_future_roots.add(future_root)
        else:
            first_ct_root[future_root] = current_root
    byblock = {height: [0, 0, 0, 0] for height in range(window["win_start_height"], window["win_end_height"] + 1)}
    for script in support:
        values = byblock[first_height[script]]; values[1] += 1; values[0] += rT[script] in merged_future_roots
    for record in records:
        if record[6]: continue
        values = byblock[record[0]]; values[3] += 1
        values[2] += (sorted({rt[x] for x in record[4]}), sorted({rt[x] for x in record[5]})) != (sorted({rT[x] for x in record[4]}), sorted({rT[x] for x in record[5]}))
    blocks = [byblock[height] for height in sorted(byblock)]
    if not sum(x[1] for x in blocks) or not sum(x[3] for x in blocks): raise ValueError("zero denominator")
    support_hash = _hash_records({"script_id": script.hex(), "first_height": first_height[script]} for script in sorted(support))
    transaction_hash = _hash_records({"height":r[0],"block_hash":r[1].hex(),"tx_index":r[2],"txid":r[3].hex(),"input_script_ids":[x.hex() for x in r[4]],"output_script_ids":[x.hex() for x in r[5]],"is_coinbase":r[6],"input_sat":r[7],"output_sat":r[8],"fee_sat":r[9]} for r in records)
    entry = {"window_id":window["window_id"],"horizon_blocks":horizon,"filter_profile":profile,"support_sha256":support_hash,"transaction_sha256":transaction_hash,"partition_sha256":{"Ct":_hash_records({"script_id":s.hex(),"representative":rt[s].hex()} for s in sorted(support)),"CT":_hash_records({"script_id":s.hex(),"representative":rT[s].hex()} for s in sorted(support))},"point":{"p_merge":sum(x[0] for x in blocks)/sum(x[1] for x in blocks),"p_rewrite":sum(x[2] for x in blocks)/sum(x[3] for x in blocks)},"bootstrap":{}}
    entry["secondary"] = secondary_statistics(records, rt, rT)
    for length in BLOCK_LENGTHS: entry["bootstrap"][str(length)] = _bootstrap(blocks, manifest, window["window_id"], horizon, profile, length)
    meta = {"analysis_cutoff_height":window["cutoff_height"],"extractor_summary_sha256":summary_hash,"filter_profile":profile,"horizon_blocks":horizon,"partition_cutoff_height":window["cutoff_height"]+horizon,"partition_vintage":"B","record_type":"meta","schema_version":"asof-entity-endpoint-multigraph-v1","source_manifest_sha256":manifest,"window_id":window["window_id"]}
    entry["graphs"] = {"B":_graph(records, rT, meta), "C":_graph(records, rt, {**meta, "partition_cutoff_height":window["cutoff_height"], "partition_vintage":"C"})}
    return entry


def evaluate(summary_path, db_path, output):
    if Path(output).exists(): raise FileExistsError("refusing to overwrite output")
    summary = json.loads(Path(summary_path).read_text(encoding="utf-8")); summary_hash = _sha(summary_path)
    con, manifest, design, windows = validate(summary, db_path)
    try:
        if design.get("primary_horizon_blocks") != PRIMARY_HORIZON or design.get("bootstrap_replicates") != REPLICATES or tuple(design.get("bootstrap_block_lengths", [])) != BLOCK_LENGTHS: raise ValueError("frozen design mismatch")
        horizons = (PRIMARY_HORIZON, 13140, 105120)
        window_by_id = {window["window_id"]: window for window in windows}
        support_by_window = {wid: _window_support(con, window) for wid, window in window_by_id.items()}
        if any(not support for support, _ in support_by_window.values()): raise ValueError("zero support denominator")
        union_hash = _union_hash(con)
        cells = []
        for profile, wid, horizon, rt, rT in iter_partition_cells(con, windows, {key: value[0] for key, value in support_by_window.items()}, horizons, target_height=summary["last_complete_height"]):
            support, first_height = support_by_window[wid]
            # ponytail: reload one window per cell to cap peak RAM while the
            # full-chain DSU is live; add a canonical disk cache only if I/O
            # is measured to dominate the full evaluation.
            records = _window_records(con, window_by_id[wid], support)
            cells.append(_cell(window_by_id[wid], profile, horizon, support, first_height, records, rt, rT, manifest, summary_hash))
            del records
        primary=[x for x in cells if x["horizon_blocks"]==PRIMARY_HORIZON and x["filter_profile"] in ("F_pub","F_wide")]
        expected_primary = {(f"t{cutoff}", profile) for cutoff in design["cutoff_heights"] for profile in ("F_pub", "F_wide")}
        if {(cell["window_id"], cell["filter_profile"]) for cell in primary} != expected_primary or len(primary) != 8:
            raise ValueError("primary cells mismatch")
        # Both metrics must clear the threshold in the same historical window.
        # Counting each metric independently would create an invalid synthetic Go.
        go = all(
            sum(
                x["bootstrap"]["144"]["p_merge"]["lower"] >= .01
                and x["bootstrap"]["144"]["p_rewrite"]["lower"] >= .01
                for x in primary
                if x["filter_profile"] == profile
            ) >= 3
            for profile in ("F_pub", "F_wide")
        )
        no=any(all(sum(x["bootstrap"]["144"][m]["upper"]<.01 for x in primary if x["filter_profile"]==p)>=3 for p in ("F_pub","F_wide")) for m in ("p_merge","p_rewrite"))
        result={"protocol_version":PROTOCOL_VERSION,"extractor_summary_sha256":summary_hash,"source_manifest_sha256":manifest,"union_log_sha256":union_hash,"seed":SEED,"runner_sha256":_sha(__file__),"environment":{"python":platform.python_version(),"sqlite":sqlite3.sqlite_version},"inputs":{"summary_sha256":summary_hash,"state_db_sha256":_sha(db_path)},"effect_metrics_read":True,"labels_read":False,"models_authorized":False,"cells":cells,"integrity":{"status":"pending_external_provenance_audit","pending_external_provenance_audit":True},"decision":{"status":"pending","candidate":"Go" if go else "No-Go" if no else "Inconclusive","final_integrity":"pending"}}
        _atomic_new(output, (_json(result)+"\n").encode())
        return result
    finally: con.close()



def self_test():
    assert _seed("a"*64,"t1",52560,"F_pub",144)==_seed("a"*64,"t1",52560,"F_pub",144)
    with sqlite3.connect(":memory:") as con:
        con.execute("create table union_events(event_id,block_hash,height,txid,tx_index,event_index,script_id_a,script_id_b,exclude_f_pub,exclude_f_wide,evidence_json)")
        a, b = bytes.fromhex("a" * 64), bytes.fromhex("b" * 64)
        con.execute("insert into union_events values(?,?,?,?,?,?,?,?,?,?,?)", (bytes.fromhex("e" * 64), bytes.fromhex("c" * 64), 2, bytes.fromhex("d" * 64), 0, 0, a, b, 0, 0, "{}"))
        cells = list(iter_partition_cells(con, [{"window_id":"t1", "cutoff_height":1}], {"t1":{a, b}}, (1,), target_height=2))
    assert len(cells) == len(PROFILES) and all(cell[3][a] != cell[3][b] and cell[4][a] == cell[4][b] for cell in cells)
    print(_json({"self_test":"passed","network":"not_used","effect_metrics_read":False,"s0_decision":None}))

def main():
    p=argparse.ArgumentParser(); p.add_argument("--summary"); p.add_argument("--state-db"); p.add_argument("--output"); p.add_argument("--self-test",action="store_true"); a=p.parse_args()
    if a.self_test: self_test(); return 0
    if not all((a.summary,a.state_db,a.output)): raise ValueError("--summary, --state-db and --output are required")
    evaluate(a.summary,a.state_db,a.output); return 0
if __name__=="__main__": raise SystemExit(main())
