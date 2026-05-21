import hashlib
import hmac
import random
import struct
from datetime import date
from typing import Optional

GRID_ROWS = 4
GRID_COLS = 4
NUM_KEYS = 4

ROW_LABELS = [chr(ord('A') + i) for i in range(GRID_ROWS)]
COL_LABELS = [str(i + 1) for i in range(GRID_COLS)]


def derive_monthly_grid(
    master_seed: bytes,
    year: Optional[int] = None,
    month: Optional[int] = None,
) -> dict:
    """
    Return {key_index: (row, col)} for the given month.

    Deterministic: identical seed + year + month always produces the
    identical grid. Defaults to the current calendar month.
    The grid changes entirely each month; intercepted coordinates are
    obsolete the moment the month rolls over.
    """
    today = date.today()
    y = year if year is not None else today.year
    m = month if month is not None else today.month

    if not (1 <= m <= 12):
        raise ValueError(f"Invalid month: {m}")

    month_tag = struct.pack('>HB', y, m)
    seed_bytes = hmac.new(master_seed, month_tag, hashlib.sha256).digest()

    # Seed Mersenne Twister for a reproducible permutation.
    # The seed_bytes are derived from HMAC-SHA256 so they are unpredictable
    # without the master_seed; the RNG is only used for position shuffling,
    # not for generating key material.
    rng = random.Random(int.from_bytes(seed_bytes, 'big'))
    all_positions = [(r, c) for r in range(GRID_ROWS) for c in range(GRID_COLS)]
    chosen = rng.sample(all_positions, NUM_KEYS)

    return {key_idx: pos for key_idx, pos in enumerate(chosen)}


def format_grid(grid: dict) -> str:
    """Return a human-readable ASCII table showing key placements."""
    pos_to_key = {pos: idx for idx, pos in grid.items()}

    col_header = "      " + "".join(f"  {COL_LABELS[c]}    " for c in range(GRID_COLS))
    divider = "    +" + "------+" * GRID_COLS

    lines = [col_header, divider]
    for r in range(GRID_ROWS):
        cells = []
        for c in range(GRID_COLS):
            key_idx = pos_to_key.get((r, c))
            cells.append(f" K-{key_idx + 1}  " if key_idx is not None else "      ")
        lines.append(f"  {ROW_LABELS[r]} |" + "|".join(cells) + "|")
    lines.append(divider)
    return "\n".join(lines)


def position_label(row: int, col: int) -> str:
    """Convert (row, col) indices to a human label such as 'B3'."""
    return f"{ROW_LABELS[row]}{COL_LABELS[col]}"
