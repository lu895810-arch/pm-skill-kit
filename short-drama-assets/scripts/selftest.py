#!/usr/bin/env python3
"""Offline self-test for the standalone asset checker."""

from __future__ import annotations

import copy
import sys
from pathlib import Path

from asset_check import SKILL_ROOT, RecordFile, ValidationError, load_jsonl, validate_records

MINIMUM_PYTHON = (3, 9)
if sys.version_info < MINIMUM_PYTHON:
    raise SystemExit("selftest.py requires Python 3.9 or newer")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def expect_failure(characters: RecordFile, looks: RecordFile, marker: str) -> None:
    try:
        validate_records(characters, looks)
    except ValidationError as exc:
        if marker not in str(exc):
            raise AssertionError(f"expected {marker!r}, got {exc!s}") from exc
    else:
        raise AssertionError(f"expected validation failure containing {marker!r}")


def edited(source: RecordFile, index: int) -> tuple[RecordFile, dict]:
    records = copy.deepcopy(source.records)
    return RecordFile(copy.deepcopy(source.sources), records), records[index]


def main() -> int:
    example = Path(SKILL_ROOT, "examples/minimal")
    characters = load_jsonl(example / "characters.jsonl")
    looks = load_jsonl(example / "looks.jsonl")
    result = validate_records(characters, looks)
    require(result["characters"] == 1 and result["looks"] == 1, "valid fixture count")

    duplicate = copy.deepcopy(characters.records[0])
    expect_failure(
        RecordFile(characters.sources, [*characters.records, duplicate]),
        looks,
        "duplicate character_id",
    )

    broken_look, record = edited(looks, 0)
    record["character_ref"]["record_id"] = "CHAR-MISSING"
    expect_failure(characters, broken_look, "does not resolve")

    undeclared, record = edited(looks, 0)
    record["character_ref"]["src"] = "not-declared"
    expect_failure(characters, undeclared, "REF_SRC_IS_NOT_DECLARED")

    unbound, record = edited(looks, 0)
    record["character_ref"] = {"record_id": "CHAR-LIN"}
    expect_failure(characters, unbound, "REF_HAS_NO_UPSTREAM_BINDING")

    # A released project may still carry the snapshot inline on the reference.
    inline, record = edited(looks, 0)
    record["character_ref"] = {
        **inline.sources["characters"],
        "record_id": "CHAR-LIN",
    }
    inline.sources.pop("characters")
    require(validate_records(characters, inline)["status"] == "valid", "inline snapshot")

    candidate, record = edited(characters, 0)
    record["creator_acceptance"] = {"status": "proposed", "decision_ref": None}
    require(validate_records(candidate, looks)["status"] == "valid", "candidate status")

    invalid, record = edited(characters, 0)
    record["creator_acceptance"] = {"status": "approved", "decision_ref": None}
    expect_failure(invalid, looks, "invalid creator_acceptance status")

    misbound, record = edited(characters, 0)
    record["creator_acceptance"]["decision_ref"]["record_id"] = "SC001-A01"
    expect_failure(misbound, looks, "must be a creator decision starting with CD-")

    print("9 self-tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
