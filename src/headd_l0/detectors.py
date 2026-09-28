"""Corrected CDADE-style pool (D3), fitted on training features only.

PyOD provides five primitives; MCD uses independent C-steps and Gaussian
consistency/reweighting. Scores increase with anomaly strength. This pool is
B1* behavior, not a claim of parity with the defective original pipeline.
"""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol, Self, cast

import numpy as np
from pyod.models.hbos import HBOS
from pyod.models.iforest import IForest
from pyod.models.knn import KNN
from pyod.models.lof import LOF
from pyod.models.pca import PCA
from scipy.stats import chi2


@dataclass(frozen=True)
class DetectorConfig:
    """Seed for this fit and expected training contamination."""

    seed: int
    contamination: float = 0.05


class _Scorer(Protocol):
    def decision_function(self, X: np.ndarray) -> np.ndarray: ...


def _matrix(X: np.ndarray) -> np.ndarray:
    X = np.asarray(X, dtype=float)
    if X.ndim != 2 or min(X.shape) == 0 or not np.isfinite(X).all():
        raise ValueError("features must be a nonempty finite 2-D matrix")
    return X


class _Detector:
    def __init__(self, cfg: DetectorConfig):
        self.cfg = cfg
        self.mean_: np.ndarray | None = None
        self.mask_: np.ndarray | None = None
        self.model_: _Scorer | None = None

    def fit(self, X: np.ndarray) -> Self:
        """Fit on training samples; freeze the constant-feature mask.

        Args:
            X: Finite training features, shape [samples, features].
        """
        X = _matrix(X)
        if len(X) < 2:
            raise ValueError("at least two training samples are required")
        if not 0 < self.cfg.contamination <= 0.5:
            raise ValueError("contamination must be in (0, .5]")
        self.mean_ = X.mean(axis=0)
        self.mask_ = np.ptp(X, axis=0) > 0
        if self.mask_.any():
            self._fit(X[:, self.mask_])
        return self

    def score(self, X: np.ndarray) -> np.ndarray:
        """Return one anomaly score per sample without updating fitted state.

        Args:
            X: Samples in the same feature order used for training.
        """
        X = _matrix(X)
        mean = self.mean_
        mask = self.mask_
        if mean is None or mask is None:
            raise ValueError("detector must be fitted before scoring")
        if X.shape[1] != len(mean):
            raise ValueError("feature dimension differs from training")
        if not mask.any():
            return np.linalg.norm(X - mean, axis=1)
        return self._score(X[:, mask])

    def _fit(self, X: np.ndarray) -> None:
        raise NotImplementedError("subclasses must implement _fit")

    def _score(self, X: np.ndarray) -> np.ndarray:
        model = self.model_
        if model is None:
            raise ValueError("detector model is not fitted")
        return model.decision_function(X)

    def _seed(self) -> int:
        return int(np.random.SeedSequence(self.cfg.seed).generate_state(1)[0])


class PCADetector(_Detector):
    """PyOD PCA with its original positive anomaly orientation."""

    def _fit(self, X: np.ndarray) -> None:
        self.model_ = PCA(
            n_components=0.95,
            contamination=self.cfg.contamination,
            random_state=self._seed(),
        ).fit(X)


class LOFDetector(_Detector):
    """Local outlier factor scores with 20 neighbours."""

    def _fit(self, X: np.ndarray) -> None:
        if len(X) <= 20:
            raise ValueError("LOF requires more than 20 training samples")
        model = LOF(n_neighbors=20, contamination=self.cfg.contamination).fit(X)
        self.model_ = cast(_Scorer, model)


class KNNDetector(_Detector):
    """Distance to the twentieth nearest training neighbour."""

    def _fit(self, X: np.ndarray) -> None:
        if len(X) <= 20:
            raise ValueError("KNN requires more than 20 training samples")
        self.model_ = KNN(n_neighbors=20, contamination=self.cfg.contamination).fit(X)


class HBOSDetector(_Detector):
    """Histogram outlier scores using ten bins per feature."""

    def _fit(self, X: np.ndarray) -> None:
        model = HBOS(n_bins=10, contamination=self.cfg.contamination).fit(X)
        self.model_ = cast(_Scorer, model)


class IFDetector(_Detector):
    """Isolation forest with 100 trees and a derived library seed."""

    def _fit(self, X: np.ndarray) -> None:
        model = IForest(
            n_estimators=100,
            contamination=self.cfg.contamination,
            random_state=self._seed(),
        ).fit(X)

        self.model_ = cast(_Scorer, model)


def _estimate(X: np.ndarray, floor: float) -> tuple[np.ndarray, np.ndarray]:
    location = X.mean(axis=0)
    centered = X - location
    covariance = centered.T @ centered / len(X)
    covariance += floor * np.eye(X.shape[1])
    return location, covariance


def _distances(
    X: np.ndarray, location: np.ndarray, covariance: np.ndarray
) -> np.ndarray:
    diff = X - location
    return np.einsum("ij,ji->i", diff, np.linalg.solve(covariance, diff.T))


def _c_steps(
    X: np.ndarray, indices: np.ndarray, h: int
) -> tuple[np.ndarray, np.ndarray, list[float]]:
    """Concentrate an initial support; keep a non-increasing logdet history."""
    floor = 1e-8 * max(float(np.var(X, axis=0).mean()), 1.0)
    location, covariance = _estimate(X[indices], floor)
    history = [float(np.linalg.slogdet(covariance)[1])]
    for _ in range(50):
        support = np.argsort(_distances(X, location, covariance), kind="stable")[:h]
        new_location, new_covariance = _estimate(X[support], floor)
        determinant = float(np.linalg.slogdet(new_covariance)[1])
        if determinant > history[-1]:
            break
        improvement = history[-1] - determinant
        location, covariance = new_location, new_covariance
        history.append(determinant)
        if improvement <= 1e-7:
            break
    return location, covariance, history


class MCDDetector(_Detector):
    """FAST-MCD C-steps with 50 starts, consistency correction and reweighting.

    ``location_`` and ``covariance_`` describe retained (nonconstant) features.
    Covariance uses a fixed ridge for degenerate geometry. Squared Mahalanobis
    distances determine supports; score returns their nonnegative square root.
    """

    def __init__(self, cfg: DetectorConfig):
        super().__init__(cfg)
        self.location_: np.ndarray | None = None
        self.covariance_: np.ndarray | None = None
        self.logdet_history_: list[float] = []

    def _fit(self, X: np.ndarray) -> None:
        n, p = X.shape
        if n <= p:
            raise ValueError("MCD needs more samples than retained features")
        h = (n + p + 1) // 2
        rng = np.random.default_rng(self.cfg.seed)
        best: tuple[np.ndarray, np.ndarray, list[float]] | None = None
        for _ in range(50):
            candidate = _c_steps(X, rng.choice(n, size=h, replace=False), h)
            if best is None or candidate[2][-1] < best[2][-1]:
                best = candidate
        assert best is not None
        location, covariance, self.logdet_history_ = best
        fraction = h / n
        covariance *= fraction / chi2.cdf(chi2.ppf(fraction, p), p + 2)
        support = _distances(X, location, covariance) <= chi2.ppf(0.975, p)
        if support.sum() > p:
            floor = 1e-8 * max(float(np.var(X, axis=0).mean()), 1.0)
            location, covariance = _estimate(X[support], floor)
            covariance *= 0.975 / chi2.cdf(chi2.ppf(0.975, p), p + 2)
        self.location_, self.covariance_ = location, covariance

    def _score(self, X: np.ndarray) -> np.ndarray:
        location = self.location_
        covariance = self.covariance_
        if location is None or covariance is None:
            raise ValueError("detector must be fitted before scoring")
        return np.sqrt(np.maximum(_distances(X, location, covariance), 0))


DETECTORS: dict[str, Callable[[DetectorConfig], _Detector]] = {
    "pca": PCADetector,
    "lof": LOFDetector,
    "knn": KNNDetector,
    "hbos": HBOSDetector,
    "iforest": IFDetector,
    "mcd": MCDDetector,
}


def rolling_zscore(counts: np.ndarray, window: int = 12) -> np.ndarray:
    """Absolute z-score against strictly previous months, separately by series.

    Args:
        counts: Finite panel [series, time].
        window: Number of previous observations; warmup scores are NaN.

    A constant history uses unit scale, making equal values score zero while
    preserving finite scores for departures. Scale otherwise uses ddof=1.
    """
    values = np.asarray(counts, dtype=float)
    if values.ndim != 2 or not np.isfinite(values).all() or window < 2:
        raise ValueError("expected a finite panel and window >= 2")
    scores = np.full(values.shape, np.nan)
    for t in range(window, values.shape[1]):
        history = values[:, t - window : t]
        scale = history.std(axis=1, ddof=1)
        scores[:, t] = np.abs(values[:, t] - history.mean(axis=1)) / np.where(
            scale > 0, scale, 1
        )
    return scores
