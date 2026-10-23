"""File integrity and Linux no-replace publication for fixed G4 packages."""

import ctypes
import errno
import hashlib
import json
from pathlib import Path


def _sha256(path: Path) -> str:
    """Hash the exact file bytes without loading the whole archive."""
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def _publish(stage: Path, destination: Path) -> None:
    """Atomically publish a closed directory, never replacing a destination."""
    libc = ctypes.CDLL(None, use_errno=True)
    rename = getattr(libc, "renameat2", None)
    if rename is None:
        raise OSError("atomic no-replace publication unavailable; staging preserved")
    rename.argtypes = [
        ctypes.c_int,
        ctypes.c_char_p,
        ctypes.c_int,
        ctypes.c_char_p,
        ctypes.c_uint,
    ]
    rename.restype = ctypes.c_int
    if rename(-100, bytes(stage), -100, bytes(destination), 1):
        error = ctypes.get_errno()
        if error == errno.EEXIST:
            raise FileExistsError(
                error, "destination exists; staging preserved", str(destination)
            )
        raise OSError(
            error,
            "atomic no-replace publication failed; staging preserved",
            str(destination),
        )


def _write_json(path: Path, value: dict) -> None:
    """Write strict JSON with stable keys and a final newline."""
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n")
