#!/usr/bin/env python3
"""D16 original SCALE-FX -> original VISUAL-REPLICA integration contract test.

Loads the ACTUAL original Python oracle sources from two locally verified
PUBLIC_SOURCE_V1 source directories. Never edits them, never imports a game
runtime, never requires keys/credentials, network, or Roblox Studio.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib
import importlib.util
import json
from pathlib import Path
import sys
import types

EXPECTED = {
    "scale": ("reference/scale_fx.py", "a9ddb614bbaca5032b240cdc9ad1f77e25b9480228af4803cff077c46c75329b", 3614),
    "bridge": ("reference/bridge.py", "199d24054eabc4535a1f7a3ef5ac2fbcf4c4ae5fb24d2523e8391444f70aba42", 1550),
    "client": ("reference/client_policy.py", "47faed08b6288b9447ad10f69a15f4d8327c9058aba1b454b130959db985e911", 3592),
}
SCALE_SHA = "584b11ef24cf3d44695d86b505207491bbd3844e"
VISUAL_SHA = "226a5664ed50131868391289723c130d35abf48f"


def file_sha(path: Path) -> tuple[str, int]:
    data = path.read_bytes()
    return hashlib.sha256(data).hexdigest(), len(data)


def verify_sources(scale_root: Path, visual_root: Path) -> dict[str, Path]:
    """Hard fail: never silently load cleanroom, stale, or modified originals."""
    roots = {"scale": scale_root, "bridge": visual_root, "client": visual_root}
    paths = {}
    for name, (relative, sha, size) in EXPECTED.items():
        path = roots[name] / relative
        if not path.is_file() or path.is_symlink():
            raise ValueError(f"SOURCE_MISSING_OR_SYMLINK:{name}:{path}")
        observed, n = file_sha(path)
        if (observed, n) != (sha, size):
            raise ValueError(f"SOURCE_SHA_MISMATCH:{name}:expected={sha}:{size}:got={observed}:{n}")
        paths[name] = path
    return paths


def import_verified_sources(paths: dict[str, Path]):
    """Import only SHA-verified read-only Python oracles; scoped module names."""
    spec = importlib.util.spec_from_file_location("_p0d_d16_exact_scale", paths["scale"])
    if spec is None or spec.loader is None:
        raise ValueError("SCALE_IMPORT_FAILED")
    scale = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = scale
    spec.loader.exec_module(scale)

    package_name = "_p0d_d16_exact_visual"
    package = types.ModuleType(package_name)
    package.__path__ = [str(paths["client"].parent)]
    sys.modules[package_name] = package
    client = importlib.import_module(package_name + ".client_policy")
    bridge = importlib.import_module(package_name + ".bridge")
    if not all([
        hasattr(scale, "ScaleFx"), hasattr(bridge, "build"),
        hasattr(client, "Policy"),
    ]):
        raise ValueError("ORIGINAL_API_UNAVAILABLE")
    return scale, bridge, client


class Checks:
    def __init__(self):
        self.passes = []
        self.failures = []

    def check(self, name: str, condition: bool, details=""):
        if condition:
            self.passes.append(name)
        else:
            self.failures.append({"name": name, "details": str(details)})

    def eq(self, name: str, actual, expected):
        self.check(name, actual == expected, f"expected={expected!r}, got={actual!r}")


def run_contract_tests(scale, bridge, client) -> Checks:
    """Exercise real original reference implementations together, not mocks."""
    x = Checks()
    S, B, P = scale.ScaleFx, bridge.build, client.Policy

    giant = S("M-GIANT")
    x.eq("giant:start", giant.begin("M-GIANT", "E1", "GIANT_ONE", "101", ["101", "102"], 30), (True, "STARTED"))
    snap, err = giant.snapshot("M-GIANT")
    x.eq("giant:server_snapshot", err, None)
    pkt, err = B(snap, 30)
    x.eq("giant:bridge_initial", err, None)
    x.eq("giant:display_scale", pkt["scaleMilli"], 1600)
    x.eq("giant:display_targets", pkt["targets"], ["101"])
    x.eq("giant:ttl_initial", pkt["remainingSeconds"], 8)
    face = P("M-GIANT")
    x.eq("giant:client_accept", face.accept(pkt, "M-GIANT", 100), (True, "DISPLAY_ONLY"))
    x.eq("giant:client_deadline", face.deadline, 108)
    x.eq("giant:client_not_expired", face.tick("M-GIANT", 107.999), "ACTIVE")
    x.eq("giant:duplicate_server_event_reject", giant.begin("M-GIANT", "E2", "MINI_ALL", None, ["101"], 31), (False, "EVENT_ALREADY_USED"))
    x.eq("giant:advance", giant.advance("M-GIANT", 32), (True, "ACTIVE"))
    pkt2, err = B(giant.snapshot("M-GIANT")[0], 32)
    x.eq("giant:bridge_followup", err, None)
    x.eq("giant:client_refresh", face.accept(pkt2, "M-GIANT", 102), (True, "DISPLAY_ONLY"))
    x.eq("giant:client_deadline_not_extended", face.deadline, 108)
    x.eq("giant:client_expiry", face.tick("M-GIANT", 108), "EXPIRED")
    x.eq("giant:client_cleared", (face.targets, face.scale_milli, face.closed), ([], 1000, True))
    x.eq("giant:replay_after_expiry", face.accept(pkt, "M-GIANT", 109), (False, "CLOSED_EVENT_REPLAY"))
    x.eq("giant:server_ttl_end", giant.advance("M-GIANT", 38), (True, "EXPIRED"))
    expired, err = B(giant.snapshot("M-GIANT")[0], 38)
    x.eq("giant:server_terminal_bridge", (err, expired["status"], expired["remainingSeconds"]), (None, "EXPIRED", 0))

    mini = S("M-MINI")
    x.eq("mini:start", mini.begin("M-MINI", "E3", "MINI_ALL", None, ["3", "1", "2"], 99), (True, "STARTED"))
    mini_msg, err = B(mini.snapshot("M-MINI")[0], 99)
    x.eq("mini:initial_bridge", err, None)
    x.eq("mini:scale", mini_msg["scaleMilli"], 700)
    x.eq("mini:canonical_targets", mini_msg["targets"], ["1", "2", "3"])
    screen = P("M-MINI")
    x.eq("mini:client_accept", screen.accept(mini_msg, "M-MINI", 1000), (True, "DISPLAY_ONLY"))
    x.eq("mini:leave_mid_event", mini.leave("M-MINI", "2"), (True, "ACTIVE"))
    less, err = B(mini.snapshot("M-MINI")[0], 100)
    x.eq("mini:subset_bridge", err, None)
    x.eq("mini:subset_accept", screen.accept(less, "M-MINI", 1001), (True, "DISPLAY_ONLY"))
    x.eq("mini:subset_only", screen.targets, ["1", "3"])
    x.eq("mini:deadline_not_extended", screen.deadline, 1008)
    x.eq("mini:stale_event_reject", screen.accept({**less, "eventId":"FORGED"}, "M-MINI", 1002), (False, "SECOND_EVENT_REJECTED"))
    x.eq("mini:bad_match_reject", screen.accept(less, "OTHER", 1002), (False, "STALE_MATCH"))
    x.eq("mini:bad_scale_reject", screen.accept({**less, "scaleMilli":1600}, "M-MINI", 1002), (False, "BAD_SCALE"))
    x.eq("mini:leave_one", mini.leave("M-MINI", "1"), (True, "ACTIVE"))
    x.eq("mini:leave_last", mini.leave("M-MINI", "3"), (True, "EXPIRED"))
    term, err = B(mini.snapshot("M-MINI")[0], 101)
    x.eq("mini:terminal_bridge", (err, term["status"]), (None, "EXPIRED"))
    x.eq("mini:terminal_clear", screen.accept(term, "M-MINI", 1002), (True, "CLEARED"))
    x.eq("mini:clear_targets", screen.targets, [])
    x.eq("mini:terminal_replay_refused", screen.accept(term, "M-MINI", 1003), (False, "TERMINAL_REPLAY"))

    close = S("M-CLOSE")
    x.eq("close:start", close.begin("M-CLOSE", "E4", "GIANT_ONE", "1", ["1"], 10), (True, "STARTED"))
    close_view = P("M-CLOSE")
    active, err = B(close.snapshot("M-CLOSE")[0], 10)
    x.eq("close:before", close_view.accept(active, "M-CLOSE", 500), (True, "DISPLAY_ONLY"))
    x.eq("close:server_close", close.close("M-CLOSE"), (True, "CLOSED"))
    close_msg, err = B(close.snapshot("M-CLOSE")[0], 12)
    x.eq("close:terminal_transport", (err,close_msg["status"]), (None,"CLOSED"))
    x.eq("close:client_cancel", close_view.accept(close_msg, "M-CLOSE", 502), (True,"CLEARED"))
    x.eq("close:after_cancel_active_replay", close_view.accept(active,"M-CLOSE",503), (False,"CLOSED_EVENT_REPLAY"))
    x.eq("close:server_no_second_event", close.begin("M-CLOSE", "E5", "MINI_ALL", None, ["1"], 13), (False,"ROUND_CLOSED"))
    x.eq("close:new_round", close.new_round("M-NEW"), (True,"RESET"))
    x.eq("close:new_round_initial", close.status, "IDLE")
    x.eq("close:old_round_blocked", close.snapshot("M-CLOSE")[1], "STALE_MATCH")

    # Delayed packets at/after expiry must NOT resurrect terminal effects.
    delayed = S("M-DELAYED")
    x.eq("delay:start", delayed.begin("M-DELAYED","E6","MINI_ALL",None,["1","2"],200),(True,"STARTED"))
    stale, err = B(delayed.snapshot("M-DELAYED")[0], 208)
    x.eq("delay:no_active_at_deadline", (stale,err), (None,"INVALID_ACTIVE_TTL"))
    stale, err = B(delayed.snapshot("M-DELAYED")[0], 208.01)
    x.eq("delay:no_active_after_deadline", (stale,err), (None,"INVALID_ACTIVE_TTL"))
    x.eq("delay:server_cleanup", delayed.advance("M-DELAYED",208), (True,"EXPIRED"))

    # The original server and client clocks are *different domains*, but the
    # bridge uses only server elapsed seconds to transmit a remaining TTL.
    for i in range(200):
        kind = "GIANT_ONE" if i % 2 else "MINI_ALL"
        match_id = f"ROUND{i}"
        ev = f"EVENT{i}"
        start = 100.0 + i * 2.5
        travel = (i % 7) * 0.17
        client_clock = 4000.0 + i * 3
        core = S(match_id)
        roster = ["1", "2", "3"]
        result = core.begin(match_id, ev, kind, "2" if kind=="GIANT_ONE" else None, roster, start)
        packet, err = B(core.snapshot(match_id)[0], start+travel)
        displayed = P(match_id)
        ok, why = displayed.accept(packet, match_id, client_clock+travel)
        x.check(f"differential_clock:{i}", result==(True,"STARTED") and err is None
                and ok and abs(displayed.deadline-(client_clock+8.0)) < 1e-8
                and displayed.tick(match_id,client_clock+8)=="EXPIRED",
                (result,err,ok,why,displayed.deadline,client_clock))

    return x


def evaluate(scale_root: Path, visual_root: Path) -> dict:
    paths = verify_sources(scale_root, visual_root)
    scale, bridge, client = import_verified_sources(paths)
    checks = run_contract_tests(scale, bridge, client)
    return {
        "game_id":"TRAP_RAIDERS", "work_id":"p0d-siege-v19",
        "source_type":"EXACT_ORIGINAL_PYTHON_ORACLES_SHA_VERIFIED",
        "scale_source_commit":SCALE_SHA, "visual_source_commit":VISUAL_SHA,
        "source_hashes":{"scale":EXPECTED["scale"][1], "bridge":EXPECTED["bridge"][1], "client":EXPECTED["client"][1]},
        "checks_passed":len(checks.passes), "checks_failed":len(checks.failures),
        "state":"ORIGINAL_PAIR_OFFLINE_PASS" if not checks.failures else "ORIGINAL_PAIR_OFFLINE_FAIL",
        "windows_pc_game_integration":"NOT_TESTED", "native_luau":"NOT_TESTED",
        "studio_2client":"NOT_TESTED", "actual_phone":"NOT_TESTED",
        "failures":checks.failures,
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Test two already keyless D16 exact original sources end-to-end; no network or Studio")
    ap.add_argument("--scale-root",required=True,type=Path,help="Verified original D16 SCALE packet root (contains reference/scale_fx.py)")
    ap.add_argument("--visual-root",required=True,type=Path,help="Verified original D16 VISUAL packet root (contains reference/bridge.py and client_policy.py)")
    ap.add_argument("--json-out",type=Path,help="A NEW output file; never overwrites")
    args = ap.parse_args(argv)
    try:
        result = evaluate(args.scale_root,args.visual_root)
    except Exception as exc:
        result={"game_id":"TRAP_RAIDERS","state":"HANDOFF_BLOCKED", "error":f"{type(exc).__name__}:{exc}", "checks_passed":0,"checks_failed":1}
    out=json.dumps(result,indent=2,ensure_ascii=False,sort_keys=True)+"\n"
    print(out,end="")
    if args.json_out is not None:
        with args.json_out.open("x",encoding="utf-8") as f:f.write(out)
    return 0 if result["state"]=="ORIGINAL_PAIR_OFFLINE_PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
