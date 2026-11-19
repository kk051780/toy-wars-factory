#!/usr/bin/env python3
"""Cumulative P0D #470 source-only spectator/Horde protection for original #297 role7.
Reuses the existing pinned respawn-safe output; never writes canonical RC/Game.
"""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
from xml.etree import ElementTree as ET
from role7_respawn_guard import extract, verify, blob

PARENT="COMPOSED_ROLE7_WIND_BUILDERQ_DELAYED_SAFE_RC82.rbxlx"
OUTPUT="P0D_ROLE7_ACK_WIND_BUILDER_COMBO_RESPAWN_SPECTATOR_RC82.rbxlx"
PIN="f6cc936a17b10d7cbfb1eb31718025a6fe21346160cacea8d58e8e52d93eb542"
BASE="d2f3ed1a47558fdaf07be0181c83c698bdb2ce34"
GAME_PATH="server/Game.server.luau"
PARENT_GAME="00fab56c721145688a34ba2825babd7bac351fbb"
RESULT_GAME="4986f23e7e0c46595aa489e4576d227945ed8686"
RESULT_PLACE="233c684371f6211d2d5f385479e8a39e6a22b0504efba96935a740cd99042a5e"

FIXES=(
 ("late_join",
 'if RunService:IsStudio() and\n        (match.phase=="ACTIVE" or match.phase=="COUNTDOWN") then',
 'if (RunService:IsStudio() or privateHordeTrialAllowed()) and\n        (match.phase=="ACTIVE" or match.phase=="COUNTDOWN") then'),
 ("horde_eligible",
 'horde:tick(now,Players:GetPlayers(),healthy)',
 'horde:tick(now,eligibleSoloPlayers(),healthy)'),
 ("elite_spectator",
 'if ok and hum and victimRoot and now>=(invulnUntil[victim] or 0) then',
 'if ok and hum and victimRoot\n                and victim:GetAttribute("P0D_LateJoinSpectator")~=true\n                and (getTeamName(victim)=="RED" or getTeamName(victim)=="BLUE")\n                and now>=(invulnUntil[victim] or 0) then'),
 ("flag_off_readmission",
 'if RunService:IsStudio() then\n            for _,entrant in ipairs(Players:GetPlayers()) do',
 'if RunService:IsStudio() or privateHordeTrialAllowed()\n            or #eligibleSoloPlayers()<#Players:GetPlayers() then\n            for _,entrant in ipairs(Players:GetPlayers()) do'),
 ("private_observer_spawn",
 'root.CFrame=LobbyIsland.spawn(getTeamName(entrant))',
 'root.CFrame=if RunService:IsStudio()\n                            then LobbyIsland.spawn(getTeamName(entrant))\n                            else map.teams[getTeamName(entrant)].spawn + Vector3.new(0,2,0)'),
 ("private_observer_physical_safe_island",
  'elseif RunService:IsStudio()\n            and player:GetAttribute("P0D_LateJoinSpectator")==true then\n            root.CFrame=LobbyIsland.spawn("RED")',
  'elseif player:GetAttribute("P0D_LateJoinSpectator")==true then\n            -- Reuse the preexisting Studio safe lobby for private real observers.\n            -- Build it only when first needed; no public/normal-game footprint.\n            if map.model:FindFirstChild("P0D_SAFE_LOBBY")==nil then\n                LobbyIsland.build(map.model)\n            end\n            root.CFrame=LobbyIsland.spawn("RED")'),
)

def sha(data): return hashlib.sha256(data).hexdigest()

def build(parent, output, extract_dir=None):
    with ZipFile(parent) as z:
        names=z.namelist()
        if len(names)!=len(set(names)) or any(
                n.startswith("/") or ".." in Path(n).parts for n in names):
            raise ValueError("UNSAFE_PARENT_ZIP")
        raw=z.read(PARENT)
        lock=json.loads(z.read("SOURCE_LOCK.json"))
        feature=json.loads(z.read("RC_FEATURE_LOCK.json"))
        prior=json.loads(z.read("RECEIPT.json"))
    if sha(raw)!=PIN or lock["blobs"][GAME_PATH]!=PARENT_GAME or prior.get("official_rc_head")!=BASE:
        raise ValueError("WRONG_OR_STALE_AUTHOR_PARENT")
    original=verify(raw,lock,feature)
    root, script=extract(raw)
    before=original["Game"].text
    repaired=before
    for name,old,new in FIXES:
        if repaired.count(old)!=1 or new in repaired:
            raise ValueError("CONFLICT_OR_ALREADY_APPLIED:"+name)
        repaired=repaired.replace(old,new,1)
    capture="map.teams[team].eggPrompt.Triggered:Connect(function(player: Player)"
    end="\n-- P0D_SAVED_PVE_MASTERY_V1:"
    if before[before.index(capture):before.index(end)] != repaired[repaired.index(capture):repaired.index(end)]:
        raise ValueError("EGG_SCORE_SOURCE_MUST_BE_BYTE_EXACT")
    for proof in (
        'sevenJobPickAckSeq[player]~=selectedAck',
        'player.Character~=castCharacter',
        'root.Parent~=castCharacter',
        'mobCombo[player]=if hitNow<(mobComboUntil[player] or 0)',
        'if ServerStorage:GetAttribute("P0D_ADAPTIVE_WIND_FIELD") == true then',
        'personalEggDeposits[player]=(personalEggDeposits[player] or 0)+1'):
        if proof not in repaired: raise ValueError("PARENT_ROLE_OR_SCORE_REGRESSION:"+proof)
    # Private observers receive real physical safe staging, public mode untouched.
    if (repaired.count('if map.model:FindFirstChild("P0D_SAFE_LOBBY")==nil then')!=1
        or repaired.count('LobbyIsland.build(map.model)')!=2
        or 'if RunService:IsStudio() then LobbyIsland.build(map.model) end' not in repaired):
        raise ValueError("PRIVATE_SAFE_ISLAND_OR_STUDIO_REUSE_MISSING")
    if blob(repaired)!=RESULT_GAME: raise ValueError("GAME_SOURCE_DRIFT")
    script["Game"].text=repaired
    place=ET.tostring(root,encoding="utf-8")
    if sha(place)!=RESULT_PLACE or len(place)!=779310:
        raise ValueError("PLACE_REPRODUCIBILITY_FAILURE")
    after=extract(place)[1]
    if any(after[n].text!=original[n].text for n in original if n!="Game"):
        raise ValueError("OTHER_SCRIPT_CHANGED")
    lock["blobs"][GAME_PATH]=feature["source_gitblobs"][GAME_PATH]=RESULT_GAME
    verify(place,lock,feature)
    report={
      "schema":"P0D_ROLE7_SPECTATOR_CUMULATIVE_SAFE_STAGING_V2",
      "official_rc_head":BASE,"official_rc_write":False,
      "parent_sha256":PIN,"place_sha256":RESULT_PLACE,"place_bytes":len(place),
      "scripts":82,"unchanged_parent_scripts":81,"source_lock_exact":True,
      "new_game_blob":RESULT_GAME,"egg_score_authority_byte_exact":True,
      "private_observer_safe_staging":True,
      "quality_fixes":[name for name,_,_ in FIXES],
      "native":"NOT_RUN","rojo":"NOT_RUN","studio":"NOT_RUN",
      "android":"NOT_RUN","product":"NO_GO","owner":False}
    with ZipFile(output,"w",ZIP_DEFLATED) as z:
        z.writestr(OUTPUT,place)
        z.writestr("SOURCE_LOCK.json",json.dumps(lock,ensure_ascii=False,indent=2)+"\n")
        z.writestr("RC_FEATURE_LOCK.json",json.dumps(feature,ensure_ascii=False,indent=2)+"\n")
        z.writestr("RECEIPT.json",json.dumps(report,ensure_ascii=False,indent=2)+"\n")
    if extract_dir is not None:
        extract_dir.mkdir(parents=True,exist_ok=True)
        for name,item in after.items():
            (extract_dir/(name+".luau")).write_text(item.text,encoding="utf-8")
    return report

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--parent",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--extract",type=Path)
    a=p.parse_args()
    print(json.dumps(build(a.parent,a.out,a.extract),ensure_ascii=False,indent=2))
