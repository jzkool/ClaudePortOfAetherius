import sys
import pytest


def _test_halt(code=0):
    raise SystemExit(code)


@pytest.fixture(autouse=True)
def patch_halt(monkeypatch):
    """
    Replace os._exit with a SystemExit raise so tests can assert on
    authentication failures without terminating the pytest process.
    """
    monkeypatch.setattr("zero_trust_auth.failsafe._HALT_IMPL", _test_halt)
