class ZeroTrustError(Exception):
    """Base exception for the zero-trust auth system."""


class AuthenticationError(ZeroTrustError):
    """Raised internally before halt is triggered."""


class KeyFormatError(ZeroTrustError):
    """Invalid key format or size."""
