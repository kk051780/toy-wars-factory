#!/usr/bin/env python3
"""Overlay the existing #484 26-source composite into one OFF-by-default private canary.

This does NOT produce or modify any formal RC source, any original author source,
or any production Game/Remote/Store object.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path

import compose

AUTHOR_26 = {
    "game": ("#482", "fe67d31bc8d1b3e481cd22d2be9ea54a1eb031c9"),
    "spatial": ("#484", "6b52eaf1f2725496277998fe0c5532b7a8fcaab5"),
    "art": ("#485", "e86702c906bdf9c71adcdf769ae48a206b26607b"),
    "score": ("#487", "438a406ccfda5563053d783d7561797ccd364361"),
}
ART_GUARDS = {
    "EGGRUMBLE_HeroSilhouetteArt.server.luau": 1,
    "EGGRUMBLE_FlagshipFieldArt.server.luau": 1,
    "EGGRUMBLE_EncounterReadabilityArt.server.luau": 1,
    "EGGRUMBLE_ArtDistanceLOD.client.luau": 1,
}
EXPECTED = {**compose.GUARDS, **ART_GUARDS}
assert len(EXPECTED) == 16 and sum(EXPECTED.values()) == 21
SERVER_COUNT = 23
CLIENT_COUNT = 3
TOTAL = SERVER_COUNT + CLIENT_COUNT

def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def get_sources(project: dict, project_dir: Path) -> dict[str, tuple[str, Path, dict]]:
    tree = project["tree"]
    if set(tree) != {"$className", "ServerScriptService", "StarterPlayer"}:
        raise ValueError("the original composer changed the authoritative Place tree")
    server = tree["ServerScriptService"]
    client = tree["StarterPlayer"]["StarterPlayerScripts"]
    if len(server)-1 != SERVER_COUNT or len(client)-1 != CLIENT_COUNT:
        raise ValueError("the original composer no longer emits exactly 23 server/3 client")
    out = {}
    for service, names in (("ServerScriptService", server), ("StarterPlayer", client)):
        for name, spec in names.items():
            if name.startswith("$"):
                continue
            if name in out or not isinstance(spec, dict) or set(spec) != {"$path"}:
                raise ValueError(f"duplicate, hidden or invalid script {name}")
            path = (project_dir/spec["$path"]).resolve(strict=True)
            if path.suffix != ".luau" or not path.is_file():
                raise ValueError(f"non-Luau original script {name}")
            if not name.startswith("EGGRUMBLE_"):
                raise ValueError(f"unrecognized original author name {name}")
            if service == "ServerScriptService" and path.name.endswith(".client.luau"):
                raise ValueError(f"incorrect LocalScript source {name}")
            if service == "StarterPlayer" and not path.name.endswith(".client.luau"):
                raise ValueError(f"incorrect server script in client scope {name}")
            out[name] = service, path, spec
    if len(out) != TOTAL:
        raise ValueError(f"expected {TOTAL} source scripts")
    if set(out) & {compose.GATE_NAME}:
        raise ValueError("private gate is already present: duplicate authority")
    required = {"EGGRUMBLE_LobbyCastleModesPreview", "EGGRUMBLE_BotActors",
                "EGGRUMBLE_BotPathRouter", "EGGRUMBLE_CastleMatchRules",
                "EGGRUMBLE_SwarmCombat", "EGGRUMBLE_SevenRoleCombat",
                "EGGRUMBLE_FieldItemPickups", "EGGRUMBLE_RaidItemIntake",
                "EGGRUMBLE_NeutralStoneGiant", "EGGRUMBLE_MatchResultService",
                "EGGRUMBLE_ScoreBalance", "EGGRUMBLE_HeroSilhouetteArt",
                "EGGRUMBLE_FlagshipFieldArt", "EGGRUMBLE_EncounterReadabilityArt",
                "EGGRUMBLE_ArtDistanceLOD"}
    if not required.issubset(out):
        raise ValueError(f"missing canonical author domains: {sorted(required - set(out))}")
    return out

def overlay(source: str, name: str, filename: str) -> tuple[str, int]:
    expected = EXPECTED.get(filename, 0)
    actual = source.count(compose.CALL)
    if actual != expected:
        raise ValueError(f"Studio guard count changed: {name}/{filename}, expected {expected}, got {actual}")
    if actual == 0:
        return source, 0
    if not source.startswith("--!strict\n"):
        raise ValueError(f"strict Luau header missing: {name}")
    if name == "EGGRUMBLE_LobbyCastleModesPreview":
        replacement = "PrivateGate.advertiseServerReady()"
    elif filename.endswith(".client.luau"):
        replacement = "PrivateGate.waitAllowed(8)"
    else:
        replacement = "PrivateGate.allowed()"
    inject = 'local PrivateGate=require(game:GetService("ReplicatedStorage"):WaitForChild("EGGRUMBLE_PrivateLiveGate"))'
    final = source.replace("--!strict\n", "--!strict\n" + inject + "\n", 1).replace(compose.CALL, replacement)
    if compose.CALL in final or final.count(replacement) != actual:
        raise ValueError("guard replacement incomplete")
    return final, actual

def build(source_project: Path, source_receipt: Path, out: Path) -> dict:
    source_project = source_project.resolve(strict=True)
    source_receipt = source_receipt.resolve(strict=True)
    out = out.resolve()
    if out == compose.REPO or compose.REPO in out.parents:
        raise ValueError("output must be outside the repository")
    if out.exists() and any(out.iterdir()):
        raise ValueError("output destination must be empty; no silent overwrite")
    original = json.loads(source_project.read_text(encoding="utf-8"))
    upstream = json.loads(source_receipt.read_text(encoding="utf-8"))
    sources = get_sources(original, source_project.parent)
    if set(upstream.get("source_sha256", {})) != set(sources):
        raise ValueError("original composer SHA receipt does not cover all 26")
    if upstream.get("script_count") != TOTAL or upstream.get("status") != "SOURCE_ONLY_NOT_OFFICIAL_RC":
        raise ValueError("original composer receipt claims unexpected status")
    out.mkdir(parents=True, exist_ok=True)
    srcdir = out / "sources"
    srcdir.mkdir()
    doc = copy.deepcopy(original)
    tree = doc["tree"]
    result = {"state": "GQ_PRIVATE_27_SOURCE_QA_CANDIDATE",
              "official_rc_adopted": False, "studio_engine": "NOT_TESTED",
              "android_engine": "NOT_TESTED", "owner_accepted": False,
              "enabled_in_public_server": False, "author_heads": AUTHOR_26,
              "sources": [], "guard_sites": 0}
    for name, (service, path, _) in sorted(sources.items()):
        data = path.read_bytes()
        actual_sha = sha(data)
        if upstream["source_sha256"][name] != actual_sha:
            raise ValueError(f"source not original composer exact: {name}")
        patched, n = overlay(data.decode("utf-8"), name, path.name)
        final = patched.encode("utf-8")
        (srcdir / path.name).write_bytes(final)
        if service == "ServerScriptService":
            spec = tree[service][name]
        else:
            spec = tree["StarterPlayer"]["StarterPlayerScripts"][name]
        spec["$path"] = "sources/" + path.name
        result["guard_sites"] += n
        result["sources"].append({
            "name": name, "service": service, "original_sha256": actual_sha,
            "private_canary_sha256": sha(final), "guard_sites": n,
            "source_path": path.name
        })
    if result["guard_sites"] != 21:
        raise ValueError(f"must intercept 21 exact guard sites; got {result['guard_sites']}")
    gate = (compose.HERE / "EGGRUMBLE_PrivateLiveGate.luau").read_bytes()
    (srcdir / "EGGRUMBLE_PrivateLiveGate.luau").write_bytes(gate)
    tree["ReplicatedStorage"] = {"$className": "ReplicatedStorage",
        compose.GATE_NAME: {"$path": "sources/EGGRUMBLE_PrivateLiveGate.luau"}}
    doc["name"] = "EGGRUMBLE_V3_FULL27_PRIVATE_SERVER_CANARY_UNPUBLISHED"
    (out / "EGGRUMBLE_V3_PRIVATE27.project.json").write_text(
        json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    result["gate_sha256"] = sha(gate)
    result["source_count"] = len(result["sources"])+1
    result["original_receipt_sha256"] = sha(source_receipt.read_bytes())
    if result["source_count"] != 27:
        raise ValueError("source count mismatch")
    (out / "SOURCE_RECEIPT_27.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    return result

if __name__ == "__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--source-project",required=True,type=Path)
    ap.add_argument("--source-receipt",required=True,type=Path)
    ap.add_argument("--out",required=True,type=Path)
    args=ap.parse_args()
    receipt=build(args.source_project,args.source_receipt,args.out)
    print(json.dumps({"result":"SOURCE_COMPOSITE_ONLY", "source_count":receipt["source_count"],
        "guard_sites":receipt["guard_sites"],"formal_rc":receipt["official_rc_adopted"]}))
