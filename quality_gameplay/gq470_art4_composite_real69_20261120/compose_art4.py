#!/usr/bin/env python3
"""GQ470: compose six existing REAL69 art-source PREPs into ONE A-only candidate.

Never modifies the official RC. Each independently pinned patcher runs against
the *same* immutable official REAL69 artifact, then only its selected-source
byte delta is transplanted. The candidate is not a Roblox/ART/OWNER pass.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

BASE = "e80973c354f14a0d0088577f3cc1a875454f0f8f"
OFF = "OFF69_ART6_ORIGINAL"
PROJECT = "EGGRUMBLE_REAL69.project.json"
RECEIPT = "REAL69_LEGACY_INTAKE_RECEIPT.json"
PLACE = "EGGRUMBLE_REAL69_PRIVATE.rbxlx"
ROUTES = 69
BASE_PLACE_SHA256 = "fc63171149a86f6b39779ba6ebe7e18fcb7099fbde98ad2ec33a7cb92b3a9934"

@dataclass(frozen=True)
class Slice:
    pr: int
    head: str
    path: str
    blob: str
    target: str
    metadata: str
    head_flag: bool = False
    candidate_path: str = ""
    candidate_blob: str = ""

SLICES = (
    Slice(924, "ea2882ae8c703bd987f2834ccb131959db34ffe2",
          "quality_gameplay/gq470_bot_objective_tag_real69_20261120/patch_bot_tag69.py",
          "28c4bc1c3b096dd80bd8374d2f6a49bf21052616",
          "ServerScriptService/EGGRUMBLE_BotActors", "gq470_fb015_bot_tag"),
    Slice(926, "68935d6054855620c5f726b6bd9568f126d69beb",
          "quality_gameplay/gq470_fb016_foliage_a01_real69_20261120/patch_foliage69.py",
          "cad4be03daab03314f85d8214c7578ddf90b20fd",
          "StarterPlayer/StarterPlayerScripts/EGGRUMBLE_ArtDistanceLOD",
          "gq470_fb016_true_occlusion", True),
    Slice(925, "a997fb5fc7ec6b7a40afa4c67667c6875483f00d",
          "quality_gameplay/gq470_social_plaza_art_real69_20261120/patch_social_art69.py",
          "daa7940970c3deb1c9b676705066743592626093",
          "ServerScriptService/GQ8_LobbySocialPlaza", "gq470_social_plaza_art"),
    Slice(928, "5beaeddd77586f170459018df7a4a113b7522609",
          "quality_gameplay/gq470_ko_slash_real69_20261120/patch_ko_slash69.py",
          "31cf788512299677a6024fc6f62e9da9aecf6cbe",
          "ServerScriptService/EGGRUMBLE_ImpactFeedback",
          "gq470_ko_slashed_confirmed", True),

    Slice(930, "a721e7acbd78b6232bf1da39ab29e6e0df442f9b",
          "quality_gameplay/gq470_stonegiant_silhouette_real69_20261120/patch_stone_giant69.py",
          "a040fa3e031930fae7304e404235bb79c8dd219c",
          "ServerScriptService/EGGRUMBLE_NeutralStoneGiant",
          "gq470_stone_giant_silhouette", True),
    Slice(929, "4255940b975bfb8481c964838f494ee08f80b753",
          "quality_gameplay/gq470_fb015_weapon_sculpt_real69_20261120/verify_weapons69.py",
          "2c2fe3bd14c70954a58e74e9c73bec8d6a12f0b7",
          "ServerScriptService/EGGRUMBLE_WeaponSilhouettes",
          "gq470_fb015_weapon_sculpt", False,
          "quality_gameplay/gq470_fb015_weapon_sculpt_real69_20261120/EGGRUMBLE_WeaponSilhouettes.luau",
          "e3392e031795b786311d57bf8fca05a931246260"),
)

def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def demand(test: bool, reason: str) -> None:
    if not test:
        raise ValueError("RED_ART6_COMPOSITE_" + reason)

# Immutable author SOURCE-budget contracts, not real device or ART scores.
# Prevent a future visual-slice intake from silently growing Parts/UI/KO cost,
# changing combat authority, or inventing human/OWNER acceptance evidence.
SOURCE_ART_BUDGETS: dict[int, dict[str, object]] = {
    924: {"tag_pixels": [104, 24], "tag_max_studs": 22,
          "near_hp_studs": 18, "extra_ui_instances": 0,
          "new_gameplay_authority": False},
    926: {"max_canopies": 160, "max_tracked_parts": 1800,
          "new_parts": 0, "remote_or_damage_changes": False,
          "source_only": True},
    925: {"world_label_pixels_after": [136, 38],
          "world_label_distance_after": 25,
          "photo_roof_parts_after": 3, "net_new_visual_parts": 2,
          "new_ui_instances": 0, "new_authority": False},
    928: {"ko_per_second_limit": 6, "new_parts_per_confirmed_ko": 2,
          "yaw_follows_victim": True, "zero_flat_look_guard": True,
          "new_remotes": 0, "new_gameplay_authority": False,
          "source_only": True},
    930: {"new_static_decorative_wedges_per_boss": 4,
          "new_remotes": 0, "new_gameplay_authority": False,
          "collision_or_targeting_changed": False, "source_only": True},
    929: {"total_existing_visual_parts": 32, "additional_visual_parts": 0,
          "new_selected_scripts": 0, "changed_selected_scripts": 1,
          "art_or_engine_pass": "NOT_TESTED",
          "source_gate": "SOURCE_PREP_PASS"},
}
SOURCE_HASH_FIELDS = {
    924: ("original_source_sha256", "changed_source_sha256"),
    925: ("original_source_sha256", "new_source_sha256"),
    926: ("before_sha256", "after_sha256"),
    928: ("before_sha256", "after_sha256"),
    929: ("before_sha256", "after_sha256"),
    930: ("before_sha256", "after_sha256"),
}

def verify_source_budget(s: Slice, meta: dict, before: bytes,
                         after: bytes) -> None:
    """Check ART source budgets and both real source digests per owner."""
    demand(isinstance(meta, dict), "SOURCE_BUDGET_METADATA_" + str(s.pr))
    for field, expected in SOURCE_ART_BUDGETS[s.pr].items():
        got = meta.get(field)
        demand(type(got) is type(expected) and got == expected,
               "SOURCE_BUDGET_" + str(s.pr) + "_" + field.upper())
    before_field, after_field = SOURCE_HASH_FIELDS[s.pr]
    demand(meta.get(before_field) == digest(before),
           "SOURCE_BUDGET_BEFORE_HASH_" + str(s.pr))
    demand(meta.get(after_field) == digest(after),
           "SOURCE_BUDGET_AFTER_HASH_" + str(s.pr))
    demand(meta.get("owner_accepted") is False,
           "SOURCE_BUDGET_FAKE_OWNER_PASS_" + str(s.pr))

def selected(root: Path) -> dict[str, Path]:
    data = json.loads((root / PROJECT).read_text(encoding="utf-8"))
    found: dict[str, Path] = {}
    def walk(node: dict, prefix: str = "") -> None:
        for name, child in node.items():
            if name == "$path":
                p = (root / child).resolve()
                demand(p.is_relative_to(root.resolve()) and p.is_file(), "UNSAFE_SOURCE")
                demand(prefix not in found, "DUPLICATE_ROUTE")
                found[prefix] = p
            elif not name.startswith("$") and isinstance(child, dict):
                walk(child, prefix + "/" + name if prefix else name)
    walk(data["tree"])
    return found

def data_map(root: Path) -> dict[str, bytes]:
    return {k: f.read_bytes() for k, f in selected(root).items()}

def changed_routes(before: dict[str, bytes], after: dict[str, bytes],
                   expected: set[str], size: int = ROUTES) -> None:
    demand(len(before) == len(after) == size, "SOURCE_COUNT")
    demand(set(before) == set(after), "ROUTE_DRIFT")
    demand({k for k in before if before[k] != after[k]} == expected, "SOURCE_SCOPE")


def art_budget_gate(before: dict[str, bytes], after: dict[str, bytes]) -> dict:
    """Source-based visual budgets for six disjoint original art modules.

    This checks bounded code and readability, NOT rendered beauty or mobile FPS.
    """
    must_have = {
        924: ('label.Size=UDim2.fromOffset(104,24)', 'label.MaxDistance=22',
              'HealthDisplayDistance=18', 'text.TextStrokeTransparency=.45'),
        926: ('local MAX_CANOPIES=160', 'local MAX_TRACKED_PARTS=1800',
              'local function blocksAvatar(', 'clipAxis(', 'task.wait(.16)'),
        925: ('b.Size=UDim2.fromOffset(136,38)', 'b.MaxDistance=25',
              'PhotoRoof_Left', 'PhotoRoof_Right', 'PhotoRoof_Ridge'),
        928: ('local MAX_KO_BURSTS_PER_SEC=6', 'for side=-1,1,2 do',
              'Instance.new("WedgePart")', 'Debris:AddItem(fin,.30)'),
        930: ('BasaltShoulder_', 'BasaltCrown_', 'for side=-1,1,2 do',
              'shoulder.CanCollide=false', 'crown.CanCollide=false'),
        929: ('PART_BUDGET_PER_AVATAR=8', 'TAPERED_WEAPONS',
              'Instance.new("WedgePart")', 'role=="NINJA"'),
    }
    # Constructor *sites*, not measured runtime parts. Four matte boss
    # wedges per spawn and two KO fins per confirmed death still need Studio QA.
    additional_sites = {924: 0, 926: 0, 925: 0, 928: 0, 930: 2, 929: 1}
    no_new_authority = ('RemoteEvent', 'RemoteFunction', 'DataStore',
                        'MarketplaceService', 'TakeDamage', 'FireServer(')
    for sl in SLICES:
        original, updated = before[sl.target].decode(), after[sl.target].decode()
        for marker in must_have[sl.pr]:
            demand(marker in updated, "ART_BUDGET_MARKER_" + str(sl.pr))
        for marker in no_new_authority:
            demand(updated.count(marker) == original.count(marker),
                   "ART_BUDGET_AUTHORITY_" + str(sl.pr))
        demand(updated.count('Instance.new(') - original.count('Instance.new(')
               == additional_sites[sl.pr], "ART_BUDGET_CONSTRUCTOR_" + str(sl.pr))
    chosen = {sl.pr: after[sl.target].decode() for sl in SLICES}
    demand('RunService.RenderStepped:Connect' not in chosen[926],
           "ART_FOREST_RENDER_LOOP")
    demand(chosen[925].count('part("PhotoRoof_') == 3,
           "ART_PLAZA_ROOF_PARTS")
    demand(chosen[928].count('Instance.new("WedgePart")') == 1 and
           'ring.Material=Enum.Material.Neon' not in chosen[928],
           "ART_KO_FIN_BUDGET")
    demand(chosen[930].count('Instance.new("WedgePart")') >= 2,
           "ART_BOSS_WEDGE_BUDGET")
    demand(chosen[929].count('Instance.new("WedgePart")') == 1,
           "ART_WEAPON_WEDGE_BUDGET")
    demand('ui.Text=id..' not in chosen[924],
           "ART_BOT_INTERNAL_ID")
    return {"status": "SOURCE_ONLY_PASS", "routes": 6, "bot_tag_studs": 22,
            "plaza_tag_studs": 25, "canopy_max": 160,
            "canopy_period_seconds": 0.16, "ko_bursts_per_second": 6,
            "boss_added_cosmetic_wedges": 4,
            "weapon_parts_per_avatar_cap": 8,
            "studio": "NOT_TESTED", "android": "NOT_TESTED",
            "owner_accepted": False}

def art_budget_self_test() -> None:
    sample = {
        924: 'label.Size=UDim2.fromOffset(104,24) label.MaxDistance=22 HealthDisplayDistance=18 text.TextStrokeTransparency=.45',
        926: 'local MAX_CANOPIES=160 local MAX_TRACKED_PARTS=1800 local function blocksAvatar( clipAxis( task.wait(.16)',
        925: 'b.Size=UDim2.fromOffset(136,38) b.MaxDistance=25 part("PhotoRoof_Left" part("PhotoRoof_Right" part("PhotoRoof_Ridge"',
        928: 'local MAX_KO_BURSTS_PER_SEC=6 for side=-1,1,2 do Instance.new("WedgePart") Debris:AddItem(fin,.30)',
        930: 'BasaltShoulder_ BasaltCrown_ for side=-1,1,2 do shoulder.CanCollide=false crown.CanCollide=false Instance.new("WedgePart") Instance.new("WedgePart")',
        929: 'PART_BUDGET_PER_AVATAR=8 TAPERED_WEAPONS Instance.new("WedgePart") role=="NINJA"',
    }
    after = {sl.target: sample[sl.pr].encode() for sl in SLICES}
    before = dict(after)
    for sl in SLICES:
        if sl.pr in (929, 930):
            before[sl.target] = after[sl.target].decode().replace(
                'Instance.new("WedgePart")', '').encode()
    demand(art_budget_gate(before, after)["routes"] == 6, "ART_BUDGET_FIXTURE")
    for pr, old, new in ((924, 'label.MaxDistance=22', 'label.MaxDistance=222'),
                         (926, 'task.wait(.16)', 'RunService.RenderStepped:Connect'),
                         (925, 'b.MaxDistance=25', 'b.MaxDistance=125'),
                         (928, 'MAX_KO_BURSTS_PER_SEC=6', 'MAX_KO_BURSTS_PER_SEC=60'),
                         (930, 'BasaltCrown_', 'RemoteEvent'),
                         (929, 'PART_BUDGET_PER_AVATAR=8', 'PART_BUDGET_PER_AVATAR=99')):
        route = next(sl.target for sl in SLICES if sl.pr == pr)
        broken = dict(after)
        broken[route] = broken[route].replace(old.encode(), new.encode())
        try:
            art_budget_gate(before, broken)
        except ValueError:
            continue
        raise AssertionError("RED_ART_BUDGET_MUTANT_" + str(pr))
    print("GQ470_ART6_6_REAL_SOURCE_BUDGET_NEGATIVES_PASS")


def verify_formal(root: Path) -> tuple[dict, dict[str, bytes]]:
    receipt = json.loads((root / RECEIPT).read_text(encoding="utf-8"))
    files = data_map(root)
    demand(digest((root / PLACE).read_bytes()) == BASE_PLACE_SHA256,
           "FORMAL_PLACE_HASH")
    demand(receipt.get("official_branch") == "rc/p0d-s1-kids-rc01",
           "FORMAL_BRANCH")
    demand(receipt.get("build_head") == BASE and
           receipt.get("canonical_build") is True, "FORMAL_PARENT")
    demand(receipt.get("selected_source_count") == ROUTES, "FORMAL_COUNT")
    demand(set(files) == set(receipt.get("source_hashes", {})) ==
           set(receipt.get("source_classes", {})), "FORMAL_ROUTE_SET")
    for route, content in files.items():
        demand(digest(content) == receipt["source_hashes"][route],
               "FORMAL_SOURCE_HASH_" + route)
    return receipt, files

def compose(formal: Path, patchers: Path, output: Path) -> None:
    formal = formal.resolve()
    patchers = patchers.resolve()
    output = output.resolve()
    demand(formal.is_dir() and patchers.is_dir() and not output.exists(),
           "INPUT_OR_OUTPUT")
    demand(not output.is_relative_to(formal) and not formal.is_relative_to(output),
           "OUTPUT_PARENT_OVERLAP")
    receipt, originals = verify_formal(formal)
    demand(len({s.target for s in SLICES}) == len(SLICES), "TARGET_COLLISION")
    demand(len({s.pr for s in SLICES}) == len(SLICES), "PR_COLLISION")
    demand(all(s.target in originals for s in SLICES), "UNKNOWN_SELECTED_TARGET")

    output.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(formal, output, symlinks=False)
    shutil.copytree(formal, output / OFF, symlinks=False)
    outpaths = selected(output)
    provenance: list[dict] = []

    for s in SLICES:
        patcher = patchers / Path(s.path).name
        demand(patcher.is_file() and not patcher.is_symlink(), "PATCHER_MISSING")
        with tempfile.TemporaryDirectory(prefix="gq470-art6-") as temporary:
            stage = Path(temporary) / "candidate"
            shutil.copytree(formal, stage, symlinks=False)
            command = [sys.executable, str(patcher), "--base", str(stage)]
            if s.head_flag:
                command += ["--head", BASE]
            if s.candidate_path:
                candidate = patchers / Path(s.candidate_path).name
                demand(candidate.is_file() and not candidate.is_symlink(),
                       "PINNED_CANDIDATE_MISSING")
                command += ["--candidate", str(candidate)]
            subprocess.run(command, check=True)
            altered = data_map(stage)
            changed_routes(originals, altered, {s.target})
            demand((stage / PROJECT).read_bytes() == (formal / PROJECT).read_bytes(),
                   "PATCHER_PROJECT_CHANGED")
            stage_receipt = json.loads((stage / RECEIPT).read_text(encoding="utf-8"))
            demand(stage_receipt["source_hashes"][s.target] ==
                   digest(altered[s.target]), "PATCHER_SOURCE_RECEIPT")
            meta = stage_receipt.get(s.metadata)
            verify_source_budget(s, meta, originals[s.target], altered[s.target])
            outpaths[s.target].write_bytes(altered[s.target])
            receipt["source_hashes"][s.target] = digest(altered[s.target])
            receipt[s.metadata] = meta
            provenance.append({
                "pr": s.pr, "pinned_pr_head": s.head,
                "pinned_patcher_git_blob": s.blob,
                "pinned_candidate_git_blob": s.candidate_blob,
                "route": s.target,
                "before_sha256": digest(originals[s.target]),
                "after_sha256": digest(altered[s.target]),
            })

    composed = data_map(output)
    visual_budget = art_budget_gate(originals, composed)
    expected = {s.target for s in SLICES}
    changed_routes(originals, composed, expected)
    demand((formal / PROJECT).read_bytes() == (output / PROJECT).read_bytes(),
           "COMPOSITE_PROJECT_CHANGED")
    demand(data_map(output / OFF) == originals, "OFF69_ROLLBACK_SOURCES")
    demand((output / OFF / PLACE).read_bytes() == (formal / PLACE).read_bytes(),
           "OFF69_ROLLBACK_PLACE")
    for route, raw in composed.items():
        demand(receipt["source_hashes"][route] == digest(raw),
               "COMPOSITE_SOURCE_RECEIPT")

    # Keep formal BUILD identity distinct: this receipt is not an official release.
    receipt["canonical_build"] = False
    receipt["build_head"] = "A_PREP_ART6_FROM_" + BASE
    receipt["gq470_art6_visual_source_budget"] = visual_budget
    receipt["gq470_art6_composite"] = {
        "source_only": True, "formal_parent": BASE,
        "formal_rc_unchanged": True, "candidate_only": True,
        "selected_sources_total": ROUTES,
        "selected_sources_changed": len(SLICES),
        "other_selected_sources_byte_exact": ROUTES - len(SLICES),
        "pinned_inputs": provenance,
        "rollback": OFF, "new_gameplay_authority": False,
        "studio_solo": "NOT_TESTED", "studio_2client": "NOT_TESTED",
        "android_15min": "NOT_TESTED", "art_32_real_png": "0/32",
        "kid_first3min": "NOT_TESTED", "owner_accepted": False,
        "product_go": False, "art_go": False,
    }
    (output / RECEIPT).write_text(
        json.dumps(receipt, sort_keys=True, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8")
    print("GQ470_ART6_6_SOURCES_COMPOSED_63_EXACT_OFF69_PASS")

def verify_attestation(receipt: dict, before: dict[str, bytes],
                       after: dict[str, bytes]) -> None:
    """Do not trust self-consistent candidate SHA claims without pinned provenance."""
    info = receipt.get("gq470_art6_composite")
    demand(isinstance(info, dict), "ATTESTATION_MISSING")
    expected_flags = {
        "source_only": True, "formal_parent": BASE,
        "formal_rc_unchanged": True, "candidate_only": True,
        "selected_sources_total": ROUTES,
        "selected_sources_changed": len(SLICES),
        "other_selected_sources_byte_exact": ROUTES - len(SLICES),
        "rollback": OFF, "new_gameplay_authority": False,
        "owner_accepted": False, "product_go": False, "art_go": False,
        "studio_solo": "NOT_TESTED", "studio_2client": "NOT_TESTED",
        "android_15min": "NOT_TESTED", "art_32_real_png": "0/32",
        "kid_first3min": "NOT_TESTED",
    }
    for field, expected in expected_flags.items():
        demand(type(info.get(field)) is type(expected) and
               info.get(field) == expected, "ATTESTATION_" + field.upper())
    pins = info.get("pinned_inputs")
    demand(isinstance(pins, list) and len(pins) == len(SLICES),
           "ATTESTATION_PIN_COUNT")
    for s, pin in zip(SLICES, pins):
        expected = {
            "pr": s.pr, "pinned_pr_head": s.head,
            "pinned_patcher_git_blob": s.blob,
                "pinned_candidate_git_blob": s.candidate_blob,
                "route": s.target,
            "before_sha256": digest(before[s.target]),
            "after_sha256": digest(after[s.target]),
        }
        demand(isinstance(pin, dict) and pin == expected,
               "ATTESTATION_PIN_" + str(s.pr))
        meta = receipt.get(s.metadata)
        verify_source_budget(s, meta, before[s.target], after[s.target])


def verify_place_provenance(root: Path, receipt: dict) -> None:
    """Do not accept a changed/stale Place after the pinned Rojo build."""
    state = receipt.get("gq470_art6_composite", {}).get("native_rojo_off69")
    demand(state in (None, "PASS_SOURCE_ONLY"), "ROJO_STATUS")
    actual = (root / PLACE).read_bytes()
    if state is None:
        # Before the build the candidate still contains the immutable official Place.
        demand(digest(actual) == BASE_PLACE_SHA256, "UNBUILT_PLACE_DRIFT")
        return
    demand(type(receipt.get("private_place_bytes")) is int and
           receipt["private_place_bytes"] == len(actual), "PLACE_BYTES")
    demand(receipt.get("private_place_sha256") == digest(actual), "PLACE_SHA256")
    demand(digest(actual) != BASE_PLACE_SHA256, "PLACE_NOT_REBUILT")


def verify_candidate(output: Path) -> None:
    receipt = json.loads((output / RECEIPT).read_text(encoding="utf-8"))
    # OFF is an independently pinned genuine official artifact, not arbitrary
    # files that could collude with a forged candidate receipt.
    formal_receipt, before = verify_formal(output / OFF)
    after = data_map(output)
    changed_routes(before, after, {s.target for s in SLICES})
    demand(receipt.get("canonical_build") is False and
           receipt.get("build_head") == "A_PREP_ART6_FROM_" + BASE and
           receipt.get("official_branch") == "rc/p0d-s1-kids-rc01",
           "MISREPRESENTED_FORMAL_OR_OWNER")
    demand(receipt.get("selected_source_count") == ROUTES and
           receipt.get("source_classes") == formal_receipt["source_classes"],
           "CANDIDATE_CLASS_OR_COUNT_DRIFT")
    demand(set(receipt.get("source_hashes", {})) == set(after),
           "CANDIDATE_ROUTE_RECEIPT")
    for route, raw in after.items():
        demand(receipt["source_hashes"][route] == digest(raw),
               "CANDIDATE_SOURCE_HASH")
    verify_attestation(receipt, before, after)
    demand(receipt.get("gq470_art6_visual_source_budget") ==
           art_budget_gate(before, after), "ART_BUDGET_RECEIPT")
    verify_place_provenance(output, receipt)
    demand((output / PROJECT).read_bytes() ==
           (output / OFF / PROJECT).read_bytes(), "CANDIDATE_PROJECT")
    print("GQ470_ART6_69_SOURCE_LOCK_6_DELTA_63_EXACT_ATTESTED_PASS")

def self_test() -> None:
    art_budget_self_test()
    original = {"r" + str(i): b"A" for i in range(ROUTES)}
    altered = dict(original)
    targets = {"r1", "r2", "r3", "r4", "r7", "r8"}
    for name in targets:
        altered[name] = b"B"
    changed_routes(original, altered, targets)
    mutations = (
        (dict(original), targets),
        (dict(altered, r5=b"B"), targets),
        (dict(altered, r1=b"A"), targets),
        ({k: v for k, v in altered.items() if k != "r6"}, targets),
        (dict(altered), {"r1", "r2", "r3"}),
        (dict(altered), set()),
    )
    for index, (candidate, claimed) in enumerate(mutations):
        try:
            changed_routes(original, candidate, claimed)
        except ValueError:
            continue
        raise AssertionError("RED_ART6_MUTANT_ACCEPTED_" + str(index))
    demand(len({s.target for s in SLICES}) == 6, "DISJOINT_SLICES")
    source_before = {s.target: b"A" for s in SLICES}
    source_after = {s.target: b"B" for s in SLICES}
    info = {
        "source_only": True, "formal_parent": BASE, "formal_rc_unchanged": True,
        "candidate_only": True, "selected_sources_total": ROUTES,
        "selected_sources_changed": len(SLICES),
        "other_selected_sources_byte_exact": ROUTES - len(SLICES),
        "rollback": OFF, "new_gameplay_authority": False,
        "studio_solo": "NOT_TESTED", "studio_2client": "NOT_TESTED",
        "android_15min": "NOT_TESTED", "art_32_real_png": "0/32",
        "kid_first3min": "NOT_TESTED", "owner_accepted": False,
        "product_go": False, "art_go": False,
        "pinned_inputs": [
            {"pr": s.pr, "pinned_pr_head": s.head,
             "pinned_patcher_git_blob": s.blob,
                "pinned_candidate_git_blob": s.candidate_blob,
                "route": s.target,
             "before_sha256": digest(source_before[s.target]),
             "after_sha256": digest(source_after[s.target])}
            for s in SLICES
        ],
    }
    valid = {"gq470_art6_composite": info}
    valid.update({
        s.metadata: {
            "owner_accepted": False,
            **SOURCE_ART_BUDGETS[s.pr],
            SOURCE_HASH_FIELDS[s.pr][0]: digest(source_before[s.target]),
            SOURCE_HASH_FIELDS[s.pr][1]: digest(source_after[s.target]),
        } for s in SLICES
    })
    verify_attestation(valid, source_before, source_after)
    cases = (
        ("formal_parent", "FAKE"),
        ("selected_sources_changed", 3),
        ("owner_accepted", True),
        ("art_32_real_png", "32/32"),
        ("new_gameplay_authority", True),
        ("pinned_inputs", []),
    )
    for field, value in cases:
        mutant = copy.deepcopy(valid)
        mutant["gq470_art6_composite"][field] = value
        try:
            verify_attestation(mutant, source_before, source_after)
        except ValueError:
            continue
        raise AssertionError("RED_ART6_ATTESTATION_MUTANT_" + field)
    for mutation in ("pinned_pr_head", "after_sha256", "pinned_candidate_git_blob"):
        mutant = copy.deepcopy(valid)
        mutant["gq470_art6_composite"]["pinned_inputs"][0][mutation] = "FAKE"
        try:
            verify_attestation(mutant, source_before, source_after)
        except ValueError:
            continue
        raise AssertionError("RED_ART6_ATTESTATION_PIN_MUTANT_" + mutation)
    mutant = copy.deepcopy(valid)
    mutant[SLICES[0].metadata]["owner_accepted"] = True
    try:
        verify_attestation(mutant, source_before, source_after)
    except ValueError:
        pass
    else:
        raise AssertionError("RED_ART6_ATTESTATION_META_MUTANT")
    # Independent source-budget and exact before/after digest mutations.
    for s in SLICES:
        field = next(iter(SOURCE_ART_BUDGETS[s.pr]))
        mutant = copy.deepcopy(valid)
        mutant[s.metadata][field] = "BUDGET_BYPASS"
        try:
            verify_attestation(mutant, source_before, source_after)
        except ValueError:
            pass
        else:
            raise AssertionError("RED_ART6_SOURCE_BUDGET_MUTANT_" + str(s.pr))
        for hashfield in SOURCE_HASH_FIELDS[s.pr]:
            mutant = copy.deepcopy(valid)
            mutant[s.metadata][hashfield] = "FORGED_SOURCE_HASH"
            try:
                verify_attestation(mutant, source_before, source_after)
            except ValueError:
                pass
            else:
                raise AssertionError("RED_ART6_SOURCE_HASH_MUTANT_" + str(s.pr))
    # The generated .rbxlx must remain bound to its receipt after Rojo.
    with tempfile.TemporaryDirectory(prefix="gq470-art6-place-") as tmp:
        root = Path(tmp)
        built = b"ART6_candidate_Rojo_Place"
        (root / PLACE).write_bytes(built)
        place_receipt = {
            "gq470_art6_composite": {"native_rojo_off69": "PASS_SOURCE_ONLY"},
            "private_place_bytes": len(built),
            "private_place_sha256": digest(built),
        }
        verify_place_provenance(root, place_receipt)
        for kind in ("wrong_bytes", "wrong_sha", "fake_status", "missing_status"):
            bad = copy.deepcopy(place_receipt)
            if kind == "wrong_bytes":
                bad["private_place_bytes"] += 1
            elif kind == "wrong_sha":
                bad["private_place_sha256"] = digest(b"forged")
            elif kind == "fake_status":
                bad["gq470_art6_composite"]["native_rojo_off69"] = "ART_PASS"
            else:
                bad["gq470_art6_composite"].pop("native_rojo_off69")
            try:
                verify_place_provenance(root, bad)
            except ValueError:
                continue
            raise AssertionError("RED_ART6_PLACE_MUTANT_" + kind)
    print("GQ470_ART6_38_MUTATION_NEGATIVES_PASS")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--verify", type=Path)
    parser.add_argument("--formal", type=Path)
    parser.add_argument("--patchers", type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    if args.manifest:
        for s in SLICES:
            print(f"{s.pr}\t{s.head}\t{s.path}\t{s.blob}\t{s.candidate_path or chr(45)}\t{s.candidate_blob or chr(45)}")
    elif args.self_test:
        self_test()
    elif args.verify is not None:
        verify_candidate(args.verify)
    else:
        demand(args.formal is not None and args.patchers is not None and
               args.out is not None, "MISSING_INPUTS")
        compose(args.formal, args.patchers, args.out)
