"""Guided first-run ceremony: generate keys, seed, and stored token."""

from .auth import compute_stored_token
from .display import display_grid_ephemeral
from .keygen import generate_keyset, generate_master_seed


def run_setup(display_grid: bool = True) -> dict:
    """
    Generate a KeySet, master seed, and stored token.

    Returns::

        {
            "keyset":       KeySet,  # distribute each key to its holder
            "master_seed":  bytes,   # store OFFLINE, never in live system
            "stored_token": bytes,   # store in live system
        }

    The raw keys must never be stored by the system. Each keyholder
    receives exactly one key, ideally in a separate private session.
    """
    keyset = generate_keyset()
    master_seed = generate_master_seed()
    stored_token = compute_stored_token(keyset)

    print()
    print("=" * 62)
    print("  ZERO-TRUST 1024-BIT SETUP")
    print("=" * 62)
    print()
    print("Four 256-bit keys generated. Each will be shown privately.")
    print("Distribute each key to its designated keyholder — one key each.")
    print()

    for i, key_hex in enumerate(keyset.as_hex()):
        input(f"Press ENTER when keyholder {i + 1} is ready to receive K-{i + 1} ...")
        print()
        print(f"  K-{i + 1}: {key_hex}")
        print()
        input("Press ENTER once the key has been recorded and the screen cleared ...")
        print("\033[2J\033[H", end="")  # Erase terminal

    print("Master seed (store OFFLINE — never enter this into any live system):")
    print(f"  {master_seed.hex()}")
    print()
    print("Stored token (safe to keep in the live system):")
    print(f"  {stored_token.hex()}")
    print()

    if display_grid:
        input("Press ENTER to display this month's authentication grid ...")
        display_grid_ephemeral(master_seed)

    return {
        "keyset": keyset,
        "master_seed": master_seed,
        "stored_token": stored_token,
    }
