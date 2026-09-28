"""Metric parity, alarm provenance and explicit detection censoring."""

from pathlib import Path

import numpy as np
import pytest

from headd_l0.evaluate import (
    auc_pr,
    classification_metrics,
    detection_outcome,
    nab_simplified,
    observed_far,
)


def test_ap_matches_original():
    with np.load(Path(__file__).parent / "reference/metrics.npz") as ref:
        assert auc_pr(ref["labels"], ref["scores"]) == pytest.approx(
            ref["metrics"][0], abs=1e-12
        )
        alarms = ref["scores"] >= ref["metrics"][5]
        values = classification_metrics(ref["labels"], ref["scores"], alarms)
        for name, index in [
            ("auc_pr", 0),
            ("f1", 1),
            ("nab_simplified", 2),
            ("precision", 3),
            ("recall", 4),
        ]:
            assert values[name] == pytest.approx(ref["metrics"][index], abs=1e-12)


def test_lead_sign():
    alarms = np.zeros(132, dtype=bool)
    alarms[[1, 80, 90]] = True
    out = detection_outcome(alarms, onset=84)
    assert (out.delay, out.lead, out.detected, out.first_alarm) == (-4, 4, True, 80)
    assert not out.censored and out.restricted_lead == 4
    alarms[80] = False
    late = detection_outcome(alarms, onset=84)
    assert (late.delay, late.lead) == (6, -6)


def test_missed_detection_is_censored():
    missing = detection_outcome(np.zeros(132, bool), onset=84)
    assert missing.censored and missing.restricted_lead == -13
    assert missing.lead is missing.delay is missing.first_alarm is None
    edge = detection_outcome(np.zeros(132, bool), onset=130)
    assert edge.censored and edge.restricted_lead == -2
    alarms = np.zeros(132, bool)
    alarms[96] = True
    assert detection_outcome(alarms, 84).detected
    alarms[96], alarms[97] = False, True
    assert not detection_outcome(alarms, 84).detected


def test_no_onset_not_in_detection_denominator():
    out = detection_outcome(np.ones(132, bool), onset=-1)
    assert not out.detected and not out.censored
    assert out.lead is out.delay is out.restricted_lead is out.first_alarm is None


@pytest.mark.parametrize("label", [0, 1])
def test_single_class_auc_status(label):
    labels = np.full(10, label)
    result = classification_metrics(labels, np.arange(10.0), np.zeros(10, bool))
    assert result["roc_auc"] is None and result["auc_pr"] is None
    assert result["f1"] == 0
    with pytest.raises(ValueError, match="both classes"):
        auc_pr(labels, np.arange(10.0))


def test_nab_uses_supplied_alarms():
    labels = np.zeros(20, bool)
    labels[10:12] = True
    none = np.zeros(20, bool)
    hit = none.copy()
    hit[10] = True
    hit[0] = True
    assert nab_simplified(labels, none) == 0
    assert nab_simplified(labels, hit) == pytest.approx(0.89)
    result = classification_metrics(labels, np.arange(20.0), none)
    assert result["f1"] == result["nab_simplified"] == 0
    assert result["roc_auc"] is not None


def test_observed_far_uses_eligible_months_only():
    assert observed_far(np.array([True] + [False] * 59), np.ones(60, bool)) == 1 / 60
    assert (
        observed_far(np.array([True, False, True]), np.array([False, True, True]))
        == 0.5
    )
    with pytest.raises(ValueError):
        observed_far(np.zeros(3, bool), np.zeros(3, bool))


def test_invalid_metric_inputs_rejected():
    with pytest.raises(ValueError):
        classification_metrics(
            np.array([0, 1]), np.array([1.0, np.nan]), np.array([0, 1])
        )
    with pytest.raises(ValueError):
        observed_far(np.array([True]), np.ones(2, bool))
    with pytest.raises(ValueError):
        detection_outcome(np.zeros(10, bool), 10)
    with pytest.raises(ValueError):
        detection_outcome(np.zeros(10, bool), 2, pre=-1)
