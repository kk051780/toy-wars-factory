#!/usr/bin/env python3
"""Source-select the EXISTING #540 Assassin respawn fix into the existing V3 31.
No new Host, Game, Combat or Remote authority: exactly one Host Source changes.
#540's own verified patch algorithm is imported from its immutable Git SHA.
"""
from __future__ import annotations
import argparse
import contextlib
import io
import copy
import hashlib
import importlib.machinery
import json
import os
from pathlib import Path

AUTHOR_HEAD = "40a79702a3ca949e2bf65f9108126a34d44c88b4"
AUTHOR_BLOB = "c7a4d39067c788a7e89e9f7010fe031d0560abcf"
CURRENT_HOST_SHA256 = "0ea188ee39e95b2a4ca00c7435622a012b6b101afb4386eec91b07710cb76eed"
HOST = ("ServerScriptService", "EGGRUMBLE_LobbyCastleModesPreview")
SWARM = ("ServerScriptService", "EGGRUMBLE_SwarmCombat")
BOT = ("ServerScriptService", "EGGRUMBLE_BotActors")

def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def git_blob(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()

def load_author(path: Path):
    path = path.resolve(strict=True)
    if git_blob(path.read_bytes()) != AUTHOR_BLOB:
        raise ValueError("RED_GQ540_AUTHOR_SOURCE_DRIFT")
    return importlib.machinery.SourceFileLoader("frozen_gq540_author", str(path)).load_module()

def select(original_project: Path, selected537_project: Path, author_path: Path, output_project: Path):
    if output_project.exists():
        raise ValueError("RED_OUTPUT_PROJECT_ALREADY_EXISTS")
    author = load_author(author_path)
    base_doc, base = author.scan(original_project.resolve(strict=True))
    doc, current = author.scan(selected537_project.resolve(strict=True))
    if len(current) != 31 or len(base) != 31 or set(base) != set(current):
        raise ValueError("RED_MISSING_AUTHOR_31")
    if current[SWARM].read_bytes() == base[SWARM].read_bytes():
        raise ValueError("RED_GQ541_NOT_SELECTED")
    for key in current:
        if key not in (SWARM, HOST) and current[key].read_bytes() != base[key].read_bytes():
            raise ValueError("RED_UNEXPECTED_BEFORE_GQ540_" + "/".join(key))
    if current[HOST].read_bytes() == base[HOST].read_bytes():
        raise ValueError("RED_GQ537_HOST_NOT_SELECTED")
    original_host = current[HOST].read_bytes()
    if sha(original_host) != CURRENT_HOST_SHA256:
        raise ValueError("RED_GQ540_SINGLE_HOST_SHA_DRIFT")
    patched_host = author.apply(original_host.decode("utf-8"), current[BOT].read_text(encoding="utf-8"))
    if (patched_host.replace(author.ALT_NEW, author.ALT_OLD, 1).encode("utf-8")
            != original_host):
        raise ValueError("RED_GQ540_REVERSE_NOT_EXACT")
    output_dir = output_project.parent.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    new_host = output_dir / "EGGRUMBLE_LobbyCastleModesPreview_540.server.luau"
    if new_host.exists():
        raise ValueError("RED_HOST_OVERWRITE")
    new_host.write_text(patched_host, encoding="utf-8")
    project = copy.deepcopy(doc)
    project["name"] = "EGGRUMBLE_RC31_GQ541_PLUS_ORIGINAL_GQ540_SOURCE_SELECT"
    def rewrite(node, path=()):
        for key, value in node.items():
            if key.startswith("$"): continue
            route = path + (key,)
            if "$path" in value:
                target = new_host if route == HOST else current[route]
                value["$path"] = os.path.relpath(target, output_dir).replace(os.sep, "/")
            else:
                rewrite(value, route)
    rewrite(project["tree"])
    output_project.write_text(json.dumps(project, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    _, updated = author.scan(output_project)
    if set(updated) != set(current):
        raise ValueError("RED_31_SCRIPT_ROUTE_MISMATCH")
    for key in current:
        expected = patched_host.encode("utf-8") if key == HOST else current[key].read_bytes()
        if updated[key].read_bytes() != expected:
            raise ValueError("RED_UNAUTHORIZED_SCRIPT_WRITE_" + "/".join(key))
    receipt = {
        "source_count": 31, "source_original_author_gq540": AUTHOR_HEAD,
        "source_original_author_blob_gq540": AUTHOR_BLOB,
        "selected_previous_original_author_gq541": True,
        "original_current_host_sha256": sha(original_host),
        "selected_current_host_sha256": sha(patched_host.encode("utf-8")),
        "changed_script": "/".join(HOST),
        "other_30_script_source_bytes_exact": 30,
        "other_neutral_541_preserved_exact": True,
        "s1_legacy_unmodified": True,
        "primary_profile_switched": False,
        "real_studio_android_fun": "NOT_TESTED",
        "published": False,
        "source_sha256": {"/".join(k): sha(p.read_bytes()) for k,p in updated.items()},
    }
    receipt_path = output_dir / "GQ540_SELECTED31_RECEIPT.json"
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("GQ540_AUTHOR_REUSED_SINGLE_HOST_ON_EXISTING_GQ541_31_PASS")
    return receipt

def verify(original_selected: Path, selected: Path, receipt: Path, place: Path, author_path: Path):
    author = load_author(author_path)
    with contextlib.redirect_stdout(io.StringIO()):
        author.verify_place(selected, receipt, place)
    _, old = author.scan(original_selected)
    _, new = author.scan(selected)
    if len(old) != len(new) or len(new) != 31 or set(old) != set(new):
        raise ValueError("RED_GQ540_SCRIPTSET_MISMATCH")
    unchanged = sum(old[k].read_bytes() == new[k].read_bytes() for k in old)
    if unchanged != 30 or old[HOST].read_bytes() == new[HOST].read_bytes():
        raise ValueError("RED_GQ540_NOT_EXACTLY_ONE_HOST_CHANGED")
    if old[SWARM].read_bytes() != new[SWARM].read_bytes():
        raise ValueError("RED_GQ541_SWARM_OVERWRITTEN")
    report = {
        "source_exact": "31/31", "only_host_changed": True,
        "unchanged_scripts": unchanged, "original_gq541_swarm_preserved": True,
        "place_bytes": place.stat().st_size, "place_sha256": sha(place.read_bytes()),
        "official_rc_adoption_from_pr": False, "studio_android_owner": "NOT_TESTED",
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return report

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--original31", type=Path, required=True)
    p.add_argument("--selected537", type=Path, required=True)
    p.add_argument("--author", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--verify-place", type=Path)
    args = p.parse_args()
    if args.verify_place:
        verify(args.selected537, args.out, args.out.parent / "GQ540_SELECTED31_RECEIPT.json",
               args.verify_place, args.author)
    else:
        select(args.original31, args.selected537, args.author, args.out)

if __name__ == "__main__":
    main()
