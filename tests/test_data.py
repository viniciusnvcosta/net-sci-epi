# ABOUTME: Tests for SIVEP loading: canonical order, count/test coherence and structural gaps.
# ABOUTME: A reference test compares the real CSVs with the pinned CDADE export, exactly.
"""Behaviour and parity tests for ``headd_l0.data``."""

import hashlib
import json
import os
from pathlib import Path

import numpy as np
import pytest
from conftest import LEAVES, hr_rows, write_raw

from headd_l0.data import hierarchy, load_sivep, main, prepare

REFERENCE = Path(__file__).parent / "reference"
KEYS = ["notification.year", "notification.month", "notification.hr"]


def _hashes(directory: Path) -> dict[str, str]:
    return {
        p.name: hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(directory.iterdir())
    }


def test_hierarchy_is_pa_over_13_leaves_in_canonical_order():
    h = hierarchy()
    assert h.state == "PA"
    assert h.leaves == LEAVES
    with pytest.raises(AttributeError):
        h.state = "AM"


def test_counts_sum_every_non_negative_result(raw_dir):
    hr = hr_rows()
    bundle = load_sivep(raw_dir)
    cell = hr[(hr["notification.hr"] == "CARAJAS") & (hr["notification.year"] == 2010)]
    cell = cell[cell["notification.month"] == 3]
    assert bundle.counts.shape == (13, 132)
    assert (
        bundle.counts[2, 14]
        == cell.loc[cell["exam.result"] != "negative", "testperhr"].sum()
    )
    assert bundle.tests[2, 14] == cell["testperhr"].sum()
    assert bundle.months[0].strftime("%Y-%m") == "2009-01"
    assert bundle.months[-1].strftime("%Y-%m") == "2019-12"
    assert bundle.counts.dtype == np.int64


def test_state_and_test_coherence(raw_dir):
    bundle = load_sivep(raw_dir)
    hr = hr_rows()
    totals = hr.groupby(KEYS[:2])["testperhr"].sum().to_numpy()
    np.testing.assert_array_equal(bundle.counts.sum(axis=0), bundle.state_counts)
    np.testing.assert_array_equal(bundle.tests.sum(axis=0), totals)


def test_incoherent_state_total_rejected(tmp_path):
    write_raw(tmp_path, hr_rows())
    state = (tmp_path / "PA.csv").read_text().splitlines()
    fields = state[5].split(",")
    fields[5] = str(int(fields[5]) + 1)  # positives of 2009-05
    state[5] = ",".join(fields)
    (tmp_path / "PA.csv").write_text("\n".join(state) + "\n")
    with pytest.raises(ValueError, match="PA"):
        load_sivep(tmp_path)


@pytest.mark.parametrize(
    "drop",
    [
        lambda hr: (hr["notification.year"] == 2012) & (hr["notification.month"] == 7),
        lambda hr: hr["notification.hr"] == "XINGU",
        lambda hr: (
            (hr["notification.hr"] == "TAPAJOS")
            & (hr["notification.year"] == 2015)
            & (hr["notification.month"] == 2)
        ),
    ],
    ids=["whole_month", "whole_region", "single_region_month"],
)
def test_missing_structure_rejected(tmp_path, drop):
    hr = hr_rows()
    write_raw(tmp_path, hr[~drop(hr)])
    with pytest.raises(ValueError, match="missing"):
        load_sivep(tmp_path)


def test_species_absent_in_observed_cell_is_zero(tmp_path):
    hr = hr_rows()
    cell = (hr["notification.hr"] == "MARAJO I") & (hr["notification.year"] == 2011)
    cell &= hr["notification.month"] == 1
    gone = cell & (hr["exam.result"] != "negative")
    write_raw(tmp_path, hr[~gone])
    bundle = load_sivep(tmp_path)
    assert bundle.counts[4, 24] == 0
    assert bundle.tests[4, 24] == hr.loc[cell & ~gone, "testperhr"].sum()
    assert len(bundle.long) == len(hr) - int(gone.sum())


def test_species_labels_preserved(raw_dir):
    long = load_sivep(raw_dir).long
    assert list(long.columns) == ["region", "month", "species", "count"]
    assert set(long["species"]) == {"falciparum", "vivax", "F+FG", "negative"}


def test_unknown_region_and_negative_count_rejected(tmp_path):
    hr = hr_rows()
    hr.loc[0, "notification.hr"] = "AMAZONAS"
    write_raw(tmp_path / "a", hr)
    with pytest.raises(ValueError, match="AMAZONAS"):
        load_sivep(tmp_path / "a")
    hr = hr_rows()
    hr.loc[0, "testperhr"] = -1
    write_raw(tmp_path / "b", hr)
    with pytest.raises(ValueError, match="negative"):
        load_sivep(tmp_path / "b")


def test_arrays_are_read_only(raw_dir):
    bundle = load_sivep(raw_dir)
    for array in (bundle.counts, bundle.state_counts, bundle.tests):
        with pytest.raises(ValueError):
            array[0] = 0


def test_raw_files_unchanged(raw_dir):
    before = _hashes(raw_dir)
    load_sivep(raw_dir)
    prepare(raw_dir, raw_dir.parent / "processed")
    assert _hashes(raw_dir) == before


def test_prepare_outputs_are_deterministic(raw_dir, tmp_path):
    prepare(raw_dir, tmp_path / "one")
    prepare(raw_dir, tmp_path / "two")
    assert _hashes(tmp_path / "one") == _hashes(tmp_path / "two")
    provenance = json.loads((tmp_path / "one/provenance.json").read_text())
    assert provenance["raw_sha256"] == _hashes(raw_dir)
    counts = np.load(tmp_path / "one/counts.npy")
    np.testing.assert_array_equal(counts, load_sivep(raw_dir).counts)


def test_cli_reads_toml(raw_dir, tmp_path):
    config = tmp_path / "data.toml"
    config.write_text(
        f'raw_dir = "{raw_dir}"\n'
        f'processed_dir = "{tmp_path / "processed"}"\n'
        f'results_dir = "{tmp_path / "results"}"\n'
    )
    assert main([str(config)]) == 0
    assert (tmp_path / "processed/counts.npy").exists()
    manifest = json.loads((tmp_path / "results/manifest.json").read_text())
    assert manifest["config"]["raw_dir"] == str(raw_dir)
    assert manifest["provenance"]["raw_sha256"] == _hashes(raw_dir)


def test_cli_missing_raw_dir_fails(tmp_path):
    config = tmp_path / "data.toml"
    config.write_text(
        f'raw_dir = "{tmp_path / "absent"}"\n'
        f'processed_dir = "{tmp_path / "p"}"\n'
        f'results_dir = "{tmp_path / "r"}"\n'
    )
    with pytest.raises(FileNotFoundError, match="absent"):
        main([str(config)])


def _array_hash(value: np.ndarray) -> str:
    arr = np.ascontiguousarray(value)
    head = f"{arr.dtype.str}|{arr.shape}|".encode()
    return hashlib.sha256(head + arr.tobytes()).hexdigest()


@pytest.mark.reference
def test_counts_match_original_exactly():
    """Pinned CDADE export (hash-checked) against the loader on the real CSVs."""
    manifest = json.loads((REFERENCE / "manifest.json").read_text())
    raw = Path(
        os.environ.get("CDADE_RAW_DIR", "/home/vinvs/projects/hybrid-theory/data/raw")
    )
    if not raw.exists():
        pytest.skip("Set CDADE_RAW_DIR to the SIVEP raw CSV directory")
    reference = np.load(REFERENCE / "data.npz")
    for name in reference.files:
        assert _array_hash(reference[name]) == manifest["array_sha256"]["data"][name]
    pinned = manifest["raw_data_sha256"]
    assert {
        n: hashlib.sha256((raw / n).read_bytes()).hexdigest() for n in pinned
    } == pinned
    bundle = load_sivep(raw)
    np.testing.assert_array_equal(bundle.counts.T, reference["counts"])
    np.testing.assert_array_equal(bundle.state_counts, reference["state"])
    np.testing.assert_array_equal(
        bundle.tests.sum(axis=0), reference["state_total_tests"]
    )
    assert bundle.hierarchy.leaves == tuple(reference["leaves"])
    assert list(bundle.months.strftime("%Y-%m-%d")) == list(reference["dates"])
