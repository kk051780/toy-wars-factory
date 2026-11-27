#!/usr/bin/env python3
"""GQ470 ART7: non-overlapping source-only intake of verified PR #931 + #956.

This is NOT a new visual author. It composes seven already-authored selected
REAL69 scripts, preserving all other 62 script bytes and the 69 source classes.
Only #220 may later adopt through authenticated nonforce official-RC CAS.
No Studio, Android, visual-human or OWNER acceptance is inferred from source QA.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import shutil
from pathlib import Path

FORMAL_HEAD = "e80973c354f14a0d0088577f3cc1a875454f0f8f"
FORMAL_PLACE_SHA = "fc63171149a86f6b39779ba6ebe7e18fcb7099fbde98ad2ec33a7cb92b3a9934"
ART6_HEAD = "0d4fa636fc92dec5c90bc18fd674d21c22a7c909"
FIELD_HEAD = "94547fde9d1dce7fe75a8d93028fe16dbbf06dab"
ART6_RUN = 44826816494
FIELD_RUN = 44839348582
PROJECT = "EGGRUMBLE_REAL69.project.json"
RECEIPT = "REAL69_LEGACY_INTAKE_RECEIPT.json"
PLACE = "EGGRUMBLE_REAL69_PRIVATE.rbxlx"
OFF = "OFF69_ART7_ORIGINAL"
PACKET = "B220_ART7_SOURCE_ONLY_NOT_FORMAL"
MANIFEST = "SOURCE_SELECT_MANIFEST.json"
FIELD_ROUTE = "ServerScriptService/EGGRUMBLE_FlagshipFieldArt"
ART6_ROUTES = {
    "ServerScriptService/EGGRUMBLE_BotActors",
    "StarterPlayer/StarterPlayerScripts/EGGRUMBLE_ArtDistanceLOD",
    "ServerScriptService/GQ8_LobbySocialPlaza",
    "ServerScriptService/EGGRUMBLE_ImpactFeedback",
    "ServerScriptService/EGGRUMBLE_NeutralStoneGiant",
    "ServerScriptService/EGGRUMBLE_WeaponSilhouettes",
}
ROUTES = ART6_ROUTES | {FIELD_ROUTE}
ART6_PRS = {924, 926, 925, 928, 930, 929}


def require(value: bool, reason: str) -> None:
    if not value:
        raise ValueError("RED_GQ470_ART7_" + reason)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def find_one(root: Path, filename: str) -> Path:
    hits = [p for p in root.rglob(filename) if p.is_file()]
    require(len(hits) == 1, "ARTIFACT_FILE_COUNT_" + filename)
    return hits[0]


def project_sources(root: Path) -> dict[str, Path]:
    root = root.resolve()
    data = json.loads((root / PROJECT).read_text(encoding="utf-8"))
    found: dict[str, Path] = {}

    def visit(node: dict, route: str = "") -> None:
        require(isinstance(node, dict), "PROJECT_TREE")
        if "$path" in node:
            path = (root / node["$path"]).resolve()
            require(path.is_relative_to(root) and path.is_file(), "ESCAPED_SOURCE")
            require(route not in found, "DUPLICATE_ROUTE")
            found[route] = path
            return
        for name, item in node.items():
            if not name.startswith("$"):
                visit(item, route + ("/" if route else "") + name)

    visit(data["tree"])
    require(len(found) == 69 and ROUTES <= set(found), "REAL69_ROUTE_SET")
    return found


def source_bytes(root: Path) -> dict[str, bytes]:
    return {route: path.read_bytes() for route, path in project_sources(root).items()}


def compare_source_delta(before: dict[str, bytes], after: dict[str, bytes]) -> None:
    require(len(before) == len(after) == 69, "SCRIPT_COUNT_69")
    require(set(before) == set(after), "SCRIPT_ROUTE_SET")
    actual = {route for route in before if before[route] != after[route]}
    require(actual == ROUTES, "EXACT_SEVEN_CHANGED")
    require(len(set(before) - actual) == 62, "SIXTY_TWO_EXACT")


def original(root: Path) -> tuple[dict, dict[str, bytes]]:
    receipt = json.loads((root / RECEIPT).read_text(encoding="utf-8"))
    before = source_bytes(root)
    require(receipt.get("canonical_build") is True and
            receipt.get("official_branch") == "rc/p0d-s1-kids-rc01" and
            receipt.get("build_head") == FORMAL_HEAD, "PINNED_FORMAL_RECEIPT")
    require(receipt.get("selected_source_count") == 69 and
            set(receipt.get("source_hashes", {})) == set(before) and
            set(receipt.get("source_classes", {})) == set(before),
            "PINNED_69_RECEIPT")
    require(all(receipt["source_hashes"][route] == sha(raw)
                for route, raw in before.items()), "PINNED_SOURCE_HASHES")
    place = (root / PLACE).read_bytes()
    require(len(place) == 798390 and sha(place) == FORMAL_PLACE_SHA,
            "PINNED_REAL_PLACE")
    return receipt, before


def load_art6_packet(root: Path) -> list[dict]:
    path = find_one(root, "B220_ART6_SOURCE_ONLY_NOT_FORMAL.json")
    data = json.loads(path.read_text(encoding="utf-8"))
    require(data.get("schema") == "GQ470_ART6_B220_SOURCE_SELECT_V1" and
            data.get("official_parent") == FORMAL_HEAD and
            data.get("official_branch") == "rc/p0d-s1-kids-rc01" and
            data.get("candidate_only") is True and
            data.get("formal_rc_modified") is False and
            data.get("selected_source_count") == 69 and
            data.get("changed_selected_routes") == 6 and
            data.get("unchanged_selected_routes") == 63 and
            data.get("art_gate") == "NO_GO" and
            data.get("owner_accepted") is False,
            "ART6_PARENT_NOT_AUTHENTIC")
    rows = data.get("source_only")
    require(isinstance(rows, list) and len(rows) == 6 and
            {row["pr"] for row in rows} == ART6_PRS and
            {row["selected_route"] for row in rows} == ART6_ROUTES and
            all(row["pinned_author_head"] and len(row["pinned_author_head"]) == 40
                for row in rows),
            "ART6_PARENT_SCOPE")
    out = []
    for row in rows:
        relative = Path(row["artifact_path"])
        require(not relative.is_absolute() and ".." not in relative.parts and
                relative.parts[0] == "selected_sources", "ART6_PATH_TRAVERSAL")
        path_source = (path.parent / relative).resolve()
        require(path_source.is_relative_to(path.parent.resolve()) and
                path_source.is_file(), "ART6_MISSING_SELECTED_SOURCE")
        raw = path_source.read_bytes()
        require(sha(raw) == row["candidate_sha256"] and
                len(raw) == row["source_bytes"], "ART6_SOURCE_HASH")
        out.append({"route": row["selected_route"], "class": row["source_class"],
                    "before": row["original_sha256"], "after": sha(raw),
                    "source": raw, "parent_pr": row["pr"]})
    return out


def load_field_packet(root: Path) -> list[dict]:
    path = find_one(root, "SOURCE_SELECT_MANIFEST.json")
    data = json.loads(path.read_text(encoding="utf-8"))
    require(data.get("schema") == "B220_FIELDART_916_934_NONAUTHORITATIVE_PREP_V1" and
            data.get("formal_branch") == "rc/p0d-s1-kids-rc01" and
            data.get("formal_base_sha") == FORMAL_HEAD and
            data.get("source_profile") == "REAL69_PRIVATE_COMPANION" and
            data.get("source_route") == FIELD_ROUTE and
            data.get("source_class") == "Script" and
            data.get("original_author_commit_shas") ==
            ["e121c11728de6784a2cfddf11beea08f677ae1ae",
             "89bd47dbff105bbcfe1005fdbaaca7cf737cc33c"] and
            data.get("officially_integrated") is False and
            data.get("source_only") is True and
            data.get("art_gate") == "ART_NO_GO" and
            data.get("studio_android_fun") == "NOT_TESTED",
            "FIELD_PARENT_NOT_AUTHENTIC")
    source_file = path.parent / "EGGRUMBLE_FlagshipFieldArt.server.luau"
    require(source_file.is_file(), "FIELD_SELECTED_SOURCE_MISSING")
    raw = source_file.read_bytes()
    require(sha(raw) == data["composed_sha256"], "FIELD_SOURCE_HASH")
    return [{"route": FIELD_ROUTE, "class": "Script",
             "before": data["original_sha256"], "after": sha(raw),
             "source": raw, "parent_pr": 956}]


def check_payloads(receipt: dict, before: dict[str, bytes],
                   payloads: list[dict]) -> None:
    require(len(payloads) == 7 and
            {p["route"] for p in payloads} == ROUTES, "PARENT_DISJOINT_ROUTES")
    for row in payloads:
        route = row["route"]
        require(receipt["source_classes"][route] == row["class"],
                "ORIGINAL_CLASS_" + route)
        require(sha(before[route]) == row["before"], "ORIGINAL_HASH_" + route)
        require(sha(row["source"]) == row["after"] and
                row["before"] != row["after"], "CANDIDATE_BYTES_" + route)
    require({row["parent_pr"] for row in payloads} ==
            ART6_PRS | {956}, "NO_NEW_AUTHOR")


def create(formal: Path, art6: Path, field: Path, target: Path) -> None:
    require(not target.exists(), "TARGET_MUST_BE_NEW")
    formal_receipt, before = original(formal)
    payloads = load_art6_packet(art6) + load_field_packet(field)
    check_payloads(formal_receipt, before, payloads)
    shutil.copytree(formal, target)
    shutil.copytree(formal, target / OFF)
    selected = project_sources(target)
    for row in payloads:
        selected[row["route"]].write_bytes(row["source"])
    after = source_bytes(target)
    compare_source_delta(before, after)
    receipt = copy.deepcopy(formal_receipt)
    receipt["source_hashes"] = {route: sha(raw) for route, raw in after.items()}
    receipt["canonical_build"] = False
    receipt["build_head"] = "A_PREP_ART7_NOT_OFFICIAL"
    receipt["gq470_art7_intake"] = {
        "feature_id": "GQ470_FB015_ART7_931_956_NONLOSS_SOURCE_COMPOSITE_20261121",
        "formal_base_sha": FORMAL_HEAD,
        "parent_art6_pr": 931, "parent_art6_head": ART6_HEAD,
        "parent_art6_successful_run": ART6_RUN,
        "parent_field_pr": 956, "parent_field_head": FIELD_HEAD,
        "parent_field_successful_run": FIELD_RUN,
        "selected_source_count": 69, "changed_selected_routes": 7,
        "unchanged_selected_routes": 62,
        "new_runtime_scripts": 0, "new_game_remote_store_score_authority": False,
        "source_only": True, "officially_integrated": False,
        "rollback": "OFF69_ART7_ORIGINAL exact source and official Place",
        "native69": "NOT_TESTED", "rojo69": "NOT_TESTED",
        "studio_solo": "NOT_TESTED", "studio_2client": "NOT_TESTED",
        "android15min": "NOT_TESTED", "first3min_fun": "NOT_TESTED",
        "art_old_new_screenshots": "0/32",
        "art_gate": "ART_NO_GO", "product_gate": "PRODUCT_NO_GO",
        "owner_accepted": False
    }
    (target / RECEIPT).write_text(
        json.dumps(receipt, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8")
    # The original Place is still at target/PLACE. Rojo must overwrite it.
    inspect(target, require_built=False)
    print("ART7_A_PREP_7_CHANGED_62_EXACT_SOURCE_ONLY")


def inspect(target: Path, require_built: bool = True) -> tuple[dict, dict[str, bytes], dict[str, bytes]]:
    formal_receipt, before = original(target / OFF)
    after = source_bytes(target)
    compare_source_delta(before, after)
    receipt = json.loads((target / RECEIPT).read_text(encoding="utf-8"))
    info = receipt.get("gq470_art7_intake", {})
    require(receipt.get("canonical_build") is False and
            receipt.get("build_head") == "A_PREP_ART7_NOT_OFFICIAL" and
            receipt.get("source_classes") == formal_receipt["source_classes"] and
            receipt.get("source_hashes") ==
            {r: sha(raw) for r, raw in after.items()}, "SOURCE_RECEIPT_DRIFT")
    require(info.get("formal_base_sha") == FORMAL_HEAD and
            info.get("parent_art6_head") == ART6_HEAD and
            info.get("parent_field_head") == FIELD_HEAD and
            info.get("parent_art6_successful_run") == ART6_RUN and
            info.get("parent_field_successful_run") == FIELD_RUN and
            info.get("changed_selected_routes") == 7 and
            info.get("unchanged_selected_routes") == 62 and
            info.get("new_runtime_scripts") == 0 and
            info.get("new_game_remote_store_score_authority") is False and
            info.get("officially_integrated") is False and
            info.get("art_gate") == "ART_NO_GO" and
            info.get("product_gate") == "PRODUCT_NO_GO" and
            info.get("art_old_new_screenshots") == "0/32" and
            info.get("owner_accepted") is False,
            "FAKE_BUNDLE_OR_ART_GO")
    require((target / PROJECT).read_bytes() ==
            (target / OFF / PROJECT).read_bytes(), "PROJECT_DRIFT")
    require((target / OFF / PLACE).read_bytes() and
            sha((target / OFF / PLACE).read_bytes()) == FORMAL_PLACE_SHA,
            "OFF69_INVERSE_PLACE")
    if require_built:
        place = (target / PLACE).read_bytes()
        require(sha(place) != FORMAL_PLACE_SHA and
                receipt.get("private_place_bytes") == len(place) and
                receipt.get("private_place_sha256") == sha(place) and
                info.get("native69") == "PASS_SOURCE_ONLY" and
                info.get("rojo69") == "PASS_SOURCE_ONLY",
                "UNSEALED_SOURCE_ONLY_PLACE")
    return receipt, before, after


def seal(target: Path) -> None:
    receipt, before, after = inspect(target, require_built=False)
    place = (target / PLACE).read_bytes()
    require(sha(place) != FORMAL_PLACE_SHA and len(place) > 0,
            "CANDIDATE_PLACE_UNBUILT")
    receipt["private_place_bytes"] = len(place)
    receipt["private_place_sha256"] = sha(place)
    receipt["gq470_art7_intake"]["native69"] = "PASS_SOURCE_ONLY"
    receipt["gq470_art7_intake"]["rojo69"] = "PASS_SOURCE_ONLY"
    (target / RECEIPT).write_text(
        json.dumps(receipt, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8")
    inspect(target)
    print("ART7_REAL_PLACE_SEALED_SOURCE_ONLY_NO_ART_GO", len(place))


def export_b(target: Path) -> None:
    receipt, before, after = inspect(target)
    packet_dir = target / PACKET
    require(not packet_dir.exists(), "NO_OVERWRITE_B_PACKET")
    packet_dir.mkdir()
    rows = []
    for route in sorted(ROUTES):
        source_class = receipt["source_classes"][route]
        path = "selected_sources/" + route + ".luau"
        outfile = packet_dir / path
        outfile.parent.mkdir(parents=True, exist_ok=True)
        outfile.write_bytes(after[route])
        rows.append({
            "selected_route": route, "source_class": source_class,
            "source_path": path, "original_sha256": sha(before[route]),
            "candidate_sha256": sha(after[route]),
            "source_bytes": len(after[route])
        })
    manifest = {
        "schema": "GQ470_ART7_B220_SOURCE_SELECT_V1",
        "official_branch": "rc/p0d-s1-kids-rc01",
        "official_base_sha": FORMAL_HEAD,
        "source_profile": "REAL69_PRIVATE_COMPANION",
        "source_selected_count": 69,
        "changed_source_count": 7, "unchanged_source_count": 62,
        "pinned_parent_prs": [931, 956],
        "pinned_parent_heads": [ART6_HEAD, FIELD_HEAD],
        "authenticated_b220_fresh_nonforce_cas_required": True,
        "candidate_only": True, "formal_rc_modified": False,
        "source_only": rows,
        "art_gate": "ART_NO_GO", "studio_android_fun": "NOT_TESTED",
        "owner_accepted": False
    }
    (packet_dir / MANIFEST).write_text(
        json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8")
    verify_packet(target)
    print("ART7_B220_SEVEN_SELECTED_SOURCE_BYTES_PACKET_PASS")


def verify_packet(target: Path) -> None:
    _, before, after = inspect(target)
    root = target / PACKET
    m = json.loads((root / MANIFEST).read_text(encoding="utf-8"))
    require(m["schema"] == "GQ470_ART7_B220_SOURCE_SELECT_V1" and
            m["official_base_sha"] == FORMAL_HEAD and
            m["source_profile"] == "REAL69_PRIVATE_COMPANION" and
            m["changed_source_count"] == 7 and
            m["unchanged_source_count"] == 62 and
            m["pinned_parent_heads"] == [ART6_HEAD, FIELD_HEAD] and
            m["formal_rc_modified"] is False and
            m["candidate_only"] is True and
            m["owner_accepted"] is False and
            m["art_gate"] == "ART_NO_GO", "B_PACKET_METADATA")
    rows = m["source_only"]
    require(len(rows) == 7 and
            {x["selected_route"] for x in rows} == ROUTES, "B_PACKET_ROUTE_SET")
    found = {p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file()}
    require(found == {MANIFEST} | {x["source_path"] for x in rows},
            "B_PACKET_FILE_SET")
    for row in rows:
        f = (root / row["source_path"]).resolve()
        require(f.is_relative_to(root.resolve()) and f.is_file(), "B_PACKET_PATH")
        raw = f.read_bytes()
        route = row["selected_route"]
        require(raw == after[route] and sha(raw) == row["candidate_sha256"] and
                len(raw) == row["source_bytes"] and
                sha(before[route]) == row["original_sha256"],
                "B_PACKET_BYTES_" + route)


def self_test() -> None:
    original_map = {r: b"original" for r in ROUTES}
    original_map.update({"UNCHANGED_" + str(i): b"untouched" for i in range(62)})
    candidate = dict(original_map)
    for route in ROUTES:
        candidate[route] = b"changed"
    compare_source_delta(original_map, candidate)
    negatives = [
        (dict(original_map), "zero changes"),
        ({**candidate, "UNCHANGED_0": b"tampered"}, "unowned change"),
        ({k: v for k, v in candidate.items() if k != "UNCHANGED_0"}, "missing source"),
        ({**candidate, FIELD_ROUTE: b"original"}, "missing field"),
        ({**candidate, next(iter(ART6_ROUTES)): b"original"}, "missing six"),
    ]
    count = 0
    for bad, name in negatives:
        try:
            compare_source_delta(original_map, bad)
        except ValueError:
            count += 1
        else:
            raise AssertionError("RED_MUTANT_SURVIVED_" + name)
    fake = [{"route": r, "class": "Script", "before": sha(b"original"),
             "after": sha(b"changed"), "source": b"changed",
             "parent_pr": (956 if r == FIELD_ROUTE else
                           sorted(ART6_PRS)[list(sorted(ART6_ROUTES)).index(r)])}
            for r in sorted(ROUTES)]
    receipt = {"source_classes": {r: "Script" for r in original_map}}
    check_payloads(receipt, original_map, fake)
    for invalid in (
        fake[:-1],
        fake[:-1] + [fake[0]],
        fake[:-1] + [{**fake[-1], "source": b"malicious"}],
        fake[:-1] + [{**fake[-1], "class": "LocalScript"}],
    ):
        try:
            check_payloads(receipt, original_map, invalid)
        except ValueError:
            count += 1
        else:
            raise AssertionError("RED_FORGED_PACKET_ACCEPTED")
    print("ART7_STATIC_9_FAIL_CLOSED_MUTATIONS_PASS", count)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--formal", type=Path)
    p.add_argument("--art6", type=Path)
    p.add_argument("--field", type=Path)
    p.add_argument("--out", type=Path)
    p.add_argument("--verify", type=Path)
    p.add_argument("--seal", type=Path)
    p.add_argument("--export-b", type=Path)
    p.add_argument("--verify-b", type=Path)
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args()
    if a.self_test:
        self_test()
    elif a.verify:
        inspect(a.verify)
    elif a.seal:
        seal(a.seal)
    elif a.export_b:
        export_b(a.export_b)
    elif a.verify_b:
        verify_packet(a.verify_b)
    else:
        require(a.formal is not None and a.art6 is not None and
                a.field is not None and a.out is not None, "MISSING_ARGUMENTS")
        create(a.formal, a.art6, a.field, a.out)
