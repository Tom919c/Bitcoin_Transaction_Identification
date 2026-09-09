"""Deterministic reference primitives for as-of address-cluster replay.

This module intentionally consumes already-extracted union events and transaction
endpoints.  It does not parse blocks, classify collaborative transactions, or
access labels.  Future-only scripts may connect historical scripts in a later
partition, but restricted representatives are always selected from the supplied
historical support.
"""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from hashlib import sha256
from types import MappingProxyType
from typing import TypeAlias

EventPosition: TypeAlias = tuple[int, int, int]
Cutoff: TypeAlias = int | EventPosition


def _required_text(name: str, value: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{name} must be a non-empty string")
    return value


@dataclass(frozen=True)
class UnionEvent:
    """One provenance-complete address union, ordered on main-chain position."""

    event_id: str
    block_hash: str
    block_height: int
    txid: str
    tx_index: int
    event_index: int
    script_id_a: str
    script_id_b: str
    heuristic_id: str
    heuristic_version: str
    filter_profile: str
    filter_decision: str
    evidence_json: str
    source_manifest_sha256: str

    def __post_init__(self) -> None:
        for name in (
            "event_id",
            "block_hash",
            "txid",
            "script_id_a",
            "script_id_b",
            "heuristic_id",
            "heuristic_version",
            "filter_profile",
            "filter_decision",
            "evidence_json",
            "source_manifest_sha256",
        ):
            _required_text(name, getattr(self, name))
        for name in ("block_height", "tx_index", "event_index"):
            value = getattr(self, name)
            if not isinstance(value, int) or value < 0:
                raise ValueError(f"{name} must be a non-negative integer")
        if self.script_id_a == self.script_id_b:
            raise ValueError("union event requires two different script IDs")
        if self.script_id_b < self.script_id_a:
            left, right = self.script_id_b, self.script_id_a
            object.__setattr__(self, "script_id_a", left)
            object.__setattr__(self, "script_id_b", right)

    @property
    def position(self) -> EventPosition:
        """Position used by a same-block, as-of cutoff."""
        return (self.block_height, self.tx_index, self.event_index)

    @property
    def sort_key(self) -> tuple[int, int, int, str, str]:
        """Canonical replay ordering key required by the protocol."""
        return (*self.position, self.script_id_a, self.script_id_b)

    def canonical_record(self) -> dict[str, object]:
        """Stable, provenance-complete serialization payload."""
        return {
            "event_id": self.event_id,
            "block_hash": self.block_hash,
            "block_height": self.block_height,
            "txid": self.txid,
            "tx_index": self.tx_index,
            "event_index": self.event_index,
            "script_id_a": self.script_id_a,
            "script_id_b": self.script_id_b,
            "heuristic_id": self.heuristic_id,
            "heuristic_version": self.heuristic_version,
            "filter_profile": self.filter_profile,
            "filter_decision": self.filter_decision,
            "evidence_json": self.evidence_json,
            "source_manifest_sha256": self.source_manifest_sha256,
        }


@dataclass(frozen=True)
class WindowTransaction:
    """Pre-filtered historical transaction endpoints for ``p_rewrite``."""

    txid: str
    input_script_ids: tuple[str, ...]
    output_script_ids: tuple[str, ...]
    is_coinbase: bool = False

    def __post_init__(self) -> None:
        _required_text("txid", self.txid)
        for name in ("input_script_ids", "output_script_ids"):
            values = getattr(self, name)
            if not isinstance(values, tuple):
                raise TypeError(f"{name} must be a tuple")
            for script_id in values:
                _required_text(name, script_id)


class _DeterministicDisjointSet:
    def __init__(self) -> None:
        self._parent: dict[str, str] = {}

    def find(self, item: str) -> str:
        parent = self._parent.setdefault(item, item)
        while parent != self._parent[parent]:
            parent = self._parent[parent]
        root = parent
        parent = self._parent[item]
        while parent != root:
            next_parent = self._parent[parent]
            self._parent[parent] = root
            parent = next_parent
        self._parent[item] = root
        return root

    def union(self, left: str, right: str) -> None:
        left_root = self.find(left)
        right_root = self.find(right)
        if left_root != right_root:
            self._parent[max(left_root, right_root)] = min(left_root, right_root)

    def frozen_partition(self) -> Mapping[str, str]:
        return MappingProxyType({item: self.find(item) for item in sorted(self._parent)})


def _canonical_events(events: Iterable[UnionEvent]) -> tuple[UnionEvent, ...]:
    """Sort pre-deduplicated events and reject every duplicate event identifier.

    Duplicate counting and source-level normalization belong to the extraction
    layer.  This reference layer requires one auditable event per ``event_id``.
    """
    by_event_id: dict[str, UnionEvent] = {}
    for event in events:
        if not isinstance(event, UnionEvent):
            raise TypeError("events must contain UnionEvent instances")
        if event.event_id in by_event_id:
            raise ValueError(f"duplicate event_id {event.event_id!r}; pre-deduplicate upstream")
        by_event_id[event.event_id] = event
    return tuple(sorted(by_event_id.values(), key=lambda event: (event.sort_key, event.event_id)))


def canonical_union_hash(events: Iterable[UnionEvent]) -> str:
    """SHA-256 of order-independent, provenance-complete union events."""
    payload = [event.canonical_record() for event in _canonical_events(events)]
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
    return sha256(encoded).hexdigest()


def _includes(event: UnionEvent, cutoff: Cutoff) -> bool:
    if isinstance(cutoff, int):
        return event.block_height <= cutoff
    if len(cutoff) != 3 or any(not isinstance(part, int) or part < 0 for part in cutoff):
        raise ValueError("tuple cutoff must be (block_height, tx_index, event_index)")
    return event.position <= cutoff


def replay_partition(events: Iterable[UnionEvent], cutoff: Cutoff) -> Mapping[str, str]:
    """Replay only unions visible at ``cutoff`` with deterministic DSU roots."""
    dsu = _DeterministicDisjointSet()
    for event in _canonical_events(events):
        if _includes(event, cutoff):
            dsu.union(event.script_id_a, event.script_id_b)
    return dsu.frozen_partition()


def partition_hash(partition: Mapping[str, str], support: Iterable[str] | None = None) -> str:
    """Stable hash for a full partition or its requested support restriction."""
    hash_support = partition if support is None else support
    items = sorted((script_id, partition.get(script_id, script_id)) for script_id in hash_support)
    encoded = json.dumps(items, separators=(",", ":"), ensure_ascii=True).encode()
    return sha256(encoded).hexdigest()


def restricted_representatives(
    partition: Mapping[str, str], support: Iterable[str]
) -> Mapping[str, str]:
    """Map each support script to its minimum same-component support script.

    ``partition`` may include future-only connector scripts.  They affect a
    component key, never the selected representative.
    """
    support_ids = tuple(sorted(set(support)))
    if not support_ids:
        raise ValueError("support must not be empty")
    if any(not isinstance(script_id, str) or not script_id for script_id in support_ids):
        raise ValueError("support must contain non-empty script IDs")
    members: dict[str, list[str]] = {}
    for script_id in support_ids:
        members.setdefault(partition.get(script_id, script_id), []).append(script_id)
    representatives = {
        script_id: min(members[partition.get(script_id, script_id)]) for script_id in support_ids
    }
    return MappingProxyType(representatives)


def _validate_paired_representatives(
    representatives_t: Mapping[str, str], representatives_T: Mapping[str, str]
) -> tuple[str, ...]:
    support_t = set(representatives_t)
    support_T = set(representatives_T)
    if not support_t:
        raise ValueError("support must not be empty")
    if support_t != support_T:
        raise ValueError("B/C supports must be identical")
    for mapping in (representatives_t, representatives_T):
        for script_id, representative in mapping.items():
            if representative not in support_t:
                raise ValueError("restricted representative must belong to support")
            if not isinstance(script_id, str) or not isinstance(representative, str):
                raise TypeError("script IDs and representatives must be strings")
    return tuple(sorted(support_t))


def p_merge(representatives_t: Mapping[str, str], representatives_T: Mapping[str, str]) -> float:
    """Fraction of support scripts whose later component joins >=2 as-of components."""
    support = _validate_paired_representatives(representatives_t, representatives_T)
    as_of_components_per_later: dict[str, set[str]] = {}
    for script_id in support:
        as_of_components_per_later.setdefault(representatives_T[script_id], set()).add(
            representatives_t[script_id]
        )
    affected = sum(
        len(as_of_components_per_later[representatives_T[script_id]]) >= 2 for script_id in support
    )
    return affected / len(support)


def _entity_endpoints(
    script_ids: tuple[str, ...], representatives: Mapping[str, str], txid: str
) -> tuple[str, ...]:
    missing = sorted(set(script_ids) - set(representatives))
    if missing:
        raise ValueError(f"transaction {txid!r} has scripts outside shared support: {missing}")
    return tuple(sorted({representatives[script_id] for script_id in script_ids}))


def p_rewrite(
    transactions: Iterable[WindowTransaction],
    representatives_t: Mapping[str, str],
    representatives_T: Mapping[str, str],
) -> float:
    """Fraction of non-coinbase transactions with changed entity endpoint lists."""
    _validate_paired_representatives(representatives_t, representatives_T)
    eligible: list[WindowTransaction] = []
    seen_txids: set[str] = set()
    for transaction in transactions:
        if not isinstance(transaction, WindowTransaction):
            raise TypeError("transactions must contain WindowTransaction instances")
        if transaction.is_coinbase:
            continue
        if transaction.txid in seen_txids:
            raise ValueError(f"duplicate non-coinbase txid {transaction.txid!r}")
        seen_txids.add(transaction.txid)
        eligible.append(transaction)
    if not eligible:
        raise ValueError("at least one non-coinbase transaction is required")
    rewritten = 0
    for transaction in eligible:
        endpoints_t = (
            _entity_endpoints(transaction.input_script_ids, representatives_t, transaction.txid),
            _entity_endpoints(transaction.output_script_ids, representatives_t, transaction.txid),
        )
        endpoints_T = (
            _entity_endpoints(transaction.input_script_ids, representatives_T, transaction.txid),
            _entity_endpoints(transaction.output_script_ids, representatives_T, transaction.txid),
        )
        rewritten += endpoints_t != endpoints_T
    return rewritten / len(eligible)
