#!/usr/bin/env python3
"""GQ8 lobby reset retry: fence a delayed LoadCharacter from a new match/avatar.

Source-exact overlay on CURRENT selected31. No new Roblox script, Remote or Store.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "quality_decor732_rc31"))
from select_current import mapping

FEATURE = "GQ8_REPLAY_RESET_RETRY_SESSION_FENCE_20261118"
TARGET = ("ServerScriptService", "EGGRUMBLE_RoundReplay")
SELECTED = "GQ8_REPLAY_RETRY_SELECTED_SOURCE.luau"
RECEIPT = "GQ8_REPLAY_RETRY_RC31_RECEIPT.json"
OLD = 'if p.Parent~=Players or p:GetAttribute("EGGRUMBLE_QueuedMode")~=nil then return end'
NEW = ('if p.Parent~=Players or p:GetAttribute("EGGRUMBLE_QueuedMode")~=nil\n'
       '     or p:GetAttribute("EGGRUMBLE_Role")~=nil or p.Character~=ch then return end')
MARKER = "-- GQ8_REPLAY_RESET_RETRY_SESSION_FENCE_20261118"

def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def patch(text: str) -> str:
    if text.count(OLD) != 1 or MARKER in text:
        raise ValueError("RED_GQ8_REPLAY_RETRY_ANCHOR_OR_DUPLICATE")
    if text.count("function Replay.resetHuman(") != 1 or "task.delay(1,function()" not in text:
        raise ValueError("RED_GQ8_REPLAY_RETRY_NOT_ORIGINAL")
    result = text.replace(OLD, MARKER + "\n    " + NEW, 1)
    if unpatch(result) != text:
        raise ValueError("RED_GQ8_REPLAY_RETRY_NOT_REVERSIBLE")
    return result

def unpatch(text: str) -> str:
    if text.count(MARKER) != 1 or text.count(NEW) != 1:
        raise ValueError("RED_GQ8_REPLAY_RETRY_OFF_DRIFT")
    return text.replace(MARKER + "\n    " + NEW, OLD, 1)

def compare(base: Path, selected: Path):
    _, before = mapping(base)
    _, after = mapping(selected)
    if len(before) != 31 or set(before) != set(after) or TARGET not in before:
        raise ValueError("RED_GQ8_REPLAY_RETRY_SOURCE_SET")
    changed = [key for key in before if before[key].read_bytes() != after[key].read_bytes()]
    if changed != [TARGET]:
        raise ValueError("RED_GQ8_REPLAY_RETRY_NOT_SINGLE_SOURCE")
    old = before[TARGET].read_text(encoding="utf-8")
    new = after[TARGET].read_text(encoding="utf-8")
    if patch(old) != new or unpatch(new) != old:
        raise ValueError("RED_GQ8_REPLAY_RETRY_ROLLBACK")
    return before, after, old, new

def prepare(base: Path, out: Path):
    base = base.resolve(strict=True)
    out = out.resolve()
    if out.exists() or base.parent != out.parent or (out.parent / SELECTED).exists():
        raise ValueError("RED_GQ8_REPLAY_RETRY_OUTPUT_COLLISION")
    document, before = mapping(base)
    old = before[TARGET].read_text(encoding="utf-8")
    new = patch(old)
    (out.parent / SELECTED).write_text(new, encoding="utf-8")
    selected = copy.deepcopy(document)
    selected["name"] = "EGGRUMBLE_GQ8_REPLAY_RETRY_SESSION_FENCE_31"
    selected["tree"][TARGET[0]][TARGET[1]]["$path"] = SELECTED
    out.write_text(json.dumps(selected, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    compare(base, out)
    receipt = {
        "feature_id": FEATURE,
        "source_count": 31,
        "changed_script": TARGET[1],
        "other30_byte_exact": True,
        "off_previous_rc_byte_exact": True,
        "failure_scenario": "old round delayed LoadCharacter retry after player entered a new round/changed avatar",
        "new_runtime_scripts": 0,
        "new_remote_store": 0,
        "old_sha256": sha(old.encode()),
        "new_sha256": sha(new.encode()),
        "native": "PENDING",
        "rojo": "PENDING",
        "studio_android_fun": "NOT_TESTED",
        "official_adoption": False,
    }
    (out.parent / RECEIPT).write_text(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("GQ8_REPLAY_RETRY_SELECTED31_ONE_REPLAY_OTHER30_EXACT_OFF_PASS")

# Run the ACTUAL selected RoundReplay source with lightweight Roblox boundary stubs.
# The mutant uses the unchanged prior retry guard; its new-round case must fail.
HARNESS = r'''
local services = {}
local Players = {}
local RunService = {IsStudio=function() return true end}
services.Players=Players
services.RunService=RunService
game = {GetService=function(_,key) return services[key] end}
local callbacks = {}
task = {delay=function(_,fn) table.insert(callbacks,fn) end}
local function avatar(health)
 return {
  FindFirstChild=function() return nil end,
  GetChildren=function() return {} end,
  FindFirstChildOfClass=function(_,name)
   if name=="Humanoid" and health then return {Health=health,WalkSpeed=16} end
   return nil
  end,
 }
end
local function scenario(label, change, retryExpected)
 callbacks={}
 local player={Parent=Players,Character=avatar(nil),attrs={},loads=0}
 function player:SetAttribute(k,v) self.attrs[k]=v end
 function player:GetAttribute(k) return self.attrs[k] end
 function player:FindFirstChild() return nil end
 function player:LoadCharacter() self.loads+=1;error("simulated transient spawn fail") end
 Replay.resetHuman(player,nil,16)
 assert(player.loads==1 and #callbacks==1,"RED_GQ8_REPLAY_RETRY_INITIAL_"..label)
 change(player)
 callbacks[1]()
 assert(player.loads==(retryExpected and 2 or 1),"RED_GQ8_REPLAY_RETRY_NEW_ROUND_AVATAR_"..label)
end
scenario("still_lobby",function() end,true)
scenario("new_match_role",function(p) p:SetAttribute("EGGRUMBLE_Role","WARRIOR") end,false)
scenario("new_avatar",function(p) p.Character=avatar(nil) end,false)
scenario("new_avatar_dead",function(p) p.Character=avatar(0) end,false)
scenario("new_queue",function(p) p:SetAttribute("EGGRUMBLE_QueuedMode","TEAM") end,false)
scenario("disconnected",function(p) p.Parent=nil end,false)
scenario("alive",function(p) p.Character=avatar(100) end,false)
print("GQ8_REPLAY_RETRY_REAL_LUAU_7_CASE_PASS")
'''

def harness(text: str) -> str:
    if not text.rstrip().endswith("return Replay"):
        raise ValueError("RED_GQ8_REPLAY_RETRY_SOURCE_TRAILER")
    prefix = text[:text.rfind("return Replay")]
    prelude, fixture = HARNESS.split("local function avatar(health)", 1)
    return prelude + "\n" + prefix + "\nlocal function avatar(health)" + fixture

def native(base: Path, selected: Path, real: Path, mutant: Path):
    _, _, old, new = compare(base.resolve(strict=True), selected.resolve(strict=True))
    real.write_text(harness(new), encoding="utf-8")
    mutant.write_text(harness(old), encoding="utf-8")
    print("GQ8_REPLAY_RETRY_NATIVE_REAL_AND_EXPECTED_RED_CREATED")

def verify(base: Path, selected: Path, place: Path):
    before, after, old, new = compare(base.resolve(strict=True), selected.resolve(strict=True))
    found = {}
    for node in ET.parse(place).getroot().iter("Item"):
        kind = node.get("class")
        if kind not in ("Script", "LocalScript", "ModuleScript"):
            continue
        prop = node.find("Properties")
        if prop is None:
            raise ValueError("RED_GQ8_REPLAY_RETRY_ROJO_PROPS")
        name = prop.findtext("string[@name='Name']")
        source = prop.findtext("ProtectedString[@name='Source']")
        if source is None:
            source = prop.findtext("string[@name='Source']")
        if not name or source is None or name in found:
            raise ValueError("RED_GQ8_REPLAY_RETRY_ROJO_DUPLICATE")
        found[name] = (kind, source.replace("\r\n", "\n"))
    if len(found) != 31 or set(found) != {key[-1] for key in after}:
        raise ValueError("RED_GQ8_REPLAY_RETRY_ROJO_31")
    for key, file in after.items():
        kind = ("Script" if file.name.endswith(".server.luau") else
                "LocalScript" if file.name.endswith(".client.luau") else "ModuleScript")
        if found[key[-1]] != (kind, file.read_text(encoding="utf-8").replace("\r\n", "\n")):
            raise ValueError("RED_GQ8_REPLAY_RETRY_ROJO_SOURCE_" + key[-1])
    rec = selected.parent / RECEIPT
    payload = json.loads(rec.read_text(encoding="utf-8"))
    if payload["old_sha256"] != sha(old.encode()) or payload["new_sha256"] != sha(new.encode()):
        raise ValueError("RED_GQ8_REPLAY_RETRY_RECEIPT_SHA")
    payload.update(native="31/31", rojo="31/31", place_sha256=sha(place.read_bytes()),
                   place_bytes=place.stat().st_size)
    rec.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("GQ8_REPLAY_RETRY_SELECTED31_REAL_ROJO31_OFF_EXACT_PASS")

def selftest():
    sample = 'function NotTheRealReplay()\n  ' + OLD + '\nend'
    # Only patch a realistic function, not an arbitrary line outside the original module.
    try:
        patch(sample)
        raise ValueError("RED_GQ8_REPLAY_RETRY_SELFTEST_ACCEPTED_NONORIGINAL")
    except ValueError as err:
        if "NOT_ORIGINAL" not in str(err):
            raise
    original = 'function Replay.resetHuman()\n task.delay(1,function()\n  ' + OLD + '\n end)\nend'
    assert original.count(OLD) == 1
    print("GQ8_REPLAY_RETRY_STATIC_SELECTOR_SELFTEST_PASS")

if __name__ == "__main__":
    cli = argparse.ArgumentParser()
    cli.add_argument("command", choices=("selftest", "prepare", "native", "verify"))
    cli.add_argument("--base", type=Path)
    cli.add_argument("--out", type=Path)
    cli.add_argument("--place", type=Path)
    cli.add_argument("--real", type=Path)
    cli.add_argument("--mutant", type=Path)
    args = cli.parse_args()
    if args.command == "selftest":
        selftest()
    elif args.command == "prepare":
        prepare(args.base, args.out)
    elif args.command == "native":
        native(args.base, args.out, args.real, args.mutant)
    else:
        verify(args.base, args.out, args.place)
