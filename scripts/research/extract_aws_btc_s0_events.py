#!/usr/bin/env python3
"""Extract label-free Gate 3A S0 union events and evaluation-window records.

This is the extraction layer that the frozen ``asof_replay`` reference module
deliberately leaves to a downstream consumer.  It reuses the frozen transaction
semantic auditor for every source-integrity and UTXO-semantic decision and adds
only: (a) common-input star-union events with provenance, (b) frozen filter
decisions, (c) evaluation-window transaction/support records for ``V_j``, and
(d) per-block/per-profile counters.

Boundaries frozen by Gate 3A v1.1
(docs/大创调研/Gate3A-严格按时可见实体图预注册协议-v1.1-20260911.md):

* S0-only: no labels, no entity types, no aliases, no model outputs, no effect
  metrics (``p_merge``/``p_rewrite`` remain uncomputed here).
* ``V_j`` support comes from creation-time window rows only; spent/terminal UTXO
  state is never consulted for support.
* ``script_id`` is SHA-256 of the raw locking-script bytes, computed once in
  ``raw_script_id_bytes``.
* Cutoffs, window and horizons are read from, and validated against, the frozen
  source manifest; they are never hard-coded here.

No network access.  All Parquet bytes must already be present in the local cache
bound by the transaction byte freeze.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import math
import platform
import shutil
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path

import pyarrow.parquet as pq

# The frozen semantic auditor, freezer and preflight modules are addressed by
# bare module name, exactly as the frozen runner imports them.
_SCRIPT_DIR = str(Path(__file__).resolve().parent)
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)

import audit_aws_btc_transaction_semantics as semantics
import freeze_aws_btc_transactions as freezer
import preflight_aws_btc_prefix as source

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from btcaml.data.coinjoin_filters import (  # noqa: E402
    TransactionFeatures,
    d_wp100k_matches,
    exclude_f_pub,
    exclude_f_wide,
    f_pub_matches,
    is_tx0_paper_diagnostic,
)
from btcaml.data.script_identity import (  # noqa: E402
    is_provably_unspendable,
    script_id as frozen_script_id,
)

S0_SCHEMA_VERSION = 1
DEFAULT_SOURCE_MANIFEST = "configs/data/aws_btc_s0_source_manifest_v1_1.json"
# Pinned at freeze time: the manifest cannot hold its own hash without a circular
# trust problem.  Verified against configs/data/aws_btc_s0_source_manifest_v1_0.json.
EXPECTED_SOURCE_MANIFEST_SHA256 = (
    "e32ad2f33ecbc184eb04159f0adbb22dd2a4a1a47f1e280cbbca699432d67f3d"
)
HEURISTIC_ID = "common-input"
HEURISTIC_VERSION = "gate3a-v1.0-common-input-star"
FILTER_PROFILE_F_PUB = "F_pub"
FILTER_PROFILE_F_WIDE = "F_wide"
FILTER_PROFILE_F_NONE = "F_none"
FILTER_PROFILES = (FILTER_PROFILE_F_PUB, FILTER_PROFILE_F_WIDE, FILTER_PROFILE_F_NONE)
PROFILE_VIEW_VERSION = "s0-profile-view-v1"
SCRIPT_ID_BYTES = 32
FROZEN_REFERENCE_CODE = (
    "src/btcaml/data/script_identity.py",
    "src/btcaml/data/asof_replay.py",
    "src/btcaml/data/coinjoin_filters.py",
)
MANIFEST_REQUIRED_FALSE = ("models_authorized", "labels_read", "effect_metrics_read")
MANIFEST_REQUIRED_TRUE = ("s0_only",)
MANIFEST_EXECUTION_FORBIDDEN = (
    "label",
    "entity_type",
    "alias",
    "ground_truth",
    "external attribution",
    "model output",
    "prior effect metric",
)
BASE_LOGICAL_FIELDS = {
    "txid", "hash", "block_hash", "block_number", "index", "input_count",
    "output_count", "is_coinbase", "output_value", "outputs.index",
    "outputs.value", "outputs.script_hex", "date",
}
INPUT_LOGICAL_FIELDS = {
    "fee", "input_value", "inputs.index", "inputs.spent_transaction_hash",
    "inputs.spent_output_index", "inputs.value",
}
BASE_PARQUET_COLUMNS = [
    "txid", "hash", "block_hash", "block_number", "index", "input_count",
    "output_count", "is_coinbase", "output_value", "outputs.list.element.index",
    "outputs.list.element.value", "outputs.list.element.script_hex", "date",
]
INPUT_PARQUET_COLUMNS = [
    "fee", "input_value", "inputs.list.element.index",
    "inputs.list.element.spent_transaction_hash",
    "inputs.list.element.spent_output_index", "inputs.list.element.value",
]


def script_sha256() -> str:
    return hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


def canonical_json_bytes(payload: object) -> bytes:
    return json.dumps(
        payload, ensure_ascii=True, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def validate_source_manifest(manifest_path: Path) -> tuple[bytes, dict]:
    """Verify the frozen manifest against its pinned hash and S0-only boundary."""
    payload = manifest_path.read_bytes()
    actual = hashlib.sha256(payload).hexdigest()
    if actual != EXPECTED_SOURCE_MANIFEST_SHA256:
        raise RuntimeError(
            f"source manifest SHA-256 mismatch: {actual} != {EXPECTED_SOURCE_MANIFEST_SHA256}"
        )
    manifest = json.loads(payload)
    if not isinstance(manifest, dict):
        raise ValueError("source manifest must be a JSON object")
    if manifest.get("schema_version") != "aws-btc-s0-source-manifest-v1.1":
        raise ValueError("unexpected source manifest schema_version")
    if manifest.get("status") != "frozen_for_private_internal_s0":
        raise ValueError("source manifest is not frozen for private internal S0")

    execution = manifest.get("execution_boundary")
    if not isinstance(execution, dict):
        raise ValueError("source manifest lacks execution_boundary")
    for name in MANIFEST_REQUIRED_FALSE:
        if execution.get(name) is not False:
            raise ValueError(f"execution_boundary.{name} must be false")
    for name in MANIFEST_REQUIRED_TRUE:
        if execution.get(name) is not True:
            raise ValueError(f"execution_boundary.{name} must be true")
    allowed = set(execution.get("allowed_columns") or ())
    forbidden = set(execution.get("forbidden_inputs") or ())
    if not allowed:
        raise ValueError("execution_boundary.allowed_columns must not be empty")
    missing_allowed = (BASE_LOGICAL_FIELDS | INPUT_LOGICAL_FIELDS) - allowed
    if missing_allowed:
        raise ValueError(
            f"execution_boundary.allowed_columns lacks {sorted(missing_allowed)}"
        )
    missing_forbidden = set(MANIFEST_EXECUTION_FORBIDDEN) - forbidden
    if missing_forbidden:
        raise ValueError(
            f"execution_boundary.forbidden_inputs lacks {sorted(missing_forbidden)}"
        )
    overlap = allowed & forbidden
    if overlap:
        raise ValueError(f"allowed_columns overlaps forbidden_inputs: {sorted(overlap)}")
    source_block = manifest.get("source")
    if not isinstance(source_block, dict) or source_block.get(
        "public_redistribution_authorized"
    ) is not False:
        raise ValueError("source.public_redistribution_authorized must be false")
    scope = manifest.get("scope")
    if not isinstance(scope, dict):
        raise ValueError("source manifest lacks scope")
    amendment = manifest.get("amendment")
    if manifest.get("supersedes") != "configs/data/aws_btc_s0_source_manifest_v1_0.json":
        raise ValueError("source manifest does not identify the v1.0 predecessor")
    if not isinstance(amendment, dict) or any(
        amendment.get(name) is not False
        for name in ("data_bytes_changed", "design_changed", "labels_or_effects_read")
    ):
        raise ValueError("source manifest amendment boundary is invalid")
    for name in ("last_height", "eligible_end_height"):
        if type(scope.get(name)) is not int:
            raise ValueError(f"scope.{name} must be an integer")
    return payload, manifest


def validate_frozen_artifacts(manifest: dict, repo_root: Path) -> list[dict]:
    """Re-verify each frozen artifact's presence, byte length and SHA-256."""
    artifacts = manifest.get("frozen_artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        raise ValueError("source manifest lacks frozen_artifacts")
    verified: list[dict] = []
    for artifact in artifacts:
        if not isinstance(artifact, dict):
            raise ValueError("frozen_artifacts entries must be objects")
        role = str(artifact.get("role"))
        path = (repo_root / str(artifact.get("path"))).resolve()
        if not path.is_file():
            raise RuntimeError(f"frozen artifact missing ({role}): {path}")
        size = path.stat().st_size
        if size != int(artifact.get("bytes")):
            raise RuntimeError(
                f"frozen artifact byte length mismatch ({role}): {size} != {artifact.get('bytes')}"
            )
        digest = semantics.file_sha256(path)
        if digest != str(artifact.get("sha256")):
            raise RuntimeError(f"frozen artifact SHA-256 mismatch ({role}): {path}")
        verified.append({"role": role, "path": str(artifact.get("path")), "sha256": digest})
    return verified


def validate_reference_code(manifest: dict, repo_root: Path) -> dict[str, str]:
    """Re-verify that the frozen reference modules still match the manifest."""
    entries = manifest.get("reference_code")
    if not isinstance(entries, list) or not entries:
        raise ValueError("source manifest lacks reference_code")
    observed: dict[str, str] = {}
    for entry in entries:
        if not isinstance(entry, dict):
            raise ValueError("reference_code entries must be objects")
        relative = str(entry.get("path"))
        path = (repo_root / relative).resolve()
        if not path.is_file():
            raise RuntimeError(f"reference code missing: {relative}")
        digest = semantics.file_sha256(path)
        if digest != str(entry.get("sha256")):
            raise RuntimeError(f"reference code SHA-256 mismatch: {relative}")
        observed[relative] = digest
    missing = set(FROZEN_REFERENCE_CODE) - set(observed)
    if missing:
        raise ValueError(f"reference_code lacks frozen modules: {sorted(missing)}")
    return observed


def validate_semantic_qualification(manifest: dict) -> dict:
    """Bind the reused UTXO/BIP30 implementation to the qualified source result."""
    qualification = manifest.get("semantic_qualification")
    if not isinstance(qualification, dict):
        raise ValueError("source manifest lacks semantic_qualification")
    if qualification.get("source_qualification_passed") is not True:
        raise ValueError("transaction semantic qualification did not pass")
    if qualification.get("sqlite_quick_check") != "ok":
        raise ValueError("transaction semantic qualification quick_check is not ok")
    if semantics.script_sha256() != qualification.get("script_sha256"):
        raise RuntimeError("frozen transaction semantic implementation SHA-256 mismatch")
    for name in ("missing_prevout_failures", "value_conservation_failures"):
        if qualification.get(name) != 0:
            raise ValueError(f"semantic_qualification.{name} must be zero")
    if qualification.get("bip30_exception_overwrites") != 2:
        raise ValueError("semantic qualification lacks the two exact BIP30 overwrites")
    return dict(qualification)


def s0_design(manifest: dict) -> dict:
    """Extract and validate the S0 design block from the frozen manifest."""
    design = manifest.get("s0_design")
    if not isinstance(design, dict):
        raise ValueError("source manifest lacks s0_design")
    cutoffs = design.get("cutoff_heights")
    if not isinstance(cutoffs, list) or not cutoffs or any(
        type(value) is not int or value < 0 for value in cutoffs
    ):
        raise ValueError("s0_design.cutoff_heights must be nonnegative integers")
    if cutoffs != sorted(set(cutoffs)):
        raise ValueError("s0_design.cutoff_heights must be strictly ascending")
    window = design.get("window_blocks")
    horizon = design.get("primary_horizon_blocks")
    sensitivity = design.get("sensitivity_horizon_blocks")
    if type(window) is not int or window <= 0:
        raise ValueError("s0_design.window_blocks must be a positive integer")
    if type(horizon) is not int or horizon <= 0:
        raise ValueError("s0_design.primary_horizon_blocks must be a positive integer")
    if not isinstance(sensitivity, list) or any(
        type(value) is not int or value <= 0 for value in sensitivity
    ):
        raise ValueError("s0_design.sensitivity_horizon_blocks must be positive integers")
    if design.get("profiles") != [FILTER_PROFILE_F_PUB, FILTER_PROFILE_F_WIDE]:
        raise ValueError("s0_design.profiles must be exactly F_pub and F_wide")
    if design.get("diagnostic_profile") != FILTER_PROFILE_F_NONE:
        raise ValueError("s0_design.diagnostic_profile must be F_none")
    if design.get("primary_metrics") != ["p_merge", "p_rewrite"]:
        raise ValueError("s0_design.primary_metrics must be p_merge and p_rewrite")
    if design.get("minimum_practical_difference") != 0.01:
        raise ValueError("s0_design.minimum_practical_difference must be 0.01")
    if design.get("bootstrap_replicates") != 10_000:
        raise ValueError("s0_design.bootstrap_replicates must be 10000")
    if design.get("bootstrap_block_lengths") != [144, 72, 288]:
        raise ValueError("s0_design.bootstrap_block_lengths must be [144, 72, 288]")
    scope = manifest.get("scope")
    if not isinstance(scope, dict):
        raise ValueError("source manifest lacks scope")
    first, last = scope.get("first_height"), scope.get("last_height")
    if first != 0 or type(last) is not int or scope.get("blocks") != last + 1:
        raise ValueError("source scope must be the contiguous genesis prefix")
    eligible_end = last - horizon
    if scope.get("eligible_end_height") != eligible_end:
        raise ValueError("scope.eligible_end_height disagrees with the primary horizon")
    if any(cutoff > eligible_end or cutoff - window + 1 < 0 for cutoff in cutoffs):
        raise ValueError("a frozen cutoff cannot support its historical window and primary horizon")
    return json.loads(json.dumps(design))


def horizon_cells(design: dict, last_height: int) -> list[dict]:
    """Enumerate every cutoff-by-horizon cell with its availability.

    A cell is available when its horizon end fits inside the frozen prefix.  Cells
    that do not fit stay in the list marked ``available: false`` so the protocol can
    record their structural unavailability; they never become windows.
    """
    horizons = sorted(
        {design["primary_horizon_blocks"], *design["sensitivity_horizon_blocks"]}
    )
    cells = []
    for cutoff in design["cutoff_heights"]:
        for horizon in horizons:
            end = cutoff + horizon
            cells.append(
                {
                    "cutoff_height": cutoff,
                    "horizon_blocks": horizon,
                    "future_end_height": end,
                    "available": end <= last_height,
                }
            )
    return cells


def compute_target_height(design: dict, scope: dict) -> int:
    """Highest height the *available* S0 cells require, bounded by the prefix.

    Only cells whose end fits inside ``scope.last_height`` count.  A horizon that
    runs past the prefix is a structurally unavailable cell, not a source failure.
    Every primary (``H_main``) cell must be available or the design cannot run.
    """
    last_height = int(scope["last_height"])
    cells = horizon_cells(design, last_height)
    primary = {
        (cutoff, design["primary_horizon_blocks"]) for cutoff in design["cutoff_heights"]
    }
    unavailable_primary = sorted(
        f"(cutoff={cell['cutoff_height']}, horizon={cell['horizon_blocks']})"
        for cell in cells
        if not cell["available"]
        and (cell["cutoff_height"], cell["horizon_blocks"]) in primary
    )
    if unavailable_primary:
        raise ValueError(
            f"primary horizon cells fall outside the frozen prefix: {unavailable_primary}"
        )
    ends = [cell["future_end_height"] for cell in cells if cell["available"]]
    if not ends:
        raise ValueError("no S0 cell is available inside the frozen prefix")
    return max(ends)


def build_windows(design: dict) -> list[dict]:
    """The four unique historical evaluation windows.

    Horizons change only the future partition cutoff.  ``X_j`` and ``V_j`` are
    keyed by the historical cutoff, so storing them once avoids three equivalent
    copies per cutoff.
    """
    window = design["window_blocks"]
    return [
            {
                "window_id": f"t{cutoff}",
                "cutoff_height": cutoff,
                "window_blocks": window,
                "win_start_height": cutoff - window + 1,
                "win_end_height": cutoff,
            }
            for cutoff in design["cutoff_heights"]
        ]


def raw_script_id_bytes(raw_script: bytes, label: str) -> bytes:
    """Frozen ``script_id`` of raw locking-script bytes, as a 32-byte blob.

    This is the only place raw locking-script bytes are hashed.
    """
    if not isinstance(raw_script, bytes):
        raise RuntimeError(f"{label} raw locking script must be bytes")
    decoded = bytes.fromhex(frozen_script_id(raw_script))
    if len(decoded) != SCRIPT_ID_BYTES:
        raise RuntimeError(f"{label} script_id did not decode to 32 bytes")
    return decoded


def common_input_star(script_id_list: list[bytes]) -> list[tuple[bytes, bytes, list[int]]]:
    """Star unions of one non-coinbase transaction.

    Returns ``(anchor, member, member_input_indices)`` triples in canonical order.
    The anchor is the lexicographically smallest distinct input ``script_id``; every
    other distinct script joins it.  Fewer than two distinct input scripts yields no
    union.  The tuple position is the protocol ``event_index``.
    """
    by_script: dict[bytes, list[int]] = defaultdict(list)
    for input_index, script_id in enumerate(script_id_list):
        by_script[script_id].append(input_index)
    ordered = sorted(by_script)
    if len(ordered) < 2:
        return []
    anchor = ordered[0]
    return [(anchor, member, sorted(by_script[member])) for member in ordered[1:]]


def compute_event_id(
    source_manifest_sha256: str,
    block_hash: bytes,
    block_height: int,
    txid: bytes,
    tx_index: int,
    event_index: int,
    script_id_a: bytes,
    script_id_b: bytes,
    heuristic_version: str,
) -> bytes:
    """Deterministic SHA-256 identity over the frozen event key fields."""
    payload = b"\x1f".join(
        (
            source_manifest_sha256.encode("ascii"),
            block_hash,
            str(block_height).encode("ascii"),
            txid,
            str(tx_index).encode("ascii"),
            str(event_index).encode("ascii"),
            script_id_a,
            script_id_b,
            heuristic_version.encode("ascii"),
        )
    )
    return hashlib.sha256(payload).digest()


def encode_script_ids(script_ids: list[bytes]) -> bytes:
    """Pack already-hashed 32-byte script IDs: deduplicate, sort, concatenate."""
    for script_id in script_ids:
        if not isinstance(script_id, bytes) or len(script_id) != SCRIPT_ID_BYTES:
            raise RuntimeError("packed endpoints must be 32-byte script-id blobs")
    return b"".join(sorted(set(script_ids)))


def decode_script_ids(payload: bytes) -> list[bytes]:
    if not isinstance(payload, bytes) or len(payload) % SCRIPT_ID_BYTES:
        raise RuntimeError("packed script-id blob has an invalid length")
    return [
        payload[offset : offset + SCRIPT_ID_BYTES]
        for offset in range(0, len(payload), SCRIPT_ID_BYTES)
    ]


def transaction_features(row: dict, input_script_ids: list[bytes]) -> TransactionFeatures:
    """Frozen-filter features for one transaction.

    OP_RETURN and every other output script stay in the features; the unspendable
    exclusion applies only when building ``V_j`` support, never to filtering.
    """
    return TransactionFeatures(
        input_script_ids=tuple(script_id.hex() for script_id in input_script_ids),
        input_values=tuple(
            item["value_sat"] for item in sorted(row["inputs"], key=lambda v: v["index"])
        ),
        output_script_ids=tuple(
            raw_script_id_bytes(output["script"], row["source"]).hex()
            for output in sorted(row["outputs"], key=lambda v: v["index"])
        ),
        output_values_raw=tuple(
            output["value_sat"]
            for output in sorted(row["outputs"], key=lambda v: v["index"])
        ),
    )


def transaction_profile_facts(row: dict, input_script_ids: list[bytes]) -> dict:
    """Compute the frozen profile decisions once for one non-coinbase transaction."""
    features = transaction_features(row, input_script_ids)
    return {
        "triples": common_input_star(input_script_ids),
        "f_pub_matches": f_pub_matches(features),
        "d_wp100k_matches": d_wp100k_matches(features),
        "exclude_f_pub": exclude_f_pub(features),
        "exclude_f_wide": exclude_f_wide(features),
        "d_tx0_paper": is_tx0_paper_diagnostic(features),
    }


def create_s0_schema(connection: sqlite3.Connection) -> None:
    """Extend the reused semantic state schema with the S0 extraction tables."""
    connection.executescript(
        """
        CREATE TABLE run_context (
            context_id INTEGER PRIMARY KEY CHECK (context_id = 1),
            s0_schema_version INTEGER NOT NULL,
            heuristic_id TEXT NOT NULL,
            heuristic_version TEXT NOT NULL,
            profile_view_version TEXT NOT NULL,
            source_manifest_sha256 TEXT NOT NULL,
            runner_sha256 TEXT NOT NULL,
            target_height INTEGER NOT NULL,
            design_json TEXT NOT NULL
        );

        CREATE TABLE union_events (
            event_id BLOB PRIMARY KEY,
            block_hash BLOB NOT NULL,
            height INTEGER NOT NULL,
            txid BLOB NOT NULL,
            tx_index INTEGER NOT NULL,
            event_index INTEGER NOT NULL,
            script_id_a BLOB NOT NULL,
            script_id_b BLOB NOT NULL,
            exclude_f_pub INTEGER NOT NULL,
            exclude_f_wide INTEGER NOT NULL,
            evidence_json TEXT NOT NULL
        ) WITHOUT ROWID;
        CREATE INDEX union_events_order
            ON union_events(height, tx_index, event_index, script_id_a, script_id_b);

        CREATE TABLE window_transactions (
            window_id TEXT NOT NULL,
            height INTEGER NOT NULL,
            block_hash BLOB NOT NULL,
            tx_index INTEGER NOT NULL,
            txid BLOB NOT NULL,
            input_script_ids BLOB NOT NULL,
            output_script_ids BLOB NOT NULL,
            is_coinbase INTEGER NOT NULL,
            input_sat INTEGER,
            output_sat INTEGER NOT NULL,
            fee_sat INTEGER,
            PRIMARY KEY (window_id, txid)
        ) WITHOUT ROWID;

        CREATE TABLE window_support (
            window_id TEXT NOT NULL,
            script_id BLOB NOT NULL,
            first_height INTEGER NOT NULL,
            PRIMARY KEY (window_id, script_id)
        ) WITHOUT ROWID;

        CREATE TABLE block_profile_stats (
            height INTEGER NOT NULL,
            filter_profile TEXT NOT NULL,
            block_hash BLOB NOT NULL,
            transactions INTEGER NOT NULL,
            noncoinbase INTEGER NOT NULL,
            excluded INTEGER NOT NULL,
            candidate_unions INTEGER NOT NULL,
            dominant_detector_hits INTEGER NOT NULL,
            joinmarket_hits INTEGER NOT NULL,
            wasabi_1_0_hits INTEGER NOT NULL,
            wasabi_1_1_hits INTEGER NOT NULL,
            wasabi_2_hits INTEGER NOT NULL,
            whirlpool_hits INTEGER NOT NULL,
            d_wp100k_hits INTEGER NOT NULL,
            d_tx0_paper_hits INTEGER NOT NULL,
            PRIMARY KEY (height, filter_profile)
        ) WITHOUT ROWID;

        CREATE INDEX window_transactions_height ON window_transactions(window_id, height);
        CREATE INDEX window_support_height ON window_support(window_id, first_height);

        CREATE VIEW union_event_records AS
        SELECT
            lower(hex(e.event_id)) AS event_id,
            e.block_hash,
            e.height AS block_height,
            e.txid,
            e.tx_index,
            e.event_index,
            e.script_id_a,
            e.script_id_b,
            v.filter_profile,
            v.filter_decision,
            e.exclude_f_pub,
            e.exclude_f_wide,
            e.evidence_json,
            'common-input' AS heuristic_id,
            (SELECT heuristic_version FROM run_context WHERE context_id = 1)
                AS heuristic_version,
            (SELECT source_manifest_sha256 FROM run_context WHERE context_id = 1)
                AS source_manifest_sha256,
            v.profile_view_version
        FROM union_events AS e
        JOIN (
            SELECT event_id, 'F_pub' AS filter_profile,
                   CASE exclude_f_pub WHEN 1 THEN 'exclude' ELSE 'include' END
                       AS filter_decision,
                   's0-profile-view-v1' AS profile_view_version
            FROM union_events
            UNION ALL
            SELECT event_id, 'F_wide',
                   CASE exclude_f_wide WHEN 1 THEN 'exclude' ELSE 'include' END,
                   's0-profile-view-v1'
            FROM union_events
            UNION ALL
            SELECT event_id, 'F_none', 'include', 's0-profile-view-v1'
            FROM union_events
        ) AS v ON v.event_id = e.event_id;
        """
    )


def s0_default_counters() -> dict[str, int]:
    return {
        "union_events": 0,
        "window_transactions": 0,
        "window_support": 0,
        "blocks_with_stats": 0,
        "block_profile_stat_rows": 0,
        "suppressed_union_events_f_pub": 0,
        "suppressed_union_events_f_wide": 0,
        "duplicate_union_events": 0,
    }


def open_s0_state(
    path: Path, bindings: dict, started_utc: str, s0_bindings: dict
) -> tuple[sqlite3.Connection, int, dict, dict]:
    """Open or create the S0 state database, layering S0 tables on the reuse.

    The reused ``open_state`` owns the semantic state and counters.  S0 tables are
    created only on fresh creation and are verified on resume, so a changed runner,
    manifest, or target height is refused.
    """
    existed = path.exists()
    connection, committed_height, counters = semantics.open_state(path, bindings, started_utc)
    if not existed:
        create_s0_schema(connection)
        s0_counters = s0_default_counters()
        connection.execute(
            "INSERT INTO run_context("
            "context_id, s0_schema_version, heuristic_id, heuristic_version, "
            "profile_view_version, source_manifest_sha256, runner_sha256, "
            "target_height, design_json) VALUES (1, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                S0_SCHEMA_VERSION,
                HEURISTIC_ID,
                HEURISTIC_VERSION,
                PROFILE_VIEW_VERSION,
                s0_bindings["source_manifest_sha256"],
                s0_bindings["runner_sha256"],
                int(s0_bindings["target_height"]),
                canonical_json_bytes(s0_bindings["design"]).decode("utf-8"),
            ),
        )
        semantics.metadata_set(connection, "s0_bindings", s0_bindings)
        semantics.metadata_set(connection, "s0_counters", s0_counters)
        connection.commit()
        return connection, committed_height, counters, s0_counters

    exists = connection.execute(
        "SELECT COUNT(*) FROM sqlite_master WHERE type = 'table' AND name = 'union_events'"
    ).fetchone()[0]
    if not exists:
        raise RuntimeError(
            "existing state database has no S0 tables; refusing to reuse a "
            "semantic-only state database for S0 extraction"
        )
    stored = json.loads(semantics.metadata_get(connection, "s0_bindings"))
    if stored != s0_bindings:
        raise RuntimeError("S0 state bindings differ from this run")
    s0_counters = json.loads(semantics.metadata_get(connection, "s0_counters"))
    if set(s0_counters) != set(s0_default_counters()):
        raise RuntimeError("S0 counters have an incompatible schema")
    row = connection.execute(
        "SELECT s0_schema_version, runner_sha256, source_manifest_sha256, target_height "
        "FROM run_context WHERE context_id = 1"
    ).fetchone()
    if row is None:
        raise RuntimeError("S0 state is missing its run_context row")
    if int(row[0]) != S0_SCHEMA_VERSION:
        raise RuntimeError("S0 run_context schema version mismatch")
    if str(row[1]) != s0_bindings["runner_sha256"]:
        raise RuntimeError("S0 runner content changed since the committed state")
    if str(row[2]) != s0_bindings["source_manifest_sha256"]:
        raise RuntimeError("S0 source manifest changed since the committed state")
    if int(row[3]) != int(s0_bindings["target_height"]):
        raise RuntimeError("S0 target height changed since the committed state")
    return connection, committed_height, counters, s0_counters


def validate_s0_checkpoint(
    connection: sqlite3.Connection, height: int, counters: dict, s0_counters: dict
) -> None:
    """Cross-check S0 tables against the committed block prefix and counters."""
    if int(counters["blocks"]) != height + 1:
        raise RuntimeError("S0 checkpoint block count disagrees with committed height")
    for table, key in (
        ("union_events", "union_events"),
        ("window_transactions", "window_transactions"),
        ("window_support", "window_support"),
        ("block_profile_stats", "block_profile_stat_rows"),
    ):
        rows = int(connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])
        if rows != int(s0_counters[key]):
            raise RuntimeError(f"S0 {table} count disagrees with SQLite state")
    stats_blocks = int(
        connection.execute(
            "SELECT COUNT(DISTINCT height) FROM block_profile_stats"
        ).fetchone()[0]
    )
    if stats_blocks != int(s0_counters["blocks_with_stats"]):
        raise RuntimeError("S0 block profile stats disagree with committed block count")
    if stats_blocks != height + 1:
        raise RuntimeError("S0 block profile stats do not cover every committed block")
    if int(s0_counters["block_profile_stat_rows"]) != (height + 1) * len(FILTER_PROFILES):
        raise RuntimeError("S0 block profile stats do not cover every frozen profile")
    for table in ("union_events", "block_profile_stats"):
        maximum = connection.execute(f"SELECT MAX(height) FROM {table}").fetchone()[0]
        if maximum is not None and int(maximum) > height:
            raise RuntimeError(
                f"S0 {table} contains a record later than the committed height"
            )


def checkpoint_s0(
    connection: sqlite3.Connection, height: int, counters: dict, s0_counters: dict
) -> None:
    """Commit the semantic checkpoint and the S0 counters together."""
    semantics.metadata_set(connection, "last_committed_height", height)
    semantics.metadata_set(connection, "counters", counters)
    semantics.metadata_set(connection, "s0_counters", s0_counters)
    connection.commit()
    connection.execute("PRAGMA wal_checkpoint(TRUNCATE)")


def _active_windows(height: int, windows: list[dict]) -> list[dict]:
    return [
        window
        for window in windows
        if window["win_start_height"] <= height <= window["win_end_height"]
    ]


def _live_input_scripts(connection: sqlite3.Connection, row: dict) -> list[bytes]:
    """Read each prevout's creation-time locking script from the live state.

    Must run before the frozen ``process_transaction`` consumes those outpoints.
    Never substitutes the spending input's scriptSig.
    """
    scripts: list[bytes] = []
    for transaction_input in sorted(row["inputs"], key=lambda value: value["index"]):
        parent = connection.execute(
            "SELECT script FROM utxo WHERE txid = ? AND vout = ?",
            (transaction_input["parent_txid"], transaction_input["parent_vout"]),
        ).fetchone()
        if parent is None or not isinstance(parent[0], bytes):
            raise RuntimeError(
                f"{row['source']} lost its live prevout during S0 extraction"
            )
        scripts.append(parent[0])
    return scripts


def _record_s0_for_row(
    connection: sqlite3.Connection,
    row: dict,
    input_scripts: list[bytes],
    s0_counters: dict,
    windows: list[dict],
    source_manifest_sha256: str,
) -> dict | None:
    """Write one accepted transaction's union, window and support records."""
    input_script_ids = [
        raw_script_id_bytes(script, row["source"]) for script in input_scripts
    ]
    facts = None if row["is_coinbase"] else transaction_profile_facts(row, input_script_ids)
    if facts is not None:
        _record_union_events(
            connection, row, input_script_ids, facts, s0_counters, source_manifest_sha256
        )
    active = _active_windows(row["height"], windows)
    if not active:
        return facts
    _record_window_transaction(connection, row, input_scripts, active, s0_counters)
    _record_window_support(connection, row, input_scripts, active, s0_counters)
    return facts


def record_transaction_s0(
    connection: sqlite3.Connection,
    row: dict,
    counters: dict,
    s0_counters: dict,
    windows: list[dict],
    source_manifest_sha256: str,
) -> dict | None:
    """The single correct entry point for one transaction's S0 records.

    Contract: read the prevout locking scripts first (they are still live), then
    hand the row to the frozen ``process_transaction``, then write S0 records only
    if that call returned.  This ordering is mandatory because the frozen processor
    deletes consumed prevouts inside the same call.
    """
    input_scripts = _live_input_scripts(connection, row)
    semantics.process_transaction(connection, row, counters)
    return _record_s0_for_row(
        connection, row, input_scripts, s0_counters, windows, source_manifest_sha256
    )


def _record_union_events(
    connection: sqlite3.Connection,
    row: dict,
    input_script_ids: list[bytes],
    facts: dict,
    s0_counters: dict,
    source_manifest_sha256: str,
) -> None:
    """Insert star-union candidate events with their frozen filter decisions."""
    triples = facts["triples"]
    if not triples:
        return
    matches = facts["f_pub_matches"]
    matches_wp100k = facts["d_wp100k_matches"]
    excluded_f_pub = facts["exclude_f_pub"]
    excluded_f_wide = facts["exclude_f_wide"]
    tx0_diagnostic = facts["d_tx0_paper"]
    for event_index, (anchor, member, member_inputs) in enumerate(triples):
        event_id = compute_event_id(
            source_manifest_sha256,
            row["block_hash"],
            row["height"],
            row["txid"],
            row["position"],
            event_index,
            anchor,
            member,
            HEURISTIC_VERSION,
        )
        evidence = canonical_json_bytes(
            {
                "heuristic_id": HEURISTIC_ID,
                "source": row["source"],
                "anchor_input_indices": sorted(
                    index
                    for index, script_id in enumerate(input_script_ids)
                    if script_id == anchor
                ),
                "member_input_indices": member_inputs,
                "f_pub_matches": list(matches),
                "d_wp100k_matches": list(matches_wp100k),
                "d_tx0_paper": bool(tx0_diagnostic),
            }
        ).decode("utf-8")
        values = (
            row["block_hash"],
            row["height"],
            row["txid"],
            row["position"],
            event_index,
            anchor,
            member,
            int(excluded_f_pub),
            int(excluded_f_wide),
            evidence,
        )
        inserted = connection.execute(
            "INSERT OR IGNORE INTO union_events("
            "event_id, block_hash, height, txid, tx_index, event_index, "
            "script_id_a, script_id_b, exclude_f_pub, exclude_f_wide, evidence_json"
            ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (event_id, *values),
        )
        if inserted.rowcount == 1:
            s0_counters["union_events"] += 1
            if excluded_f_pub:
                s0_counters["suppressed_union_events_f_pub"] += 1
            if excluded_f_wide:
                s0_counters["suppressed_union_events_f_wide"] += 1
        else:
            stored = connection.execute(
                "SELECT block_hash, height, txid, tx_index, event_index, script_id_a, "
                "script_id_b, exclude_f_pub, exclude_f_wide, evidence_json "
                "FROM union_events WHERE event_id = ?",
                (event_id,),
            ).fetchone()
            if stored != values:
                raise RuntimeError("union event ID collision has conflicting provenance")
            s0_counters["duplicate_union_events"] += 1


def _record_window_transaction(
    connection: sqlite3.Connection,
    row: dict,
    input_scripts: list[bytes],
    active: list[dict],
    s0_counters: dict,
) -> None:
    """Insert the window transaction with unspendable outputs removed.

    Input endpoints keep every prevout locking script.  Output endpoints drop
    scripts the frozen rule calls provably unspendable at creation time.
    """
    spendable_outputs = [
        output["script"]
        for output in sorted(row["outputs"], key=lambda value: value["index"])
        if not is_provably_unspendable(output["script"])
    ]
    packed_inputs = encode_script_ids(
        [raw_script_id_bytes(script, row["source"]) for script in input_scripts]
    )
    packed_outputs = encode_script_ids(
        [raw_script_id_bytes(script, row["source"]) for script in spendable_outputs]
    )
    for window in active:
        inserted = connection.execute(
            "INSERT OR IGNORE INTO window_transactions("
            "window_id, height, block_hash, tx_index, txid, input_script_ids, "
            "output_script_ids, is_coinbase, input_sat, output_sat, fee_sat"
            ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                window["window_id"],
                row["height"],
                row["block_hash"],
                row["position"],
                row["txid"],
                packed_inputs,
                packed_outputs,
                int(row["is_coinbase"]),
                None if row["input_value"] is None else int(row["input_value"]),
                int(row["output_value"]),
                None if row["fee"] is None else int(row["fee"]),
            ),
        )
        if inserted.rowcount == 1:
            s0_counters["window_transactions"] += 1


def _record_window_support(
    connection: sqlite3.Connection,
    row: dict,
    input_scripts: list[bytes],
    active: list[dict],
    s0_counters: dict,
) -> None:
    """Add window support scripts from creation-time rows only.

    Support is the unique set of prevout locking scripts of every window input,
    plus every window output script not provably unspendable at creation.  Spent
    and terminal UTXO state is never consulted.
    """
    contributions: dict[bytes, int] = {
        raw_script_id_bytes(script, row["source"]): row["height"]
        for script in input_scripts
    }
    for output in sorted(row["outputs"], key=lambda value: value["index"]):
        if is_provably_unspendable(output["script"]):
            continue
        contributions[raw_script_id_bytes(output["script"], row["source"])] = row["height"]
    for window in active:
        for script_id, first_height in contributions.items():
            inserted = connection.execute(
                "INSERT OR IGNORE INTO window_support("
                "window_id, script_id, first_height) VALUES (?, ?, ?)",
                (window["window_id"], script_id, first_height),
            )
            if inserted.rowcount == 1:
                s0_counters["window_support"] += 1


def process_block_s0(
    connection: sqlite3.Connection,
    height: int,
    rows: list[dict],
    block: dict,
    counters: dict,
    s0_counters: dict,
    windows: list[dict],
    source_manifest_sha256: str,
    profile_stats: dict,
) -> None:
    """Validate one complete block, then process each row through the single S0 entry."""
    expected_count = int(block["transaction_count"])
    if len(rows) != expected_count:
        raise RuntimeError(
            f"height {height} transaction count differs: {len(rows)} != {expected_count}"
        )
    rows.sort(key=lambda row: row["position"])
    if [row["position"] for row in rows] != list(range(expected_count)):
        raise RuntimeError(f"height {height} indexes are not the exact block permutation")
    expected_hash = bytes.fromhex(str(block["hash"]))
    processed: list[tuple[dict, dict | None]] = []
    for row in rows:
        if row["height"] != height or row["block_hash"] != expected_hash:
            raise RuntimeError(f"height {height} row block binding mismatch")
        facts = record_transaction_s0(
            connection,
            row,
            counters,
            s0_counters,
            windows,
            source_manifest_sha256,
        )
        processed.append((row, facts))
    counters["blocks"] += 1
    _accumulate_block_profile_stats(height, block, processed, profile_stats)


def _accumulate_block_profile_stats(
    height: int,
    block: dict,
    rows: list[tuple[dict, dict | None]],
    profile_stats: dict,
) -> None:
    """Count per-profile exclusions and detector hits for one committed block."""
    for profile in FILTER_PROFILES:
        entry = profile_stats.setdefault(
            (height, profile),
            {
                "block_hash": bytes.fromhex(str(block["hash"])),
                "transactions": 0,
                "noncoinbase": 0,
                "excluded": 0,
                "candidate_unions": 0,
                "detectors": defaultdict(int),
                "d_wp100k": 0,
                "d_tx0_paper": 0,
            },
        )
        for row, facts in rows:
            entry["transactions"] += 1
            if row["is_coinbase"]:
                continue
            if facts is None:
                raise RuntimeError("non-coinbase transaction lacks profile facts")
            entry["noncoinbase"] += 1
            excluded = (
                facts["exclude_f_pub"]
                if profile == FILTER_PROFILE_F_PUB
                else facts["exclude_f_wide"]
                if profile == FILTER_PROFILE_F_WIDE
                else False
            )
            if excluded:
                entry["excluded"] += 1
            for name in facts["f_pub_matches"]:
                entry["detectors"][name] += 1
            if facts["d_wp100k_matches"]:
                entry["d_wp100k"] += 1
            if facts["d_tx0_paper"]:
                entry["d_tx0_paper"] += 1
            if not excluded:
                entry["candidate_unions"] += len(facts["triples"])

def flush_block_profile_stats(
    connection: sqlite3.Connection, profile_stats: dict, s0_counters: dict
) -> None:
    """Persist accumulated per-block/per-profile counters and clear the buffer."""
    for (height, profile), entry in sorted(profile_stats.items()):
        detectors = entry["detectors"]
        connection.execute(
            "INSERT OR REPLACE INTO block_profile_stats("
            "height, filter_profile, block_hash, transactions, noncoinbase, excluded, "
            "candidate_unions, dominant_detector_hits, joinmarket_hits, wasabi_1_0_hits, "
            "wasabi_1_1_hits, wasabi_2_hits, whirlpool_hits, d_wp100k_hits, d_tx0_paper_hits"
            ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                height,
                profile,
                entry["block_hash"],
                entry["transactions"],
                entry["noncoinbase"],
                entry["excluded"],
                entry["candidate_unions"],
                sum(detectors.values()),
                detectors.get("joinmarket", 0),
                detectors.get("wasabi_1_0", 0),
                detectors.get("wasabi_1_1", 0),
                detectors.get("wasabi_2", 0),
                detectors.get("whirlpool", 0),
                entry["d_wp100k"],
                entry["d_tx0_paper"],
            ),
        )
    profile_stats.clear()
    # Derive both counters from the table so they stay exact across resumes and
    # after INSERT OR REPLACE rewrites of the same (height, profile) keys.
    s0_counters["block_profile_stat_rows"] = int(
        connection.execute("SELECT COUNT(*) FROM block_profile_stats").fetchone()[0]
    )
    s0_counters["blocks_with_stats"] = int(
        connection.execute("SELECT COUNT(DISTINCT height) FROM block_profile_stats").fetchone()[0]
    )


def replay_s0(
    connection: sqlite3.Connection,
    items: list[dict],
    schema_by_key: dict[str, dict],
    transaction_cache_dir: Path,
    by_height: dict[int, dict],
    hmax: int,
    committed_height: int,
    counters: dict,
    s0_counters: dict,
    windows: list[dict],
    source_manifest_sha256: str,
    batch_size: int,
    checkpoint_blocks: int,
    reserve_bytes: int,
    state_db: Path,
    pause_after_height: int | None,
) -> int:
    """Drive the frozen partition plan, emitting S0 records per committed block."""
    if pause_after_height is not None and pause_after_height <= committed_height:
        raise semantics.OperatorPause(
            f"requested pause height {pause_after_height} is already committed"
        )
    groups = semantics.partition_plan(items, by_height, committed_height)
    buffer: dict[int, list[dict]] = defaultdict(list)
    next_height = committed_height + 1
    blocks_since_checkpoint = 0
    profile_stats: dict = {}
    connection.execute("BEGIN IMMEDIATE")
    try:
        for group_number, group in enumerate(groups, start=1):
            partition_date = group["date"]
            if math.isinf(group["eligible_min"]):
                continue
            for item in group["items"]:
                key = str(item["key"])
                path = source.cache_path(transaction_cache_dir, item)
                schema_record = schema_by_key[key]
                columns = list(BASE_PARQUET_COLUMNS)
                if schema_record.get("inputs_present"):
                    columns.extend(INPUT_PARQUET_COLUMNS)
                parquet = pq.ParquetFile(path)
                rows_read = 0
                for batch in parquet.iter_batches(batch_size=batch_size, columns=columns):
                    rows = batch.to_pylist()
                    rows_read += len(rows)
                    for raw_row in rows:
                        raw_height = semantics.integer(
                            raw_row.get("block_number"), f"{key}.block_number"
                        )
                        if raw_height <= committed_height or raw_height > hmax:
                            # Above target is deliberately skipped: S0 needs only the
                            # rows up to the required target height.
                            continue
                        row = semantics.compact_row(raw_row, partition_date, key)
                        block = by_height[row["height"]]
                        if str(block["partition_date"]) != partition_date:
                            raise RuntimeError(
                                f"{row['source']} differs from block partition date"
                            )
                        buffer[row["height"]].append(row)
                if rows_read != int(schema_record["rows"]):
                    raise RuntimeError(f"{key} row count changed since schema audit")

            flush_before = group["flush_before"]
            if math.isinf(flush_before):
                flush_before = hmax + 1
            while next_height < min(int(flush_before), hmax + 1):
                rows = buffer.pop(next_height, None)
                if rows is None:
                    raise RuntimeError(
                        f"height {next_height} is absent below the unread watermark"
                    )
                process_block_s0(
                    connection,
                    next_height,
                    rows,
                    by_height[next_height],
                    counters,
                    s0_counters,
                    windows,
                    source_manifest_sha256,
                    profile_stats,
                )
                blocks_since_checkpoint += 1
                low_space = shutil.disk_usage(state_db.parent).free < reserve_bytes
                operator_pause = (
                    pause_after_height is not None and next_height >= pause_after_height
                )
                if blocks_since_checkpoint >= checkpoint_blocks or low_space or operator_pause:
                    flush_block_profile_stats(connection, profile_stats, s0_counters)
                    checkpoint_s0(connection, next_height, counters, s0_counters)
                    print(
                        json.dumps(
                            {
                                "checkpoint_height": next_height,
                                "union_events": s0_counters["union_events"],
                                "free_bytes": shutil.disk_usage(state_db.parent).free,
                            },
                            sort_keys=True,
                        ),
                        file=sys.stderr,
                        flush=True,
                    )
                    blocks_since_checkpoint = 0
                    if low_space:
                        raise semantics.SpaceStop(
                            f"free space fell below reserve after height {next_height}"
                        )
                    if operator_pause:
                        raise semantics.OperatorPause(
                            f"paused after complete height {next_height}"
                        )
                    connection.execute("BEGIN IMMEDIATE")
                next_height += 1
            if group_number == 1 or group_number % 100 == 0 or group_number == len(groups):
                print(
                    f"read partition group {group_number}/{len(groups)}; "
                    f"next height {next_height}",
                    file=sys.stderr,
                    flush=True,
                )

        while next_height <= hmax:
            rows = buffer.pop(next_height, None)
            if rows is None:
                raise RuntimeError(f"height {next_height} is absent at final flush")
            process_block_s0(
                connection,
                next_height,
                rows,
                by_height[next_height],
                counters,
                s0_counters,
                windows,
                source_manifest_sha256,
                profile_stats,
            )
            next_height += 1
        if buffer:
            raise RuntimeError(f"unflushed heights remain: {sorted(buffer)[:5]}")
        flush_block_profile_stats(connection, profile_stats, s0_counters)
        checkpoint_s0(connection, hmax, counters, s0_counters)
        return hmax
    except BaseException:
        if connection.in_transaction:
            connection.rollback()
        raise


def parser() -> argparse.ArgumentParser:
    argument_parser = argparse.ArgumentParser(description=__doc__)
    argument_parser.add_argument("--source-manifest", default=DEFAULT_SOURCE_MANIFEST)
    argument_parser.add_argument("--transaction-cache-dir")
    argument_parser.add_argument("--block-cache-dir")
    argument_parser.add_argument("--state-db")
    argument_parser.add_argument("--output")
    argument_parser.add_argument(
        "--reserve-gib", type=freezer.nonnegative_int, default=semantics.DEFAULT_RESERVE_GIB
    )
    argument_parser.add_argument(
        "--batch-size", type=source.positive_int, default=semantics.DEFAULT_BATCH_SIZE
    )
    argument_parser.add_argument(
        "--checkpoint-blocks",
        type=source.positive_int,
        default=semantics.DEFAULT_CHECKPOINT_BLOCKS,
    )
    argument_parser.add_argument("--pause-after-height", type=freezer.nonnegative_int)
    argument_parser.add_argument("--self-test", action="store_true")
    return argument_parser


def self_test() -> None:
    """Fast synthetic checks that touch no cache and no network."""
    manifest_path = Path(__file__).resolve().parents[2] / DEFAULT_SOURCE_MANIFEST
    payload, manifest = validate_source_manifest(manifest_path)
    assert hashlib.sha256(payload).hexdigest() == EXPECTED_SOURCE_MANIFEST_SHA256
    validate_semantic_qualification(manifest)
    design = s0_design(manifest)
    target = compute_target_height(design, manifest["scope"])
    assert target == 286560, target
    cells = horizon_cells(design, target)
    assert len(cells) == len(design["cutoff_heights"]) * 3
    # The three later cutoffs cannot carry H_long=105120 inside this prefix.  That
    # is a recorded structural unavailability, never a reason to reselect H or W.
    assert {
        (cell["cutoff_height"], cell["horizon_blocks"])
        for cell in cells
        if not cell["available"]
    } == {(199584, 105120), (215712, 105120), (225792, 105120)}
    primary = design["primary_horizon_blocks"]
    assert all(cell["available"] for cell in cells if cell["horizon_blocks"] == primary)
    windows = build_windows(design)
    assert [window["cutoff_height"] for window in windows] == design["cutoff_heights"]
    assert all(w["win_start_height"] >= 0 for w in windows)

    anchor = bytes.fromhex("11" * 32)
    member = bytes.fromhex("22" * 32)
    other = bytes.fromhex("33" * 32)
    assert common_input_star([other, member, anchor, member]) == [
        (anchor, member, [1, 3]),
        (anchor, other, [0]),
    ]
    assert common_input_star([anchor, anchor]) == []
    assert encode_script_ids([member, anchor, member]) == anchor + member
    assert decode_script_ids(anchor + member) == [anchor, member]

    event_id = compute_event_id(
        EXPECTED_SOURCE_MANIFEST_SHA256,
        bytes.fromhex("aa" * 32),
        7,
        bytes.fromhex("bb" * 32),
        1,
        0,
        anchor,
        member,
        HEURISTIC_VERSION,
    )
    assert len(event_id) == 32
    assert event_id != compute_event_id(
        EXPECTED_SOURCE_MANIFEST_SHA256,
        bytes.fromhex("aa" * 32),
        7,
        bytes.fromhex("bb" * 32),
        1,
        1,
        anchor,
        member,
        HEURISTIC_VERSION,
    )

    connection = sqlite3.connect(":memory:")
    semantics.create_state_schema(connection)
    create_s0_schema(connection)
    assert "union_event_records" in {
        row[0]
        for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'view'")
    }
    connection.close()

    print(
        json.dumps(
            {
                "self_test": "passed",
                "network": "not_used",
                "target_height": target,
                "unavailable_cells": sorted(
                    f"t{c}-h{h}"
                    for c, h in {
                        (cell["cutoff_height"], cell["horizon_blocks"])
                        for cell in cells
                        if not cell["available"]
                    }
                ),
                "effect_metrics_read": False,
                "s0_decision": None,
                "models_authorized": False,
            },
            sort_keys=True,
        )
    )


def main() -> int:
    args = parser().parse_args()
    if args.self_test:
        self_test()
        return 0

    required = {
        "--transaction-cache-dir": args.transaction_cache_dir,
        "--block-cache-dir": args.block_cache_dir,
        "--state-db": args.state_db,
        "--output": args.output,
    }
    missing = [flag for flag, value in required.items() if not value]
    if missing:
        raise ValueError(f"missing required arguments: {missing}")

    repo_root = Path(__file__).resolve().parents[2]
    manifest_path = Path(args.source_manifest)
    if not manifest_path.is_absolute():
        manifest_path = repo_root / manifest_path
    manifest_bytes, manifest = validate_source_manifest(manifest_path)
    source_manifest_sha256 = hashlib.sha256(manifest_bytes).hexdigest()
    frozen_artifacts = validate_frozen_artifacts(manifest, repo_root)
    artifacts_by_role = {artifact["role"]: artifact for artifact in frozen_artifacts}
    required_roles = {
        "selected object listing",
        "transaction byte freeze",
        "transaction schema audit",
        "main-chain block preflight",
    }
    if not required_roles <= set(artifacts_by_role):
        raise ValueError(
            f"source manifest lacks runner artifacts: {sorted(required_roles - set(artifacts_by_role))}"
        )
    reference_code = validate_reference_code(manifest, repo_root)
    semantic_qualification = validate_semantic_qualification(manifest)
    design = s0_design(manifest)
    target_height = compute_target_height(design, manifest["scope"])
    cells = horizon_cells(design, int(manifest["scope"]["last_height"]))
    windows = build_windows(design)

    listing_record = artifacts_by_role["selected object listing"]
    preflight_record = artifacts_by_role["main-chain block preflight"]
    listing_path = repo_root / listing_record["path"]
    freeze_path = repo_root / artifacts_by_role["transaction byte freeze"]["path"]
    schema_path = repo_root / artifacts_by_role["transaction schema audit"]["path"]
    preflight_path = repo_root / preflight_record["path"]
    expected_listing_sha256 = listing_record["sha256"]
    expected_preflight_sha256 = preflight_record["sha256"]
    transaction_cache_dir = Path(args.transaction_cache_dir).resolve()
    block_cache_dir = Path(args.block_cache_dir).resolve()
    state_db = Path(args.state_db).resolve()
    output = Path(args.output)
    if output.exists():
        raise FileExistsError(f"refusing to overwrite existing file: {output}")
    source.preflight_output_parent(output)
    source.preflight_output_parent(state_db)
    reserve_bytes = args.reserve_gib * source.GIB
    free_before = shutil.disk_usage(state_db.parent).free
    if free_before < reserve_bytes:
        raise semantics.SpaceStop(
            f"free space below {args.reserve_gib} GiB reserve before S0 extraction"
        )

    (
        listing_bytes,
        listing,
        items,
        freeze_bytes,
        freeze,
        schema_bytes,
        schema,
    ) = semantics.verify_freeze_and_schema(
        listing_path, expected_listing_sha256, freeze_path, schema_path
    )
    transaction_dates = {source.parse_partition_date(str(item["key"])) for item in items}
    by_height, block_info = semantics.load_block_map(
        listing,
        expected_listing_sha256,
        preflight_path,
        expected_preflight_sha256,
        block_cache_dir,
        transaction_dates,
    )
    if int(block_info["candidate_hmax"]) < target_height:
        raise RuntimeError(
            "candidate prefix cannot cover the required S0 target height: "
            f"{block_info['candidate_hmax']} < {target_height}"
        )
    if schema.get("row_count") != block_info["expected_transactions"]:
        raise RuntimeError(
            "schema row count differs from candidate block transaction total: "
            f"{schema.get('row_count')} != {block_info['expected_transactions']}"
        )
    schema_by_key = semantics.verify_transaction_files(
        items, freeze, schema, transaction_cache_dir
    )

    bindings = {
        "listing_sha256": hashlib.sha256(listing_bytes).hexdigest(),
        "transaction_freeze_sha256": hashlib.sha256(freeze_bytes).hexdigest(),
        "schema_audit_sha256": hashlib.sha256(schema_bytes).hexdigest(),
        "block_preflight_sha256": hashlib.sha256(block_info["preflight_bytes"]).hexdigest(),
        "script_sha256": semantics.script_sha256(),
        "candidate_hmax": block_info["candidate_hmax"],
    }
    s0_bindings = {
        "source_manifest_sha256": source_manifest_sha256,
        "runner_sha256": script_sha256(),
        "reference_code": reference_code,
        "semantic_qualification": semantic_qualification,
        "target_height": target_height,
        "design": design,
    }
    invocation_started = dt.datetime.now(dt.timezone.utc).isoformat()
    connection, committed_height, counters, s0_counters = open_s0_state(
        state_db, bindings, invocation_started, s0_bindings
    )
    try:
        if committed_height < -1 or committed_height > target_height:
            raise RuntimeError("S0 committed height is outside the required prefix")
        semantics.validate_checkpoint_state(
            connection, committed_height, counters, by_height
        )
        validate_s0_checkpoint(connection, committed_height, counters, s0_counters)
        final_height = replay_s0(
            connection,
            items,
            schema_by_key,
            transaction_cache_dir,
            by_height,
            target_height,
            committed_height,
            counters,
            s0_counters,
            windows,
            source_manifest_sha256,
            args.batch_size,
            args.checkpoint_blocks,
            reserve_bytes,
            state_db,
            args.pause_after_height,
        )
        if connection.execute("PRAGMA quick_check").fetchone()[0] != "ok":
            raise RuntimeError("final S0 state database quick_check failed")
        validate_s0_checkpoint(connection, final_height, counters, s0_counters)
        semantics.validate_bip30_complete(connection, counters)
        result = {
            "schema_version": S0_SCHEMA_VERSION,
            "status": "s0_union_extraction_complete",
            "s0_extraction_complete": True,
            "s0_decision": None,
            "effect_metrics_read": False,
            "labels_read": False,
            "models_authorized": False,
            "public_redistribution_authorized": False,
            "target_height": target_height,
            "last_complete_height": final_height,
            "target_block_hash": str(by_height[final_height]["hash"]),
            "source_manifest_sha256": source_manifest_sha256,
            "runner_sha256": s0_bindings["runner_sha256"],
            "reference_code": reference_code,
            "semantic_qualification": semantic_qualification,
            "frozen_artifacts": frozen_artifacts,
            "design": design,
            "horizon_cells": cells,
            "windows": windows,
            "transaction_counters": counters,
            "s0_counters": s0_counters,
            "state_database": {
                "path": str(state_db),
                "sizes": semantics.state_size(state_db),
                "quick_check": "ok",
            },
            "runtime": {
                "python_implementation": platform.python_implementation(),
                "python_version": platform.python_version(),
                "pyarrow_version": __import__("pyarrow").__version__,
                "sqlite_version": sqlite3.sqlite_version,
                "platform": platform.platform(),
                "batch_size": args.batch_size,
                "checkpoint_blocks": args.checkpoint_blocks,
                "reserve_gib": args.reserve_gib,
                "free_bytes_before": free_before,
                "free_bytes_after": shutil.disk_usage(state_db.parent).free,
                "argv": sys.argv[1:],
            },
            "limitations": [
                "This extracts label-free S0 union and window structure only.",
                "p_merge, p_rewrite and all bootstrap outputs remain uncomputed.",
                "No labels, entity types, aliases, model outputs or effect metrics were read.",
                "Gate 3A v1.1 S0 Go/No-Go requires a separate frozen evaluation run.",
            ],
        }
        source.atomic_write_new(output, source.canonical_json(result))
        print(
            json.dumps(
                {
                    "status": result["status"],
                    "output": str(output),
                    "target_height": target_height,
                    "union_events": s0_counters["union_events"],
                    "s0_extraction_complete": True,
                    "effect_metrics_read": False,
                    "s0_decision": None,
                },
                sort_keys=True,
            )
        )
        return 0
    finally:
        connection.close()


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except semantics.SpaceStop as error:
        print(
            json.dumps(
                {
                    "status": "resumable_space_stop",
                    "error": str(error),
                    "effect_metrics_read": False,
                    "s0_decision": None,
                },
                sort_keys=True,
            ),
            file=sys.stderr,
        )
        raise SystemExit(3)
    except semantics.OperatorPause as error:
        print(
            json.dumps(
                {
                    "status": "resumable_operator_pause",
                    "error": str(error),
                    "effect_metrics_read": False,
                    "s0_decision": None,
                },
                sort_keys=True,
            ),
            file=sys.stderr,
        )
        raise SystemExit(4)
