"""Scan a fixed Bitcoin block range for outputs with an exact satoshi value."""

from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


def fetch(url: str, attempts: int = 5) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "bitcoin-research-pilot/1.0"})
    for attempt in range(attempts):
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                return response.read()
        except (urllib.error.URLError, TimeoutError):
            if attempt + 1 == attempts:
                raise
            time.sleep(2**attempt)
    raise AssertionError("unreachable")


def extract_matches(block: dict, target_sats: int) -> list[dict]:
    matches = []
    for tx in block["tx"]:
        for output in tx["out"]:
            if output["value"] == target_sats:
                matches.append(
                    {
                        "txid": tx["hash"],
                        "vout": output["n"],
                        "value_sats": output["value"],
                        "address": output.get("addr"),
                        "script_hex": output.get("script"),
                    }
                )
    return matches


def scan_height(height: int, target_sats: int, start_ts: int, end_ts: int) -> dict:
    url = f"https://blockchain.info/rawblock/{height}"
    raw = fetch(url)
    block = json.loads(raw)
    if block["height"] != height:
        raise ValueError(f"height mismatch: requested {height}, received {block['height']}")
    if not start_ts <= block["time"] < end_ts:
        raise ValueError(f"block {height} timestamp {block['time']} is outside the frozen UTC day")
    output_count = sum(len(tx["out"]) for tx in block["tx"])
    return {
        "height": height,
        "block_hash": block["hash"],
        "block_time": datetime.fromtimestamp(block["time"], timezone.utc).isoformat(),
        "source_url": url,
        "response_sha256": hashlib.sha256(raw).hexdigest(),
        "transaction_count": len(block["tx"]),
        "output_count": output_count,
        "matches": extract_matches(block, target_sats),
    }


def verify_match(match: dict) -> dict:
    url = f"https://mempool.space/api/tx/{match['txid']}"
    raw = fetch(url)
    tx = json.loads(raw)
    output = tx["vout"][match["vout"]]
    return {
        "source_url": url,
        "response_sha256": hashlib.sha256(raw).hexdigest(),
        "value_sats": output["value"],
        "scriptpubkey": output["scriptpubkey"],
        "scriptpubkey_type": output["scriptpubkey_type"],
        "scriptpubkey_address": output.get("scriptpubkey_address"),
        "confirmed": tx["status"]["confirmed"],
        "block_height": tx["status"].get("block_height"),
        "block_hash": tx["status"].get("block_hash"),
        "block_time": tx["status"].get("block_time"),
    }


def self_test() -> None:
    block = {
        "tx": [
            {"hash": "a", "out": [{"n": 0, "value": 4}, {"n": 1, "value": 5}]},
            {"hash": "b", "out": [{"n": 0, "value": 4, "addr": "x", "script": "00"}]},
        ]
    }
    assert extract_matches(block, 4) == [
        {"txid": "a", "vout": 0, "value_sats": 4, "address": None, "script_hex": None},
        {"txid": "b", "vout": 0, "value_sats": 4, "address": "x", "script_hex": "00"},
    ]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", default="2023-04-04")
    parser.add_argument("--target-sats", type=int, default=4_931_202_270)
    parser.add_argument("--start-height", type=int, default=783_816)
    parser.add_argument("--end-height", type=int, default=783_977)
    parser.add_argument("--workers", type=int, default=3)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    self_test()
    if args.self_test:
        return

    start = datetime.fromisoformat(args.date).replace(tzinfo=timezone.utc)
    start_ts = int(start.timestamp())
    end_ts = start_ts + 86_400
    args.output.parent.mkdir(parents=True, exist_ok=True)

    records = []
    heights = range(args.start_height, args.end_height + 1)
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {
            pool.submit(scan_height, height, args.target_sats, start_ts, end_ts): height
            for height in heights
        }
        for future in concurrent.futures.as_completed(futures):
            record = future.result()
            records.append(record)
            print(
                json.dumps(
                    {
                        "height": record["height"],
                        "outputs": record["output_count"],
                        "matches": len(record["matches"]),
                    }
                ),
                flush=True,
            )

    records.sort(key=lambda row: row["height"])
    matches = []
    for record in records:
        for match in record["matches"]:
            enriched = {"height": record["height"], "block_hash": record["block_hash"], **match}
            enriched["independent_verification"] = verify_match(match)
            matches.append(enriched)

    result = {
        "protocol": {
            "date_utc": args.date,
            "target_sats": args.target_sats,
            "start_height": args.start_height,
            "end_height": args.end_height,
            "matching_rule": "exact equality on every transaction output value; no tolerance or heuristic",
        },
        "summary": {
            "blocks_scanned": len(records),
            "transactions_scanned": sum(row["transaction_count"] for row in records),
            "outputs_scanned": sum(row["output_count"] for row in records),
            "match_count": len(matches),
        },
        "matches": matches,
        "block_manifest": records,
    }
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
