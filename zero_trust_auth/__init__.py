"""
Zero-Trust 1024-Bit Authentication System

Four 256-bit keys + monthly coordinate grid + fail-secure halt.
No external dependencies — pure Python standard library.
"""

from .auth import authenticate, compute_stored_token
from .display import display_grid_ephemeral
from .exceptions import ZeroTrustError, AuthenticationError, KeyFormatError
from .failsafe import halt
from .grid import derive_monthly_grid, format_grid, position_label
from .keygen import KeySet, generate_keyset, generate_master_seed
from .recovery import request_recovery, print_recovery_instructions
from .setup_system import run_setup

__all__ = [
    "authenticate",
    "compute_stored_token",
    "display_grid_ephemeral",
    "ZeroTrustError",
    "AuthenticationError",
    "KeyFormatError",
    "halt",
    "derive_monthly_grid",
    "format_grid",
    "position_label",
    "KeySet",
    "generate_keyset",
    "generate_master_seed",
    "request_recovery",
    "print_recovery_instructions",
    "run_setup",
]
