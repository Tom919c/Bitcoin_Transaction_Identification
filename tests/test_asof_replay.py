import pytest

from btcaml.data.asof_replay import (
    UnionEvent,
    WindowTransaction,
    canonical_union_hash,
    p_merge,
    p_rewrite,
    partition_hash,
    replay_partition,
    restricted_representatives,
)


def _event(event_id, height, tx_index, event_index, left, right):
    return UnionEvent(
        event_id=event_id,
        block_hash=f"block-{height}",
        block_height=height,
        txid=f"tx-{height}-{tx_index}",
        tx_index=tx_index,
        event_index=event_index,
        script_id_a=left,
        script_id_b=right,
        heuristic_id="common-input",
        heuristic_version="v1",
        filter_profile="F_none",
        filter_decision="include",
        evidence_json="{}",
        source_manifest_sha256="manifest",
    )


def test_event_order_does_not_change_hash_or_partition():
    events = [
        _event("two", 11, 0, 0, "b", "c"),
        _event("one", 10, 3, 0, "a", "b"),
    ]
    shuffled = list(reversed(events))

    assert canonical_union_hash(events) == canonical_union_hash(shuffled)
    assert replay_partition(events, 11) == replay_partition(shuffled, 11)
    assert partition_hash(replay_partition(events, 11)) == partition_hash(replay_partition(shuffled, 11))


def test_duplicate_event_id_is_rejected_even_when_records_match():
    event = _event("duplicate", 10, 0, 0, "a", "b")

    with pytest.raises(ValueError, match="duplicate event_id"):
        canonical_union_hash([event, event])


def test_same_block_position_cutoff_respects_canonical_event_order():
    first = _event("first", 20, 1, 0, "a", "b")
    second = _event("second", 20, 1, 1, "b", "c")

    at_first = replay_partition([second, first], (20, 1, 0))
    at_second = replay_partition([second, first], (20, 1, 1))

    assert at_first["a"] == at_first["b"]
    assert "c" not in at_first
    assert at_second["a"] == at_second["b"] == at_second["c"]


def test_future_only_connector_merges_history_but_never_becomes_representative():
    events = [
        _event("future-left", 11, 0, 0, "a", "0-future"),
        _event("future-right", 12, 0, 0, "b", "0-future"),
    ]
    support = {"a", "b"}
    as_of = restricted_representatives(replay_partition(events, 10), support)
    later = restricted_representatives(replay_partition(events, 12), support)

    assert as_of == {"a": "a", "b": "b"}
    assert later == {"a": "a", "b": "a"}
    assert set(later.values()) <= support
    assert replay_partition(events, 12)["a"] == "0-future"
    assert "0-future" not in later.values()


def test_paired_conditions_keep_support_and_compute_manual_rates():
    events = [
        _event("future-left", 11, 0, 0, "a", "z-future"),
        _event("future-right", 12, 0, 0, "b", "z-future"),
    ]
    support = {"a", "b", "c"}
    representatives_t = restricted_representatives(replay_partition(events, 10), support)
    representatives_T = restricted_representatives(replay_partition(events, 12), support)
    transactions = [
        WindowTransaction("rewrite", ("a",), ("b",)),
        WindowTransaction("unchanged", ("c",), ("c",)),
        WindowTransaction("coinbase", (), ("a",), is_coinbase=True),
    ]

    assert set(representatives_t) == set(representatives_T) == support
    assert p_merge(representatives_t, representatives_T) == pytest.approx(2 / 3)
    assert p_rewrite(transactions, representatives_t, representatives_T) == pytest.approx(1 / 2)


def test_events_later_than_cutoff_cannot_enter_as_of_partition():
    events = [
        _event("visible", 10, 0, 0, "a", "b"),
        _event("future", 11, 0, 0, "b", "c"),
    ]

    as_of = replay_partition(events, 10)

    assert as_of["a"] == as_of["b"]
    assert "c" not in as_of


def test_paired_rates_reject_mismatched_support():
    with pytest.raises(ValueError, match="supports must be identical"):
        p_merge({"a": "a"}, {"b": "b"})


def test_p_rewrite_rejects_duplicate_non_coinbase_txids():
    transactions = [
        WindowTransaction("duplicate", ("a",), ("b",)),
        WindowTransaction("duplicate", ("b",), ("a",)),
    ]

    with pytest.raises(ValueError, match="duplicate non-coinbase txid"):
        p_rewrite(transactions, {"a": "a", "b": "b"}, {"a": "a", "b": "a"})
