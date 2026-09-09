from hashlib import sha256

import pytest

from btcaml.data.script_identity import (
    MAX_SCRIPT_SIZE,
    is_provably_unspendable,
    script_id,
)


def test_script_id_hashes_raw_bytes_stably_and_is_byte_sensitive():
    script = b"\x00\x14" + b"\x01" * 20
    assert script_id(script) == sha256(script).hexdigest()
    assert script_id(script) == script_id(bytes(script))
    assert script_id(script) != script_id(script + b"\x00")


def test_operational_unspendable_boundaries():
    assert is_provably_unspendable(b"\x6a")
    assert is_provably_unspendable(b"\x6a\x00")
    assert not is_provably_unspendable(b"")
    assert not is_provably_unspendable(b"\x00\x6a")
    assert not is_provably_unspendable(b"\x51" * MAX_SCRIPT_SIZE)
    assert is_provably_unspendable(b"\x51" * (MAX_SCRIPT_SIZE + 1))


@pytest.mark.parametrize("value", ["6a", bytearray(b"\x6a"), memoryview(b"\x6a"), None])
def test_only_bytes_are_accepted(value):
    with pytest.raises(TypeError, match="must be bytes"):
        script_id(value)  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="must be bytes"):
        is_provably_unspendable(value)  # type: ignore[arg-type]
