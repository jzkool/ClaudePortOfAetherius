import secrets
from dataclasses import dataclass

KEY_SIZE = 32        # 256 bits per key
NUM_KEYS = 4         # 4 keys × 256 bits = 1024-bit total credential
MASTER_SEED_SIZE = 32


@dataclass(frozen=True)
class KeySet:
    """Four immutable 256-bit keys constituting the 1024-bit credential."""

    keys: tuple  # tuple[bytes, ...], length NUM_KEYS, each KEY_SIZE bytes

    def __post_init__(self):
        if len(self.keys) != NUM_KEYS:
            raise ValueError(
                f"Exactly {NUM_KEYS} keys required, got {len(self.keys)}"
            )
        for i, k in enumerate(self.keys):
            if not isinstance(k, bytes) or len(k) != KEY_SIZE:
                raise ValueError(
                    f"Key {i} must be {KEY_SIZE} bytes; "
                    f"got {len(k) if isinstance(k, bytes) else type(k).__name__}"
                )

    def as_hex(self) -> list:
        return [k.hex() for k in self.keys]

    @classmethod
    def from_hex(cls, hex_keys: list) -> "KeySet":
        if len(hex_keys) != NUM_KEYS:
            raise ValueError(f"Expected {NUM_KEYS} hex strings, got {len(hex_keys)}")
        return cls(keys=tuple(bytes.fromhex(h) for h in hex_keys))


def generate_keyset() -> KeySet:
    """Generate four cryptographically secure 256-bit keys."""
    return KeySet(keys=tuple(secrets.token_bytes(KEY_SIZE) for _ in range(NUM_KEYS)))


def generate_master_seed() -> bytes:
    """Generate the master seed used to derive monthly grids."""
    return secrets.token_bytes(MASTER_SEED_SIZE)
