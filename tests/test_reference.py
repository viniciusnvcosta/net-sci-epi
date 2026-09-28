"""Archived oracle fixtures stay verifiable without the retired legacy importer."""

import hashlib
import json
from pathlib import Path

import numpy as np
import pytest

REFERENCE = Path(__file__).parent / "reference"


@pytest.mark.parametrize("path", sorted(REFERENCE.glob("*.npz")), ids=lambda p: p.stem)
def test_archived_arrays_match_pinned_hashes(path):
    manifest = json.loads((REFERENCE / "manifest.json").read_text())
    expected = manifest["array_sha256"][path.stem]
    with np.load(path, allow_pickle=False) as arrays:
        assert set(arrays.files) == set(expected)
        for name in arrays.files:
            # Original exporter makes 0-D arrays contiguous before hashing.
            array = np.ascontiguousarray(arrays[name])
            header = f"{array.dtype.str}|{array.shape}|".encode()
            assert (
                hashlib.sha256(header + array.tobytes()).hexdigest() == expected[name]
            )
