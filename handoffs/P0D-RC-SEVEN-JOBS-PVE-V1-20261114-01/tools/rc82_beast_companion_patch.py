#!/usr/bin/env python3
"""Source-exact original #297 Game-only beast companion, private RC82 candidate.

Input: actual GitHub-native/Rojo spectator-composite artifact ZIP, one Place with
existing 82 scripts. Output: single privately testable Place and dual-source locks.
Does not write official RC, main, remote, persistent Store or release decisions.
"""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile,ZIP_DEFLATED

BASE = "d2f3ed1a47558fdaf07be0181c83c698bdb2ce34"
PARENT_PLACE = "P0D_ROLE7_ACK_WIND_BUILDER_COMBO_RESPAWN_SPECTATOR_RC82.rbxlx"
PARENT_SHA256 = "bbb9c919cb11cfc5147a75a9d8f8e770eb5a7d540acfffeb650010f5710e0d1c"
PARENT_GAME_BLOB = "6848da45a10242e5908a102bd9db47b9d3f30023"
GAME = "server/Game.server.luau"
OUTPUT_PLACE = "P0D_RC82_BEAST_TAMER_REAL_COMPANION_PRIVATE.rbxlx"

def sha(x:bytes)->str: return hashlib.sha256(x).hexdigest()
def blob(x:str)->str:
    b=x.encode('utf-8')
    return hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
def one(s:str,old:str,new:str,label:str)->str:
    if s.count(old)!=1: raise ValueError('ANCHOR_DRIFT_'+label+'_'+str(s.count(old)))
    return s.replace(old,new,1)

COMPANION_STATE = '''local sevenBeastCompanions: {[Player]: Model} = {}
'''
COMPANION_CLEANUP = '''-- SevenJob Beast Tamer: ONE short-lived server-owned pet per player.
local function clearSevenBeast(player:Player)
    local model=sevenBeastCompanions[player]
    sevenBeastCompanions[player]=nil
    if model and model.Parent then model:Destroy() end
end
'''

COMPANION_FUNCTION = '''-- FB004: real summon, not a flash/second instant attack. 1 pet / caster,
-- bounded 9s, <= 40 server updates, <= 17 existing neutral enemies, no PvP.
-- Existing single Game/Remote and horde:hit remain the ONLY damage/KO authority.
local function summonSevenBeast(player:Player,root:BasePart,team:string,serial:number)
    clearSevenBeast(player)
    local castCharacter=player.Character
    local selectedAck=sevenJobPickAckSeq[player]
    if not castCharacter or selectedAck==nil then return end
    local pet=Instance.new("Model")
    pet.Name="P0D_JOB_BEAST_TAMER_FOLLOW_ATTACK"
    local initial=root.Position+Vector3.new(3,-1.3,-2.5)
    local function bodyPart(name:string,size:Vector3,offset:Vector3,color:Color3,
            shape:Enum.PartType):Part
        local part=Instance.new("Part")
        part.Name=name
        part.Size=size;part.Shape=shape;part.Color=color
        part.Material=Enum.Material.SmoothPlastic
        part.Anchored=true;part.CanCollide=false;part.CanTouch=false
        part.CanQuery=false;part.CastShadow=false
        part.CFrame=CFrame.new(initial+offset)
        part.Parent=pet
        return part
    end
    local emerald=Color3.fromRGB(45,180,126)
    local jade=Color3.fromRGB(113,232,174)
    local gold=Color3.fromRGB(242,196,91)
    local core=bodyPart("BeastTorso",Vector3.new(2.9,2.2,3.7),Vector3.zero,
        emerald,Enum.PartType.Ball)
    pet.PrimaryPart=core
    bodyPart("DragonHead",Vector3.new(2.1,1.9,2.1),Vector3.new(0,.5,-2),
        jade,Enum.PartType.Ball)
    bodyPart("DragonTail",Vector3.new(.9,.9,2.7),Vector3.new(0,.1,2.3),
        emerald,Enum.PartType.Ball)
    for _,sign in ipairs({-1,1}) do
        bodyPart("Wing"..sign,Vector3.new(2.4,.25,2.3),Vector3.new(sign*2,.75,.2),
            jade,Enum.PartType.Block)
        bodyPart("Horn"..sign,Vector3.new(.48,1.4,.48),Vector3.new(sign*.7,1.75,-2.2),
            gold,Enum.PartType.Ball)
        bodyPart("Foot"..sign,Vector3.new(.85,.9,1.1),Vector3.new(sign*.85,-1,-1.2),
            gold,Enum.PartType.Block)
    end
    pet.Parent=map.model
    sevenBeastCompanions[player]=pet
    task.spawn(function()
        local expires=serverNow()+9
        local lastPetHit=serverNow()
        local petPosition=initial
        local params=RaycastParams.new()
        params.FilterType=Enum.RaycastFilterType.Exclude
        params.FilterDescendantsInstances={castCharacter,horde.folder,pet}
        for _=1,40 do
            task.wait(.25)
            local now=serverNow()
            if now>=expires or sevenBeastCompanions[player]~=pet
                or not pet.Parent or player.Parent~=Players
                or player.Character~=castCharacter or match.phase~="ACTIVE"
                or match.serial~=serial or getTeamName(player)~=team
                or sevenJobs[player]~="BEAST_TAMER"
                or sevenJobSelected[player]~=true
                or sevenJobPickAckSeq[player]~=selectedAck
                or carry[player]~=nil or slowed[player]~=nil
                or ServerStorage:GetAttribute("P0D_RC_ENABLE_SEVEN_JOBS_PVE")==false
                or not (RunService:IsStudio() or privateHordeTrialAllowed()) then break end
            local alive,currentRoot=healthy(player)
            if not alive or not currentRoot or currentRoot.Parent~=castCharacter then break end
            local nearest:any=nil
            local nearestDistance=17
            for _,mob in ipairs(horde.mobs) do
                if mob.hp>0 and mob.model.Parent==horde.folder then
                    local planar=Vector3.new(mob.pos.X-currentRoot.Position.X,0,
                        mob.pos.Z-currentRoot.Position.Z)
                    if planar.Magnitude<nearestDistance
                        and math.abs(mob.pos.Y-currentRoot.Position.Y)<7 then
                        nearest=mob;nearestDistance=planar.Magnitude
                    end
                end
            end
            local desired=currentRoot.Position+Vector3.new(3,-1.3,-2.5)
            if nearest then
                local delta=Vector3.new(nearest.pos.X-currentRoot.Position.X,0,
                    nearest.pos.Z-currentRoot.Position.Z)
                -- Guard mode: the summon NEVER leaves the owner's 7-stud leash.
                if delta.Magnitude>.05 then
                    desired=currentRoot.Position+delta.Unit*math.min(delta.Magnitude,7)
                        +Vector3.new(0,-1.3,0)
                end
            end
            if (petPosition-currentRoot.Position).Magnitude>25 then
                -- Teleports cannot leave a persistent invisible attacker behind.
                petPosition=currentRoot.Position+Vector3.new(3,-1.3,-2.5)
            end
            local direction=Vector3.new(desired.X-petPosition.X,0,
                desired.Z-petPosition.Z)
            local step=if direction.Magnitude>.05
                then direction.Unit*math.min(direction.Magnitude,3.2)
                else Vector3.zero
            if step.Magnitude>0 and not workspace:Raycast(petPosition,step,params) then
                petPosition=Vector3.new(petPosition.X+step.X,
                    currentRoot.Position.Y-1.3,petPosition.Z+step.Z)
            end
            local aim=if nearest then Vector3.new(nearest.pos.X-petPosition.X,0,
                nearest.pos.Z-petPosition.Z) else Vector3.new(currentRoot.CFrame.LookVector.X,
                0,currentRoot.CFrame.LookVector.Z)
            if aim.Magnitude<.01 then aim=Vector3.new(1,0,0) end
            aim=aim.Unit
            pet:PivotTo(CFrame.lookAt(petPosition,petPosition+aim))
            if nearest and (nearest.pos-petPosition).Magnitude<10
                and now-lastPetHit>=1.2 then
                lastPetHit=now
                -- Actual existing server-owned horde:hit credits the owner's KO.
                sevenJobStrike(player,petPosition,aim,14)
            end
        end
        if sevenBeastCompanions[player]==pet then clearSevenBeast(player)
        elseif pet.Parent then pet:Destroy() end
    end)
end
'''

def modify_game(s:str)->str:
    s=one(s,'local sevenJobLastUse: {[Player]: number} = {}\n',
       'local sevenJobLastUse: {[Player]: number} = {}\n'+COMPANION_STATE+COMPANION_CLEANUP,'PET_STATE')
    s=one(s,'    sevenJobs[player]=job\n    sevenJobSelected[player]=true\n',
       '    clearSevenBeast(player) -- no old pet survives role re-selection\n'
       '    sevenJobs[player]=job\n    sevenJobSelected[player]=true\n','SELECT_PET_REVOKE')
    s=one(s,'            dropEgg(player)\n            sevenJobs[player]="WARRIOR"\n',
       '            dropEgg(player)\n            clearSevenBeast(player)\n'
       '            sevenJobs[player]="WARRIOR"\n','TEAM_CLEAR_PET')
    s=one(s,'local function useSevenJob(player:Player,data:any)\n',
       COMPANION_FUNCTION+'local function useSevenJob(player:Player,data:any)\n','PET_BEFORE_USE')
    s=one(s,'    elseif job=="BEAST_TAMER" then\n        sevenJobStrike(player,root.Position,facing,23)\n        sevenJobDelayedStrike(player,job,match.serial,root.Position,facing,23,.8)\n',
       '    elseif job=="BEAST_TAMER" then\n'
       '        sevenJobStrike(player,root.Position,facing,23)\n'
       '        summonSevenBeast(player,root,team,match.serial)\n','PET_Q_REAL')
    s=one(s,'        clearEarnedPowerVisual(player)\n        cleanupScout(player)\n        dropEgg(player)\n',
       '        clearEarnedPowerVisual(player)\n        cleanupScout(player)\n'
       '        clearSevenBeast(player)\n        dropEgg(player)\n','RESPAWN_CLEAR_PET')
    s=one(s,'    dropEgg(player)\n    cleanupScout(player)\n    lastFreeHatch[player]=nil\n',
       '    dropEgg(player)\n    cleanupScout(player)\n    clearSevenBeast(player)\n    lastFreeHatch[player]=nil\n','LEAVE_CLEAR_PET')
    return s

def main(parent:Path,target:Path):
    with ZipFile(parent) as z:
        members=z.namelist()
        if len(members)!=len(set(members)):raise ValueError('DUPLICATE_PARENT_ZIP_MEMBER')
        place=z.read(PARENT_PLACE)
        sl=json.loads(z.read('SOURCE_LOCK.json'))
        fl=json.loads(z.read('RC_FEATURE_LOCK.json'))
        receipt=json.loads(z.read('RECEIPT.json'))
    if sha(place)!=PARENT_SHA256 or receipt.get('official_rc_head')!=BASE:
        raise ValueError('BEAST_PARENT_MISMATCH')
    root=ET.fromstring(place)
    scripts={}
    for item in root.iter('Item'):
        if item.get('class') not in ('Script','LocalScript','ModuleScript'):continue
        props=item.find('Properties')
        if props is None:continue
        name=props.find("./string[@name='Name']")
        src=props.find("./string[@name='Source']")
        if name is None or src is None or src.text is None or name.text in scripts:
            raise ValueError('MALFORMED_SCRIPT')
        scripts[name.text]=src
    if len(scripts)!=82 or sl.get('total_scripts')!=82 or fl.get('total_sources')!=82:
        raise ValueError('SOURCE_COUNT_DRIFT')
    if sl.get('blobs')!=fl.get('source_gitblobs'):
        raise ValueError('SOURCE_DUAL_LOCK_DRIFT')
    if Counter(blob(v.text) for v in scripts.values())!=Counter(sl['blobs'].values()):
        raise ValueError('PINNED_82_SOURCE_DRIFT')
    if sl['blobs'].get(GAME)!=PARENT_GAME_BLOB or blob(scripts['Game'].text)!=PARENT_GAME_BLOB:
        raise ValueError('ORIGINAL_GAME_BLOB_DRIFT')
    before=scripts['Game'].text
    after=modify_game(before)
    if blob(after)==PARENT_GAME_BLOB or 'summonSevenBeast(player,root,team,match.serial)' not in after:
        raise ValueError('PET_GAME_NOT_APPLIED')
    # Preserve original exact ACK, objective and spectator authority.
    for literal in ('sevenJobPickAckSeq[player]~=selectedAck',
         'horde:tick(now,eligibleSoloPlayers(),healthy)',
         'personalEggDeposits[player]=(personalEggDeposits[player] or 0)+1',
         'mobCombo[player]=if hitNow<(mobComboUntil[player] or 0)',
         'or player.Character~=castCharacter',
         'or #eligibleSoloPlayers()<#Players:GetPlayers() then'):
        if literal not in after:raise ValueError('PARENT_REAL_FEATURE_LOST_'+literal)
    for no in scripts:
        if no!='Game' and scripts[no].text is None:raise ValueError('OTHER_SOURCE_MISSING')
    scripts['Game'].text=after
    xml=ET.tostring(root,encoding='utf-8')
    check=ET.fromstring(xml)
    actual=[]
    for item in check.iter('Item'):
        if item.get('class') not in ('Script','LocalScript','ModuleScript'):continue
        p=item.find('Properties')
        if p is None:continue
        src=p.find("./string[@name='Source']")
        if src is not None and src.text is not None:actual.append(blob(src.text))
    sl['blobs'][GAME]=fl['source_gitblobs'][GAME]=blob(after)
    if len(actual)!=82 or Counter(actual)!=Counter(sl['blobs'].values()):
        raise ValueError('NEW_LOCK_OR_XML_BAD')
    meta={
      'schema':'P0D_ROLE7_REAL_BEAST_COMPANION_PRIVATE_SOURCE_V1',
      'official_parent':BASE,'parent_place_sha256':PARENT_SHA256,
      'place_sha256':sha(xml),'place_bytes':len(xml),
      'scripts':82,'modified_only':[GAME],'unchanged_parent':81,
      'game_blob_before':PARENT_GAME_BLOB,'game_blob_after':blob(after),
      'summon_max_per_player':1,'summon_lifetime_seconds':9,
      'summon_tick_seconds':.25,'summon_steps_max':40,
      'summon_attack_interval_min':1.2,'damage_owner':'existing sevenJobStrike/horde:hit',
      'feature':'BEAST_TAMER physical follower+neutral auto attack (no mount yet)',
      'studio':'NOT_RUN','android':'NOT_RUN','owner':False,
      'official_rc_write':False,'product':'NO_GO',
    }
    with ZipFile(target,'w',ZIP_DEFLATED) as z:
        z.writestr(OUTPUT_PLACE,xml)
        z.writestr('SOURCE_LOCK.json',json.dumps(sl,ensure_ascii=False,indent=2)+'\n')
        z.writestr('RC_FEATURE_LOCK.json',json.dumps(fl,ensure_ascii=False,indent=2)+'\n')
        z.writestr('RECEIPT.json',json.dumps(meta,ensure_ascii=False,indent=2)+'\n')
        z.writestr('source/server/Game.server.luau',after)
    print(json.dumps(meta,ensure_ascii=False,indent=2))

if __name__=='__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('--parent',required=True,type=Path)
    ap.add_argument('--out',required=True,type=Path)
    args=ap.parse_args();main(args.parent,args.out)
