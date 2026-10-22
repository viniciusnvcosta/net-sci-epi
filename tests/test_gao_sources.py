"""Read-only source verification against independent synthetic archived tables."""

import json
import warnings
from hashlib import sha256
from pathlib import Path
from zipfile import ZipFile

import pytest

from headd_l0.gao_sources import verify_sources

REFERENCE = Path(__file__).parent / "reference"
PAIRS = {
    "white": {"AR1": {"T": 0.6, "N": 0.2}, "CV": {"T": 0.5, "N": 0.9}},
    "env": {"AR1": {"T": 0.7, "N": -0.1}, "CV": {"T": 0.8, "N": 0.4}},
    "dem": {"AR1": {"T": 0.8, "N": 0.1}, "CV": {"T": 1.2, "N": 0.6}},
}


@pytest.fixture
def sources(tmp_path):
    manifest = json.loads((REFERENCE / "gao_manifest.json").read_text())
    manifest["fixture"]["path"] = str((REFERENCE / "gao_single.npz").resolve())
    payloads = {}
    for noise, pairs in PAIRS.items():
        table = manifest["archived_characterization"]["tables"][noise]
        table.update(pairs)
        # Half of each class lies below its median and half above, so using
        # a single middle row, ignoring the N half, or scaling CV is detectable.
        rows = ["AR1,CV"]
        for label in ("T", "N"):
            for offset in (-0.02, 0.02):
                rows.extend(
                    [f"{pairs['AR1'][label] + offset},{pairs['CV'][label] + offset}"]
                    * 3000
                )
        payloads[noise] = ("\n".join(rows) + "\n").encode()
    archive = tmp_path / "Code.zip"
    supplement = tmp_path / "supplement.pdf"
    supplement.write_bytes(b"%PDF-1.4\nsynthetic supplement\n%%EOF\n")
    manifest["sources"]["supplement"]["sha256"] = sha256(
        supplement.read_bytes()
    ).hexdigest()
    path = tmp_path / "manifest.json"

    def publish(*, omit=None, duplicate=None, pin_members=True):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            with ZipFile(archive, "w") as zipped:
                for noise, payload in payloads.items():
                    table = manifest["archived_characterization"]["tables"][noise]
                    if pin_members:
                        table["sha256"] = sha256(payload).hexdigest()
                    if noise != omit:
                        zipped.writestr(table["path"], payload)
                    if noise == duplicate:
                        zipped.writestr(table["path"], payload)
        manifest["sources"]["archive"]["sha256"] = sha256(
            archive.read_bytes()
        ).hexdigest()
        path.write_text(json.dumps(manifest))

    publish()
    return archive, supplement, path, manifest, payloads, publish


def test_absent_sources_remain_pending(sources, tmp_path):
    archive, supplement, manifest, *_ = sources
    missing = verify_sources(tmp_path / "absent.zip", tmp_path / "absent.pdf", manifest)
    assert missing["status"] == "pending"
    assert missing["source_archive_verification"] == "pending"
    assert missing["archive"]["status"] == "pending"
    assert missing["equation_fixture"]["status"] == "passed"
    assert missing["tables"]["white"].get("AR1") is None
    partial = verify_sources(archive, tmp_path / "absent.pdf", manifest)
    assert partial["archive"]["status"] == "passed"
    assert partial["source_archive_verification"] == "pending"
    assert partial["status"] == "pending"
    inverse = verify_sources(tmp_path / "absent.zip", supplement, manifest)
    assert inverse["supplement"]["status"] == "passed"
    assert inverse["status"] == "pending"


@pytest.mark.parametrize("component", ["archive", "supplement", "white", "env", "dem"])
def test_hash_mismatch_fails_before_characterization(sources, component):
    archive, supplement, path, _, payloads, publish = sources
    if component in payloads:
        payloads[component] = b"not a valid CSV"
        publish(pin_members=False)
    else:
        target = archive if component == "archive" else supplement
        target.write_bytes(b"mismatched bytes")
    result = verify_sources(archive, supplement, path)
    assert result["status"] == "failed"
    check = result["tables"][component] if component in payloads else result[component]
    assert check["status"] == "failed"
    assert check["observed_sha256"] != check["expected_sha256"]
    assert check.get("AR1") is None
    assert any("hash" in reason.lower() for reason in check["reasons"])
    if component == "supplement":
        assert result["archive"]["status"] == "passed"
    if component == "archive":
        assert result["tables"]["white"].get("AR1") is None


def test_complete_sources_preserve_archived_label_directions(sources):
    archive, supplement, path, *_ = sources
    verified = verify_sources(archive, supplement, path)
    assert verified["status"] == "passed"
    assert verified["source_archive_verification"] == "passed"
    assert verified["G4"] == "pending"
    assert verified["interpretation_allowed"] is False
    assert verified["labels"]["T"] == {"first_row_1based": 1, "last_row_1based": 6000}
    for noise, pairs in PAIRS.items():
        table = verified["tables"][noise]
        assert table["rows"] == 12000
        assert table["status"] == "passed"
        for feature, expected in pairs.items():
            assert table[feature]["T"] == pytest.approx(expected["T"], abs=1e-15)
            assert table[feature]["N"] == pytest.approx(expected["N"], abs=1e-15)
            assert table[feature]["within_tolerance"] is True
            assert table[feature]["direction"]["passed"] is True
    assert (
        verified["tables"]["white"]["CV"]["T"] < verified["tables"]["white"]["CV"]["N"]
    )
    assert verified["tables"]["env"]["CV"]["T"] > verified["tables"]["env"]["CV"]["N"]
    json.dumps(verified, allow_nan=False)


@pytest.mark.parametrize(
    "defect",
    ["truncated", "missing", "duplicate", "rows", "AR1", "CV", "nan", "inf", "median"],
)
def test_bad_table_members_rows_or_values_fail(sources, defect):
    archive, supplement, path, manifest, payloads, publish = sources
    if defect in {"missing", "duplicate"}:
        publish(**{"omit" if defect == "missing" else "duplicate": "white"})
    elif defect == "truncated":
        archive.write_bytes(b"PK\x03\x04truncated")
        manifest["sources"]["archive"]["sha256"] = sha256(
            archive.read_bytes()
        ).hexdigest()
        path.write_text(json.dumps(manifest))
    else:
        rows = payloads["white"].decode().splitlines()
        if defect == "rows":
            rows.pop()
        elif defect in {"AR1", "CV"}:
            rows[0] = rows[0].replace(defect, "OTHER")
        elif defect in {"nan", "inf"}:
            rows[1] = f"{defect},0.5"
        else:
            # A 2e-12 error fails the absolute pin despite tiny relative error.
            rows[1:6001] = [
                f"{row.split(',')[0]},0.500000000002" for row in rows[1:6001]
            ]
        payloads["white"] = ("\n".join(rows) + "\n").encode()
        publish()
    result = verify_sources(archive, supplement, path)
    assert result["status"] == "failed"
    assert result["archive"]["status"] == "failed"
    assert result["archive"]["reasons"] or result["tables"]["white"]["reasons"]
    if defect != "truncated":
        assert result["tables"]["white"]["status"] == "failed"
    json.dumps(result, allow_nan=False)


def test_reversed_halves_fail_expected_medians(sources):
    archive, supplement, path, _, payloads, publish = sources
    rows = payloads["env"].decode().splitlines()
    payloads["env"] = (
        "\n".join([rows[0], *rows[6001:], *rows[1:6001]]) + "\n"
    ).encode()
    publish()
    result = verify_sources(archive, supplement, path)
    assert result["status"] == "failed"
    assert result["tables"]["env"]["AR1"]["T"] == pytest.approx(-0.1)
    assert result["tables"]["env"]["CV"]["direction"]["passed"] is False
    assert result["tables"]["env"]["AR1"]["within_tolerance"] is False


@pytest.mark.parametrize("missing", [False, True])
def test_equation_fixture_hash_is_independent(sources, tmp_path, missing):
    archive, supplement, path, manifest, *_ = sources
    fixture = tmp_path / "equation.npz"
    if not missing:
        fixture.write_bytes(b"not the equation fixture")
    manifest["fixture"]["path"] = str(fixture)
    path.write_text(json.dumps(manifest))
    result = verify_sources(archive, supplement, path)
    assert result["archive"]["status"] == "passed"
    assert result["source_archive_verification"] == "passed"
    assert result["equation_fixture"]["status"] == ("pending" if missing else "failed")
    assert result["status"] == ("pending" if missing else "failed")


def test_source_read_is_immutable(sources):
    archive, supplement, path, manifest, *_ = sources
    paths = [archive, supplement, path, Path(manifest["fixture"]["path"])]
    before = {p: (p.read_bytes(), p.stat().st_mtime_ns) for p in paths}
    directory_before = set(path.parent.iterdir())
    assert verify_sources(archive, supplement, path)["status"] == "passed"
    assert {p: (p.read_bytes(), p.stat().st_mtime_ns) for p in paths} == before
    assert set(path.parent.iterdir()) == directory_before


def test_manifest_is_required_contract(sources, tmp_path):
    archive, supplement, *_ = sources
    with pytest.raises(FileNotFoundError):
        verify_sources(archive, supplement, tmp_path / "missing.json")
    invalid = tmp_path / "invalid.json"
    invalid.write_text("not JSON")
    with pytest.raises(json.JSONDecodeError):
        verify_sources(archive, supplement, invalid)
