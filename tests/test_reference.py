"""Audit contracts: committed sources, real subprocess failures, honest E0 gate."""

import hashlib
import json
import os
import subprocess
import sys
import tarfile
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/export_cdade_reference.py"


def _git(repo, *args):
    return subprocess.check_output(["git", "-C", str(repo), *args], text=True).strip()


@pytest.fixture
def audit(tmp_path):
    repo = tmp_path / "original"
    repo.mkdir()
    _git(repo, "init", "-q")
    (repo / "configs/dataset").mkdir(parents=True)
    (repo / "configs/dataset/sivep.yaml").write_text("dataset:\n  name: sivep\n")
    (repo / "cdade").mkdir()
    (repo / "cdade/__init__.py").write_text('raise RuntimeError("committed failure")\n')
    (repo / "tracked.txt").write_bytes(b"committed bytes\n")
    _git(repo, "add", ".")
    _git(
        repo,
        "-c",
        "user.name=Test",
        "-c",
        "user.email=test@example.org",
        "commit",
        "-qm",
        "fixture",
    )
    revision = _git(repo, "rev-parse", "HEAD")
    (repo / "tracked.txt").write_bytes(b"dirty bytes\n")
    (repo / "cdade/__init__.py").write_text('raise RuntimeError("dirty failure")\n')
    before = _git(repo, "status", "--porcelain")
    output = tmp_path / "audit"
    completed = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--repo",
            str(repo),
            "--revision",
            revision,
            "--output",
            str(output),
            "--python",
            sys.executable,
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    return repo, revision, output, completed, before


def _report(audit):
    report = audit[2] / "reference_audit.json"
    assert report.exists(), audit[3].stderr
    return json.loads(report.read_text())


def test_export_uses_commit_not_dirty_tree(audit):
    """Copying the working tree instead of git archive must fail this check."""
    report = _report(audit)
    with tarfile.open(audit[2] / "source.tar") as archive:
        assert archive.extractfile("tracked.txt").read() == b"committed bytes\n"
    assert report["revision"] == audit[1]
    assert (
        report["source_hashes"]["tracked.txt"]
        == hashlib.sha256(b"committed bytes\n").hexdigest()
    )
    assert (audit[0] / "tracked.txt").read_bytes() == b"dirty bytes\n"
    assert _git(audit[0], "status", "--porcelain") == audit[4]


def test_missing_tasks_blocks_reference(audit):
    """A dataset name cannot certify the 14 region/aggregate tasks."""
    report = _report(audit)
    assert report["task_names"] == ["sivep"]
    assert audit[3].returncode == 2
    assert "missing_14_tasks" in report["blocking_findings"]
    assert report["e0_passed"] is False


def test_captures_actual_snapshot_exception(audit):
    """Swallowing worker errors or importing dirty sources loses this evidence."""
    report = _report(audit)
    failure = next(e for e in report["exceptions"] if e["stage"] == "import_reference")
    assert failure["type"] == "RuntimeError"
    assert failure["message"] == "committed failure"
    assert "cdade/__init__.py" in failure["traceback"]
    assert "worker_failed" in report["blocking_findings"]


@pytest.mark.reference
@pytest.mark.integration
def test_pinned_reference_exports_arrays_and_runtime_failure(tmp_path):
    """Run the real snapshot; fabricated arrays or an unobserved EVT error fail."""
    import numpy as np

    repo = Path(
        os.environ.get("CDADE_REFERENCE_REPO", "/home/vinvs/projects/hybrid-theory")
    )
    if not (repo / ".venv/bin/python").exists():
        pytest.skip(
            "Set CDADE_REFERENCE_REPO to the pinned source with legacy interpreter"
        )
    output = tmp_path / "audit"
    completed = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--repo",
            str(repo),
            "--revision",
            "fbfa609bba6cb0b0f2a9e8d73be18022aec319b7",
            "--output",
            str(output),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert (output / "reference_audit.json").exists(), completed.stderr
    report = json.loads((output / "reference_audit.json").read_text())
    assert completed.returncode == 2
    assert report["immutability"]["unchanged"]
    arrays = np.load(output / "fixtures/data.npz")
    assert arrays["counts"].shape == (132, 13)
    np.testing.assert_array_equal(arrays["counts"].sum(axis=1), arrays["state"])
    assert arrays["leaves"].shape == (13,)
    assert any(
        e["stage"] == "evt" and e["type"] == "ValueError" for e in report["exceptions"]
    )
    assert report["environment"]["imported_from_snapshot"]
    assert report["environment"]["numpy_blas"]
    assert report["task_names"] == ["sivep"]
    assert report["outputs"]["data"]["seed"] is None
    for component in report["outputs"].values():
        path = output / component["path"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == component["sha256"]
