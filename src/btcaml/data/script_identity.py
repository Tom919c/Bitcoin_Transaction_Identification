"""Stable scriptPubKey identities and frozen operational exclusion rule."""

from __future__ import annotations

from hashlib import sha256

OP_RETURN = 0x6A
MAX_SCRIPT_SIZE = 10_000


def _require_bytes(script_pubkey: bytes) -> bytes:
    if not isinstance(script_pubkey, bytes):
        raise TypeError("script_pubkey must be bytes")
    return script_pubkey


def script_id(script_pubkey: bytes) -> str:
    """Return lowercase SHA-256 hex for raw locking-script bytes."""
    return sha256(_require_bytes(script_pubkey)).hexdigest()


def is_provably_unspendable(script_pubkey: bytes) -> bool:
    """Operational rule: OP_RETURN first byte, or a script longer than 10,000 bytes."""
    script_pubkey = _require_bytes(script_pubkey)
    starts_with_op_return = bool(script_pubkey and script_pubkey[0] == OP_RETURN)
    return starts_with_op_return or len(script_pubkey) > MAX_SCRIPT_SIZE
