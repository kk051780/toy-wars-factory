#!/usr/bin/env python3
"""P0-D progress visibility guard. Validates a supplied report; never audits #220."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

GAME_ID = "TRAP_RAIDERS"
WORK_ID = "p0d-siege-v19"
UNKNOWN = "UNKNOWN_PENDING_GATE_AUDIT"
CANONICAL_220 = "https://github.com/kk051780/toy-wars-factory/issues/220"
AUDITED_COMMENT = re.compile(re.escape(CANONICAL_220) + r"#issuecomment-[1-9][0-9]*\Z")
SHA40 = re.compile(r"[a-f0-9]{40}\Z")
STAGES = {"RESEARCH", "SOURCE_IMPLEMENTED", "CHAT_ASSEMBLED", "CHAT_QA_PENDING", "CHAT_RC_READY", "STUDIO_PARTIAL", "STUDIO_PASS", "RELEASED"}
PHASES = {"PRELAUNCH", "FIRST_RELEASE", "POST_RELEASE"}
STUDIO = {"NOT_TESTED", "NOT_FINAL_TESTED", "PARTIAL", "PASS", "FAIL"}


class BadReport(ValueError):
    pass


def need(condition: bool, message: str) -> None:
    if not condition:
        raise BadReport(message)


def real_int(value: object, field: str) -> int:
    need(type(value) is int, f"{field}: integer required")
    return value


def nonblank(value: object, field: str) -> str:
    need(isinstance(value, str) and bool(value.strip()), f"{field}: required")
    return value


def percent(n: int, den: int) -> str:
    return f"{100*n/den:.1f}%"


def validate(report: dict) -> dict:
    need(isinstance(report, dict), "root object required")
    need(report.get("game_id") == GAME_ID and report.get("work_id") == WORK_ID, "game/work mismatch")
    nonblank(report.get("date_jst"), "date_jst")
    lane = report.get("lane")
    globe = report.get("global")
    need(isinstance(lane, dict) and isinstance(globe, dict), "lane/global objects required")
    nonblank(lane.get("name"), "lane.name")
    blockers = lane.get("blockers")
    need(isinstance(blockers, list) and all(isinstance(v, str) and v.strip() for v in blockers), "blockers must be list of nonblank strings")
    nonblank(lane.get("next_acceptance"), "lane.next_acceptance")
    accepted = lane.get("accepted")
    total = lane.get("total")
    if accepted is None and total is None:
        lane_display = "UNKNOWN (受入分母未確定)"
    else:
        a = real_int(accepted, "lane.accepted")
        t = real_int(total, "lane.total")
        need(t > 0 and 0 <= a <= t, "invalid lane accepted/total")
        if a:
            nonblank(lane.get("evidence_url"), "lane.evidence_url")
        lane_display = f"{percent(a,t)} ({a}/{t})"
    phase = globe.get("product_phase")
    stage = globe.get("stage")
    studio = globe.get("studio_status")
    need(phase in PHASES and stage in STAGES and studio in STUDIO, "bad phase/stage/studio")
    source = nonblank(globe.get("source_url"), "global.source_url")
    pct = globe.get("pct")
    status = globe.get("audit_status")
    prev = globe.get("previous_pct")
    if pct is None:
        need(status == UNKNOWN, "unknown percentage must retain UNKNOWN_PENDING_GATE_AUDIT")
        need(source == CANONICAL_220 or AUDITED_COMMENT.fullmatch(source), "unknown must cite #220")
        need(prev is None, "unknown cannot display invented previous delta")
        global_display = f"未監査 ({UNKNOWN})"
        delta = "比較不可（監査未発行）"
    else:
        p = real_int(pct, "global.pct")
        need(0 <= p <= 100 and status == "AUDITED", "global official score must be #220 audited 0..100 integer")
        need(bool(AUDITED_COMMENT.fullmatch(source)), "numeric global score requires exact #220 audit comment URL")
        need(globe.get("audit_points") == p and globe.get("audit_max_points") == 100, "audited point breakdown total missing or mismatched")
        sha = globe.get("last_rc_sha")
        need(isinstance(sha,str) and bool(SHA40.fullmatch(sha)), "numeric global score needs exact 40-hex RC SHA")
        global_display = f"{p}% ({p}/100, #220監査値)"
        if prev is None:
            delta = "初回監査（比較元なし）"
        else:
            old = real_int(prev, "global.previous_pct")
            need(0 <= old <= 100, "invalid previous official audit")
            delta = f"{p-old:+d}pt（前回公式監査比）"
    evidence = lane.get("evidence_url") or "未提出"
    return {
        "global_display": global_display,
        "lane_display": lane_display,
        "phase": phase,
        "stage": stage,
        "studio": studio,
        "delta": delta,
        "source": source,
        "lane_evidence": evidence,
        "blockers": " / ".join(blockers) if blockers else "なし（申告）",
        "next": lane["next_acceptance"],
    }


def render(report: dict) -> str:
    r = validate(report)
    return "\n".join([
        "[P0D_PROGRESS_V3]",
        f"P0-D全体完成率（公式）: {r['global_display']}",
        f"自担当進捗率: {r['lane_display']}",
        f"全体フェーズ: {r['phase']} / {r['stage']}",
        f"PC Studio: {r['studio']}",
        f"前回比: {r['delta']}",
        f"公式根拠: {r['source']}",
        f"担当根拠: {r['lane_evidence']}",
        f"BLOCKER: {r['blockers']}",
        f"次の受入: {r['next']}",
    ]) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate and render P0-D two-meter visibility report (no network; NOT an audit)")
    parser.add_argument("report", type=Path, help="JSON report prepared from latest #220 and own lane")
    args = parser.parse_args()
    try:
        data = json.loads(args.report.read_text(encoding="utf-8"))
        sys.stdout.write(render(data))
    except (BadReport, OSError, json.JSONDecodeError) as exc:
        print(f"P0D_PROGRESS_REPORT_REJECTED: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
