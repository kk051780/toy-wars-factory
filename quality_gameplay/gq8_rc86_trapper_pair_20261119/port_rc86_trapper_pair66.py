#!/usr/bin/env python3
"""Bring original RC86 TrapperWarpService's useful team-pair travel to the
existing V3 SevenRoleCombat authority. Does not create another Game/Remote/Store.
Sole canonical RC remains the existing 66 selected source profile.
"""
import argparse, hashlib, json, shutil
from pathlib import Path

MARK = 'GQ8_RC86_TRAPPER_PAIR_PORT_20261119'
ROUTE = 'ServerScriptService/EGGRUMBLE_SevenRoleCombat'

BODY = r'''
-- GQ8_RC86_TRAPPER_PAIR_PORT_20261119
-- Adapted from the original 86-source TrapperWarpService (old RC86).
-- Augments the existing TRAPPER C's short safeMove without adding a new Game,
-- Remote or damage owner. The server owns both endpoints and all travel.
local Players=game:GetService("Players")
local trapperWarpByUser:{[number]:any}={}
local TRAPPER_WARP_LIFE=40
local TRAPPER_WARP_USES=3
local TRAPPER_WARP_SPACING=16
local TRAPPER_WARP_REUSE=2.5
local function endTrapperWarp(userId:number)
 local state=trapperWarpByUser[userId]
 if state==nil then return end
 trapperWarpByUser[userId]=nil
 if state.folder and state.folder.Parent then state.folder:Destroy() end
end
local function trapperGround(session:any,root:BasePart,char:Model):Vector3?
 local arena=session.world and session.world:FindFirstChild("TacticalBattlefield")
 if not arena or not arena:IsA("BasePart") or not arena.Anchored or not arena.CanCollide then return nil end
 local at=root.Position
 if math.abs(at.X-arena.Position.X)>arena.Size.X*.5-8
  or math.abs(at.Z-arena.Position.Z)>arena.Size.Z*.5-8 then return nil end
 local ray=RaycastParams.new();ray.FilterType=Enum.RaycastFilterType.Exclude
 ray.FilterDescendantsInstances={char};ray.RespectCanCollide=true
 local hit=workspace:Raycast(at+Vector3.new(0,5,0),Vector3.new(0,-19,0),ray)
 if not hit or not hit.Instance.CanCollide or not hit.Instance.Anchored or hit.Normal.Y<.65
  or math.abs(at.Y-hit.Position.Y)>9 then return nil end
 return hit.Position
end
local function trapperAuthorized(session:any,ownerPlayer:Player,passenger:Player,state:any):boolean
 if state.session~=session or session.rules.phase~="ACTIVE"
  or state.owner~=ownerPlayer or ownerPlayer.Parent~=Players or passenger.Parent~=Players
  or not currentHumanMember(session,passenger) or not currentHumanMember(session,ownerPlayer)
  or passenger:GetAttribute("EGGRUMBLE_QueuedMode")~=session.mode
  or passenger:GetAttribute("EGGRUMBLE_Eliminated")==true
  or passenger:GetAttribute("EGGRUMBLE_CarryingEgg")==true then return false end
 local host=session.rules.castles[tostring(ownerPlayer.UserId)]
 local member=session.rules.castles[tostring(passenger.UserId)]
 if not host or not member or not host.alive or not member.alive
  or host.isAI or member.isAI or (member.heldEggs or 0)>0
  or (host.heldEggs or 0)>0 or ownerPlayer:GetAttribute("EGGRUMBLE_Role")~="TRAPPER" then return false end
 if session.mode=="BATTLE_ROYALE" then return passenger==ownerPlayer end
 return session.mode=="TEAM" and member.team==host.team
end
local function placeTrapperWarp(session:any,ownerPlayer:Player,root:BasePart,char:Model):()
 if not RunService:IsStudio() or session.rules.phase~="ACTIVE"
  or not currentHumanMember(session,ownerPlayer) then return end
 local host=session.rules.castles[tostring(ownerPlayer.UserId)]
 if not host or not host.alive or host.isAI or (host.heldEggs or 0)>0
  or ownerPlayer:GetAttribute("EGGRUMBLE_CarryingEgg")==true
  or ownerPlayer:GetAttribute("EGGRUMBLE_Role")~="TRAPPER" then return end
 local ground=trapperGround(session,root,char)
 if not ground then return end
 local now=os.clock()
 local old=trapperWarpByUser[ownerPlayer.UserId]
 if old and (old.session~=session or now>=old.expires or old.folder.Parent~=session.world) then
  endTrapperWarp(ownerPlayer.UserId);old=nil
 end
 if old and old.second then endTrapperWarp(ownerPlayer.UserId);old=nil end
 if old and (old.first.Position-ground).Magnitude<TRAPPER_WARP_SPACING then return end
 if not old then
  local folder=Instance.new("Folder")
  folder.Name="GQ8_RC86_TrapperWarp_"..tostring(ownerPlayer.UserId)
  folder:SetAttribute("FeatureId","GQ8_RC86_TRAPPER_PAIR_PORT_20261119")
  folder:SetAttribute("SessionOnly",true)
  folder.Parent=session.world
  old={session=session,owner=ownerPlayer,folder=folder,first=nil,second=nil,
   remaining=TRAPPER_WARP_USES,lastUse={},expires=now+TRAPPER_WARP_LIFE}
  trapperWarpByUser[ownerPlayer.UserId]=old
  local pinned=old
  task.delay(TRAPPER_WARP_LIFE+1,function()
   if trapperWarpByUser[ownerPlayer.UserId]==pinned then endTrapperWarp(ownerPlayer.UserId) end
  end)
 end
 local state=old
 local pad=Instance.new("Part")
 pad.Name=if state.first then "TrapperExit" else "TrapperEntrance"
 pad.Shape=Enum.PartType.Cylinder
 pad.Size=Vector3.new(.3,6,6)
 pad.CFrame=CFrame.new(ground+Vector3.new(0,.18,0))*CFrame.Angles(0,0,math.rad(90))
 pad.Anchored=true;pad.CanCollide=false;pad.CanTouch=false;pad.CanQuery=false
 pad.Material=Enum.Material.Neon;pad.Color=Color3.fromRGB(184,96,240)
 pad.Transparency=.25;pad.Parent=state.folder
 local prompt=Instance.new("ProximityPrompt")
 prompt.Name="GQ8_RC86_TrapperWarpUse"
 prompt.ActionText="味方ワープ";prompt.ObjectText="空間転移｜残り3回"
 prompt.HoldDuration=.25;prompt.MaxActivationDistance=7
 prompt.RequiresLineOfSight=true;prompt.Enabled=false;prompt.Parent=pad
 if state.first then state.second=pad else state.first=pad end
 local function use(passenger:Player)
  if state~=trapperWarpByUser[ownerPlayer.UserId] or state.folder.Parent~=session.world
   or state.remaining<=0
   or os.clock()>=state.expires or not state.first or not state.second
   or not trapperAuthorized(session,ownerPlayer,passenger,state) then return end
  local liveChar,liveRoot,liveHum=characterOf(passenger)
  if not liveChar or not liveRoot or not liveHum or liveHum.SeatPart~=nil
   or liveChar:GetAttribute("EGGRUMBLE_Downed")==true then return end
  local source=pad
  local destination=if pad==state.first then state.second else state.first
  if not destination or not destination.Parent or not source.Parent
   or (liveRoot.Position-source.Position).Magnitude>8 then return end
  local current=os.clock()
  if current-(state.lastUse[passenger.UserId] or -10000)<TRAPPER_WARP_REUSE then return end
  -- The prompt is a visual hint; the actual server ray blocks a forged
  -- prompt through a closed castle gate or a solid rock.
  local ray=RaycastParams.new();ray.FilterType=Enum.RaycastFilterType.Exclude
  ray.FilterDescendantsInstances={liveChar,state.folder};ray.RespectCanCollide=true
  local access=workspace:Raycast(liveRoot.Position+Vector3.new(0,1,0),
   source.Position+Vector3.new(0,1,0)-(liveRoot.Position+Vector3.new(0,1,0)),ray)
  if access and access.Instance and access.Instance.CanCollide then return end
  local landingRay=workspace:Raycast(destination.Position+Vector3.new(0,7,0),
   Vector3.new(0,-17,0),ray)
  if not landingRay or not landingRay.Instance.CanCollide or not landingRay.Instance.Anchored
   or landingRay.Normal.Y<.65 then return end
  local target=landingRay.Position+Vector3.new(0,3.35,0)
  local arena=session.world:FindFirstChild("TacticalBattlefield")
  if not arena or not arena:IsA("BasePart")
   or math.abs(target.X-arena.Position.X)>arena.Size.X*.5-5
   or math.abs(target.Z-arena.Position.Z)>arena.Size.Z*.5-5 then return end
  local overlap=OverlapParams.new();overlap.FilterType=Enum.RaycastFilterType.Exclude
  overlap.FilterDescendantsInstances={liveChar,state.folder};overlap.RespectCanCollide=true
  for _,hit in ipairs(workspace:GetPartBoundsInBox(CFrame.new(target),Vector3.new(3.8,5.0,3.8),overlap)) do
   if hit.CanCollide then return end
  end
  for _,other in ipairs(Players:GetPlayers()) do
   if other~=passenger then
    local _,otherRoot=characterOf(other)
    if otherRoot and (otherRoot.Position-target).Magnitude<5 then return end
   end
  end
  -- Re-validate after all queries; no egg-carrier travel / stale round.
  if not trapperAuthorized(session,ownerPlayer,passenger,state) then return end
  liveChar:PivotTo(CFrame.new(target,target+liveRoot.CFrame.LookVector))
  liveRoot.AssemblyLinearVelocity=Vector3.zero
  liveRoot.AssemblyAngularVelocity=Vector3.zero
  state.lastUse[passenger.UserId]=current
  state.remaining-=1
  for _,part in ipairs({state.first,state.second}) do
   local pr=part and part:FindFirstChild("GQ8_RC86_TrapperWarpUse")
   if pr and pr:IsA("ProximityPrompt") then
    pr.ObjectText="空間転移｜残り"..tostring(state.remaining).."回"
   end
  end
  if state.remaining<=0 then endTrapperWarp(ownerPlayer.UserId) end
 end
 prompt.Triggered:Connect(use)
 if state.first and state.second then
  for _,part in ipairs({state.first,state.second}) do
   local pr=part:FindFirstChild("GQ8_RC86_TrapperWarpUse")
   if pr and pr:IsA("ProximityPrompt") then pr.Enabled=true end
  end
 end
end
'''

def check(condition, key):
    if not condition: raise ValueError('RED_GQ8_TRAPPER_'+key)

def one(s,old,new,key):
    check(s.count(old)==1,'ANCHOR_'+key)
    return s.replace(old,new,1)

def run(project_path,receipt_path,archive_path=None):
    root=project_path.parent
    project=json.loads(project_path.read_text(encoding='utf-8'))
    receipt=json.loads(receipt_path.read_text(encoding='utf-8'))
    sources=receipt['sources']; check(len(sources)==65,'EXPECT_65')
    check('rc85_dojo_lobby_training' in receipt and 'stage_weapon_reach_balance' in receipt,'PRIOR_INTAKES')
    check('rc86_trapper_pair_warp' not in receipt,'DUPLICATE_RECEIPT')
    rows={r['route']:r for r in sources}
    check(len(rows)==65 and ROUTE in rows,'ROUTE_65')
    def path_for(route):
        d=project['tree']
        for part in route.split('/'):d=d[part]
        return root/d['$path']
    # All original 65 are validated before any write. Fail closed on stale source.
    for route,row in rows.items():
        b=path_for(route).read_bytes()
        check(len(b)==row['bytes'] and hashlib.sha256(b).hexdigest()==row['sha256'],'SOURCE_DRIFT_'+route)
    dst=path_for(ROUTE)
    original=dst.read_bytes()
    src=original.decode('utf-8')
    check(MARK not in src and 'TRAPPER' in src and 'EGGRUMBLE_Role' in src,'OLD_COMBAT_AUTH')
    # Bind only to existing shared role module after session and human membership are known.
    anchor='local function hitHumanHeroes(session:any,p:Player,root:BasePart,char:Model,center:Vector3,range:number,damage:number,shape:string):number'
    src=one(src,anchor,BODY+'\n'+anchor,'PLACE_PAIR_ONCE')
    old=''' elseif role=="TRAPPER" then
  if slot=="A" then blast()
  elseif slot=="B" then
   blast()
  else
   if owner.heldEggs==0 then safeMove(session,char,root,20) end
   blast()
  end
 elseif role=="BUILDER" then'''
    new=''' elseif role=="TRAPPER" then
  if slot=="A" then blast()
  elseif slot=="B" then
   blast()
  else
   -- Keep the current real66 short safeMove and add original RC86 team pair.
   if owner.heldEggs==0 then safeMove(session,char,root,20) end
   placeTrapperWarp(session,p,root,char)
   blast()
  end
 elseif role=="BUILDER" then'''
    src=one(src,old,new,'ONE_EXISTING_TRAPPER_C')
    src=one(src,
        'function HeroCombat.clear(p:Player)\n lastByPlayer[p.UserId]=nil',
        'function HeroCombat.clear(p:Player)\n endTrapperWarp(p.UserId)\n lastByPlayer[p.UserId]=nil',
        'LIFECYCLE_CLEAR')
    check(src.count('-- '+MARK)==1 and src.count('placeTrapperWarp(session,p,root,char)')==1,'SINGLE_AUTHORITY')
    check(src.count('endTrapperWarp(p.UserId)')==1,'CLEAR_ONCE')
    # Save a one-file rollback source in the artifact, outside the selected project.
    backup=root/'TRAPPER_OFF_EXACT_ORIGINAL_COMBAT.luau'
    check(not backup.exists(),'BACKUP_ALREADY_EXISTS')
    backup.write_bytes(original)
    updated=src.encode('utf-8');dst.write_bytes(updated)
    rows[ROUTE]['sha256']=hashlib.sha256(updated).hexdigest()
    rows[ROUTE]['bytes']=len(updated)
    for route,row in rows.items():
        b=path_for(route).read_bytes()
        check(len(b)==row['bytes'] and hashlib.sha256(b).hexdigest()==row['sha256'],'POST_SOURCE_DRIFT_'+route)
    receipt['rc86_trapper_pair_warp']={
        'feature_id':MARK,'original_rc86_artifact_id':14161823401,
        'original_rc86_source':'ServerScriptService/TrapRaidersS1/TrapperWarpService',
        'changed_existing_routes':[ROUTE],'other_original65_sources_byte_exact':64,
        'new_game_owners':0,'new_remote_owners':0,'new_damage_owners':0,
        'new_selected_luau':0,'gameplay':'TRAPPER_C_FIRST_SECOND_2TEAM_WARP_3USES_40S',
        'old_short_warp_preserved':True,'trapper_only_cast':True,
        'server_session_team_egg_down_los_ground_collision_checks':True,
        'all_original_roles_and_existing_buffs_preserved':True,
        'studio_2client':'NOT_TESTED','android':'NOT_TESTED','fun':'NO_GO',
        'backup_original_combat_sha256':hashlib.sha256(original).hexdigest(),
        'rollback_file':backup.name,
    }
    receipt_path.write_text(json.dumps(receipt,ensure_ascii=False,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    print('GQ8_REAL66_RC86_TRAPPER_PAIR_SOURCE_64UNCHANGED_COMBAT1_PASS')

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--project',type=Path,required=True)
    parser.add_argument('--receipt',type=Path,required=True)
    a=parser.parse_args()
    run(a.project,a.receipt)