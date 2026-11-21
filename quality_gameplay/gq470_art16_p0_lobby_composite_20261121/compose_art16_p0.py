#!/usr/bin/env python3
"""Verified ART16 (PR970) + early-lobby P0 (PR980) source-only REAL69 compositor.

Reads pinned *actual* GitHub Actions artifacts, preserves all author code verbatim,
emits exactly 17 selected sources for certified B220 adoption. No official RC write,
no Studio/fps/ART claim and no direct PR merge.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
import shutil
from pathlib import Path

FORMAL = "e80973c354f14a0d0088577f3cc1a875454f0f8f"
FORMAL_PLACE_SHA = "fc63171149a86f6b39779ba6ebe7e18fcb7099fbde98ad2ec33a7cb92b3a9934"
FORMAL_PLACE_BYTES = 798390
ART16_HEAD = "180f5067bfe71c59b8c0c59b90aa69f1cd00cb7f"
ART16_PLACE_SHA = "41a4bad1ce3fe8aa7f04c92cecfe4c710fbe92e702151887066279c2f3fda703"
P0_HEAD = "579cae991c609730291cdb3531c3a4cf916cd79f"
P0_PLACE_SHA = "001870f50f33b3741e221b8cef1cd66350226757875a13452f6c0cd98fa3f281"
HOST = "ServerScriptService/EGGRUMBLE_LobbyCastleModesPreview"
HOST_SHA = "8d8f6a63db5dd24740f787437b7aa88edfbaaa9c2aae062b07a884e59c06ad85"
PROJECT = "EGGRUMBLE_REAL69.project.json"
RECEIPT = "REAL69_LEGACY_INTAKE_RECEIPT.json"
PLACE = "EGGRUMBLE_REAL69_PRIVATE.rbxlx"
OFF = "OFF69_ART16_P0_ORIGINAL"
PACKET = "B220_ART16_P0_SELECTED17_NOT_FORMAL"
MARK = "GQ470_ART16_P0_A_CANDIDATE_NOT_FORMAL"
NOTE = "gq470_art16_p0_lobby_composite"
FEATURE = "GQ470_P0_EARLY_EXISTING_LOBBY_SPAWN_REAL69_20261121"

def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def need(ok: bool, reason: str) -> None:
    if not ok:
        raise ValueError("RED_GQ470_ART16_P0_" + reason)

def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))

def selected(root: Path) -> dict[str, tuple[Path, str]]:
    root = root.resolve()
    project = load(root / PROJECT)
    found: dict[str, tuple[Path, str]] = {}
    def visit(node: dict, route: str) -> None:
        need(isinstance(node, dict), "INVALID_PROJECT_NODE")
        if "$path" in node:
            rel = node["$path"]
            need(isinstance(rel, str) and rel and not rel.startswith("/"),
                 "INVALID_SOURCE_PATH")
            path = (root / rel).resolve()
            need(path.is_relative_to(root) and path.is_file() and route not in found,
                 "SOURCE_TRAVERSAL_OR_DUPLICATE")
            kind = ("LocalScript" if rel.endswith(".client.luau") else
                    "Script" if rel.endswith(".server.luau") else "ModuleScript")
            found[route] = (path, kind)
            return
        for key, value in node.items():
            if not key.startswith("$"):
                visit(value, (route + "/" if route else "") + key)
    visit(project["tree"], "")
    need(len(found) == 69, "SOURCE_COUNT_NOT_69")
    return found

def snapshot(root: Path) -> tuple[dict[str, bytes], dict[str, str]]:
    sels = selected(root)
    return ({r: p.read_bytes() for r, (p, _) in sels.items()},
            {r: k for r, (_, k) in sels.items()})

def exact_formal(root: Path) -> tuple[dict, dict[str, bytes], dict[str, str]]:
    rec = load(root / RECEIPT)
    sources, classes = snapshot(root)
    need(rec.get("canonical_build") is True and
         rec.get("build_head") == FORMAL and
         rec.get("official_branch") == "rc/p0d-s1-kids-rc01" and
         rec.get("selected_source_count") == 69 and
         rec.get("source_hashes") == {r: sha(b) for r, b in sources.items()} and
         rec.get("source_classes") == classes, "FORMAL_PROVENANCE")
    place = (root / PLACE).read_bytes()
    need(sha(place) == FORMAL_PLACE_SHA and len(place) == FORMAL_PLACE_BYTES,
         "FORMAL_PLACE_MISMATCH")
    need(sha(sources[HOST]) == HOST_SHA and classes[HOST] == "Script",
         "FORMAL_HOST_LOCK")
    return rec, sources, classes

def author_deltas(formal: Path, art: Path, p0: Path) -> tuple[dict[str, bytes], dict[str, list[str]]]:
    base_rec, original, classes = exact_formal(formal)
    need((art / PROJECT).read_bytes() == (formal / PROJECT).read_bytes() and
         (p0 / PROJECT).read_bytes() == (formal / PROJECT).read_bytes(),
         "AUTHOR_PROJECT_CHANGED")
    art_rec = load(art / RECEIPT)
    art_src, art_class = snapshot(art)
    art_note = art_rec.get("gq470_art16_source_bridge", {})
    art_changed = {r for r in original if original[r] != art_src[r]}
    need(set(art_src) == set(original) and art_class == classes and
         art_rec.get("source_hashes") == {r: sha(b) for r, b in art_src.items()} and
         art_rec.get("source_classes") == classes and
         art_rec.get("canonical_build") is False and
         art_rec.get("build_head") == "ART16_A_SOURCE_BRIDGE_NOT_FORMAL" and
         art_note.get("formal_base_sha") == FORMAL and
         art_note.get("selected_changed") == 16 and
         art_note.get("untouched_original") == 53 and
         art_note.get("owner_accepted") is False and
         art_note.get("officially_integrated") is False and
         art_note.get("art_gate") == "ART_NO_GO" and
         len(art_changed) == 16 and
         HOST not in art_changed and
         sha((art / PLACE).read_bytes()) == ART16_PLACE_SHA,
         "ART16_PARENT_NOT_EXACT")
    # PR980 retains the original formal receipt and changes one selected Host.
    p0_rec = load(p0 / RECEIPT)
    p0_src, p0_class = snapshot(p0)
    changed_p0 = {r for r in original if original[r] != p0_src[r]}
    p0_note = load(p0 / "GQ470_P0_EARLY_LOBBY_CANDIDATE_RECEIPT.json")
    host_text = p0_src[HOST].decode("utf-8")
    need(set(p0_src) == set(original) and p0_class == classes and
         p0_rec == base_rec and changed_p0 == {HOST} and
         p0_note.get("formal_rc_head") == FORMAL and
         p0_note.get("official_host_sha256") == HOST_SHA and
         p0_note.get("new_host_sha256") == sha(p0_src[HOST]) and
         p0_note.get("changed_selected_routes") == [HOST] and
         p0_note.get("unchanged_routes") == 68 and
         p0_note.get("new_script_count") == 0 and
         p0_note.get("new_lobby_world_instances") == 0 and
         p0_note.get("studio_player_visibility_fix_proven") is False and
         p0_note.get("owner_accepted") is False and
         p0_note.get("source_native_rojo") == "PASS_SOURCE_ONLY" and
         p0_note.get("candidate_place_sha256") == P0_PLACE_SHA and
         sha((p0 / PLACE).read_bytes()) == P0_PLACE_SHA and
         host_text.count(FEATURE) == 1 and
         host_text.index("gqEarlySpawn.Parent=gqEarlyFolder") <
         host_text.index("local Rules=require") and
         host_text.count('Instance.new("SpawnLocation")') == 1,
         "P0_PARENT_NOT_EXACT")
    need(art_changed.isdisjoint(changed_p0) and
         len(art_changed | changed_p0) == 17, "ART_P0_SOURCE_COLLISION")
    return ({r: art_src[r] for r in art_changed} | {HOST: p0_src[HOST]},
            {"art16_970": sorted(art_changed), "early_lobby_980": [HOST]})

def composited_delta(original: dict[str, bytes], candidate: dict[str, bytes],
                     authors: dict[str, list[str]]) -> None:
    aa, bb = set(authors["art16_970"]), set(authors["early_lobby_980"])
    need(len(aa) == 16 and bb == {HOST} and aa.isdisjoint(bb),
         "AUTHORS_NOT_DISJOINT_16_PLUS_1")
    need(len(original) == len(candidate) == 69 and set(original) == set(candidate) and
         {r for r in original if original[r] != candidate[r]} == aa | bb and
         len(set(original) - aa - bb) == 52, "17_CHANGED_52_EXACT_REQUIRED")

def compose(formal: Path, art: Path, p0: Path, dest: Path) -> None:
    need(not dest.exists(), "OUTPUT_EXISTS")
    rec, original, classes = exact_formal(formal)
    updates, authors = author_deltas(formal, art, p0)
    shutil.copytree(formal, dest)
    shutil.copytree(formal, dest / OFF)
    sels = selected(dest)
    for route, value in updates.items():
        sels[route][0].write_bytes(value)
    newer, newer_classes = snapshot(dest)
    composited_delta(original, newer, authors)
    need(newer_classes == classes, "CLASS_DRIFT")
    rec = copy.deepcopy(rec)
    rec["canonical_build"] = False
    rec["build_head"] = MARK
    rec["source_hashes"] = {r: sha(b) for r, b in newer.items()}
    rec[NOTE] = {
        "feature_ids": ["GQ470_ART16_966_967_SOURCE_BRIDGE_20261121", FEATURE],
        "formal_head": FORMAL, "art16_pr": 970, "art16_head": ART16_HEAD,
        "art16_run": 44850475985, "p0_pr": 980, "p0_head": P0_HEAD,
        "p0_run": 44862433160, "authors": authors,
        "changed_selected_sources": 17, "unchanged_original_sources": 52,
        "source_count": 69, "new_runtime_sources": 0,
        "formal_adopted": False, "studio": "NOT_TESTED",
        "studio_spawn_fix_proven": False, "android": "NOT_TESTED",
        "screen_shots": "0/32", "human_art": "NOT_TESTED",
        "owner_accepted": False, "art_gate": "ART_NO_GO",
        "product_gate": "PRODUCT_NO_GO", "fun_gate": "FUN_NO_GO",
        "rollback": OFF, "native_rojo": "NOT_TESTED"
    }
    (dest / RECEIPT).write_text(json.dumps(rec, indent=2, sort_keys=True,
                                          ensure_ascii=False) + "\n", encoding="utf-8")
    verify(dest, sealed=False)
    print("ART16_PLUS_P0_REAL69_TRUE_17_CHANGED_52_UNCHANGED_A_PREP")

def verify(root: Path, sealed: bool = True) -> None:
    _, old, classes = exact_formal(root / OFF)
    newer, kinds = snapshot(root)
    rec = load(root / RECEIPT)
    n = rec.get(NOTE, {})
    authors = n.get("authors", {})
    need(set(authors) == {"art16_970", "early_lobby_980"}, "AUTHOR_MAP")
    composited_delta(old, newer, authors)
    need(kinds == classes and
         rec.get("source_classes") == classes and
         rec.get("source_hashes") == {r: sha(b) for r, b in newer.items()} and
         rec.get("canonical_build") is False and
         rec.get("build_head") == MARK and
         n.get("formal_head") == FORMAL and
         n.get("art16_head") == ART16_HEAD and
         n.get("p0_head") == P0_HEAD and
         n.get("changed_selected_sources") == 17 and
         n.get("unchanged_original_sources") == 52 and
         n.get("formal_adopted") is False and
         n.get("studio_spawn_fix_proven") is False and
         n.get("owner_accepted") is False and
         n.get("screen_shots") == "0/32" and
         n.get("art_gate") == "ART_NO_GO" and
         (root / PROJECT).read_bytes() == (root / OFF / PROJECT).read_bytes(),
         "SELECTION_RECEIPT_GATE_DRIFT")
    if sealed:
        place = (root / PLACE).read_bytes()
        need(sha(place) != FORMAL_PLACE_SHA and
             rec.get("private_place_sha256") == sha(place) and
             rec.get("private_place_bytes") == len(place) and
             n.get("native_rojo") == "PASS_SOURCE_ONLY",
             "NO_SEALED_REAL_PRIVATE_PLACE")

def seal(root: Path) -> None:
    verify(root, sealed=False)
    content = (root / PLACE).read_bytes()
    need(len(content) > FORMAL_PLACE_BYTES and
         sha(content) != FORMAL_PLACE_SHA, "NEW_PLACE_NOT_BUILT")
    rec = load(root / RECEIPT)
    rec["private_place_bytes"] = len(content)
    rec["private_place_sha256"] = sha(content)
    rec[NOTE]["native_rojo"] = "PASS_SOURCE_ONLY"
    (root / RECEIPT).write_text(json.dumps(rec, ensure_ascii=False,
                                           indent=2, sort_keys=True) + "\n")
    verify(root)
    print("ART16_P0_REAL69_NATIVE_ROJO_SOURCE_SEALED", len(content), sha(content))

def export(root: Path) -> None:
    verify(root)
    _, original, classes = exact_formal(root / OFF)
    newer, _ = snapshot(root)
    rec = load(root / RECEIPT)
    authors = rec[NOTE]["authors"]
    chosen = set(authors["art16_970"]) | set(authors["early_lobby_980"])
    packet = root / PACKET
    need(not packet.exists(), "PACKET_EXISTS")
    rows = []
    for route in sorted(chosen):
        rel = "selected_sources/" + route + ".luau"
        path = packet / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(newer[route])
        rows.append({"route": route, "class": classes[route], "path": rel,
                     "old_sha256": sha(original[route]),
                     "new_sha256": sha(newer[route]),
                     "source": 980 if route == HOST else 970})
    report = {"schema": "GQ470_ART16_P0_17_ROUTE_B220_SOURCE_ONLY_V1",
              "formal_head": FORMAL, "candidate_private_place_sha256":
              rec["private_place_sha256"], "candidate_private_place_bytes":
              rec["private_place_bytes"], "selected_count": 17,
              "original_untouched": 52, "original_selected_count": 69,
              "source_only": rows, "parent_art16_head": ART16_HEAD,
              "parent_p0_head": P0_HEAD, "formal_adopted": False,
              "requires_writer_220_fresh_nonforce_cas": True,
              "studio": "NOT_TESTED", "android": "NOT_TESTED",
              "art_images": "0/32", "art_gate": "ART_NO_GO",
              "owner_accepted": False}
    (packet / "SOURCE_SELECT_MANIFEST.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    need(len(rows) == 17 and
         all((packet / row["path"]).read_bytes() == newer[row["route"]]
             for row in rows), "B_PACKET_BYTES")
    print("ART16_P0_B220_17_SOURCE_BYTES_READY_A_ONLY_NOT_FORMAL")

def self_test() -> None:
    old = {str(i): b"original" for i in range(68)}
    authors = {"art16_970": [str(i) for i in range(16)],
               "early_lobby_980": [HOST]}
    old[HOST] = b"original"
    new = old.copy()
    for r in authors["art16_970"] + authors["early_lobby_980"]:
        new[r] = b"changed"
    composited_delta(old, new, authors)
    mutations = [
        ({**authors, "art16_970": authors["art16_970"] + [HOST]}, new),
        ({**authors, "art16_970": authors["art16_970"][:-1]}, new),
        (authors, {**new, "unexpected": b"script"}),
        (authors, {**new, "28": b"unauthorized"}),
        (authors, {**new, HOST: b"original"}),
        ({**authors, "early_lobby_980": ["not host"]}, new),
    ]
    for bad_authors, bad_new in mutations:
        try:
            composited_delta(old, bad_new, bad_authors)
        except ValueError:
            continue
        raise AssertionError("UNSAFE_COMPOSITE_MUTANT_ACCEPTED")
    print("ART16_P0_SIX_ROUTE_COLLISION_AUTHORITY_NEGATIVES_PASS")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--formal", type=Path)
    ap.add_argument("--art16", type=Path)
    ap.add_argument("--p0", type=Path)
    ap.add_argument("--out", type=Path)
    ap.add_argument("--seal", type=Path)
    ap.add_argument("--verify", type=Path)
    ap.add_argument("--export", type=Path)
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        self_test()
    elif a.formal and a.art16 and a.p0 and a.out:
        compose(a.formal, a.art16, a.p0, a.out)
    elif a.seal:
        seal(a.seal)
    elif a.verify:
        verify(a.verify)
    elif a.export:
        export(a.export)
    else:
        ap.error("Specify self-test or formal/art16/p0/out or seal/verify/export")
