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


def test_bounded_durations_window_and_coherence():
    from headd_l0.inject import InjectionConfig, inject_original_bounded

    counts = np.tile(np.arange(132, dtype=float) + 50, (13, 1))
    before = counts.copy()
    out = inject_original_bounded(counts, np.random.default_rng(42), InjectionConfig())
    np.testing.assert_array_equal(counts, before)
    np.testing.assert_array_equal(out.counts[1:, :60], before[:, :60])
    np.testing.assert_array_equal(out.counts[0], out.counts[1:].sum(axis=0))
    np.testing.assert_array_equal(out.mask[0], out.mask[1:].any(axis=0))
    assert not out.mask[:, :60].any()
    assert len(out.events) == 13 * 7
    for event in out.events:
        assert event.onset >= 60 and event.onset + event.duration <= 132
        assert event.duration == 1 if event.kind == 0 else 3 <= event.duration <= 6
    again = inject_original_bounded(
        counts, np.random.default_rng(42), InjectionConfig()
    )
    np.testing.assert_array_equal(out.counts, again.counts)
    # PA can have a single class when the union covers the test window.
    # Never change seeds or labels to make the gate pass.
    assert out.mask[0, 60:].all()
    assert (~out.mask[1:, 60:]).any(axis=1).all()


def test_bounded_injection_keeps_stream_order():
    from headd_l0.inject import InjectionConfig, inject_original_bounded

    class Draws:
        def choice(self, values, size=None, replace=None):
            if size is not None:
                assert replace is False and size == 1
                return np.array([131])
            return -1.0

        def integers(self, low, high, size=None):
            if size is not None:
                assert (low, high, size) == (0, 3, 1)
                return np.array([2])
            assert (low, high) == (3, 7)
            return 6

    counts = np.full((13, 132), 100.0)
    out = inject_original_bounded(
        counts, Draws(), InjectionConfig(contamination=1 / 132)
    )
    np.testing.assert_allclose(
        out.counts[1:, 126:], np.tile([95, 90, 85, 80, 75, 70], (13, 1))
    )
    assert all(e.proposed_onset == 131 and e.onset == 126 for e in out.events)
    assert (out.onset == 126).all()
