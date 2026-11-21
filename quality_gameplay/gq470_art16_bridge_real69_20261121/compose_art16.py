#!/usr/bin/env python3
"""GQ470 ART16 A-only bridge: verified PR966 ART15 + PR967 Canyon/Moguron.

This script never edits official RC, checks exact previous A candidates before
reusing their REAL69 Luaus, fails closed on source-route collision, and emits
a byte-exact B220 selection packet. SOURCE pass is NOT Studio/ART/FUN pass.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
import shutil
from pathlib import Path

FORMAL = "e80973c354f14a0d0088577f3cc1a875454f0f8f"
FORMAL_SHA = "fc63171149a86f6b39779ba6ebe7e18fcb7099fbde98ad2ec33a7cb92b3a9934"
FORMAL_SIZE = 798390
PROJECT = "EGGRUMBLE_REAL69.project.json"
RECEIPT = "REAL69_LEGACY_INTAKE_RECEIPT.json"
PLACE = "EGGRUMBLE_REAL69_PRIVATE.rbxlx"
OFF = "OFF69_ART16_ORIGINAL"
PACKET = "B220_ART16_SELECTED_BYTES_ONLY_NOT_FORMAL"
NOTE = "gq470_art16_source_bridge"
MARKER = "ART16_A_SOURCE_BRIDGE_NOT_FORMAL"
PARENTS = (
    dict(pr=966, head="e7c425b3af566defaff71bd540734a117cf2bf2b",
         run=44844649777, artifact="GQ470-ART15-REAL69-ONE-B220-PACKET-NOT-FORMAL",
         changed=15, source_count=69,
         place_sha="98e76ff68e9763b97ee6805e3d7fd24e422b27a23372d3f9afd684066d797084"),
    dict(pr=967, head="89719973047c13dde5ba64732231814a4db32f42",
         run=44845621663,
         artifact="GQ470-REAL69-CANYON-MOGURON-933-967-B220-PACKET-NOT-FORMAL",
         changed=1, source_count=69,
         place_sha="2c14ff8ddf304da21046cd13ad54da0b56c9b6e603525199d37de108ee13a647"),
)

def need(ok: bool, tag: str) -> None:
    if not ok:
        raise ValueError("RED_GQ470_ART16_" + tag)

def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()

def get_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))

def select(root: Path) -> dict[str, tuple[Path, str]]:
    """Project declaration, not directory guesses, defines runtime source."""
    root = root.resolve()
    project = get_json(root / PROJECT)
    paths: dict[str, tuple[Path, str]] = {}
    def visit(node: dict, route: str = "") -> None:
        need(isinstance(node, dict), "PROJECT_NODE")
        if "$path" in node:
            rel = node["$path"]
            need(isinstance(rel, str) and not rel.startswith("/"), "PATH_KIND")
            p = (root / rel).resolve()
            need(p.is_relative_to(root) and p.is_file() and route not in paths,
                 "PATH_TRAVERSAL_FILE_OR_DUPLICATE")
            kind = ("LocalScript" if rel.endswith(".client.luau") else
                    "Script" if rel.endswith(".server.luau") else "ModuleScript")
            paths[route] = (p, kind)
            return
        for key, child in node.items():
            if not key.startswith("$"):
                visit(child, f"{route}/{key}" if route else key)
    visit(project["tree"])
    need(len(paths) == 69, "SELECTED69_NOT_PROVEN")
    return paths

def source_map(root: Path) -> tuple[dict[str, bytes], dict[str, str]]:
    paths = select(root)
    return ({route: value[0].read_bytes() for route, value in paths.items()},
            {route: value[1] for route, value in paths.items()})

def exact_formal(root: Path) -> tuple[dict, dict[str, bytes], dict[str, str]]:
    metadata = get_json(root / RECEIPT)
    original, classes = source_map(root)
    need(metadata.get("canonical_build") is True and
         metadata.get("official_branch") == "rc/p0d-s1-kids-rc01" and
         metadata.get("build_head") == FORMAL and
         metadata.get("selected_source_count") == 69 and
         metadata.get("source_hashes") == {r: sha(v) for r, v in original.items()} and
         metadata.get("source_classes") == classes, "AUTHENTIC_REAL69_RECEIPT")
    place = (root / PLACE).read_bytes()
    need(len(place) == FORMAL_SIZE and sha(place) == FORMAL_SHA,
         "AUTHENTIC_REAL69_PLACE")
    return metadata, original, classes

def candidate_root(root: Path) -> Path:
    paths = [p.parent for p in root.rglob(PROJECT)
             if (p.parent / RECEIPT).is_file() and (p.parent / PLACE).is_file()
             and "OFF69_" not in str(p.parent)]
    need(len(paths) == 1, "ONE_PARENT_CANDIDATE_REQUIRED")
    return paths[0]

def parent_delta(spec: dict, artifact: Path, formal: Path,
                 pristine: dict[str, bytes], classes: dict[str, str]) -> dict[str, bytes]:
    c = candidate_root(artifact)
    need((c / PROJECT).read_bytes() == (formal / PROJECT).read_bytes(),
         "PARENT_REWRITES_PROJECT")
    metadata = get_json(c / RECEIPT)
    candidate, found_classes = source_map(c)
    need(found_classes == classes and set(candidate) == set(pristine),
         "PARENT_SOURCE_CLASSES_OR_ROUTES")
    need(metadata.get("source_hashes") == {r: sha(b) for r,b in candidate.items()}
         and metadata.get("source_classes") == classes,
         "PARENT_SOURCE_HASH_RECEIPT")
    need(sha((c / PLACE).read_bytes()) == spec["place_sha"],
         "PINNED_PARENT_ACTUAL_PLACE")
    changed = {route for route in candidate if candidate[route] != pristine[route]}
    need(len(changed) == spec["changed"], "PARENT_EXACT_CHANGED_COUNT")
    if spec["pr"] == 966:
        note = metadata.get("gq470_art15_fast_bridge", {})
        need(note.get("changed_selected_routes") == 15 and
             note.get("unchanged_selected_routes") == 54 and
             note.get("formal_base_sha") == FORMAL and
             note.get("source_only") is True and
             note.get("officially_integrated") is False and
             note.get("owner_accepted") is False and
             note.get("art_gate") == "ART_NO_GO" and
             note.get("native_69") == "PASS_SOURCE_ONLY" and
             note.get("rojo_69") == "PASS_SOURCE_ONLY",
             "ART15_PROVENANCE_OR_UNTRUE_GATE")
    elif spec["pr"] == 967:
        canyon = metadata.get("gq470_canyon_facet_shoreline", {})
        mole = metadata.get("gq470_moguron_matte", {})
        need(len(changed) == 1 and
             "ServerScriptService/EGGRUMBLE_LegacyCanyonRoutes" in changed and
             canyon.get("owner_accepted") is False and
             mole.get("owner_accepted") is False and
             mole.get("candidate_head") == spec["head"] and
             mole.get("native_rojo_off69") == "PASS_SOURCE_ONLY" and
             canyon.get("native_rojo_off69") == "PASS_SOURCE_ONLY",
             "CANYON_MOLE_COMPOSITE_PROVENANCE")
    return {route: candidate[route] for route in changed}

def assert_disjoint(a: set[str], b: set[str], expected_a: int = 15,
                    expected_b: int = 1) -> None:
    need(len(a) == expected_a and len(b) == expected_b and not (a & b),
         "COLLIDING_OR_MISSING_AUTHOR_SOURCE_ROUTE")

def diff(before: dict[str, bytes], after: dict[str, bytes],
         expected: set[str]) -> None:
    need(len(before) == len(after) == 69 and set(before) == set(after),
         "69_ROUTE_CLASS_CONTRACT")
    need({r for r in before if before[r] != after[r]} == expected
         and len(expected) == 16 and len(before.keys() - expected) == 53,
         "EXACT_16_CHANGED_53_UNCHANGED")

def compose(formal: Path, parents: Path, out: Path) -> None:
    need(not out.exists(), "NO_OUTPUT_OVERWRITE")
    receipt, before, classes = exact_formal(formal)
    patches: dict[str, bytes] = {}
    owners: dict[str, list[str]] = {}
    for spec in PARENTS:
        part = parent_delta(spec, parents / str(spec["pr"]), formal, before, classes)
        assert_disjoint(set(patches), set(part), 0 if not patches else 15,
                        spec["changed"])
        # An empty accumulator may only receive the first 15-source packet.
        patches.update(part)
        owners[str(spec["pr"])] = sorted(part)
    need(len(patches) == 16 and len(owners["966"]) == 15 and
         len(owners["967"]) == 1, "16_SOURCE_NOLOSS_AND_OWNER_MAP")
    shutil.copytree(formal, out)
    shutil.copytree(formal, out / OFF)
    selected = select(out)
    for route, content in patches.items():
        selected[route][0].write_bytes(content)
    after, after_classes = source_map(out)
    diff(before, after, set(patches))
    need(after_classes == classes, "SOURCE_CLASS_DIVERGENCE")
    receipt = copy.deepcopy(receipt)
    receipt["canonical_build"] = False
    receipt["build_head"] = MARKER
    receipt["source_hashes"] = {r: sha(b) for r,b in after.items()}
    receipt[NOTE] = {
        "feature_id": "GQ470_ART16_966_967_SOURCE_BRIDGE_20261121",
        "formal_base_sha": FORMAL, "parent_heads": [{k:s[k] for k in
          ("pr","head","run","artifact")} for s in PARENTS],
        "parent_routes": owners,
        "source_count": 69, "selected_changed": 16,
        "untouched_original": 53, "gameplay_authority_added": 0,
        "only_visual_original_art_16_sources": True,
        "officially_integrated": False,
        "native_69_on_off": "NOT_TESTED",
        "rojo_69_on_off": "NOT_TESTED",
        "studio": "NOT_TESTED", "android_15min": "NOT_TESTED",
        "real_old_new_screenshots": "0/32", "human_art": "NOT_TESTED",
        "kid_fun": "NOT_TESTED", "owner_accepted": False,
        "product_gate": "PRODUCT_NO_GO", "art_gate": "ART_NO_GO",
        "mobile_gate": "MOBILE_NO_GO", "fun_gate": "FUN_NO_GO",
        "rollback": OFF,
    }
    (out / RECEIPT).write_text(json.dumps(receipt, ensure_ascii=False,
                             sort_keys=True, indent=2) + "\n", encoding="utf-8")
    verify(out, sealed=False)
    print("ART16_COMPOSE_16_OF_69_TRUE_CHANGED_53_EXACT_A_ONLY")

def verify(root: Path, sealed: bool = True) -> None:
    _, old, classes = exact_formal(root / OFF)
    metadata = get_json(root / RECEIPT)
    after, updated_classes = source_map(root)
    note = metadata.get(NOTE,{})
    owners = note.get("parent_routes", {})
    need(set(owners) == {"966","967"} and len(owners["966"]) == 15
         and len(owners["967"]) == 1, "AUTHOR_MAP")
    first, second = set(owners["966"]), set(owners["967"])
    assert_disjoint(first, second)
    diff(old,after,first|second)
    need(updated_classes == classes and metadata.get("source_classes") == classes
         and metadata.get("source_hashes") == {r:sha(b) for r,b in after.items()},
         "SOURCES_HASH_CLASS_MATCH")
    need(metadata.get("canonical_build") is False and
         metadata.get("build_head") == MARKER and
         note.get("formal_base_sha") == FORMAL and
         note.get("source_count") == 69 and note.get("selected_changed") == 16
         and note.get("untouched_original") == 53 and
         note.get("parent_heads") == [{k:s[k] for k in
           ("pr","head","run","artifact")} for s in PARENTS] and
         note.get("gameplay_authority_added") == 0 and
         note.get("officially_integrated") is False and
         note.get("owner_accepted") is False and
         note.get("real_old_new_screenshots") == "0/32" and
         note.get("art_gate") == "ART_NO_GO" and
         note.get("product_gate") == "PRODUCT_NO_GO",
         "FALSE_GO_OR_DRIFT")
    need((root / PROJECT).read_bytes() == (root / OFF / PROJECT).read_bytes(),
         "PROJECT_DRIFT")
    if sealed:
        place = (root / PLACE).read_bytes()
        need(sha(place) != FORMAL_SHA and
             metadata.get("private_place_bytes") == len(place) and
             metadata.get("private_place_sha256") == sha(place) and
             note.get("native_69_on_off") == "PASS_SOURCE_ONLY" and
             note.get("rojo_69_on_off") == "PASS_SOURCE_ONLY", "UNSEALED_REAL_PLACE")

def seal(root: Path) -> None:
    verify(root, sealed=False)
    place = (root / PLACE).read_bytes()
    need(sha(place) != FORMAL_SHA and len(place) > 0, "NO_ACTUAL_CANDIDATE_PLACE")
    meta = get_json(root / RECEIPT)
    meta["private_place_bytes"] = len(place)
    meta["private_place_sha256"] = sha(place)
    meta[NOTE]["native_69_on_off"] = "PASS_SOURCE_ONLY"
    meta[NOTE]["rojo_69_on_off"] = "PASS_SOURCE_ONLY"
    (root / RECEIPT).write_text(json.dumps(meta, ensure_ascii=False,
                                sort_keys=True, indent=2) + "\n", encoding="utf-8")
    verify(root)
    print("ART16_SOURCE_ONLY_SEALED_PLACE",len(place),sha(place))

def export_b(root: Path) -> None:
    verify(root)
    _, before, _ = exact_formal(root / OFF)
    after, classes = source_map(root)
    parent_routes = get_json(root / RECEIPT)[NOTE]["parent_routes"]
    chosen = set(parent_routes["966"]) | set(parent_routes["967"])
    packet_root = root / PACKET
    need(not packet_root.exists(), "B_PACKET_NO_OVERWRITE")
    rows=[]
    for route in sorted(chosen):
        file_rel = "selected_sources/" + route + ".luau"
        p = packet_root / file_rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(after[route])
        rows.append(dict(selected_route=route, selected_class=classes[route],
                         selected_path=file_rel, original_sha256=sha(before[route]),
                         new_sha256=sha(after[route]), bytes=len(after[route]),
                         source_parent=966 if route in parent_routes["966"] else 967))
    manifest = {
        "schema": "GQ470_ART16_966_967_B220_SOURCE_ONLY_V1",
        "formal_head": FORMAL, "source_profile": "REAL69_PRIVATE_COMPANION",
        "original_script_count": 69, "selected_changed": 16,
        "other53_exact": True, "source_only": rows, "parent_heads": PARENTS,
        "source_authorized_for_formal": False, "formal_rc_adopted": False,
        "requires_unique_writer_220_fresh_expected_sha_nonforce": True,
        "studio": "NOT_TESTED", "android": "NOT_TESTED",
        "real_png": "0/32", "art_gate": "ART_NO_GO",
        "owner_accepted": False
    }
    (packet_root / "SOURCE_SELECT_MANIFEST.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True)+"\n",
        encoding="utf-8")
    test = get_json(packet_root / "SOURCE_SELECT_MANIFEST.json")
    need(len(test["source_only"])==16
         and {r["selected_route"] for r in test["source_only"]}==chosen
         and all((packet_root / r["selected_path"]).read_bytes()
                 == after[r["selected_route"]] for r in rows)
         and test["formal_rc_adopted"] is False and
         test["art_gate"] == "ART_NO_GO",
         "B16_PACKET_SOURCE_BYTES_UNPROVEN")
    print("ART16_B220_PACKET_EXACT16_SOURCE_BYTES_READY_NOT_FORMAL")

def self_test() -> None:
    assert_disjoint(set(range(15)),{15})
    for a,b in ((set(range(15)),{14}), (set(range(14)),{15}),
                (set(range(15)),set()),(set(range(16)),{16})):
        try:
            assert_disjoint(a,b)
        except ValueError:
            pass
        else:
            raise AssertionError("MUTANT_OVERLAP_COUNT_ACCEPTED")
    old = {str(i):b"a" for i in range(69)}
    newer = dict(old)
    for i in range(16): newer[str(i)]=b"b"
    diff(old,newer,{str(i) for i in range(16)})
    newer["17"]=b"FORBIDDEN_UNOWNED_CHANGE"
    try:
        diff(old,newer,{str(i) for i in range(16)})
    except ValueError:
        pass
    else:
        raise AssertionError("MUTANT_UNOWNED_ROUTE_ACCEPTED")
    print("ART16_SIX_DISJOINT_COUNT_AND_UNOWNED_ROUTE_NEGATIVES_PASS")

if __name__ == "__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--base",type=Path)
    p.add_argument("--parents",type=Path)
    p.add_argument("--out",type=Path)
    p.add_argument("--seal",type=Path)
    p.add_argument("--verify",type=Path)
    p.add_argument("--export-b",type=Path)
    p.add_argument("--self-test",action="store_true")
    a=p.parse_args()
    if a.self_test: self_test()
    elif a.base and a.parents and a.out: compose(a.base,a.parents,a.out)
    elif a.seal: seal(a.seal)
    elif a.verify: verify(a.verify)
    elif a.export_b: export_b(a.export_b)
    else: p.error("give --self-test or --base/--parents/--out or --seal/--verify/--export-b")
