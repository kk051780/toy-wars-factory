#!/usr/bin/env python3
"""FB-001/008/015: exact-source neutral horde label de-cluttering (A-only).

This patches ONLY the existing SwarmCombat.soldier() Humanoid display setup.
Roblox Subject makes the NPC's own 0-stud name/16-stud health range win over
the viewpoint's policy. Damaged-only HP keeps close-range combat feedback.
No added visual parts, Remote, store, new script route, or gameplay authority.
Studio/Android/ART/FUN are NOT_TESTED, and formal RC is NOT changed.
"""
from __future__ import annotations

import hashlib

FEATURE = "GQ470_FB001_008_015_NEUTRAL_SUBJECT_READABILITY_20261121"
ROUTE = "ServerScriptService/EGGRUMBLE_SwarmCombat"
ART16_PARENT_SWARM_SHA256 = "09e72ccce28fb669725a71b40e26fac276900a0ffa737f24a193f778b0378925"
START = "local function soldier(parent:Instance,at:Vector3,serial:number):Model\n"
END = "-- Low-cost server-driven physical reaction on the existing accent only.\n"
OLD = (
    " -- GQ8_P0_NEUTRAL_BILLBOARD_DISTANCE_20261120: hide repetitive internal HordeSoldier names and show nearby HP only.\n"
    " h.NameDisplayDistance=0;h.HealthDisplayDistance=16\n"
)
NEW = (
    " -- GQ8_P0_NEUTRAL_BILLBOARD_DISTANCE_20261120: hide repetitive internal HordeSoldier names and show nearby HP only.\n"
    f" -- {FEATURE}: NPC-owned distances rather than viewer-owned distances.\n"
    " -- Retain only near-range damaged HP; no new world/UI Parts.\n"
    " h.DisplayDistanceType=Enum.HumanoidDisplayDistanceType.Subject\n"
    " h.NameDisplayDistance=0;h.HealthDisplayDistance=16\n"
    " h.HealthDisplayType=Enum.HumanoidHealthDisplayType.DisplayWhenDamaged\n"
)

def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def need(ok: bool, why: str) -> None:
    if not ok:
        raise ValueError("RED_GQ470_NEUTRAL_SUBJECT_" + why)

def soldier_section(text: str) -> tuple[int, int, str]:
    need(text.count(START) == text.count(END) == 1, "EXACT_SOLDIER_SCOPE")
    lo, hi = text.index(START), text.index(END)
    need(lo < hi, "SOLDIER_BOUNDARY_ORDER")
    part = text[lo:hi]
    need(
        part.count('m.Name="HordeSoldier"') == 1
        and part.count('m:SetAttribute("EGGRUMBLE_Neutral",true)') == 1
        and part.count('m.PrimaryPart=root') == 1
        and part.count('local h=Instance.new("Humanoid")') == 1
        and part.count('h.Parent=m') == 1
        and part.count('return m') == 1
        and part.count("SPECIES_IDS[(serial-1)%#SPECIES_IDS+1]") == 1
        and "NeutralFinisherPolicy.species(speciesId)" in part,
        "EXACT_EIGHT_SPECIES_NEUTRAL_OWNER",
    )
    return lo, hi, part

def patch(source: bytes) -> bytes:
    need(isinstance(source, bytes), "INPUT_NOT_BYTES")
    text = source.decode("utf-8")
    lo, hi, soldier = soldier_section(text)
    need(FEATURE not in text, "ALREADY_APPLIED")
    need(text.count(OLD) == soldier.count(OLD) == 1, "SOURCE_ANCHOR_DRIFT")
    need("h.DisplayDistanceType=" not in soldier
         and "h.HealthDisplayType=" not in soldier,
         "EXISTING_OWNER_POLICY")
    result = text[:lo] + soldier.replace(OLD, NEW, 1) + text[hi:]
    need(result.replace(NEW, OLD, 1) == text, "UNRELATED_SOURCE_BYTES")
    need(result.count(FEATURE) == 1, "FEATURE_MARKER_DUPLICATED")
    need(not any(x in NEW for x in (
        "Instance.new(", "RemoteEvent", "DataStore", "Marketplace",
        ":TakeDamage(", "RunService", "CanCollide"
    )), "FORBIDDEN_AUTHORITY_OR_PART")
    return result.encode("utf-8")

def verify_art16_overlay(actual: bytes) -> dict:
    text = actual.decode("utf-8")
    _, _, soldier = soldier_section(text)
    need(text.count(NEW) == soldier.count(NEW) == 1, "EXACT_DISPLAY_POLICY")
    parent = text.replace(NEW, OLD, 1).encode("utf-8")
    need(sha(parent) == ART16_PARENT_SWARM_SHA256,
         "ACTUAL_ART16_PARENT_SOURCE_SHA")
    return {
        "feature_id": FEATURE, "route": ROUTE,
        "original_art16_swarm_sha256": ART16_PARENT_SWARM_SHA256,
        "patched_swarm_sha256": sha(actual),
        "new_part_count": 0,
        "studio": "NOT_TESTED", "android": "NOT_TESTED",
        "human_art": "ART_NO_GO", "formal_adopted": False
    }

def selftest() -> int:
    sample = (START
      + ' local m=Instance.new("Model")\n'
      + ' m.Name="HordeSoldier";m:SetAttribute("EGGRUMBLE_Neutral",true)\n'
      + ' local speciesId=SPECIES_IDS[(serial-1)%#SPECIES_IDS+1]\n'
      + ' local profile=NeutralFinisherPolicy.species(speciesId)\n'
      + ' m.PrimaryPart=root\n'
      + ' local h=Instance.new("Humanoid")\n'
      + OLD + ' h.MaxHealth=80;h.Health=80;h.Parent=m\n'
      + ' return m\nend\n' + END).encode()
    output = patch(sample)
    need(output.replace(NEW.encode(), OLD.encode(), 1) == sample, "SOURCE_ROLLBACK")
    need(output.count(b"Instance.new(") == sample.count(b"Instance.new("),
         "ADDED_INSTANCE")
    invalid = [
        output,
        sample.replace(b"NameDisplayDistance=0", b"NameDisplayDistance=22"),
        sample.replace(b"HealthDisplayDistance=16", b"HealthDisplayDistance=100"),
        sample.replace(b'HordeSoldier', b"DifferentOwner"),
        sample.replace(b"EGGRUMBLE_Neutral", b"WRONG_ATTRIBUTE"),
        sample.replace(b'local h=Instance.new("Humanoid")', b'local h=0'),
        sample.replace(b'h.Parent=m', b'h.Parent=workspace'),
        sample.replace(b'NeutralFinisherPolicy.species(speciesId)', b"no_profile()"),
        sample.replace(OLD.encode(), OLD.encode()*2),
        sample.replace(OLD.encode(), b' h.DisplayDistanceType=Enum.HumanoidDisplayDistanceType.Viewer\n'+OLD.encode()),
        sample.replace(START.encode(), b'local function wrong_scope()\n'),
    ]
    for i, bad in enumerate(invalid):
        try:
            patch(bad)
        except (ValueError, UnicodeError):
            continue
        raise AssertionError("UNSAFE_MUTANT_ACCEPTED_" + str(i))
    print("GQ470_NEUTRAL_SUBJECT_SOURCE_11_NEGATIVE_MUTANTS_PASS")
    return len(invalid)

if __name__ == "__main__":
    import argparse
    from pathlib import Path
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--parent-source", type=Path)
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()
    if args.self_test:
        selftest()
    elif args.parent_source and args.out:
        parent = args.parent_source.read_bytes()
        need(sha(parent) == ART16_PARENT_SWARM_SHA256, "PARENT_SHA")
        candidate = patch(parent)
        print(verify_art16_overlay(candidate))
        args.out.write_bytes(candidate)
    else:
        ap.error("Use --self-test or --parent-source + --out")
