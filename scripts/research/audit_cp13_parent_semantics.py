"""Bounded raw-prevout and direct-reveal audit; not a full Ordinals indexer."""

from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.research.scan_exact_bitcoin_outputs import fetch
from scripts.scan_block_sighash import parse_transaction, read_compact_size


def hash256(value: bytes) -> bytes:
    return hashlib.sha256(hashlib.sha256(value).digest()).digest()


def merkle_root(leaves: list[bytes]) -> bytes:
    if not leaves:
        raise ValueError("empty merkle tree")
    level = list(leaves)
    while len(level) > 1:
        if len(level) % 2:
            level.append(level[-1])
        level = [hash256(level[index] + level[index + 1]) for index in range(0, len(level), 2)]
    return level[0]


def check_witness_commitment(coinbase: dict, witness_root: bytes) -> str:
    stack = coinbase["witnesses"]
    if len(stack) != 1 or len(stack[0]) != 1 or len(bytes.fromhex(stack[0][0])) != 32:
        raise ValueError("invalid witness reserved value")
    commits = [bytes.fromhex(row["scriptpubkey"])[6:38] for row in coinbase["outputs"]
               if len(row["scriptpubkey"]) >= 76 and row["scriptpubkey"].startswith("6a24aa21a9ed")]
    computed = hash256(witness_root + bytes.fromhex(stack[0][0]))
    if not commits or computed != commits[-1]:
        raise ValueError("witness commitment mismatch")
    return computed.hex()


def verify_block(data: bytes, expected_hash: str, targets: dict[str, str]) -> dict:
    if len(data) < 81 or hash256(data[:80])[::-1].hex() != expected_hash:
        raise ValueError("block header hash mismatch")
    count, pos = read_compact_size(data, 80)
    txids, wtxids, found = [], [], []
    coinbase = None
    for index in range(count):
        start = pos
        transaction, pos = parse_transaction(data, pos, retain_witnesses=index == 0)
        txids.append(bytes.fromhex(transaction["txid"])[::-1])
        wtxid = bytes(32) if index == 0 else hash256(data[start:pos])
        wtxids.append(wtxid)
        if index == 0:
            coinbase = transaction
        if transaction["txid"] in targets:
            digest = hashlib.sha256(data[start:pos]).hexdigest()
            if digest != targets[transaction["txid"]]:
                raise ValueError("parent raw witness differs from committed block transaction")
            found.append({"txid": transaction["txid"], "transaction_index": index,
                          "wtxid": wtxid[::-1].hex(), "raw_sha256": digest})
    if pos != len(data) or merkle_root(txids) != data[36:68]:
        raise ValueError("block parsing or transaction merkle root mismatch")
    if {row["txid"] for row in found} != set(targets):
        raise ValueError("target transaction missing from block")
    root = merkle_root(wtxids)
    commitment = check_witness_commitment(coinbase, root)
    return {"block_hash": expected_hash, "transactions": count,
            "raw_block_sha256": hashlib.sha256(data).hexdigest(),
            "txid_merkle_root_matches_header": True, "witness_commitment_verified": True,
            "witness_root": root.hex(), "commitment": commitment, "targets": found}


def select_sample(candidates: list[dict]) -> list[dict]:
    selected = []
    for stratum in ("early_marketplace", "post_runes", "recent"):
        for compatible in (False, True):
            cell = [row for row in candidates if row["tier1"]
                    and row["stratum"] == stratum
                    and row["msigner_default_template"] == compatible]
            cell.sort(key=lambda row: hashlib.sha256(
                ("CP13-semantic-v1|" + row["txid"]).encode()).digest())
            selected.extend(cell[:2])
    return selected


def script_tokens(script: bytes) -> list[bytes | int]:
    tokens, pos = [], 0
    while pos < len(script):
        opcode = script[pos]
        pos += 1
        if opcode <= 78:
            if opcode <= 75:
                size = opcode
            else:
                width = {76: 1, 77: 2, 78: 4}[opcode]
                if pos + width > len(script):
                    raise ValueError("truncated push length")
                size = int.from_bytes(script[pos:pos + width], "little")
                pos += width
            if pos + size > len(script):
                raise ValueError("truncated push data")
            tokens.append(script[pos:pos + size])
            pos += size
        else:
            tokens.append(opcode)
    return tokens


def simple_reveal(transaction: dict) -> dict | None:
    if transaction["input_count"] != 1 or transaction["output_count"] != 1:
        return None
    stacks = transaction.get("witnesses", [])
    if len(stacks) != 1:
        return None
    items = [bytes.fromhex(item) for item in stacks[0]]
    if len(items) >= 2 and items[-1][:1] == b"\x50":
        items.pop()
    if len(items) != 3 or len(items[-1]) != 33 or items[-1][0] & 0xFE != 0xC0:
        return None
    tokens = script_tokens(items[-2])
    if (len(tokens) < 9 or not isinstance(tokens[0], bytes) or len(tokens[0]) != 32
            or tokens[1:5] != [0xAC, b"", 0x63, b"ord"] or tokens[-1] != 0x68):
        return None
    envelope = tokens[5:-1]
    if any(not isinstance(token, bytes) for token in envelope):
        return None
    # Only one content-type field and no pointer/other fields are supported.
    if len(envelope) < 3 or envelope[0] != b"\x01" or envelope[2] != b"":
        return None
    body = b"".join(envelope[3:])
    record = {"content_type": envelope[1].decode("ascii", errors="replace"),
              "body_length": len(body), "body_sha256": hashlib.sha256(body).hexdigest(),
              "sat_offset": 0, "scope": "single-input single-output simple envelope; no pointer"}
    if len(body) <= 2048:
        try:
            obj = json.loads(body)
            if isinstance(obj, dict) and obj.get("p") == "brc-20":
                record["brc20_declaration"] = {key: obj.get(key) for key in ("p", "op", "tick", "amt")}
        except (ValueError, UnicodeDecodeError):
            pass
    return record


def destination(outputs: list[dict], offset: int) -> int | None:
    if offset < 0:
        raise ValueError("negative sat offset")
    for index, output in enumerate(outputs):
        if offset < output["value"]:
            return index
        offset -= output["value"]
    return None


def self_test() -> None:
    leaves = [bytes([value]) * 32 for value in (1, 2, 3)]
    assert merkle_root(leaves) == hash256(hash256(leaves[0] + leaves[1]) + hash256(leaves[2] * 2))
    commitment = hash256(bytes(64)).hex()
    coinbase = {"witnesses": [[bytes(32).hex()]], "outputs": [
        {"scriptpubkey": "6a24aa21a9ed" + bytes(32).hex()},
        {"scriptpubkey": "6a24aa21a9ed" + commitment}]}
    assert check_witness_commitment(coinbase, bytes(32)) == commitment
    try:
        check_witness_commitment(coinbase, b"\x01" + bytes(31))
    except ValueError:
        pass
    else:
        raise AssertionError("mutated witness root accepted")
    script = b"\x20" + bytes(32) + b"\xac\x00\x63\x03ord\x01\x01\x0atext/plain\x00\x02{}\x68"
    tx = {"input_count": 1, "output_count": 1,
          "witnesses": [[bytes(64).hex(), script.hex(), (b"\xc0" + bytes(32)).hex()]]}
    assert simple_reveal(tx)["body_length"] == 2
    tx["input_count"] = 2
    assert simple_reveal(tx) is None
    assert destination([{"value": 5}, {"value": 8}], 5) == 1
    assert destination([{"value": 5}], 5) is None
    try:
        script_tokens(b"\x4d\x01")
    except ValueError:
        pass
    else:
        raise AssertionError("truncated push accepted")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pilot", type=Path, default=ROOT / "experiments/diagnostics/cp13_pilot_v1_detector_v2.json")
    parser.add_argument("--cache-dir", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--plan", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--verify-witness-blocks", action="store_true")
    args = parser.parse_args()
    self_test()
    if args.self_test:
        return
    pilot_raw = args.pilot.read_bytes()
    selected = select_sample(json.loads(pilot_raw)["candidates"])
    parent_ids = sorted({point.split(":")[0] for row in selected for point in row["prevouts"]})
    plan = {"sample_rule": "two lowest SHA256(CP13-semantic-v1|txid) per stratum x msigner-compatible cell; no replacement",
            "pilot_sha256": hashlib.sha256(pilot_raw).hexdigest(),
            "selected": [{"txid": row["txid"], "stratum": row["stratum"],
                          "msigner_compatible": row["msigner_default_template"]} for row in selected],
            "unique_direct_parents": len(parent_ids)}
    if args.plan:
        print(json.dumps(plan, indent=2))
        return
    if args.cache_dir is None or args.output is None:
        parser.error("--cache-dir and --output required unless --plan or --self-test")
    if args.output.exists():
        parser.error("output exists; choose a new versioned path")
    if len(parent_ids) > 150:
        parser.error("parent budget exceeded; review scope before fetching")
    args.cache_dir.mkdir(parents=True, exist_ok=True)

    def load_parent(txid: str) -> tuple[dict, dict]:
        target = args.cache_dir / f"{txid}.hex"
        url = f"https://blockchain.info/rawtx/{txid}?format=hex"
        payload = target.read_bytes() if target.exists() else fetch(url, attempts=2)
        raw = bytes.fromhex(payload.decode().strip())
        transaction, end = parse_transaction(raw, 0, retain_witnesses=True)
        if end != len(raw) or transaction["txid"] != txid:
            raise ValueError(f"raw parent identity mismatch: {txid}")
        if not target.exists():
            target.write_bytes(payload)
        return transaction, {"txid": txid, "url": url,
                             "raw_sha256": hashlib.sha256(raw).hexdigest()}

    parents, manifests = {}, {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        for txid, pair in zip(parent_ids, pool.map(load_parent, parent_ids)):
            parents[txid], manifests[txid] = pair
    records = []
    for row in selected:
        previous = []
        for point in row["prevouts"]:
            txid, index = point.split(":")
            previous.append(parents[txid]["outputs"][int(index)])
        matches = []
        for match in row["tier1_matches"]:
            index = match["input_index"]
            if previous[index] != {"value": match["prevout_value"], "scriptpubkey": match["scriptpubkey"]}:
                raise ValueError(f"API/raw prevout mismatch: {row['txid']} input {index}")
            parent_id, output_index = row["prevouts"][index].split(":")
            reveal = simple_reveal(parents[parent_id]) if output_index == "0" else None
            evidence = {"input_index": index, "outpoint": row["prevouts"][index],
                        "raw_prevout_verified": True, "direct_simple_reveal": reveal}
            if reveal:
                commit_id, commit_index = parents[parent_id]["prevouts"][0].split(":")
                if commit_id not in parents:
                    parents[commit_id], manifests[commit_id] = load_parent(commit_id)
                commit_output = parents[commit_id]["outputs"][int(commit_index)]
                if not (len(commit_output["scriptpubkey"]) == 68 and commit_output["scriptpubkey"].startswith("5120")):
                    raise ValueError("reveal did not spend P2TR")
                sat_position = sum(item["value"] for item in previous[:index])
                recipient = destination(row["outputs"], sat_position)
                evidence.update({"commit_outpoint": f"{commit_id}:{commit_index}",
                                 "asset_destination_vout": recipient,
                                 "asset_destination_differs_from_seller_script": recipient is not None and row["outputs"][recipient]["scriptpubkey"] != previous[index]["scriptpubkey"]})
            matches.append(evidence)
        records.append({"txid": row["txid"], "stratum": row["stratum"],
                        "msigner_compatible": row["msigner_default_template"],
                        "input_count": len(previous),
                        "raw_distinct_input_scripts": len({item["scriptpubkey"] for item in previous}),
                        "matched_inputs": matches})
    block_proofs = []
    if args.verify_witness_blocks:
        revealed = {item["outpoint"].split(":")[0] for row in records for item in row["matched_inputs"]
                    if item["direct_simple_reveal"]}
        by_height = {}
        for txid in sorted(revealed):
            metadata_path = args.cache_dir / f"{txid}.json"
            metadata_raw = metadata_path.read_bytes() if metadata_path.exists() else fetch(
                f"https://blockchain.info/rawtx/{txid}?format=json", attempts=2)
            metadata = json.loads(metadata_raw)
            if metadata["hash"] != txid:
                raise ValueError("metadata txid mismatch")
            if not metadata_path.exists():
                metadata_path.write_bytes(metadata_raw)
            by_height.setdefault(metadata["block_height"], {})[txid] = manifests[txid]["raw_sha256"]
        for height, targets in sorted(by_height.items()):
            anchor_url = f"https://blockstream.info/api/block-height/{height}"
            anchor_path = args.cache_dir / f"{height}.blockstream.hash"
            anchor_raw = anchor_path.read_bytes() if anchor_path.exists() else fetch(anchor_url, attempts=2)
            block_hash = anchor_raw.decode().strip()
            if len(block_hash) != 64 or len(bytes.fromhex(block_hash)) != 32:
                raise ValueError("invalid block anchor")
            if not anchor_path.exists():
                anchor_path.write_bytes(anchor_raw)
            raw_path = args.cache_dir / f"{height}.raw"
            raw_url = f"https://blockchain.info/rawblock/{block_hash}?format=hex"
            raw_block = raw_path.read_bytes() if raw_path.exists() else bytes.fromhex(
                fetch(raw_url, attempts=2).decode().strip())
            proof = verify_block(raw_block, block_hash, targets)
            if not raw_path.exists():
                raw_path.write_bytes(raw_block)
            block_proofs.append({"height": height, "anchor_url": anchor_url,
                                 "raw_block_url": raw_url, **proof})
            print(f"verified witness commitment for block {height}", flush=True)
    result = {"protocol": {**plan, "verify_witness_blocks": args.verify_witness_blocks}, "summary": {
        "sample_transactions": len(records), "raw_parent_transactions": len(manifests),
        "matched_inputs_verified": sum(len(row["matched_inputs"]) for row in records),
        "transactions_with_direct_simple_reveal": sum(any(item["direct_simple_reveal"] for item in row["matched_inputs"]) for row in records),
        "reveal_transactions_with_witness_commitment": sum(len(proof["targets"]) for proof in block_proofs)},
        "limitations": ["targeted feasibility sample, not prevalence or detector precision estimate",
                        "raw txids recomputed; reveal witness commitments checked only when block_proofs present",
                        "main-chain block anchors trusted from Blockstream; not a full-node consensus or proof-of-work-chain validation",
                        "simple direct reveals only; no full Ordinals or BRC-20 validity/indexing",
                        "asset movement does not prove marketplace attribution or different real-world owners"],
        "code_sha256": {"audit": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                        "parser": hashlib.sha256((ROOT / "scripts/scan_block_sighash.py").read_bytes()).hexdigest()},
        "parent_manifest": list(manifests.values()), "block_proofs": block_proofs, "records": records}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result["summary"], indent=2))


if __name__ == "__main__":
    main()
