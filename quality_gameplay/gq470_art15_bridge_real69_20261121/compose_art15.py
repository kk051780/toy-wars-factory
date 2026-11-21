#!/usr/bin/env python3
"""ART15 B220 rapid admission bridge: compose three disjoint verified *source-only* A packets.

Uses #961 ART7, #964 ART6B and #963 castle2 candidate artifacts,
never their Git commits/PR merge contents. Does NOT write the canonical RC.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
from pathlib import Path
import shutil

FORMAL = "e80973c354f14a0d0088577f3cc1a875454f0f8f"
FORMAL_PLACE = "fc63171149a86f6b39779ba6ebe7e18fcb7099fbde98ad2ec33a7cb92b3a9934"
PROJECT = "EGGRUMBLE_REAL69.project.json"
RECEIPT = "REAL69_LEGACY_INTAKE_RECEIPT.json"
PLACE = "EGGRUMBLE_REAL69_PRIVATE.rbxlx"
OFF = "OFF69_ART15_ORIGINAL"
PACKET = "B220_ART15_SELECTED_BYTES_ONLY_NOT_FORMAL"
SOURCES = "selected_sources"
MANIFEST = "SOURCE_SELECT_MANIFEST.json"

PARENTS = (
    {"pr": 961, "head": "a3a750d167a0c1042f098f63bd1802ad5cbf31e5",
     "run": 44840200202, "artifact": "GQ470-ART7-REAL69-SELECTED-SOURCES-NOT-FORMAL",
     "source_count": 7, "unchanged": 62, "receipt_key": "gq470_art7_intake",
     "place_sha": "60cbd3fc3945ce04c976218fbcfff4d9aaa3c9f3a8b7310c502ee795f04a3893"},
    {"pr": 964, "head": "ece8c4ee909cceaea870b0fff3df4983f2ee9012",
     "run": 44840981553, "artifact": "GQ470-ART6B-REAL69-SELECTED-SOURCES-NOT-FORMAL",
     "source_count": 6, "unchanged": 63, "receipt_key": "gq470_art6b_intake",
     "place_sha": "05f57a56b9037234e3e9cae9079abbafe972eaf585a9585a2746902f587eb455"},
    {"pr": 963, "head": "ca577768d91bc2b611433c255230327d013e68e7",
     "run": 44840359818,
     "artifact": "GQ470-REAL69-GUARDIAN-GATEHP-TWO-SOURCES-NOT-FORMAL",
     "source_count": 2, "unchanged": 67, "receipt_key": "gq470_dual_candidate_957_958",
     "place_sha": "f94ee0e10fe45ea2187a2b12643af4b2a707835e04cdf1f6445f83031727d9fa"},
)


def require(ok: bool, error: str) -> None:
    if not ok:
        raise ValueError("RED_GQ470_ART15_" + error)


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def selected(root: Path) -> dict[str, Path]:
    root = root.resolve()
    project = json.loads((root / PROJECT).read_text(encoding="utf-8"))
    output = {}

    def walk(node: dict, route: str = "") -> None:
        require(isinstance(node, dict), "PROJECT_TREE")
        if "$path" in node:
            p = (root / node["$path"]).resolve()
            require(p.is_relative_to(root) and p.is_file() and route not in output,
                    "SOURCE_PATH_UNSAFE_OR_DUPLICATE")
            output[route] = p
            return
        for name, child in node.items():
            if not name.startswith("$"):
                walk(child, route + ("/" if route else "") + name)

    walk(project["tree"])
    require(len(output) == 69, "REAL69_SOURCE_COUNT")
    return output


def bytes_map(root: Path) -> dict[str, bytes]:
    return {route: p.read_bytes() for route, p in selected(root).items()}


def original(root: Path) -> tuple[dict, dict[str, bytes]]:
    meta = json.loads((root / RECEIPT).read_text(encoding="utf-8"))
    sources = bytes_map(root)
    require(meta.get("canonical_build") is True and
            meta.get("build_head") == FORMAL and
            meta.get("official_branch") == "rc/p0d-s1-kids-rc01" and
            meta.get("selected_source_count") == 69 and
            set(meta.get("source_hashes", {})) == set(sources) and
            set(meta.get("source_classes", {})) == set(sources),
            "ORIGINAL_CANONICAL_RECEIPT")
    require(all(meta["source_hashes"][k] == sha(raw) for k, raw in sources.items()),
            "ORIGINAL_SOURCE_HASHES")
    p = (root / PLACE).read_bytes()
    require(len(p) == 798390 and sha(p) == FORMAL_PLACE,
            "ORIGINAL_FORMAL_PRIVATE_PLACE")
    return meta, sources


def parent_candidate(parent: dict, root: Path,
                     original_receipt: dict,
                     original_sources: dict[str, bytes]) -> dict[str, bytes]:
    # A uploads may have an artifact root above their
    # candidate/ folder because the rollback Place is a sibling.
    artifact_root = root
    candidates = [p.parent for p in artifact_root.rglob(PROJECT)
                  if (p.parent / PLACE).is_file() and
                     (p.parent / RECEIPT).is_file()]
    require(len(candidates) == 1, "PARENT_ARTIFACT_INCOMPLETE")
    root = candidates[0]
    p = (root / PLACE).read_bytes()
    require(sha(p) == parent["place_sha"], "PARENT_PINNED_PLACE_SHA")
    require((root / PROJECT).read_bytes() ==
            (artifact_root.parent.parent / "formal" / PROJECT).read_bytes(),
            "PARENT_PROJECT_DRIFT")
    candidate = bytes_map(root)
    info = json.loads((root / RECEIPT).read_text(encoding="utf-8"))
    note = info.get(parent["receipt_key"], {})
    require((info.get("canonical_build") is False if parent["pr"] != 963
             else (info.get("canonical_build") is True and
                   info.get("build_head") == FORMAL)) and
            info.get("source_classes") == original_receipt["source_classes"] and
            info.get("source_hashes") ==
            {k: sha(b) for k, b in candidate.items()},
            "PARENT_CANDIDATE_SOURCE_RECEIPT")
    changed = {k for k in candidate if candidate[k] != original_sources[k]}
    require(len(changed) == parent["source_count"] and
            len(candidate) - len(changed) == parent["unchanged"] and
            (
                (note.get("changed_selected_routes") == parent["source_count"] and
                 note.get("unchanged_selected_routes") == parent["unchanged"] and
                 note.get("officially_integrated") is False and
                 note.get("owner_accepted") is False and
                 note.get("source_only") is True and
                 note.get("art_gate") == "ART_NO_GO" and
                 note.get("product_gate") == "PRODUCT_NO_GO" and
                 note.get("formal_base_sha") == FORMAL)
                if parent["pr"] != 963 else
                (set(note.get("only_selected_routes_changed", [])) == changed and
                 note.get("unchanged_selected_sources") == 67 and
                 note.get("formal_integrated") is False and
                 note.get("no_new_server_authority") is True and
                 note.get("native_rojo_off69") == "PASS_SOURCE_ONLY" and
                 note.get("original_formal_head") == FORMAL)
            ) and
            info.get("private_place_sha256") == parent["place_sha"],
            "PARENT_SCOPE_OR_FALSE_ART")
    for k in changed:
        require(k in original_sources and k in original_receipt["source_classes"],
                "PARENT_UNRECOGNIZED_SELECTED_SCRIPT")
    return {route: candidate[route] for route in changed}


def changed_routes(before: dict[str, bytes], after: dict[str, bytes],
                   expected: set[str], count: int) -> None:
    require(len(before) == len(after) == 69 and
            set(before) == set(after), "SCRIPT_69_ROUTE_LOCK")
    actual = {route for route in before if before[route] != after[route]}
    require(actual == expected and len(actual) == count and
            len(set(before) - actual) == 69 - count,
            "EXACT_NONOVERLAP_SCRIPTS")


def create(formal: Path, parents: Path, output: Path) -> None:
    require(not output.exists(), "OUTPUT_ALREADY_EXISTS")
    baseline, before = original(formal)
    patches: dict[str, bytes] = {}
    by_parent = {}
    for parent in PARENTS:
        root = parents / str(parent["pr"])
        art = parent_candidate(parent, root, baseline, before)
        require(not patches.keys() & art.keys(), "OVERLAPPING_ART7_ART6B_CASTLE2_SOURCE_ROUTE")
        patches.update(art)
        by_parent[str(parent["pr"])] = sorted(art)
    require(len(patches) == 15 and
            set(by_parent) == {"961", "964", "963"}, "EXACT_7_PLUS_6_PLUS_2")
    shutil.copytree(formal, output)
    shutil.copytree(formal, output / OFF)
    files = selected(output)
    for route, raw in patches.items():
        files[route].write_bytes(raw)
    after = bytes_map(output)
    changed_routes(before, after, set(patches), 15)
    receipt = copy.deepcopy(baseline)
    receipt["canonical_build"] = False
    receipt["build_head"] = "ART15_A_SOURCE_BRIDGE_NOT_OFFICIAL"
    receipt["source_hashes"] = {route: sha(raw) for route, raw in after.items()}
    receipt["gq470_art15_fast_bridge"] = {
        "feature_id": "GQ470_ART15_961_964_SOURCE_BRIDGE_20261121",
        "formal_base_sha": FORMAL,
        "parent_authors": [{"pr": x["pr"], "head": x["head"], "run": x["run"]}
                           for x in PARENTS],
        "parent_routes": by_parent, "selected_source_count": 69,
        "changed_selected_routes": 15, "unchanged_selected_routes": 54,
        "source_only": True, "new_gameplay_scripts": 0,
        "new_hp_egg_score_store_remote_authority": False,
        "officially_integrated": False, "rollback": OFF,
        "native_69": "NOT_TESTED", "rojo_69": "NOT_TESTED",
        "studio_solo": "NOT_TESTED", "studio_2client": "NOT_TESTED",
        "android15min": "NOT_TESTED", "kid_fun": "NOT_TESTED",
        "real_32_capture": "0/32", "human_art": "NOT_TESTED",
        "owner_accepted": False, "art_gate": "ART_NO_GO",
        "product_gate": "PRODUCT_NO_GO",
    }
    (output / RECEIPT).write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8")
    inspect(output, built=False)
    print("GQ470_ART15_15_SELECTED_CHANGED_54_EXACT_SOURCE_BRIDGE_PREP")


def inspect(root: Path, built: bool = True):
    original_receipt, before = original(root / OFF)
    after = bytes_map(root)
    receipt = json.loads((root / RECEIPT).read_text(encoding="utf-8"))
    note = receipt.get("gq470_art15_fast_bridge", {})
    routes = note.get("parent_routes", {})
    require(set(routes) == {"961", "964", "963"} and
            len(routes["961"]) == 7 and len(routes["964"]) == 6 and
            len(routes["963"]) == 2 and
            len(set(routes["961"]) | set(routes["964"]) | set(routes["963"])) == 15,
            "PARENT_ROUTE_NONOVERLAP")
    expected = set(routes["961"]) | set(routes["964"]) | set(routes["963"])
    changed_routes(before, after, expected, 15)
    require(receipt.get("canonical_build") is False and
            receipt.get("build_head") == "ART15_A_SOURCE_BRIDGE_NOT_OFFICIAL" and
            receipt.get("source_classes") == original_receipt["source_classes"] and
            receipt.get("source_hashes") ==
            {route: sha(raw) for route, raw in after.items()}, "RECEIPT_SOURCE_LOCK")
    require(note.get("formal_base_sha") == FORMAL and
            note.get("parent_authors") ==
            [{"pr": x["pr"], "head": x["head"], "run": x["run"]} for x in PARENTS] and
            note.get("selected_source_count") == 69 and
            note.get("changed_selected_routes") == 15 and
            note.get("unchanged_selected_routes") == 54 and
            note.get("source_only") is True and
            note.get("new_gameplay_scripts") == 0 and
            note.get("new_hp_egg_score_store_remote_authority") is False and
            note.get("officially_integrated") is False and
            note.get("owner_accepted") is False and
            note.get("real_32_capture") == "0/32" and
            note.get("art_gate") == "ART_NO_GO" and
            note.get("product_gate") == "PRODUCT_NO_GO", "FAKE_FORMAL_OR_ART")
    require((root / PROJECT).read_bytes() ==
            (root / OFF / PROJECT).read_bytes() and
            sha((root / OFF / PLACE).read_bytes()) == FORMAL_PLACE,
            "ORIGINAL_ROLLBACK_EXACT")
    if built:
        p = (root / PLACE).read_bytes()
        require(sha(p) != FORMAL_PLACE and
                receipt.get("private_place_bytes") == len(p) and
                receipt.get("private_place_sha256") == sha(p) and
                note.get("native_69") == "PASS_SOURCE_ONLY" and
                note.get("rojo_69") == "PASS_SOURCE_ONLY",
                "ROJO_PLACE_NOT_SEALED")
    return receipt, before, after, expected


def seal(root: Path) -> None:
    receipt, _, _, _ = inspect(root, built=False)
    p = (root / PLACE).read_bytes()
    require(len(p) > 0 and sha(p) != FORMAL_PLACE, "UNBUILT_PLACE")
    receipt["private_place_bytes"] = len(p)
    receipt["private_place_sha256"] = sha(p)
    receipt["gq470_art15_fast_bridge"]["native_69"] = "PASS_SOURCE_ONLY"
    receipt["gq470_art15_fast_bridge"]["rojo_69"] = "PASS_SOURCE_ONLY"
    (root / RECEIPT).write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8")
    inspect(root)
    print("GQ470_ART15_CANDIDATE_PLACE_SOURCE_SEALED", len(p), sha(p))


def export_b(root: Path) -> None:
    receipt, before, after, routes = inspect(root)
    out = root / PACKET
    require(not out.exists(), "NO_OVERWRITE_B")
    out.mkdir()
    rows = []
    for route in sorted(routes):
        name = SOURCES + "/" + route + ".luau"
        dest = out / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(after[route])
        rows.append({
            "source_path": name, "selected_route": route,
            "source_class": receipt["source_classes"][route],
            "original_sha256": sha(before[route]),
            "candidate_sha256": sha(after[route]),
            "source_bytes": len(after[route])
        })
    packet = {
        "schema": "GQ470_ART15_B220_SOURCE_SELECT_V1",
        "official_branch": "rc/p0d-s1-kids-rc01",
        "formal_base_sha": FORMAL,
        "source_profile": "REAL69_PRIVATE_COMPANION",
        "source_selected_count": 69, "changed_selected_routes": 15,
        "unchanged_selected_routes": 54, "source_only": rows,
        "parent_head_run": [{"pr":p["pr"],"head":p["head"],"run":p["run"]}
                            for p in PARENTS],
        "authoritative_b220_fresh_expected_sha_nonforce_only": True,
        "candidate_not_official": True, "formal_rc_adopted": False,
        "art_gate": "ART_NO_GO", "studio_android_fun": "NOT_TESTED",
        "owner_accepted": False
    }
    (out / MANIFEST).write_text(
        json.dumps(packet, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8")
    verify_b(root)
    print("GQ470_ART15_B220_SELECTED_15_LUAU_BYTES_PACKAGE_PASS")


def verify_b(root: Path) -> None:
    receipt, before, after, expected = inspect(root)
    base = root / PACKET
    info = json.loads((base / MANIFEST).read_text(encoding="utf-8"))
    rows = info.get("source_only", [])
    require(info.get("schema") == "GQ470_ART15_B220_SOURCE_SELECT_V1" and
            info.get("formal_base_sha") == FORMAL and
            info.get("source_profile") == "REAL69_PRIVATE_COMPANION" and
            info.get("source_selected_count") == 69 and
            info.get("changed_selected_routes") == 15 and
            info.get("unchanged_selected_routes") == 54 and
            info.get("formal_rc_adopted") is False and
            info.get("candidate_not_official") is True and
            info.get("art_gate") == "ART_NO_GO" and
            info.get("owner_accepted") is False and
            info.get("parent_head_run") ==
            [{"pr":p["pr"],"head":p["head"],"run":p["run"]} for p in PARENTS],
            "B_METADATA")
    require(len(rows) == 15 and
            {r["selected_route"] for r in rows} == expected,
            "B_EXACT_15_ROUTES")
    found = {p.relative_to(base).as_posix() for p in base.rglob("*") if p.is_file()}
    require(found == {MANIFEST} | {r["source_path"] for r in rows},
            "B_FILES_NOT_EXACT")
    for r in rows:
        f = (base / r["source_path"]).resolve()
        route = r["selected_route"]
        require(f.is_relative_to(base.resolve()) and f.is_file() and
                f.read_bytes() == after[route] and
                r["candidate_sha256"] == sha(after[route]) and
                r["original_sha256"] == sha(before[route]) and
                r["source_class"] == receipt["source_classes"][route] and
                r["source_bytes"] == len(after[route]),
                "B_CORRUPTED_SOURCE_" + route)


def selftest() -> None:
    before = {"r" + str(i): b"off" for i in range(69)}
    after = dict(before)
    changed = {"r" + str(i) for i in range(15)}
    for k in changed:
        after[k] = b"on"
    changed_routes(before, after, changed, 15)
    negatives = [
        before,
        {**after, "r15": b"mutated"},
        {**after, "r0": b"off"},
        {**after, "new": b"extra"},
        {k:v for k,v in after.items() if k != "r65"},
        {**after,"r13":b"mutated","r0":b"off"},
    ]
    blocked=0
    for value in negatives:
        try: changed_routes(before, value, changed, 15)
        except ValueError: blocked+=1
        else: raise AssertionError("RED_WRONG_15_SOURCE_PASS")
    require({x["pr"] for x in PARENTS} == {961,964,963} and
            all(len(x["head"]) == 40 and len(x["place_sha"]) == 64
                for x in PARENTS), "PARENT_IDENTITY")
    print("GQ470_ART15_STATIC_" + str(blocked) + "_SOURCE_MUTANT_NEGATIVES_PASS")


if __name__ == "__main__":
    a=argparse.ArgumentParser()
    a.add_argument("--base",type=Path)
    a.add_argument("--parents",type=Path)
    a.add_argument("--out",type=Path)
    a.add_argument("--verify",type=Path)
    a.add_argument("--seal",type=Path)
    a.add_argument("--export-b",type=Path)
    a.add_argument("--verify-b",type=Path)
    a.add_argument("--self-test",action="store_true")
    x=a.parse_args()
    if x.self_test:selftest()
    elif x.verify:inspect(x.verify)
    elif x.seal:seal(x.seal)
    elif x.export_b:export_b(x.export_b)
    elif x.verify_b:verify_b(x.verify_b)
    else:
        require(x.base is not None and x.parents is not None and
                x.out is not None,"MISSING_INPUTS")
        create(x.base,x.parents,x.out)
