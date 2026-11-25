#!/usr/bin/env python3
"""Source-select ORIGINAL GQ522 Builder wall/Tool into one EXISTING current V3 Host.

Reuse the two exact immutable original author's modules as local functions of
existing Host, not 2 new Script instances. Exactly 31 scripts remain; all
other 30 bytes identical, inverse OFF restores original Host byte-exact.
Requires actual latest original #499 selected project. No main/RC writes.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "quality_zombie582_rc31"))
from select_original_zombie582 import scan, git_blob, digest

AUTHOR_HEAD = "fd7e23feced51ea1d22559f0b6adb42bc5921217"
BUILDER_BLOB = "ed2c7b8fb421920083dd014693e9ae2ab9b206a8"
POLICY_BLOB = "87b1db809435f0e13b6a356f269daf96a437a9a6"
HOST = ("ServerScriptService", "EGGRUMBLE_LobbyCastleModesPreview")
REQUIRE = 'local SevenRoleCombat=require(script.Parent:WaitForChild("EGGRUMBLE_SevenRoleCombat"))'
EQUIP = 'SevenRoleCombat.equip(session,p,role)'
CLOSE = 'if session.world.Parent then session.world:Destroy() end'
POLICY_REQUIRE = 'local Policy=require(script.Parent:WaitForChild("EGGRUMBLE_BuilderPlacementPolicy"))'
STAMP = "-- GQ522_ORIGINAL_BUILDER_WALL_ONLY_INLINE_RC31"
SELECTED = "GQ522_WALL_EXISTING_HOST_SELECTED.server.luau"
RECEIPT = "GQ522_WALL_RC31_RECEIPT.json"
PROJECT = "GQ522_WALL_SELECTED31.project.json"

def exact_author(builder: Path, policy: Path):
    a, b = builder.read_bytes(), policy.read_bytes()
    if git_blob(a) != BUILDER_BLOB or git_blob(b) != POLICY_BLOB:
        raise ValueError("RED_GQ522_ORIGINAL_AUTHOR_BLOB_DRIFT")
    aa, bb = a.decode("utf8"), b.decode("utf8")
    if not (aa.startswith("--!strict\n") and bb.startswith("--!strict\n")):
        raise ValueError("RED_GQ522_STRICT_AUTHOR_DRIFT")
    return aa, bb

def strip_module(text: str, final: str) -> str:
    if not text.startswith("--!strict\n") or not text.rstrip().endswith(final):
        raise ValueError("RED_AUTHOR_MODULE_RETURN_ANCHOR")
    body = text[len("--!strict\n"):].rstrip()
    lines = body.splitlines()
    # "return Policy..." inside original helper functions is normal; only
    # the exact final module-level return statement is removed.
    if not lines or lines[-1].strip() != final or sum(
        line.strip() == final for line in lines) != 1:
        raise ValueError("RED_AUTHOR_MODULE_RETURN_COUNT")
    return "\n".join(lines[:-1]).rstrip() + "\n"

def inline_source(builder: str, policy: str) -> str:
    pp = strip_module(policy, "return Policy")
    bb = strip_module(builder, "return Build")
    if bb.count(POLICY_REQUIRE) != 1:
        raise ValueError("RED_GQ522_POLICY_REQUIRE_DRIFT")
    bb = bb.replace(POLICY_REQUIRE, "-- GQ522 Policy is inlined below (original source preserved)", 1)
    if "function Build.equip(" not in bb or "function Build.clear(" not in bb:
        raise ValueError("RED_GQ522_AUTHOR_TOOL_OR_CLEAR_MISSING")
    if "Build.DEFAULT_ENABLED=false" not in bb or 'Build.place(session,p,kind,true)' not in bb:
        raise ValueError("RED_GQ522_DEFAULT_OFF_OR_SERVER_TOOL_MISSING")
    if 'if typeof(session.isCurrentHuman)~="function" then return nil,nil end' not in bb:
        raise ValueError("RED_GQ522_CURRENT_SESSION_FENCE_MISSING")
    return (STAMP + "\n" + "local BuilderConstruction\n"
            + "do\n" + pp + bb
            + "\nBuilderConstruction=Build\nend\n")

HOOK = ('\n   if role=="BUILDER" then\n'
        '    BuilderConstruction.equip(session,p,true,false) -- only WALL, BRIDGE remains OFF\n'
        '   end')

def select_host(src: str, builder: str, policy: str):
    if STAMP in src or "BuilderConstruction.equip(session,p,true,false)" in src:
        raise ValueError("RED_GQ522_ALREADY_SELECTED")
    if src.count(REQUIRE) != 1 or src.count(EQUIP) != 2 or src.count(CLOSE) != 1:
        raise ValueError("RED_GQ522_CURRENT_HOST_ORIGIN_DRIFT")
    if "session.isCurrentHuman=function" not in src:
        raise ValueError("RED_GQ522_NO_CURRENT_HUMAN_FENCE")
    block = inline_source(builder, policy)
    selected = src.replace(REQUIRE, REQUIRE + "\n" + block, 1)
    selected = selected.replace(EQUIP, EQUIP + HOOK)
    selected = selected.replace(CLOSE, "BuilderConstruction.clear(session)\n  " + CLOSE, 1)
    if selected.count("BuilderConstruction.equip(session,p,true,false)") != 2:
        raise ValueError("RED_GQ522_NO_TWO_AUTHOR_EQUIP_HOOKS")
    if selected.count("BuilderConstruction.clear(session)") != 1:
        raise ValueError("RED_GQ522_NO_CLEANUP")
    if rollback(selected, block) != src:
        raise ValueError("RED_GQ522_OFF_NOT_BYTE_EXACT")
    return selected, block

def rollback(src: str, block: str):
    if (src.count(REQUIRE+"\n"+block) != 1
        or src.count(EQUIP+HOOK) != 2
        or src.count("BuilderConstruction.clear(session)\n  "+CLOSE) != 1):
        raise ValueError("RED_GQ522_INVERSE_SHAPE_DRIFT")
    src = src.replace("BuilderConstruction.clear(session)\n  "+CLOSE, CLOSE, 1)
    src = src.replace(EQUIP+HOOK, EQUIP)
    src = src.replace(REQUIRE+"\n"+block, REQUIRE, 1)
    return src

def inputs(base:Path, builder:Path, policy:Path):
    original, files = scan(base)
    if HOST not in files:
        raise ValueError("RED_GQ522_NO_EXISTING_HOST")
    author_builder, author_policy = exact_author(builder, policy)
    source_before = files[HOST].read_bytes()
    source_after, block = select_host(source_before.decode("utf8"), author_builder, author_policy)
    return original, files, source_before, source_after.encode("utf8"), block

def prepare(base:Path, out:Path, builder:Path, policy:Path):
    base=base.resolve(strict=True);out=out.resolve()
    if out.exists() or out == base or out.parent != base.parent:
        raise ValueError("RED_GQ522_OUTPUT_NOT_FRESH_SIBLING")
    obj, before, raw, modified, block = inputs(base,builder,policy)
    selected_path=out.parent/SELECTED
    if selected_path.exists(): raise ValueError("RED_GQ522_HOST_OUTPUT_EXISTS")
    selected_path.write_bytes(modified)
    candidate=copy.deepcopy(obj)
    candidate["tree"][HOST[0]][HOST[1]]["$path"]=SELECTED
    out.write_text(json.dumps(candidate,indent=2,ensure_ascii=False)+"\n")
    _, after=scan(out)
    if set(after) != set(before) or any(before[k].read_bytes()!=after[k].read_bytes()
        for k in before if k!=HOST):
        raise ValueError("RED_GQ522_OTHER30_SOURCES_CHANGED")
    if sum(before[k].read_bytes()!=after[k].read_bytes() for k in before)!=1:
        raise ValueError("RED_GQ522_NOT_ONLY_HOST_DIFF")
    if rollback(modified.decode(),block).encode()!=raw:
        raise ValueError("RED_GQ522_BAD_ROLLBACK")
    receipt=dict(feature_id="GQ_BUILDER_WALL_SERVER_TOOL_522",author_head=AUTHOR_HEAD,
         builder_blob=BUILDER_BLOB,policy_blob=POLICY_BLOB,
         source_count=31,only_changed_existing_script="EGGRUMBLE_LobbyCastleModesPreview",
         other30_byte_exact=True,one_host_inverse_off_exact=True,
         original_host_sha256=digest(raw),selected_host_sha256=digest(modified),
         no_new_runtime_script=True,bridge_enabled=False,wall_enabled=True,
         prior_author_original=True,studio_android_art_fun_owner="NOT_TESTED",
         source_gate="PREMERGE_ONLY",formal_rc_adopted=False)
    (out.parent/RECEIPT).write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
    print("GQ522_CURRENT31_ONE_EXISTING_HOST_WALL_ONLY_AUTHOR_SOURCE_OFF_EXACT_PASS")

def verify(base:Path,out:Path,builder:Path,policy:Path,place:Path):
    _,before,raw,expected,block=inputs(base,builder,policy)
    _,after=scan(out)
    if set(before)!=set(after) or after[HOST].read_bytes()!=expected:
        raise ValueError("RED_GQ522_SELECTED_HOST_DRIFT")
    if any(before[k].read_bytes()!=after[k].read_bytes() for k in before if k!=HOST):
        raise ValueError("RED_GQ522_OTHER30_CHANGED")
    if rollback(expected.decode(),block).encode()!=raw:
        raise ValueError("RED_GQ522_REVERSE_BAD")
    actual={}
    for item in ET.parse(place).getroot().iter("Item"):
        typ=item.attrib.get("class")
        if typ not in ("Script","ModuleScript","LocalScript"):continue
        props=item.find("Properties")
        if props is None:raise ValueError("RED_GQ522_NO_PROPS")
        name=props.findtext("string[@name='Name']")
        source=props.findtext("ProtectedString[@name='Source']")
        if source is None:source=props.findtext("string[@name='Source']")
        if not name or source is None or name in actual:
            raise ValueError("RED_GQ522_DUPLICATE_SCRIPT")
        actual[name]=(typ,source.replace("\r\n","\n"))
    if len(actual)!=31 or {r[-1] for r in before}!=set(actual):
        raise ValueError("RED_GQ522_ROJO_NAMES_OR_COUNT")
    for route,path in after.items():
        typ=("Script" if path.name.endswith(".server.luau") else
             "LocalScript" if path.name.endswith(".client.luau") else "ModuleScript")
        if actual[route[-1]]!=(typ,path.read_text(encoding="utf8").replace("\r\n","\n")):
            raise ValueError("RED_GQ522_ROJO_SOURCE_CLASS_"+route[-1])
    receipt_path=out.parent/RECEIPT
    rec=json.loads(receipt_path.read_text())
    if rec["original_host_sha256"]!=digest(raw) or rec["selected_host_sha256"]!=digest(expected):
        raise ValueError("RED_GQ522_RECEIPT_HASH_DRIFT")
    rec.update(real_rojo_source_class_exact="31/31",place_sha256=digest(place.read_bytes()),
               place_bytes=place.stat().st_size)
    receipt_path.write_text(json.dumps(rec,indent=2,sort_keys=True)+"\n")
    print("GQ522_CURRENT31_ACTUAL_ROJO31_SOURCE_CLASS_WALL_ONLY_EXACT_PASS",rec["place_bytes"])

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("action",choices=("prepare","verify"))
    for key in ("base","out","builder","policy","place"):
        ap.add_argument("--"+key,type=Path)
    a=ap.parse_args()
    for field in ("base","out","builder","policy"):
        if getattr(a,field) is None:ap.error("missing --"+field)
    if a.action=="prepare":prepare(a.base,a.out,a.builder,a.policy)
    else:
        if a.place is None:ap.error("verify requires --place")
        verify(a.base,a.out,a.builder,a.policy,a.place)
