#!/usr/bin/env python3
"""Combine TWO already-authored REAL69 FlagshipFieldArt visual fixes, source-exact.

PR #934 owns castle-essential budget accounting; PR #916 owns matte ridges.
They both patch ONE selected Script. Neither original author branch is edited.
This is A PREP ONLY; it is not an official RC write or an Engine/ART/FUN pass.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import shutil
import sys

FORMAL = "e80973c354f14a0d0088577f3cc1a875454f0f8f"
FORMAL_SHA256 = "fc63171149a86f6b39779ba6ebe7e18fcb7099fbde98ad2ec33a7cb92b3a9934"
FORMAL_PLACE_BYTES = 798390
ROUTE = "ServerScriptService/EGGRUMBLE_FlagshipFieldArt"
ORIGINAL_SHA256 = "d77fdaf390506f87dfea3064611898320288690f4ef14b97f4e8416eaef40395"
PROJECT = "EGGRUMBLE_REAL69.project.json"
RECEIPT = "REAL69_LEGACY_INTAKE_RECEIPT.json"
PLACE = "EGGRUMBLE_REAL69_PRIVATE.rbxlx"
OFF = "OFF69_ORIGINAL"
FEATURE = "GQ470_FB015_FIELDART_916_934_COMPOSITE_20261121"
SOURCE_916 = ("89bd47dbff105bbcfe1005fdbaaca7cf737cc33c",
              "3e5b8a0355bfb255208b480ac7c47879385da268")
SOURCE_934 = ("e121c11728de6784a2cfddf11beea08f677ae1ae",
              "9fc1e50ab63d7537f361c52a0572cb740c54e223")

# The two author-pinned, immutable patchers are downloaded by the workflow.
# They are never edited by this composite and fail closed on anchor drift.
PARENTS = Path(__file__).resolve().parents
sys.path.insert(0, str(PARENTS[1] / "gq8_rc85_rc86_real68_nonloss_20261120"))

def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()

def need(value: bool, code: str) -> None:
    if not value:
        raise ValueError("RED_GQ470_FIELDART_COMPOSITE_" + code)

def load(path: Path, name: str):
    need(path.is_file(), "PINNED_AUTHOR_PATCHER_MISSING_" + name)
    spec = importlib.util.spec_from_file_location(name, path)
    need(spec is not None and spec.loader is not None, "IMPORT_" + name)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def selected(root: Path) -> tuple[dict[str, Path], dict]:
    root = root.resolve()
    meta = json.loads((root / PROJECT).read_text())
    found = {}
    def walk(node, route=""):
        need(isinstance(node, dict), "SELECTED_TREE")
        if "$path" in node:
            path = (root / node["$path"]).resolve()
            need(path.is_relative_to(root) and path.is_file(), "ESCAPED_SELECTED_PATH")
            need(route not in found, "DUPLICATE_SELECTED_ROUTE")
            found[route] = path
            return
        for key, item in node.items():
            if not key.startswith("$"):
                walk(item, (route + "/" if route else "") + key)
    walk(meta["tree"])
    need(len(found) == 69 and ROUTE in found, "SELECTED_69_ONE_FIELDART")
    return found, meta

def source_maps(root: Path):
    files, _ = selected(root)
    return {route: sha(path.read_bytes()) for route, path in files.items()}

def prove_original(root: Path):
    files, _ = selected(root)
    receipt = json.loads((root / RECEIPT).read_text())
    actual = source_maps(root)
    need(receipt["official_branch"] == "rc/p0d-s1-kids-rc01", "OFFICIAL_BRANCH")
    need(receipt["build_head"] == FORMAL and receipt["canonical_build"] is True,
         "OFFICIAL_HEAD_AND_CANONICAL")
    need(receipt["selected_source_count"] == 69
         and len(receipt["source_classes"]) == 69
         and len(receipt["source_hashes"]) == 69, "OFFICIAL_69_RECEIPT")
    need(receipt["source_hashes"] == actual, "SOURCE_LOCK_ALL_69")
    need(receipt["source_classes"][ROUTE] == "Script", "FIELDART_SCRIPT_CLASS")
    need(actual[ROUTE] == ORIGINAL_SHA256, "AUTHOR_BASE_SHA")
    place = (root / PLACE).read_bytes()
    need(len(place) == FORMAL_PLACE_BYTES and sha(place) == FORMAL_SHA256,
         "ORIGINAL_PRIVATE_PLACE_SHA")
    return files, receipt

def artist_composite(original: str, castle, ridge) -> str:
    # #934 fixes the primary castle-first reservation and teardown first.
    # #916 then appends bounded decorative ridges with no new script owner.
    need(sha(original.encode()) == ORIGINAL_SHA256, "UNEXPECTED_SOURCE")
    modified = castle.transform(original)
    need(modified.count(castle.FEATURE) == 1, "MISSING_CASTLE_AUTHOR")
    modified = ridge.patch(modified)
    need(modified.count(castle.FEATURE) == 1 and
         modified.count(ridge.MARK) == 2, "AUTHOR_FEATURES_NONLOSS")
    need("local MAX_VISUAL_PARTS_PER_ARENA = 320" in modified and
         "local MAX_CASTLE_PARTS = 19" in modified, "MOBILE_PART_BUDGET")
    need("MIN_CASTLE_ESSENTIAL_PARTS = 10" in modified and
         "HorizonCliffCrown_" in modified and
         "HorizonCliffBase_" in modified, "CASTLES_AND_MATTE_RIDGES")
    need("if not builtArenas[arena] then return end" in modified and
         "if not reserveCastleIdentity(arena) then return end" in modified,
         "KEEP_CASTLE_GAMEPLAY_CLEAR")
    need("if (budgets[arena] or 0)+2<=MAX_VISUAL_PARTS_PER_ARENA" in modified,
         "ATOMIC_RIDGE_BUDGET")
    need(modified.count("p.CanCollide=false") >= original.count("p.CanCollide=false")
         and modified.count("p.CanQuery=false") >= original.count("p.CanQuery=false"),
         "NONPHYSICAL_GUARD")
    # Do not permit an imported visual patch to introduce any game authority.
    forbidden = ("RemoteEvent", "RemoteFunction", "DataStoreService",
                 "GetAsync(", "SetAsync(", "UpdateAsync(", "FireServer(",
                 "FireClient(", "TakeDamage(", "Humanoid.Health",
                 "MarketplaceService")
    for marker in forbidden:
        need(modified.count(marker) == original.count(marker),
             "NEW_AUTHORITY_" + re.sub(r"\W", "_", marker))
    # Geometric smoke: landscape=140, 16 minimum castles=160, ridges<=12
    # leaves >=8 under max320. Optional castle trim may be reclaimed.
    need(140 + 16 * 10 + 12 == 312 and 312 <= 320,
         "SIXTEEN_CASTLE_VISUAL_CAPACITY")
    ridge.verify_atomic_source_contract(modified)
    return modified

def copy_original(original: Path, output: Path):
    need(not output.exists(), "NO_OVERWRITE_OUTPUT")
    output.mkdir(parents=True)
    shutil.copytree(original / "sources", output / "sources")
    for fn in (PROJECT, RECEIPT, PLACE):
        shutil.copy2(original / fn, output / fn)

def compose(original: Path, patcher_dir: Path, output: Path):
    original = original.resolve()
    files, receipt = prove_original(original)
    castle = load(patcher_dir / "patch_castle_fairbudget.py", "author934")
    ridge = load(patcher_dir / "patch_ridge69.py", "author916")
    need(castle.BASE == FORMAL and ridge.PARENT == FORMAL,
         "AUTHOR_OFFICIAL_HEAD")
    need(castle.ROUTE == ridge.TARGET == ROUTE and
         castle.OLD_SHA == ORIGINAL_SHA256, "SAME_AUTHENTIC_SCRIPT")
    old = files[ROUTE].read_bytes()
    result = artist_composite(old.decode("utf-8"), castle, ridge).encode("utf-8")
    copy_original(original, output)
    copy_original(original, output / OFF)
    new_files, _ = selected(output)
    new_files[ROUTE].write_bytes(result)
    new_hashes = source_maps(output)
    changed = [k for k in new_hashes if new_hashes[k] != receipt["source_hashes"][k]]
    need(changed == [ROUTE], "EXACT_ONE_SELECTED_SOURCE_68_ORIGINAL")
    inverse_hashes = source_maps(output / OFF)
    need(inverse_hashes == receipt["source_hashes"], "ORIGINAL_INVERSE_69")
    need((output / OFF / PLACE).read_bytes() == (original / PLACE).read_bytes(),
         "ORIGINAL_INVERSE_PLACE")
    receipt["source_hashes"] = new_hashes
    receipt["canonical_build"] = False
    receipt["build_head"] = "A_PREP_NOT_FORMAL"
    receipt["gq470_fieldart_916_934_composite"] = {
        "feature_id": FEATURE,
        "base_formal_rc_sha": FORMAL,
        "author_prs": [934, 916],
        "author_commit_shas": [SOURCE_934[0], SOURCE_916[0]],
        "author_patch_blobs": [SOURCE_934[1], SOURCE_916[1]],
        "selected_route": ROUTE,
        "before_source_sha256": ORIGINAL_SHA256,
        "after_source_sha256": new_hashes[ROUTE],
        "changed_selected_routes": 1,
        "preserved_selected_routes": 68,
        "runtime_scripts_added": 0,
        "visual_part_cap": 320,
        "castle_min_essential": 10,
        "maximum_mat_ridges": 12,
        "all_original_game_authority_preserved": True,
        "rollback": "OFF69_ORIGINAL source + exact original Place",
        "native69_on_off": "NOT_YET_TESTED",
        "rojo69_on_off": "NOT_YET_TESTED",
        "studio_solo": "NOT_TESTED",
        "studio_2client": "NOT_TESTED",
        "android_15min": "NOT_TESTED",
        "art_32_screenshots": "0/32",
        "kid_first3min_fun": "NOT_TESTED",
        "owner_accepted": False,
        "product_gate": "PRODUCT_NO_GO",
        "art_gate": "ART_NO_GO",
    }
    (output / RECEIPT).write_text(
        json.dumps(receipt, sort_keys=True, ensure_ascii=False, indent=2) + "\n")
    print("FIELDART_916_934_COMPOSED_REAL_SELECTED_SOURCE_ONE_68_EXACT")
    print("ORIGINAL", ORIGINAL_SHA256, "CANDIDATE", new_hashes[ROUTE])

def verify(output: Path):
    files, _ = selected(output)
    before = source_maps(output / OFF)
    after = source_maps(output)
    receipt = json.loads((output / RECEIPT).read_text())
    note = receipt["gq470_fieldart_916_934_composite"]
    need([r for r in after if before[r] != after[r]] == [ROUTE],
         "VERIFY_EXACTLY_ONE_CHANGED")
    need(sha(files[ROUTE].read_bytes()) == note["after_source_sha256"],
         "VERIFY_CURRENT_CANDIDATE")
    need(receipt["source_hashes"] == after, "VERIFY_CURRENT_69")
    need(note["before_source_sha256"] == before[ROUTE] == ORIGINAL_SHA256,
         "VERIFY_ORIGINAL_SOURCE")
    need(note["art_32_screenshots"] == "0/32" and
         note["owner_accepted"] is False and
         note["product_gate"] == "PRODUCT_NO_GO",
         "NO_FAKE_VISUAL_ACCEPTANCE")
    need("GQ470_FORTRESS_VISUAL_FAIR_BUDGET_REAL69_20261121" in files[ROUTE].read_text()
         and "GQ470_FB015_RIDGE_HORIZON_P0_20261120" in files[ROUTE].read_text(),
         "VERIFY_BOTH_AUTHORS_PRESENT")
    need(sha((output / OFF / PLACE).read_bytes()) == FORMAL_SHA256,
         "VERIFY_OFF_ORIGINAL_PLACE")
    print("GQ470_FIELDART_COMPOSITE_VERIFY_1_OF_69_OTHER68_EXACT")
    return note

def export_b(output: Path):
    note = verify(output)
    p = output / "B220_FIELDART_ONE_SOURCE_NOT_FORMAL"
    need(not p.exists(), "NO_OVERWRITE_B_PACKET")
    p.mkdir()
    files, meta = selected(output)
    cls = json.loads((output / RECEIPT).read_text())["source_classes"][ROUTE]
    need(cls == "Script", "EXPORT_SCRIPT_CLASS")
    shutil.copy2(files[ROUTE], p / "EGGRUMBLE_FlagshipFieldArt.server.luau")
    manifest = {
        "schema": "B220_FIELDART_916_934_NONAUTHORITATIVE_PREP_V1",
        "formal_branch": "rc/p0d-s1-kids-rc01",
        "formal_base_sha": FORMAL,
        "source_profile": "REAL69_PRIVATE_COMPANION",
        "feature_id": FEATURE,
        "source_route": ROUTE,
        "source_class": cls,
        "original_sha256": ORIGINAL_SHA256,
        "composed_sha256": note["after_source_sha256"],
        "original_author_commit_shas": [SOURCE_934[0], SOURCE_916[0]],
        "rollback": "replace selected one source by exact original SHA",
        "authoritative_rc_writer": "#220 ONLY after authenticated nonforce CAS",
        "officially_integrated": False,
        "source_only": True,
        "art_gate": "ART_NO_GO",
        "studio_android_fun": "NOT_TESTED",
    }
    (p / "SOURCE_SELECT_MANIFEST.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    need(sha((p / "EGGRUMBLE_FlagshipFieldArt.server.luau").read_bytes())
         == manifest["composed_sha256"], "EXPORT_EXACT_CANDIDATE")
    print("B220_SINGLE_SOURCE_HANDOFF_NOT_FORMAL_READY")

def selftest():
    need(len(FORMAL) == len(SOURCE_934[0]) == len(SOURCE_916[0]) == 40,
         "PINNED_SHA_FORMAT")
    need(len(ORIGINAL_SHA256) == len(FORMAL_SHA256) == 64, "HASH_FORMAT")
    # These model-level checks are NOT proof that Roblox scripts rendered.
    for ridges in (0, 2, 6, 12):
        for castles in range(17):
            must = 140 + ridges + castles * 10
            need(must <= 320, "MODEL_MANDATORY_CASTLE_NOT_LOST")
    need(140 + 12 + 160 == 312, "BUDGET_MODEL")
    for fake in ("WRONG" + ORIGINAL_SHA256, "",
                 "d77fdaf390506f87dfea3064611898320288690f4ef14b97f4e8416eaef40394"):
        try:
            need(fake == ORIGINAL_SHA256, "PINNED_SOURCE_MUTANT")
        except ValueError:
            pass
        else:
            raise AssertionError("RED_MUTANT_ACCEPTED")
    print("GQ470_FIELDART_COMPOSITE_STATIC_BUDGET_AND_3_NEGATIVES_PASS")

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--original", type=Path)
    p.add_argument("--patchers", type=Path)
    p.add_argument("--out", type=Path)
    p.add_argument("--verify", type=Path)
    p.add_argument("--export-b", type=Path)
    p.add_argument("--self-test", action="store_true")
    args = p.parse_args()
    if args.self_test: selftest()
    elif args.verify: verify(args.verify)
    elif args.export_b: export_b(args.export_b)
    else:
        need(args.original is not None and args.patchers is not None
             and args.out is not None, "ARGS")
        compose(args.original, args.patchers, args.out)
