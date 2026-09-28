# ABOUTME: Shared pytest fixtures: a small synthetic SIVEP raw directory built in tmp_path.
# ABOUTME: Lets loader tests exercise real CSV parsing without the external raw files.
"""Synthetic raw files in the exact layout of the SIVEP-PA CSVs."""

import pandas as pd
import pytest

LEAVES = (
    "ARAGUAIA",
    "BAIXO AMAZONAS",
    "CARAJAS",
    "LAGO DE TUCURUI",
    "MARAJO I",
    "MARAJO II",
    "METROPOLITANA I",
    "METROPOLITANA II",
    "METROPOLITANA III",
    "RIO CAETES",
    "TAPAJOS",
    "TOCANTINS",
    "XINGU",
)
SPECIES = {"falciparum": 1, "vivax": 2, "F+FG": 1, "negative": 10}


def hr_rows() -> pd.DataFrame:
    """One row per region, month and species; values vary with region and month."""
    rows = []
    for year in range(2009, 2020):
        for month in range(1, 13):
            for r, region in enumerate(LEAVES):
                for species, base in SPECIES.items():
                    rows.append((year, month, region, species, base * (r + 1) + month))
    columns = [
        "notification.year",
        "notification.month",
        "notification.hr",
        "exam.result",
        "testperhr",
    ]
    return pd.DataFrame(rows, columns=columns)


def write_raw(directory, hr: pd.DataFrame) -> None:
    """Write both CSVs, deriving PA.csv totals from ``hr`` as the real file does."""
    directory.mkdir(parents=True, exist_ok=True)
    hr.to_csv(directory / "PASIVEPDailyPerHr.csv", index=False)
    keys = ["notification.year", "notification.month"]
    positive = hr["exam.result"] != "negative"
    state = pd.DataFrame(
        {
            "positives": hr[positive].groupby(keys)["testperhr"].sum(),
            "totalTests": hr.groupby(keys)["testperhr"].sum(),
        }
    ).reset_index()
    state["negatives"] = state["totalTests"] - state["positives"]
    state["monthlyPrevalence"] = state["positives"] / state["totalTests"]
    state.insert(0, "Date", [f"{m}/1/{y}" for y, m in zip(*[state[k] for k in keys])])
    columns = [
        "Date",
        *keys,
        "monthlyPrevalence",
        "negatives",
        "positives",
        "totalTests",
    ]
    state[columns].to_csv(directory / "PA.csv", index=False)


@pytest.fixture
def raw_dir(tmp_path):
    """A complete, coherent synthetic raw directory."""
    write_raw(tmp_path / "raw", hr_rows())
    return tmp_path / "raw"
