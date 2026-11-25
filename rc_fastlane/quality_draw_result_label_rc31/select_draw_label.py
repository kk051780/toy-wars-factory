#!/usr/bin/env python3
"""Non-overlapping GQ draw-result UI overlay for the already adopted 900s DRAW.

Owns only the EXISTING EGGRUMBLE_MatchResultService source.  It neither
changes the original #487/#538 author source nor writes to Game, Host,
Combat, RoundReplay, Score, Inventory, Store or Remote.  All other 30 real
31-source files must be byte-for-byte identical; OFF is exactly reversible.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

TARGET = "EGGRUMBLE_MatchResultService"
OLD = ' local status=if won then (if castle.alive then "勝利！" else "チーム勝利！") else "試合終了"'
NEW = (' local status=if session.rules.winner=="DRAW" then "引き分け"\n'
       '  elseif won then (if castle.alive then "勝利！" else "チーム勝利！")\n'
       '  else "試合終了"')
FILENAME = "GQ_DRAW_LABEL_EXISTING_RESULT.luau"
RECEIPT = "GQ_DRAW_RESULT_RC31_SOURCE_EXACT_RECEIPT.json"

def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def mapped(project: Path):
    project = project.resolve(strict=True)
    data = json.loads(project.read_text(encoding="utf8"))
    files = {}
    def walk(node, route=()):
        for name, value in node.items():
            if name.startswith("$"):
                continue
            if not isinstance(value, dict):
                raise ValueError("RED_BAD_ROJO_NODE")
            key = route + (name,)
            if "$path" in value:
                if set(value) != {"$path"} or key in files:
                    raise ValueError("RED_NONUNIQUE_SCRIPT_ROUTE")
                files[key] = (project.parent / value["$path"]).resolve(strict=True)
            else:
                walk(value, key)
    walk(data["tree"])
    if len(files) != 31 or len({key[-1] for key in files}) != 31:
        raise ValueError("RED_SOURCE_COUNT_OR_DUPLICATE")
    choices = [key for key in files if key[-1] == TARGET]
    if len(choices) != 1:
        raise ValueError("RED_SINGLE_RESULT_AUTHORITY")
    return data, files, choices[0]

def patch(before: str) -> str:
    if before.count(OLD) != 1 or "GQ_DRAW_LABEL_RESULT" in before or before.count('function ResultService.showIfFinished') != 1:
        raise ValueError("RED_ORIGINAL_RESULT_SOURCE_DRIFT")
    after = before.replace(OLD, '-- GQ_DRAW_LABEL_RESULT: the original server-authoritative draw must not appear as a loss.\n' + NEW, 1)
    if after.replace('-- GQ_DRAW_LABEL_RESULT: the original server-authoritative draw must not appear as a loss.\n' + NEW, OLD, 1) != before:
        raise ValueError("RED_DRAW_RESULT_OFF_INVERSE")
    if 'session.rules.winner=="DRAW"' not in after or after.count('makeResultGui(') != before.count('makeResultGui('):
        raise ValueError("RED_RESULT_SEMANTICS_DRIFT")
    return after

def prepare(base: Path, out: Path):
    base = base.resolve(strict=True)
    out = out.resolve()
    if out.exists() or out.parent != base.parent or base == out:
        raise ValueError("RED_NOT_ISOLATED_SIBLING")
    obj, old, target = mapped(base)
    before = old[target].read_text(encoding="utf8")
    selected = patch(before)
    output_source = out.parent / FILENAME
    if output_source.exists():
        raise ValueError("RED_SELECTED_RESULT_ALREADY_EXISTS")
    output_source.write_text(selected, encoding="utf8")
    obj = copy.deepcopy(obj)
    node = obj["tree"]
    for key in target:
        node = node[key]
    node["$path"] = output_source.name
    out.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf8")
    _, new, updated = mapped(out)
    changed = [key for key in old if old[key].read_bytes() != new[key].read_bytes()]
    if set(new) != set(old) or updated != target or changed != [target]:
        raise ValueError("RED_MORE_THAN_ONE_RESULT_SOURCE_CHANGED")
    receipt = {
        "feature_id": "GQ_DRAW_LABEL_20261117",
        "adopted_dependency": "MATCH_DEADLINE_DRAW_499",
        "changed_existing_script": TARGET,
        "runtime_source_count": 31,
        "new_scripts": 0,
        "other_30_byte_exact": True,
        "off_previous_result_byte_exact": True,
        "result_win_loss_score_authority_unchanged": True,
        "draw_display": "引き分け",
        "prior_sha256": digest(old[target].read_bytes()),
        "selected_sha256": digest(selected.encode("utf8")),
        "rojo_class_source_exact": "NOT_TESTED",
        "real_studio_android_fun": "NOT_TESTED",
        "formal_rc_adopted": False
    }
    (out.parent / RECEIPT).write_text(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf8")
    print("GQ_DRAW_RESULT_ONLY_ONE_SOURCE_OTHER30_OFF_EXACT_PASS")

def verify(base: Path, out: Path, place: Path):
    _, old, target = mapped(base)
    _, new, other_target = mapped(out)
    selected = patch(old[target].read_text(encoding="utf8"))
    if other_target != target or new[target].read_text(encoding="utf8") != selected:
        raise ValueError("RED_WRONG_DRAW_SOURCE")
    if set(old) != set(new) or [key for key in old if old[key].read_bytes() != new[key].read_bytes()] != [target]:
        raise ValueError("RED_OTHER30_CHANGED")
    embedded = {}
    for item in ET.parse(place).getroot().iter("Item"):
        klass = item.attrib.get("class")
        if klass not in {"Script", "ModuleScript", "LocalScript"}:
            continue
        props = item.find("Properties")
        if props is None:
            raise ValueError("RED_MISSING_CLASS_PROPERTIES")
        name = props.findtext("string[@name='Name']")
        source = props.findtext("ProtectedString[@name='Source']")
        if source is None:
            source = props.findtext("string[@name='Source']")
        if not name or source is None or name in embedded:
            raise ValueError("RED_DUPLICATE_MISSING_ROJO_SOURCE")
        embedded[name] = (klass, source.replace("\r\n", "\n"))
    if len(embedded) != 31 or set(embedded) != {key[-1] for key in new}:
        raise ValueError("RED_ROJO31_ACTUAL_SOURCES")
    for route, path in new.items():
        klass = ("Script" if path.name.endswith(".server.luau") else
                 "LocalScript" if path.name.endswith(".client.luau") else "ModuleScript")
        if embedded[route[-1]] != (klass, path.read_text(encoding="utf8").replace("\r\n", "\n")):
            raise ValueError("RED_ROJO_SOURCE_OR_CLASS_" + route[-1])
    receipt_file = out.parent / RECEIPT
    receipt = json.loads(receipt_file.read_text(encoding="utf8"))
    if not (receipt["other_30_byte_exact"] and receipt["off_previous_result_byte_exact"]):
        raise ValueError("RED_ROLLBACK")
    receipt.update(rojo_class_source_exact="31/31",
                   place_sha256=digest(place.read_bytes()),
                   place_bytes=place.stat().st_size)
    receipt_file.write_text(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True)+"\n", encoding="utf8")
    print("GQ_DRAW_ACTUAL_ROJO31_NATIVE_SOURCE_CLASS_OFF_EXACT_PASS")

def selftest():
    source = 'local x=0\n'+OLD+'\nfunction ResultService.showIfFinished() end\nmakeResultGui()'
    changed = patch(source)
    assert changed.count('session.rules.winner=="DRAW"') == 1
    assert changed.replace('-- GQ_DRAW_LABEL_RESULT: the original server-authoritative draw must not appear as a loss.\n' + NEW, OLD) == source
    assert 'elseif won then' in changed and 'else "試合終了"' in changed
    for invalid in (source.replace(OLD, ""), source.replace(OLD, OLD+"\n"+OLD),
                    source.replace("function ResultService.showIfFinished","function NotResult"),
                    changed):
        try: patch(invalid)
        except ValueError: pass
        else: raise AssertionError("RED_MUTATION_NOT_REJECTED")
    print("GQ_DRAW_SOURCE_INVERSE_AND_FOUR_NEGATIVE_CONTROLS_PASS")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("action", choices=("prepare", "verify", "selftest"))
    ap.add_argument("--base", type=Path)
    ap.add_argument("--out", type=Path)
    ap.add_argument("--place", type=Path)
    a = ap.parse_args()
    if a.action == "selftest": selftest()
    elif a.base is None or a.out is None: ap.error("--base and --out required")
    elif a.action == "prepare": prepare(a.base, a.out)
    elif a.place is None: ap.error("--place required for verify")
    else: verify(a.base, a.out, a.place)
