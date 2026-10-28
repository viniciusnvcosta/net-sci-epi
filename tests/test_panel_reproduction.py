import numpy as np
import pandas as pd
import pytest

from headd_l0.data import MONTHS, hierarchy
from headd_l0.panel_reproduction import canonical_panel, panel_hash


@pytest.fixture
def groups():
    return pd.DataFrame(
        [
            {"region": name, "month": month, "species": "negative", "count": 2}
            for name in hierarchy().leaves
            for month in MONTHS
        ]
        + [
            {
                "region": hierarchy().leaves[0],
                "month": MONTHS[0],
                "species": "vivax",
                "count": 3,
            }
        ]
    )


def test_panel_missing_and_difference(groups):
    with pytest.raises(ValueError, match="missing"):
        canonical_panel(
            groups.loc[
                ~(
                    (groups.region == hierarchy().leaves[1])
                    & (groups.month == MONTHS[0])
                )
            ]
        )
    positives, tests = canonical_panel(groups)
    assert positives[0, 0] == 3
    assert tests[0, 0] == 5
    altered = groups.copy()
    altered.loc[0, "count"] = 4
    other = canonical_panel(altered)
    assert not np.array_equal(tests, other[1])
    assert panel_hash((positives, tests)) != panel_hash(other)


def test_canonical_panel_order(groups):
    a = canonical_panel(groups)
    b = canonical_panel(groups.sample(frac=1, random_state=3))
    assert all(np.array_equal(x, y) for x, y in zip(a, b, strict=True))
    assert panel_hash(a) == panel_hash(b)
