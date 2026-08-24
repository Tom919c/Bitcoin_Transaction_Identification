"""Run the frozen N1-A1 synthetic correctness pilot."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from dataclasses import asdict
from pathlib import Path
from statistics import median

from btcaml.analysis.flow_certificate import (
    CERTIFIED_FALSE,
    CERTIFIED_TRUE,
    UNRESOLVED,
    FlowCertificate,
    Transaction,
)

TARGETS = tuple(f"D{i}" for i in range(6))
FAMILIES = ("unique", "mixed", "symmetric")
MAX_ORACLE_COMPLETIONS = 2_000_000


def hashed_int(family: str, index: int, field: str, slot: int, modulus: int) -> int:
    payload = f"N1-A1-v1|{family}|{index:02d}|{field}|{slot}".encode()
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big") % modulus


def split_value(
    total: int, parts: int, minimum: int, family: str, index: int, field: str
) -> tuple[int, ...]:
    remaining = total - parts * minimum
    if remaining < 0:
        raise ValueError("split minimum exceeds total")
    weights = [1 + hashed_int(family, index, f"{field}:weight", j, 17) for j in range(parts)]
    weight_sum = sum(weights)
    values = [minimum + remaining * weight // weight_sum for weight in weights]
    residue = total - sum(values)
    order = sorted(
        range(parts),
        key=lambda j: hashed_int(family, index, f"{field}:remainder", j, 2**64),
    )
    for j in order[:residue]:
        values[j] += 1
    return tuple(values)


def build_instance(family: str, index: int) -> tuple[str, tuple[Transaction, ...], dict[str, int]]:
    instance_id = f"{family}-{index:02d}"

    def name(value: str) -> str:
        return f"{instance_id}:{value}"

    if family == "unique":
        source = 36 + hashed_int(family, index, "source", 0, 10)
        extra = sorted(split_value(source - 27, 6, 0, family, index, "targets"))
        targets = tuple(2 + j + extra[j] for j in range(6))
        roots = tuple(targets[2 * j] + targets[2 * j + 1] for j in range(3))
        transactions = (
            Transaction(
                name("T0"),
                ((name("S"), source),),
                tuple((name(f"A{j}"), roots[j]) for j in range(3)),
            ),
            *(
                Transaction(
                    name(f"T{j + 1}"),
                    ((name(f"A{j}"), roots[j]),),
                    (
                        (name(f"D{2 * j}"), targets[2 * j]),
                        (name(f"D{2 * j + 1}"), targets[2 * j + 1]),
                    ),
                )
                for j in range(3)
            ),
        )
    elif family == "mixed":
        source = 9 + hashed_int(family, index, "source", 0, 7)
        clean_root = 8 + hashed_int(family, index, "clean-root", 0, 9)
        root_fee = hashed_int(family, index, "root-fee", 0, 2)
        roots = split_value(
            source + clean_root - root_fee, 3, 2, family, index, "roots"
        )
        children: list[Transaction] = []
        for j, root in enumerate(roots):
            clean = 2 + hashed_int(family, index, "clean-child", j, 7)
            fee = hashed_int(family, index, "child-fee", j, 2)
            outputs = split_value(root + clean - fee, 2, 1, family, index, f"child-{j}")
            children.append(
                Transaction(
                    name(f"T{j + 1}"),
                    ((name(f"A{j}"), root), (name(f"N{j + 1}"), clean)),
                    (
                        (name(f"D{2 * j}"), outputs[0]),
                        (name(f"D{2 * j + 1}"), outputs[1]),
                    ),
                    fee,
                )
            )
        transactions = (
            Transaction(
                name("T0"),
                ((name("S"), source), (name("N0"), clean_root)),
                tuple((name(f"A{j}"), roots[j]) for j in range(3)),
                root_fee,
            ),
            *children,
        )
    elif family == "symmetric":
        unit = 3 + hashed_int(family, index, "unit", 0, 3)
        source = 3 * unit
        roots = (2 * unit,) * 3
        transactions = (
            Transaction(
                name("T0"),
                ((name("S"), source), (name("N0"), source)),
                tuple((name(f"A{j}"), roots[j]) for j in range(3)),
            ),
            *(
                Transaction(
                    name(f"T{j + 1}"),
                    ((name(f"A{j}"), roots[j]), (name(f"N{j + 1}"), roots[j])),
                    (
                        (name(f"D{2 * j}"), roots[j]),
                        (name(f"D{2 * j + 1}"), roots[j]),
                    ),
                )
                for j in range(3)
            ),
        )
    else:
        raise ValueError(f"unknown family: {family}")

    return instance_id, transactions, {name("S"): source}


def bounded_compositions(total: int, capacities: tuple[int, ...]):
    if len(capacities) == 1:
        if 0 <= total <= capacities[0]:
            yield (total,)
        return
    lower = max(0, total - sum(capacities[1:]))
    for value in range(lower, min(total, capacities[0]) + 1):
        for tail in bounded_compositions(total - value, capacities[1:]):
            yield (value, *tail)


def validate_oracle_input(
    transactions: tuple[Transaction, ...], seeds: dict[str, int], targets: tuple[str, ...]
) -> None:
    if len(seeds) != 1 or len(targets) != 6 or len(set(targets)) != 6:
        raise AssertionError("A1 requires one source and six distinct targets")
    producers: dict[str, int] = {}
    values: dict[str, int] = {}
    spent: set[str] = set()
    txids: set[str] = set()
    for index, tx in enumerate(transactions):
        if not tx.txid or tx.txid in txids or not tx.inputs or tx.fee_sats < 0:
            raise AssertionError(f"invalid transaction envelope: {tx.txid!r}")
        txids.add(tx.txid)
        for outpoint, value in tx.outputs:
            if not outpoint or value <= 0 or outpoint in producers:
                raise AssertionError(f"invalid or duplicate output: {outpoint!r}")
            producers[outpoint] = index
            values[outpoint] = value

    for index, tx in enumerate(transactions):
        input_total = 0
        for outpoint, value in tx.inputs:
            if not outpoint or value <= 0 or outpoint in spent:
                raise AssertionError(f"invalid or repeated input: {outpoint!r}")
            spent.add(outpoint)
            input_total += value
            if outpoint in producers:
                if producers[outpoint] >= index or values[outpoint] != value:
                    raise AssertionError(f"non-causal or mismatched input: {outpoint}")
            elif outpoint in values and values[outpoint] != value:
                raise AssertionError(f"inconsistent boundary input: {outpoint}")
            else:
                values[outpoint] = value
        if input_total != sum(value for _, value in tx.outputs) + tx.fee_sats:
            raise AssertionError(f"value is not conserved in {tx.txid}")

    for outpoint, value in seeds.items():
        if outpoint in producers or values.get(outpoint) != value or value <= 0:
            raise AssertionError(f"invalid source boundary: {outpoint}")
    if any(target not in producers or target in spent for target in targets):
        raise AssertionError("targets must be produced, terminal UTXOs")


def exact_oracle(
    transactions: tuple[Transaction, ...], seeds: dict[str, int], targets: tuple[str, ...]
) -> dict[str, object]:
    validate_oracle_input(transactions, seeds, targets)
    target_min = {target: None for target in targets}
    target_max = {target: None for target in targets}
    pairs = {(left, right): [None, None] for left in targets for right in targets if left != right}
    completions = 0

    def visit(index: int, masses: dict[str, int]) -> None:
        nonlocal completions
        if index == len(transactions):
            if completions >= MAX_ORACLE_COMPLETIONS:
                raise RuntimeError("oracle completion guard reached; no partial result is valid")
            completions += 1
            for target in targets:
                value = masses[target]
                current_min, current_max = target_min[target], target_max[target]
                target_min[target] = value if current_min is None else min(current_min, value)
                target_max[target] = value if current_max is None else max(current_max, value)
            for (left, right), bounds in pairs.items():
                difference = masses[left] - masses[right]
                bounds[0] = difference if bounds[0] is None else min(bounds[0], difference)
                bounds[1] = difference if bounds[1] is None else max(bounds[1], difference)
            return

        tx = transactions[index]
        source_total = sum(masses.get(outpoint, 0) for outpoint, _ in tx.inputs)
        capacities = tuple(value for _, value in tx.outputs) + (tx.fee_sats,)
        for allocation in bounded_compositions(source_total, capacities):
            updated = masses.copy()
            for (outpoint, _), value in zip(tx.outputs, allocation[:-1], strict=True):
                updated[outpoint] = value
            visit(index + 1, updated)

    visit(0, dict(seeds))
    if not completions:
        raise AssertionError("oracle found no compatible completion")
    return {
        "completions": completions,
        "intervals": {target: [target_min[target], target_max[target]] for target in targets},
        "pair_intervals": {f"{left}>{right}": bounds for (left, right), bounds in pairs.items()},
    }


def status_from_interval(lower: int, upper: int, threshold: int) -> str:
    if lower >= threshold:
        return CERTIFIED_TRUE
    if upper < threshold:
        return CERTIFIED_FALSE
    return UNRESOLVED


def canonical_instance(
    instance_id: str, transactions: tuple[Transaction, ...], seeds: dict[str, int]
) -> dict[str, object]:
    return {
        "instance_id": instance_id,
        "seeds": seeds,
        "transactions": [asdict(tx) for tx in transactions],
    }


def evaluate_instance(family: str, index: int) -> tuple[dict[str, object], dict[str, object]]:
    instance_id, transactions, seeds = build_instance(family, index)
    prefix = f"{instance_id}:"
    targets = tuple(prefix + target for target in TARGETS)
    oracle = exact_oracle(transactions, seeds, targets)
    candidate = FlowCertificate(transactions, seeds)
    source_value = next(iter(seeds.values()))
    threshold = (source_value + 99) // 100
    target_values = {
        outpoint: value
        for tx in transactions
        for outpoint, value in tx.outputs
        if outpoint in targets
    }

    intervals: dict[str, list[int]] = {}
    statuses: dict[str, str] = {}
    widths: list[float] = []
    for target in targets:
        short = target.removeprefix(prefix)
        interval = candidate.interval(target)
        expected = tuple(oracle["intervals"][target])
        if interval != expected:
            raise AssertionError(f"{instance_id} interval mismatch for {short}: {interval} != {expected}")
        for test_threshold in range(source_value + 1):
            actual_status = candidate.threshold_status(target, test_threshold)
            expected_status = status_from_interval(*expected, test_threshold)
            if actual_status != expected_status:
                raise AssertionError(
                    f"{instance_id} threshold mismatch for {short} at {test_threshold}"
                )
        intervals[short] = list(interval)
        statuses[short] = candidate.threshold_status(target, threshold)
        widths.append((interval[1] - interval[0]) / min(source_value, target_values[target]))

    certified_pairs = 0
    for left in targets:
        for right in targets:
            if left == right:
                continue
            actual = candidate.difference_interval(left, right)
            expected = tuple(oracle["pair_intervals"][f"{left}>{right}"])
            if actual != expected:
                raise AssertionError(f"{instance_id} pair mismatch: {left}, {right}")
            certified_pairs += candidate.strict_order_status(left, right) != UNRESOLVED

    certified_targets = sum(status != UNRESOLVED for status in statuses.values())
    if family == "unique" and any(lower != upper for lower, upper in intervals.values()):
        raise AssertionError(f"{instance_id} unique-family point interval invariant failed")
    if family == "symmetric" and (certified_targets or certified_pairs):
        raise AssertionError(f"{instance_id} symmetric-family abstention invariant failed")

    instance = canonical_instance(instance_id, transactions, seeds)
    result = {
        "instance_id": instance_id,
        "family": family,
        "source_value": source_value,
        "threshold": threshold,
        "oracle_completions": oracle["completions"],
        "intervals": intervals,
        "threshold_statuses": statuses,
        "threshold_cdr": certified_targets / len(targets),
        "pair_cdr": certified_pairs / 30,
        "median_normalized_width": median(widths),
        "strict_top3": "not_implemented",
    }
    return instance, result


def git_revision() -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"], check=True, capture_output=True, text=True
    ).stdout.strip()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("docs/研究/重新选题/n1-a1-synthetic-results.json"),
    )
    args = parser.parse_args()

    print("A1 tests exact certificate correctness and abstention; it does not estimate Bitcoin utility.")
    instances: list[dict[str, object]] = []
    results: list[dict[str, object]] = []
    for family in FAMILIES:
        for index in range(16):
            instance, result = evaluate_instance(family, index)
            instances.append(instance)
            results.append(result)

    suite_bytes = json.dumps(instances, sort_keys=True, separators=(",", ":")).encode()
    family_summary = {
        family: {
            "instances": 16,
            "median_threshold_cdr": median(
                result["threshold_cdr"] for result in results if result["family"] == family
            ),
            "median_pair_cdr": median(
                result["pair_cdr"] for result in results if result["family"] == family
            ),
            "median_normalized_width": median(
                result["median_normalized_width"]
                for result in results
                if result["family"] == family
            ),
        }
        for family in FAMILIES
    }
    payload = {
        "protocol": "N1-A1-v1",
        "protocol_document": "n1-flow-certificate-pilot.md v0.2",
        "code_revision": git_revision(),
        "suite_sha256": hashlib.sha256(suite_bytes).hexdigest(),
        "instances": results,
        "family_summary": family_summary,
        "oracle_mismatches": 0,
        "gate": "A1_PASS_CORRECTNESS_ONLY",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(family_summary, indent=2))
    print(f"suite_sha256={payload['suite_sha256']}")
    print(f"wrote {args.output}")


if __name__ == "__main__":
    main()
