#!/usr/bin/env python3
"""GQ586: select ONE current-session deposit guard into the existing canonical Host.

Never edits original author files, any other gameplay controller, main or RC.
Input must be current exact 31-source project; stale anchors fail closed.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

HOST = ("ServerScriptService", "EGGRUMBLE_LobbyCastleModesPreview")
N = 31
START = 'prompt(deposit,"卵を納入","自分の城",function(p)\n'
END = ' end)\n local vault=block(model,"EggVault"'
# GQ537 already added the post-success session.refresh(); DO NOT remove it.
OLD = '  if tostring(p.UserId)~=entry.id or not session.rules then return end\n'
NEW = ('  -- GQ_DEPOSIT_CURRENT_MATCH_586: old-mode/retired-session deposit is forbidden.\n'
       '  if tostring(p.UserId)~=entry.id or joined[p.UserId]~=session.mode\n'
       '   or sessions[session.mode]~=session or not session.rules then return end\n')
FLAG = "GQ_DEPOSIT_CURRENT_MATCH_586"

def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()

def flatten(project: Path):
    project = project.resolve(strict=True)
    data = json.loads(project.read_text(encoding="utf-8"))
    found = {}
    def walk(node, path=()):
        for key, value in node.items():
            if key.startswith("$"):
                continue
            if not isinstance(value, dict):
                raise ValueError("RED_PROJECT_INVALID")
            route = path + (key,)
            if "$path" in value:
                if set(value) != {"$path"} or route in found:
                    raise ValueError("RED_DUPLICATE_AUTHORITY")
                found[route] = (project.parent / value["$path"]).resolve(strict=True)
            else:
                walk(value, route)
    walk(data["tree"])
    if len(found) != N or len({x[-1] for x in found}) != N or HOST not in found:
        raise ValueError("RED_NOT_SINGLE_HOST_31")
    return data, found

def body(source: str) -> str:
    if source.count(START) != 1 or source.count(END) != 1:
        raise ValueError("RED_DEPOSIT_CALLBACK_ANCHOR_DRIFT")
    p = source.index(START) + len(START)
    q = source.index(END, p)
    callback = source[p:q]
    if 'Rules.depositEggs(session.rules,entry.id,c.heldEggs)' not in callback:
        raise ValueError("RED_DEPOSIT_OWNER_MISSING")
    if 'if ok then session.refresh() end' not in callback:
        raise ValueError("RED_GQ537_DEPOSIT_REFRESH_LOST")
    return callback

def overlay(source: str) -> str:
    if FLAG in source:
        raise ValueError("RED_DEPOSIT_GUARD_ALREADY_SELECTED")
    original = body(source)
    if original.count(OLD) != 1 or "joined[p.UserId]" in original or "sessions[session.mode]" in original:
        raise ValueError("RED_OLD_CALLBACK_ALREADY_MODIFIED")
    fixed = original.replace(OLD, NEW, 1)
    selected = source.replace(START + original, START + fixed, 1)
    if selected.replace(NEW, OLD, 1) != source:
        raise ValueError("RED_ROLLBACK_NOT_EXACT")
    if selected.count(FLAG) != 1:
        raise ValueError("RED_WRONG_GUARD_COUNT")
    if "if ok then session.refresh() end" not in body(selected):
        raise ValueError("RED_DEPOSIT_REFRESH_LOST")
    return selected

def prepare(base: Path, out: Path):
    base = base.resolve(strict=True)
    out = out.resolve()
    if base == out or out.parent != base.parent:
        raise ValueError("RED_INPLACE_OR_FOREIGN_PROJECT")
    project, scripts = flatten(base)
    raw = scripts[HOST].read_bytes()
    before = raw.decode("utf-8")
    after = overlay(before)
    if after == before or after.replace(NEW, OLD, 1) != before:
        raise ValueError("RED_UNEXPECTED_HOST_DIFF")
    out_host = out.parent / "GQ586_CURRENT_MATCH_HOST.server.luau"
    if out_host.exists() and out_host.read_text(encoding="utf-8") != after:
        raise ValueError("RED_OUTPUT_HOST_ALREADY_DIFFERENT")
    out_host.write_text(after, encoding="utf-8")
    selected = copy.deepcopy(project)
    selected["tree"]["ServerScriptService"][HOST[-1]]["$path"] = out_host.name
    out.write_text(json.dumps(selected, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    _, next_scripts = flatten(out)
    changed = [k for k in scripts if scripts[k].read_bytes() != next_scripts[k].read_bytes()]
    if set(scripts) != set(next_scripts) or changed != [HOST]:
        raise ValueError("RED_OTHER_30_RUNTIME_SCRIPTS_CHANGED")
    proof = {
        "source_count": 31, "only_changed_script": "/".join(HOST),
        "other_30_byte_exact": True, "rollback_host_exact": True,
        "current_host_sha256_before": sha(raw),
        "current_host_sha256_after": sha(after.encode("utf-8")),
        "source_flag": FLAG,
        "official_rc_adopted": False,
        "studio_android_fun_owner": "NOT_TESTED"
    }
    (out.parent / "GQ586_SOURCE_RECEIPT.json").write_text(
        json.dumps(proof, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("GQ586_ONE_CURRENT_HOST_OTHER30_UNCHANGED_ROLLBACK_PASS")

def embedded_scripts(place: Path):
    entries = {}
    for item in ET.parse(place).iter("Item"):
        kind = item.attrib.get("class")
        if kind not in {"Script", "ModuleScript", "LocalScript"}:
            continue
        properties = item.find("Properties")
        if properties is None:
            raise ValueError("RED_EMBEDDED_SCRIPT_PROPERTIES")
        name = properties.findtext("string[@name='Name']")
        value = properties.findtext("ProtectedString[@name='Source']")
        if value is None:
            value = properties.findtext("string[@name='Source']")
        if not name or value is None or name in entries:
            raise ValueError("RED_EMBEDDED_DUPLICATE_SCRIPT")
        entries[name] = kind, value.replace("\r\n", "\n")
    return entries

def verify(base: Path, out: Path, place: Path):
    _, original = flatten(base)
    _, current = flatten(out)
    if set(original) != set(current):
        raise ValueError("RED_SCRIPT_NAMES_CHANGED")
    changed = [k for k in original if original[k].read_bytes() != current[k].read_bytes()]
    if changed != [HOST]:
        raise ValueError("RED_MORE_THAN_HOST_CHANGED")
    old = original[HOST].read_text(encoding="utf-8")
    now = current[HOST].read_text(encoding="utf-8")
    if now != overlay(old):
        raise ValueError("RED_SELECTED_HOST_DRIFT")
    if now.replace(NEW, OLD, 1) != old:
        raise ValueError("RED_INVERSE_ROLLBACK_DRIFT")
    embedded = embedded_scripts(place)
    if len(embedded) != N or set(embedded) != {k[-1] for k in current}:
        raise ValueError("RED_NOT_EXACT_31_EMBEDDED")
    for k, path in current.items():
        kind = ("Script" if path.name.endswith(".server.luau") else
                "LocalScript" if path.name.endswith(".client.luau") else "ModuleScript")
        actual = (kind, path.read_text(encoding="utf-8").replace("\r\n", "\n"))
        if embedded[k[-1]] != actual:
            raise ValueError("RED_PLACE_SOURCE_CLASS_MISMATCH_" + k[-1])
    receipt = out.parent / "GQ586_SOURCE_RECEIPT.json"
    proof = json.loads(receipt.read_text(encoding="utf-8"))
    if not proof["other_30_byte_exact"] or not proof["rollback_host_exact"]:
        raise ValueError("RED_PROOF_INVALID")
    proof.update(real_rojo_source_class_exact="31/31",
                 private_place_bytes=place.stat().st_size,
                 private_place_sha256=sha(place.read_bytes()))
    receipt.write_text(json.dumps(proof, indent=2, sort_keys=True) + "\n",
                       encoding="utf-8")
    print("GQ586_TRUE_PLACE_SOURCE_CLASS_31_31_PASS", proof["private_place_bytes"])

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["prepare", "verify"])
    parser.add_argument("--base", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--place", type=Path)
    args = parser.parse_args()
    if args.action == "prepare":
        prepare(args.base, args.out)
    else:
        if not args.place:
            parser.error("verify needs --place")
        verify(args.base, args.out, args.place)

if __name__ == "__main__":
    main()
