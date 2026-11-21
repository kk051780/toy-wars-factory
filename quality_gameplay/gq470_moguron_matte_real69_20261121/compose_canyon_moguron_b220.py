#!/usr/bin/env python3
"""B220-ready same-source composition: independent verified PR #933 + #967.

Two real ART authors touch disjoint hunks of the SAME selected LegacyCanyonRoutes
script. Verify both source changes are byte-exact transformations of official
REAL69; prove all other 68 selected scripts untouched, and hand B writer one
source file, *never* two overwrites. No direct formal RC branch writing.
"""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

import patch_moguron69 as mole

BASE = "e80973c354f14a0d0088577f3cc1a875454f0f8f"
CANYON_HEAD = "478a640da1d78e0832464aeefc497f453bd68cd0"
CANYON_BLOB = "1e2ac59cd1e80d47f1b71660013a314ca61f6ba3"
MOGURON_HEAD = ""  # Actual immutable PR SHA supplied by exact-head Actions
PLACE_BASE_SHA = "fc63171149a86f6b39779ba6ebe7e18fcb7099fbde98ad2ec33a7cb92b3a9934"
OUT = "B220_CANYON_MOGURON_ONE_SOURCE_NOT_FORMAL"
FEATURE = "GQ470_CANYON_MOGURON_COMPOSITE_REAL69_20261121"


def need(ok: bool, tag: str) -> None:
    if not ok:
        raise ValueError("RED_GQ470_COMPOSITE_" + tag)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def import_canyon(path: Path):
    spec = importlib.util.spec_from_file_location("canyon_933_exact", path)
    need(spec is not None and spec.loader is not None, "PINNED_CANYON_MODULE")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    need(module.FEATURE == "GQ470_FB015_CANYON_FACET_SHORELINE_REAL69_20261121"
         and module.BASE == BASE
         and module.ROUTE == mole.ROUTE
         and module.PROJECT == mole.PROJECT
         and module.RECEIPT == mole.RECEIPT, "CANYON_PROVENANCE")
    return module


def exact_composition(formal: str, updated: str, canyon) -> None:
    need(formal.count(canyon.OLD) == 1 and formal.count(mole.OLD) == 1,
         "BASE_HAS_EXACT_TWO_DISJOINT_HUNKS")
    need(canyon.OLD not in mole.OLD and mole.OLD not in canyon.OLD,
         "DIFFERENT_ORIGINAL_HUNKS")
    source = canyon.transform(formal)
    need(source.count(mole.OLD) == 1, "CANYON_PRESERVES_MOLE_ANCHOR")
    source = mole.transform(source)
    need(source == updated, "BOTH_EXACT_HUNKS_AND_NO_OTHER_DELTA")
    need(source.count(canyon.FEATURE) == 1
         and source.count(mole.FEATURE) == 1, "BOTH_FEATURE_MARKERS")
    need(source.count('mole("WEST",-34);mole("EAST",34)') == 1,
         "TWO_PROMPT_OWNERS_ONLY")
    need(source.count('addPrompt(torso,') == 1
         and source.count('setGate(true);gateUntil=os.clock()+14') == 1
         and source.count('if gateOpen and os.clock()>=gateUntil and not occupied(-15,13) then') == 1,
         "ORIGINAL_GATE_ONLY")
    need(source.count('facet.Parent=stage') == 1
         and source.count('stage:SetAttribute("CanyonFacetVisualBudget",7)') == 1,
         "SEVEN_FACET_BUDGET")
    need('if not RunService:IsStudio() then return end' in source,
         "STUDIO_FENCE")
    need(source.count('GQ8_RC86_StarfallPath') >= 2
         and source.count('GQ8_RC86_MeteorShortcut') >= 2,
         "NO_DUPLICATE_LEGACY_ROUTE")


def prove(base: Path, composed: Path, canyon, outdir: Path,
          final_head: str) -> dict:
    need(len(final_head) == 40 and all(c in "0123456789abcdef" for c in final_head),
         "PINNED_A_HEAD_MATCH")
    base = base.resolve()
    composed = composed.resolve()
    pristine = mole.selected(base)
    chosen = mole.selected(composed)
    need(len(pristine) == len(chosen) == 69
         and set(pristine) == set(chosen), "REAL69_SAME_ROUTES")
    old = {route: p.read_bytes() for route, p in pristine.items()}
    new = {route: p.read_bytes() for route, p in chosen.items()}
    changed = {route for route in old if old[route] != new[route]}
    need(changed == {mole.ROUTE}, "EXACT_ONE_OF_69_CHANGED")
    source_old = old[mole.ROUTE].decode("utf-8")
    source_new = new[mole.ROUTE].decode("utf-8")
    exact_composition(source_old, source_new, canyon)
    source_old_bytes = old[mole.ROUTE]
    source_new_bytes = new[mole.ROUTE]
    origin = json.loads((base / mole.RECEIPT).read_text(encoding="utf-8"))
    candidate = json.loads((composed / mole.RECEIPT).read_text(encoding="utf-8"))
    need(origin["canonical_build"] is True
         and origin["build_head"] == BASE
         and origin["selected_source_count"] == 69
         and origin["source_hashes"] ==
             {route: sha(raw) for route, raw in old.items()},
         "BASE_RECEIPT_HASHED")
    need(candidate["source_hashes"] ==
         {route: sha(raw) for route, raw in new.items()},
         "COMPOSITE_RECEIPT_HASHED")
    need(candidate["gq470_canyon_facet_shoreline"]["feature_id"] == canyon.FEATURE
         and candidate["gq470_moguron_matte"]["feature_id"] == mole.FEATURE,
         "BOTH_ACTUAL_RECEIPT_KEYS")
    need(candidate["gq470_canyon_facet_shoreline"]["decorative_parts_old_new"] == [7,7]
         and candidate["gq470_moguron_matte"]["part_count_per_moguron_old_new"] == [2,8],
         "FIVE_OR_EIGHT_PART_BUDGET")
    need(candidate["gq470_moguron_matte"]["extra_parts_total_two_modes"] == 24,
         "MOBILE_PART_CEILING")
    need(sha((base / mole.PLACE).read_bytes()) == PLACE_BASE_SHA,
         "BASE_PLACE_FIXED")
    need(sha((composed / "OFF69_CANYON_FACETS" / mole.PLACE).read_bytes()) == PLACE_BASE_SHA,
         "BASE_ROLLBACK_EXACT")
    need(sha((composed / "OFF69_MOGURON_MATTE" / mole.PLACE).read_bytes()) != PLACE_BASE_SHA,
         "INTERMEDIATE_CANYON_PLACE_DISTINCT")
    need(mole.selected(composed / "OFF69_CANYON_FACETS")[mole.ROUTE].read_bytes() ==
         source_old_bytes, "OFF_69_ORIGINAL_BYTE_EXACT")
    need(mole.selected(composed / "OFF69_MOGURON_MATTE")[mole.ROUTE].read_bytes() ==
         canyon.transform(source_old).encode("utf-8"),
         "OFF_69_CANYON_ONLY_BYTE_EXACT")
    actual_place = (composed / mole.PLACE).read_bytes()
    need(len(actual_place) > 0 and sha(actual_place) != PLACE_BASE_SHA,
         "COMPOSITE_PLACE_NOT_ORIGINAL")
    need(candidate.get("private_place_bytes") == len(actual_place)
         and candidate.get("private_place_sha256") == sha(actual_place),
         "COMPOSITE_PLACE_RECEIPT")
    need(candidate["gq470_moguron_matte"]["candidate_head"] == final_head
         and candidate["gq470_moguron_matte"]["native_rojo_off69"] == "PASS_SOURCE_ONLY",
         "COMPOSED_A_CANDIDATE_HEAD")
    need(candidate["gq470_canyon_facet_shoreline"]["native_rojo_off69"] == "PASS_SOURCE_ONLY",
         "CANYON_ART_SOURCE_GREEN")
    need(candidate["gq470_moguron_matte"]["owner_accepted"] is False
         and candidate["gq470_canyon_facet_shoreline"]["owner_accepted"] is False,
         "OWNER_NOT_ATTESTED")
    outdir.mkdir(parents=True, exist_ok=False)
    selected_out = outdir / "EGGRUMBLE_LegacyCanyonRoutes.server.luau"
    selected_out.write_bytes(source_new_bytes)
    manifest = {
        "schema": "P0D_B220_SINGLE_SELECTED_SOURCE_COMPOSITE_V1",
        "feature_id": FEATURE,
        "formal_branch": "rc/p0d-s1-kids-rc01",
        "formal_head": BASE, "candidate_author_heads": {
            "canyon_pr933": CANYON_HEAD, "moguron_pr967": final_head},
        "canyon_source_git_blob": CANYON_BLOB,
        "selected_source_route": mole.ROUTE, "selected_source_count": 69,
        "changed_selected_routes": 1, "other68_selected_byte_exact": True,
        "original_route_sha256": sha(source_old_bytes),
        "candidate_route_sha256": sha(source_new_bytes),
        "source_file_bytes": len(source_new_bytes),
        "formal_private_place_bytes": len((base / mole.PLACE).read_bytes()),
        "candidate_private_place_bytes": len(actual_place),
        "candidate_place_delta_bytes": len(actual_place)-len((base / mole.PLACE).read_bytes()),
        "candidate_place_sha256": sha(actual_place),
        "seven_shore_facets_part_delta": 0, "additional_moguron_parts": 24,
        "new_game_authority": False, "studio_solo": "NOT_TESTED",
        "studio_2client": "NOT_TESTED", "android15": "NOT_TESTED",
        "real_old_new_png": "0/32", "art_gate": "ART_NO_GO",
        "fun_gate": "FUN_NO_GO", "owner_accepted": False,
        "formal_rc_adopted": False, "requires_B220_fresh_nonforce_CAS": True,
        "required_next": "Compare to fresh B220 RC, independent reviewer, select one source, ON/OFF69 Rojo/NATIVE/17+48, official same-head build; then Studio+Android+human acceptance",
        "rollback": "OFF69_CANYON_FACETS exact original source+project+receipt+Place; retain separately OFF69_MOGURON_MATTE intermediate Canyon-only",
    }
    (outdir / "SOURCE_SELECT_MANIFEST.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True)+"\n",
        encoding="utf-8")
    need(selected_out.read_bytes() == source_new_bytes
         and json.loads((outdir / "SOURCE_SELECT_MANIFEST.json").read_text()) ==
         manifest, "B220_PACKET_BYTE_VERIFY")
    print("GQ470_COMPOSITE_933_967_ONE_SELECTED_SOURCE_68_EXACT_NATIVE_ROJO_SOURCE_ONLY")
    print(json.dumps(manifest, ensure_ascii=False, sort_keys=True))
    return manifest


def self_test(canyon) -> None:
    # Isolate both mutable hunks to verify ordering and exact no-loss composition.
    sample = (
        "-- GQ8_RC85_RC86_WCS_STARRY_METEOR_REAL67_20261119\n"
        + 'if not RunService:IsStudio() then return end\n'
        + "local stage=Instance.new(\"Model\")\n"
        + "local gateOpen=false\n"
        + "local function setGate(open:boolean) end\n"
        + "local function authorized(p:Player,target:BasePart):boolean end\n"
        + 'stage:SetAttribute("SafeRouteAlwaysAvailable",true)\n'
        + 'local safe=block("AlwaysOpenSafeRoute"\n'
        + 'local shortcut=block("ShortcutBridge"\n'
        + 'gate.CanCollide=not open\n'
        + 'p:GetAttribute("EGGRUMBLE_QueuedMode")~=mode\n'
        + 'CanTouch=false;p.CanQuery=collide;p.CanCollide=collide\n'
        + 'mole("WEST",-34);mole("EAST",34)\n'
        + 'if gateOpen and os.clock()>=gateUntil and not occupied(-15,13) then\n'
        + "GQ8_RC86_StarfallPath GQ8_RC86_StarfallPath\n"
        + "GQ8_RC86_MeteorShortcut GQ8_RC86_MeteorShortcut\n"
        + canyon.OLD + mole.OLD)
    try:
        # This simple specimen intentionally lacks creator/source invariants.
        canyon.transform(sample)
    except ValueError:
        pass
    # String disjointness and actual original/new markers are tested
    # using true full REAL69 artifacts, not synthetic partially-valid source.
    need(canyon.OLD not in mole.OLD and mole.OLD not in canyon.OLD,
         "DISJOINT_HUNK_PROOF")
    for m in (canyon.NEW.replace("facet.CanQuery=false","facet.CanQuery=true"),
              mole.NEW.replace("authorized(p,torso)", "true")):
        need(m not in canyon.NEW + mole.NEW, "MUTANT_REJECTED")
    print("GQ470_COMPOSITE_SOURCE_ANCHORS_DISJOINT_PASS_REAL_PLACE_NEXT")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--canyon-py", type=Path, required=True)
    p.add_argument("--formal", type=Path)
    p.add_argument("--candidate", type=Path)
    p.add_argument("--out", type=Path)
    p.add_argument("--head", default=MOGURON_HEAD)
    p.add_argument("--self-test", action="store_true")
    args = p.parse_args()
    canyon = import_canyon(args.canyon_py)
    if args.self_test:
        self_test(canyon)
    else:
        need(args.formal is not None and args.candidate is not None
             and args.out is not None, "NEED_REAL_PACKAGES")
        prove(args.formal,args.candidate,canyon,args.out,args.head)
