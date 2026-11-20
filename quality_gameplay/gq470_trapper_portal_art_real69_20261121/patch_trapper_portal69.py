#!/usr/bin/env python3
"""Reversible REAL69 quality-art source patch: Trapper paired warp ground markers.

Only SevenRoleCombat's existing two warp-pad visual constructors and their
prompt labels change. No Game, skill action, travel, score, HP, Remote or Store
logic is added or removed. Source/CI PREP is not a Studio/Human ART pass.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import shutil
from pathlib import Path

BASE = "e80973c354f14a0d0088577f3cc1a875454f0f8f"
BRANCH = "rc/p0d-s1-kids-rc01"
FEATURE = "GQ470_FB015_TRAPPER_WARP_FACET_REAL69_20261121"
PORT_MARK = "GQ8_RC86_TRAPPER_PAIR_PORT_20261119"
ROUTE = "ServerScriptService/EGGRUMBLE_SevenRoleCombat"
PROJECT = "EGGRUMBLE_REAL69.project.json"
RECEIPT = "REAL69_LEGACY_INTAKE_RECEIPT.json"
PLACE = "EGGRUMBLE_REAL69_PRIVATE.rbxlx"
OFF = "OFF69_TRAPPER_PORTAL_ART"

OLD_PAD = ''' local pad=Instance.new("Part")
 pad.Name=if state.first then "TrapperExit" else "TrapperEntrance"
 pad.Shape=Enum.PartType.Cylinder
 pad.Size=Vector3.new(.3,6,6)
 pad.CFrame=CFrame.new(ground+Vector3.new(0,.18,0))*CFrame.Angles(0,0,math.rad(90))
 pad.Anchored=true;pad.CanCollide=false;pad.CanTouch=false;pad.CanQuery=false
 pad.Material=Enum.Material.Neon;pad.Color=Color3.fromRGB(184,96,240)
 pad.Transparency=.25;pad.Parent=state.folder
'''

NEW_PAD = ''' -- GQ470_FB015_TRAPPER_WARP_FACET_REAL69_20261121
 -- Keep the current ground pad and safe server teleport; low-glare A/B
 -- landmarks avoid two identical neon disks. Exactly ONE matte silhouette
 -- wedge per endpoint, under the existing expiry/round cleanup folder.
 local pointA=(state.first==nil)
 local pad=Instance.new("Part")
 pad.Name=if state.first then "TrapperExit" else "TrapperEntrance"
 pad.Shape=Enum.PartType.Cylinder
 pad.Size=Vector3.new(.3,6,6)
 pad.CFrame=CFrame.new(ground+Vector3.new(0,.18,0))*CFrame.Angles(0,0,math.rad(90))
 pad.Anchored=true;pad.CanCollide=false;pad.CanTouch=false;pad.CanQuery=false
 pad.Material=Enum.Material.SmoothPlastic
 pad.Color=if pointA then Color3.fromRGB(87,176,167) else Color3.fromRGB(230,161,103)
 pad.Transparency=.16;pad.CastShadow=false;pad.Parent=state.folder
 local facet=Instance.new("WedgePart")
 facet.Name=if pointA then "TrapperPortalFacetA" else "TrapperPortalFacetB"
 facet.Size=Vector3.new(1.8,.35,2.4)
 facet.CFrame=CFrame.new(ground+Vector3.new(0,.23,3.1))
  *CFrame.Angles(0,math.rad(if pointA then 180 else 0),0)
 facet.Anchored=true;facet.CanCollide=false;facet.CanTouch=false;facet.CanQuery=false
 facet.CastShadow=false;facet.Material=Enum.Material.SmoothPlastic
 facet.Color=pad.Color;facet.Transparency=.06;facet.Parent=state.folder
'''

OLD_PROMPT = ' prompt.ActionText="味方ワープ";prompt.ObjectText="空間転移｜残り3回"\n'
NEW_PROMPT = ' prompt.ActionText="味方ワープ";prompt.ObjectText=(if pointA then "転移門A" else "転移門B").."｜残り3回"\n'
OLD_UPDATE = '    pr.ObjectText="空間転移｜残り"..tostring(state.remaining).."回"\n'
NEW_UPDATE = '    pr.ObjectText=(if part==state.first then "転移門A" else "転移門B").."｜残り"..tostring(state.remaining).."回"\n'

def need(ok: bool, key: str) -> None:
    if not ok:
        raise ValueError("RED_TRAPPER_PORTAL_ART_" + key)

def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

def selected(root: Path) -> dict[str, Path]:
    document = json.loads((root / PROJECT).read_text(encoding="utf-8"))
    base = root.resolve()
    found: dict[str, Path] = {}
    def scan(node: object, route: str = "") -> None:
        if not isinstance(node, dict):
            return
        if "$path" in node:
            value = node["$path"]
            need(isinstance(value, str), "BAD_PATH")
            target = (base / value).resolve()
            need(target.is_relative_to(base) and target.is_file(), "ESCAPED_SOURCE_PATH")
            need(route not in found, "DUPLICATE_ROUTE")
            found[route] = target
        for key, child in node.items():
            if key != "$path" and not key.startswith("$"):
                scan(child, route + "/" + key if route else key)
    scan(document["tree"])
    return found

def visual_contract(new_pad: str) -> None:
    # This is static/geometry-budget evidence, not screen-space readability.
    need(re.findall(r'Instance\.new\("([^"]+)"\)', new_pad) ==
         ["Part", "WedgePart"], "EXACT_ONE_ADDED_WEDGE")
    for token in (
        'pad.Shape=Enum.PartType.Cylinder',
        'pad.Size=Vector3.new(.3,6,6)',
        'pad.Material=Enum.Material.SmoothPlastic',
        'facet.Material=Enum.Material.SmoothPlastic',
        'facet.Size=Vector3.new(1.8,.35,2.4)',
        'facet.Parent=state.folder',
        'pad.Parent=state.folder',
        'Color3.fromRGB(87,176,167)',
        'Color3.fromRGB(230,161,103)',
        'facet.Color=pad.Color',
    ):
        need(new_pad.count(token) == 1, "VISUAL_CONTRACT_" + token[:24])
    for kind in ("pad", "facet"):
        for prop in ("CanCollide", "CanTouch", "CanQuery", "CastShadow"):
            need(len(re.findall(r'\b' + kind + r'\.' + prop +
                                r'\s*=\s*false\b', new_pad)) == 1,
                 "NO_PHYSICS_" + kind + "_" + prop)
            need(len(re.findall(r'\b' + kind + r'\.' + prop +
                                r'\s*=\s*true\b', new_pad)) == 0,
                 "PHYSICS_TRUE_" + kind + "_" + prop)
    need('Enum.Material.Neon' not in new_pad and
         'Instance.new("BillboardGui")' not in new_pad and
         "ParticleEmitter" not in new_pad and
         "PointLight" not in new_pad, "NO_OVERBRIGHT_UI_PARTICLES")
    need('facet.Anchored=true' in new_pad and
         'pad.Anchored=true' in new_pad and
         'local pointA=(state.first==nil)' in new_pad,
         "ANCHORED_ENDPOINT_A_B")
    # Both endpoints keep exact same functional trigger/cylinder geometry.
    need('pad.Name=if state.first then "TrapperExit" else "TrapperEntrance"' in new_pad,
         "ORIGINAL_PAD_IDENTITIES")
    need('facet.Transparency=.06' in new_pad and
         'pad.Transparency=.16' in new_pad, "LOW_GLARE_ALPHA")

def transform(source: str) -> str:
    need(FEATURE not in source, "ALREADY_PATCHED")
    for key in (PORT_MARK, 'local function trapperAuthorized(',
                'local function endTrapperWarp(', 'state.remaining-=1',
                'if state.remaining<=0 then endTrapperWarp(ownerPlayer.UserId) end',
                'if not RunService:IsStudio()'):
        need(key in source, "ORIGINAL_RUNTIME_" + key[:20])
    for old, tag in ((OLD_PAD, "PAD"), (OLD_PROMPT, "PROMPT"),
                     (OLD_UPDATE, "USES_LABEL")):
        need(source.count(old) == 1, "EXACT_ORIGINAL_" + tag)
    visual_contract(NEW_PAD)
    changed = (source.replace(OLD_PAD, NEW_PAD, 1)
               .replace(OLD_PROMPT, NEW_PROMPT, 1)
               .replace(OLD_UPDATE, NEW_UPDATE, 1))
    need(changed.count(FEATURE) == 1 and
         changed.count('Instance.new("WedgePart")') ==
         source.count('Instance.new("WedgePart")') + 1, "ONE_DECORATOR")
    need(unpatch(changed) == source, "EXACT_INVERSE")
    return changed

def unpatch(source: str) -> str:
    for token in (NEW_PAD, NEW_PROMPT, NEW_UPDATE):
        need(source.count(token) == 1, "INVERSE_ANCHOR")
    return (source.replace(NEW_PAD, OLD_PAD, 1)
            .replace(NEW_PROMPT, OLD_PROMPT, 1)
            .replace(NEW_UPDATE, OLD_UPDATE, 1))

def self_test() -> None:
    marker = ("-- " + PORT_MARK + "\n"
              + 'if not RunService:IsStudio() then return end\n'
              + 'local function trapperAuthorized(\nend\n'
              + 'local function endTrapperWarp(\nend\n'
              + 'state.remaining-=1\n'
              + 'if state.remaining<=0 then endTrapperWarp(ownerPlayer.UserId) end\n')
    original = marker + OLD_PAD + OLD_PROMPT + OLD_UPDATE
    changed = transform(original)
    need(unpatch(changed) == original, "ROUNDTRIP_INVERSE")
    need('TrapperPortalFacetA' in changed and
         'TrapperPortalFacetB' in changed and
         '転移門A' in changed and '転移門B' in changed, "A_B_SIGNPOSTS")
    for bad in (
        NEW_PAD.replace("facet.CanCollide=false", "facet.CanCollide=true"),
        NEW_PAD.replace("facet.CanQuery=false", "facet.CanQuery=true"),
        NEW_PAD.replace("pad.CastShadow=false", "pad.CastShadow=true"),
        NEW_PAD.replace('Instance.new("WedgePart")', 'Instance.new("Part")'),
        NEW_PAD.replace('facet.Parent=state.folder', 'facet.Parent=workspace'),
        NEW_PAD.replace('Color3.fromRGB(230,161,103)', 'Color3.fromRGB(87,176,167)'),
        NEW_PAD.replace('Enum.Material.SmoothPlastic', 'Enum.Material.Neon'),
        NEW_PAD.replace('local pointA=(state.first==nil)', 'local pointA=true'),
    ):
        try:
            visual_contract(bad)
        except ValueError:
            pass
        else:
            raise AssertionError("RED_VISUAL_MUTANT_ACCEPTED")
    for mutated in (
        changed, original.replace(OLD_PAD, ""),
        original.replace(OLD_PAD, OLD_PAD + OLD_PAD),
        original.replace(OLD_UPDATE, ""), original.replace(PORT_MARK, ""),
        original.replace('state.remaining-=1', 'state.remaining+=1'),
    ):
        try:
            transform(mutated)
        except ValueError:
            pass
        else:
            raise AssertionError("RED_SOURCE_MUTANT_ACCEPTED")
    # Source-level bound: original 1 pad, candidate 1 pad + 1 wedge per endpoint.
    need(len(re.findall(r'Instance\.new\("', NEW_PAD)) == 2,
         "NO_EXTRA_PART_FACTORY")
    print("GQ470_TRAPPER_PORTAL_8_VISUAL_6_SOURCE_NEGATIVES_INVERSE_PASS")

def patch(root: Path) -> None:
    root = root.resolve()
    scripts = selected(root)
    need(len(scripts) == 69 and ROUTE in scripts, "SELECTED69_ROUTE")
    meta_file = root / RECEIPT
    meta = json.loads(meta_file.read_text(encoding="utf-8"))
    before = {k: sha(v.read_bytes()) for k, v in scripts.items()}
    need(meta.get("build_head") == BASE and
         meta.get("selected_source_count") == 69 and
         meta.get("source_hashes") == before, "PINNED_OFFICIAL69")
    need(meta.get("official_branch") == BRANCH and
         (root / PLACE).is_file(), "BRANCH_OR_PLACE")
    old = scripts[ROUTE].read_bytes()
    after_bytes = transform(old.decode("utf-8")).encode("utf-8")
    need(after_bytes != old, "MISSING_SOURCE_DELTA")
    off = root / OFF
    need(not off.exists() and (root / "sources").is_dir(), "ROLLBACK_ALREADY_EXISTS")
    off.mkdir()
    shutil.copytree(root / "sources", off / "sources")
    for name in (PROJECT, RECEIPT, PLACE):
        shutil.copy2(root / name, off / name)
    scripts[ROUTE].write_bytes(after_bytes)
    after = {k: sha(v.read_bytes()) for k, v in selected(root).items()}
    need(len(after) == 69 and set(after) == set(before) and
         {k for k in after if after[k] != before[k]} == {ROUTE},
         "EXACT_ONE_CHANGED_68_UNCHANGED")
    need(selected(off)[ROUTE].read_bytes() == old and
         unpatch(after_bytes.decode("utf-8")).encode("utf-8") == old,
         "EXACT_ROLLBACK")
    need((off / PROJECT).read_bytes() == (root / PROJECT).read_bytes(),
         "PROJECT_CLASS_ROUTE_DRIFT")
    meta["source_hashes"][ROUTE] = sha(after_bytes)
    # Keep the official baseline HEAD in the receipt; the separate feature
    # receipt records that this is only an A PREP candidate, not a formal RC.
    meta["gq470_trapper_portal_art"] = {
        "feature_id": FEATURE, "parent_rc_head": BASE,
        "selected_route": ROUTE, "changed_source_routes": 1,
        "byte_exact_unmodified_routes": 68,
        "extra_visual_parts_per_trapper_max": 2,
        "new_neon_parts": 0,
        "physics_and_queries_new_parts": False,
        "new_scripts": 0, "new_remotes": 0,
        "modified_travel_authority": False,
        "modified_egg_score_hp_store": False,
        "source_rollback": OFF, "studio_solo": "NOT_TESTED",
        "studio_2client": "NOT_TESTED", "android15": "NOT_TESTED",
        "human_art": "NOT_TESTED", "owner_accepted": False
    }
    meta_file.write_text(json.dumps(meta, ensure_ascii=False,
                                    sort_keys=True, indent=2) + "\n",
                         encoding="utf-8")
    print("GQ470_TRAPPER_PORTAL_REAL69_ONE_SOURCE_OFF69_PREP",
          sha(after_bytes))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--base", type=Path)
    args = parser.parse_args()
    if args.self_test:
        self_test()
    else:
        need(args.base is not None, "BASE_REQUIRED")
        patch(args.base)
