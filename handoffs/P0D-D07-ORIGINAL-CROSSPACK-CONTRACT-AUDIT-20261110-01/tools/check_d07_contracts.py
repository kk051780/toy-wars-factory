#!/usr/bin/env python3
"""Read-only D07/D08 keyless source contract preflight; never modifies the game.

The input is the isolated verified 21-packet receipt from the separately
published PUBLIC_SOURCE_V1 intake. This checker does not fetch GitHub, change
source, start Studio, or claim Luau runtime verification.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

PACKETS = {
    "visual": "P0D-D07-GOROGAN-VISUAL-LIBRARY-RECOVER-20261110-01",
    "ai": "P0D-D07-GOROGAN-AI-LIBRARY-RECOVER-20261110-01",
    "combined": "P0D-D07-GOROGAN-COMBINED-LIBRARY-RECOVER-20261110-01",
    "rig": "P0D-D07-GOROGAN-RIGNAV-LIBRARY-RECOVER-20261110-01",
    "event": "P0D-D08-CANONICAL-BRIDGE-PUBLIC-RECOVER-20261110-01",
}
PINNED_COMMITS = {
    "visual": "e9b0a7496a69bda3e0e6527ff4d112d50cf70e80",
    "ai": "d65adccef6ce08ec48854ff2cc99f77e69e0765e",
    "combined": "80a1f0ce15adfb475df0c95677f9966bb760a8ae",
    "rig": "14935dca217391a7d82d809a3856ee602c446704",
    "event": "70dcc3b50129c288441452776360588184ca6c22",
}
MODULES = {
    "visual": ("GoroganVisualPolicy.luau", "GoroganVisualPrefab.luau", "GoroganClientAdapter.client.luau"),
    "ai": ("GoroganServerAICore.luau", "GoroganServerRuntime.luau"),
    "combined": ("GoroganCombinedRuntime.luau",),
    "rig": ("GoroganRigDriver.luau", "GoroganDamageBoundary.luau", "GoroganAttackReceiptWindow.luau"),
    "event": ("CanonicalEventBridge.luau", "CanonicalEventServerAdapter.server.luau"),
}

class SourceBlocked(ValueError):
    pass


def _safe_file(path: Path, parent: Path) -> bytes:
    if path.is_symlink() or not path.is_file() or not path.resolve().is_relative_to(parent.resolve()):
        raise SourceBlocked(f"BLOCKED_MISSING_OR_UNSAFE: {path}")
    return path.read_bytes()


def load_verified(root: Path) -> dict[str, str]:
    """Require original manifest hashes for each Luau file before static analysis."""
    sources: dict[str, str] = {}
    for area, packet in PACKETS.items():
        folder = root / "packs" / packet
        raw = _safe_file(folder / "BUILD_MANIFEST.json", folder)
        try:
            manifest = json.loads(raw)
            if manifest.get("packet_id") != packet:
                raise ValueError("packet id mismatch")
            listed = {f["path"]: f for f in manifest["files"]}
        except (ValueError, KeyError, TypeError) as e:
            raise SourceBlocked(f"BLOCKED_MANIFEST: {packet}: {e}") from e
        for name in MODULES[area]:
            rel = "luau/" + name
            expected = listed.get(rel)
            if not expected:
                raise SourceBlocked(f"BLOCKED_UNLISTED_LUAU: {packet}/{rel}")
            data = _safe_file(folder / rel, folder)
            if len(data) != expected.get("size") or hashlib.sha256(data).hexdigest() != expected.get("sha256"):
                raise SourceBlocked(f"BLOCKED_SHA_MISMATCH: {packet}/{rel}")
            try:
                sources[name] = data.decode("utf-8")
            except UnicodeError as e:
                raise SourceBlocked(f"BLOCKED_INVALID_UTF8: {packet}/{rel}") from e
    return sources


def inspect(sources: dict[str, str]) -> list[dict[str, str]]:
    required = [x for module_names in MODULES.values() for x in module_names]
    missing = sorted(set(required) - set(sources))
    if missing:
        raise SourceBlocked("BLOCKED_MISSING_MODULES: " + ",".join(missing))
    bridge = sources["CanonicalEventBridge.luau"]
    combined = sources["GoroganCombinedRuntime.luau"]
    policy = sources["GoroganVisualPolicy.luau"]
    visual = sources["GoroganVisualPrefab.luau"]
    client = sources["GoroganClientAdapter.client.luau"]
    gate = sources["GoroganDamageBoundary.luau"]
    window = sources["GoroganAttackReceiptWindow.luau"]
    driver = sources["GoroganRigDriver.luau"]
    old_runtime = sources["GoroganServerRuntime.luau"]
    findings: list[dict[str, str]] = []

    def record(code: str, status: str, note: str) -> None:
        findings.append({"code": code, "status": status, "note": note})

    # Direct shape of the two immutable source implementations: cannot pass as-is.
    mismatch = all(x in bridge for x in ("phase = event.event", "validUntil = event.untilAt", "stage = cur.stage")) and all(
        x in combined for x in ('activation.event~="ACTIVATE"', "activation.untilAt", "self.deps.getStageId(roundId)")
    )
    record("D08_TO_D07_ACTIVATE", "REMAP_REQUIRED" if mismatch else "REVIEW_SOURCE_CHANGE",
           "D08 envelope phase/stage/validUntil differs from Combined event/stage via server getter/untilAt. Use only owner-attested server-side mapping; never forge canonical origin.")

    static = ("handle.rootPosition" in visual and "rootPosition=rootPosition" in visual and
              'snapshot.kind == "STOMP"' in policy and 'snapshot.kind == "MOVE"' not in policy and
              'sendVisual(self,a,"START"' in combined and 'sendVisual(self,a,"STOMP"' in combined)
    record("BOSS_VISUAL_MOVEMENT", "VISUAL_TRACKING_REVIEW" if static else "REVIEW_SOURCE_CHANGE",
           "Client visual stays at initial rootPosition; there is no MOVE position update. Validate overlay vs moving real rig in S1 two-client Studio; do not assume hits follow decoration.")

    receipt = ("isCanonicalAttackReceipt" in gate and "getAttackCenter" in gate
               and "function Window:attests" in window and "function Window:center" in window
               and "openFromCoreResult" in combined)
    record("DAMAGE_RECEIPT_WIRING", "TRUSTED_CALLBACK_REQUIRED" if receipt else "REVIEW_SOURCE_CHANGE",
           "Bind Gate attestation and center to the single genuine Window instance only during real STOMP_RESOLVE; never accept client-provided attack receipts.")

    remote = ("TRAP_BossVisualEvent" in client and "TRAP_ActiveMatchId" in client
              and "TRAP_ActiveStage" in client)
    record("CLIENT_REPLICATION_DEPENDENCY", "PC_INTEGRATION_REQUIRED" if remote else "REVIEW_SOURCE_CHANGE",
           "Client adapter requires approved server RemoteEvent and replicated match/stage attributes; verify real PC names and lifecycle before enabling.")

    dual_runtime = ("Core.new()" in old_runtime and "Core.new()" in combined)
    record("ONE_GOROGAN_AI_OWNER", "MUTUAL_EXCLUSION_REQUIRED" if dual_runtime else "REVIEW_SOURCE_CHANGE",
           "Original GoroganServerRuntime and newer CombinedRuntime each own a Core state; select ONE runtime per round, no dual AI/attack scheduling.")

    passed = ("driver:requestNavigation(cmd.position,cmd.reason,now)" in combined
              and "function Driver:requestNavigation(position,reason,now)" in driver)
    record("NAVIGATION_TIME_ARGUMENT", "SOURCE_CONTRACT_ALIGNED" if passed else "REVIEW_SOURCE_CHANGE",
           "Combined forwards server now to Driver requestNavigation (old runtime lacked this argument). Runtime still requires real Studio pathfinding QA.")

    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=Path,
                        help="isolated verified_intake.py output containing packs/<packet>/")
    parser.add_argument("--json", action="store_true")
    ns = parser.parse_args(argv)
    try:
        findings = inspect(load_verified(ns.root))
    except (OSError, SourceBlocked) as e:
        print(json.dumps({"state": "BLOCKED", "reason": str(e)}, ensure_ascii=False))
        return 2
    result = {"state": "SOURCE_STATIC_AUDIT_COMPLETE__NOT_STUDIO",
              "game_id": "TRAP_RAIDERS", "work_id": "p0d-siege-v19",
              "checked_pinned_commits": PINNED_COMMITS,
              "findings": findings, "studio_qa": "NOT_TESTED", "pc_game_integration": "NOT_TESTED"}
    if ns.json:
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        for f in findings:
            print(f"{f['status']:<27} {f['code']}: {f['note']}")
        print("Status: source static audit only, not Windows Codex receipt or Studio QA")
    return 0


if __name__ == "__main__":
    sys.exit(main())
