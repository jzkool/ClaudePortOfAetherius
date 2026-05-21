import pytest
from zero_trust_auth.keygen import (
    KEY_SIZE,
    NUM_KEYS,
    KeySet,
    generate_keyset,
    generate_master_seed,
)


def test_generate_keyset_correct_count():
    ks = generate_keyset()
    assert len(ks.keys) == NUM_KEYS


def test_generate_keyset_correct_size():
    ks = generate_keyset()
    for k in ks.keys:
        assert len(k) == KEY_SIZE


def test_keyset_is_bytes():
    ks = generate_keyset()
    for k in ks.keys:
        assert isinstance(k, bytes)


def test_keyset_uniqueness():
    # Collision probability is 2^-256 per pair — effectively impossible.
    ks1 = generate_keyset()
    ks2 = generate_keyset()
    assert ks1.keys != ks2.keys


def test_keyset_hex_roundtrip():
    ks = generate_keyset()
    assert KeySet.from_hex(ks.as_hex()).keys == ks.keys


def test_keyset_wrong_count_raises():
    with pytest.raises(ValueError):
        KeySet(keys=(b"\x00" * KEY_SIZE,) * (NUM_KEYS - 1))


def test_keyset_wrong_size_raises():
    with pytest.raises(ValueError):
        KeySet(keys=(b"\x00" * (KEY_SIZE // 2),) * NUM_KEYS)


def test_master_seed_size():
    assert len(generate_master_seed()) == 32


def test_master_seed_uniqueness():
    assert generate_master_seed() != generate_master_seed()
