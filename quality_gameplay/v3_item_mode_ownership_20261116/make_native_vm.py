#!/usr/bin/env python3
"""Emit a native Luau VM spec from the exact generated Lobby and ITEM functions.

The spec executes the real extracted author overlay, NOT a Python reimplementation.
It stubs only Roblox Player/session tables (no physical Studio).
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

from patch_sources import HOST_NAME, ITEM_NAME, MARKER


def extract_authority_functions(candidate: Path) -> tuple[str, str]:
    lobby = (candidate / HOST_NAME).read_text(encoding="utf-8")
    item = (candidate / ITEM_NAME).read_text(encoding="utf-8")
    if lobby.count(MARKER) != 1 or item.count(MARKER) != 1:
        raise ValueError("expected exactly one accepted patch in each author source")
    hook = re.search(
        r"(?m)^  session\.canCollectWorldItem=function\(actor:Player\):boolean\n"
        r"(?:.*\n)*?^  end$", lobby)
    can_use = re.search(
        r"(?ms)^local function canUse\(player:Player,session:any\):boolean\n"
        r".*?^end$", item)
    if not hook or not can_use:
        raise ValueError("cannot extract *exact* patched Luau functions")
    return hook.group(0), can_use.group(0)


def emit(candidate: Path, output: Path) -> None:
    hook, can_use = extract_authority_functions(candidate)
    harness = """--!strict
-- Exact patched source functions; actual native Luau runtime, simulated session objects.
local joined: {[number]:string}={}
local sessions: {[string]:any}={}
local function attach(session:any,mode:string)
""" + hook + """
end
""" + can_use + """
local assertions=0
local function check(yes:boolean,why:string)
 assertions+=1
 assert(yes,why)
end
local actor={UserId=101,Parent=true}
local function makeSession(mode:string)
 return {mode=mode,rules={phase="ACTIVE",castles={["101"]={alive=true}}}}
end
local team=makeSession("TEAM")
joined[101]="TEAM";sessions.TEAM=team;attach(team,"TEAM")
check(canUse(actor,team),"same live TEAM player accepts item")
joined[101]="BATTLE_ROYALE"
check(not canUse(actor,team),"stale TEAM castle while BR joined rejected")
joined[101]="TEAM"
sessions.TEAM=makeSession("TEAM")
check(not canUse(actor,team),"old session epoch rejected")
sessions.TEAM=team
team.rules.phase="FINISHED"
check(not canUse(actor,team),"post-result rejected")
team.rules.phase="ACTIVE"
actor.Parent=nil
check(not canUse(actor,team),"disconnected player rejected")
actor.Parent=true
team.rules.castles["101"].alive=false
check(not canUse(actor,team),"destroyed castle rejected")
team.rules.castles["101"].alive=true
local missing=makeSession("TEAM")
check(not canUse(actor,missing),"V3 mode without server hook fails closed")
missing.canCollectWorldItem=function() error("stale source") end
check(not canUse(actor,missing),"server hook exception fails closed")
missing.canCollectWorldItem=function() return 1 end
check(not canUse(actor,missing),"nontrue hook result fails closed")
local br=makeSession("BATTLE_ROYALE")
sessions.BATTLE_ROYALE=br;joined[101]="BATTLE_ROYALE";attach(br,"BATTLE_ROYALE")
check(canUse(actor,br),"live BR authorized")
check(not canUse(actor,team),"TEAM cross-mode excluded while BR active")
br.rules.phase="ABANDONED"
check(not canUse(actor,br),"abandoned BR rejected")
local preview={rules={phase="ACTIVE",castles={["101"]={alive=true}}}}
check(canUse(actor,preview),"standalone ITEM preview preserved")
print("NATIVE_LUAU_ITEM_MODE_GUARD", assertions, "assertions PASS")
"""
    output.write_text(harness, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    emit(args.candidate, args.out)


if __name__ == "__main__":
    main()
