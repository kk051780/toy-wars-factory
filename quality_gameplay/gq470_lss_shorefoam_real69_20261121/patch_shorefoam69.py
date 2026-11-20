#!/usr/bin/env python3
"""GQ470 FB011/015: exact, reversible player-visible shoreline surf patch.

One original Luau selected route, never an extra Game/Host or third RC.
SOURCE/BUILD gates are not Studio, Android, FUN or OWNER acceptance.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
from pathlib import Path, PurePosixPath
import shutil
import zipfile

BASE_HEAD = "e80973c354f14a0d0088577f3cc1a875454f0f8f"
TARGET = "ServerScriptService/EGGRUMBLE_LandSeaSkyTraversal"
TARGET_FILE = "sources/" + TARGET + ".server.luau"
MARK = "GQ470_FB011_FB015_LSS_SHORE_FOAM_FACETS_REAL69_20261121"
ORIGINAL_PATH = "handoffs/EGGRUMBLE-LAND-SEA-SKY-20261117/EGGRUMBLE_LandSeaSkyTraversal.server.luau"
OLD = " for i=1,6 do\n  local xi=x-265+(i-1)*106\n  local foam=put(scene,\"ShoreFoam_\"..i,\n   CFrame.new(xi,y+0.21,shoreZ-63),Vector3.new(55,.10,2.3),\n   Color3.fromRGB(225,247,248),Enum.Material.SmoothPlastic,false,.19)\n end"
NEW = " -- GQ470_FB011_FB015_LSS_SHORE_FOAM_FACETS_REAL69_20261121\n -- Six original, visual-only surf patches. Varied ellipses break up the\n -- six glaring rectangular stripes while preserving route and part budget.\n -- All foam stays shallow, noncolliding and outside the public land dock.\n for i=1,6 do\n  local xi=x-265+(i-1)*106\n  local sideways=if i%2==0 then 1 else -1\n  local drift=math.sin(i*1.73)*1.55\n  local surfAngle=math.rad(sideways*(7+(i%3)*4))\n  local width=47+(i%3)*5\n  local foam=put(scene,\"ShoreFoam_\"..i,\n   CFrame.new(xi,y+0.21,shoreZ-63+drift)*CFrame.Angles(0,surfAngle,0),\n   Vector3.new(width,.10,2.0+(i%2)*.45),\n   if i%2==0 then Color3.fromRGB(190,225,228)\n    else Color3.fromRGB(207,235,237),\n   Enum.Material.SmoothPlastic,false,.33)\n  -- Cylinder's local X axis is the length: flattened oval-like surf,\n  -- not a thick pipe, and neither casts nor receives physics queries.\n  foam.Shape=Enum.PartType.Cylinder\n  foam.CastShadow=false\n  foam.CanQuery=false\n end"

def require(ok: bool, reason: str) -> None:
    if not ok:
        raise ValueError("RED_GQ470_SHOREFOAM_" + reason)

def digest(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()

def patch(source: str) -> str:
    require(MARK not in source, "ALREADY_PATCHED")
    require(source.count(OLD) == 1, "UNIQUE_SIX_FOAM_ANCHOR")
    for expected in ("if not RunService:IsStudio() then return end",
                     "MAX_PARTS_PER_WORLD = 95",
                     "COASTAL_WATER_VISUAL_ONLY",
                     "OFFSHORE_NAVIGABLE_SEA_LANE",
                     "PublicOffshoreShuttle", "PublicCloudLift_",
                     "local function makeRide", "ShoreFoam_"):
        require(expected in source, "SINGLE_OWNER_" + expected)
    candidate = source.replace(OLD, NEW, 1)
    require(candidate.count(MARK) == 1, "MARK")
    require(candidate.count('local foam=put(scene,"ShoreFoam_"..i,') == 1,
            "ONE_SIX_PART_LOOP")
    require(candidate.count("foam.Shape=Enum.PartType.Cylinder") == 1 and
            candidate.count("foam.CanQuery=false") == 1, "SURF_AND_NO_QUERY")
    require(unpatch(candidate) == source, "BYTE_EXACT_OFF")
    return candidate

def unpatch(candidate: str) -> str:
    require(candidate.count(NEW) == 1, "OFF_ANCHOR")
    return candidate.replace(NEW, OLD, 1)

def routes(project: dict) -> dict[str, str]:
    seen: dict[str, str] = {}
    def walk(node: dict, route: str = "") -> None:
        if "$path" in node:
            require(route not in seen, "DUP_ROUTE_" + route)
            seen[route] = node["$path"]
            return
        for name, child in node.items():
            if not name.startswith("$") and isinstance(child, dict):
                walk(child, route + "/" + name if route else name)
    walk(project["tree"])
    return seen

def build(archive_path: Path, out: Path) -> dict:
    require(not out.exists(), "DEST_EXISTS")
    with zipfile.ZipFile(archive_path) as archive:
        names = archive.namelist()
        require(all(not n.startswith("/") and ".." not in PurePosixPath(n).parts
                    for n in names), "ZIP_TRAVERSAL")
        project_bytes = archive.read("EGGRUMBLE_REAL69.project.json")
        receipt_bytes = archive.read("REAL69_LEGACY_INTAKE_RECEIPT.json")
        project = json.loads(project_bytes)
        receipt = json.loads(receipt_bytes)
        selected = routes(project)
        require(receipt.get("build_head") == BASE_HEAD, "BASE_RC_HEAD")
        require(receipt.get("selected_source_count") == len(selected) == 69,
                "REAL69_COUNT")
        require(set(selected) == set(receipt.get("source_hashes", {})), "ROUTES")
        require(selected.get(TARGET) == TARGET_FILE, "TARGET_ROUTE_CLASS")
        require(TARGET_FILE in names, "MISSING_TARGET")
        source_bytes = {}
        for route, name in selected.items():
            require(name in names and name.startswith("sources/"), "FILE_PATH_" + route)
            data = archive.read(name)
            require(digest(data) == receipt["source_hashes"][route],
                    "BEFORE_SHA_" + route)
            source_bytes[route] = data
        old = source_bytes[TARGET]
        candidate = patch(old.decode("utf-8")).encode("utf-8")
        require(unpatch(candidate.decode("utf-8")).encode("utf-8") == old,
                "BYTE_EXACT_OFF69")
        out.mkdir(parents=True)
        for route, name in selected.items():
            path = out / name
            require(path.resolve().is_relative_to(out.resolve()), "PATH_ESCAPE")
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(candidate if route == TARGET else source_bytes[route])
        (out / "EGGRUMBLE_REAL69.project.json").write_bytes(project_bytes)
        (out / "OFF69_ORIGINAL_REAL69_RECEIPT.json").write_bytes(receipt_bytes)
        (out / "OFF69_ORIGINAL_LSS.server.luau").write_bytes(old)
        next_receipt = copy.deepcopy(receipt)
        next_receipt["source_hashes"][TARGET] = digest(candidate)
        next_receipt["candidate_only_gq470_shorefoam"] = {
            "feature": MARK,
            "formal_rc_head_unchanged": BASE_HEAD,
            "selected_route_changed": TARGET,
            "other_selected_routes_byte_exact": 68,
            "original_source_sha256": digest(old),
            "candidate_source_sha256": digest(candidate),
            "decorative_parts_before_after": [6, 6],
            "physics_collision_change": False,
            "new_script_count": 0,
            "engine": "NOT_TESTED",
            "android": "NOT_TESTED",
            "art_gate": "NO_GO",
            "owner_accepted": False,
            "official_rc_adopted": False
        }
        (out / "REAL69_LEGACY_INTAKE_RECEIPT.json").write_text(
            json.dumps(next_receipt, indent=2, sort_keys=True, ensure_ascii=False) + "\n")
        report = {
            "formal_base_head": BASE_HEAD,
            "selected_source_count": 69,
            "changed_selected_routes": [TARGET],
            "unchanged_selected_routes": 68,
            "new_parts": 0,
            "new_remotes": 0,
            "part_count_preserved": True,
            "source_bytes_before": len(old),
            "source_bytes_after": len(candidate),
            "source_sha_before": digest(old),
            "source_sha_after": digest(candidate),
            "rollback_byte_exact": True,
            "formal_rc_changed": False,
            "studio": "NOT_TESTED",
            "android": "NOT_TESTED",
            "art_gate": "NO_GO",
        }
        (out / "GQ470_SHOREFOAM_SOURCE_QA.json").write_text(
            json.dumps(report, indent=2, ensure_ascii=False) + "\n")
        return report

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--artifact", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    print(json.dumps(build(args.artifact, args.out), indent=2))

if __name__ == "__main__":
    main()
