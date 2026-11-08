"""
Stable protocol error codes for E4A 1.0 (spec section 11/14).

Every protocol-level failure raised by the SDK is an E4AError carrying a
machine-readable ``code``. Clients MUST branch on ``code``, never on the
human-readable message text.
"""


class E4AError(Exception):
    """Base class for protocol errors. ``code`` is one of the constants below."""

    code = "E4A_ERROR"

    def __init__(self, message, code=None):
        super().__init__(message)
        if code:
            self.code = code


# Stable error codes (spec section 14)
VALIDATION_FAILED = "E4A_VALIDATION_FAILED"
UNSUPPORTED_VERSION = "E4A_UNSUPPORTED_VERSION"
NOT_FOUND = "E4A_NOT_FOUND"
UNAUTHORIZED_APPROVER = "E4A_UNAUTHORIZED_APPROVER"
APPROVAL_REQUIRED = "E4A_APPROVAL_REQUIRED"
MANDATE_REJECTED = "E4A_MANDATE_REJECTED"
MANDATE_EXPIRED = "E4A_MANDATE_EXPIRED"
INVALID_TRANSITION = "E4A_INVALID_TRANSITION"
NONCE_CONFLICT = "E4A_NONCE_CONFLICT"
EXECUTION_FAILED = "E4A_EXECUTION_FAILED"
STORE_VERSION = "E4A_STORE_VERSION"

ALL_CODES = [
    VALIDATION_FAILED,
    UNSUPPORTED_VERSION,
    NOT_FOUND,
    UNAUTHORIZED_APPROVER,
    APPROVAL_REQUIRED,
    MANDATE_REJECTED,
    MANDATE_EXPIRED,
    INVALID_TRANSITION,
    NONCE_CONFLICT,
    EXECUTION_FAILED,
    STORE_VERSION,
]
