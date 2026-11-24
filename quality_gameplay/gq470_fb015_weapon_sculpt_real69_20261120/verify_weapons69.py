#!/usr/bin/env python3
"""GQ470 FB015: source-exact seven-role weapon sculpture; never an ART PASS."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess

FORMAL = "f6c9a503361e95eb6b166c2123ec3d18f8b5c9fc"
TARGET = "ServerScriptService/EGGRUMBLE_WeaponSilhouettes"
EXPECTED_BEFORE = "08b33e6639d61fd07b526b1b41cd448505927acd4675c3c6b975cab4fc7a1ec8"
EXPECTED_V2 = "9a19fa6394b44f3bdf7ed60b09ca789cadfd2eec75eee57d6a0075c3e1a0a741"
EXPECTED_AFTER = "497c6b91e0d02b3f8d15c517e9359d940b39ccf6295529f39286dee04eb42289"
FORMAL_PLACE = {"bytes": 829328, "sha256": "4c35d93b6d8243ecff753ddaef39de0d45d0793085435a21d8f33e4814e78b5a"}
FEATURE = "GQ470_FB015_SEVEN_ROLE_WEAPON_SCULPT_REAL69_20261120"
SOURCE = Path("quality_gameplay/gq470_fb015_weapon_sculpt_real69_20261120/EGGRUMBLE_WeaponSilhouettes.luau")
PROJECT = "EGGRUMBLE_REAL69.project.json"
RECEIPT = "REAL69_LEGACY_INTAKE_RECEIPT.json"
PLACE = "EGGRUMBLE_REAL69_PRIVATE.rbxlx"
ROLES = ("WARRIOR", "MAGE", "NINJA", "TRAPPER", "BUILDER", "BEAST", "ZOMBIE")
PIECES = (5, 4, 5, 4, 5, 4, 5)
TAPERED = ("OdachiBlade", "TwinDaggerNear", "TwinDaggerFar", "TamingHorn", "BeastClawLeft", "BeastClawRight", "PrismProngLeft", "PrismProngRight", "PsiOrbitLeft", "PsiOrbitRight", "RailGunBarrelLeft", "RailGunBarrelRight", "SoulProngLeft", "SoulProngRight")

FRONT_TAPERED = set(TAPERED) - {"RailGunBarrelLeft", "RailGunBarrelRight"}
DOWNWARD_TIP = {"OdachiBlade", "TwinDaggerNear", "TwinDaggerFar", "BeastClawLeft", "BeastClawRight"}

def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()

def demand(ok: bool, code: str) -> None:
    if not ok:
        raise ValueError("RED_GQ470_WEAPON_" + code)

def chosen(root: Path) -> dict[str, tuple[Path, str]]:
    data = json.loads((root / PROJECT).read_text())
    found: dict[str, tuple[Path, str]] = {}
    def scan(node: dict, route: str = "") -> None:
        if "$path" in node:
            file = (root / node["$path"]).resolve()
            demand(file.is_relative_to(root.resolve()) and file.is_file(), "ESCAPED_OR_MISSING_FILE")
            demand(route not in found, "DUPLICATE_ROUTE")
            found[route] = (file, node.get("$className", ""))
        else:
            for key, child in node.items():
                if not key.startswith("$") and isinstance(child, dict):
                    scan(child, f"{route}/{key}" if route else key)
    scan(data["tree"])
    return found

def pieces_by_role(source: str) -> tuple[tuple[int, ...], tuple[tuple[str, ...], ...]]:
    names = []
    counts = []
    for index, role in enumerate(ROLES):
        anchor = ('if' if index == 0 else 'elseif') + f' role=="{role}" then'
        end = ('elseif role==' if index < len(ROLES) - 1 else '\n end\n model:SetAttribute("VisualParts",count)')
        demand(source.count(anchor) == 1, "ROLE_" + role)
        body = source.split(anchor, 1)[1].split(end, 1)[0]
        current = tuple(re.findall(r'piece\("([^"]+)"', body))
        names.append(current)
        counts.append(len(current))
    return tuple(counts), tuple(names)

def check(before: bytes, after: bytes) -> dict:
    demand(digest(before) == EXPECTED_BEFORE, "OFF_SOURCE_SHA")
    demand(digest(after) == EXPECTED_AFTER, "CANDIDATE_SOURCE_SHA")
    old, new = before.decode("utf-8"), after.decode("utf-8")
    demand(FEATURE not in old and new.count(FEATURE) == 1, "MARKER_OR_DOUBLE_PATCH")
    before_parts, before_names = pieces_by_role(old)
    after_parts, after_names = pieces_by_role(new)
    demand(before_parts == after_parts == PIECES, "PARTS_BY_ROLE")
    demand(before_names == after_names, "WEAPON_ID_RENAMED")
    demand(max(after_parts) <= 8 and sum(after_parts) == 32, "MOBILE_PART_CAP")
    demand("PART_BUDGET_PER_AVATAR=8" in new, "BUDGET_DRIFT")
    demand(all(f"{n}=true" in new for n in TAPERED), "TAPERED_ROLE_COVERAGE")
    demand(new.count("p.Transparency=if material==Enum.Material.Neon then .32 else 0") == 1, "WEAPON_GLARE_BUDGET")
    demand(new.count('Instance.new("WedgePart")') == 1, "WEDGE_OBJECT_BUDGET")
    demand("size=Vector3.new(size.Z,size.Y,size.X)" in new
           and "offset=offset*CFrame.Angles(0,yaw,0)" in new
           and "offset=offset*CFrame.Angles(math.pi,0,0)" in new, "FRONT_TAPER_TRANSFORM")
    for marker in ('CanCollide=false', 'CanTouch=false', 'CanQuery=false',
                   'Massless=true', 'CastShadow=false', 'EGGRUMBLE_SafeGrip',
                   'Weapons.clear(player)', 'model:SetAttribute("VisualParts",count)'):
        demand(marker in new, "WELD_OR_PHYSICS_" + marker)
    for danger in ('RemoteEvent', 'RemoteFunction', 'DataStore', 'TakeDamage', 'MarketplaceService'):
        demand(danger not in new, "GAMEPLAY_AUTHORITY_" + danger)
    demand('NINJA={' in new and 'role=="NINJA"' in new, "ASSASSIN_INTERNAL_ID_COMPAT")
    return {
        "old_per_role": before_parts, "new_per_role": after_parts,
        "total_existing_visual_parts": 32, "additional_visual_parts": 0,
        "tapered_geometry_names": TAPERED,
        "front_facet_names": sorted(FRONT_TAPERED),
        "downward_tip_names": sorted(DOWNWARD_TIP),
        "new_selected_scripts": 0, "changed_selected_scripts": 1,
        "art_or_engine_pass": "NOT_TESTED",
    }

def selftest() -> None:
    candidate = SOURCE.read_bytes()
    # With no official artifact, synthesize an old fixture ONLY for negative
    # candidate cases. Full old hash/source and all 69 checks run in apply().
    demand(digest(candidate) == EXPECTED_AFTER, "CURRENT_PR_SHA")
    source = candidate.decode("utf-8")
    demand(len(source.encode("utf-8")) == 7547, "CANDIDATE_BYTE_LENGTH")
    demand(pieces_by_role(source)[0] == PIECES, "ROLE_COUNTS")
    mutations = (
        source.replace('OdachiBlade=true', 'OdachiBlade=false'),
        source.replace('CanCollide=false', 'CanCollide=true'),
        source.replace('role=="ZOMBIE"', 'role=="GHOST"'),
        source.replace('PART_BUDGET_PER_AVATAR=8', 'PART_BUDGET_PER_AVATAR=888'),
        source.replace('Instance.new("WedgePart")', 'Instance.new("Part")'),
        source.replace("PrismProngLeft=true", "PrismProngLeft=false"),
        source.replace("PsiOrbitLeft=true", "PsiOrbitLeft=false"),
        source.replace("RailGunBarrelLeft=true", "RailGunBarrelLeft=false"),
        source.replace("SoulProngLeft=true", "SoulProngLeft=false"),
        source.replace("then .32 else 0", "then .03 else 0"),
        source.replace("size=Vector3.new(size.Z,size.Y,size.X)", "size=Vector3.new(size.X,size.Y,size.Z)"),
        source.replace("offset=offset*CFrame.Angles(math.pi,0,0)", "offset=offset*CFrame.Angles(0,0,0)"),
    )
    for corrupt in mutations:
        demand(digest(corrupt.encode("utf-8")) != EXPECTED_AFTER, "NEGATIVE_FALSE_ACCEPT")
    demand(len(mutations) == 12, "MUTATION_TEST_CASES")
    template = {"build_head": FORMAL, "canonical_build": True, "formal_rc_adoption_proven": True,
                "receipt_provenance": "OFFICIAL", "official_build_head": FORMAL,
                "execution_context": {"kind": "OFFICIAL"}}
    flag_candidate(template)
    demand(template["build_head"] == "PREP_FROM_" + FORMAL
           and template["canonical_build"] is False and template["formal_rc_adoption_proven"] is False
           and template["receipt_provenance"] == "PR_CANDIDATE" and template["official_build_head"] is None
           and template["execution_context"] == {"kind": "PR_SOURCE_PREVIEW", "official_parent": FORMAL},
           "CANDIDATE_PROVENANCE")
    print("GQ470_FB015_WEAPON_CANDIDATE_AND_12_NEGATIVE_SOURCE_MUTANTS_PASS")


def pin(raw: bytes) -> dict:
    return {"bytes": len(raw), "sha256": digest(raw)}

def verify_official(root: Path, meta: dict) -> None:
    manifest_file = "UNION22_DELIVERY_MANIFEST.json"
    manifest = json.loads((root / manifest_file).read_bytes())
    admission = json.loads((root / "UNION22_FINAL_ADMISSION.json").read_bytes())
    demand(admission["formal_rc_adoption_proven"] is True and admission["official_build_head"] == FORMAL
           and admission["receipt_provenance"] == "OFFICIAL" and admission["instances"] == 75
           and meta["canonical_build"] is True and meta["formal_rc_adoption_proven"] is True,
           "OFFICIAL_ADMISSION_NOT_CANDIDATE")
    demand(pin((root / PLACE).read_bytes()) == FORMAL_PLACE, "OFFICIAL_PLACE_IDENTITY")
    present = {p.relative_to(root).as_posix():pin(p.read_bytes()) for p in root.rglob("*")
               if p.is_file() and p != root / manifest_file}
    demand(len(present) == 162 and present == manifest["files"], "OFFICIAL_MANIFEST_162")

def facets_cli(root: Path, binary: Path, former: Path, candidate: Path, output: Path) -> None:
    official = chosen(root / "OFF69_WEAPON")[TARGET][0].read_bytes()
    previous = former.read_bytes()
    final = candidate.read_bytes()
    demand(digest(official)==EXPECTED_BEFORE and digest(previous)==EXPECTED_V2
           and digest(final)==EXPECTED_AFTER, "NATIVE_SOURCE_PINS")
    fixture = (SOURCE.parent / "native_facets.luau").read_bytes()
    sources = {"RC":official,"V2":previous,"FACETS":final}
    for label, raw in sources.items():
        demand(b"]===]" not in raw, "NATIVE_LITERAL")
        fixture += b'\nscan("' + label.encode() + b'",[===[' + raw + b']===])\n'
    output.mkdir(exist_ok=False)
    generated = output / "generated.luau"
    generated.write_bytes(fixture)
    executed = subprocess.run([str(binary), str(generated)], capture_output=True, timeout=30)
    (output / "parts.tsv").write_bytes(executed.stdout)
    (output / "stderr.log").write_bytes(executed.stderr)
    demand(executed.returncode == 0 and not executed.stderr, "NATIVE_EXECUTION")
    decoded = [row.split("\t") for row in executed.stdout.decode().splitlines()]
    demand(len(decoded)==96 and all(len(row)==26 for row in decoded), "NATIVE_ROW_SET")
    variants = {name:{(row[1],row[2]):row[3:] for row in decoded if row[0]==name} for name in sources}
    before, old, fo = (variants[key] for key in sources)
    demand(before.keys()==old.keys()==fo.keys() and len(old)==32, "NATIVE_EXACT_PIECE_SET")
    demand([sum(p[0]=="WedgePart" for p in pieces.values()) for pieces in variants.values()]==[0,14,14],
           "NATIVE_WEDGE_COUNTS")
    found = set()
    for key, prior in old.items():
        after = fo[key]
        if key[1] not in FRONT_TAPERED:
            demand(prior == after, "NATIVE_UNRELATED_VISUAL_DRIFT")
            continue
        demand(prior[:8]==after[:8] and prior[11:14]==after[11:14]
               and after[8:11]==[prior[10],prior[9],prior[8]], "NATIVE_FACET_POSE_AND_EXTENT")
        a, b = ([float(item) for item in row[14:]] for row in (prior, after))
        def column_dot(c0, c1):
            return sum(a[index+c0] * b[index+c1] for index in (0,3,6))
        expected_tip_direction = -1 if key[1] in DOWNWARD_TIP else 1
        demand(abs(column_dot(1,1)-expected_tip_direction)<1e-7
               and abs(abs(column_dot(2,0))-1)<1e-7 and abs(abs(column_dot(0,2))-1)<1e-7,
               "NATIVE_FACET_ORIENTATION_OR_TIP")
        found.add(key[1])
    demand(found==FRONT_TAPERED, "NATIVE_EXPECTED_FACETS")
    report = {"sources":{key:pin(raw) for key,raw in sources.items()}, "generated":pin(fixture),
              "raw":pin(executed.stdout), "native":pin(binary.read_bytes()), "native_rows":len(decoded),
              "front_tapered":sorted(found), "parts_per_version":32, "studio":"NOT_TESTED"}
    (output / "receipt.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print("GQ470_7ROLE_NATIVE_FACETS_EXACT_96_ROWS_AND_12_FACETS_PASS")

def flag_candidate(receipt: dict) -> None:
    receipt.update(build_head="PREP_FROM_" + FORMAL, canonical_build=False,
                   formal_rc_adoption_proven=False, receipt_provenance="PR_CANDIDATE",
                   official_build_head=None,
                   execution_context={"kind": "PR_SOURCE_PREVIEW", "official_parent": FORMAL})

def apply(root: Path, candidate: Path) -> None:
    root = root.resolve()
    mapping = chosen(root)
    demand(len(mapping) == 69 and TARGET in mapping, "REAL69_SELECTED_ROUTES")
    target, cls = mapping[TARGET]
    meta = json.loads((root / RECEIPT).read_text())
    verify_official(root, meta)
    demand(meta["source_classes"].get(TARGET) == "ModuleScript", "EXISTING_MODULE_CLASS")
    demand(meta.get("build_head") == FORMAL and
           meta.get("official_branch") == "rc/p0d-s1-kids-rc01" and
           meta.get("selected_source_count") == 69 and
           len(meta.get("source_hashes", {})) == 69, "FORMAL_EXACT_RECEIPT")
    demand(set(mapping) == set(meta["source_hashes"]), "SELECTED_PATH_SET")
    for route, (path, kind) in mapping.items():
        demand(digest(path.read_bytes()) == meta["source_hashes"][route],
               "PARENT_HASH_" + route)
        demand(not kind or kind == meta["source_classes"][route], "PARENT_CLASS_" + route)
    original = target.read_bytes()
    replacement = candidate.read_bytes()
    findings = check(original, replacement)
    off = root / "OFF69_WEAPON"
    demand(not off.exists(), "DOUBLE_ROLLBACK_DIRECTORY")
    shutil.copytree(root / "sources", off / "sources")
    for name in (PROJECT, RECEIPT, PLACE):
        shutil.copy2(root / name, off / name)
    target.write_bytes(replacement)
    updated = chosen(root)
    old = chosen(off)
    demand(len(updated) == len(old) == 69 and set(updated) == set(old), "ROUTE_LOSS")
    changed = [route for route in updated if
               updated[route][0].read_bytes() != old[route][0].read_bytes()]
    demand(changed == [TARGET], "ONLY_ONE_EXISTING_MODULE_CHANGED")
    demand(all(updated[r][1] == old[r][1] for r in updated), "CLASS_CHANGED")
    demand(old[TARGET][0].read_bytes() == original, "OFF69_NOT_EXACT")
    meta["source_hashes"][TARGET] = EXPECTED_AFTER
    flag_candidate(meta)
    meta["gq470_fb015_weapon_sculpt"] = {
        "feature_id": FEATURE,
        "official_parent_sha": FORMAL,
        "selected_route": TARGET,
        "before_sha256": EXPECTED_BEFORE,
        "after_sha256": EXPECTED_AFTER,
        "other_selected_sources_byte_exact": 68,
        "source_gate": "SOURCE_PREP_PASS",
        "android15": "NOT_TESTED",
        "studio_solo_2client": "NOT_TESTED",
        "art_images_received": 0,
        "art_images_required": 32,
        "owner_accepted": False,
        **findings,
    }
    (root / RECEIPT).write_text(json.dumps(meta, indent=2, ensure_ascii=False, sort_keys=True) + "\n")
    prepared = json.loads((root / RECEIPT).read_bytes())
    demand(prepared["receipt_provenance"] == "PR_CANDIDATE"
           and prepared["canonical_build"] is False and prepared["formal_rc_adoption_proven"] is False
           and prepared["official_build_head"] is None, "PACKAGED_CANDIDATE_PROVENANCE")
    demand(json.loads((off / RECEIPT).read_bytes())["formal_rc_adoption_proven"] is True,
           "OFF69_RECEIPT_PROVENANCE")
    (root / "WEAPON_ART_SOURCE_REPORT.json").write_text(
        json.dumps(meta["gq470_fb015_weapon_sculpt"], indent=2, ensure_ascii=False) + "\n")
    print("GQ470_FB015_SELECTED_ONE_OF_69_WEAPON_SCULPT_SOURCE_AND_EXACT_OFF_PASS")

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--self-test", action="store_true")
    p.add_argument("--base", type=Path)
    p.add_argument("--candidate", type=Path, default=SOURCE)
    p.add_argument("--native", type=Path)
    p.add_argument("--previous-v2", type=Path)
    p.add_argument("--evidence", type=Path)
    args = p.parse_args()
    if args.self_test:
        selftest()
    elif args.native:
        demand(args.base is not None and args.previous_v2 is not None and args.evidence is not None,
               "NATIVE_INPUTS_REQUIRED")
        facets_cli(args.base, args.native, args.previous_v2, args.candidate, args.evidence)
    else:
        demand(args.base is not None, "BASE_REQUIRED")
        apply(args.base, args.candidate)
