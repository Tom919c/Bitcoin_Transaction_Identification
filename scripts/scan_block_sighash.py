"""Discover witness byte-shape candidates; prevout-aware validation is required."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


TARGET_SIGHASH = 0x83


def read_compact_size(data: bytes, pos: int) -> tuple[int, int]:
    if pos >= len(data):
        raise ValueError("truncated CompactSize")
    first = data[pos]
    pos += 1
    if first < 0xFD:
        return first, pos
    width = {0xFD: 2, 0xFE: 4, 0xFF: 8}[first]
    end = pos + width
    if end > len(data):
        raise ValueError("truncated CompactSize")
    return int.from_bytes(data[pos:end], "little"), end


def is_der_signature_with_hash_type(item: bytes) -> bool:
    if not 9 <= len(item) <= 73 or item[0] != 0x30 or item[1] != len(item) - 3:
        return False
    len_r = item[3]
    s_tag = 4 + len_r
    if item[2] != 0x02 or s_tag + 2 >= len(item) or item[s_tag] != 0x02:
        return False
    len_s = item[s_tag + 1]
    if not len_r or not len_s or s_tag + 2 + len_s != len(item) - 1:
        return False
    r, s = item[4:s_tag], item[s_tag + 2:-1]
    return all(
        not value[0] & 0x80
        and not (len(value) > 1 and value[0] == 0 and not value[1] & 0x80)
        for value in (r, s)
    )


def signature_kind(item: bytes) -> str | None:
    """Byte shape only: neither signature use nor cryptographic validity is implied."""
    if not item or item[-1] != TARGET_SIGHASH:
        return None
    if len(item) == 65:
        return "schnorr"
    if is_der_signature_with_hash_type(item):
        return "ecdsa"
    return None


def take(data: bytes, pos: int, size: int) -> int:
    end = pos + size
    if end > len(data):
        raise ValueError("truncated block")
    return end


def parse_transaction(data: bytes, pos: int, retain_witnesses: bool = False) -> tuple[dict[str, object], int]:
    version_start = pos
    pos = take(data, pos, 4)
    version = data[version_start:pos]

    has_witness = pos + 2 <= len(data) and data[pos] == 0 and data[pos + 1] != 0
    if has_witness:
        pos += 2

    vin_start = pos
    input_count, pos = read_compact_size(data, pos)
    prevouts: list[str] = []
    script_sigs: list[str] = []
    for _ in range(input_count):
        outpoint_end = take(data, pos, 36)
        prev_txid = data[pos : pos + 32][::-1].hex()
        prev_vout = int.from_bytes(data[pos + 32 : outpoint_end], "little")
        prevouts.append(f"{prev_txid}:{prev_vout}")
        pos = outpoint_end
        script_len, pos = read_compact_size(data, pos)
        script_sigs.append(data[pos:take(data, pos, script_len)].hex())
        pos = take(data, pos, script_len + 4)
    vin_end = pos

    vout_start = pos
    output_count, pos = read_compact_size(data, pos)
    outputs = []
    for _ in range(output_count):
        value = int.from_bytes(data[pos:take(data, pos, 8)], "little")
        pos = take(data, pos, 8)
        script_len, pos = read_compact_size(data, pos)
        end = take(data, pos, script_len)
        outputs.append({"value": value, "scriptpubkey": data[pos:end].hex()})
        pos = end
    vout_end = pos

    matches: list[dict[str, object]] = []
    candidate_witnesses = {}
    all_witnesses = []
    if has_witness:
        for input_index in range(input_count):
            item_count, pos = read_compact_size(data, pos)
            items: list[bytes] = []
            for _ in range(item_count):
                item_len, pos = read_compact_size(data, pos)
                end = take(data, pos, item_len)
                items.append(data[pos:end])
                pos = end

            if retain_witnesses:
                all_witnesses.append([item.hex() for item in items])

            for item_index, item in enumerate(items):
                kind = signature_kind(item)
                if kind:
                    candidate_witnesses[str(input_index)] = {
                        "script_sig": script_sigs[input_index],
                        "items": [value.hex() for value in items],
                    }
                    matches.append(
                        {
                            "input_index": input_index,
                            "witness_item_index": item_index,
                            "signature_kind": kind,
                        }
                    )

    locktime_start = pos
    pos = take(data, pos, 4)
    locktime = data[locktime_start:pos]
    stripped = version + data[vin_start:vin_end] + data[vout_start:vout_end] + locktime
    txid = hashlib.sha256(hashlib.sha256(stripped).digest()).digest()[::-1].hex()
    result = {
        "txid": txid,
        "input_count": input_count,
        "output_count": output_count,
        "prevouts": prevouts,
        "matches": matches,
        "candidate_witnesses": candidate_witnesses,
        "outputs": outputs,
    }
    if retain_witnesses:
        result["witnesses"] = all_witnesses
    return result, pos


def scan_block(data: bytes) -> dict[str, object]:
    if len(data) < 81:
        raise ValueError("raw block is too short")
    pos = 80
    transaction_count, pos = read_compact_size(data, pos)
    candidates: list[dict[str, object]] = []
    for _ in range(transaction_count):
        transaction, pos = parse_transaction(data, pos)
        if transaction["matches"]:
            candidates.append(transaction)
    if pos != len(data):
        raise ValueError(f"unparsed bytes: {len(data) - pos}")
    return {
        "block_hash": hashlib.sha256(hashlib.sha256(data[:80]).digest()).digest()[::-1].hex(),
        "transaction_count": transaction_count,
        "candidate_transaction_count": len(candidates),
        "candidates": candidates,
    }


def self_test() -> None:
    assert read_compact_size(b"\xfc", 0) == (0xFC, 1)
    assert read_compact_size(b"\xfd\x00\x01", 0) == (0x100, 3)
    der = bytes.fromhex("3006020101020101") + bytes([TARGET_SIGHASH])
    assert signature_kind(der) == "ecdsa"
    assert signature_kind(bytes(64) + bytes([TARGET_SIGHASH])) == "schnorr"
    assert signature_kind(bytes([0xC0]) + bytes(63) + bytes([TARGET_SIGHASH])) == "schnorr"
    assert not is_der_signature_with_hash_type(bytes.fromhex("300602018102010183"))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("block", nargs="?", type=Path)
    parser.add_argument("--expect-txid")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        self_test()
    if args.block is None:
        if args.self_test:
            return
        parser.error("block path is required")

    result = scan_block(args.block.read_bytes())
    if args.expect_txid and args.expect_txid not in {
        candidate["txid"] for candidate in result["candidates"]
    }:
        raise SystemExit(f"expected candidate not found: {args.expect_txid}")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
