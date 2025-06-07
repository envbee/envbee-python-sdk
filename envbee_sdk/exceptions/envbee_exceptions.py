# ------------------------------------
# Copyright (c) envbee
# Licensed under the MIT License.
# ------------------------------------


class RequestTimeoutError(Exception):
    def __init__(self, message="Request timed out"):
        self.message = message
        super().__init__(self.message)


class RequestError(Exception):
    def __init__(self, status_code, message="Request error"):
        self.status_code = status_code
        self.message = f"{message}. Status code: {status_code}"
        super().__init__(self.message)


class DecryptionError(Exception):
    """Custom exception to signal decryption failures."""

    def __init__(self, message: str, cause: Exception = None):
        super().__init__(message)
        self.cause = cause

    def __str__(self):
        base = super().__str__()
        if self.cause:
            return f"{base} (caused by {repr(self.cause)})"
        return base
