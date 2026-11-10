"""P0-D S1 independent dynamic trace validation. Python 3.10+, stdlib only.

All events are observations, not authority. This tool never changes a game.
"""
from __future__ import annotations
import argparse
import json
import math
import re
import sys
from pathlib import Path

SCHEMA = "p0d.s1.trace.v1"
TEAMS = {"red", "blue"}
RECEIPT_EVENTS = {"DAMAGE", "CASTLE_DAMAGE", "BOSS_HIT", "REMOTE_REJECT"}
KINDS = {"JOIN", "START", "TAKE", "DROP", "SCORE", "DAMAGE", "CASTLE_DAMAGE",
         "BOSS_WARN", "WARN_VISIBLE", "BOSS_HIT", "BOSS_CLEAR", "REMOTE_REJECT",
         "LEAVE", "END", "RESET", "DONE"}
HEX40 = re.compile(r"^[0-9a-f]{40}$")

class TraceError(ValueError):
    pass

def need(ok, message):
    if not ok:
        raise TraceError(message)

def number(x, *, low=0, high=1e9):
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x) and low <= x <= high

def ident(x):
    return isinstance(x, str) and 1 <= len(x) <= 100 and bool(re.fullmatch(r"[A-Za-z0-9_.:-]+", x))

def validate(doc, *, real=False, require_full=True):
    """Validate a complete S1 exported trace; raises TraceError on first defect.

    A real/studio flag only validates metadata, never authenticates Roblox execution.
    """
    need(isinstance(doc, dict), "root:not_object")
    meta = doc.get("meta")
    need(isinstance(meta, dict), "meta:missing")
    need(meta.get("schema") == SCHEMA, "meta:wrong_schema")
    need(ident(meta.get("match_id")), "meta:match_id")
    need(isinstance(meta.get("epoch"), int) and not isinstance(meta["epoch"], bool)
         and 1 <= meta["epoch"] <= 1_000_000, "meta:epoch")
    need(meta.get("capture_mode") in ("SYNTHETIC", "STUDIO_CAPTURE"), "meta:capture_mode")
    if real:
        need(meta.get("capture_mode") == "STUDIO_CAPTURE", "BLOCKED_NO_REAL_CAPTURE")
        need(ident(meta.get("studio_session")), "meta:studio_session")
        need(isinstance(meta.get("source_commit"), str)
             and bool(HEX40.fullmatch(meta["source_commit"])), "meta:source_commit")
        need(ident(meta.get("place_id")), "meta:place_id")
    events = doc.get("events")
    need(isinstance(events, list) and 1 <= len(events) <= 10000, "events:missing_or_oversize")
    current_epoch = meta["epoch"]
    players = {}
    hp = {}
    castle_hp = {"red": 100, "blue": 100}
    used_receipts = set()
    boss = {}
    carrier = None
    phase = "lobby"
    reason = None
    scored = None
    left = set()
    complete = False
    stats = {"rounds_started": 0, "rounds_ended": 0, "egg_scores": 0,
             "damage_receipts": 0, "rejects": 0, "boss_hits": 0,
             "client_warning_views": 0, "resets": 0}
    last_seq, last_t = 0, -1.0
    for pos, e in enumerate(events):
        loc = f"events[{pos}]"
        need(isinstance(e, dict), f"{loc}:not_object")
        k = e.get("kind")
        need(k in KINDS, f"{loc}:kind")
        seq, t, epoch = e.get("seq"), e.get("t"), e.get("epoch")
        need(isinstance(seq, int) and not isinstance(seq, bool) and seq == last_seq + 1,
             f"{loc}:seq_not_contiguous")
        need(number(t, low=0, high=86400) and t >= last_t, f"{loc}:clock_not_monotonic_seconds")
        need(isinstance(epoch, int) and not isinstance(epoch, bool) and epoch == current_epoch,
             f"{loc}:stale_or_wrong_epoch")
        need(not complete, f"{loc}:event_after_done")
        last_seq, last_t = seq, t
        actor = e.get("actor")
        if k in RECEIPT_EVENTS:
            rid = e.get("receipt_id")
            need(ident(rid), f"{loc}:missing_receipt")
            need(rid not in used_receipts, f"{loc}:duplicate_receipt")
            used_receipts.add(rid)
        if k == "JOIN":
            need(phase == "lobby" and ident(actor) and actor not in players,
                 f"{loc}:invalid_join")
            need(e.get("team") in TEAMS and len(players) < 16, f"{loc}:invalid_team")
            players[actor] = e["team"]
        elif k == "START":
            need(phase == "lobby" and len(players) >= 2 and set(players.values()) == TEAMS,
                 f"{loc}:start_without_two_teams")
            phase, carrier, reason, scored = "active", None, None, None
            hp = {p: 100 for p in players}
            castle_hp = {"red": 100, "blue": 100}
            left.clear()
            boss.clear()
            stats["rounds_started"] += 1
        elif k == "TAKE":
            need(phase == "active" and actor in players and actor not in left
                 and hp.get(actor, 0) > 0 and carrier is None, f"{loc}:illegal_take")
            carrier = actor
        elif k == "DROP":
            need(phase == "active" and actor == carrier, f"{loc}:illegal_drop")
            carrier = None
        elif k == "SCORE":
            need(phase == "active" and scored is None and actor == carrier and actor not in left
                 and e.get("home_team") == players.get(actor), f"{loc}:illegal_score")
            carrier = None
            scored = players[actor]
            stats["egg_scores"] += 1
        elif k in ("DAMAGE", "BOSS_HIT"):
            target = e.get("target")
            amount = e.get("amount")
            need(phase == "active" and target in players and target not in left,
                 f"{loc}:damage_target")
            need(number(amount, low=1, high=50) and isinstance(amount, int), f"{loc}:damage_amount")
            if k == "DAMAGE":
                need(actor in players and actor not in left and hp.get(actor, 0) > 0
                     and players[actor] != players[target], f"{loc}:friendly_or_untrusted_damage")
            else:
                eid = e.get("event_id")
                need(eid in boss and boss[eid]["active"] and t >= boss[eid]["deadline"],
                     f"{loc}:boss_hit_before_warning_or_after_clear")
                stats["boss_hits"] += 1
            new_hp = max(0, hp.get(target, 0) - amount)
            need(e.get("after_hp") == new_hp, f"{loc}:hp_mismatch")
            hp[target] = new_hp
            if target == carrier and new_hp == 0:
                carrier = None
            stats["damage_receipts"] += 1
        elif k == "CASTLE_DAMAGE":
            team, amount = e.get("target_team"), e.get("amount")
            need(phase == "active" and actor in players and actor not in left
                 and hp.get(actor, 0) > 0 and team in TEAMS and players[actor] != team,
                 f"{loc}:castle_damage_authority")
            need(isinstance(amount, int) and not isinstance(amount, bool) and 1 <= amount <= 50,
                 f"{loc}:castle_amount")
            value = max(0, castle_hp[team] - amount)
            need(e.get("after_hp") == value, f"{loc}:castle_hp_mismatch")
            castle_hp[team] = value
            stats["damage_receipts"] += 1
        elif k == "BOSS_WARN":
            eid, deadline = e.get("event_id"), e.get("deadline")
            need(phase == "active" and ident(eid) and eid not in boss, f"{loc}:boss_double_event")
            need(number(deadline) and 1.8 <= deadline-t <= 2.2,
                 f"{loc}:boss_deadline_not_2s_server_time")
            boss[eid] = {"deadline": deadline, "active": True, "views": set()}
        elif k == "WARN_VISIBLE":
            eid, viewer = e.get("event_id"), e.get("viewer")
            need(phase == "active" and eid in boss and boss[eid]["active"],
                 f"{loc}:client_view_missing_warning")
            need(viewer in players and viewer not in boss[eid]["views"],
                 f"{loc}:duplicate_or_unknown_client_view")
            remaining = max(0, boss[eid]["deadline"]-t)
            actual = e.get("shown_remaining")
            need(number(actual) and abs(actual-remaining) <= 0.1,
                 f"{loc}:client_warning_not_deadline_synced")
            need(actual >= 1.5, f"{loc}:warning_ux_too_short")
            boss[eid]["views"].add(viewer)
            stats["client_warning_views"] += 1
        elif k == "BOSS_CLEAR":
            eid = e.get("event_id")
            need(phase == "active" and eid in boss and boss[eid]["active"],
                 f"{loc}:boss_clear_unknown")
            need({players[p] for p in boss[eid]["views"]} == TEAMS, f"{loc}:boss_view_not_two_teams")
            boss[eid]["active"] = False
        elif k == "REMOTE_REJECT":
            need(phase == "active" and ident(actor) and ident(e.get("reason")),
                 f"{loc}:invalid_reject")
            stats["rejects"] += 1
        elif k == "LEAVE":
            need(actor in players and actor not in left, f"{loc}:leave_unknown")
            left.add(actor)
            if actor == carrier:
                carrier = None
        elif k == "END":
            win = e.get("winner")
            why = e.get("reason")
            need(phase == "active" and win in TEAMS, f"{loc}:end_without_round")
            if why == "egg":
                need(scored == win, f"{loc}:false_egg_win")
            elif why == "castle":
                enemy = "blue" if win == "red" else "red"
                need(castle_hp[enemy] == 0, f"{loc}:false_castle_win")
            elif why == "forfeit":
                need(any(players[p] != win for p in left), f"{loc}:false_forfeit")
            else:
                raise TraceError(f"{loc}:unknown_end_reason")
            need(all(not b["active"] for b in boss.values()), f"{loc}:boss_not_cleared_on_end")
            phase = "ended"
            reason = why
            stats["rounds_ended"] += 1
        elif k == "RESET":
            need(phase == "ended" and e.get("next_epoch") == current_epoch + 1,
                 f"{loc}:reset_without_end")
            current_epoch += 1
            phase = "lobby"
            players.clear(); hp.clear(); left.clear(); boss.clear()
            carrier, scored, reason = None, None, None
            stats["resets"] += 1
        elif k == "DONE":
            need(phase in ("ended", "lobby"), f"{loc}:done_during_match")
            complete = True
    need(complete, "trace:missing_done_marker")
    if require_full:
        for field in ("rounds_started", "rounds_ended", "egg_scores", "damage_receipts",
                      "rejects", "boss_hits", "client_warning_views", "resets"):
            need(stats[field] >= (2 if field == "client_warning_views" else 1), f"trace:missing_coverage:{field}")
    return stats

def run(argv=None):
    p = argparse.ArgumentParser(description="P0-D S1 dynamic trace independent QA (read-only)")
    p.add_argument("trace", type=Path, help="JSON export of actual or synthetic trace")
    p.add_argument("--release", action="store_true", help="require STUDIO_CAPTURE metadata, not synthetic")
    p.add_argument("--partial", action="store_true", help="allow incomplete scenario coverage, but still require DONE")
    opts = p.parse_args(argv)
    try:
        if not opts.trace.is_file():
            raise TraceError("BLOCKED_NO_REAL_CAPTURE" if opts.release else "trace:file_missing")
        need(opts.trace.stat().st_size <= 5_000_000, "trace:file_too_large")
        doc = json.loads(opts.trace.read_text(encoding="utf-8"))
        stats = validate(doc, real=opts.release, require_full=not opts.partial)
        status = "TRACE_CONSISTENT_STUDIO_METADATA_UNVERIFIED" if opts.release else "PASS_SYNTHETIC_OR_UNVERIFIED"
        code = 0
        findings = []
    except (ValueError, OSError, json.JSONDecodeError) as ex:
        findings = [str(ex)]
        status = "BLOCKED_NO_REAL_CAPTURE" if "BLOCKED_NO_REAL_CAPTURE" in str(ex) else "FAIL_TRACE"
        stats, code = {}, (2 if status.startswith("BLOCKED") else 1)
    print(json.dumps({"status": status, "stats": stats, "findings": findings,
                      "native_luau": "NOT_TESTED", "studio_provenance": "NOT_AUTHENTICATED_BY_THIS_TOOL",
                      "publish_gate": "OWNER_FINAL_STUDIO_QA_REQUIRED"}, ensure_ascii=False, sort_keys=True))
    return code

if __name__ == "__main__":
    sys.exit(run())
