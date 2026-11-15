#!/usr/bin/env python3
"""FB029: one-use authoritative revive-position ticket for original Game.

Reads genuine user-owned private FB028 .rbxlx, patches Game only, and fails closed
on parent SHA, anchors, source drift or output overwrite. This is NOT a Studio
runtime test and does not authorize official RC adoption.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
from lxml import etree

PARENT_SHA256="7981960d1f3027d7c411f7ce9de4e3e467011d59183d758cab77b2fa717d352d"
FIXED_SHA256="f43d1a0a9b5577fc3022541d929d34fa0c5fead829a43fdd20afa855b77f7511"

def sha(data:bytes)->str:
    return hashlib.sha256(data).hexdigest()

def blob(txt:str)->str:
    data=txt.encode("utf8")
    return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()

def exactly_once(s:str, a:str, b:str)->str:
    count=s.count(a)
    if count!=1:
        raise AssertionError(f"SOURCE_ANCHOR_DRIFT:{a[:90]} count={count}")
    return s.replace(a,b,1)

def patch_game(s:str)->str:
    s=exactly_once(s,
'''local fb027Deaths: {[Player]:any} = {}
local fb027Bridges: {[Player]:any} = {}''',
'''local fb027Deaths: {[Player]:any} = {}
-- FB029: hand off a one-use server-only revive position across CharacterAdded.
-- Without this, a delayed assignSpawn can overwrite Mage's frontline return.
local fb029ReviveArrival: {[Player]:any} = {}
local fb027Bridges: {[Player]:any} = {}''')
    s=exactly_once(s,
'''        local team = getTeamName(player)
        if team == "RED" or team == "BLUE" then
            root.CFrame = if RunService:IsStudio() and match.phase~="ACTIVE"
                then LobbyIsland.spawn(team)
                else map.teams[team].spawn + Vector3.new(0, 2, 0)
        elseif player:GetAttribute("P0D_LateJoinSpectator")==true then''',
'''        local team = getTeamName(player)
        -- This runs in a separate task from the Mage's LoadCharacter receipt.
        -- Consume the pending ticket in either scheduler order, exactly once.
        local reviveTicket=fb029ReviveArrival[player]
        fb029ReviveArrival[player]=nil
        player:SetAttribute("FB029ReviveSpawnApplied",nil)
        if team == "RED" or team == "BLUE" then
            if reviveTicket and RunService:IsStudio() and match.phase=="ACTIVE"
                and reviveTicket.epoch==match.serial and reviveTicket.team==team
                and serverNow()<=reviveTicket.expires then
                root.CFrame=CFrame.new(reviveTicket.pos+Vector3.new(0,4,0))
                player:SetAttribute("FB029ReviveSpawnApplied",match.serial)
            else
                root.CFrame = if RunService:IsStudio() and match.phase~="ACTIVE"
                    then LobbyIsland.spawn(team)
                    else map.teams[team].spawn + Vector3.new(0, 2, 0)
            end
        elseif player:GetAttribute("P0D_LateJoinSpectator")==true then''')
    s=exactly_once(s,
'''        local alive,oldRoot=healthy(ally)
        if not alive then
            local ok=pcall(function() ally:LoadCharacter() end)
            if not ok then return end
        end
        local model=ally.Character''',
'''        local alive,oldRoot=healthy(ally)
        if not alive then
            -- CharacterAdded may schedule assignSpawn before or after this task.
            -- A server-owned one-time ticket makes both orders land at the
            -- authentic death beacon, not at the ordinary castle spawn.
            fb029ReviveArrival[ally]={pos=floor,epoch=serial,
                team=reviveTeam,expires=serverNow()+5}
            local ok=pcall(function() ally:LoadCharacter() end)
            if not ok then fb029ReviveArrival[ally]=nil;return end
        end
        local model=ally.Character''')
    s=exactly_once(s,
'''fb027Tick=function(now:number)
    for owner,rec in pairs(fb027Deaths) do''',
'''fb027Tick=function(now:number)
    for owner,ticket in pairs(fb029ReviveArrival) do
        if owner.Parent~=Players or match.phase~="ACTIVE"
            or match.serial~=ticket.epoch or getTeamName(owner)~=ticket.team
            or now>ticket.expires then
            fb029ReviveArrival[owner]=nil
        end
    end
    for owner,rec in pairs(fb027Deaths) do''')
    s=exactly_once(s,
'''    fb027Cleanup(player)
    fb027DestroyBeacon(player)
    fb026AltLast[player]=nil''',
'''    fb027Cleanup(player)
    fb027DestroyBeacon(player)
    fb029ReviveArrival[player]=nil
    fb026AltLast[player]=nil''')
    assert s.count("remote.OnServerEvent:Connect(")==1
    assert s.count("fb029ReviveArrival")>=7
    return s

def entries(root):
    all_items=[]
    for item in root.xpath("//Item"):
        p=item.find("Properties")
        if p is None:continue
        n=p.find('string[@name="Name"]')
        v=next((v for v in p if v.get("name")=="Source"),None)
        if n is not None and v is not None:
            all_items.append((n.text or "",v))
    if len(all_items)!=82 or len({n for n,_ in all_items})!=82:
        raise AssertionError("RC82_SCRIPT_INVENTORY_UNEXPECTED")
    return all_items

def apply(source:Path,target:Path):
    if target.exists(): raise FileExistsError(target)
    raw=source.read_bytes()
    if sha(raw)!=PARENT_SHA256: raise AssertionError("PARENT_PLACE_SHA_MISMATCH")
    parser=etree.XMLParser(resolve_entities=False,no_network=True,load_dtd=False)
    root=etree.fromstring(raw,parser)
    before={n:element.text or "" for n,element in entries(root)}
    assert list(before).count("Game")==1
    game=next(element for name,element in entries(root) if name=="Game")
    game.text=patch_game(game.text or "")
    after={n:element.text or "" for n,element in entries(root)}
    changed=[n for n in before if before[n]!=after[n]]
    if changed!=["Game"]:
        raise AssertionError("GAME_ONLY_SOURCE_CONTRACT_FAILED")
    target.write_bytes(etree.tostring(root,encoding="utf-8",xml_declaration=False,pretty_print=True))
    verified={n:element.text or "" for n,element in entries(etree.parse(str(target),parser))}
    if verified!=after: raise AssertionError("WRITTEN_PLACE_SOURCE_DRIFT")
    actual=sha(target.read_bytes())
    if actual!=FIXED_SHA256:
        target.unlink()
        raise AssertionError(f"EXACT_OUTPUT_SHA_MISMATCH: {actual}")
    return {"source_count":82,"changed":["Game"],"unchanged_sources":81,
        "parent":PARENT_SHA256,"result":actual,
        "before_game_blob":blob(before["Game"]),"after_game_blob":blob(after["Game"]),
        "native_luau":"NOT_RUN","studio":"NOT_RUN","official_rc_adopted":False}

if __name__=="__main__":
    cli=argparse.ArgumentParser()
    cli.add_argument("--parent",type=Path,required=True)
    cli.add_argument("--out",type=Path,required=True)
    args=cli.parse_args()
    print(json.dumps(apply(args.parent,args.out),ensure_ascii=False,indent=2))
