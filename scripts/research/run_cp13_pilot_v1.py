"""Run the frozen CP-13 Tier-0/Tier-1 block sample."""

from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import sys
import time
import urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.research.scan_exact_bitcoin_outputs import fetch
from scripts.scan_block_sighash import scan_block


STRATA = {
    "control": [722970, 727123, 732002, 738810, 741953, 750002],
    "early_marketplace": [789561, 815344, 820955, 824355, 827471, 830004],
    "post_runes": [847310, 848410, 848594, 877986, 887012, 888771],
    "recent": [901077, 902343, 918143, 918573, 939796, 943404],
}


def classify_tier1(candidate: dict, transaction: dict) -> list[dict]:
    if transaction.get("txid") != candidate["txid"]:
        raise ValueError(f"txid mismatch: {candidate['txid']}")
    inputs = transaction["vin"]
    outputs = transaction["vout"]
    input_scripts = {
        row["prevout"]["scriptpubkey"] for row in inputs if row.get("prevout") is not None
    }
    matches = []
    for signature in candidate["matches"]:
        index = signature["input_index"]
        if index >= len(inputs) or index >= len(outputs) or inputs[index].get("prevout") is None:
            continue
        previous = inputs[index]["prevout"]
        output = outputs[index]
        previous_script = previous["scriptpubkey"]
        if (
            output["scriptpubkey"] == previous_script
            and output["value"] > previous["value"]
            and any(script != previous_script for script in input_scripts)
        ):
            matches.append(
                {
                    "input_index": index,
                    "signature_kind": signature["signature_kind"],
                    "prevout_value": previous["value"],
                    "output_value": output["value"],
                    "scriptpubkey": previous_script,
                    "distinct_input_scripts": len(input_scripts),
                }
            )
    return matches


def public_filter_structure(transaction: dict) -> dict:
    input_scripts = [
        row["prevout"]["scriptpubkey"]
        for row in transaction["vin"]
        if row.get("prevout") is not None
    ]
    output_scripts = [row["scriptpubkey"] for row in transaction["vout"]]
    repeated_output_script = len(set(output_scripts)) < len(output_scripts)
    return {
        "distinct_input_scripts": len(set(input_scripts)),
        "distinct_output_scripts": len(set(output_scripts)),
        "all_output_scripts_distinct": not repeated_output_script,
        "schnoering_protocol_rules_guaranteed_miss": repeated_output_script,
    }


def msigner_default_template(transaction: dict, tier1_matches: list[dict]) -> bool:
    inputs = transaction["vin"]
    outputs = transaction["vout"]
    if (
        not any(row["input_index"] == 2 for row in tier1_matches)
        or len(inputs) < 4
        or len(outputs) < 6
        or any(inputs[index].get("prevout") is None for index in (0, 1))
    ):
        return False
    first, second = inputs[0]["prevout"], inputs[1]["prevout"]
    buyer_script = first["scriptpubkey"]
    return (
        first["scriptpubkey"] == second["scriptpubkey"]
        and 580 <= first["value"] <= 1000
        and 580 <= second["value"] <= 1000
        and outputs[0]["scriptpubkey"] == buyer_script
        and outputs[0]["value"] >= first["value"] + second["value"]
        and outputs[4]["scriptpubkey"] == buyer_script
        and outputs[4]["value"] == 600
        and outputs[5]["scriptpubkey"] == buyer_script
        and outputs[5]["value"] == 600
    )


def load_transaction(txid: str, cache_dir: Path, api_base: str) -> tuple[dict, str, str]:
    target = cache_dir / f"{txid}.json"
    if "blockchain.info" in api_base:
        url = f"{api_base.rstrip('/')}/rawtx/{txid}?format=json"
    else:
        url = f"{api_base.rstrip('/')}/tx/{txid}"
    raw = target.read_bytes() if target.exists() else fetch(url)
    if not target.exists():
        target.write_bytes(raw)
    transaction = json.loads(raw)
    if "txid" not in transaction:
        transaction = {
            "txid": transaction["hash"],
            "vin": [
                {
                    "prevout": {
                        "scriptpubkey": row["prev_out"]["script"],
                        "value": row["prev_out"]["value"],
                    }
                    if row.get("prev_out") is not None
                    else None
                }
                for row in transaction["inputs"]
            ],
            "vout": [
                {"scriptpubkey": row["script"], "value": row["value"]}
                for row in transaction["out"]
            ],
        }
    return transaction, url, hashlib.sha256(raw).hexdigest()


def load_inscription_transfer_txids(
    height: int, cache_dir: Path, api_base: str
) -> tuple[set[str], dict]:
    target = cache_dir / f"{height}.json"
    if target.exists():
        record = json.loads(target.read_bytes())
    else:
        results = []
        sources = []
        cursor = None
        while True:
            query = {"blockHeight": height, "kind": "transfer", "limit": 60}
            if cursor:
                query["cursor"] = cursor
            url = f"{api_base.rstrip('/')}?{urllib.parse.urlencode(query)}"
            raw = fetch(url)
            page = json.loads(raw)
            results.extend(page["results"])
            sources.append({"url": url, "sha256": hashlib.sha256(raw).hexdigest()})
            cursor = page.get("nextCursor")
            if not cursor:
                break
            time.sleep(2.1)
        if any(row["blockHeight"] != height for row in results):
            raise ValueError(f"Magic Eden activity height mismatch: {height}")
        record = {"height": height, "results": results, "sources": sources}
        target.write_text(json.dumps(record) + "\n", encoding="utf-8")
    return {row["txId"] for row in record["results"]}, {
        "height": height,
        "activity_count": len(record["results"]),
        "unique_transaction_count": len({row["txId"] for row in record["results"]}),
        "sources": record["sources"],
    }


def self_test() -> None:
    candidate = {
        "txid": "a",
        "matches": [{"input_index": 1, "signature_kind": "schnorr"}],
    }
    transaction = {
        "txid": "a",
        "vin": [
            {"prevout": {"scriptpubkey": "buyer", "value": 20}},
            {"prevout": {"scriptpubkey": "seller", "value": 5}},
        ],
        "vout": [
            {"scriptpubkey": "buyer", "value": 10},
            {"scriptpubkey": "seller", "value": 12},
        ],
    }
    assert classify_tier1(candidate, transaction)[0]["output_value"] == 12
    assert public_filter_structure(transaction)[
        "schnoering_protocol_rules_guaranteed_miss"
    ] is False
    transaction["vout"][1]["scriptpubkey"] = "other"
    assert classify_tier1(candidate, transaction) == []
    template_tx = {
        "vin": [
            {"prevout": {"scriptpubkey": "buyer", "value": 600}},
            {"prevout": {"scriptpubkey": "buyer", "value": 600}},
            {"prevout": {"scriptpubkey": "seller", "value": 546}},
            {"prevout": {"scriptpubkey": "buyer", "value": 10_000}},
        ],
        "vout": [
            {"scriptpubkey": "buyer", "value": 1200},
            {"scriptpubkey": "receiver", "value": 546},
            {"scriptpubkey": "seller", "value": 20_000},
            {"scriptpubkey": "fee", "value": 1000},
            {"scriptpubkey": "buyer", "value": 600},
            {"scriptpubkey": "buyer", "value": 600},
        ],
    }
    assert msigner_default_template(template_tx, [{"input_index": 2}])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--block-dir", type=Path, required=True)
    parser.add_argument("--cache-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--api-base", default="https://blockstream.info/api")
    parser.add_argument("--activity-cache-dir", type=Path)
    parser.add_argument(
        "--activity-api-base",
        default="https://api-mainnet.magiceden.dev/v2/ord/btc/block/activities",
    )
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    self_test()
    if args.self_test:
        return
    if not 1 <= args.workers <= 8:
        parser.error("--workers must be between 1 and 8")

    args.cache_dir.mkdir(parents=True, exist_ok=True)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    stratum_by_height = {
        height: stratum for stratum, heights in STRATA.items() for height in heights
    }
    block_records = []
    candidates = []
    for height in sorted(stratum_by_height):
        path = args.block_dir / f"{height}.raw"
        if not path.is_file():
            raise FileNotFoundError(path)
        raw_block = path.read_bytes()
        result = scan_block(raw_block)
        block_records.append(
            {
                "height": height,
                "stratum": stratum_by_height[height],
                "transaction_count": result["transaction_count"],
                "tier0_count": result["candidate_transaction_count"],
                "raw_block_sha256": hashlib.sha256(raw_block).hexdigest(),
            }
        )
        for candidate in result["candidates"]:
            candidates.append(
                {"height": height, "stratum": stratum_by_height[height], **candidate}
            )

    def enrich(candidate: dict) -> dict:
        transaction, url, digest = load_transaction(
            candidate["txid"], args.cache_dir, args.api_base
        )
        tier1_matches = classify_tier1(candidate, transaction)
        return {
            **candidate,
            "source_url": url,
            "response_sha256": digest,
            "tier1": bool(tier1_matches),
            "tier1_matches": tier1_matches,
            "public_filter_structure": public_filter_structure(transaction),
            "msigner_default_template": msigner_default_template(
                transaction, tier1_matches
            ),
        }

    enriched = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(enrich, row): row["txid"] for row in candidates}
        for completed, future in enumerate(concurrent.futures.as_completed(futures), 1):
            enriched.append(future.result())
            if completed % 50 == 0 or completed == len(futures):
                print(f"enriched {completed}/{len(futures)}", flush=True)
    enriched.sort(key=lambda row: (row["height"], row["txid"]))

    activity_manifest = []
    if args.activity_cache_dir:
        args.activity_cache_dir.mkdir(parents=True, exist_ok=True)
        transfers_by_height = {}
        for height in sorted(stratum_by_height):
            if stratum_by_height[height] == "control":
                continue
            txids, record = load_inscription_transfer_txids(
                height, args.activity_cache_dir, args.activity_api_base
            )
            transfers_by_height[height] = txids
            activity_manifest.append(record)
        for row in enriched:
            row["magic_eden_indexed_inscription_transfer"] = row["txid"] in transfers_by_height.get(
                row["height"], set()
            )

    by_stratum = {}
    for stratum in STRATA:
        blocks = [row for row in block_records if row["stratum"] == stratum]
        rows = [row for row in enriched if row["stratum"] == stratum]
        by_stratum[stratum] = {
            "blocks": len(blocks),
            "transactions": sum(row["transaction_count"] for row in blocks),
            "tier0": len(rows),
            "tier1": sum(row["tier1"] for row in rows),
        }

    result = {
        "protocol": {
            "name": "CP-13 zero-model sample v1",
            "as_of_height": 947352,
            "excluded_smoke_height": 947353,
            "strata": STRATA,
            "transaction_api_base": args.api_base,
            "inscription_activity_api_base": (
                args.activity_api_base if args.activity_cache_dir else None
            ),
            "tier1_rule": (
                "explicit 0x83 input j; vout[j] exists; same prevout/output script; "
                "another input script exists; vout[j] value exceeds prevout value"
            ),
        },
        "summary": {
            "blocks": len(block_records),
            "transactions": sum(row["transaction_count"] for row in block_records),
            "tier0": len(enriched),
            "tier1": sum(row["tier1"] for row in enriched),
            "tier1_published_protocol_rules_guaranteed_miss": sum(
                row["tier1"]
                and row["public_filter_structure"][
                    "schnoering_protocol_rules_guaranteed_miss"
                ]
                for row in enriched
            ),
            "tier1_msigner_default_template_compatible": sum(
                row["tier1"] and row["msigner_default_template"] for row in enriched
            ),
            "tier1_with_indexed_inscription_transfer": (
                sum(
                    row["tier1"]
                    and row.get("magic_eden_indexed_inscription_transfer", False)
                    for row in enriched
                )
                if args.activity_cache_dir
                else None
            ),
            "by_stratum": by_stratum,
        },
        "blocks": block_records,
        "activity_manifest": activity_manifest,
        "candidates": enriched,
    }
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result["summary"], indent=2))


if __name__ == "__main__":
    main()
