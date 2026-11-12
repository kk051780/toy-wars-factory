# P0-D S1 V6 triple-source review only; no Studio, live, mobile verification.
#!/usr/bin/env python3
"""Original V6 + two verified child-facing UX sources, genuine Rojo XML QA.

Review-only. Every 21-source byte is pinned; only MapBuilder and
FirstMinuteModel substitute existing independent vetted source blobs.
No Roblox Studio, device, actual multiplayer, publishing or release PASS.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parents[1]
ROOT = HERE.parents[1] / "releases/P0D_S1_KIDS_RC01"
LOCK = HERE / "SELECTION_LOCK.json"
RC_ROOT = "releases/P0D_S1_KIDS_RC01/"
ORIGINAL = "1263a03701211a652b99b91d2339575dc8104eff"
MAP_INPUT = "78f849af28e15d7e990dd2690f2cafff0854d001"
HELP_INPUT = "e29d37737890671d458072bebe729127878700f6"
MAP_FILE = "src/server/MapBuilder.luau"
HELP_FILE = "src/shared/FirstMinuteModel.luau"
HUD_FILE = "src/client/HUD.client.luau"
HUD_INPUT = "10940c76d708f99be908c587094c00757b22e7f6"
OVERRIDES = {
    MAP_FILE: (
        MAP_INPUT,
        "handoffs/P0D-S1-JP-MAP-SIGNS-20261112-01/candidate/src/server/MapBuilder.luau",
        "94655d019fdf9798fa24a350ebf49f8290465ac0",
    ),
    HELP_FILE: (
        HELP_INPUT,
        "handoffs/P0D-S1-GUARDIAN-TRAP-FTUE-COPY-20261112-01/candidate/src/shared/FirstMinuteModel.luau",
        "967ea52df79884e6c73e3e0952d5a97de0d1796e",
    ),
    HUD_FILE: (
        HUD_INPUT,
        "handoffs/P0D-S1-V6-MOBILE-GUARDIAN-HUD-SAFE-20261112-01/candidate/src/client/HUD.client.luau",
        "b3d3996c40c690e19007a36a847d5b10fc6a1522",
    ),
}
SCRIPT_TYPES = {"Script", "LocalScript", "ModuleScript"}

class Blocked(ValueError):
    pass

def insist(ok, msg):
    if not ok:
        raise Blocked(msg)

def gitblob(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()

def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def exact_git(repo, commit, path, sha, expected_bytes):
    p = subprocess.run(["git", "-C", str(repo), "show", commit + ":" + path],
                       capture_output=True, check=False, timeout=35)
    insist(p.returncode == 0, "FIXED_ORIGIN_FILE_UNREADABLE_" + path)
    insist(gitblob(p.stdout) == sha, "FIXED_GIT_BLOB_CHANGED_" + path)
    if expected_bytes is not None:
        insist(len(p.stdout) == expected_bytes, "FIXED_GIT_BYTES_CHANGED_" + path)
    return p.stdout

def load_lock():
    lock = json.loads(LOCK.read_text(encoding="utf8"))
    insist(set(lock) == {
        "format", "game_id", "work_id", "packet_id", "public_source_allowed",
        "official_rc_base", "japanese_map_input_commit",
        "guardian_help_input_commit", "mobile_guardian_hud_input_commit", "source_count", "studio_tested",
        "roblox_published", "files"
    }, "SELECTION_LOCK_SCHEMA")
    insist(lock["format"] == "P0D_PUBLIC_SOURCE_V1"
           and lock["public_source_allowed"] is True
           and lock["game_id"] == "TRAP_RAIDERS"
           and lock["work_id"] == "p0d-siege-v19"
           and lock["packet_id"] == "P0D-S1-V6-TRIPLE-CHILD-UX-20261112-03"
           and lock["official_rc_base"] == ORIGINAL
           and lock["japanese_map_input_commit"] == MAP_INPUT
           and lock["guardian_help_input_commit"] == HELP_INPUT
           and lock["mobile_guardian_hud_input_commit"] == HUD_INPUT
           and lock["studio_tested"] is False
           and lock["roblox_published"] is False
           and lock["source_count"] == 21, "SOURCE_LOCK_WRONG_PROVENANCE_OR_STATUS")
    rows = lock["files"]
    insist(type(rows) is list and len(rows) == 22, "SOURCE_LOCK_WRONG_FILE_COUNT")
    seen = set()
    selected = {}
    changes = []
    for row in rows:
        insist(type(row) is dict and set(row) == {
            "path", "git_blob", "bytes", "original_git_blob"
        }, "SOURCE_LOCK_ENTRY_SCHEMA")
        p = row["path"]
        insist(isinstance(p, str) and p not in seen
               and (p == "default.project.json"
                    or re.fullmatch(r"src/(shared|server|client)/[A-Za-z0-9_\.]+\.luau", p)),
               "UNAUTHORIZED_SOURCE_PATH")
        seen.add(p)
        insist(type(row["bytes"]) is int and row["bytes"] > 20
               and isinstance(row["git_blob"], str)
               and re.fullmatch(r"[a-f0-9]{40}", row["git_blob"])
               and isinstance(row["original_git_blob"], str)
               and re.fullmatch(r"[a-f0-9]{40}", row["original_git_blob"]),
               "SOURCE_LOCK_BAD_SHA_OR_LENGTH")
        f = ROOT / p
        insist(f.is_file() and not f.is_symlink(), "SOURCE_SNAPSHOT_MISSING_" + p)
        raw = f.read_bytes()
        insist(len(raw) == row["bytes"] and gitblob(raw) == row["git_blob"],
               "SOURCE_SNAPSHOT_BYTES_DIFFER_" + p)
        insist(gitblob(exact_git(
            LOCK_REPO, ORIGINAL, RC_ROOT + p, row["original_git_blob"], None
        )) == row["original_git_blob"], "RC_ORIGINAL_PIN_INVALID_" + p)
        if p in OVERRIDES:
            commit, origin, exact = OVERRIDES[p]
            insist(row["git_blob"] == exact
                   and row["original_git_blob"] != row["git_blob"],
                   "EXPECTED_CHILD_UX_SOURCE_NOT_SELECTED_" + p)
            independently_vetted = exact_git(
                LOCK_REPO, commit, origin, exact, row["bytes"]
            )
            insist(raw == independently_vetted,
                   "TRIPLE_SOURCE_DIFFERS_FROM_ITS_PREVIOUS_QA_" + p)
            changes.append(p)
        else:
            insist(row["git_blob"] == row["original_git_blob"],
                   "UNAUTHORIZED_THIRD_SOURCE_MODIFICATION_" + p)
        selected[p] = raw
    insist(set(changes) == {MAP_FILE, HELP_FILE, HUD_FILE},
           "NOT_EXACTLY_THREE_CHILD_UI_PATCHES")
    insist(sum(p.endswith(".luau") for p in seen) == 21,
           "NOT_EXACTLY_21_GAME_SOURCES")
    disk = {
        x.relative_to(ROOT).as_posix() for x in ROOT.rglob("*")
        if x.is_file() and (x.relative_to(ROOT).as_posix().startswith("src/")
                            or x.relative_to(ROOT).as_posix()=="default.project.json")
    }
    insist(disk == seen, "EXTRA_OR_MISSING_PREVIEW_SOURCE")
    manifest = json.loads((ROOT/"BUILD_MANIFEST.json").read_text(encoding="utf8"))
    insist(manifest.get("format") == "P0D_PUBLIC_SOURCE_V1"
           and len(manifest.get("files", [])) == 37, "PREVIEW_MANIFEST_SCHEMA")
    for f in manifest["files"]:
        p = ROOT / f["path"]
        insist(p.is_file() and not p.is_symlink()
               and len(p.read_bytes()) == f["size"]
               and sha256(p.read_bytes()) == f["sha256"],
               "PREVIEW_MANIFEST_SHA256_FAIL_" + f["path"])
    print("P0D_V6_TRIPLE_FULL_MANIFEST_SHA256_PASS files=37/37")
    project = json.loads(selected["default.project.json"])
    insist(project["name"].startswith("TRAP_RAIDERS_S1")
           and project["tree"]["ServerScriptService"]["TrapRaidersS1"]["$path"] ==
           "src/server", "PROJECT_SOURCE_MAPPING_CHANGED")
    server = selected["src/server/Game.server.luau"].decode("utf8")
    trap = selected["src/server/S1TrapRules.luau"].decode("utf8")
    hud = selected["src/client/HUD.client.luau"].decode("utf8")
    maptext = selected[MAP_FILE].decode("utf8")
    coachtext = selected[HELP_FILE].decode("utf8")
    for v in ('data.action == "PLACE_TRAP"', 'trapCooldown = math.max(',
              'TrapRules.shouldTrigger('):
        insist(v in server, "REAL_GUARDIAN_TRAP_SERVER_MISSING_" + v)
    for v in ('TrapRules.COOLDOWN = 20', 'TrapRules.SLOW_SECONDS = 3'):
        insist(v in trap, "TRAP_RULES_SOURCE_MISSING_" + v)
    for v in ('"GuardianTrap"', 'action("PLACE_TRAP", nil)', 'Enum.KeyCode.T',
              'UDim2.new(1, -140, 1, -110)'):
        insist(v in hud, "GUARDIAN_MOBILE_BUTTON_SOURCE_MISSING_" + v)
    for v in ('"卵を取る"', '"卵を届ける"', '"卵はここへ！"'):
        insist(v in maptext, "JAPANESE_OBJECTIVE_SIGN_MISSING_" + v)
    for v in ('"守護：罠を置こう！"', '"守護：仲間を守ろう！"', "20秒たてば次の罠"):
        insist(v in coachtext, "GUARDIAN_FIRST_MINUTE_COPY_MISSING_" + v)
    print("P0D_V6_TRIPLE_SOURCE_SELECT_PASS exact21/21 unchanged18 and selected3")
    print("P0D_V6_TRIPLE_TRAP_INTEGRITY_PASS unchanged_real_server_rules")
    return selected

def expected_script_paths(sources):
    expected = {}
    for f, raw in sources.items():
        if not f.endswith(".luau"):
            continue
        section, name = f.split("/")[1], f.rsplit("/", 1)[1]
        if section == "server":
            cls = "Script" if name.endswith(".server.luau") else "ModuleScript"
            dest = "ServerScriptService/TrapRaidersS1/" + name.replace(
                ".server.luau", "").replace(".luau", "")
        elif section == "shared":
            cls = "ModuleScript"
            dest = "ReplicatedStorage/TrapRaidersShared/" + name.replace(".luau", "")
        elif section == "client":
            path = "StarterPlayer/StarterPlayerScripts/"
            if name == "HUD.client.luau":
                cls, dest = "LocalScript", path + "TrapRaidersHUD"
            elif name == "FirstMinuteCoach.client.luau":
                cls, dest = "LocalScript", path + "TrapRaidersCoach"
            elif name == "S1GoroganStompRing.client.luau":
                cls, dest = "LocalScript", path + "S1GoroganStompRing"
            else:
                cls, dest = "ModuleScript", path + name.replace(".luau", "")
        else:
            raise Blocked("UNRECOGNIZED_SOURCE_GROUP")
        insist(dest not in expected, "DUPLICATE_SCRIPT_MAPPING")
        expected[dest] = (cls, raw)
    insist(len(expected) == 21
           and sum(v[0] == "Script" for v in expected.values()) == 1
           and sum(v[0] == "LocalScript" for v in expected.values()) == 3
           and sum(v[0] == "ModuleScript" for v in expected.values()) == 17,
           "EXPECTED_GAME_INSTANCE_TOPOLOGY_ERROR")
    return expected

def property_value(item, prop):
    props = item.find("Properties")
    if props is None:
        return None
    for x in props:
        if x.get("name") == prop:
            return x.text or ""
    return None

def extract_place(xml):
    try:
        root = ET.fromstring(xml)
    except ET.ParseError as ex:
        raise Blocked("BAD_ROJO_RBXLX_XML") from ex
    insist(root.tag == "roblox", "NOT_ROBLOX_RBXLX")
    records = []
    def walk(parent, names=()):
        for child in parent:
            if child.tag != "Item":
                continue
            cls, name = child.get("class"), property_value(child, "Name")
            insist(cls and name, "MALFORMED_INSTANCE")
            path = names if cls == "DataModel" else names + (name,)
            if cls in SCRIPT_TYPES:
                records.append(("/".join(path), cls,
                                property_value(child, "Source")))
            walk(child, path)
    walk(root)
    return root, records

def verify_actual_place(xml, expected):
    insist(len(xml) > 8192, "EMPTY_ROJO_PLACE")
    root, records = extract_place(xml)
    insist(len(records) == 21, "UNEXPECTED_ROJO_SCRIPT_COUNT_" + str(len(records)))
    seen = set()
    for name, cls, content in records:
        insist(name in expected and name not in seen,
               "UNAUTHORIZED_OR_DUPLICATE_ROJO_SCRIPT_" + name)
        expected_cls, expect_raw = expected[name]
        insist(cls == expected_cls, "ROJO_SCRIPT_WRONG_CLASS_" + name)
        insist(content is not None and content.encode("utf8") == expect_raw,
               "ROJO_EMBEDDED_SCRIPT_BYTES_DIFFER_" + name)
        seen.add(name)
    insist(seen == set(expected), "ROJO_SCRIPT_MISSING")
    insist(sum(c == "Script" for _, c, _ in records) == 1
           and sum(c == "LocalScript" for _, c, _ in records) == 3
           and sum(c == "ModuleScript" for _, c, _ in records) == 17,
           "ROJO_AUTHORITY_OR_CLIENT_COUNT_CHANGED")
    return root

def find_named(root, name):
    found = [x for x in root.iter("Item") if property_value(x, "Name") == name]
    insist(len(found) == 1, "SOURCE_TARGET_NOT_UNIQUE_" + name)
    return found[0]

def verify_negative_controls(xml, expected):
    def fail_case(tag, callback, check=True):
        try:
            payload = callback()
            verify_actual_place(payload, expected)
        except Blocked:
            print("P0D_V6_TRIPLE_XML_NEGATIVE_REJECTED_" + tag)
            return
        raise Blocked("DANGEROUS_XML_MUTATION_ACCEPTED_" + tag)
    def mutate(fn):
        root = copy.deepcopy(extract_place(xml)[0])
        fn(root)
        return ET.tostring(root, encoding="utf8")
    fail_case("malformed_xml", lambda: b"<roblox><Item")
    def corrupt_map(root):
        x = find_named(root, "MapBuilder")
        props = x.find("Properties")
        field = next(c for c in props if c.get("name") == "Source")
        field.text = (field.text or "") + "\n-- changed collision"
    fail_case("changed_selected_map_source", lambda: mutate(corrupt_map))
    def corrupt_model(root):
        x = find_named(root, "FirstMinuteModel")
        props = x.find("Properties")
        field = next(c for c in props if c.get("name") == "Source")
        field.text = (field.text or "").replace("20秒", "5秒")
    fail_case("wrong_guardian_cooldown", lambda: mutate(corrupt_model))
    def duplicate_game(root):
        x = find_named(root, "Game")
        parent = {c: p for p in root.iter() for c in p}[x]
        parent.append(copy.deepcopy(x))
    fail_case("duplicate_server_game", lambda: mutate(duplicate_game))
    def remove_coach(root):
        x = find_named(root, "TrapRaidersCoach")
        parent = {c: p for p in root.iter() for c in p}[x]
        parent.remove(x)
    fail_case("removed_first_minute_client", lambda: mutate(remove_coach))
    def remove_trap(root):
        x = find_named(root, "S1TrapRules")
        parent = {c: p for p in root.iter() for c in p}[x]
        parent.remove(x)
    fail_case("removed_guardian_trap_rules", lambda: mutate(remove_trap))
    def change_hud_class(root):
        find_named(root, "TrapRaidersHUD").attrib["class"] = "ModuleScript"
    fail_case("removed_touch_client_script_class", lambda: mutate(change_hud_class))
    def move_game(root):
        x = find_named(root, "Game")
        old = {c: p for p in root.iter() for c in p}[x]
        old.remove(x)
        find_named(root, "TrapRaidersShared").append(x)
    fail_case("server_game_moved_to_client_visible", lambda: mutate(move_game))
    def revert_mobile_button(root):
        x = find_named(root, "TrapRaidersHUD")
        props = x.find("Properties")
        field = next(c for c in props if c.get("name") == "Source")
        field.text = (field.text or "").replace(
            "UDim2.new(1, -140, 1, -110)", "UDim2.new(.02, 0, 1, -16)")
    fail_case("guardian_mobile_button_reverted", lambda: mutate(revert_mobile_button))
    print("P0D_V6_TRIPLE_XML_NEGATIVE_CONTROLS=9/9")

def main():
    global LOCK_REPO
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    parser.add_argument("--place", required=True)
    parser.add_argument("--receipt", required=True)
    args = parser.parse_args()
    LOCK_REPO = args.repo
    exact_sources = load_lock()
    path = Path(args.place)
    insist(path.is_file() and not path.is_symlink(), "PLACE_NOT_FOUND")
    data = path.read_bytes()
    expected = expected_script_paths(exact_sources)
    verify_actual_place(data, expected)
    print("P0D_V6_TRIPLE_REAL_ROJO_RBXLX_SOURCE_BYTES_PASS scripts=21/21")
    print("P0D_V6_TRIPLE_ROJO_SINGLE_AUTHORITY_3_CLIENTS_17_MODULES_PASS")
    verify_negative_controls(data, expected)
    receipt = {
        "format": "P0D_V6_TRIPLE_CHILD_UX_REVIEW_ONLY_V1",
        "game_id": "TRAP_RAIDERS",
        "original_rc_source_commit": ORIGINAL,
        "selected_ux_source_commits": [MAP_INPUT, HELP_INPUT, HUD_INPUT],
        "rojo_version": "7.7.1",
        "rojo_linux_zip_sha256": "00feb4fa0829a1dd72b49df2639da519a352bfe13cadcd83969e2ba2bb5693c4",
        "source_count": 21,
        "unaltered_original_source_count": 18,
        "approved_child_ux_source_override_count": 3,
        "source_bytes_verified": True,
        "source_xml_mutations_rejected": 8,
        "place_sha256": sha256(data),
        "place_bytes": len(data),
        "official_release_rc_modified": False,
        "roblox_studio_tested": False,
        "real_two_client_tested": False,
        "real_mobile_tested": False,
        "published": False,
        "owner_release_approved": False,
        "stage": "OPTIONAL_PRELAUNCH_CODE_REVIEW_ONLY",
    }
    Path(args.receipt).write_text(
        json.dumps(receipt, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf8"
    )
    print("P0D_V6_TRIPLE_ROJO_SOURCE_REVIEW_READY_NOT_STUDIO")
    print("P0D_V6_TRIPLE_PLACE_SHA256=" + sha256(data))
    print("P0D_V6_TRIPLE_PLACE_BYTES=" + str(len(data)))
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except (Blocked, ValueError, OSError, UnicodeError,
            subprocess.TimeoutExpired) as exc:
        print("P0D_V6_TRIPLE_SOURCE_GATE_BLOCKED " + str(exc), file=sys.stderr)
        sys.exit(1)
