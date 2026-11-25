#!/usr/bin/env python3
"""GQ8 mobile post-match readability, existing ResultService only.
The 31-script RC has no new ScreenGui, score producer, or authority.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "rc_fastlane/quality_castle_prompt_session_20261117"))
from select_castle import mapping

FEATURE = "GQ8_RESULT_MOBILE_READABILITY_20261118"
TARGET = ("ServerScriptService", "EGGRUMBLE_MatchResultService")
FILE = "GQ8_RESULT_MOBILE_SELECTED_SOURCE.luau"
MARKER = "-- GQ8_RESULT_MOBILE_READABILITY_20261118"
POSITION_BEFORE = (
    " statsLabel.Position=UDim2.fromOffset(12,51)\n"
    " statsLabel.Size=UDim2.new(1,-24,0,30)\n"
)
POSITION_AFTER = (
    " statsLabel.Position=UDim2.fromOffset(12,49)\n"
    " statsLabel.Size=UDim2.new(1,-24,0,41)\n"
)
TEXT_BEFORE = (
    " statsLabel.TextScaled=true\n"
    " statsLabel.TextWrapped=false\n"
    " statsLabel.Text=stats\n"
)
TEXT_AFTER = (
    " statsLabel.TextScaled=false\n"
    " statsLabel.TextSize=15\n"
    " statsLabel.TextWrapped=true\n"
    " statsLabel.TextYAlignment=Enum.TextYAlignment.Center\n"
    ' statsLabel.Text=stats:gsub(" 納","\\n納",1)\n'
)

def sha(source: str) -> str:
    return hashlib.sha256(source.encode("utf-8")).hexdigest()

def select(source: str) -> str:
    required = (
        "local function makeResultGui(",
        'statsLabel.Name="VerifiedPersonalStats"',
        "function ResultService.showIfFinished(",
    )
    if MARKER in source or any(source.count(s) != 1 for s in required):
        raise ValueError("RED_GQ8_MOBILE_RESULT_OWNER_DRIFT")
    if source.count(POSITION_BEFORE) != 1 or source.count(TEXT_BEFORE) != 1:
        raise ValueError("RED_GQ8_MOBILE_RESULT_LAYOUT_DRIFT")
    result = source.replace(POSITION_BEFORE, MARKER + "\n" + POSITION_AFTER, 1)
    result = result.replace(TEXT_BEFORE, TEXT_AFTER, 1)
    if off(result) != source:
        raise ValueError("RED_GQ8_MOBILE_RESULT_NOT_REVERSIBLE")
    return result

def off(source: str) -> str:
    if source.count(MARKER + "\n" + POSITION_AFTER) != 1 or source.count(TEXT_AFTER) != 1:
        raise ValueError("RED_GQ8_MOBILE_RESULT_INVALID_OFF")
    return source.replace(MARKER + "\n" + POSITION_AFTER, POSITION_BEFORE, 1).replace(TEXT_AFTER, TEXT_BEFORE, 1)

def prepare(base: Path, out: Path) -> None:
    base = base.resolve(strict=True)
    out = out.resolve()
    if base.parent != out.parent or out.exists() or (out.parent / FILE).exists():
        raise ValueError("RED_GQ8_MOBILE_RESULT_COLLISION")
    project, before = mapping(base)
    if len(before) != 31 or TARGET not in before:
        raise ValueError("RED_GQ8_MOBILE_RESULT_MISSING_31")
    source = before[TARGET].read_text(encoding="utf-8")
    result = select(source)
    (out.parent / FILE).write_text(result, encoding="utf-8")
    selected = copy.deepcopy(project)
    selected["name"] = "EGGRUMBLE_V3_GQ8_MOBILE_RESULT_31"
    selected["tree"][TARGET[0]][TARGET[1]]["$path"] = FILE
    out.write_text(json.dumps(selected, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    _, after = mapping(out)
    if len(after) != 31 or set(before) != set(after):
        raise ValueError("RED_GQ8_MOBILE_RESULT_SOURCE_SET")
    changed = [key for key in before if before[key].read_bytes() != after[key].read_bytes()]
    if changed != [TARGET] or off(after[TARGET].read_text(encoding="utf-8")) != source:
        raise ValueError("RED_GQ8_MOBILE_RESULT_NOT_ONE_SOURCE")
    receipt = {
        "feature_id": FEATURE,
        "changed_source": TARGET[-1],
        "source_count": 31,
        "other30_byte_exact": True,
        "off_previous_source_byte_exact": True,
        "adds_gui": False,
        "changes_score_or_gameplay": False,
        "before_sha256": sha(source),
        "after_sha256": sha(result),
        "studio_android_fun": "NOT_TESTED",
        "official_rc_integrated": False,
    }
    (out.parent / "GQ8_MOBILE_RESULT_RECEIPT.json").write_text(
        json.dumps(receipt, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print("GQ8_MOBILE_CURRENT31_SINGLE_RESULT_OTHER30_EXACT_OFF_PASS")


def verify(base: Path, out: Path, place: Path) -> None:
    import xml.etree.ElementTree as ET
    _, before = mapping(base.resolve(strict=True))
    _, after = mapping(out.resolve(strict=True))
    if len(before) != 31 or set(before) != set(after):
        raise ValueError("RED_GQ8_MOBILE_REAL31_SET")
    changed = [key for key in before if before[key].read_bytes() != after[key].read_bytes()]
    if changed != [TARGET]:
        raise ValueError("RED_GQ8_MOBILE_REAL31_ONLY_RESULT")
    source = before[TARGET].read_text(encoding="utf-8")
    selected = after[TARGET].read_text(encoding="utf-8")
    if select(source) != selected or off(selected) != source:
        raise ValueError("RED_GQ8_MOBILE_REAL31_INVERSE")
    found = {}
    for item in ET.parse(place).getroot().iter("Item"):
        kind = item.get("class")
        if kind not in ("Script", "ModuleScript", "LocalScript"):
            continue
        props = item.find("Properties")
        if props is None:
            raise ValueError("RED_GQ8_MOBILE_PLACE_PROPS")
        name = props.findtext("string[@name='Name']")
        body = props.findtext("ProtectedString[@name='Source']")
        if body is None:
            body = props.findtext("string[@name='Source']")
        if not name or body is None or name in found:
            raise ValueError("RED_GQ8_MOBILE_PLACE_DUPLICATE")
        found[name] = (kind, body.replace("\r\n", "\n"))
    if len(found) != 31 or set(found) != {key[-1] for key in after}:
        raise ValueError("RED_GQ8_MOBILE_PLACE_SET")
    for key, filepath in after.items():
        kind = ("Script" if filepath.name.endswith(".server.luau") else
                "LocalScript" if filepath.name.endswith(".client.luau") else "ModuleScript")
        if found[key[-1]] != (kind, filepath.read_text(encoding="utf-8").replace("\r\n", "\n")):
            raise ValueError("RED_GQ8_MOBILE_PLACE_SOURCE_" + key[-1])
    receipt_path = out.parent / "GQ8_MOBILE_RESULT_RECEIPT.json"
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    if receipt["before_sha256"] != sha(source) or receipt["after_sha256"] != sha(selected):
        raise ValueError("RED_GQ8_MOBILE_RECEIPT_SOURCE")
    receipt.update(native="31/31", rojo="31/31",
                   place_bytes=place.stat().st_size,
                   place_sha256=hashlib.sha256(place.read_bytes()).hexdigest())
    receipt_path.write_text(json.dumps(receipt, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print("GQ8_MOBILE_REAL31_NATIVE_ROJO_CLASS_SOURCE_OFF_EXACT_PASS")

def selftest() -> None:
    sample = (
        "--!strict\n"
        "local function makeResultGui(player,title,stats,won)\n"
        ' statsLabel.Name="VerifiedPersonalStats"\n'
        + POSITION_BEFORE + TEXT_BEFORE +
        "end\nfunction ResultService.showIfFinished() end\n"
    )
    selected = select(sample)
    assert off(selected) == sample
    assert "TextScaled=false" in selected and "TextSize=15" in selected
    assert 'stats:gsub(" 納","\\n納",1)' in selected
    for wrong in (sample.replace(TEXT_BEFORE, ""), sample.replace(POSITION_BEFORE, ""),
                  sample + POSITION_BEFORE, selected):
        try:
            select(wrong)
        except ValueError:
            pass
        else:
            raise AssertionError("RED_GQ8_MOBILE_BAD_LAYOUT_ACCEPTED")
    try:
        off(sample)
    except ValueError:
        pass
    else:
        raise AssertionError("RED_GQ8_MOBILE_OFF_UNMODIFIED")
    print("GQ8_MOBILE_RESULT_INVERSE_AND_NEGATIVE_6_CASE_PASS")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("command", choices=("selftest", "patch-file", "prepare", "verify"))
    ap.add_argument("--source", type=Path)
    ap.add_argument("--out", type=Path)
    ap.add_argument("--off", action="store_true")
    ap.add_argument("--base", type=Path)
    ap.add_argument("--place", type=Path)
    args = ap.parse_args()
    if args.command == "selftest":
        selftest()
    elif args.command == "patch-file":
        if args.source is None or args.out is None:
            ap.error("patch-file requires --source and --out")
        raw = args.source.read_text(encoding="utf-8")
        args.out.write_text(off(raw) if args.off else select(raw), encoding="utf-8")
    elif args.command == "prepare":
        if args.base is None or args.out is None:
            ap.error("prepare requires --base and --out")
        prepare(args.base, args.out)
    elif args.command == "verify":
        if args.base is None or args.out is None or args.place is None:
            ap.error("verify requires --base --out --place")
        verify(args.base, args.out, args.place)
