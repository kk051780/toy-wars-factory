#!/usr/bin/env python3
"""GQ470 FB-015: source-exact, low-part neutral horde silhouette candidate.

Changes ONLY the soldier() 8-species, 3-Part visuals of the REAL69 SwarmCombat
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
FEATURE = "GQ470_FB015_NEUTRAL_HORDE_8_SPECIES_MATTE_FACETS_REAL69_20261121"
ROUTE = "ServerScriptService/EGGRUMBLE_SwarmCombat"
PROJECT = "EGGRUMBLE_REAL69.project.json"
RECEIPT = "REAL69_LEGACY_INTAKE_RECEIPT.json"
START = "local function soldier(parent:Instance,at:Vector3,serial:number):Model\n"
END = "-- Low-cost server-driven physical reaction on the existing accent only.\n"
OLD_VISUAL = """ local sc=visual.scale
 local root=piece(m,"HumanoidRootPart",at+Vector3.new(0,2*sc,0),Vector3.new(1.7,2.5,1.5)*sc,visual.color)
 root.CanTouch=false
 local head=piece(m,"Head",root.Position+Vector3.new(0,1.85*sc,0),Vector3.new(1.3,1.3,1.3)*sc,visual.accent)
 head.Shape=Enum.PartType.Ball;head.CanTouch=false
 local accent=piece(m,"SpeciesAccent",root.Position+Vector3.new(-1.1*sc,-.1*sc,-.25*sc),Vector3.new(.5,1.5,1.4)*sc,visual.accent)
"""
NEW_VISUAL = """ -- GQ470_FB015_NEUTRAL_HORDE_8_SPECIES_MATTE_FACETS_REAL69_20261121
 -- Keep all eight real species, original personality/motion/HP/speed/KO and
 -- original THREE BaseParts per NPC. Only existing silhouettes/materials differ.
 local sc=visual.scale
 local root=piece(m,"HumanoidRootPart",at+Vector3.new(0,2*sc,0),Vector3.new(1.7,2.5,1.5)*sc,visual.color)
 root.CanTouch=false
 root.Material=if speciesId=="ICE_SLIME" then Enum.Material.SmoothPlastic
  elseif speciesId=="ACORN_IMP" then Enum.Material.Wood
  elseif speciesId=="SHY_WRAITH" then Enum.Material.Fabric
  else Enum.Material.Slate
 root.CastShadow=false
 local head=piece(m,"Head",root.Position+Vector3.new(0,1.85*sc,0),Vector3.new(1.3,1.3,1.3)*sc,visual.accent)
 head.Shape=Enum.PartType.Ball;head.CanTouch=false
 head.Material=Enum.Material.SmoothPlastic;head.CastShadow=false
 -- Replace exactly the existing SpeciesAccent, not a fourth Part.
 -- Keep a sphere-capable Part for boar/slime/acorn; wedge-face for five others.
 local accent:BasePart
 if speciesId=="ICE_SLIME" or speciesId=="ACORN_IMP" or speciesId=="SPIKE_BOAR" then
  accent=piece(m,"SpeciesAccent",root.Position+Vector3.new(-1.1*sc,-.1*sc,-.25*sc),Vector3.new(.5,1.5,1.4)*sc,visual.accent)
 else
  local facet=Instance.new("WedgePart")
  facet.Name="SpeciesAccent";facet.Anchored=true;facet.CanCollide=false
  -- Species-specific facet orientation makes banners, shields, ghosts and
  -- sparks distinguishable without adding a part, surface decal or loop.
  local tilt=if speciesId=="BANNER_KNIGHT" then 8
   elseif speciesId=="BABY_GOLEM" then 28
   elseif speciesId=="SPARK_GOBLIN" then -32
   elseif speciesId=="TINY_SHIELD" then 17
   else -11
  facet.CFrame=CFrame.new(root.Position+Vector3.new(-1.1*sc,-.1*sc,-.25*sc))
   *CFrame.Angles(0,math.rad(tilt),0)
  facet.Size=Vector3.new(.5,1.5,1.4)*sc
  facet.Color=visual.accent;facet.Parent=m
  accent=facet
 end
 accent.Material=if speciesId=="SHY_WRAITH" or speciesId=="BANNER_KNIGHT" then Enum.Material.Fabric else Enum.Material.Slate
 accent.CastShadow=false
"""

def demand(value: bool, reason: str) -> None:
    if not value:
        raise ValueError("RED_GQ470_NEUTRAL_SHAPES_" + reason)

def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def transform(source: str) -> str:
    demand(FEATURE not in source, "ALREADY_APPLIED")
    demand(source.count(START) == 1 and source.count(END) == 1,
           "EIGHT_SPECIES_SOLDIER_SCOPE_MISSING")
    lo, hi = source.index(START), source.index(END)
    demand(lo < hi, "SOLDIER_REACTION_ORDER")
    section = source[lo:hi]
    demand(section.count(OLD_VISUAL) == 1, "EXACT_VISUAL_ANCHOR_DRIFT")
    demand(section.count('local speciesId=SPECIES_IDS[(serial-1)%#SPECIES_IDS+1]') == 1
           and 'NeutralFinisherPolicy.species(speciesId)' in section
           and 'm:SetAttribute("EGGRUMBLE_NeutralSpecies",speciesId)' in section,
           "EIGHT_SPECIES_SOURCE_AND_PERSONALITY")
    for species in ("ICE_SLIME", "ACORN_IMP", "SPIKE_BOAR", "SHY_WRAITH",
                    "BANNER_KNIGHT", "BABY_GOLEM", "SPARK_GOBLIN", "TINY_SHIELD"):
        demand(species in section, "EIGHT_SPECIES_NOT_PRESERVED_" + species)
    demand('h.NameDisplayDistance=0;h.HealthDisplayDistance=16' in section,
           "P0_NEAR_HP_NAME_POLICY_NOT_PRESERVED")
    demand('m.PrimaryPart=root' in section and
           'h.MaxHealth=NEUTRAL_HEALTH' in section and
           'return m' in section, "NEUTRAL_GAMEPLAY_CONTRACT")
    # Existing boar is a Part, but the other five accents become WedgeParts.
    # Narrow the union before using Part-only .Shape under --!strict.
    boar_old = 'accent.Shape=Enum.PartType.Ball'
    boar_new = 'if accent:IsA("Part") then accent.Shape=Enum.PartType.Ball end'
    demand(section.count(boar_old) == 1, "BOAR_PART_TYPE_GUARD_DRIFT")
    changed = section.replace(OLD_VISUAL, NEW_VISUAL, 1).replace(
        boar_old, boar_new, 1)
    after = source[:lo] + changed + source[hi:]
    demand(after.replace(NEW_VISUAL, OLD_VISUAL, 1).replace(
        boar_new, boar_old, 1) == source,
           "UNRELATED_SOURCE_BYTES")
    demand(after.count(FEATURE) == 1 and
           NEW_VISUAL.count('Instance.new("WedgePart")') == 1 and
           NEW_VISUAL.count('piece(m,"HumanoidRootPart"') == 1 and
           NEW_VISUAL.count('piece(m,"Head"') == 1 and
           NEW_VISUAL.count('piece(m,"SpeciesAccent"') == 1 and
           'CFrame.Angles(0,math.rad(tilt),0)' in NEW_VISUAL and
           'Enum.Material.Wood' in NEW_VISUAL and
           'Enum.Material.Fabric' in NEW_VISUAL and
           'local accent:BasePart' in NEW_VISUAL,
           "THREE_PART_ACCURATE_SOURCE_COUNT")
    forbidden = ('RemoteEvent', 'DataStoreService', 'MarketplaceService',
                 ':TakeDamage(', 'task.spawn(', 'RunService.', 'CanCollide=true')
    demand(not any(v in NEW_VISUAL for v in forbidden), "NO_NEW_AUTHORITY")
    return after

def selftest() -> None:
    example = ("--!strict\n" + START +
       ' local m=Instance.new("Model")\n' +
       ' local speciesId=SPECIES_IDS[(serial-1)%#SPECIES_IDS+1]\n' +
       ' local profile=NeutralFinisherPolicy.species(speciesId)\n' +
       ' m:SetAttribute("EGGRUMBLE_NeutralSpecies",speciesId)\n' +
       ' local visual=SPECIES_VISUAL[speciesId]\n' +
       OLD_VISUAL +
       ' if speciesId=="ICE_SLIME" or speciesId=="ACORN_IMP" then\n'
       '  root.Shape=Enum.PartType.Ball\n'
       ' elseif speciesId=="SPIKE_BOAR" then\n'
       '  accent.Shape=Enum.PartType.Ball\n'
       ' elseif speciesId=="SHY_WRAITH" then\n'
       '  root.Transparency=.34;head.Transparency=.24\n'
       ' elseif speciesId=="BANNER_KNIGHT" then\n'
       '  accent.Size=Vector3.new(.28,3.2,1.1)*sc\n'
       ' elseif speciesId=="BABY_GOLEM" then\n'
       '  head.Size=Vector3.new(1.7,1.5,1.55)*sc\n'
       ' elseif speciesId=="SPARK_GOBLIN" then\n'
       '  head.Shape=Enum.PartType.Ball\n'
       ' elseif speciesId=="TINY_SHIELD" then\n'
       '  accent.Size=Vector3.new(.55,1.8,1.7)*sc\n end\n'
       ' m.PrimaryPart=root\n'
       ' local h=Instance.new("Humanoid")\n'
       ' h.NameDisplayDistance=0;h.HealthDisplayDistance=16\n'
       ' h.MaxHealth=NEUTRAL_HEALTH;h.Health=NEUTRAL_HEALTH\n'
       ' return m\nend\n' + END +
       'local function playActualReaction(model:Model,cue:any)\n'
       ' local accent=model:FindFirstChild("SpeciesAccent")\nend\n')
    candidate = transform(example)
    demand(candidate.replace(NEW_VISUAL, OLD_VISUAL, 1).replace(
           'if accent:IsA("Part") then accent.Shape=Enum.PartType.Ball end',
           'accent.Shape=Enum.PartType.Ball', 1) == example
           and 'WedgePart' in candidate
           and 'SpeciesAccent' in candidate
           and 'ICE_SLIME' in candidate
           and 'TINY_SHIELD' in candidate
           and candidate.count(FEATURE) == 1, "POSITIVE_EIGHT_PRESERVED")
    corrupts = [
      candidate, example.replace(' local speciesId=SPECIES_IDS[(serial-1)%#SPECIES_IDS+1]', ''),
      example.replace('h.HealthDisplayDistance=16', 'h.HealthDisplayDistance=100'),
      example.replace('m.PrimaryPart=root', ''),
      example.replace(' h.MaxHealth=NEUTRAL_HEALTH', ''),
      example.replace(' return m', ' return nil'),
      example.replace(START, 'local function soldier(parent,at)\n'),
      example.replace('elseif speciesId=="TINY_SHIELD"','elseif speciesId=="OTHER"'),
      example.replace('local accent=piece(m,"SpeciesAccent"', 'local accent=piece(m,"DifferentAccent"'),
      example.replace('accent.Shape=Enum.PartType.Ball', 'accent.Size=Vector3.new(1,1,1)'),
    ]
    failed = 0
    for bad in corrupts:
        try:
            transform(bad)
        except (ValueError, AssertionError):
            failed += 1
    demand(failed == len(corrupts), "MUTANTS_NOT_REJECTED")
    print("GQ470_EIGHT_SPECIES_3PART_MATTE_WEDGE_TEN_NEGATIVES_PASS")

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
        "npc_parts_after": 3, "added_world_parts": 0, "species_kept": 8,
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
