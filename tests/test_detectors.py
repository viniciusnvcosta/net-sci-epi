"""Behavior and independent numerical checks for the corrected six-detector pool."""

import numpy as np
import pytest
from pyod.models.iforest import IForest
from pyod.models.pca import PCA
from scipy.stats import spearmanr
from sklearn.covariance import MinCovDet

from headd_l0.detectors import DETECTORS, DetectorConfig, MCDDetector, _c_steps


@pytest.fixture
def samples():
    rng = np.random.default_rng(42)
    return rng.normal(size=(240, 3)), rng.normal(size=(40, 3))


@pytest.mark.parametrize("name", ["pca", "lof", "knn", "hbos", "iforest", "mcd"])
def test_outlier_has_larger_score(name, samples):
    train, test = samples
    detector = DETECTORS[name](DetectorConfig(seed=42)).fit(train)
    scores = detector.score(test)
    assert scores.shape == (40,)
    assert np.isfinite(scores).all()
    assert np.median(detector.score(test + 10)) > np.median(scores)


@pytest.mark.parametrize("name", ["pca", "lof", "knn", "hbos", "iforest", "mcd"])
def test_scoring_batch_does_not_refit(name, samples):
    train, test = samples
    detector = DETECTORS[name](DetectorConfig(seed=42)).fit(train)
    before = detector.score(test[:3])
    detector.score(test + 1000)
    np.testing.assert_allclose(before, detector.score(test)[:3], rtol=1e-12)
    repeated = DETECTORS[name](DetectorConfig(seed=42)).fit(train).score(test)
    np.testing.assert_array_equal(detector.score(test), repeated)


@pytest.mark.parametrize("name", ["pca", "lof", "knn", "hbos", "iforest", "mcd"])
def test_univariate_and_constant_features(name):
    x = np.random.default_rng(5).normal(size=(100, 1))
    cfg = DetectorConfig(seed=42)
    solo = DETECTORS[name](cfg).fit(x)
    padded = DETECTORS[name](cfg).fit(np.column_stack([x, np.ones(100)]))
    query = np.array([[0.0], [10.0]])
    assert np.isfinite(solo.score(query)).all()
    assert solo.score(query)[1] > solo.score(query)[0]
    np.testing.assert_allclose(
        solo.score(query), padded.score(np.column_stack([query, [1, 1]]))
    )
    constant = DETECTORS[name](cfg).fit(np.ones((50, 2)))
    np.testing.assert_allclose(constant.score(np.array([[1, 1], [4, 5]])), [0, 5])


@pytest.mark.parametrize("name", ["pca", "lof", "knn", "hbos", "iforest", "mcd"])
def test_invalid_shapes_and_values_rejected(name, samples):
    train, _ = samples
    for bad in (np.ones(20), np.empty((0, 3)), np.full((30, 2), np.nan)):
        with pytest.raises(ValueError):
            DETECTORS[name](DetectorConfig(seed=42)).fit(bad)
    detector = DETECTORS[name](DetectorConfig(seed=42)).fit(train)
    with pytest.raises(ValueError):
        detector.score(np.ones((2, 4)))


@pytest.mark.parametrize("name,model", [("pca", PCA), ("iforest", IForest)])
def test_detector_reference(name, model, samples):
    # These are the two functioning original wrapper primitives; PCA sign is corrected.
    train, test = samples
    seed = int(np.random.SeedSequence(42).generate_state(1)[0])
    options = {"n_components": 0.95} if name == "pca" else {"n_estimators": 100}
    original_primitive = model(contamination=0.05, random_state=seed, **options).fit(
        train
    )
    actual = DETECTORS[name](DetectorConfig(seed=42)).fit(train).score(test)
    np.testing.assert_allclose(
        actual, original_primitive.decision_function(test), rtol=1e-7, atol=1e-9
    )


def test_c_steps_do_not_increase_logdet(samples):
    train, _ = samples
    _, covariance, history = _c_steps(train, np.arange(122), 122)
    assert len(history) > 1
    assert np.all(np.diff(history) <= 1e-10)
    assert np.isfinite(covariance).all()


def test_mcd_against_sklearn(samples):
    train, test = samples
    actual = MCDDetector(DetectorConfig(seed=42)).fit(train)
    reference = MinCovDet(random_state=42).fit(train)
    relative = np.linalg.norm(
        actual.covariance_ - reference.covariance_
    ) / np.linalg.norm(reference.covariance_)
    assert relative <= 0.15
    assert spearmanr(actual.score(test), reference.mahalanobis(test)).statistic >= 0.95


def test_mcd_contamination_and_degenerate_geometry(samples):
    train, test = samples
    model = MCDDetector(DetectorConfig(seed=42)).fit(
        np.vstack([train, np.full((30, 3), 50)])
    )
    assert np.linalg.norm(model.location_) < 0.5
    assert np.median(model.score(test + 50)) > 10 * np.median(model.score(test))
    collinear = np.column_stack([train[:, 0], train[:, 0]])
    assert np.isfinite(
        MCDDetector(DetectorConfig(seed=42)).fit(collinear).score(collinear[:2])
    ).all()
    with pytest.raises(ValueError):
        MCDDetector(DetectorConfig(seed=42)).fit(np.arange(12).reshape(3, 4))
