"""Pinned primitives and time-causal selection without ground-truth labels."""

import inspect
from itertools import combinations
from pathlib import Path

import numpy as np
import pytest

from headd_l0.select import (
    ADWIN,
    SELECTORS,
    SelectionConfig,
    q_statistic,
    select_stream,
    select_subset,
)


@pytest.fixture
def reference():
    with np.load(Path(__file__).parent / "reference/select.npz") as values:
        yield values


def test_subset_matches_reference(reference):
    actual = select_subset(
        reference["competence"],
        reference["predictions"],
        reference["labels"],
        SelectionConfig(),
    )
    np.testing.assert_array_equal(actual, reference["selected"])
    tied = select_subset(np.ones(6), np.zeros((6, 12)), np.zeros(12), SelectionConfig())
    np.testing.assert_array_equal(tied, np.arange(5))


def test_q_matches_reference(reference):
    pairs = combinations(range(6), 2)
    q = [
        q_statistic(
            reference["predictions"][i],
            reference["predictions"][j],
            reference["labels"],
        )
        for i, j in pairs
    ]
    np.testing.assert_allclose(q, reference["q_pairs"], atol=1e-12)
    assert q_statistic(np.zeros(4), np.zeros(4), np.zeros(4)) == 0


def test_adwin_flags_match_pinned_dependency(reference):
    # Version-compatibility check against exported original calls, not a flow parity claim.
    drift = ADWIN(delta=0.002)
    flags = []
    for value in reference["drift_signal"]:
        drift.update(float(value))
        flags.append(drift.drift_detected)
    np.testing.assert_array_equal(flags, reference["drift_flags"])


def test_prefix_invariance():
    scores = np.random.default_rng(42).normal(size=(132, 6))
    first = select_stream(scores, 60, SelectionConfig())
    changed = scores.copy()
    changed[90:] += 1000
    second = select_stream(changed, 60, SelectionConfig())
    prefix = select_stream(scores[:90], 60, SelectionConfig())
    np.testing.assert_array_equal(first.active[:91], second.active[:91])
    np.testing.assert_allclose(first.competence[:91], second.competence[:91])
    np.testing.assert_allclose(first.scores[:90], second.scores[:90])
    np.testing.assert_array_equal(first.active[:90], prefix.active)
    np.testing.assert_allclose(first.scores[:90], prefix.scores)
    assert np.all(first.active[60:] < 6)
    assert np.isnan(first.scores[:60]).all()


def test_competence_uses_previous_window_precision_and_recall():
    train = np.tile(np.linspace(0, 1, 60)[:, None], (1, 6))
    recent = np.array(
        [
            [2, 2, 2, 2, 0, 0],
            [2, 2, 2, 0, 2, 0],
            [0, 0, 0, 2, 2, 0],
            [0, 0, 0, 0, 0, 0],
            [100] * 6,
        ]
    )
    result = select_stream(np.vstack([train, recent]), 60, SelectionConfig(window=4))
    np.testing.assert_allclose(result.competence[64], [1, 1, 1, 0.5, 0.5, 0])
    np.testing.assert_array_equal(result.active[64], [0, 1, 2, 3, 4])


def test_no_positive_window_uses_negative_agreement():
    train = np.tile(np.linspace(0, 1, 60)[:, None], (1, 6))
    recent = np.array([[2, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0], [100] * 6])
    result = select_stream(np.vstack([train, recent]), 60, SelectionConfig(window=2))
    np.testing.assert_allclose(result.competence[62], [0.5, 1, 1, 1, 1, 1])


def test_drift_resets_only_future():
    train = np.tile(np.linspace(0, 1, 60)[:, None], (1, 6))
    stable = np.zeros((200, 6))
    conflict = np.tile([2, 2, 2, 0, 0, 0], (400, 1))
    scores = np.vstack([train, stable, conflict])
    result = select_stream(scores, 60, SelectionConfig())
    events = np.flatnonzero(result.drift)
    assert len(events) > 0
    first = events[0]
    assert first > 260
    assert not np.all(result.competence[first] == 0.5)
    np.testing.assert_array_equal(result.competence[first + 1], np.full(6, 0.5))
    np.testing.assert_array_equal(result.active[first + 1], np.arange(5))
    prefix = select_stream(scores[: first + 1], 60, SelectionConfig())
    np.testing.assert_allclose(result.competence[: first + 1], prefix.competence)
    np.testing.assert_allclose(result.scores[: first + 1], prefix.scores)


def test_no_labels_argument_and_training_normalization():
    assert tuple(inspect.signature(select_stream).parameters) == (
        "scores",
        "train_end",
        "cfg",
    )
    train = np.tile(np.linspace(0, 1, 60)[:, None], (1, 6))
    scores = np.vstack([train, np.full((3, 6), 2)])
    original = scores.copy()
    result = SELECTORS["meta_des"](scores, 60, SelectionConfig())
    np.testing.assert_allclose(result.scores[60:], 2.0)
    np.testing.assert_array_equal(scores, original)
    constant = select_stream(
        np.vstack([np.ones((60, 6)), np.full((2, 6), 10)]), 60, SelectionConfig()
    )
    np.testing.assert_array_equal(constant.scores[60:], np.zeros(2))


@pytest.mark.parametrize(
    "scores,end,cfg",
    [
        (np.ones((70, 6)), 0, SelectionConfig()),
        (np.ones((70, 6)), 71, SelectionConfig()),
        (np.full((70, 6), np.nan), 60, SelectionConfig()),
        (np.ones((70, 6)), 60, SelectionConfig(k=7)),
        (np.ones((70, 6)), 60, SelectionConfig(window=0)),
        (np.ones((70, 6)), 60, SelectionConfig(alpha=2)),
    ],
)
def test_invalid_stream_rejected(scores, end, cfg):
    with pytest.raises(ValueError):
        select_stream(scores, end, cfg)
