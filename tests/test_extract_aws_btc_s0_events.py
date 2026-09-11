"""Synthetic contract tests for the Gate 3A S0 union-event extraction layer.

Fully synthetic: in-memory SQLite state and hand-made ``compact_row``-shaped rows.
No 53 GB cache, no network, no labels, no model outputs, no effect metrics.
Run with ``python -m pytest -p no:cacheprovider``.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts" / "research"))
sys.path.insert(0, str(REPO_ROOT / "src"))

import audit_aws_btc_transaction_semantics as semantics  # noqa: E402
import extract_aws_btc_s0_events as s0  # noqa: E402

SOURCE_MANIFEST_SHA = (
    "e32ad2f33ecbc184eb04159f0adbb22dd2a4a1a47f1e280cbbca699432d67f3d"
)
OP_RETURN_SCRIPT = b"\x6a\x04test"
P2PKH = b"\x76\xa9\x14" + b"\x11" * 20 + b"\x88\xac"
P2SH = b"\xa9\x14" + b"\x22" * 20 + b"\x87"
P2WPKH = b"\x00\x14" + b"\x33" * 20
BLOCK_HASH = hashlib.sha256(b"s0-test-block").digest()


def _script_id(raw):
    return bytes.fromhex(s0.frozen_script_id(raw))


def _txid(tag):
    return hashlib.sha256(tag.encode()).digest()


def _row(tag, height, position, *, coinbase, inputs, outputs):
    """Build a ``compact_row``-shaped row without touching Parquet."""
    output_value = sum(value for value, _ in outputs)
    input_value = None if coinbase else sum(item["value_sat"] for item in inputs)
    return {
        "height": height,
        "position": position,
        "txid": _txid(tag),
        "witness_hash": _txid(tag),
        "block_hash": BLOCK_HASH,
        "input_count": len(inputs),
        "output_count": len(outputs),
        "is_coinbase": coinbase,
        "input_value": input_value,
        "output_value": output_value,
        "fee": None if coinbase else input_value - output_value,
        "inputs": inputs,
        "outputs": [
            {"index": index, "value_sat": value, "script": script}
            for index, (value, script) in enumerate(outputs)
        ],
        "max_amount_residual_sats": 0.0,
        "source": f"test:{tag}:{height}:{position}",
    }


def _spend(row, vout=0, index=0):
    return {
        "index": index,
        "parent_txid": row["txid"],
        "parent_vout": vout,
        "value_sat": row["outputs"][vout]["value_sat"],
    }


def _block(rows):
    return {
        "transaction_count": len(rows),
        "hash": BLOCK_HASH.hex(),
        "partition_date": "2026-01-01",
    }


def _fresh_state():
    connection = sqlite3.connect(":memory:")
    semantics.create_state_schema(connection)
    s0.create_s0_schema(connection)
    return connection, semantics.default_counters(), s0.s0_default_counters()


def _seed_context(connection, target_height=10):
    connection.execute(
        "INSERT INTO run_context("
        "context_id, s0_schema_version, heuristic_id, heuristic_version, "
        "profile_view_version, source_manifest_sha256, runner_sha256, "
        "target_height, design_json) VALUES (1, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            s0.S0_SCHEMA_VERSION,
            s0.HEURISTIC_ID,
            s0.HEURISTIC_VERSION,
            s0.PROFILE_VIEW_VERSION,
            SOURCE_MANIFEST_SHA,
            "0" * 64,
            target_height,
            "{}",
        ),
    )
    connection.commit()


def _window(win_start=0, win_end=9, horizon=5):
    """One synthetic evaluation window.

    ``windows`` is a list keyed by ``window_id``; several horizons can share the
    same block bounds, so the bounds alone are not a unique key.
    """
    return [
        {
            "window_id": f"t{win_end}-h{horizon}",
            "cutoff_height": win_end,
            "horizon_blocks": horizon,
            "window_blocks": win_end - win_start + 1,
            "win_start_height": win_start,
            "win_end_height": win_end,
            "future_end_height": win_end + horizon,
        }
    ]


def _commit_block(connection, counters, s0_counters, height, rows):
    """Commit one full block through the single production entry point."""
    profile_stats = {}
    s0.process_block_s0(
        connection,
        height,
        list(rows),
        _block(rows),
        counters,
        s0_counters,
        _window(),
        SOURCE_MANIFEST_SHA,
        profile_stats,
    )
    s0.flush_block_profile_stats(connection, profile_stats, s0_counters)


def _chain_fixture():
    """Three valid blocks ending in one two-input merge."""
    coinbase = _row(
        "coinbase-0",
        0,
        0,
        coinbase=True,
        inputs=[],
        outputs=[
            (5_000_000_000, P2PKH),
            (4_000_000_000, P2SH),
            (1, OP_RETURN_SCRIPT),
        ],
    )
    coinbase_1 = _row(
        "coinbase-1", 1, 0, coinbase=True, inputs=[], outputs=[(5_000_000_000, P2PKH)]
    )
    spend = _row(
        "spend",
        1,
        1,
        coinbase=False,
        inputs=[_spend(coinbase, 0)],
        outputs=[(3_000_000_000, P2WPKH)],
    )
    coinbase_2 = _row(
        "coinbase-2", 2, 0, coinbase=True, inputs=[], outputs=[(5_000_000_000, P2PKH)]
    )
    merge = _row(
        "merge",
        2,
        1,
        coinbase=False,
        inputs=[_spend(coinbase, 1, index=0), _spend(spend, 0, index=1)],
        outputs=[(1_000_000_000, P2PKH)],
    )
    return {
        "coinbase": coinbase,
        "spend": spend,
        "merge": merge,
        "blocks": [[coinbase], [coinbase_1, spend], [coinbase_2, merge]],
    }


def _run_chain():
    connection, counters, s0_counters = _fresh_state()
    _seed_context(connection)
    chain = _chain_fixture()
    for height, rows in enumerate(chain["blocks"]):
        _commit_block(connection, counters, s0_counters, height, rows)
    return connection, counters, s0_counters, chain


# --------------------------------------------------------------------------- #
# Frozen design, horizon cells and target height
# --------------------------------------------------------------------------- #


def test_design_is_manifest_bound_and_unavailable_cells_are_recorded():
    payload, manifest = s0.validate_source_manifest(REPO_ROOT / s0.DEFAULT_SOURCE_MANIFEST)
    assert hashlib.sha256(payload).hexdigest() == SOURCE_MANIFEST_SHA
    design = s0.s0_design(manifest)
    allowed = set(manifest["execution_boundary"]["allowed_columns"])
    assert s0.BASE_LOGICAL_FIELDS | s0.INPUT_LOGICAL_FIELDS <= allowed
    assert "inputs" not in s0.INPUT_PARQUET_COLUMNS
    assert "outputs" not in s0.BASE_PARQUET_COLUMNS
    assert all(".list.element." in name for name in s0.INPUT_PARQUET_COLUMNS[2:])
    assert all(".list.element." in name for name in s0.BASE_PARQUET_COLUMNS[-4:-1])
    assert design["cutoff_heights"] == [181440, 199584, 215712, 225792]
    assert design["window_blocks"] == 2016
    assert design["primary_horizon_blocks"] == 52560
    assert design["sensitivity_horizon_blocks"] == [13140, 105120]

    # An out-of-prefix long-horizon cell is recorded, not treated as a source failure.
    target = s0.compute_target_height(design, manifest["scope"])
    assert target == 286560
    cells = s0.horizon_cells(design, manifest["scope"]["last_height"])
    assert {
        (cell["cutoff_height"], cell["horizon_blocks"])
        for cell in cells
        if not cell["available"]
    } == {(199584, 105120), (215712, 105120), (225792, 105120)}
    assert all(
        cell["available"]
        for cell in cells
        if cell["horizon_blocks"] == design["primary_horizon_blocks"]
    )
    windows = s0.build_windows(design)
    assert [window["cutoff_height"] for window in windows] == design["cutoff_heights"]
    assert len(windows) == 4


def test_unavailable_primary_cell_is_refused():
    design = {
        "cutoff_heights": [10],
        "window_blocks": 2,
        "primary_horizon_blocks": 100,
        "sensitivity_horizon_blocks": [5],
    }
    with pytest.raises(ValueError, match="primary horizon cells"):
        s0.compute_target_height(design, {"last_height": 50})


def test_manifest_tamper_and_boundary_are_enforced(tmp_path):
    source = REPO_ROOT / s0.DEFAULT_SOURCE_MANIFEST
    tampered = tmp_path / "manifest.json"
    tampered.write_bytes(source.read_bytes() + b"\n")
    with pytest.raises(RuntimeError, match="SHA-256 mismatch"):
        s0.validate_source_manifest(tampered)

    manifest = json.loads(source.read_text(encoding="utf-8"))
    manifest["execution_boundary"]["models_authorized"] = True
    payload = json.dumps(manifest, sort_keys=True).encode("utf-8")
    flipped = tmp_path / "flipped.json"
    flipped.write_bytes(payload)
    original = s0.EXPECTED_SOURCE_MANIFEST_SHA256
    s0.EXPECTED_SOURCE_MANIFEST_SHA256 = hashlib.sha256(payload).hexdigest()
    try:
        with pytest.raises(ValueError, match="models_authorized"):
            s0.validate_source_manifest(flipped)
    finally:
        s0.EXPECTED_SOURCE_MANIFEST_SHA256 = original


# --------------------------------------------------------------------------- #
# Union events and frozen filter profiles
# --------------------------------------------------------------------------- #


def test_common_input_star_is_canonical_and_needs_two_scripts():
    a, b, c = b"a" * 32, b"b" * 32, b"c" * 32
    assert s0.common_input_star([c, a, b, b]) == [(a, b, [2, 3]), (a, c, [0])]
    assert s0.common_input_star([a, a, a]) == []
    assert s0.common_input_star([a]) == []


def test_event_id_is_deterministic_and_field_sensitive():
    anchor, member = b"a" * 32, b"b" * 32
    base = dict(
        source_manifest_sha256=SOURCE_MANIFEST_SHA,
        block_hash=BLOCK_HASH,
        block_height=7,
        txid=b"t" * 32,
        tx_index=1,
        event_index=0,
        script_id_a=anchor,
        script_id_b=member,
        heuristic_version=s0.HEURISTIC_VERSION,
    )
    first = s0.compute_event_id(**base)
    assert len(first) == 32
    assert first == s0.compute_event_id(**base)
    assert first != s0.compute_event_id(**{**base, "event_index": 1})
    assert first != s0.compute_event_id(**{**base, "script_id_b": b"z" * 32})
    assert first != s0.compute_event_id(**{**base, "source_manifest_sha256": "0" * 64})
    # Script order is part of the identity, so a/b must not be swapped silently.
    assert first != s0.compute_event_id(
        **{**base, "script_id_a": member, "script_id_b": anchor}
    )


def test_encode_script_ids_packs_ids_without_rehashing():
    a, b = _script_id(P2PKH), _script_id(P2WPKH)
    packed = s0.encode_script_ids([a, b, a])
    assert packed == b"".join(sorted({a, b}))
    assert len(packed) == 64
    assert s0.decode_script_ids(packed) == sorted({a, b})
    # A raw locking script must never be accepted here: that would re-hash it.
    with pytest.raises(RuntimeError, match="32-byte script-id blobs"):
        s0.encode_script_ids([P2PKH])


def test_one_union_uses_parent_locking_scripts_and_single_input_yields_none():
    connection, _, s0_counters, chain = _run_chain()
    events = connection.execute(
        "SELECT height, tx_index, event_index, script_id_a, script_id_b FROM union_events"
    ).fetchall()
    # ``merge`` is the only two-distinct-input transaction; ``spend`` has one input.
    anchor, member = sorted([_script_id(P2SH), _script_id(P2WPKH)])
    assert events == [(2, 1, 0, anchor, member)]
    assert chain["spend"]["txid"] is not None
    # The merge's own output locking script must not leak in as an endpoint.
    assert _script_id(P2PKH) not in set(events[0][3:])
    input_ids = [_script_id(P2SH), _script_id(P2WPKH)]
    facts = s0.transaction_profile_facts(chain["merge"], input_ids)
    s0._record_union_events(
        connection, chain["merge"], input_ids, facts, s0_counters, SOURCE_MANIFEST_SHA
    )
    assert s0_counters["duplicate_union_events"] == 1
    assert connection.execute("SELECT COUNT(*) FROM union_events").fetchone() == (1,)
    connection.close()


def test_three_profile_view_expands_each_event():
    connection, _, _, _ = _run_chain()
    view = connection.execute(
        "SELECT filter_profile, filter_decision, heuristic_id, source_manifest_sha256 "
        "FROM union_event_records ORDER BY filter_profile"
    ).fetchall()
    assert [row[0] for row in view] == ["F_none", "F_pub", "F_wide"]
    for row in view:
        assert row[2] == s0.HEURISTIC_ID
        assert row[3] == SOURCE_MANIFEST_SHA
    assert dict((row[0], row[1]) for row in view)["F_none"] == "include"
    connection.close()


def test_joinmarket_shape_is_excluded_by_both_public_profiles():
    """A JoinMarket-shaped transaction must be excluded by F_pub and F_wide.

    Frozen ``is_coinjoin_joinmarket``: the most-represented output value appears at
    least 3 times, at least half the outputs share it, that count does not exceed
    the number of distinct input script IDs, and all output scripts are distinct.
    """
    connection, counters, s0_counters = _fresh_state()
    _seed_context(connection)
    coinbase = _row(
        "cb",
        0,
        0,
        coinbase=True,
        inputs=[],
        outputs=[(10_000_000_000, P2PKH), (10_000_000_000, P2SH), (10_000_000_000, P2WPKH)],
    )
    _commit_block(connection, counters, s0_counters, 0, [coinbase])
    next_coinbase = _row(
        "cb-next", 1, 0, coinbase=True, inputs=[], outputs=[(5_000_000_000, P2PKH)]
    )
    mixer = _row(
        "mixer",
        1,
        1,
        coinbase=False,
        inputs=[
            {
                "index": index,
                "parent_txid": coinbase["txid"],
                "parent_vout": index,
                "value_sat": 10_000_000_000,
            }
            for index in range(3)
        ],
        outputs=[
            (9_999_000_000, P2PKH),
            (9_999_000_000, P2SH),
            (9_999_000_000, P2WPKH),
        ],
    )
    _commit_block(connection, counters, s0_counters, 1, [next_coinbase, mixer])

    row = connection.execute(
        "SELECT exclude_f_pub, exclude_f_wide, evidence_json FROM union_events"
    ).fetchone()
    assert (row[0], row[1]) == (1, 1)
    assert "joinmarket" in json.loads(row[2])["f_pub_matches"]
    decisions = dict(
        connection.execute(
            "SELECT filter_profile, filter_decision FROM union_event_records"
        ).fetchall()
    )
    assert (decisions["F_pub"], decisions["F_wide"]) == ("exclude", "exclude")
    assert decisions["F_none"] == "include"
    assert s0_counters["suppressed_union_events_f_pub"] == 2
    assert s0_counters["suppressed_union_events_f_wide"] == 2
    connection.close()


# --------------------------------------------------------------------------- #
# Window records and creation-time V_j support
# --------------------------------------------------------------------------- #


def test_window_transaction_keeps_inputs_and_drops_unspendable_outputs():
    connection, _, _, chain = _run_chain()
    coinbase = connection.execute(
        "SELECT input_script_ids, output_script_ids, input_sat, output_sat, fee_sat "
        "FROM window_transactions WHERE height = 0"
    ).fetchone()
    assert coinbase[0] == b""
    # OP_RETURN is excluded from window output endpoints.
    assert s0.decode_script_ids(coinbase[1]) == sorted([_script_id(P2PKH), _script_id(P2SH)])
    assert (coinbase[2], coinbase[4]) == (None, None)
    assert coinbase[3] == 9_000_000_001

    merge = connection.execute(
        "SELECT input_script_ids, input_sat, fee_sat FROM window_transactions "
        "WHERE txid = ?",
        (chain["merge"]["txid"],),
    ).fetchone()
    assert s0.decode_script_ids(merge[0]) == sorted(
        [_script_id(P2SH), _script_id(P2WPKH)]
    )
    assert merge[1] == 7_000_000_000
    assert merge[2] == 6_000_000_000
    connection.close()


def test_support_excludes_op_return_but_features_keep_it():
    connection, _, _, chain = _run_chain()
    support = {
        row[0] for row in connection.execute("SELECT script_id FROM window_support")
    }
    assert _script_id(P2PKH) in support
    # OP_RETURN never enters V_j support...
    assert _script_id(OP_RETURN_SCRIPT) not in support
    # ...but it stays in the filter features: the exclusion applies only to V_j.
    features = s0.transaction_features(chain["coinbase"], [])
    assert _script_id(OP_RETURN_SCRIPT).hex() in features.output_script_ids
    connection.close()


def test_support_records_creation_time_first_height():
    connection, _, _, _ = _run_chain()
    assert connection.execute(
        "SELECT first_height FROM window_support WHERE script_id = ?",
        (_script_id(P2PKH),),
    ).fetchone() == (0,)
    # P2WPKH is created by the height-1 spend, not by the later merge.
    assert connection.execute(
        "SELECT first_height FROM window_support WHERE script_id = ?",
        (_script_id(P2WPKH),),
    ).fetchone() == (1,)
    connection.close()


# --------------------------------------------------------------------------- #
# Checkpoint integrity and resumability
# --------------------------------------------------------------------------- #


def test_checkpoint_roundtrip_and_tamper_detection():
    connection, counters, s0_counters, _ = _run_chain()
    s0.flush_block_profile_stats(connection, {}, s0_counters)
    s0.checkpoint_s0(connection, 2, counters, s0_counters)
    s0.validate_s0_checkpoint(connection, 2, counters, s0_counters)

    for key, message in (
        ("window_transactions", "window_transactions count"),
        ("union_events", "union_events count"),
        ("block_profile_stat_rows", "block_profile_stats count"),
    ):
        bad = dict(s0_counters)
        bad[key] += 1
        with pytest.raises(RuntimeError, match=message):
            s0.validate_s0_checkpoint(connection, 2, counters, bad)
    connection.close()


def test_resume_rejects_changed_bindings_and_run_context(tmp_path):
    state_db = tmp_path / "state.sqlite"
    bindings = {"listing_sha256": "a" * 64, "candidate_hmax": 10}
    s0_bindings = {
        "source_manifest_sha256": SOURCE_MANIFEST_SHA,
        "runner_sha256": s0.script_sha256(),
        "reference_code": {},
        "target_height": 10,
        "design": {},
    }
    connection, _, _, _ = s0.open_s0_state(
        state_db, bindings, "2026-01-01T00:00:00+00:00", s0_bindings
    )
    connection.close()

    # Same bindings resume cleanly.
    connection, committed, _, _ = s0.open_s0_state(
        state_db, bindings, "2026-01-01T00:00:00+00:00", s0_bindings
    )
    assert committed == -1
    connection.close()

    def _mutate_stored_blob(**changes):
        store = sqlite3.connect(state_db)
        stored = json.loads(semantics.metadata_get(store, "s0_bindings"))
        stored.update(changes)
        semantics.metadata_set(store, "s0_bindings", stored)
        store.commit()
        store.close()

    # The stored blob itself no longer matches this run's bindings.
    _mutate_stored_blob(runner_sha256="f" * 64)
    with pytest.raises(RuntimeError, match="bindings differ"):
        s0.open_s0_state(state_db, bindings, "2026-01-01T00:00:00+00:00", s0_bindings)

    # Independent guard: a desynchronised run_context row is refused even when the
    # stored blob is consistent again.
    _mutate_stored_blob(runner_sha256=s0_bindings["runner_sha256"])
    store = sqlite3.connect(state_db)
    store.execute(
        "UPDATE run_context SET runner_sha256 = ? WHERE context_id = 1", ("f" * 64,)
    )
    store.commit()
    store.close()
    with pytest.raises(RuntimeError, match="runner content changed"):
        s0.open_s0_state(state_db, bindings, "2026-01-01T00:00:00+00:00", s0_bindings)


def test_runner_self_test_passes():
    s0.self_test()
