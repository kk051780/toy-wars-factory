#!/usr/bin/env python3
"""Compose an AUTHOR-EXACT isolated V3 test Place. Never edits author or RC files."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import subprocess

PIN = "fe67d31bc8d1b3e481cd22d2be9ea54a1eb031c9"
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
SOURCE = REPO / "handoffs/P0D-PQG-SEVEN-HERO-PLAYABLE-20261116"
PROJECT = SOURCE / "EGGRUMBLE_V3_STUDIO.project.json"

# Fail closed if the original author changes ANY Studio-only guard. No silent
# mass replacement; only twelve known paths and exactly seventeen guard sites.
GUARDS = {
 "EGGRUMBLE_BotPathRouter.luau": 1,
 "EGGRUMBLE_BotActors.luau": 1,
 "EGGRUMBLE_SwarmCombat.luau": 1,
 "EGGRUMBLE_LobbyCastleModesPreview.server.luau": 1,
 "EGGRUMBLE_SevenRoleCombat.luau": 1,
 "EGGRUMBLE_MatchResultService.luau": 1,
 "EGGRUMBLE_RoundReplay.luau": 6,
 "EGGRUMBLE_DivineMantle.luau": 1,
 "EGGRUMBLE_FieldItemPickups.luau": 1,
 "EGGRUMBLE_NeutralStoneGiant.luau": 1,
 "EGGRUMBLE_CombatFeel.client.luau": 1,
 "EGGRUMBLE_ProceduralSkills.client.luau": 1,
}
ORIGINAL_SERVER = {
 "EGGRUMBLE_CastleMatchRules.luau",
 "EGGRUMBLE_BotPathRouter.luau",
 "EGGRUMBLE_BotActors.luau",
 "EGGRUMBLE_SwarmCombat.luau",
 "EGGRUMBLE_LobbyCastleModesPreview.server.luau",
 "EGGRUMBLE_InteractionGuard.luau",
 "EGGRUMBLE_SevenRoleCombat.luau",
 "EGGRUMBLE_MatchResultService.luau",
 "EGGRUMBLE_CombatBalance.luau",
 "EGGRUMBLE_SkillFX.luau",
 "EGGRUMBLE_RoundReplay.luau",
 "EGGRUMBLE_AttackGeometry.luau",
 "EGGRUMBLE_ImpactFeedback.luau",
 "EGGRUMBLE_WeaponSilhouettes.luau",
 "EGGRUMBLE_DivineMantle.luau",
 "EGGRUMBLE_FieldItemPickups.luau",
 "EGGRUMBLE_RaidItemIntake.luau",
 "EGGRUMBLE_NeutralStoneGiant.luau",
 "EGGRUMBLE_BossSessionFence.luau",
}
ORIGINAL_CLIENT = {
 "EGGRUMBLE_CombatFeel.client.luau",
 "EGGRUMBLE_ProceduralSkills.client.luau",
}
GATE_NAME = "EGGRUMBLE_PrivateLiveGate"
CALL = "RunService:IsStudio()"
INJECT = 'local PrivateGate=require(game:GetService("ReplicatedStorage"):WaitForChild("EGGRUMBLE_PrivateLiveGate"))'
WORLD_MARKER='folder.Name="EGGRUMBLE_LOBBY_CASTLE_MODES_PREVIEW";folder.Parent=workspace'
WORLD_WATCH='if not PrivateGate.watchWorld(folder) then return end'

def add_private_world_watch(source: str) -> str:
    # The original host is the ONLY owner of this arena root. Never hook a
    # duplicate Game or subscribe globally to all of Workspace.
    if source.count(WORLD_MARKER) != 1 or WORLD_WATCH in source:
        raise ValueError("private host anchor moved or already watched")
    return source.replace(WORLD_MARKER, WORLD_MARKER+"\n"+WORLD_WATCH, 1)
assert len(ORIGINAL_SERVER) == 19 and len(ORIGINAL_CLIENT) == 2
assert sum(GUARDS.values()) == 17

def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def pinned_bytes(path: Path) -> bytes:
    rel = path.relative_to(REPO).as_posix()
    cmd = ["git", "-C", str(REPO), "show", f"{PIN}:{rel}"]
    result = subprocess.run(cmd, capture_output=True, check=True)
    return result.stdout

def transform(source: str, name: str) -> tuple[str, int]:
    expected = GUARDS.get(name, 0)
    actual = source.count(CALL)
    if expected != actual:
        raise ValueError(f"guard drift in {name}: expected {expected} got {actual}")
    if not actual:
        return source, 0
    if not source.startswith("--!strict\n"):
        raise ValueError(f"{name} has no strict module header")
    if name in ORIGINAL_CLIENT:
        replacement = "PrivateGate.waitAllowed(8)"
    elif name == "EGGRUMBLE_LobbyCastleModesPreview.server.luau":
        replacement = "PrivateGate.advertiseServerReady()"
    else:
        replacement = "PrivateGate.allowed()"
    patched = source.replace(CALL, replacement)
    patched = patched.replace("--!strict\n", "--!strict\n" + INJECT + "\n", 1)
    if name == "EGGRUMBLE_LobbyCastleModesPreview.server.luau":
        patched = add_private_world_watch(patched)
    if CALL in patched or patched.count(replacement) != expected:
        raise ValueError(f"incomplete guard change: {name}")
    return patched, actual

def mapped_files(project: dict) -> list[tuple[str, str, dict]]:
    rows = []
    for service in ("ServerScriptService", "StarterPlayer"):
        if service == "ServerScriptService":
            tree = project["tree"][service]
        else:
            tree = project["tree"][service]["StarterPlayerScripts"]
        for name, data in tree.items():
            if name == "$className":
                continue
            if not isinstance(data, dict) or set(data) != {"$path"}:
                raise ValueError(f"unexpected project mapping for {name}")
            rows.append((service, data["$path"], data))
    names = {r[1] for r in rows}
    if len(rows) != 21 or names != ORIGINAL_SERVER | ORIGINAL_CLIENT:
        raise ValueError("original 21-source whitelist mismatch")
    if len(names) != 21:
        raise ValueError("duplicate path in game source")
    for service, filename, _ in rows:
        if service == "ServerScriptService" and filename not in ORIGINAL_SERVER:
            raise ValueError("server source cross-mapped to client")
        if service == "StarterPlayer" and filename not in ORIGINAL_CLIENT:
            raise ValueError("client source cross-mapped to server")
    return rows

def build(out: Path) -> dict:
    out = out.resolve()
    if out == REPO or REPO in out.parents or out == SOURCE:
        raise ValueError("output must be OUTSIDE repository; never overwrite original/official source")
    if out.exists() and any(out.iterdir()):
        raise ValueError("output path must be empty (fail closed)")
    original = json.loads(PROJECT.read_text(encoding="utf-8"))
    project = copy.deepcopy(original)
    paths = mapped_files(project)
    out.mkdir(parents=True, exist_ok=True)
    srcdir = out / "sources"
    srcdir.mkdir()
    manifest = {"source_pin": PIN, "runtime": "ISOLATED_PRIVATE_CANARY_ONLY",
                "official_rc_adopted": False, "startup_default": "OFF",
                "sources": [], "modified_guard_sites": 0}
    for service, filename, mapped in paths:
        path = SOURCE / filename
        data = path.read_bytes()
        if pinned_bytes(path) != data:
            raise ValueError(f"author source drift from pinned #{PIN}: {filename}")
        patched, n = transform(data.decode("utf-8"), filename)
        final = patched.encode("utf-8")
        (srcdir / filename).write_bytes(final)
        mapped["$path"] = f"sources/{filename}"
        manifest["modified_guard_sites"] += n
        manifest["sources"].append({
            "owner": "PR#482",
            "service": service,
            "name": filename,
            "author_sha256": digest(data),
            "canary_sha256": digest(final),
            "guard_sites": n,
        })
    if manifest["modified_guard_sites"] != 17:
        raise ValueError("17 original guard sites required")
    gatebytes = (HERE / "EGGRUMBLE_PrivateLiveGate.luau").read_bytes()
    (srcdir / "EGGRUMBLE_PrivateLiveGate.luau").write_bytes(gatebytes)
    project["name"] = "EGGRUMBLE_V3_PRIVATE_CANARY_ONLY_NOT_PUBLIC"
    project["tree"]["ReplicatedStorage"] = {
        "$className": "ReplicatedStorage",
        GATE_NAME: {"$path": f"sources/{GATE_NAME}.luau"},
    }
    # A different dedicated test Place, never the existing production RC Game.
    (out / "EGGRUMBLE_V3_PRIVATE_CANARY.project.json").write_text(
        json.dumps(project, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    manifest["gate_sha256"] = digest(gatebytes)
    (out / "SOURCE_RECEIPT.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return manifest

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    report = build(args.out)
    print(json.dumps({
        "result": "SOURCE_COMPOSITE_ONLY",
        "original_sources": len(report["sources"]),
        "gate_sources": 1,
        "guard_sites": report["modified_guard_sites"],
        "official_rc_adopted": False,
    }, ensure_ascii=False))
