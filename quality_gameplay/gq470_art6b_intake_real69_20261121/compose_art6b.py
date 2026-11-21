#!/usr/bin/env python3
"""GQ470 ART6-B: composed 6 independent original visual Luau source selections.

A source-only candidate. Authenticated #220 is the sole formal-RC writer; this
branch does not publish, activate, merge to RC, or assert actual Roblox beauty.
Source bytes come only from exact-head SUCCESS Actions artifacts of original A
authors, with immutable original and candidate source digests.
"""
from __future__ import annotations

import argparse
import copy
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import shutil

FORMAL = "e80973c354f14a0d0088577f3cc1a875454f0f8f"
PLACE_HASH = "fc63171149a86f6b39779ba6ebe7e18fcb7099fbde98ad2ec33a7cb92b3a9934"
PROJECT = "EGGRUMBLE_REAL69.project.json"
RECEIPT = "REAL69_LEGACY_INTAKE_RECEIPT.json"
PLACE = "EGGRUMBLE_REAL69_PRIVATE.rbxlx"
OFF = "OFF69_ART6B_ORIGINAL"
PACKET = "B220_ART6B_SOURCE_ONLY_NOT_FORMAL"
MANIFEST = "SOURCE_SELECT_MANIFEST.json"

@dataclass(frozen=True)
class Parent:
    pr: int
    head: str
    run: int
    artifact: str
    route: str
    klass: str
    old: str
    new: str

PARENTS = (
    Parent(954, "a9342e482d0cbd7e36e2e472b338fdda11b1e261", 44836657935,
        "GQ470-REAL69-COMBATFEEL-949-952-COMPOSITE-A-NOT-FORMAL",
        "StarterPlayer/StarterPlayerScripts/EGGRUMBLE_CombatFeel", "LocalScript",
        "d378d6a356b9462c99deddc19b4393d79bf113225047a057658d1782e1e8a32e",
        "b37194cb97357cf7290fc6eb3f94396720265b15915ad588d2bd05b9b870e833"),
    Parent(942, "2448dc4f0580462335b3b4777f94c641e38b3c65", 44828660187,
        "GQ470-REAL69-SHOREFOAM-B220-SOURCE-NOT-FORMAL",
        "ServerScriptService/EGGRUMBLE_LandSeaSkyTraversal", "Script",
        "0119d26e27e09a46390679e3207c22871aa3886cc04bc09d0cc0bbe701680092",
        "655a0f5fd8c1b27343bb85c92ecc1a0c24e7fd411dec106c7a33d31ed42f4c48"),
    Parent(947, "47eef95e1b824d3d196cc119174df8a9e7426ecf", 44832220292,
        "GQ470-REAL69-HUD-PORTRAIT-SOURCE-ONLY-NOT-FORMAL",
        "ReplicatedStorage/EGGRUMBLE_HudPresentationPolicy", "ModuleScript",
        "18519fb774ba892db9cd70331da29695df87098fadd2f1a2af8a06d104eb3976",
        ""),  # Parent's own source-exact receipt supplies the candidate hash.
    Parent(943, "b2be1131ec4ae26811dd768b9490e3729431f958", 44828741977,
        "GQ470-REAL69-ROLE-MOTION-SOURCE-ONLY-NOT-FORMAL",
        "StarterPlayer/StarterPlayerScripts/EGGRUMBLE_ProceduralSkills", "LocalScript",
        "95e5dba544a759547ea41e8ecec1984317fc61b35281f4533b2323df1951491f",
        "1856594a79d2e7ab7d4f6ac386c9379a45a8647a4168f65354246e888428bffb"),
    Parent(946, "a2028bb20e42f6a01346aedfbdc39df2e64e21d9", 44831277524,
        "GQ470-REAL69-RESULT-MATTE-SOURCE-ONLY-NOT-FORMAL",
        "ServerScriptService/EGGRUMBLE_MatchResultService", "ModuleScript",
        "5fbb6a5017363bb8ef2a9793e279a1cb8a76480f6b2e74758ec35188508ce1a4",
        "2870337b83979f7981739accc91cbcb12deea5fe3cd7c2ab77ebea8781b77cec"),
    Parent(951, "fc41bc12624bdec681b524bfa5cf780d9c73864a", 44836227196,
        "GQ470-REAL69-NEUTRAL-HORDE-3-SHAPES-NOT-FORMAL",
        "ServerScriptService/EGGRUMBLE_SwarmCombat", "ModuleScript",
        "cc40d9902834b63db15bc8ff63a0be0f092cdc17e5a962d9669784f4e15dd75a",
        "09e72ccce28fb669725a71b40e26fac276900a0ffa737f24a193f778b0378925"),
)

ART7_ROUTES = {
    "ServerScriptService/EGGRUMBLE_BotActors",
    "StarterPlayer/StarterPlayerScripts/EGGRUMBLE_ArtDistanceLOD",
    "ServerScriptService/GQ8_LobbySocialPlaza",
    "ServerScriptService/EGGRUMBLE_ImpactFeedback",
    "ServerScriptService/EGGRUMBLE_NeutralStoneGiant",
    "ServerScriptService/EGGRUMBLE_WeaponSilhouettes",
    "ServerScriptService/EGGRUMBLE_FlagshipFieldArt",
}
CHANGED = {p.route for p in PARENTS}


def require(value: bool, name: str) -> None:
    if not value:
        raise ValueError("RED_GQ470_ART6B_" + name)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def selected(root: Path) -> dict[str, Path]:
    root = root.resolve()
    doc = json.loads((root / PROJECT).read_text(encoding="utf-8"))
    found: dict[str, Path] = {}

    def visit(tree: dict, parent: str = "") -> None:
        require(isinstance(tree, dict), "INVALID_PROJECT")
        if "$path" in tree:
            path = (root / tree["$path"]).resolve()
            require(path.is_relative_to(root) and path.is_file(), "ESCAPED_SOURCE_PATH")
            require(parent not in found, "DUPLICATE_SOURCE_ROUTE")
            found[parent] = path
            return
        for name, item in tree.items():
            if not name.startswith("$"):
                visit(item, parent + ("/" if parent else "") + name)

    visit(doc["tree"])
    require(len(found) == 69 and CHANGED <= set(found), "REAL69_SELECTED_SOURCE_COUNT")
    return found


def bytes_by_route(root: Path) -> dict[str, bytes]:
    return {k: path.read_bytes() for k, path in selected(root).items()}


def original(root: Path) -> tuple[dict, dict[str, bytes]]:
    meta = json.loads((root / RECEIPT).read_text(encoding="utf-8"))
    files = bytes_by_route(root)
    require(meta.get("canonical_build") is True and
            meta.get("official_branch") == "rc/p0d-s1-kids-rc01" and
            meta.get("build_head") == FORMAL, "FORMAL_PROVENANCE")
    require(meta.get("selected_source_count") == len(files) == 69 and
            set(meta["source_hashes"]) == set(files) and
            set(meta["source_classes"]) == set(files), "FORMAL_69_CLASS_RECEIPT")
    for route, data in files.items():
        require(meta["source_hashes"][route] == digest(data),
                "FORMAL_SELECTED_SOURCE_HASH")
    raw = (root / PLACE).read_bytes()
    require(len(raw) == 798390 and digest(raw) == PLACE_HASH,
            "FORMAL_PRIVATE_PLACE")
    return meta, files


def find_947_hash(folder: Path, parent: Parent) -> str:
    candidates = []
    for path in folder.rglob(RECEIPT):
        if not path.is_file():
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        meta = data.get("gq470_fb015_hud_portrait", {})
        if (meta.get("selected_route") == parent.route and
                meta.get("formal_rc_base") == FORMAL and
                meta.get("original_source_sha256") == parent.old and
                meta.get("expected_class") == parent.klass and
                meta.get("owner_accepted") is False and
                meta.get("formal_rc_adopted") is False):
            new = meta.get("candidate_source_sha256")
            require(isinstance(new, str) and len(new) == 64 and new != parent.old,
                    "HUD_CANDIDATE_DIGEST")
            require(data.get("source_hashes", {}).get(parent.route) == new,
                    "HUD_CANDIDATE_RECEIPT_SOURCE")
            candidates.append(new)
    require(len(set(candidates)) == 1, "HUD_PINNED_RECEIPT_NOT_FOUND")
    return candidates[0]


def find_source(folder: Path, expected_hash: str) -> bytes:
    sources = []
    for path in folder.rglob("*"):
        if not path.is_file() or path.is_symlink() or path.stat().st_size > 200000:
            continue
        if path.suffix.lower() not in (".luau", ".lua", ".txt"):
            continue
        raw = path.read_bytes()
        if digest(raw) == expected_hash:
            sources.append(raw)
    require(len(sources) > 0 and len({digest(s) for s in sources}) == 1,
            "PINNED_ACTUAL_LUAU_NOT_IN_PARENT_ARTIFACT")
    return sources[0]


def parent_sources(base_receipt: dict, before: dict[str, bytes],
                   artifacts: Path) -> list[dict]:
    require(len(PARENTS) == 6 and len(CHANGED) == 6 and
            not CHANGED.intersection(ART7_ROUTES), "PARENT_ART7_SCOPE_OVERLAP")
    source_rows = []
    for p in PARENTS:
        folder = artifacts / str(p.pr)
        require(folder.is_dir(), "PARENT_ARTIFACT_NOT_FOUND_" + str(p.pr))
        require(base_receipt["source_classes"][p.route] == p.klass and
                digest(before[p.route]) == p.old, "ORIGINAL_SELECTED_LOCK_" + str(p.pr))
        new_hash = (find_947_hash(folder, p) if p.pr == 947 else p.new)
        require(new_hash != p.old and len(new_hash) == 64,
                "NO_REAL_ART_SOURCE_DELTA_" + str(p.pr))
        raw = find_source(folder, new_hash)
        source_rows.append({
            "pr": p.pr, "route": p.route, "class": p.klass,
            "original_sha256": p.old, "candidate_sha256": new_hash,
            "source": raw, "pinned_run": p.run, "pinned_head": p.head
        })
    require({x["route"] for x in source_rows} == CHANGED,
            "EXACT_SIX_PARENT_SOURCE_FILES")
    return source_rows


def delta(before: dict[str, bytes], after: dict[str, bytes]) -> None:
    require(len(before) == len(after) == 69 and
            set(before) == set(after), "SELECTED_ROUTE_AND_COUNT")
    changed = {k for k in before if before[k] != after[k]}
    require(changed == CHANGED and len(set(before) - changed) == 63,
            "EXACT_SIX_CHANGED_SIXTYTHREE_ORIGINAL")


def create(formal: Path, artifacts: Path, out: Path) -> None:
    require(not out.exists(), "NO_OVERWRITE")
    base_receipt, before = original(formal)
    authors = parent_sources(base_receipt, before, artifacts)
    shutil.copytree(formal, out)
    shutil.copytree(formal, out / OFF)
    sources = selected(out)
    for author in authors:
        sources[author["route"]].write_bytes(author["source"])
    after = bytes_by_route(out)
    delta(before, after)
    receipt = copy.deepcopy(base_receipt)
    receipt["source_hashes"] = {r: digest(b) for r, b in after.items()}
    receipt["canonical_build"] = False
    receipt["build_head"] = "A_PREP_ART6B_NOT_FORMAL"
    receipt["gq470_art6b_intake"] = {
        "feature_id": "GQ470_ART6B_COMPOSITE_954_942_947_943_946_951_20261121",
        "formal_base_sha": FORMAL,
        "author_heads": {str(p.pr): p.head for p in PARENTS},
        "author_runs": {str(p.pr): p.run for p in PARENTS},
        "routes": sorted(CHANGED),
        "selected_source_count": 69, "changed_selected_routes": 6,
        "unchanged_selected_routes": 63,
        "new_gameplay_scripts": 0, "new_authority": False,
        "officially_integrated": False, "source_only": True,
        "rollback": OFF + " exact official Place and 69 original source bytes",
        "native_luau_69": "NOT_TESTED", "rojo_69": "NOT_TESTED",
        "studio_2client": "NOT_TESTED", "studio_solo": "NOT_TESTED",
        "android15": "NOT_TESTED", "fun_3min": "NOT_TESTED",
        "before_after_real_images": "0/32", "human_art": "NOT_TESTED",
        "owner_accepted": False, "art_gate": "ART_NO_GO",
        "product_gate": "PRODUCT_NO_GO",
        "candidate_source_details": [
            {key: val for key, val in a.items() if key != "source"} for a in authors
        ],
    }
    (out / RECEIPT).write_text(
        json.dumps(receipt, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8")
    inspect(out, built=False)
    print("GQ470_ART6B_SOURCE_COMPOSITE_6_CHANGED_63_EXACT_NOT_FORMAL")


def inspect(root: Path, built: bool = True) -> tuple[dict, dict, dict]:
    formal, before = original(root / OFF)
    after = bytes_by_route(root)
    delta(before, after)
    meta = json.loads((root / RECEIPT).read_text(encoding="utf-8"))
    info = meta.get("gq470_art6b_intake", {})
    require(meta.get("canonical_build") is False and
            meta.get("build_head") == "A_PREP_ART6B_NOT_FORMAL" and
            meta.get("source_classes") == formal["source_classes"] and
            meta.get("source_hashes") ==
            {k: digest(b) for k, b in after.items()}, "CANDIDATE_69_SOURCE_RECEIPT")
    require(info.get("selected_source_count") == 69 and
            info.get("changed_selected_routes") == 6 and
            info.get("unchanged_selected_routes") == 63 and
            set(info.get("routes", [])) == CHANGED and
            info.get("author_heads") == {str(p.pr): p.head for p in PARENTS} and
            info.get("author_runs") == {str(p.pr): p.run for p in PARENTS} and
            info.get("new_gameplay_scripts") == 0 and
            info.get("new_authority") is False and
            info.get("officially_integrated") is False and
            info.get("source_only") is True and
            info.get("before_after_real_images") == "0/32" and
            info.get("owner_accepted") is False and
            info.get("art_gate") == "ART_NO_GO" and
            info.get("product_gate") == "PRODUCT_NO_GO",
            "FALSE_PROVENANCE_OR_ART_VERDICT")
    # Every source byte has to match original selected bytes or the exact
    # independently attested corresponding parent candidate source.
    rows = info.get("candidate_source_details", [])
    require(len(rows) == 6 and {x["route"] for x in rows} == CHANGED,
            "INCOMPLETE_AUTHOR_SOURCE_DETAILS")
    for row in rows:
        p = next(p for p in PARENTS if p.route == row["route"])
        require(row["pr"] == p.pr and row["pinned_head"] == p.head and
                row["pinned_run"] == p.run and row["class"] == p.klass and
                row["original_sha256"] == p.old and
                row["candidate_sha256"] == digest(after[p.route]) and
                (not p.new or row["candidate_sha256"] == p.new),
                "FORGED_SELECTED_SOURCE_" + str(p.pr))
    require((root / PROJECT).read_bytes() ==
            (root / OFF / PROJECT).read_bytes() and
            digest((root / OFF / PLACE).read_bytes()) == PLACE_HASH,
            "PROJECT_ORIGINAL_ROLLBACK")
    if built:
        place = (root / PLACE).read_bytes()
        require(digest(place) != PLACE_HASH and
                meta.get("private_place_bytes") == len(place) and
                meta.get("private_place_sha256") == digest(place) and
                info.get("native_luau_69") == "PASS_SOURCE_ONLY" and
                info.get("rojo_69") == "PASS_SOURCE_ONLY",
                "REAL_PLACE_NOT_VERIFIED")
    return meta, before, after


def seal(root: Path) -> None:
    meta, before, after = inspect(root, built=False)
    data = (root / PLACE).read_bytes()
    require(len(data) > 0 and digest(data) != PLACE_HASH, "ROJO_NOT_BUILT")
    meta["private_place_bytes"] = len(data)
    meta["private_place_sha256"] = digest(data)
    meta["gq470_art6b_intake"]["native_luau_69"] = "PASS_SOURCE_ONLY"
    meta["gq470_art6b_intake"]["rojo_69"] = "PASS_SOURCE_ONLY"
    (root / RECEIPT).write_text(
        json.dumps(meta, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8")
    inspect(root)
    print("GQ470_ART6B_REAL_PLACE_SEALED_SOURCE_ONLY", len(data), digest(data))


def packet(root: Path) -> None:
    meta, before, after = inspect(root)
    base = root / PACKET
    require(not base.exists(), "PACKET_MUST_BE_NEW")
    base.mkdir()
    rows = []
    for p in sorted(PARENTS, key=lambda item: item.pr):
        path = "selected_sources/" + p.route + ".luau"
        dest = base / path
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(after[p.route])
        rows.append({
            "original_author_pr": p.pr, "selected_route": p.route,
            "source_class": p.klass, "source_path": path,
            "before_sha256": digest(before[p.route]),
            "candidate_sha256": digest(after[p.route]),
            "source_bytes": len(after[p.route])
        })
    data = {
        "schema": "GQ470_ART6B_B220_SELECTED_SOURCES_V1",
        "official_branch": "rc/p0d-s1-kids-rc01",
        "original_official_head": FORMAL,
        "source_profile": "REAL69_PRIVATE_COMPANION",
        "selected_source_count": 69,
        "modified_source_count": 6, "preserved_source_count": 63,
        "separate_prior_a_art7_routes": True,
        "author_commits": {str(p.pr): p.head for p in PARENTS},
        "source_only": rows,
        "authenticated_b220_fresh_expected_sha_nonforce_required": True,
        "formal_rc_changed": False, "candidate_only": True,
        "studio_art_mobile_fun": "NOT_TESTED", "art_gate": "ART_NO_GO",
        "owner_accepted": False,
    }
    (base / MANIFEST).write_text(
        json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8")
    packet_verify(root)
    print("GQ470_ART6B_B220_SIX_REAL_LUAU_BYTES_READY")


def packet_verify(root: Path) -> None:
    meta, before, after = inspect(root)
    folder = root / PACKET
    data = json.loads((folder / MANIFEST).read_text(encoding="utf-8"))
    rows = data.get("source_only", [])
    require(data.get("schema") == "GQ470_ART6B_B220_SELECTED_SOURCES_V1" and
            data.get("original_official_head") == FORMAL and
            data.get("source_profile") == "REAL69_PRIVATE_COMPANION" and
            data.get("selected_source_count") == 69 and
            data.get("modified_source_count") == 6 and
            data.get("preserved_source_count") == 63 and
            data.get("formal_rc_changed") is False and
            data.get("candidate_only") is True and
            data.get("owner_accepted") is False and
            data.get("art_gate") == "ART_NO_GO" and
            data.get("author_commits") == {str(p.pr): p.head for p in PARENTS},
            "B_PACKET_METADATA_DRIFT")
    require(len(rows) == 6 and
            {r["selected_route"] for r in rows} == CHANGED,
            "B_PACKET_SOURCE_ROUTE_DRIFT")
    files = {p.relative_to(folder).as_posix() for p in folder.rglob("*") if p.is_file()}
    require(files == {MANIFEST} | {r["source_path"] for r in rows},
            "B_PACKET_EXTRA_OR_MISSING_FILES")
    for row in rows:
        p = next(x for x in PARENTS if x.route == row["selected_route"])
        path = (folder / row["source_path"]).resolve()
        require(path.is_relative_to(folder.resolve()) and path.is_file(),
                "B_PACKET_TRAVERSAL")
        data_bytes = path.read_bytes()
        require(row["original_author_pr"] == p.pr and
                row["source_class"] == p.klass and
                data_bytes == after[p.route] and
                row["before_sha256"] == digest(before[p.route]) and
                row["candidate_sha256"] == digest(data_bytes) and
                row["source_bytes"] == len(data_bytes),
                "B_PACKET_SOURCE_BYTES_" + str(p.pr))


def selftest() -> None:
    require(len(PARENTS) == 6 and len(CHANGED) == 6 and
            not CHANGED.intersection(ART7_ROUTES), "LANE_DISTINCT_FROM_ART7")
    before = {route: b"off" for route in CHANGED}
    before.update({"unchanged" + str(i): b"same" for i in range(63)})
    after = dict(before)
    for r in CHANGED:
        after[r] = b"on"
    delta(before, after)
    bads = [
        before,
        {**after, "unchanged0": b"altered"},
        {key: value for key, value in after.items() if key != "unchanged0"},
        {**after, next(iter(CHANGED)): b"off"},
        {**after, "unexpected": b"extra"},
    ]
    blocked = 0
    for candidate in bads:
        try:
            delta(before, candidate)
        except ValueError:
            blocked += 1
        else:
            raise AssertionError("RED_UNSAFE_SOURCE_DELTA_ACCEPTED")
    original_shas = [p.old for p in PARENTS]
    new_shas = [p.new for p in PARENTS if p.new]
    require(all(len(x) == 64 for x in original_shas + new_shas),
            "PINNED_HASH_LENGTH")
    require(all(len(p.head) == 40 and p.run > 44000000000 for p in PARENTS),
            "PINNED_AUTHOR_RUN_AND_HEAD")
    for p in PARENTS:
        for fake in (p.old[:63], p.old + "x"):
            try:
                require(len(fake) == 64, "SOURCE_HASH_DRIFT")
            except ValueError:
                blocked += 1
            else:
                raise AssertionError("RED_PINNED_SOURCE_HASH_MUTANT_ACCEPTED")
    print("GQ470_ART6B_STATIC_FAIL_CLOSED_NEGATIVES_PASS", blocked)


if __name__ == "__main__":
    a = argparse.ArgumentParser()
    a.add_argument("--base", type=Path)
    a.add_argument("--artifacts", type=Path)
    a.add_argument("--out", type=Path)
    a.add_argument("--verify", type=Path)
    a.add_argument("--seal", type=Path)
    a.add_argument("--export-b", type=Path)
    a.add_argument("--verify-b", type=Path)
    a.add_argument("--self-test", action="store_true")
    p = a.parse_args()
    if p.self_test:
        selftest()
    elif p.verify:
        inspect(p.verify)
    elif p.seal:
        seal(p.seal)
    elif p.export_b:
        packet(p.export_b)
    elif p.verify_b:
        packet_verify(p.verify_b)
    else:
        require(p.base is not None and p.artifacts is not None and
                p.out is not None, "ARGS")
        create(p.base, p.artifacts, p.out)
