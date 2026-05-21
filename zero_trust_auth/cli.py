"""Entry point: zt-auth <setup|grid|auth|recover>"""

import argparse
import getpass
import sys

from .auth import authenticate
from .display import display_grid_ephemeral
from .grid import NUM_KEYS, derive_monthly_grid, position_label
from .keygen import KEY_SIZE
from .recovery import print_recovery_instructions, request_recovery
from .setup_system import run_setup


def _read_hex(prompt: str) -> bytes:
    raw = getpass.getpass(prompt).strip()
    try:
        return bytes.fromhex(raw)
    except ValueError:
        print("Error: expected a hex string.", file=sys.stderr)
        sys.exit(1)


def _prompt_keys(master_seed: bytes) -> dict:
    """Interactively prompt each keyholder for their key at the required position."""
    grid = derive_monthly_grid(master_seed)
    claimed = {}
    print()
    print("Enter each key at its required grid position for this month.")
    print()
    for key_idx in range(NUM_KEYS):
        pos = grid[key_idx]
        label = position_label(*pos)
        while True:
            raw = getpass.getpass(f"  K-{key_idx + 1}  (position {label}): ").strip()
            try:
                key_bytes = bytes.fromhex(raw)
            except ValueError:
                print("    Invalid hex string. Try again.")
                continue
            if len(key_bytes) != KEY_SIZE:
                print(f"    Expected {KEY_SIZE} bytes ({KEY_SIZE * 2} hex chars), got {len(key_bytes)}. Try again.")
                continue
            claimed[pos] = key_bytes
            break
    return claimed


def cmd_setup(_args) -> None:
    run_setup()


def cmd_grid(_args) -> None:
    master_seed = _read_hex("Master seed (hex): ")
    display_grid_ephemeral(master_seed)


def cmd_auth(_args) -> None:
    master_seed = _read_hex("Master seed (hex): ")
    stored_token = _read_hex("Stored token (hex): ")
    claimed = _prompt_keys(master_seed)
    authenticate(claimed, master_seed, stored_token)
    print()
    print("[ACCESS GRANTED]")


def cmd_recover(_args) -> None:
    user_id = input("User identifier (name / employee ID): ").strip()
    if not user_id:
        print("Error: user identifier required.", file=sys.stderr)
        sys.exit(1)
    ref = request_recovery(user_id)
    print_recovery_instructions(ref)


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="zt-auth",
        description="Zero-Trust 1024-Bit Authentication System",
    )
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("setup", help="First-run: generate keys, seed, and token")
    sub.add_parser("grid", help="Display this month's grid (90 s, auto-clear)")
    sub.add_parser("auth", help="Authenticate using the 1024-bit threshold")
    sub.add_parser("recover", help="Request in-person key recovery")

    args = parser.parse_args()
    {"setup": cmd_setup, "grid": cmd_grid, "auth": cmd_auth, "recover": cmd_recover}[args.command](args)


if __name__ == "__main__":
    main()
