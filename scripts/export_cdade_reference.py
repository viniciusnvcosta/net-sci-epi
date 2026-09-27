# ABOUTME: Exports a pinned CDADE revision with git archive and audits it in the legacy interpreter.
# ABOUTME: Writes reference_audit.json; exit 2 means the reference cannot support the E0 gate.
"""Pinned-reference audit for the E0 parity gate.

The source always comes from ``git archive <revision>``, never from the working
tree. The original repository and its interpreter are only read: the snapshot
and the raw CSV copies live in a temporary directory, and the worker runs with
bytecode and caches redirected there. Exit code 2 reports an insufficient
reference; exit code 0 still does not pass E0, which needs the rebuilt B1.
"""

import argparse
import hashlib
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

WORKER = Path(__file__).with_name("_reference_worker.py")
LEAVES = (
    "ARAGUAIA", "BAIXO AMAZONAS", "CARAJAS", "LAGO DE TUCURUI", "MARAJO I", "MARAJO II",
    "METROPOLITANA I", "METROPOLITANA II", "METROPOLITANA III", "RIO CAETES", "TAPAJOS",
    "TOCANTINS", "XINGU",
)  # fmt: skip
REQUIRED_TASKS = ("PA", *LEAVES)
RAW_FILES = ("PA.csv", "PASIVEPDailyPerHr.csv")
LOCAL_ARTIFACTS = (
    "results/metrics/sivep/metrics.json",
    "data/processed/sivep_counts.parquet",
    "data/injected/sivep_counts_injected.parquet",
    "data/injected/sivep_counts_mask.parquet",
)
LOCKED = (
    "numpy",
    "pandas",
    "scipy",
    "scikit-learn",
    "pyod",
    "river",
    "hydra-core",
    "pyarrow",
)
# Spec §3 divergence -> (static source locations, runtime evidence keys, exception stage prefixes)
DIVERGENCES = {
    "D1": ([("cdade/detectors/run_detect.py", "detector.fit(data)")], ["reconcile"],
           ["pipeline_detect"]),
    "D2": ([("cdade/reconciliation/min_t.py", "np.zeros((n_leaves, n_leaves)")], [],
           ["pipeline_reconcile"]),
    "D3": ([("cdade/detectors/mcd.py", "subset_size = min(10"),
            ("cdade/detectors/pca.py", "-self.model.decision_function")], ["detectors"],
           ["detector_", "pipeline_detect_mcd"]),
    "D4": ([("cdade/reconciliation/evt.py", "self.scale, self.shape = genpareto.fit")], [],
           ["evt"]),
    "D5": ([("cdade/reconciliation/run_reconcile.py", '"leaf_forecasts.csv"')], ["reconcile"],
           []),
    "D6": ([("cdade/selection/run_select.py", "w_idx = min(t // stride")], ["select_lookahead"],
           ["select_lookahead"]),
    "D7": ([("cdade/evaluation/run_evaluate.py", "max(axis=1)")], ["evaluate"],
           ["pipeline_evaluate"]),
    "D8": ([("cdade/evaluation/stats.py", "np.random.RandomState")], ["stats"], ["stats"]),
    "D9": ([("cdade/evaluation/metrics.py", "threshold = np.median(scores)")], [], ["metrics"]),
}  # fmt: skip


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git(repo: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(repo), *args], text=True).strip()


def repo_state(repo: Path, raw_dir: Path) -> dict:
    """Capture what must stay unchanged: HEAD, working-tree status and raw bytes."""
    return {
        "revision": git(repo, "rev-parse", "HEAD"),
        "status": git(repo, "status", "--porcelain"),
        "raw_hashes": raw_hashes(raw_dir),
    }


def raw_hashes(raw_dir: Path) -> dict[str, str]:
    return {
        n: sha256((raw_dir / n).read_bytes())
        for n in RAW_FILES
        if (raw_dir / n).exists()
    }


def export_snapshot(
    repo: Path, revision: str, output: Path, snapshot: Path
) -> dict[str, str]:
    """Write ``source.tar`` for the pinned revision, unpack it and hash every member."""
    archive = output / "source.tar"
    subprocess.run(["git", "-C", str(repo), "archive", "--format=tar", "-o", str(archive),
                    revision], check=True)  # fmt: skip
    hashes = {}
    with tarfile.open(archive) as tar:
        for member in tar.getmembers():
            if member.isfile():
                hashes[member.name] = sha256(tar.extractfile(member).read())
        tar.extractall(snapshot, filter="data")
    return hashes


def lock_versions(snapshot: Path) -> dict[str, list[str]]:
    lock = snapshot / "uv.lock"
    if not lock.exists():
        return {}
    pairs = re.findall(
        r'\[\[package\]\]\nname = "([^"]+)"\nversion = "([^"]+)"', lock.read_text()
    )
    found: dict[str, list[str]] = {}
    for name, version in pairs:
        if name in LOCKED:
            found.setdefault(name, []).append(version)
    return found


def run_worker(
    python: str, snapshot: Path, scratch: Path, fixtures: Path, log: Path
) -> dict:
    """Run the worker on the snapshot with bytecode and caches kept out of the original."""
    env = {
        **os.environ,
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONNOUSERSITE": "1",
        "PYTHONPATH": str(snapshot),
        "MPLCONFIGDIR": str(scratch / "mpl"),
        "NUMBA_CACHE_DIR": str(scratch / "numba"),
        "XDG_CACHE_HOME": str(scratch / "cache"),
        "HYDRA_FULL_ERROR": "1",
    }
    command = [python, "-B", "-s", str(WORKER), "--snapshot", str(snapshot), "--raw-dir",
               str(snapshot / "data/raw"), "--out", str(fixtures), "--log", str(log)]  # fmt: skip
    done = subprocess.run(
        command, env=env, cwd=scratch, capture_output=True, text=True, check=False
    )
    result = json.loads(log.read_text()) if log.exists() else {"exceptions": []}
    result["returncode"] = done.returncode
    result["stderr_tail"] = done.stderr[-4000:]
    return result


def task_names(snapshot: Path, worker: dict) -> tuple[list[str], str]:
    """Evaluation units: observed at runtime, else the dataset name the pipeline evaluates."""
    if worker.get("task_names"):
        return worker["task_names"], "runtime:pipeline_evaluate"
    config = snapshot / "configs/dataset/sivep.yaml"
    names = (
        re.findall(r"^\s*name:\s*(\S+)", config.read_text(), re.MULTILINE)
        if config.exists()
        else []
    )
    return names, "static:configs/dataset/sivep.yaml (one metrics table per dataset)"


def divergences(snapshot: Path, worker: dict) -> dict:
    """Pair each spec divergence with its source line and any runtime evidence."""
    report = {}
    for key, (patterns, evidence_keys, stages) in DIVERGENCES.items():
        locations = []
        for relative, pattern in patterns:
            path = snapshot / relative
            lines = path.read_text().splitlines() if path.exists() else []
            locations += [
                f"{relative}:{i}" for i, line in enumerate(lines, 1) if pattern in line
            ]
        evidence = {k: worker.get("evidence", {}).get(k) for k in evidence_keys}
        errors = [f"{e['stage']}: {e['type']}: {e['message']}" for e in worker["exceptions"]
                  if any(e["stage"].startswith(s) for s in stages)]  # fmt: skip
        observed = errors or any(v is not None for v in evidence.values())
        status = "runtime" if observed else ("static" if locations else "not_found")
        report[key] = {"status": status, "locations": locations, "evidence": evidence,
                       "exceptions": errors}  # fmt: skip
    return report


def blocking(worker: dict, names: list[str], unchanged: bool) -> list[str]:
    findings = []
    stages = [e["stage"] for e in worker["exceptions"]]
    if worker["returncode"] != 0 or "import_reference" in stages:
        findings.append("worker_failed")
    elif not worker.get("environment", {}).get("imported_from_snapshot"):
        findings.append("imported_outside_snapshot")
    if sorted(names) != sorted(REQUIRED_TASKS):
        findings.append("missing_14_tasks")
    findings += [f"stage_failed:{s}" for s in stages if s.startswith("pipeline_")]
    rate = worker.get("evidence", {}).get("evaluate", {}).get("test_positive_rate")
    if rate in (
        0.0,
        1.0,
    ):  # AP is constant for single-class labels, so ranks are all ties
        findings.append("single_class_test_labels")
    if not unchanged:
        findings.append("original_changed_during_audit")
    return findings


def audit(repo: Path, revision: str, output: Path, python: str, raw_dir: Path) -> dict:
    output.mkdir(parents=True, exist_ok=True)
    before = repo_state(repo, raw_dir)
    pinned = git(repo, "rev-parse", "--verify", f"{revision}^0")
    with tempfile.TemporaryDirectory(prefix="cdade-reference-") as tmp:
        scratch, snapshot = Path(tmp), Path(tmp) / "snapshot"
        snapshot.mkdir()
        sources = export_snapshot(repo, pinned, output, snapshot)
        (snapshot / "data/raw").mkdir(parents=True, exist_ok=True)
        for name in RAW_FILES:
            if (raw_dir / name).exists():
                shutil.copy2(raw_dir / name, snapshot / "data/raw" / name)
        worker = run_worker(
            python, snapshot, scratch, output / "fixtures", output / "worker.json"
        )
        names, names_source = task_names(snapshot, worker)
        divergence = divergences(snapshot, worker)
        locked = lock_versions(snapshot)
    after = repo_state(repo, raw_dir)
    installed = worker.get("environment", {}).get("packages", {})
    outputs = worker.get("outputs", {})
    for entry in outputs.values():
        entry["sha256"] = sha256((output / entry["path"]).read_bytes())
    exceptions = list(worker["exceptions"])
    if worker["returncode"] != 0:
        exceptions.append({"stage": "worker", "type": "ExitCode",
                           "message": str(worker["returncode"]),
                           "traceback": worker["stderr_tail"]})  # fmt: skip
    unchanged = before == after
    report = {
        "revision": pinned,
        "source_hashes": sources,
        "environment": {
            **worker.get("environment", {}),
            "exporter_python": platform.python_version(),
            "reference_interpreter": python,
            "lock_versions": locked,
            "lock_mismatches": {
                n: v
                for n, v in installed.items()
                if locked.get(n) and v not in locked[n]
            },
            "isolation": "git archive snapshot; PYTHONDONTWRITEBYTECODE; caches in tempdir",
        },
        "data_hashes": before["raw_hashes"],
        "local_artifacts": {
            "role": "clues only, never goldens",
            "sha256": {
                p: sha256((repo / p).read_bytes())
                for p in LOCAL_ARTIFACTS
                if (repo / p).exists()
            },
        },
        "outputs": outputs,
        "exceptions": exceptions,
        "evidence": worker.get("evidence", {}),
        "divergences": divergence,
        "task_names": names,
        "task_names_source": names_source,
        "required_tasks": list(REQUIRED_TASKS),
        "immutability": {"before": before, "after": after, "unchanged": unchanged},
        "blocking_findings": blocking(worker, names, unchanged),
        "e0_passed": False,  # this audit never evaluates the rebuilt B1
    }
    (output / "reference_audit.json").write_text(json.dumps(report, indent=2) + "\n")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--revision", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--python", help="reference interpreter (default: <repo>/.venv)"
    )
    parser.add_argument(
        "--raw-dir", type=Path, help="raw CSV directory (default: <repo>/data/raw)"
    )
    args = parser.parse_args()
    repo = args.repo.resolve()
    python = args.python or str(repo / ".venv/bin/python")
    report = audit(repo, args.revision, args.output.resolve(), python,
                   args.raw_dir or repo / "data/raw")  # fmt: skip
    for finding in report["blocking_findings"]:
        print(f"blocking: {finding}", file=sys.stderr)
    return 2 if report["blocking_findings"] else 0


if __name__ == "__main__":
    sys.exit(main())
