#!/usr/bin/env python3
"""Offline self-test for the standalone review checker."""

from __future__ import annotations

import copy
import sys

from review_check import SKILL_ROOT, ValidationError, load_jsonl, load_object, validate_records

MINIMUM_PYTHON = (3, 9)
if sys.version_info < MINIMUM_PYTHON:
    raise SystemExit("selftest.py requires Python 3.9 or newer")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def fail(findings: list[dict], verdict: dict, marker: str) -> None:
    try:
        validate_records(findings, verdict)
    except ValidationError as exc:
        require(marker in str(exc), f"expected {marker!r}, got {exc!s}")
    else:
        raise AssertionError(f"expected failure containing {marker!r}")


def expand(records: list[dict], verdict: dict) -> tuple[list[dict], dict]:
    """Rewrite the fixture into the expanded reference form.

    Projects written before the ``sources`` declaration carry that form on disk,
    so the checker keeps resolving it.
    """
    sources = records[0]["sources"]
    expanded_findings = [copy.deepcopy(record) for record in records[1:]]
    for finding in expanded_findings:
        for ref in [*finding["evidence_refs"], finding["target_ref"]]:
            ref.update(sources[ref.pop("src")])
    expanded_verdict = copy.deepcopy(verdict)
    verdict_sources = expanded_verdict.pop("sources")
    for ref in [*expanded_verdict["reviewed_artifacts"], expanded_verdict["findings_ref"]]:
        ref.update(verdict_sources[ref.pop("src")])
    return expanded_findings, expanded_verdict


def main() -> int:
    findings = load_jsonl(SKILL_ROOT / "examples/minimal-findings.jsonl")
    verdict = load_object(SKILL_ROOT / "examples/minimal-verdict.json")
    result = validate_records(findings, verdict)
    require(
        result["open_blockers"] == 1 and result["verdict"] == "REVISE",
        "valid fixture verdict",
    )
    require(result["findings"] == 1, "the sources header is not counted as a finding")

    expanded_findings, expanded_verdict = expand(findings, verdict)
    expanded = validate_records(expanded_findings, expanded_verdict)
    require(expanded == result, "expanded references validate to the same result")

    undeclared = copy.deepcopy(findings)
    undeclared[1]["target_ref"] = {"src": "unknown-source", "record_id": "SC001"}
    fail(undeclared, verdict, "REF_SRC_IS_NOT_DECLARED")

    unbound = copy.deepcopy(findings)
    unbound[1]["evidence_refs"][0] = {"role": "source", "record_id": "SC001-A01"}
    fail(unbound, verdict, "REF_HAS_NO_UPSTREAM_BINDING")

    wrong_count = copy.deepcopy(verdict)
    wrong_count["open_blocker_count"] = 0
    fail(findings, wrong_count, "open_blocker_count")

    false_approval = copy.deepcopy(verdict)
    false_approval["verdict"] = "APPROVE"
    fail(findings, false_approval, "open blockers require REVISE")

    broken_finding = copy.deepcopy(findings)
    broken_finding[1]["evidence_refs"] = []
    fail(broken_finding, verdict, "evidence_refs")

    print("8 self-tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
