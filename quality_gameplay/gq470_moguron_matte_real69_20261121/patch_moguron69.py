#!/usr/bin/env python3
"""Reversible A-only Moguron art patch for the actual selected REAL69 source.

Applies independently of PR #933 Canyon crystal art; BOTH edit different hunks
of the SAME selected route. B #220 must source-compose and certify one route.
No formal RC, Studio, mobile, human ART, OWNER or FUN acceptance is implied.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import shutil
from pathlib import Path

BASE = "e80973c354f14a0d0088577f3cc1a875454f0f8f"
FEATURE = "GQ470_FB015_MOGURON_MATTE_SILHOUETTE_REAL69_20261121"
ROUTE = "ServerScriptService/EGGRUMBLE_LegacyCanyonRoutes"
PROJECT = "EGGRUMBLE_REAL69.project.json"
RECEIPT = "REAL69_LEGACY_INTAKE_RECEIPT.json"
PLACE = "EGGRUMBLE_REAL69_PRIVATE.rbxlx"
OFF = "OFF69_MOGURON_MATTE"
OLD = ''' local function mole(side:string,x:number)
  local torso=block("Moguron_"..side.."_Body",Vector3.new(4,3,4),
   Vector3.new(x,2.4,-15),Color3.fromRGB(155,106,72),Enum.Material.SmoothPlastic,false)
  torso.Shape=Enum.PartType.Ball
  local nose=block("Moguron_"..side.."_Nose",Vector3.new(1.5,1.2,1.5),
   Vector3.new(x,2.65,-17),gold,Enum.Material.Neon,false)
  nose.Shape=Enum.PartType.Ball
  addPrompt(torso,"橋をひらく","橋掘りモグロン",function(p:Player)
   if not authorized(p,torso) or gateOpen or os.clock()<nextGate then return end
   setGate(true);gateUntil=os.clock()+14
  end)
 end'''
NEW = ''' -- GQ470_FB015_MOGURON_MATTE_SILHOUETTE_REAL69_20261121
 local function mole(side:string,x:number)
  local torso=block("Moguron_"..side.."_Body",Vector3.new(4.8,3.4,3.8),
   Vector3.new(x,2.4,-15),Color3.fromRGB(142,99,73),Enum.Material.SmoothPlastic,false)
  torso.Shape=Enum.PartType.Ball
  torso.CastShadow=false
  local nose=block("Moguron_"..side.."_Nose",Vector3.new(1.85,1.35,1.35),
   Vector3.new(x,2.6,-17.1),Color3.fromRGB(203,159,116),Enum.Material.SmoothPlastic,false)
  nose.Shape=Enum.PartType.Ball
  nose.CastShadow=false
  for _,sign in ipairs({-1,1}) do
   local eye=block("Moguron_"..side.."_Eye"..sign,Vector3.new(.32,.4,.26),
    Vector3.new(x+sign*.9,3.14,-16.72),Color3.fromRGB(38,49,55),Enum.Material.SmoothPlastic,false)
   eye.Shape=Enum.PartType.Ball
   eye.CastShadow=false
   local ear=block("Moguron_"..side.."_Ear"..sign,Vector3.new(.88,1.05,.64),
    Vector3.new(x+sign*2.0,3.55,-14.8),Color3.fromRGB(173,119,88),Enum.Material.SmoothPlastic,false)
   ear.Shape=Enum.PartType.Ball
   ear.CastShadow=false
   local paw=block("Moguron_"..side.."_Paw"..sign,Vector3.new(1.2,.6,1.15),
    Vector3.new(x+sign*1.48,1.08,-16.38),Color3.fromRGB(111,78,64),Enum.Material.SmoothPlastic,false)
   paw.Shape=Enum.PartType.Ball
   paw.CastShadow=false
  end
  -- Keep exactly the original torso prompt: no duplicate activation surface.
  addPrompt(torso,"橋をひらく","橋掘りモグロン",function(p:Player)
   if not authorized(p,torso) or gateOpen or os.clock()<nextGate then return end
   setGate(true);gateUntil=os.clock()+14
  end)
 end'''

def demand(ok: bool, tag: str) -> None:
    if not ok:
        raise ValueError("RED_GQ470_MOGURON_" + tag)

def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()

def selected(root: Path) -> dict[str, Path]:
    doc = json.loads((root / PROJECT).read_text(encoding="utf-8"))
    base = root.resolve()
    out: dict[str, Path] = {}
    def walk(node: object, route: str = "") -> None:
        if not isinstance(node, dict):
            return
        if "$path" in node:
            path = (base / node["$path"]).resolve()
            demand(path.is_relative_to(base) and path.is_file(), "PATH_ESCAPE")
            demand(route not in out, "DUPLICATE_ROUTE")
            out[route] = path
        for key, sub in node.items():
            if not key.startswith("$"):
                walk(sub, route + "/" + key if route else key)
    walk(doc["tree"])
    return out

def check_art_fragment(fragment: str) -> None:
    demand(fragment.count("GQ470_FB015_MOGURON_MATTE_SILHOUETTE_REAL69_20261121") == 1,
           "EXACT_MARKER")
    demand(fragment.count("local torso=block(") == 1 and
           fragment.count("local nose=block(") == 1 and
           fragment.count("local eye=block(") == 1 and
           fragment.count("local ear=block(") == 1 and
           fragment.count("local paw=block(") == 1 and
           fragment.count("block(") == 5, "ANATOMY_AND_PART_BUDGET")
    demand(fragment.count("for _,sign in ipairs({-1,1}) do") == 1,
           "BILATERAL_ONLY")
    demand(fragment.count("CastShadow=false") == 5 and
           fragment.count("Enum.Material.SmoothPlastic,false)") == 5 and
           "Enum.Material.Neon" not in fragment, "MATTE_NO_SHADOW")
    demand(fragment.count("addPrompt(torso,") == 1 and
           fragment.count("authorized(p,torso)") == 1 and
           fragment.count("setGate(true);gateUntil=os.clock()+14") == 1,
           "PROMPT_ORIGINAL_AUTHORITY")
    demand("Instance.new(" not in fragment and
           'Instance.new("RemoteEvent")' not in fragment and "DataStore" not in fragment,
           "NO_EXTRA_OWNERS")
    demand("local torso=block(" in fragment and
           "Enum.Material.SmoothPlastic,false)" in fragment, "NON_PHYSICS")

def transform(source: str) -> str:
    demand(FEATURE not in source, "DOUBLE_APPLY")
    demand(source.count(OLD) == 1, "ORIGINAL_MOGURON_ANCHOR")
    demand("GQ8_RC85_RC86_WCS_STARRY_METEOR_REAL67_20261119" in source,
           "ORIGINAL_WCS_OWNER")
    demand('if not RunService:IsStudio() then return end' in source,
           "STUDIO_ONLY")
    demand(source.count('mole("WEST",-34);mole("EAST",34)') == 1,
           "TWO_MOGURON_OWNERS")
    for literal in (
        'if gateOpen and os.clock()>=gateUntil and not occupied(-15,13) then',
        'stage:SetAttribute("SafeRouteAlwaysAvailable",true)',
        'local safe=block("AlwaysOpenSafeRoute"',
        'local shortcut=block("ShortcutBridge"',
        'gate.CanCollide=not open',
        'p:GetAttribute("EGGRUMBLE_QueuedMode")~=mode',
        'CanTouch=false;p.CanQuery=collide;p.CanCollide=collide',
        'for i=1,7 do',  # Both #933 original / composed facet loop.
    ):
        demand(literal in source, "ORIGINAL_GAMEPLAY_GUARD")
    check_art_fragment(NEW)
    before, after = source.split(OLD, 1)
    candidate = before + NEW + after
    demand(candidate.count(FEATURE) == 1 and
           candidate.replace(NEW, OLD, 1) == source, "MOLE_ONLY_DIFF")
    return candidate

def self_test() -> None:
    check_art_fragment(NEW)
    for mutant in (
        NEW.replace("CastShadow=false", "CastShadow=true", 1),
        NEW.replace("Enum.Material.SmoothPlastic,false)",
                    "Enum.Material.Neon,false)", 1),
        NEW.replace("for _,sign in ipairs({-1,1}) do",
                    "for _,sign in ipairs({-1,0,1}) do"),
        NEW.replace("local paw=block(", "local paw=Instance.new(", 1),
        NEW.replace("setGate(true);gateUntil=os.clock()+14",
                    "setGate(true);gateUntil=os.clock()+5"),
        NEW.replace("addPrompt(torso,", "addPrompt(nose,", 1),
        NEW.replace("authorized(p,torso)", "true", 1),
    ):
        try:
            check_art_fragment(mutant)
        except ValueError:
            pass
        else:
            raise AssertionError("RED_MOGURON_MUTATION_WAS_ACCEPTED")
    demand(OLD.count('addPrompt(torso,') == 1 and
           OLD.count("block(") == 2 and
           NEW.count("block(") == 5, "PART_BUDGET_BEFORE_AFTER")
    demand(NEW.count("for _,sign in ipairs({-1,1}) do") == 1,
           "EIGHT_PARTS_PER_NPC")
    print("GQ470_MOGURON_7_NEGATIVE_MUTATIONS_PASS_EXTRA24_PARTS_FOR_2_MODES")
    print("SOURCE_ONLY_NOT_STUDIO_NOT_ART_NOT_OWNER")

def patch(root: Path) -> None:
    root = root.resolve()
    paths = selected(root)
    demand(len(paths) == 69 and ROUTE in paths, "EXACT_SELECTED69")
    receipt_path = root / RECEIPT
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    current = {route: sha(path.read_bytes()) for route, path in paths.items()}
    demand(receipt.get("canonical_build") is True and
           receipt.get("build_head") == BASE and
           receipt.get("selected_source_count") == 69 and
           receipt.get("source_hashes") == current, "PINNED_HEAD_ALL69_HASHES")
    demand((root / PLACE).is_file(), "REAL69_PLACE_REQUIRED")
    original = paths[ROUTE].read_bytes()
    altered = transform(original.decode("utf-8")).encode("utf-8")
    demand(altered != original, "ACTUAL_SOURCE_DELTA")
    off = root / OFF
    demand(not off.exists(), "OFF_DUPLICATE")
    off.mkdir()
    shutil.copytree(root / "sources", off / "sources")
    for file in (PROJECT, RECEIPT, PLACE):
        shutil.copyfile(root / file, off / file)
    paths[ROUTE].write_bytes(altered)
    after = {route: sha(path.read_bytes()) for route, path in selected(root).items()}
    demand(set(after) == set(current) and
           {key for key in after if after[key] != current[key]} == {ROUTE},
           "EXACT_ONE_SELECTED_SOURCE_CHANGED_OTHER68_IDENTICAL")
    demand(selected(off)[ROUTE].read_bytes() == original,
           "OFF69_BYTE_EXACT")
    receipt["source_hashes"][ROUTE] = sha(altered)
    receipt["gq470_moguron_matte"] = {
        "feature_id": FEATURE,
        "selected_route": ROUTE,
        "official_parent": BASE,
        "original_source_sha256": sha(original),
        "candidate_source_sha256": sha(altered),
        "changed_routes": 1,
        "other68_byte_exact": True,
        "part_count_per_moguron_old_new": [2, 8],
        "max_mogurons_two_modes": 4,
        "extra_parts_total_two_modes": 24,
        "new_physics_owners": False,
        "prompt_authority_unchanged": True,
        "compatible_crystal_art_pr": 933,
        "same_route_requires_b220_composition": True,
        "rollback": OFF,
        "engine": "NOT_TESTED", "studio": "NOT_TESTED",
        "android": "NOT_TESTED", "human_art": "NOT_TESTED",
        "owner_accepted": False
    }
    receipt_path.write_text(json.dumps(receipt, ensure_ascii=False,
                                       indent=2, sort_keys=True) + "\n",
                            encoding="utf-8")
    print("GQ470_MOGURON_REAL69_ONE_SOURCE_OTHER68_EXACT_OFF69_PREP",
          sha(altered))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--base", type=Path)
    opts = parser.parse_args()
    if opts.self_test:
        self_test()
    else:
        demand(opts.base is not None, "REAL69_BUILD_INPUT_REQUIRED")
        patch(opts.base)
