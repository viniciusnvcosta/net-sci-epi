"""Read-only verification of frozen Gao external source evidence."""

import csv
import io
import json
import math
import statistics
from hashlib import sha256
from pathlib import Path
from zipfile import BadZipFile, ZipFile


def _status(checks: list[dict]) -> str:
    statuses = [check["status"] for check in checks]
    if "failed" in statuses:
        return "failed"
    return "passed" if all(value == "passed" for value in statuses) else "pending"


def _file_check(path: Path, expected: str) -> dict:
    result = {
        "path": str(path.resolve()),
        "status": "pending",
        "expected_sha256": expected,
        "observed_sha256": None,
        "reasons": [],
    }
    try:
        with path.open("rb") as source:
            digest = sha256()
            for block in iter(lambda: source.read(1024 * 1024), b""):
                digest.update(block)
        result["observed_sha256"] = digest.hexdigest()
    except FileNotFoundError:
        result["reasons"].append("File is absent; bytes have not been verified")
        return result
    except OSError as error:
        result["status"] = "failed"
        result["reasons"].append(f"Cannot read supplied file: {error}")
        return result
    result["status"] = "passed" if result["observed_sha256"] == expected else "failed"
    if result["status"] == "failed":
        result["reasons"].append("SHA-256 hash mismatch")
    return result


def _table_check(payload: bytes, expected: dict, characterization: dict) -> dict:
    result = {
        "path": expected["path"],
        "status": "failed",
        "expected_sha256": expected["sha256"],
        "observed_sha256": sha256(payload).hexdigest(),
        "expected_rows": characterization["rows"],
        "rows": None,
        "reasons": [],
    }
    if result["observed_sha256"] != expected["sha256"]:
        result["reasons"].append("Table SHA-256 hash mismatch")
        return result
    try:
        reader = csv.DictReader(io.StringIO(payload.decode("utf-8")), strict=True)
        if any((reader.fieldnames or []).count(key) != 1 for key in ("AR1", "CV")):
            raise ValueError("Table must contain exactly one AR1 and one CV column")
        rows = list(reader)
        result["rows"] = len(rows)
        if len(rows) != characterization["rows"]:
            raise ValueError("Table row count does not match declared characterization")
        values = {key: [float(row[key]) for row in rows] for key in ("AR1", "CV")}
        if not all(
            math.isfinite(value) for column in values.values() for value in column
        ):
            raise ValueError(
                "Nonfinite AR1/CV values cannot be dropped or characterized"
            )
    except (UnicodeError, csv.Error, ValueError, TypeError) as error:
        result["reasons"].append(f"Invalid source table: {error}")
        return result

    tolerance = characterization["median_tolerance"]
    for feature, column in values.items():
        medians = {
            label: float(
                statistics.median(
                    column[bounds["first_row_1based"] - 1 : bounds["last_row_1based"]]
                )
            )
            for label, bounds in characterization["labels"].items()
        }
        within_tolerance = all(
            abs(medians[label] - expected[feature][label]) <= tolerance
            for label in ("T", "N")
        )
        # The frozen expected pair declares the archived direction, including
        # white CV(T)<CV(N); preserve it rather than imposing all-noise CV>.
        increasing = expected[feature]["T"] > expected[feature]["N"]
        direction_passed = (
            medians["T"] > medians["N"] if increasing else medians["T"] < medians["N"]
        )
        result[feature] = {
            **medians,
            "expected": expected[feature],
            "absolute_tolerance": tolerance,
            "within_tolerance": within_tolerance,
            "direction": {
                "expected": "T > N" if increasing else "T < N",
                "passed": direction_passed,
            },
        }
        if not within_tolerance:
            result["reasons"].append(f"{feature} medians exceed absolute tolerance")
        if not direction_passed:
            result["reasons"].append(
                f"{feature} archived T/N direction is not preserved"
            )
    result["status"] = "failed" if result["reasons"] else "passed"
    return result


def verify_sources(archive: Path, supplement: Path, manifest: Path) -> dict:
    """Verify pinned source bytes and archived medians without writes or network.

    Args:
        archive: Official Code.zip path, resolved from the execution directory.
        supplement: Official supplement PDF path.
        manifest: Required frozen JSON contract; fixture.path is resolved from
            the execution directory, as are the other supplied relative paths.

    Returns:
        Strict-JSON-compatible component evidence. source_archive_verification
        aggregates archive (including tables) and supplement; status additionally
        includes the equation fixture hash. Missing bytes are pending, supplied
        invalid bytes fail. G4 stays pending and interpretation is never enabled.
        Fixture hashing does not assert numerical equation validation.

    Raises:
        OSError: The required manifest cannot be read.
        ValueError: The required manifest is invalid JSON.
        KeyError: The required manifest lacks a pinned contract field.
    """
    contract = json.loads(manifest.read_text())
    characterization = contract["archived_characterization"]
    archive_check = _file_check(archive, contract["sources"]["archive"]["sha256"])
    supplement_check = _file_check(
        supplement, contract["sources"]["supplement"]["sha256"]
    )
    fixture_check = _file_check(
        Path(contract["fixture"]["path"]), contract["fixture"]["sha256"]
    )
    tables = {
        noise: {
            "path": expected["path"],
            "status": "pending",
            "expected_sha256": expected["sha256"],
            "observed_sha256": None,
            "expected_rows": characterization["rows"],
            "rows": None,
            "reasons": ["Archive bytes have not passed verification"],
        }
        for noise, expected in characterization["tables"].items()
    }
    if archive_check["status"] == "passed":
        try:
            with ZipFile(archive) as zipped:
                names = zipped.namelist()
                for noise, expected in characterization["tables"].items():
                    if names.count(expected["path"]) != 1:
                        tables[noise]["status"] = "failed"
                        tables[noise]["reasons"] = [
                            "Expected ZIP member must occur exactly once"
                        ]
                    else:
                        tables[noise] = _table_check(
                            zipped.read(expected["path"]), expected, characterization
                        )
            archive_check["status"] = _status(list(tables.values()))
            if archive_check["status"] != "passed":
                archive_check["reasons"].append("Archived table verification failed")
        except (BadZipFile, OSError, RuntimeError, NotImplementedError) as error:
            archive_check["status"] = "failed"
            archive_check["reasons"].append(f"Cannot read supplied ZIP: {error}")

    components = {
        "archive": archive_check,
        "supplement": supplement_check,
        "equation_fixture": fixture_check,
    }
    return {
        "status": _status(list(components.values())),
        "source_archive_verification": _status([archive_check, supplement_check]),
        **components,
        "labels": characterization["labels"],
        "tables": tables,
        "reasons": [
            f"{name}: {reason}"
            for name, check in {**components, **tables}.items()
            for reason in check["reasons"]
        ],
        "G4": "pending",
        "interpretation_allowed": False,
    }
