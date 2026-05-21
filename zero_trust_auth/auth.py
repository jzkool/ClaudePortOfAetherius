import hashlib
import hmac
from typing import Optional

from .failsafe import halt
from .grid import derive_monthly_grid
from .keygen import KEY_SIZE, NUM_KEYS, KeySet

_HASH = hashlib.sha3_512


def compute_stored_token(keyset: KeySet) -> bytes:
    """
    Compute the token stored permanently by the system.

    Token = SHA3-512(key-0 ‖ key-1 ‖ key-2 ‖ key-3)

    Store this value; raw keys are NEVER held by the system.
    Call this once during setup, then discard the KeySet.
    """
    return _HASH(b"".join(keyset.keys)).digest()


def authenticate(
    claimed_positions: dict,
    master_seed: bytes,
    stored_token: bytes,
    year: Optional[int] = None,
    month: Optional[int] = None,
) -> bool:
    """
    Authenticate using the 1024-bit multi-key threshold.

    claimed_positions  -- {(row, col): key_bytes} as supplied by the user
    master_seed        -- offline secret used to derive the monthly grid
    stored_token       -- SHA3-512 digest produced at setup time

    Returns True on success.
    Calls halt() immediately on ANY failure: wrong keys, wrong positions,
    missing keys, wrong token, unexpected exceptions. Nothing is returned
    or raised on failure — the process ends.
    """
    try:
        grid = derive_monthly_grid(master_seed, year, month)

        # Reconstruct keys in canonical order (key-0 ... key-3) using the
        # current month's grid to determine required positions.
        ordered_keys = []
        for key_idx in range(NUM_KEYS):
            required_pos = grid[key_idx]
            key_bytes = claimed_positions.get(required_pos)
            if not isinstance(key_bytes, (bytes, bytearray)) or len(key_bytes) != KEY_SIZE:
                halt()
            ordered_keys.append(bytes(key_bytes))

        computed = _HASH(b"".join(ordered_keys)).digest()

        # Constant-time comparison prevents timing oracle attacks.
        if not hmac.compare_digest(computed, stored_token):
            halt()

        return True

    except SystemExit:
        raise  # Let halt()'s exit propagate cleanly in tests.
    except Exception:
        halt()

    return False  # Unreachable; satisfies static analysers.
