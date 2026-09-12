import hashlib, importlib.util, json, sqlite3
from pathlib import Path
import pytest
from btcaml.data.asof_replay import UnionEvent, replay_partition, restricted_representatives

ROOT=Path(__file__).resolve().parents[1]; P=ROOT/'scripts/research/evaluate_aws_btc_s0.py'
spec=importlib.util.spec_from_file_location('ev',P); ev=importlib.util.module_from_spec(spec); spec.loader.exec_module(ev)
X=ROOT/'scripts/research/extract_aws_btc_s0_events.py'
xspec=importlib.util.spec_from_file_location('extract_s0',X); extract_s0=importlib.util.module_from_spec(xspec); xspec.loader.exec_module(extract_s0)
b = lambda value: bytes.fromhex(value * 64)

def test_graph_exact_bytes_and_seed_and_bootstrap():
    meta={"analysis_cutoff_height":1,"extractor_summary_sha256":"a"*64,"filter_profile":"F_pub","horizon_blocks":52560,"partition_cutoff_height":1,"partition_vintage":"B","record_type":"meta","schema_version":"asof-entity-endpoint-multigraph-v1","source_manifest_sha256":"b"*64,"window_id":"t1"}
    row=(1,b("c"),0,b("d"),(b("a"),),(b("b"),),False,1,1,0)
    graph=ev._graph([row],{b("a"):b("a"),b("b"):b("b")},meta)
    lines=[meta, {'record_type':'node','script_id':'a'*64}, {'record_type':'node','script_id':'b'*64}, {'block_hash':'c'*64,'block_height':1,'fee_sat':0,'input_entities':['a'*64],'input_sat':1,'output_entities':['b'*64],'output_sat':1,'record_type':'transaction','tx_index':0,'txid':'d'*64}, {'block_height':1,'record_type':'edge','source':'a'*64,'target':'b'*64,'tx_index':0,'txid':'d'*64}]
    raw=('\n'.join(ev._json(x) for x in lines)+'\n').encode()
    assert graph['sha256']==hashlib.sha256(raw).hexdigest(); assert ev._seed('b'*64,'t1',52560,'F_pub',144)==ev._seed('b'*64,'t1',52560,'F_pub',144)
    assert ev._bootstrap([[1,1,1,1]],'b'*64,'t1',52560,'F_pub',144)['p_merge']['lower']==1

def test_future_connector_and_zero_denominator_and_decision_no_splice():
    reps=ev._representatives([(11,0,0,'a','z'),(12,0,0,'b','z')],12,{'a','b'})
    assert reps=={'a':'a','b':'a'}
    reference = [UnionEvent('x', 'h', 11, 'x', 0, 0, 'a', 'z', 'common-input', 'v', 'F_none', 'include', '{}', 'm'), UnionEvent('y', 'h', 12, 'y', 0, 0, 'b', 'z', 'common-input', 'v', 'F_none', 'include', '{}', 'm')]
    assert reps == dict(restricted_representatives(replay_partition(reference, 12), {'a', 'b'}))
    with pytest.raises(ValueError,match='zero denominator'): ev._bootstrap([[0,0,0,0]],'a'*64,'t1',1,'F_pub',1)
    # No-Go requires same metric in both profiles; this mixed evidence must not qualify.
    cells=[{'filter_profile':'F_pub','bootstrap':{'144':{'p_merge':{'upper':0},'p_rewrite':{'upper':1}}}}]*4+[{'filter_profile':'F_wide','bootstrap':{'144':{'p_merge':{'upper':1},'p_rewrite':{'upper':0}}}}]*4
    assert not any(all(sum(x['bootstrap']['144'][m]['upper']<.01 for x in cells if x['filter_profile']==p)>=3 for p in ('F_pub','F_wide')) for m in ('p_merge','p_rewrite'))

def test_go_cannot_splice_metrics_across_windows():
    # Each metric clears in three windows, but never together in three windows.
    cells = []
    for profile in ('F_pub', 'F_wide'):
        for merge, rewrite in ((.02, .02), (.02, .02), (.02, 0), (0, .02)):
            cells.append({'filter_profile': profile, 'bootstrap': {'144': {
                'p_merge': {'lower': merge}, 'p_rewrite': {'lower': rewrite}}}})
    assert all(sum(x['bootstrap']['144'][m]['lower'] >= .01 for x in cells if x['filter_profile'] == p) >= 3 for p in ('F_pub','F_wide') for m in ('p_merge','p_rewrite'))
    assert not all(sum(x['bootstrap']['144']['p_merge']['lower'] >= .01 and x['bootstrap']['144']['p_rewrite']['lower'] >= .01 for x in cells if x['filter_profile'] == p) >= 3 for p in ('F_pub','F_wide'))

def test_secondary_statistics_are_descriptive_and_deterministic():
    records = [(1, b('a'), 0, b('b'), (b('1'),), (b('2'),), False, 100, 2, 98),
               (1, b('a'), 1, b('c'), (b('3'),), (b('4'),), False, 1, 8, 0)]
    ct = {b(x):b(x) for x in '1234'}
    future = {b('1'):b('1'), b('2'):b('1'), b('3'):b('3'), b('4'):b('4')}
    stats = ev.secondary_statistics(records, ct, future)
    assert stats['node_compression_fraction'] == .25
    assert stats['cross_entity_to_self_loop_fraction'] == .5
    assert stats['cross_entity_to_self_loop_transaction_counts']['numerator'] == 1
    assert stats['cross_entity_to_self_loop_transaction_counts']['denominator'] == 2
    assert stats['merged_ct_component_group_count'] == 1
    assert stats['merged_ct_components_per_group_quantiles'] == {'p50':2, 'p90':2}
    assert stats['amount_weighted_endpoint_rewrite_fraction'] == .2
    assert stats['amount_weight_definition'] == 'output_sat'

def test_cell_merge_membership_and_streaming_file_hash(tmp_path, monkeypatch):
    monkeypatch.setattr(ev, '_bootstrap', lambda *args: {'checked': True})
    monkeypatch.setattr(ev, '_graph', lambda *args: {'checked': True})
    support={b('1'),b('2'),b('3')}; first_height={script:1 for script in support}
    rt={script:script for script in support}; future={b('1'):b('1'),b('2'):b('1'),b('3'):b('3')}
    records=[(1,b('a'),0,b('b'),(b('1'),),(b('2'),),False,1,1,0)]
    window={'window_id':'t1','cutoff_height':1,'win_start_height':1,'win_end_height':1}
    cell=ev._cell(window,'F_pub',1,support,first_height,records,rt,future,'m'*64,'s'*64)
    assert cell['point'] == {'p_merge':2/3,'p_rewrite':1.0}
    path=tmp_path/'bytes.bin'; path.write_bytes(b'x'*(9*1024*1024)+b'y')
    expected=hashlib.sha256(path.read_bytes()).hexdigest()
    monkeypatch.setattr(Path, 'read_bytes', lambda self: (_ for _ in ()).throw(AssertionError('not streaming')))
    assert ev._sha(path) == expected

def test_graph_and_record_hash_streaming_match_exact_jsonl_bytes():
    meta={"analysis_cutoff_height":1,"extractor_summary_sha256":"a"*64,"filter_profile":"F_pub","horizon_blocks":52560,"partition_cutoff_height":1,"partition_vintage":"B","record_type":"meta","schema_version":"asof-entity-endpoint-multigraph-v1","source_manifest_sha256":"b"*64,"window_id":"t1"}
    records=[(1,b('c'),0,b('d'),(b('1'),b('2')),(b('3'),),False,2,3,0), (1,b('c'),1,b('e'),(b('3'),),(b('1'),),False,3,2,1)]
    reps={b(x):b(x) for x in '123'}
    graph=ev._graph(records,reps,meta)
    lines=[meta, *({'record_type':'node','script_id':x*64} for x in '123'),
           {'block_hash':'c'*64,'block_height':1,'fee_sat':0,'input_entities':['1'*64,'2'*64],'input_sat':2,'output_entities':['3'*64],'output_sat':3,'record_type':'transaction','tx_index':0,'txid':'d'*64},
           {'block_hash':'c'*64,'block_height':1,'fee_sat':1,'input_entities':['3'*64],'input_sat':3,'output_entities':['1'*64],'output_sat':2,'record_type':'transaction','tx_index':1,'txid':'e'*64},
           *({'block_height':1,'record_type':'edge','source':source*64,'target':'3'*64,'tx_index':0,'txid':'d'*64} for source in '12'),
           {'block_height':1,'record_type':'edge','source':'3'*64,'target':'1'*64,'tx_index':1,'txid':'e'*64}]
    raw=('\n'.join(ev._json(line) for line in lines)+'\n').encode()
    assert graph == {'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw),'record_counts':{'meta':1,'node':3,'transaction':2,'edge':3}}
    assert ev._hash_records(({'n':n} for n in range(3))) == hashlib.sha256(b'{"n":0}\n{"n":1}\n{"n":2}\n').hexdigest()

def test_partition_cell_generator_streams_boundaries_and_releases_ct_maps():
    con = sqlite3.connect(':memory:')
    con.execute('create table union_events(event_id,block_hash,height,txid,tx_index,event_index,script_id_a,script_id_b,exclude_f_pub,exclude_f_wide,evidence_json)')
    con.execute('insert into union_events values(?,?,?,?,?,?,?,?,?,?,?)', (b('e'),b('c'),2,b('d'),0,0,b('a'),b('b'),0,0,'{}'))
    windows = [{'window_id':'t1','cutoff_height':1}, {'window_id':'t3','cutoff_height':3}]
    instrument = {}
    yielded = list(ev.iter_partition_cells(con, windows, {'t1':{b('a'),b('b')},'t3':{b('a'),b('b')}}, (1, 2), instrument))
    assert [item[:3] for item in yielded] == [(p,w,h) for p in ev.PROFILES for w,h in [('t1',1),('t1',2),('t3',1),('t3',2)]]
    assert instrument['max_live_ct_maps'] <= 2
    assert instrument['dsu_cursors'] == len(ev.PROFILES)
    assert instrument['dsu_profiles'] == list(ev.PROFILES)

def test_raw_union_hash_matches_legacy_view_and_bytes_partition():
    con = sqlite3.connect(':memory:')
    extract_s0.create_s0_schema(con)
    con.execute('insert into run_context values(1,?,?,?,?,?,?,?,?)',
                (1, 'common-input', 'v1', 's0-profile-view-v1', 'm'*64, 'r'*64, 2, '{}'))
    # The first two rows deliberately tie on every protocol order field except
    # event_id, exercising the legacy hash's final deterministic tie-breaker.
    rows=[(b('e'),b('c'),1,b('d'),0,0,b('a'),b('b'),0,1,'{}'),
          (b('f'),b('c'),1,b('d'),0,0,b('a'),b('b'),1,0,'{}'),
          (b('9'),b('c'),2,b('d'),1,0,b('b'),b('c'),1,1,'{}')]
    con.executemany('insert into union_events values(?,?,?,?,?,?,?,?,?,?,?)', rows)
    digest=hashlib.sha256()
    query = '''select event_id,block_hash,block_height,txid,tx_index,event_index,
               script_id_a,script_id_b,filter_profile,filter_decision,exclude_f_pub,
               exclude_f_wide,evidence_json,heuristic_id,heuristic_version,
               source_manifest_sha256,profile_view_version from union_event_records
               order by filter_profile,block_height,tx_index,event_index,script_id_a,script_id_b,event_id'''
    for event_id,bh,height,txid,idx,event_idx,left,right,profile,decision,pub,wide,evidence,heuristic,version,manifest,view in con.execute(query):
        digest.update(ev._json({'event_id':event_id,'block_hash':bh.hex(),'block_height':height,'txid':txid.hex(),'tx_index':idx,'event_index':event_idx,'script_id_a':left.hex(),'script_id_b':right.hex(),'filter_profile':profile,'filter_decision':decision,'exclude_f_pub':pub,'exclude_f_wide':wide,'evidence_json':evidence,'heuristic_id':heuristic,'heuristic_version':version,'source_manifest_sha256':manifest,'profile_view_version':view}).encode()+b'\n')
    statements=[]; con.set_trace_callback(statements.append)
    assert ev._union_hash(con) == digest.hexdigest()
    assert ev.UNION_HASH_PROFILES == tuple(sorted(ev.PROFILES))
    assert sum(' from union_events ' in statement.lower() for statement in statements) == len(ev.PROFILES)
    assert not any('union_event_records' in statement.lower() for statement in statements)
    byte_reps=ev._representatives([(1,0,0,b('a'),b('b')),(2,0,0,b('b'),b('c'))], 2, {b('a'),b('b'),b('c')})
    hex_reps=ev._representatives([(1,0,0,'a'*64,'b'*64),(2,0,0,'b'*64,'c'*64)], 2, {'a'*64,'b'*64,'c'*64})
    assert {key.hex(): value.hex() for key,value in byte_reps.items()} == hex_reps
    dsu=ev.DSU(); dsu.union(b('a'), b('b'))
    ev._restricted_representatives(dsu, {b('a'), b('b'), b('c')})
    assert b('c') not in dsu.p

def test_bootstrap_truncates_final_circular_block(monkeypatch):
    class FixedRandom:
        def __init__(self, seed): pass
        def randrange(self, width): return 0
    monkeypatch.setattr(ev.random, 'Random', FixedRandom)
    result = ev._bootstrap([[1, 1, 1, 1], [1, 1, 1, 1], [1, 3, 1, 3], [1, 1, 1, 1], [1, 1, 1, 1]], 'b'*64, 't1', 1, 'F_pub', 3)
    assert result['p_merge']['sorted_replicates'] == [5 / 7] * ev.REPLICATES
    assert result['p_rewrite']['sorted_replicates'] == [5 / 7] * ev.REPLICATES

def test_bootstrap_prefix_sums_match_naive_wrap_and_truncation(monkeypatch):
    class FixedRandom:
        def __init__(self, seed): self.i = 0
        def randrange(self, width):
            value = (width - 1, 1, 0, width - 2)[self.i % 4]; self.i += 1
            return value
    monkeypatch.setattr(ev.random, 'Random', FixedRandom)
    def naive(blocks, length, replicates):
        width = len(blocks); rng = ev.random.Random(ev._seed('b'*64, 't1', 1, 'F_pub', length))
        samples = [[], []]; digest = hashlib.sha256()
        for _ in range(replicates):
            starts = [rng.randrange(width) for _ in range(-(-width // length))]
            digest.update(ev._json(starts).encode() + b'\n')
            totals = [0, 0, 0, 0]; taken = 0
            for start in starts:
                for offset in range(min(length, width - taken)):
                    for column, value in enumerate(blocks[(start + offset) % width]): totals[column] += value
                taken += length
            samples[0].append(totals[0] / totals[1]); samples[1].append(totals[2] / totals[3])
        return samples, digest.hexdigest()
    for blocks, length in (([[1,2,3,4],[2,3,4,5],[3,4,5,6],[4,5,6,7],[5,6,7,8]], 3),
                           ([[1,3,2,4],[2,4,3,5],[3,5,4,6],[4,6,5,7]], 2)):
        expected_samples, expected_hash = naive(blocks, length, 7)
        actual_samples, actual_hash = ev._bootstrap_samples(blocks, 'b'*64, 't1', 1, 'F_pub', length, replicates=7)
        assert actual_samples == expected_samples
        assert actual_hash.hexdigest() == expected_hash

def test_validate_rejects_tamper_and_pending_is_not_final(tmp_path):
    db=tmp_path/'x.sqlite'; c=sqlite3.connect(db); c.execute('create table run_context(context_id integer primary key,source_manifest_sha256,runner_sha256,target_height,design_json)'); c.execute('create table union_events(x)'); c.execute('create table window_transactions(x)'); c.execute('create table window_support(x)'); design={'primary_horizon_blocks':52560}; c.execute('insert into run_context values(1,?,?,?,?)',('a'*64,'b'*64,1,json.dumps(design))); c.commit(); c.close()
    s={'status':'s0_union_extraction_complete','s0_extraction_complete':True,'labels_read':False,'effect_metrics_read':False,'models_authorized':False,'source_manifest_sha256':'a'*64,'runner_sha256':'b'*64,'last_complete_height':1,'design':design,'s0_counters':{'union_events':0,'window_transactions':0,'window_support':0},'windows':[]}
    p=tmp_path/'s.json';p.write_text(json.dumps(s)); s['runner_sha256']='x';
    with pytest.raises(ValueError): ev.validate(s,db)
    assert {'status':'pending_external_provenance_audit'}['status']!='passed'
