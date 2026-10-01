#!/usr/bin/env python3
"""Offline self-test for screenplay indexing and voice-sheet projection."""

from __future__ import annotations

import hashlib
import json
import sys
import tempfile
from pathlib import Path

from duration_estimate import StaleIndex, estimate, index_blocks
from screenplay_index import build_index
from voice_sheet_check import check

MINIMUM_PYTHON = (3, 9)
if sys.version_info < MINIMUM_PYTHON:
    raise SystemExit("selftest.py requires Python 3.9 or newer")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def codes(result: dict[str, object]) -> set[str]:
    findings = result["findings"]
    assert isinstance(findings, list)
    return {finding["code"] for finding in findings}


def measure_text(body: str, project: dict[str, object] | None = None) -> dict[str, object]:
    """Index a screenplay the documented way, then estimate from that index.

    The estimate has no reader of its own. Going through ``build_index`` here is
    the point of the test, not overhead: it is what stops this script and the
    index from holding two opinions about the same line.
    """
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        screenplay = root / "screenplay.md"
        index_path = root / "screenplay-index.jsonl"
        screenplay.write_text(
            "# EP001\n\n## EP001-SC001 内 · 房间 · 日\n\n" + body, encoding="utf-8"
        )
        build_index(
            screenplay,
            index_path,
            source_ref="剧集/EP001/screenplay.md",
            speakers=["甲"],
        )
        records = [
            json.loads(line)
            for line in index_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        source = screenplay.read_bytes()
        blocks, review = index_blocks(records, source)
        return estimate(source, blocks, project, review)


def test_duration_reports_counts_without_rates() -> None:
    """No declared rates must yield no seconds -- never a default guess."""
    report = measure_text("甲：一二三四五。\n\n他把门关上。\n")
    require(report["seconds"] is None, "seconds must stay unknown without rates")
    require(report["counts"]["dialogue_characters"] == 6, "spoken characters counted")
    require(report["counts"]["action_paragraphs"] == 1, "action paragraph counted")


def test_duration_uses_the_projects_own_rates() -> None:
    project = {
        "format": {
            "target_seconds_per_episode": 10,
            "pacing": {
                "spoken_characters_per_second": 3.0,
                "seconds_per_action_paragraph": 2.0,
            },
        }
    }
    report = measure_text("甲：一二三四五六\n\n他把门关上。\n", project)
    # Punctuation counts as spoken time because it stands for the pause it
    # creates; here the line is six bare characters: 6 / 3.0 + 1 * 2.0 == 4.0.
    require(report["seconds"] == 4.0, f"expected 4.0s, got {report['seconds']}")
    require(report["delta_seconds"] == -6.0, "delta is reported against the target")


def test_production_tags_are_not_performed_time() -> None:
    report = measure_text("[画面文字] 账号后台：粉丝 2\n\n他把门关上。\n")
    require(report["counts"]["production_tag_lines"] == 1, "tag counted separately")
    require(report["counts"]["action_paragraphs"] == 1, "tag is not an action")


def test_voice_over_is_performed_time() -> None:
    """[VO] is a line delivered off-camera, not an instruction to a later stage."""
    report = measure_text("[VO] 甲：一二三四五。\n")
    require(report["counts"]["dialogue_lines"] == 1, "[VO] is a spoken line")
    require(report["counts"]["dialogue_characters"] == 6, "[VO] characters are timed")
    require(report["counts"]["production_tag_lines"] == 0, "[VO] is not a mute tag")


def test_one_action_paragraph_is_one_paragraph_however_many_lines() -> None:
    """The format contract lets an action paragraph run several lines."""
    report = measure_text("他站起来，\n走到窗边，\n把窗帘拉开。\n")
    require(
        report["counts"]["action_paragraphs"] == 1,
        f"expected 1 paragraph, got {report['counts']['action_paragraphs']}",
    )


def test_comments_are_not_production_content() -> None:
    """A Markdown comment is a note to the writer, not a line to perform."""
    report = measure_text("<!-- 待确认：这一段的转场是否保留。 -->\n")
    require(report["counts"]["dialogue_lines"] == 0, "a comment is not dialogue")
    require(report["counts"]["dialogue_characters"] == 0, "a comment is not spoken")
    require(report["counts"]["action_paragraphs"] == 0, "a comment is not an action")


def test_an_index_from_other_bytes_is_refused() -> None:
    """Spans from a stale index land on text it never classified."""
    stale = [
        {
            "record_type": "screenplay_index_meta",
            "source_byte_length": 999_999,
        }
    ]
    try:
        index_blocks(stale, b"short")
    except StaleIndex:
        return
    raise AssertionError("a stale index must be refused, not measured")


def main() -> int:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        screenplay = root / "screenplay.md"
        index_path = root / "screenplay-index.jsonl"
        screenplay.write_text(
            "# EP001\n\n## EP001-SC001 内 · 客厅 · 夜\n\n陈予安推开门。\n\n陈予安：我回来了。\n",
            encoding="utf-8",
        )
        summary = build_index(
            screenplay,
            index_path,
            source_ref="剧集/EP001/screenplay.md",
            speakers=["陈予安"],
        )
        require(summary["review_status"] == "clean", "valid screenplay index")
        index_bytes = index_path.read_bytes()
        records = [
            json.loads(line) for line in index_bytes.decode("utf-8").splitlines()
        ]
        dialogue = next(record for record in records if record.get("kind") == "dialogue")

        header = {
            "record_type": "sources",
            "schema_version": "1.0.0",
            "sources": {
                "screenplay-index": {
                    "owner": "short-drama-write",
                    "artifact": "剧集/EP001/screenplay-index.jsonl",
                    "hash": hashlib.sha256(index_bytes).hexdigest(),
                }
            },
        }
        line = {
            "line_id": "LINE-001",
            "channel": "sync",
            "speaker_display": "陈予安",
            "line_text": "我回来了。",
            "source_ref": {"src": "screenplay-index", "record_id": dialogue["block_id"]},
        }
        sheet = [header, line]
        result = check(sheet, records, screenplay.read_bytes())
        require(result["status"] == "pass", "faithful voice sheet")
        require(result["lines"] == 1, "the sources header is not a voice line")

        # A sheet written before the compact form still resolves; real projects
        # hold both spellings and neither is rewritten.
        expanded = [
            dict(
                line,
                source_ref={
                    "owner": "short-drama-write",
                    "artifact": "剧集/EP001/screenplay-index.jsonl",
                    "hash": hashlib.sha256(index_bytes).hexdigest(),
                    "record_id": dialogue["block_id"],
                },
            )
        ]
        require(
            check(expanded, records, screenplay.read_bytes())["status"] == "pass",
            "expanded voice sheet",
        )

        undeclared = [header, dict(line, source_ref={"src": "screenplay", "record_id": "X"})]
        require(
            "VOICE_SOURCE_REF_UNDECLARED"
            in codes(check(undeclared, records, screenplay.read_bytes())),
            "src without a sources entry was not detected",
        )

        unbound = [header, dict(line, source_ref={"record_id": dialogue["block_id"]})]
        require(
            "VOICE_SOURCE_REF_MISSING"
            in codes(check(unbound, records, screenplay.read_bytes())),
            "source_ref naming no upstream snapshot was not detected",
        )

        changed = [header, dict(line, line_text="我走了。")]
        require(
            check(changed, records, screenplay.read_bytes())["status"] == "fail",
            "changed voice line was not detected",
        )

    test_duration_reports_counts_without_rates()
    test_duration_uses_the_projects_own_rates()
    test_production_tags_are_not_performed_time()
    test_voice_over_is_performed_time()
    test_one_action_paragraph_is_one_paragraph_however_many_lines()
    test_comments_are_not_production_content()
    test_an_index_from_other_bytes_is_refused()

    print("14 self-tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
