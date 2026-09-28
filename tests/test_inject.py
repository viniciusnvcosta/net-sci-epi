"""The original injection defect remains independently reproducible in tests."""

from pathlib import Path

import numpy as np


def test_original_defect_characterized():
    from legacy_injection import inject_original

    reference = np.load(Path(__file__).parent / "reference/inject.npz")
    rng = np.random.default_rng(42)
    original = reference["processed_counts"]
    leaves = [inject_original(original[:, i], rng) for i in range(13)]
    state, state_mask = inject_original(original.sum(axis=1), rng)
    np.testing.assert_array_equal(
        np.column_stack([x[0] for x in leaves]), reference["counts_injected"]
    )
    np.testing.assert_array_equal(
        np.column_stack([x[1] for x in leaves]), reference["counts_mask"]
    )
    np.testing.assert_array_equal(state, reference["state_injected"][:, 0])
    np.testing.assert_array_equal(state_mask, reference["state_mask"][:, 0])
    # Original evaluation uses OR over leaves and the last 20% of months.
    labels = reference["counts_mask"].any(axis=1)
    assert labels[-26:].all()
