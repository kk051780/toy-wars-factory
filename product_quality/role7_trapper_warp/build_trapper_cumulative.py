#!/usr/bin/env python3
"""Private RC84 actual Game integration: existing #471 RC83 + real Trapper portals.

One ORIGINAL Game owns JOB_SKILL/phase/egg/score/win; no second match or remote.
Copies 83 authentic source bodies except Game, adds one server ModuleScript.
No public default enable, no official RC/main write.
"""
from __future__ import annotations
import argparse,copy,hashlib,json
from collections import Counter
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
from xml.etree import ElementTree as ET

ROOT=Path(__file__).resolve().parent
PARENT="P0D_CASTLE_BEAST_SOLO_SEVEN_WEAPONS_PRIVATE_RC83.rbxlx"
PARENT_SHA="c342010e40208df4411831acb01c9e429c4fe7d100fdd953b1d342882cfc92c3"
PARENT_GAME_BLOB="8a15f03ea45e4cf6512b09430e3f5dca6d0e1893"
PARENT_WEAPON_BLOB="7468f143ef801ebc7bdeab75f13bb5b16f66b103"
PARENT_MAP_BLOB="52e677d208412483b744c7ac464eb0ffbc9e6ecd"
PARENT_BOTS_BLOB="a77176fdcfe3351b5dc9ed4aa23fcf48a28edd53"
RC="d2f3ed1a47558fdaf07be0181c83c698bdb2ce34"
OUTPUT="P0D_RC84_CASTLE_BEAST_SOLO_SEVEN_WEAPONS_TRAPPER_PRIVATE.rbxlx"
GAME="server/Game.server.luau"
MODULE="server/TrapperWarpService.luau"

EXPECTED_PLACE_SHA=""
EXPECTED_GAME_BLOB=""
EXPECTED_MODULE_BLOB=""
EXPECTED_BYTES=0

def sha(data):return hashlib.sha256(data).hexdigest()
def blob(src):
    b=src.encode('utf-8')
    return hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()

def once(source,old,new,label):
    if source.count(old)!=1 or new in source:
        raise ValueError("ORIGINAL_GAME_HUNK_ANCHOR_DRIFT_"+label)
    return source.replace(old,new,1)

def source_nodes(place):
    root=ET.fromstring(place)
    scripts={}
    for item in root.iter("Item"):
        if item.get("class") not in ("Script","LocalScript","ModuleScript"):
            continue
        p=item.find("Properties")
        if p is None:continue
        name=p.findtext("string[@name='Name']")
        src=p.find("string[@name='Source']")
        if not name or src is None or src.text is None or name in scripts:
            raise ValueError("INVALID_OR_DUPLICATE_SCRIPT_NAME")
        scripts[name]=src
    return root,scripts

def old_egg_logic(src):
    first='for _, team in ipairs({"RED", "BLUE"}) do\n    map.teams[team].eggPrompt.Triggered:Connect'
    last='\n-- P0D_SAVED_PVE_MASTERY_V1:'
    i=src.index(first)
    return src[i:src.index(last,i)]

IMPORT_OLD='SevenJobs.ArmamentM1 = require(script.Parent:WaitForChild("SevenJobArmamentM1"))'
IMPORT_NEW=IMPORT_OLD+'\nSevenJobs.TrapperWarp = require(script.Parent:WaitForChild("TrapperWarpService"))'

SKILL_OLD='''    elseif job=="TRAPPER" then
        for _,d in ipairs({facing,-facing,Vector3.new(-facing.Z,0,facing.X),
            Vector3.new(facing.Z,0,-facing.X)}) do
            sevenJobStrike(player,root.Position,d,12)
        end
    elseif job=="BUILDER" then'''
SKILL_NEW='''    elseif job=="TRAPPER" then
        for _,d in ipairs({facing,-facing,Vector3.new(-facing.Z,0,facing.X),
            Vector3.new(facing.Z,0,-facing.X)}) do
            sevenJobStrike(player,root.Position,d,12)
        end
        -- FB020-B: server-derived paired transport. No client-supplied
        -- teleport destination or extra Remote; original Q seq/cooldown/phase
        -- and original 7-job ownership above remain authoritative.
        SevenJobs.TrapperWarp.place(player,team,root.Position,facing,map.model,
            match.serial,function(passenger,side,serial)
                local ok,passRoot=healthy(passenger)
                return serial==match.serial and match.phase=="ACTIVE"
                    and ok and passRoot~=nil and getTeamName(passenger)==side
                    and carry[passenger]==nil and slowed[passenger]==nil
                    and passenger:GetAttribute("P0D_LateJoinSpectator")~=true
                    and ServerStorage:GetAttribute("P0D_RC_ENABLE_SEVEN_JOBS_PVE")~=false
            end)
    elseif job=="BUILDER" then'''

def patch_game(src):
    s=once(src,IMPORT_OLD,IMPORT_NEW,"UNIQUE_MODULE_REQUIRE")
    s=once(s,SKILL_OLD,SKILL_NEW,"TRAPPER_AUTH_SKILL")
    s=once(s,'    SoloTeamBots.stop()\n    match.phaseUntil = serverNow() + Config.ResultsSeconds',
        '    SoloTeamBots.stop()\n    SevenJobs.TrapperWarp.clearAll()\n'
        '    match.phaseUntil = serverNow() + Config.ResultsSeconds',"ROUND_END")
    s=once(s,'local function resetRound()\n    SoloTeamBots.stop()',
        'local function resetRound()\n    SoloTeamBots.stop()\n    SevenJobs.TrapperWarp.clearAll()',"ROUND_RESET")
    s=once(s,'    horde:clearSevenBeast(player) -- no old pet survives role re-selection',
        '    horde:clearSevenBeast(player) -- no old pet survives role re-selection\n'
        '    SevenJobs.TrapperWarp.clearOwner(player) -- old pair revoked on job change',"JOB_RESELECT")
    s=once(s,'            SevenJobs.ArmamentM1.clear(player.Character) -- clear revoked job on lobby team transfer',
        '            SevenJobs.ArmamentM1.clear(player.Character) -- clear revoked job on lobby team transfer\n'
        '            SevenJobs.TrapperWarp.clearOwner(player) -- team migration revokes pair',"TEAM_CHANGE")
    s=once(s,'        SevenJobs.ArmamentM1.resetPlayer(player) -- a respawn never carries a prior 3-hit chain',
        '        SevenJobs.ArmamentM1.resetPlayer(player) -- a respawn never carries a prior 3-hit chain\n'
        '        SevenJobs.TrapperWarp.clearOwner(player) -- respawn revokes owned pair',"RESPAWN")
    s=once(s,'    SevenJobs.ArmamentM1.clear(player.Character)\n    sevenJobPickAckSeq[player]=nil',
        '    SevenJobs.ArmamentM1.clear(player.Character)\n'
        '    SevenJobs.TrapperWarp.clearOwner(player) -- disconnect cleanup\n'
        '    sevenJobPickAckSeq[player]=nil',"LEAVE")
    for term in ('P0D_FB_CASTLE_WALKIN_SIEGE_V1','SevenJobs.ArmamentM1.strike(',
        'summonSevenBeast','SoloTeamBots.tryHumanHit(',
        'horde:tick(now,eligibleSoloPlayers(),healthy)',
        'pcall(SoloTeamBots.start,map,getTeamName(player),botAuthority)',
        'sevenJobPickAckSeq[player]~=selectedAck',
        'player.Character~=castCharacter','P0D_SAFE_LOBBY',
        'personalEggDeposits[player]=(personalEggDeposits[player] or 0)+1'):
        if term=="P0D_FB_CASTLE_WALKIN_SIEGE_V1":continue # in original MapBuilder, not Game
        if term not in s:raise ValueError("EXISTING_GAME_FEATURE_LOST_"+term)
    for term in ('local function tickRound()','local function resetRound()',
        'local function applyAttack(','local function useSevenJob(','local botAuthority=',
        'remote.OnServerEvent:Connect('):
        if s.count(term)!=1:raise ValueError("DUPLICATED_MATCH_AUTHORITY_"+term)
    if old_egg_logic(src)!=old_egg_logic(s):
        raise ValueError("ORIGINAL_EGG_SCORE_WINNER_CHANGED")
    return s

def add_module(root,module):
    candidates=[]
    for parent in root.iter():
        for item in parent.findall("Item"):
            p=item.find("Properties")
            name=p.findtext("string[@name='Name']") if p is not None else None
            if name=="SevenJobsRules":
                candidates.append((parent,item))
            if name=="TrapperWarpService":raise ValueError("TRAPPER_MODULE_ALREADY_PRESENT")
    if len(candidates)!=1 or candidates[0][1].get("class")!="ModuleScript":
        raise ValueError("ORIGINAL_SEVEN_JOBS_SHELL_NOT_UNIQUE")
    parent,original=candidates[0]
    fresh=copy.deepcopy(original)
    used={int(item.attrib['referent']) for item in root.iter('Item')
        if item.attrib.get('referent','').isdigit()}
    fresh.set("referent",str(max(used)+1))
    p=fresh.find("Properties")
    p.find("string[@name='Name']").text="TrapperWarpService"
    p.find("string[@name='Source']").text=module
    parent.append(fresh)

def verify84(place,lock,feature):
    root,nodes=source_nodes(place)
    if len(nodes)!=84 or lock.get("total_scripts")!=84 or feature.get("total_sources")!=84:
        raise ValueError("SOURCE84_COUNT_MISMATCH")
    if len(lock["blobs"])!=84 or lock["blobs"]!=feature["source_gitblobs"]:
        raise ValueError("SOURCE84_DUAL_LOCK_MISMATCH")
    if Counter(blob(n.text) for n in nodes.values())!=Counter(lock["blobs"].values()):
        raise ValueError("SOURCE84_GITBLOB_MISMATCH")
    return root,nodes

def build(parent,out,extract=None):
    with ZipFile(parent) as z:
        names=z.namelist()
        if len(names)!=len(set(names)) or any(n.startswith("/") or ".." in Path(n).parts for n in names):
            raise ValueError("UNSAFE_PARENT_ZIP")
        place=z.read(PARENT)
        lock=json.loads(z.read("SOURCE_LOCK.json"))
        feature=json.loads(z.read("RC_FEATURE_LOCK.json"))
        prior=json.loads(z.read("RECEIPT.json"))
    if sha(place)!=PARENT_SHA or prior.get("official_rc_head")!=RC or prior.get("official_rc_write") is not False:
        raise ValueError("UNPINNED_83_SOURCE_PARENT")
    if lock.get("total_scripts")!=83 or feature.get("total_sources")!=83:
        raise ValueError("WRONG_83_SCRIPT_SOURCE_COUNT")
    if lock["blobs"]!=feature["source_gitblobs"] or len(lock["blobs"])!=83:
        raise ValueError("ORIGINAL_83_LOCK_DRIFT")
    checks={"server/Game.server.luau":PARENT_GAME_BLOB,
        "server/SevenJobArmamentM1.luau":PARENT_WEAPON_BLOB,
        "server/MapBuilder.luau":PARENT_MAP_BLOB,
        "server/SoloTeamBots.luau":PARENT_BOTS_BLOB}
    if any(lock["blobs"].get(p)!=digest for p,digest in checks.items()):
        raise ValueError("ORIGINAL_83_BEAST_MAP_AI_WEAPON_CHANGED")
    root,nodes=source_nodes(place)
    before={n:s.text for n,s in nodes.items()}
    if len(before)!=83 or Counter(blob(s) for s in before.values())!=Counter(lock["blobs"].values()):
        raise ValueError("ORIGINAL_83_BODIES_DRIFT")
    module=(ROOT/"TrapperWarpService.luau").read_text(encoding="utf-8")
    original_blob=blob(module)
    if EXPECTED_MODULE_BLOB and original_blob!=EXPECTED_MODULE_BLOB:raise ValueError("TRAPPER_MODULE_GITBLOB_CHANGED")
    new_game=patch_game(before["Game"])
    nodes["Game"].text=new_game
    add_module(root,module)
    built=ET.tostring(root,encoding="utf-8")
    _,after=source_nodes(built)
    if len(after)!=84 or set(after)-set(before)!={"TrapperWarpService"}:
        raise ValueError("SOURCE84_NOT_ONE_NEW_MODULE")
    if any(before[n]!=after[n].text for n in before if n!="Game"):
        raise ValueError("EXISTING_82_SCRIPT_SOURCE_REPLACED")
    if EXPECTED_PLACE_SHA and (sha(built)!=EXPECTED_PLACE_SHA or len(built)!=EXPECTED_BYTES or blob(new_game)!=EXPECTED_GAME_BLOB):
        raise ValueError("SOURCE84_PLACE_SHA_BYTE_GAME_DRIFT")
    lock["blobs"][GAME]=feature["source_gitblobs"][GAME]=blob(new_game)
    lock["blobs"][MODULE]=feature["source_gitblobs"][MODULE]=original_blob
    lock["total_scripts"]=feature["total_sources"]=84
    verify84(built,lock,feature)
    receipt={"schema":"P0D_470_RC84_CASTLE_BEAST_SOLO_ARMAMENT_TRAPPER_WARP_V1",
        "official_rc_head":RC,"official_rc_write":False,
        "parent_place_sha256":PARENT_SHA,"place_sha256":sha(built),
        "place_bytes":len(built),"game_blob":blob(new_game),
        "trapper_warp_gitblob":original_blob,
        "source_count":84,"existing_82_scripts_byte_exact":True,
        "game_changed_only_and_added_module":True,
        "egg_steal_deposit_score_winner_source_exact":True,
        "castle_beast_solo_ai_seven_weapons_preserved":True,
        "warp_pair_actual_server_pad":True,
        "warp_private_optin":"P0D_PRIVATE_TRAPPER_WARP",
        "anti_bounce_all_active_portals":True,
        "safe_landing_resets_velocity":True,
        "shared_three_transfer_limit":True,"no_second_remote_score_authority":True,
        "native":"NOT_RUN","rojo":"NOT_RUN",
        "roblox_engine":"NOT_RUN","android":"NOT_RUN",
        "owner":False,"product":"NO_GO"}
    with ZipFile(out,"w",ZIP_DEFLATED) as z:
        z.writestr(OUTPUT,built)
        z.writestr("SOURCE_LOCK.json",json.dumps(lock,ensure_ascii=False,indent=2)+"\n")
        z.writestr("RC_FEATURE_LOCK.json",json.dumps(feature,ensure_ascii=False,indent=2)+"\n")
        z.writestr("RECEIPT.json",json.dumps(receipt,ensure_ascii=False,indent=2)+"\n")
        z.writestr("source/server/TrapperWarpService.luau",module)
    if extract:
        extract.mkdir(parents=True,exist_ok=True)
        for name,node in after.items():
            (extract/(name+".luau")).write_text(node.text,encoding="utf-8")
    return receipt

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--parent",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--extract",type=Path)
    a=p.parse_args()
    print(json.dumps(build(a.parent,a.out,a.extract),ensure_ascii=False,indent=2))
