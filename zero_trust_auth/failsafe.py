import os
import sys

# Replaced with sys.exit in the test suite via monkeypatch.
# In production this is os._exit: no Python cleanup, no atexit handlers,
# no exception that can be caught — the process simply ceases to exist.
_HALT_IMPL = os._exit


def halt() -> None:
    """Immediate silent process termination. No error output. No recovery."""
    try:
        sys.stdout.flush()
        sys.stderr.flush()
    except Exception:
        pass
    _HALT_IMPL(0)
