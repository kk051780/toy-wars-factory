#!/usr/bin/env python3
"""Source-pinned, independent Rojo 7.7.1-generated RBXLX validator.

This asserts that Rojo actually exported each Luau source into the expected
Roblox Instance type, at the expected service path, with original UTF-8 code.
It DOES NOT simulate Studio's DataModel runtime, test gameplay, or publish.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET

PACKET = Path(__file__).resolve().parents[1]
GAME = PACKET / "official_src"
GAME_SOURCE_SHA = "5dc6c958ea5549b1e859d6d250e6179e731181fb"
GAME_MANIFEST_GIT_BLOB_SHA1 = "f7522d379fcbced00b03e35ba3da1c33f6642251"
OFFICIAL_BLOB_LOCK = PACKET / "OFFICIAL_SOURCE_LOCK.json"
ROJO_VERSION = "7.7.1"
ROJO_RELEASE_LINUX_ZIP_SHA256 = "00feb4fa0829a1dd72b49df2639da519a352bfe13cadcd83969e2ba2bb5693c4"
SCRIPT_CLASSES = {"Script", "LocalScript", "ModuleScript"}
MANIFEST_KEYS = {"files", "format", "game_id", "packet_id", "public_source_allowed", "work_id"}


class VerificationError(ValueError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise VerificationError(message)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def source_manifest(root: Path = GAME) -> dict[str, bytes]:
    manpath = root / "BUILD_MANIFEST.json"
    manifest_raw = manpath.read_bytes()
    manifest_object_sha1 = hashlib.sha1(b"blob " + str(len(manifest_raw)).encode() + b"\0" + manifest_raw).hexdigest()
    require(manifest_object_sha1 == GAME_MANIFEST_GIT_BLOB_SHA1, "OFFICIAL_RC_MANIFEST_GIT_BLOB_CHANGED")
    manifest = json.loads(manifest_raw)
    require(set(manifest) == MANIFEST_KEYS, "MANIFEST_KEYS_NOT_CANONICAL")
    require(manifest["format"] == "P0D_PUBLIC_SOURCE_V1", "NOT_PUBLIC_SOURCE")
    require(manifest["game_id"] == "TRAP_RAIDERS", "WRONG_GAME")
    require(manifest["public_source_allowed"] is True, "GAME_NOT_PUBLIC_APPROVED")
    rows = manifest["files"]
    require(isinstance(rows, list) and len(rows) == 32, "EXPECTED_32_MANIFEST_FILES")
    paths = [x["path"] for x in rows]
    require(len(paths) == len(set(paths)), "MANIFEST_DUPLICATE_SOURCE")
    disk_files = set()
    for p in root.rglob("*"):
        if p.is_file():
            require(not p.is_symlink(), "SYMLINK_SOURCE_REJECTED")
            disk_files.add(p.relative_to(root).as_posix())
    require(disk_files == set(paths) | {"BUILD_MANIFEST.json"}, "MISSING_OR_EXTRA_GAME_SOURCE")
    lock = json.loads(OFFICIAL_BLOB_LOCK.read_text(encoding="utf-8"))
    require(set(lock) == {"format", "official_rc_commit", "official_root", "files"}, "OFFICIAL_SOURCE_LOCK_KEYS")
    require(lock["format"] == "P0D_OFFICIAL_RC_BLOB_SNAPSHOT_V1", "OFFICIAL_SOURCE_LOCK_FORMAT")
    require(lock["official_rc_commit"] == GAME_SOURCE_SHA and lock["official_root"] == "releases/P0D_S1_KIDS_RC01", "OFFICIAL_RC_COMMIT_LOCK_BAD")
    require(isinstance(lock["files"], list) and len(lock["files"]) == 33, "OFFICIAL_RC_33_FILE_LOCK")
    require({row["path"] for row in lock["files"]} == disk_files, "OFFICIAL_RC_FILES_NOT_EXACT")
    for row in lock["files"]:
        require(set(row) == {"path", "git_blob_sha1", "size"}, "OFFICIAL_RC_LOCK_ROW")
        blob = (root / row["path"]).read_bytes()
        git_sha = hashlib.sha1(b"blob " + str(len(blob)).encode() + b"\0" + blob).hexdigest()
        require(git_sha == row["git_blob_sha1"] and len(blob) == row["size"],
            "ORIGINAL_GIT_OBJECT_MISMATCH " + row["path"])
    checked = {}
    for row in rows:
        require(set(row) == {"path", "sha256", "size"}, "MANIFEST_ROW_INVALID")
        name = row["path"]
        require(isinstance(name, str) and "\\" not in name, "INVALID_MANIFEST_PATH")
        parts = Path(name).parts
        require(parts and not Path(name).is_absolute() and ".." not in parts, "PATH_TRAVERSAL")
        data = (root / name).read_bytes()
        require(len(data) == row["size"] and sha(data) == row["sha256"], "SOURCE_SHA_MISMATCH " + name)
        checked[name] = data
    source_list = [p for p in paths if p.startswith("src/") and p.endswith(".luau")]
    require(len(source_list) == 20, "EXPECTED_EXACTLY_20_LUAU")
    return checked


def expected_rojo_source_paths(root: Path = GAME) -> dict[str, tuple[str, bytes]]:
    originals = source_manifest(root)
    mapping: dict[str, tuple[str, bytes]] = {}
    for name, data in originals.items():
        if not (name.startswith("src/") and name.endswith(".luau")):
            continue
        prefix = name.split("/")[1]
        short = name.rsplit("/", 1)[1]
        if prefix == "server":
            location = "ServerScriptService/TrapRaidersS1/"
            instance_class = "Script" if short.endswith(".server.luau") else "ModuleScript"
            instance_name = short.replace(".server.luau", "").replace(".luau", "")
        elif prefix == "shared":
            location = "ReplicatedStorage/TrapRaidersShared/"
            instance_class = "ModuleScript"
            instance_name = short.replace(".luau", "")
        elif prefix == "client":
            location = "StarterPlayer/StarterPlayerScripts/"
            if short == "HUD.client.luau":
                instance_name, instance_class = "TrapRaidersHUD", "LocalScript"
            elif short == "FirstMinuteCoach.client.luau":
                instance_name, instance_class = "TrapRaidersCoach", "LocalScript"
            elif short == "S1GoroganStompRing.client.luau":
                instance_name, instance_class = "S1GoroganStompRing", "LocalScript"
            else:
                instance_name, instance_class = short.replace(".luau", ""), "ModuleScript"
        else:
            raise VerificationError("UNEXPECTED_LUAU_SOURCE_ROOT " + prefix)
        path = location + instance_name
        require(path not in mapping, "DUPLICATE_PLANNED_ROJO_PATH")
        mapping[path] = (instance_class, data)
    require(len(mapping) == 20, "WRONG_EXPECTED_ROJO_INSTANCES")
    return mapping


def prop(item: ET.Element, key: str) -> str | None:
    props = item.find("Properties")
    if props is None:
        return None
    for p in props:
        if p.get("name") == key:
            return p.text or ""
    return None


def item_records(xml: bytes) -> list[tuple[str, str, str | None]]:
    try:
        root = ET.fromstring(xml)
    except ET.ParseError as exc:
        raise VerificationError("RBXLX_INVALID_XML") from exc
    require(root.tag == "roblox", "NOT_ROBLOX_XML_ROOT")
    found = []
    def walk(el: ET.Element, parents: tuple[str, ...]) -> None:
        for child in el:
            if child.tag != "Item":
                continue
            cls = child.get("class")
            name = prop(child, "Name")
            require(isinstance(cls, str) and cls, "RBXLX_ITEM_CLASS_MISSING")
            require(isinstance(name, str) and name, "RBXLX_ITEM_NAME_MISSING")
            # A DataModel wrapper (if any) is not part of service paths.
            path = parents if cls == "DataModel" else parents + (name,)
            found.append(("/".join(path), cls, prop(child, "Source")))
            walk(child, path)
    walk(root, ())
    require(bool(found), "EMPTY_PLACE")
    return found


def verify_place(xml: bytes, root: Path = GAME) -> dict:
    expected = expected_rojo_source_paths(root)
    records = item_records(xml)
    scripts = [row for row in records if row[1] in SCRIPT_CLASSES]
    require(len(scripts) == 20, "WRONG_TOTAL_SCRIPT_INSTANCE_COUNT " + str(len(scripts)))
    observed = {}
    for path, cls, src in scripts:
        require(path not in observed, "DUPLICATE_ROBLOX_SCRIPT_PATH " + path)
        require(path in expected, "UNAPPROVED_SCRIPT_INSTANCE " + path)
        actual_cls, expected_data = expected[path]
        require(cls == actual_cls, "SCRIPT_WRONG_CLASS " + path)
        require(src is not None, "SCRIPT_SOURCE_NOT_SERIALIZED " + path)
        require(src.encode("utf-8") == expected_data, "ACTUAL_SCRIPT_BYTES_DIFFER " + path)
        observed[path] = cls
    require(set(observed) == set(expected), "MISSING_EXPECTED_SCRIPT_INSTANCE")
    require(sum(cls == "Script" for cls in observed.values()) == 1, "DUPLICATE_GAME_AUTHORITY")
    require(sum(cls == "LocalScript" for cls in observed.values()) == 3, "MISSING_CLIENT_HUD_OR_FTUE")
    require(sum(cls == "ModuleScript" for cls in observed.values()) == 16, "BAD_SHARED_SERVER_MODULES")
    return {
        "format": "P0D_REAL_ROJO_RBXLX_SOURCE_RECEIPT_V1",
        "source_game_commit": GAME_SOURCE_SHA,
        "source_manifest_sha256": sha((root / "BUILD_MANIFEST.json").read_bytes()),
        "official_source_lock_git_blob_count": 33,
        "official_source_commit_pinned": GAME_SOURCE_SHA,
        "rojo_version": ROJO_VERSION,
        "rojo_release_linux_zip_sha256": ROJO_RELEASE_LINUX_ZIP_SHA256,
        "script_source_count": len(scripts),
        "server_authority_script_count": 1,
        "local_script_count": 3,
        "module_script_count": 16,
        "all_source_bytes_identical_to_game_manifest": True,
        "src_server_game_path": "ServerScriptService/TrapRaidersS1/Game",
        "src_client_hud_path": "StarterPlayer/StarterPlayerScripts/TrapRaidersHUD",
        "stage": "PRELAUNCH",
        "official_rc_adopted": False,
        "roblox_studio_tested": False,
        "two_client_tested": False,
        "mobile_tested": False,
        "roblox_published": False,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--place", required=True)
    ap.add_argument("--receipt", required=True)
    args = ap.parse_args()
    place = Path(args.place)
    require(place.is_file() and not place.is_symlink(), "MISSING_RBXLX")
    data = place.read_bytes()
    require(len(data) > 8192, "RBXLX_UNEXPECTEDLY_SMALL")
    result = verify_place(data)
    result["rojo_place_sha256"] = sha(data)
    result["rojo_place_bytes"] = len(data)
    Path(args.receipt).write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("P0D_REAL_ROJO_RBXLX_20_OF_20_SOURCE_BYTES_PASS")
    print("P0D_REAL_ROJO_RBXLX_SINGLE_AUTHORITY_THREE_CLIENTS_16_MODULES_PASS")
    print("P0D_ROJO_PLACE_FILE_SHA256=" + result["rojo_place_sha256"])
    print("P0D_ROJO_PLACE_FILE_BYTES=" + str(result["rojo_place_bytes"]))
    print("P0D_STUDIO_RUNTIME_NOT_TESTED")


if __name__ == "__main__":
    main()
