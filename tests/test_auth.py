import pytest
from zero_trust_auth.auth import authenticate, compute_stored_token
from zero_trust_auth.grid import derive_monthly_grid
from zero_trust_auth.keygen import generate_keyset, generate_master_seed

FIXED_SEED = b"\x00" * 32


def _build_claimed(keyset, master_seed, year, month):
    """Build a correctly populated claimed_positions dict."""
    grid = derive_monthly_grid(master_seed, year, month)
    return {pos: keyset.keys[key_idx] for key_idx, pos in grid.items()}


def test_correct_auth_returns_true():
    keyset = generate_keyset()
    stored_token = compute_stored_token(keyset)
    claimed = _build_claimed(keyset, FIXED_SEED, 2025, 6)
    assert authenticate(claimed, FIXED_SEED, stored_token, year=2025, month=6) is True


def test_wrong_key_value_halts():
    keyset = generate_keyset()
    stored_token = compute_stored_token(keyset)
    claimed = _build_claimed(keyset, FIXED_SEED, 2025, 6)
    # Replace one key's value with zeros.
    first_pos = next(iter(claimed))
    claimed[first_pos] = bytes(32)
    with pytest.raises(SystemExit):
        authenticate(claimed, FIXED_SEED, stored_token, year=2025, month=6)


def test_missing_key_halts():
    keyset = generate_keyset()
    stored_token = compute_stored_token(keyset)
    claimed = _build_claimed(keyset, FIXED_SEED, 2025, 6)
    del claimed[next(iter(claimed))]
    with pytest.raises(SystemExit):
        authenticate(claimed, FIXED_SEED, stored_token, year=2025, month=6)


def test_wrong_month_grid_halts():
    """
    Keys placed for month 6 must fail when authenticated against month 7.
    The grids differ so positions don't match — halt is triggered.
    """
    keyset = generate_keyset()
    stored_token = compute_stored_token(keyset)
    g6 = derive_monthly_grid(FIXED_SEED, 2025, 6)
    g7 = derive_monthly_grid(FIXED_SEED, 2025, 7)
    if g6 == g7:
        pytest.skip("Grid collision between months (vanishingly rare)")
    claimed = {pos: keyset.keys[key_idx] for key_idx, pos in g6.items()}
    with pytest.raises(SystemExit):
        authenticate(claimed, FIXED_SEED, stored_token, year=2025, month=7)


def test_wrong_stored_token_halts():
    keyset = generate_keyset()
    wrong_token = bytes(64)  # All-zero token — will never match.
    claimed = _build_claimed(keyset, FIXED_SEED, 2025, 6)
    with pytest.raises(SystemExit):
        authenticate(claimed, FIXED_SEED, wrong_token, year=2025, month=6)


def test_short_key_halts():
    keyset = generate_keyset()
    stored_token = compute_stored_token(keyset)
    claimed = _build_claimed(keyset, FIXED_SEED, 2025, 6)
    first_pos = next(iter(claimed))
    claimed[first_pos] = b"\x00" * 16  # Half-length key.
    with pytest.raises(SystemExit):
        authenticate(claimed, FIXED_SEED, stored_token, year=2025, month=6)


def test_empty_claimed_halts():
    keyset = generate_keyset()
    stored_token = compute_stored_token(keyset)
    with pytest.raises(SystemExit):
        authenticate({}, FIXED_SEED, stored_token, year=2025, month=6)


def test_stored_token_is_64_bytes():
    keyset = generate_keyset()
    token = compute_stored_token(keyset)
    assert len(token) == 64  # SHA3-512 output


def test_stored_token_changes_with_keys():
    ks1 = generate_keyset()
    ks2 = generate_keyset()
    assert compute_stored_token(ks1) != compute_stored_token(ks2)
