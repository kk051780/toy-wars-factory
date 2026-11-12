#!/usr/bin/env python3
"""Real Rojo .rbxlx exact-source verifier for the isolated seven-change S1 preview.

Consumes an ACTUAL Rojo-generated XML Place, checks every embedded Script byte
against the fixed complete release tree, and rejects malicious XML mutations.
This is neither Roblox Studio nor multi-client gameplay validation.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

REPO = Path(__file__).resolve().parents[2]
ROOT = REPO / "releases" / "P0D_S1_KIDS_RC01"
SCRIPTS = {"Script", "LocalScript", "ModuleScript"}
OFFICIAL_RC = "1263a03701211a652b99b91d2339575dc8104eff"
PREVIEW_BASE = "09e118c9af3a7f30c2763b956ab80c4056d2a09d"
EXPECTED_BLOBS = {
    "src/server/Game.server.luau": "e684ca79b8f5ed279bcdf033f4118bf77d552abb",
    "src/server/S1CanonicalRoundHost.luau": "1808fa630b13ad2be2dfdac188823957530b9086",
    "src/server/MapBuilder.luau": "94655d019fdf9798fa24a350ebf49f8290465ac0",
    "src/shared/FirstMinuteModel.luau": "d8dda6b1781375612c123f8c83b6f23fe45d09f1",
    "src/client/HUD.client.luau": "b3d3996c40c690e19007a36a847d5b10fc6a1522",
}

class Blocked(ValueError):
    pass

def require(condition, code):
    if not condition:
        raise Blocked(code)

def git_blob(raw: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()

def property_value(item, name):
    props = item.find("Properties")
    if props is None:
        return None
    for child in props:
        if child.get("name") == name:
            return child.text or ""
    return None

def expected_sources():
    project = json.loads((ROOT / "default.project.json").read_text(encoding="utf8"))
    tree = project["tree"]
    require(tree["ServerScriptService"]["TrapRaidersS1"]["$path"] == "src/server",
            "BAD_ROJO_SERVER_MAPPING")
    require(tree["ReplicatedStorage"]["TrapRaidersShared"]["$path"] == "src/shared",
            "BAD_ROJO_SHARED_MAPPING")
    client = tree["StarterPlayer"]["StarterPlayerScripts"]
    require(client["TrapRaidersHUD"]["$path"] == "src/client/HUD.client.luau",
            "BAD_ROJO_HUD_MAPPING")
    require(client["TrapRaidersCoach"]["$path"] == "src/client/FirstMinuteCoach.client.luau",
            "BAD_ROJO_COACH_MAPPING")
    rows = list((ROOT / "src").rglob("*.luau"))
    require(len(rows) == 21, "NOT_EXACTLY_21_SOURCE_SCRIPTS")
    expected = {}
    for file in rows:
        rel = file.relative_to(ROOT).as_posix()
        group = rel.split("/")[1]
        name = file.name
        if group == "server":
            cls = "Script" if name.endswith(".server.luau") else "ModuleScript"
            dest = "ServerScriptService/TrapRaidersS1/" + name.replace(".server.luau", "").replace(".luau", "")
        elif group == "shared":
            cls = "ModuleScript"
            dest = "ReplicatedStorage/TrapRaidersShared/" + name.replace(".luau", "")
        elif group == "client":
            parent = "StarterPlayer/StarterPlayerScripts/"
            mapped = {
                "HUD.client.luau": ("LocalScript", "TrapRaidersHUD"),
                "FirstMinuteCoach.client.luau": ("LocalScript", "TrapRaidersCoach"),
                "S1GoroganStompRing.client.luau": ("LocalScript", "S1GoroganStompRing"),
                "GoroganVisualPolicy.luau": ("ModuleScript", "GoroganVisualPolicy"),
            }
            require(name in mapped, "UNKNOWN_CLIENT_SCRIPT")
            cls, display = mapped[name]
            dest = parent + display
        else:
            raise Blocked("UNKNOWN_SOURCE_DIRECTORY")
        require(dest not in expected, "DUPLICATED_SOURCE_MAPPING")
        raw = file.read_bytes()
        if rel in EXPECTED_BLOBS:
            require(git_blob(raw) == EXPECTED_BLOBS[rel],
                    "SIX_SELECTED_SOURCE_SHA_CHANGED_" + rel)
        expected[dest] = (cls, raw)
    require(len(expected) == 21, "MISSING_EXPECTED_SCRIPT")
    require(sum(v[0] == "Script" for v in expected.values()) == 1, "WRONG_GAME_OWNER_COUNT")
    require(sum(v[0] == "LocalScript" for v in expected.values()) == 3, "WRONG_CLIENT_COUNT")
    require(sum(v[0] == "ModuleScript" for v in expected.values()) == 17, "WRONG_MODULE_COUNT")
    return expected

def parse(xml):
    require(len(xml) >= 8192, "TRUNCATED_PLACE")
    try:
        root = ET.fromstring(xml)
    except ET.ParseError as e:
        raise Blocked("MALFORMED_PLACE_XML") from e
    require(root.tag == "roblox", "NOT_ROBLOX_PLACE")
    records = []
    def visit(node, names=()):
        for item in node:
            if item.tag != "Item":
                continue
            cls = item.get("class")
            name = property_value(item, "Name")
            require(cls is not None and name is not None, "MISSING_INSTANCE_NAME_OR_CLASS")
            path = names if cls == "DataModel" else names + (name,)
            if cls in SCRIPTS:
                records.append(("/".join(path), cls, property_value(item, "Source")))
            visit(item, path)
    visit(root)
    return root, records

def verify_place(xml, expected):
    root, records = parse(xml)
    require(len(records) == 21, "WRONG_SCRIPT_COUNT")
    seen = set()
    for path, cls, content in records:
        require(path in expected and path not in seen, "EXTRA_OR_DUPLICATE_SCRIPT_" + path)
        required_class, required_source = expected[path]
        require(cls == required_class, "BAD_SCRIPT_CLASS_" + path)
        require(content is not None and content.encode("utf8") == required_source,
                "BAD_EMBEDDED_SCRIPT_BYTES_" + path)
        seen.add(path)
    require(seen == set(expected), "MISSING_EXPECTED_SOURCE")
    return root

def named(root, name):
    found = [item for item in root.iter("Item")
             if property_value(item, "Name") == name]
    require(len(found) == 1, "NON_UNIQUE_TARGET_" + name)
    return found[0]

def replace_source(root, name, old, new):
    item = named(root, name)
    props = item.find("Properties")
    field = next((x for x in props if x.get("name") == "Source"), None)
    require(field is not None and old in (field.text or ""),
            "SOURCE_MUTATION_ANCHOR_MISSING_" + name)
    field.text = (field.text or "").replace(old, new, 1)

def adversarial_controls(original, expected):
    def check(name, transform):
        try:
            data = transform()
            verify_place(data, expected)
        except Blocked:
            print("P0D_SEVEN_ROJO_NEGATIVE_REJECTED " + name)
            return
        raise Blocked("ACCEPTED_UNSAFE_XML_MUTATION_" + name)
    def change(fn):
        root = copy.deepcopy(parse(original)[0])
        fn(root)
        return ET.tostring(root, encoding="utf8")
    check("corrupt_xml", lambda: b"<roblox><Item")
    check("game_egg_drop_removed", lambda: change(
        lambda r: replace_source(r, "Game", "dropEgg(player)", "--dropEgg(player)")))
    check("host_guard_removed", lambda: change(
        lambda r: replace_source(r, "S1CanonicalRoundHost",
                                 "if not good or reason ~= nil", "if false then")))
    check("map_japanese_label_corrupted", lambda: change(
        lambda r: replace_source(r, "MapBuilder", "卵", "tampered-eggs")))
    def duplicate_game(r):
        game = named(r, "Game")
        parent = next(p for p in r.iter() if game in p)
        parent.append(copy.deepcopy(game))
    check("duplicate_game_owner", lambda: change(duplicate_game))
    def remove_coach(r):
        item = named(r, "TrapRaidersCoach")
        parent = next(p for p in r.iter() if item in p)
        parent.remove(item)
    check("missing_child_coach", lambda: change(remove_coach))
    check("mobile_hud_left_stick_regression", lambda: change(
        lambda r: replace_source(r, "TrapRaidersHUD",
                                 "UDim2.new(1, -140, 1, -110)",
                                 "UDim2.new(.02, 0, 1, -16)")))
    check("wrong_game_class", lambda: change(
        lambda r: named(r, "Game").set("class", "LocalScript")))
    def leak_game_to_clients(r):
        item = named(r, "Game")
        parent = next(p for p in r.iter() if item in p)
        parent.remove(item)
        named(r, "TrapRaidersShared").append(item)
    check("game_exposed_in_replicated_storage", lambda: change(leak_game_to_clients))
    check("server_snapshot_sequence_erased", lambda: change(
        lambda r: replace_source(r, "Game", "snapshotUpdateId += 1", "-- snapshotUpdateId += 1")))
    check("coach_stale_view_guard_erased", lambda: change(
        lambda r: replace_source(r, "FirstMinuteModel",
                                 "id <= state.lastUpdateId", "id < -1")))
    print("P0D_SEVEN_ROJO_11_OF_11_MUTANTS_REJECTED")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--place", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()
    expected = expected_sources()
    source_game = (ROOT / "src/server/Game.server.luau").read_text(encoding="utf8")
    source_coach = (ROOT / "src/shared/FirstMinuteModel.luau").read_text(encoding="utf8")
    require("snapshotUpdateId += 1" in source_game and "updateId = snapshotUpdateId" in source_game, "NO_SERVER_SNAPSHOT_SEQUENCE")
    require("id <= state.lastUpdateId" in source_coach and "lastUpdateId = id" in source_coach, "NO_COACH_STALE_PACKET_GATE")
    raw = args.place.read_bytes()
    verify_place(raw, expected)
    adversarial_controls(raw, expected)
    game = (ROOT / "src/server/Game.server.luau").read_text(encoding="utf8")
    require("CANONICAL_S1_ENABLED = false" in game
            and "D07_D08_RELEASE_REVIEW_APPROVED = false" in game,
            "UNAUTHORIZED_BOSS_ACTIVATION")
    receipt = {
        "format": "P0D_SEVEN_CHANGE_S1_RBXLX_REVIEW_ONLY_V1",
        "game": "TRAP_RAIDERS",
        "baseline_official_rc": OFFICIAL_RC,
        "base_triple_ux_review": PREVIEW_BASE,
        "source_scripts_verified": 21,
        "server_scripts": 1,
        "local_scripts": 3,
        "module_scripts": 17,
        "rojo_xml_mutations_rejected": 9,
        "place_sha256": hashlib.sha256(raw).hexdigest(),
        "place_bytes": len(raw),
        "studio_tested": False,
        "two_real_clients_tested": False,
        "mobile_tested": False,
        "owner_approved_public_release": False,
        "published": False,
    }
    args.receipt.write_text(
        json.dumps(receipt, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf8")
    print("P0D_SEVEN_ROJO_ACTUAL_21_OF_21_SCRIPT_BYTES_PASS")
    print("P0D_SEVEN_ROJO_PLACE_SHA256=" + receipt["place_sha256"])
    print("P0D_SEVEN_ROJO_PLACE_BYTES=" + str(receipt["place_bytes"]))
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except (Blocked, ValueError, UnicodeError, OSError) as exc:
        print("P0D_SEVEN_ROJO_REJECTED " + str(exc), file=sys.stderr)
        sys.exit(1)
