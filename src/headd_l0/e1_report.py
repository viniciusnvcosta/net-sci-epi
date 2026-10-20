"""Export preserved E1 evidence, keeping scientific gates separate from diagnostics."""

import argparse
import hashlib
import json
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd

from headd_l0.data import hierarchy
from headd_l0.stats import primary_analysis


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _verify(run: Path, manifest: dict) -> None:
    if type(manifest.get("interpretation_allowed")) is not bool or not manifest.get(
        "gates"
    ):
        raise ValueError("manifest requires interpretation_allowed and gates")
    for name, digest in manifest.get("artifact_sha256", {}).items():
        path = run / name
        if path.parent != run or not path.is_file() or _digest(path) != digest:
            raise ValueError(f"artifact hash mismatch: {name}")
    # Envelope inventories include historical source/config hashes. Revalidate
    # preserved results only: the current checkout may legitimately have changed.
    root = Path(__file__).resolve().parents[2]
    for name, record in manifest.get("artifact_inventory", {}).items():
        if Path(name).parts[0] == "results":
            path = root / name
            if not path.is_file() or _digest(path) != record["sha256"]:
                raise ValueError(f"artifact hash mismatch: {name}")


def _blockers(run: Path, manifest: dict) -> list[str]:
    reasons = []
    if not manifest["interpretation_allowed"]:
        reasons.append("interpretation_allowed=false")
    for gate in ("E0_star", "G4", "scientific_ratification", "D5", "FAR", "D_REACH"):
        status = manifest["gates"].get(gate, {}).get("status", "not_evaluated")
        if status != "passed":
            reasons.append(f"{gate}={status}")
    cfg = manifest.get("config", {})
    if cfg.get("name") != "e1_bench" or manifest["status"] != "completed":
        reasons.append("bench=not_executed_or_technical_only")
    if reasons:
        return reasons
    reach = pd.DataFrame(manifest["gates"]["D_REACH"].get("cells", []))
    high = reach.loc[reach.epsilon == 0.2] if not reach.empty else reach
    if (
        high.empty
        or set(high.noise) != set(cfg["noise_types"])
        or high.noise.duplicated().any()
        or not high.n.eq(200).all()
        or not high.fraction.ge(0.5).all()
        or not np.allclose(high.fraction, high.reached / high.n, rtol=0, atol=1e-15)
    ):
        reasons.append("D_REACH=insufficient_power_or_incomplete")
    if (
        cfg["n_transition"],
        cfg["n_null"],
        cfg["n_calibration"],
        cfg.get("n_placebo_transition_per_cell"),
    ) != (200, 200, 200, 100) or manifest.get("budget_policy", {}).get(
        "placebo_transition_indices"
    ) != list(range(100)):
        reasons.append("D_COST=unmatched_design")
    if (
        not {"comparisons.parquet", "far.parquet"}
        <= manifest.get("artifact_sha256", {}).keys()
    ):
        reasons.append("inference_artifacts=unverified")
        return reasons
    comparisons = pd.read_parquet(run / "comparisons.parquet")
    expected_cells = {
        (noise, epsilon)
        for noise in cfg["noise_types"]
        for epsilon in cfg["epsilon_levels"]
    }
    if (
        set(comparisons[["noise", "epsilon"]].itertuples(index=False, name=None))
        != expected_cells
    ):
        reasons.append("primary=incomplete_strata")
    far = pd.read_parquet(run / "far.parquet")
    keys = ["noise", "epsilon", "arm", "task"]
    arms = ["B0", "B1*", "B2", *(f"B2-placebo-{p:02d}" for p in range(30))]
    expected = {
        (noise, epsilon, arm, task)
        for noise in cfg["noise_types"]
        for epsilon in cfg["epsilon_levels"]
        for arm in arms
        for task in hierarchy().leaves
    }
    if (
        far.duplicated(keys).any()
        or set(far[keys].itertuples(index=False, name=None)) != expected
        or not far.passed.eq(True).all()
        or not far.complete.eq(True).all()
        or not far.target_far.eq(1 / 60).all()
        or not far.tolerance.eq(1 / 300).all()
        or not far.calibration_n.eq(cfg["n_calibration"] * 72).all()
        or not far.n.eq(cfg["n_null"] * 72).all()
        or not np.isfinite(far.observed_far).all()
        or not (far.observed_far.sub(1 / 60).abs() <= 1 / 300).all()
    ):
        reasons.append("FAR=not_comparable")
    return reasons


def export_report(run_dir: Path) -> int:
    """Persist descriptive tables, figures and limitations before checking exit code.

    Args:
        run_dir: Preserved runner or blocked execution-envelope directory.

    Returns:
        2 when interpretation is blocked; 0 only for authorized inference.
        A fresh report directory is required; source artifacts are immutable.
    """
    run = Path(run_dir).resolve()
    source = run / "manifest.json"
    manifest = json.loads(source.read_text())
    _verify(run, manifest)
    reasons = _blockers(run, manifest)
    allowed = not reasons
    report = run / "report"
    report.mkdir(exist_ok=False)
    gates = pd.DataFrame(
        [
            {
                "gate": name,
                "status": value["status"],
                "details": json.dumps(value, sort_keys=True),
                "interpretation_allowed": allowed,
            }
            for name, value in manifest["gates"].items()
        ]
    )
    gates.to_parquet(report / "gates.parquet", index=False)
    sizes = pd.DataFrame(manifest.get("effective_sizes", []))
    sizes["interpretation_allowed"] = allowed
    sizes.to_parquet(report / "effective_sizes.parquet", index=False)
    reach = pd.DataFrame(manifest["gates"].get("D_REACH", {}).get("cells", []))
    reach["interpretation_allowed"] = allowed
    reach.to_parquet(report / "reach.parquet", index=False)
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt  # noqa: PLC0415

    fig, ax = plt.subplots(figsize=(7, 3))
    if not reach.empty:
        for noise, rows in reach.groupby("noise", sort=True):
            ax.plot(rows.epsilon, rows.fraction, "o-", label=noise)
        ax.legend()
        ax.set(xlabel="epsilon", ylabel="Neighbor onset fraction", ylim=(0, 1))
    else:
        counts = gates.status.value_counts()
        ax.bar(counts.index, counts.values)
        ax.set(ylabel="Technical gates")
    qualifier = "DESCRIPTIVE" + (" — NOT INTERPRETABLE" if not allowed else "")
    ax.set_title(f"{qualifier}: reach/gate diagnostics")
    fig.tight_layout()
    fig.savefig(report / "reach.png")
    plt.close(fig)
    limitations = (
        f"# E1 preliminary report — {qualifier}\n\n"
        "E0 is inconclusive. B1* is the corrected baseline, not CDADE v1 parity.\n"
        f"Source status: {manifest.get('status')}; bench: {manifest.get('bench', {}).get('status', 'technical_run')}.\n"
        f"Interpretation allowed: {allowed}. Blocking gates: {', '.join(reasons) or 'none'}.\n"
        "Smoke and D-REACH describe technical checks, not scientific detection effects.\n"
        "D-COST: B2/B1* uses 200 T/cell; B2/placebos uses the same fixed T0000–T0099 (100 T).\n"
        "Inactive arms are omitted; they are not failures, missing scores or censored detections.\n"
        "Censored misses retain restricted leads; onset -1 has no timing denominator.\n"
        "Epsilon-zero equivalence is not ratified; a CI containing zero does not establish equivalence.\n"
        "The 82–105 hour bench was not executed by this exporter.\n"
    )
    (report / "limitations.md").write_text(limitations)
    if allowed:
        cfg = manifest["config"]
        seed = manifest["seeds"]["bootstrap"]
        rng = np.random.default_rng(
            np.random.SeedSequence(seed["entropy"], spawn_key=tuple(seed["spawn_key"]))
        )
        inference = primary_analysis(
            pd.read_parquet(run / "comparisons.parquet"),
            rng,
            n_transition=cfg["n_transition"],
            n_placebo_transition=cfg["n_placebo_transition_per_cell"],
        )
        (report / "inference.json").write_text(
            json.dumps(inference, indent=2, allow_nan=False) + "\n"
        )
    output = {
        "source_manifest_sha256": _digest(source),
        "source_git_sha": manifest.get("git_sha"),
        "interpretation_allowed": allowed,
        "blocking_reasons": reasons,
        "artifact_sha256": {p.name: _digest(p) for p in sorted(report.iterdir())},
    }
    (report / "manifest.json").write_text(
        json.dumps(output, indent=2, allow_nan=False) + "\n"
    )
    print(
        f"Report: {report}; "
        + (
            "authorized inference"
            if allowed
            else "interpretation blocked; descriptive only"
        )
    )
    return 0 if allowed else 2


def main() -> int:
    """Export E1 evidence without running simulations or changing the source manifest."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_dir", type=Path)
    return export_report(parser.parse_args().run_dir)


if __name__ == "__main__":
    raise SystemExit(main())
