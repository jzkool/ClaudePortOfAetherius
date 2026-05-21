import pytest
from zero_trust_auth.grid import (
    GRID_COLS,
    GRID_ROWS,
    NUM_KEYS,
    derive_monthly_grid,
    format_grid,
    position_label,
)
from zero_trust_auth.keygen import generate_master_seed

FIXED_SEED = b"\x00" * 32


def test_grid_has_correct_key_count():
    grid = derive_monthly_grid(FIXED_SEED, 2025, 1)
    assert len(grid) == NUM_KEYS


def test_grid_positions_in_bounds():
    grid = derive_monthly_grid(FIXED_SEED, 2025, 1)
    for r, c in grid.values():
        assert 0 <= r < GRID_ROWS
        assert 0 <= c < GRID_COLS


def test_grid_positions_unique():
    grid = derive_monthly_grid(FIXED_SEED, 2025, 1)
    positions = list(grid.values())
    assert len(positions) == len(set(positions))


def test_grid_deterministic():
    g1 = derive_monthly_grid(FIXED_SEED, 2025, 6)
    g2 = derive_monthly_grid(FIXED_SEED, 2025, 6)
    assert g1 == g2


def test_grid_changes_monthly():
    g1 = derive_monthly_grid(FIXED_SEED, 2025, 6)
    g2 = derive_monthly_grid(FIXED_SEED, 2025, 7)
    assert g1 != g2


def test_grid_changes_with_different_seeds():
    seed2 = generate_master_seed()
    g1 = derive_monthly_grid(FIXED_SEED, 2025, 6)
    g2 = derive_monthly_grid(seed2, 2025, 6)
    assert g1 != g2


def test_invalid_month_raises():
    with pytest.raises(ValueError):
        derive_monthly_grid(FIXED_SEED, 2025, 13)


def test_format_grid_contains_all_keys():
    grid = derive_monthly_grid(FIXED_SEED, 2025, 1)
    output = format_grid(grid)
    for i in range(NUM_KEYS):
        assert f"K-{i + 1}" in output


def test_position_label():
    assert position_label(0, 0) == "A1"
    assert position_label(1, 2) == "B3"
    assert position_label(3, 3) == "D4"
