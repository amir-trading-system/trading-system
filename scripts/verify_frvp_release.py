"""Release gate for the FRVP Pine indicator and its Python mirror.

This gate solves two different problems and reports them separately:

1. Source-locked Python validation: every Pine/Python/fixture change invalidates
   the prior attestation, and a new attestation can be recorded only after the
   complete behavioral regression suite passes.
2. Pine-runtime parity: a TradingView CSV export carrying the current
   ``Validation Build ID`` is compared bar-for-bar with Python.  This is the
   only layer that proves TradingView actually executed the same behavior.

Use ``--record`` after a deliberate, reviewed Pine/Python change.  Use
``--require-pine-traces`` for the final release standard.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

import test_frvp_reclaim_regression as regression


SCRIPT_DIR = Path(__file__).resolve().parent
PINE_PATH = SCRIPT_DIR / "frvp_new_indicator.pine"
PYTHON_PATH = SCRIPT_DIR / "test_frvp_reclaim_regression.py"
FIXTURE_DIR = SCRIPT_DIR / "fixtures" / "frvp"
TRACE_DIR = SCRIPT_DIR / "fixtures" / "frvp_pine_traces"
ATTESTATION_PATH = SCRIPT_DIR / "frvp_validation_attestation.json"
REPORT_PATH = SCRIPT_DIR / "frvp_validation_report.json"

START_MARKER = "PARITY_DETECTION_START"
END_MARKER = "PARITY_DETECTION_END"
RULE_PATTERN = re.compile(r"PARITY_RULE:\s*([a-z0-9_]+)")
PINE_BUILD_PATTERN = re.compile(
    r"const\s+int\s+VALIDATION_BUILD_ID\s*=\s*(\d+)"
)


class ValidationError(RuntimeError):
    pass


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def sha256_tree(directory: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(directory.glob("*.csv")):
        digest.update(path.name.encode())
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def marked_region(source: str, path: Path) -> str:
    if source.count(START_MARKER) != 1 or source.count(END_MARKER) != 1:
        raise ValidationError(
            f"{path.name} must contain exactly one {START_MARKER} and "
            f"one {END_MARKER}"
        )
    start = source.index(START_MARKER)
    end = source.index(END_MARKER)
    if end <= start:
        raise ValidationError(f"Invalid parity marker order in {path.name}")
    return source[start:end]


def validate_pine_delimiters(source: str) -> None:
    pairs = {"(": ")", "[": "]", "{": "}"}
    stack: list[tuple[str, int]] = []
    in_string = False
    escaped = False
    for index, char in enumerate(source):
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char in pairs:
            stack.append((char, index))
        elif char in pairs.values():
            if not stack or pairs[stack[-1][0]] != char:
                raise ValidationError(
                    f"Unmatched Pine delimiter {char!r} at byte {index}"
                )
            stack.pop()
    if in_string:
        raise ValidationError("Unterminated Pine string")
    if stack:
        raise ValidationError(f"Unclosed Pine delimiter {stack[-1][0]!r}")


def source_state() -> dict[str, Any]:
    pine_source = PINE_PATH.read_text()
    python_source = PYTHON_PATH.read_text()
    validate_pine_delimiters(pine_source)
    if not pine_source.startswith("//@version=6"):
        raise ValidationError("Pine source is not version 6")

    pine_rules = RULE_PATTERN.findall(pine_source)
    python_rules = RULE_PATTERN.findall(python_source)
    if len(pine_rules) != len(set(pine_rules)):
        raise ValidationError("Pine contains duplicate PARITY_RULE identifiers")
    if len(python_rules) != len(set(python_rules)):
        raise ValidationError("Python contains duplicate PARITY_RULE identifiers")
    if set(pine_rules) != set(python_rules):
        raise ValidationError(
            "Pine/Python parity-rule mismatch: "
            f"Pine-only={sorted(set(pine_rules) - set(python_rules))}, "
            f"Python-only={sorted(set(python_rules) - set(pine_rules))}"
        )

    build_match = PINE_BUILD_PATTERN.search(pine_source)
    if not build_match:
        raise ValidationError("Pine VALIDATION_BUILD_ID is missing")
    pine_build = int(build_match.group(1))
    if pine_build != regression.VALIDATION_BUILD_ID:
        raise ValidationError(
            "VALIDATION_BUILD_ID differs: "
            f"Pine={pine_build}, Python={regression.VALIDATION_BUILD_ID}"
        )

    return {
        "validation_build_id": pine_build,
        "pine_sha256": sha256_bytes(pine_source.encode()),
        "python_sha256": sha256_bytes(python_source.encode()),
        "validation_gate_sha256": sha256_file(Path(__file__).resolve()),
        "fixture_tree_sha256": sha256_tree(FIXTURE_DIR),
        "pine_detection_sha256": sha256_bytes(
            marked_region(pine_source, PINE_PATH).encode()
        ),
        "python_detection_sha256": sha256_bytes(
            marked_region(python_source, PYTHON_PATH).encode()
        ),
        "parity_rules": sorted(pine_rules),
        "fixture_files": len(list(FIXTURE_DIR.glob("*.csv"))),
    }


def marker_times(data: pd.DataFrame, column: str, date: str) -> set[str]:
    if column not in data.columns:
        return set()
    timestamps = pd.to_datetime(data["time"])
    dated = data[timestamps.dt.strftime("%Y-%m-%d") == date].copy()
    if dated.empty:
        return set()
    values = pd.to_numeric(dated[column], errors="coerce")
    # plot() exports entry markers as 0/1. plotshape() exports either 1 or a
    # non-null marker value, depending on TradingView's CSV version.
    active = values.notna() & (values != 0.0)
    return set(pd.to_datetime(dated.loc[active, "time"]).dt.strftime("%H:%M"))


def pine_runtime_report(build_id: int) -> dict[str, Any]:
    expected_cases: dict[tuple[str, str, str], dict[str, Any]] = {}
    for symbol, fixture_path, date, _, _ in regression.REGRESSION_CASES:
        key = (symbol, date, Path(fixture_path).name)
        expected_cases[key] = {
            "symbol": symbol,
            "date": date,
            "fixture": Path(fixture_path).name,
        }

    results = []
    for case in expected_cases.values():
        trace_path = TRACE_DIR / case["fixture"]
        record = dict(case)
        if not trace_path.exists():
            record.update(status="MISSING_TRACE")
            results.append(record)
            continue
        trace = pd.read_csv(trace_path)
        if "Validation Build ID" not in trace.columns:
            record.update(status="TRACE_HAS_NO_BUILD_ID")
            results.append(record)
            continue
        builds = set(
            pd.to_numeric(trace["Validation Build ID"], errors="coerce")
            .dropna().astype(int)
        )
        if builds != {build_id}:
            record.update(
                status="STALE_TRACE", trace_build_ids=sorted(builds)
            )
            results.append(record)
            continue

        python_result = regression.detect(
            str(FIXTURE_DIR / case["fixture"]), case["date"]
        )
        python_entries = (
            set(python_result.time.dt.strftime("%H:%M"))
            if len(python_result) else set()
        )
        python_setups = {
            item["time"].strftime("%H:%M")
            for item in python_result.attrs.get("setups", [])
        }
        pine_entries = marker_times(
            trace, "Strong Reclaim Entry", case["date"]
        )
        pine_setups = marker_times(
            trace, "Nested Reclaim Evidence Marker", case["date"]
        )
        entry_match = pine_entries == python_entries
        setup_match = pine_setups == python_setups
        record.update(
            status="PASS" if entry_match and setup_match else "MISMATCH",
            python_entries=sorted(python_entries),
            pine_entries=sorted(pine_entries),
            python_setups=sorted(python_setups),
            pine_setups=sorted(pine_setups),
        )
        results.append(record)

    passing = sum(item["status"] == "PASS" for item in results)
    return {
        "required_cases": len(results),
        "passing_cases": passing,
        "complete": bool(results) and passing == len(results),
        "cases": results,
    }


def current_attestation_payload(
    state: dict[str, Any], regression_report: dict[str, Any],
    runtime_report: dict[str, Any],
) -> dict[str, Any]:
    return {
        "schema": 1,
        "recorded_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": (
            "FULLY_VERIFIED"
            if runtime_report["complete"]
            else "PYTHON_VERIFIED_PINE_RUNTIME_PENDING"
        ),
        "source": state,
        "regression": regression_report,
        "pine_runtime": runtime_report,
    }


def compare_attested_source(
    attestation: dict[str, Any], state: dict[str, Any]
) -> list[str]:
    old = attestation.get("source", {})
    keys = (
        "validation_build_id",
        "pine_sha256",
        "python_sha256",
        "validation_gate_sha256",
        "fixture_tree_sha256",
        "pine_detection_sha256",
        "python_detection_sha256",
        "parity_rules",
        "fixture_files",
    )
    return [key for key in keys if old.get(key) != state.get(key)]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--record", action="store_true",
        help="Record a new attestation only after all Python checks pass.",
    )
    parser.add_argument(
        "--require-pine-traces", action="store_true",
        help="Fail unless every case has a matching current-build TradingView export.",
    )
    args = parser.parse_args()

    state = source_state()
    old_attestation = (
        json.loads(ATTESTATION_PATH.read_text())
        if ATTESTATION_PATH.exists() else None
    )

    # If Pine detection changed, a release cannot be re-attested by merely
    # rerunning unchanged Python tests. The mirror and build ID must both move.
    if args.record and old_attestation:
        old_source = old_attestation.get("source", {})
        pine_detection_changed = (
            old_source.get("pine_detection_sha256")
            != state["pine_detection_sha256"]
        )
        if pine_detection_changed:
            if (
                old_source.get("python_detection_sha256")
                == state["python_detection_sha256"]
            ):
                raise ValidationError(
                    "Pine detection changed but the Python detector did not. "
                    "Update the mirror before recording a release."
                )
            if (
                old_source.get("validation_build_id")
                == state["validation_build_id"]
            ):
                raise ValidationError(
                    "Pine detection changed without incrementing "
                    "VALIDATION_BUILD_ID."
                )

    regression_report = regression.run_regression_suite()
    runtime_report = pine_runtime_report(state["validation_build_id"])
    payload = current_attestation_payload(
        state, regression_report, runtime_report
    )

    REPORT_PATH.write_text(json.dumps(payload, indent=2) + "\n")

    if args.record:
        ATTESTATION_PATH.write_text(json.dumps(payload, indent=2) + "\n")
        print(f"Recorded {payload['status']} attestation")
    else:
        if old_attestation is None:
            raise ValidationError(
                "No FRVP attestation exists. Run with --record after review."
            )
        changed = compare_attested_source(old_attestation, state)
        if changed:
            raise ValidationError(
                "FRVP source is not the attested release. Changed: "
                + ", ".join(changed)
            )
        print("Source attestation: PASS")

    print(
        "Python regression: PASS - "
        f"{regression_report['positive_entry_fixtures']} positive entries, "
        f"{regression_report['negative_entry_fixtures']} negative entries, "
        f"{regression_report['positive_setup_fixtures']} positive setups, "
        f"{regression_report['negative_setup_fixtures']} negative setups"
    )
    print(
        "TradingView Pine runtime parity: "
        f"{runtime_report['passing_cases']}/"
        f"{runtime_report['required_cases']} cases"
    )
    if args.require_pine_traces and not runtime_report["complete"]:
        raise ValidationError(
            "Full release verification requires fresh TradingView CSV traces "
            f"for build {state['validation_build_id']} in {TRACE_DIR}."
        )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValidationError, AssertionError) as error:
        REPORT_PATH.write_text(json.dumps({
            "schema": 1,
            "recorded_at_utc": datetime.now(timezone.utc).isoformat(),
            "status": "VALIDATION_FAILED",
            "error": repr(error),
        }, indent=2) + "\n")
        print(f"VALIDATION FAILED: {error}", file=sys.stderr)
        raise SystemExit(1)
