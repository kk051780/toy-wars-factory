#!/usr/bin/env python3
"""GQ470 FB-015: source-exact, low-part neutral horde silhouette candidate.

Changes ONLY the soldier() 3-Part visuals of the existing REAL69 SwarmCombat
ModuleScript. No new script, NPC, combat authority, per-frame render loop,
health, KO, source route, or RC branch writer. Studio/Android/ART untested.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] /
                       "gq8_rc85_rc86_real68_nonloss_20261120"))
from verify_nonloss import project_scan

FORMAL_HEAD = "e80973c354f14a0d0088577f3cc1a875454f0f8f"
FORMAL_BRANCH = "rc/p0d-s1-kids-rc01"
FEATURE = "GQ470_FB015_NEUTRAL_HORDE_3_SHAPES_REAL69_20261121"
ROUTE = "ServerScriptService/EGGRUMBLE_SwarmCombat"
PROJECT = "EGGRUMBLE_REAL69.project.json"
RECEIPT = "REAL69_LEGACY_INTAKE_RECEIPT.json"
START = "local function soldier(parent:Instance,at:Vector3):Model\n"
END = "local function labelKo(p:Player,n:number)\n"
OLD_VISUAL = """ local root=piece(m,"HumanoidRootPart",at+Vector3.new(0,2,0),Vector3.new(1.7,2.5,1.5),Color3.fromRGB(127,102,89))
 root.CanTouch=false
 local head=piece(m,"Head",root.Position+Vector3.new(0,1.85,0),Vector3.new(1.3,1.3,1.3),Color3.fromRGB(180,158,128))
 head.Shape=Enum.PartType.Ball;head.CanTouch=false
 piece(m,"Shield",root.Position+Vector3.new(-1.1,-.1,-.25),Vector3.new(.5,1.5,1.4),Color3.fromRGB(94,101,114))
"""
NEW_VISUAL = """ -- GQ470_FB015_NEUTRAL_HORDE_3_SHAPES_REAL69_20261121
 -- Three readable horde silhouettes; STILL exactly three world BaseParts
 -- (root + head + shield). No new Instance loops, collisions, damage, or AI.
 local variant=math.abs(math.floor(at.X*.71)+math.floor(at.Z*1.29)*7)%3
 local kind=if variant==0 then "BULWARK" elseif variant==1 then "SCOUT" else "LANCER"
 m:SetAttribute("EGGRUMBLE_NeutralVisual",kind)
 local bodySize=if variant==0 then Vector3.new(2.05,2.60,1.62)
  elseif variant==1 then Vector3.new(1.40,2.23,1.22)
  else Vector3.new(1.72,2.72,1.37)
 local bodyColor=if variant==0 then Color3.fromRGB(112,100,93)
  elseif variant==1 then Color3.fromRGB(83,118,120)
  else Color3.fromRGB(124,112,83)
 local root=piece(m,"HumanoidRootPart",at+Vector3.new(0,2,0),bodySize,bodyColor)
 root.CanTouch=false
 root.Material=if variant==1 then Enum.Material.Fabric else Enum.Material.Slate
 root.CastShadow=false
 local headSize=if variant==0 then Vector3.new(1.42,1.35,1.42)
  elseif variant==1 then Vector3.new(1.09,1.09,1.09)
  else Vector3.new(1.24,1.50,1.24)
 local headColor=if variant==0 then Color3.fromRGB(184,159,130)
  elseif variant==1 then Color3.fromRGB(148,181,178)
  else Color3.fromRGB(193,178,134)
 local head=piece(m,"Head",root.Position+Vector3.new(0,1.85,0),headSize,headColor)
 head.Shape=Enum.PartType.Ball;head.CanTouch=false;head.CastShadow=false
 -- Replaces the ONE former rectangular shield, never adds a fourth world Part.
 local shield=Instance.new("WedgePart")
 shield.Name="Shield";shield.Anchored=true;shield.CanCollide=false
 shield.Size=if variant==0 then Vector3.new(.77,1.78,1.54)
  elseif variant==1 then Vector3.new(.35,1.26,1.12)
  else Vector3.new(.53,2.06,1.20)
 local tilt=if variant==0 then -13 elseif variant==1 then 23 else -24
 shield.CFrame=CFrame.new(root.Position+Vector3.new(-1.1,-.1,-.25))
  *CFrame.Angles(0,math.rad(tilt),0)
 shield.Color=if variant==0 then Color3.fromRGB(81,92,107)
  elseif variant==1 then Color3.fromRGB(75,113,126)
  else Color3.fromRGB(119,98,67)
 shield.Material=Enum.Material.Slate
 shield.CastShadow=false
 shield.Parent=m
"""

def demand(value: bool, reason: str) -> None:
    if not value:
        raise ValueError("RED_GQ470_NEUTRAL_SHAPES_" + reason)

def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def transform(source: str) -> str:
    demand(FEATURE not in source, "ALREADY_APPLIED")
    if source.count(START) != 1 or source.count(END) != 1:
        # On actual immutable official REAL69 only, surface minimal source
        # anchors for remediation instead of guessing or replacing a new owner.
        import re
        functions = re.findall(r"(?:local\\s+)?function\\s+[A-Za-z0-9_.:]+\\(", source)
        print("GQ470_ACTUAL_SWARM_FUNCTIONS", functions[:65])
        print("GQ470_ACTUAL_SWARM_VISUAL_LINES",
              [s.strip()[:165] for s in source.splitlines()
               if any(k in s for k in ("soldier", "Shield", "HumanoidRootPart",
                                       "labelKo", "NameDisplayDistance", "NEUTRAL_HEALTH"))][:50])
        demand(False, "SOLDIER_SCOPE_OR_FUNCTION_MISSING")
    lo, hi = source.index(START), source.index(END)
    demand(lo < hi, "SOLDIER_SCOPE_ORDER")
    section = source[lo:hi]
    demand(section.count(OLD_VISUAL) == 1, "EXACT_THREE_PART_ART_DRIFT")
    demand('h.NameDisplayDistance=0;h.HealthDisplayDistance=16' in section,
           "EXISTING_P0_NEAR_HP_NAME_POLICY_NOT_PRESERVED")
    demand(section.count(" m.PrimaryPart=root") == 1 and
           section.count(" h.MaxHealth=NEUTRAL_HEALTH") == 1 and
           section.count(" return m") == 1, "NPC_CONTRACT_DRIFT")
    changed = section.replace(OLD_VISUAL, NEW_VISUAL, 1)
    after = source[:lo] + changed + source[hi:]
    demand(after.replace(NEW_VISUAL, OLD_VISUAL, 1) == source,
           "UNRELATED_SCRIPT_BYTES_CHANGED")
    demand(after.count(FEATURE) == 1 and
           changed.count('Instance.new("WedgePart")') == 1 and
           changed.count('piece(m,"HumanoidRootPart"') == 1 and
           changed.count('piece(m,"Head"') == 1 and
           changed.count('piece(m,"Shield"') == 0, "THREE_PART_BUDGET")
    forbidden = ('RemoteEvent', 'DataStoreService', 'MarketplaceService',
                 ':TakeDamage(', 'task.spawn(', 'RunService.', 'CanCollide=true')
    demand(not any(v in NEW_VISUAL for v in forbidden),
           "AUTHORITY_OR_PERFORMANCE_SCOPE")
    return after

def selftest() -> None:
    # Actual original 3-Part visual source from #482, plus official P0 HUD LOD.
    example = ("--!strict\n" + START +
       ' local m=Instance.new("Model")\n m.Parent=parent\n' + OLD_VISUAL +
       ' m.PrimaryPart=root\n local h=Instance.new("Humanoid")\n' +
       ' h.NameDisplayDistance=0;h.HealthDisplayDistance=16\n' +
       ' h.MaxHealth=NEUTRAL_HEALTH;h.Health=NEUTRAL_HEALTH\n' +
       ' return m\nend\n' + END + ' return nil\nend\n')
    transformed = transform(example)
    demand(transformed != example and
           transformed.count("EGGRUMBLE_NeutralVisual") == 1 and
           transformed.count("Instance.new(") == 3,
           "POSITIVE_VISUAL_OUTPUT")
    # Three actual coordinate bins must produce three archetypes.
    bins = {(abs(int(x*.71//1)+int(z*1.29//1)*7)%3)
            for x,z in ((0,0),(0,1),(3,0),(9,-2),(-3,10))}
    demand(bins == {0,1,2}, "DETERMINISTIC_VARIANT_DIVERSITY")
    mutants = (
        transformed,
        example.replace('piece(m,"Shield"', 'piece(m,"ExtraShield"'),
        example.replace('h.HealthDisplayDistance=16', 'h.HealthDisplayDistance=64'),
        example.replace(' m.PrimaryPart=root', ''),
        example.replace(' h.MaxHealth=NEUTRAL_HEALTH', ''),
        example.replace(' return m', ' return nil'),
        example.replace(START, 'local function soldier(parent,at)\n'),
        example + START + "end\n",
    )
    rejected = 0
    for bad in mutants:
        try:
            transform(bad)
        except (ValueError, AssertionError):
            rejected += 1
    demand(rejected == len(mutants), "NEGATIVE_MUTANTS_NOT_REJECTED")
    print("GQ470_NEUTRAL_SHAPES_3_PARTS_THREE_VARIANTS_8_NEGATIVES_PASS")

def selected(root: Path) -> dict:
    result = project_scan(root, PROJECT)
    demand(len(result) == 69 and ROUTE in result, "EXACT_69_SELECTED")
    demand(result[ROUTE]["class"] == "ModuleScript", "OWNER_CLASS")
    return result

def run(root: Path, author_head: str) -> None:
    demand(len(author_head) == 40 and all(c in "0123456789abcdef"
           for c in author_head), "PINNED_AUTHOR_HEAD_REQUIRED")
    receipt_file = root / RECEIPT
    place = root / "EGGRUMBLE_REAL69_PRIVATE.rbxlx"
    demand(receipt_file.is_file() and place.is_file(), "CANONICAL_ARTIFACT_MISSING")
    r = json.loads(receipt_file.read_text(encoding="utf-8"))
    demand(r.get("official_branch") == FORMAL_BRANCH and
           r.get("build_head") == FORMAL_HEAD and
           r.get("source_profile") == "REAL69" and
           r.get("canonical_build") is True, "NOT_VERIFIED_OFFICIAL_PARENT")
    demand(r.get("private_place_sha256") == digest(place.read_bytes()) and
           r.get("private_place_bytes") == place.stat().st_size,
           "CANONICAL_PLACE_RECEIPT")
    before = selected(root)
    demand(set(before) == set(r.get("source_hashes", {})) and
           all(entry["sha256"] == r["source_hashes"][route]
               for route, entry in before.items()) and
           len(r.get("source_classes", {})) == 69 and
           all(entry["class"] == r["source_classes"][route]
               for route, entry in before.items()), "SOURCERECEIPT_69_EXACT")
    src = root / before[ROUTE]["path"]
    original = src.read_bytes()
    candidate = transform(original.decode("utf-8")).encode("utf-8")
    backup = root / "OFF69_SOURCE_EXACT"
    demand(not backup.exists(), "ROLLBACK_COLLISION")
    shutil.copytree(root / "sources", backup / "sources")
    for item in (PROJECT, RECEIPT, place.name):
        shutil.copy2(root / item, backup / item)
    demand((backup / before[ROUTE]["path"]).read_bytes() == original,
           "SOURCE_OFF_NOT_EXACT")
    src.write_bytes(candidate)
    after = selected(root)
    changed = [key for key in before if before[key]["sha256"] != after[key]["sha256"]]
    demand(changed == [ROUTE] and len(before) == len(after) == 69 and
           all(before[k]["class"] == after[k]["class"] and
               before[k]["path"] == after[k]["path"] for k in before) and
           all(before[k]["sha256"] == after[k]["sha256"]
               for k in before if k != ROUTE), "ONE_OF_69_SOURCE_LOCK")
    packet = root / "B220_ONE_SOURCE_NOT_FORMAL"
    target = packet / "selected_sources" / "EGGRUMBLE_SwarmCombat.luau"
    target.parent.mkdir(parents=True)
    target.write_bytes(candidate)
    manifest = {
        "feature_id": FEATURE, "decision": "CONDITIONAL_DEFER_P0_910_ART6_FIRST",
        "design_source_url": "https://github.com/kk051780/toy-wars-factory/issues/219",
        "quality_evidence_url": "https://github.com/kk051780/toy-wars-factory/issues/470",
        "claim_url": "https://github.com/kk051780/toy-wars-factory/issues/218#issuecomment-7052846820",
        "official_branch": FORMAL_BRANCH, "formal_parent_sha": FORMAL_HEAD,
        "author_head_sha": author_head, "route": ROUTE,
        "class": "ModuleScript", "old_sha256": digest(original),
        "new_sha256": digest(candidate), "selected_sources": 69,
        "other_source_bytes_exact": 68, "npc_parts_before": 3,
        "npc_parts_after": 3, "added_world_parts": 0,
        "studio_solo": "NOT_TESTED", "studio_two_client": "NOT_TESTED",
        "matched_camera_png": "0/32", "android_15min": "NOT_TESTED",
        "kid_fun": "NOT_TESTED", "art_gate": "ART_NO_GO",
        "product_gate": "PRODUCT_NO_GO", "owner_accepted": False,
        "formal_rc_adopted": False, "B_QUEUE_READY": "NOT_ATTESTED",
    }
    (packet / "SOURCE_SELECT_MANIFEST.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    r["source_hashes"][ROUTE] = digest(candidate)
    r["build_head"] = author_head
    r["canonical_build"] = False
    r["candidate_only_not_formal"] = manifest
    receipt_file.write_text(json.dumps(r, ensure_ascii=False, indent=2) + "\n",
                            encoding="utf-8")
    (root / "ART_CHECK_REPORT_NEUTRAL_HORDE.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("GQ470_NEUTRAL_HORDE_ACTUAL_SOURCE_1_OF_69_OFF69_PREP_PASS")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--base", type=Path)
    parser.add_argument("--author-head")
    opts = parser.parse_args()
    if opts.self_test:
        selftest()
    else:
        demand(opts.base is not None and opts.author_head, "REQUIRED_ARGS")
        run(opts.base, opts.author_head)
