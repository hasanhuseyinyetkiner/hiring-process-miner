class ImportRejected(Exception):
    """A user-facing import failure that should not include a traceback."""

    def __init__(self, message: str, code: str, status_code: int = 400) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code


class CaseNotFound(Exception):
    """Raised when a case id is not in the filtered dataset."""


class DatasetNotFound(Exception):
    """Raised when an analytics request names a dataset that is not stored."""


class BindRefused(RuntimeError):
    """Startup refused a non-loopback bind without an explicit opt-in."""
