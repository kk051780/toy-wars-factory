#!/usr/bin/env python3
"""Port RC86 original STARRY_PATH_V1 into the *one* REAL66 Realm owner.

Original RC86 StarfallPath (6,463 byte physical Script) had 10 timed stones,
two symmetric switches, 16s open, 7s cooldown, no vanish beneath players.
Current V3 has no old CrystalCanyon model, so attach an equivalent reachable
elevated bridge to the already valid TEAM/BR TacticalBattlefield. Do not add
a second independent Game, Realm, Remote, Score, XP or DataStore writer.
"""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path

ROUTE = "ServerScriptService/EGGRUMBLE_RealmBattleCore"
FEATURE = "GQ8_RC86_STARRY_PATH_SINGLE_REALM_REAL66_20261119"
OLD = ''' scenes[world]=state
 -- A physical underwater cavern reachable by everyone. Water is represented'''
BLOCK = r''' -- GQ8_RC86_STARRY_PATH_SINGLE_REALM_REAL66_20261119:
 -- Original StarfallPath real-world policy, V3 arena adaptation.
 -- Ten timed physical star slabs, two symmetric prompts, open16s/cooldown7s.
 -- Keep its existing TacticalBattlefield underneath: no unsafe map removal.
 -- Studio-only like original RC86, never a second Game/Realm/Score writer.
 local function installLegacyStarPath()
  if not RunService:IsStudio() or core:FindFirstChild("GQ8_RC86_StarfallPath") then return end
  if floor.Size.X<600 or floor.Size.Z<500 then return end
  local stage=Instance.new("Folder")
  stage.Name="GQ8_RC86_StarfallPath"
  stage:SetAttribute("FeatureId","STARRY_PATH_V1")
  stage:SetAttribute("Origin","RC86_AUTHOR_STARRY_PATH_V1")
  stage:SetAttribute("NoDamageScoreStoreRemote",true)
  stage:SetAttribute("OriginalTacticalFloorAlwaysAvailable",true)
  stage:SetAttribute("TimedStarSteps",10)
  stage:SetAttribute("Switches",2)
  stage:SetAttribute("PathOpen",false)
  stage.Parent=core
  local center=Vector3.new(x,y+12,z-175)
  local bridge={}
  for i=1,10 do
   local cx=-22.5+(i-1)*5
   local color=if i%2==0 then Color3.fromRGB(89,208,255)
    else Color3.fromRGB(235,160,255)
   local slab=part(stage,"StarStep_"..tostring(i),
    CFrame.new(center+Vector3.new(cx,0,0)),
    Vector3.new(6,1.3,12),color,false,.82)
   slab.CanTouch=false;slab.CanQuery=false;slab.Material=Enum.Material.Neon
   table.insert(bridge,slab)
  end
  for side=-1,1,2 do
   -- Persistent six-step V3 arena stairs; the original canyon-specific banks
   -- do not exist in V3. Both factions can approach the timed route on foot.
   for i=1,6 do
    local sx=side*(29+(i-1)*6)
    local sy=-(i-1)*2
    local step=part(stage,"StarAccess_"..tostring(side).."_"..tostring(i),
     CFrame.new(center+Vector3.new(sx,sy,0)),
     Vector3.new(7.3,1.4,12),Color3.fromRGB(83,99,142),true)
    step.CanTouch=false
   end
  end
  local orb=part(stage,"ConstellationCore",
   CFrame.new(center+Vector3.new(0,8,0)),Vector3.new(2,2,2),
   Color3.fromRGB(250,236,125),false,.35)
  orb.Shape=Enum.PartType.Ball
  local glow=Instance.new("PointLight")
  glow.Brightness=1.4;glow.Range=19;glow.Enabled=false;glow.Parent=orb
  local dust=Instance.new("ParticleEmitter")
  dust.Name="StarfallDust"
  dust.Texture="rbxasset://textures/particles/sparkles_main.dds"
  dust.Rate=5;dust.Lifetime=NumberRange.new(.8,1.8)
  dust.Speed=NumberRange.new(.5,2)
  dust.SpreadAngle=Vector2.new(90,90);dust.Enabled=false
  dust.Parent=orb
  local open=false
  local readyAt=0
  local expiresAt=0
  local function occupied()
   for _,player in ipairs(Players:GetPlayers()) do
    local char=player.Character
    local root=char and char:FindFirstChild("HumanoidRootPart")
    local human=char and char:FindFirstChildOfClass("Humanoid")
    if root and human and human.Health>0 then
     local rel=root.Position-center
     if math.abs(rel.X)<=28 and math.abs(rel.Z)<=9
      and rel.Y>=-4 and rel.Y<=10 then return true end
    end
   end
   return false
  end
  local function setOpen(enabled)
   if open and not enabled then readyAt=os.clock()+7 end
   open=enabled
   for _,stone in ipairs(bridge) do
    stone.CanCollide=enabled
    stone.CanQuery=enabled
    stone.Transparency=if enabled then .07 else .82
   end
   glow.Enabled=enabled;dust.Enabled=enabled
   stage:SetAttribute("PathOpen",enabled)
   stage:SetAttribute("LastOpenedSeconds",if enabled then 16 else 0)
  end
  for side=-1,1,2 do
   local switch=part(stage,"StarSwitch_"..tostring(side),
    CFrame.new(center+Vector3.new(side*31,3,0)),
    Vector3.new(3,3,3),
    if side==-1 then Color3.fromRGB(228,158,255)
     else Color3.fromRGB(114,215,255),false)
   switch.Shape=Enum.PartType.Ball
   switch.CanTouch=false
   prompt(switch,"星の橋を呼ぶ","星降る橋・16秒",function(player)
    if not state.active or not eligible(player,mode,world)
     or open or os.clock()<readyAt then return end
    -- The existing Realm prompt validates real server distance and raycast.
    setOpen(true)
    expiresAt=os.clock()+16
   end)
  end
  setOpen(false)
  task.spawn(function()
   while state.active and stage.Parent==core and world.Parent do
    if open and os.clock()>=expiresAt and not occupied() then
     -- Original RC86 non-loss safety: never delete collision under a player.
     setOpen(false)
    end
    task.wait(.4)
   end
  end)
 end
 installLegacyStarPath()
'''
NEW = ''' scenes[world]=state
''' + BLOCK + ''' -- A physical underwater cavern reachable by everyone. Water is represented'''


def hash_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def patch(src: str) -> str:
    if src.count(OLD)!=1 or FEATURE in src:
        raise ValueError("RED_STARRY66_REALM_SOURCE_ANCHOR_OR_DOUBLE_PATCH")
    for marker in (
        'local function eligible(p,mode,world)',
        'local function prompt(p,action,object,callback)',
        'local function install(world)',
        'local RunService = game:GetService("RunService")',
        'local CORE_NAME = "EGGRUMBLE_REALM_BATTLE_CORE"',
        'REAL65_LATE_HOST_WATCH_V1',
    ):
        if src.count(marker)!=1:
            raise ValueError("RED_STARRY66_MISSING_SINGLE_REALM_AUTHORITY_"+marker[:25])
    out=src.replace(OLD,NEW,1)
    if out.replace(NEW,OLD,1)!=src:
        raise ValueError("RED_STARRY66_MUTATED_UNRELATED_REALM_LINES")
    if out.count(FEATURE)!=1 or out.count('stage:SetAttribute("TimedStarSteps",10)')!=1:
        raise ValueError("RED_STARRY66_NO_PHYSICAL_TEN_STEP_ROUTE")
    for token in ('RemoteEvent',':TakeDamage(', 'ProcessReceipt','DataStoreService','Instance.new("Script")'):
        if out.count(token)!=src.count(token):
            raise ValueError("RED_STARRY66_NEW_SECOND_GAME_AUTHORITY_"+token)
    return out


def self_test() -> None:
    base="\n".join([
        'local RunService = game:GetService("RunService")',
        'local CORE_NAME = "EGGRUMBLE_REALM_BATTLE_CORE"',
        'local function eligible(p,mode,world)',
        'local function prompt(p,action,object,callback)',
        'local function install(world)',
        OLD, 'REAL65_LATE_HOST_WATCH_V1',
    ])
    result=patch(base)
    assert 'installLegacyStarPath()' in result
    assert 'not occupied()' in result and 'os.clock()+7' in result
    assert 'expiresAt=os.clock()+16' in result
    assert 'local center=Vector3.new(x,y+12,z-175)' in result
    assert result.replace(NEW,OLD,1)==base
    for mutant in (
        result, base.replace('scenes[world]=state','scenes[world]=state2'),
        base.replace('REAL65_LATE_HOST_WATCH_V1',''),
        base+"\n"+OLD,
    ):
        try: patch(mutant)
        except ValueError: pass
        else: raise AssertionError("RED_STARRY66_MUTANT_ACCEPTED")
    print("GQ8_OLD_RC86_STARRY_PATH_REAL66_ORIGINAL_FOUR_GUARDS_NEGATIVE_PASS")


def apply(project_file: Path, receipt_file: Path) -> None:
    proj=json.loads(project_file.read_text(encoding="utf8"))
    receipt=json.loads(receipt_file.read_text(encoding="utf8"))
    rows={x["route"]:x for x in receipt.get("sources",[])}
    if proj.get("name")!="EGGRUMBLE_REAL65_PRIVATE_STUDIO" or len(rows)!=65 or len(receipt["sources"])!=65:
        raise ValueError("RED_STARRY66_PARENT_65_SOURCE_PROFILE")
    if not receipt.get("rc85_dojo_lobby_training") or not receipt.get("legacy_rc86_wind") or not receipt.get("stage_weapon_reach_balance"):
        raise ValueError("RED_STARRY66_OLD_RC85_86_CUMULATIVE_FEATURE_MISSING")
    if ROUTE not in rows or rows[ROUTE]["class"]!="Script" or receipt.get("rc86_starry_path"):
        raise ValueError("RED_STARRY66_REALM_ROUTE_OR_DOUBLE_PORT")
    before={}
    for route,row in rows.items():
        node=proj["tree"]
        for component in route.split("/"):node=node[component]
        file=project_file.parent/node["$path"]
        raw=file.read_bytes()
        if len(raw)!=row["bytes"] or hash_bytes(raw)!=row["sha256"]:
            raise ValueError("RED_STARRY66_PARENT_SOURCE_LOCK_"+route)
        before[route]=(file,raw)
    realm_path,original=before[ROUTE]
    altered=patch(original.decode("utf8")).encode("utf8")
    realm_path.write_bytes(altered)
    rows[ROUTE]["bytes"]=len(altered)
    rows[ROUTE]["sha256"]=hash_bytes(altered)
    if sum(p.read_bytes()!=data for p,data in before.values())!=1:
        raise ValueError("RED_STARRY66_NOT_EXACT_ONE_OLD_SOURCE_CHANGE")
    if ROUTE not in receipt.get("patched_existing_routes",[]):
        raise ValueError("RED_STARRY66_EXISTING_REALM_OWNER_NOT_SELECTED")
    receipt["rc86_starry_path"]={
      "feature_id":FEATURE,"old_feature_flag":"STARRY_PATH_V1",
      "old_source":"ServerScriptService/TrapRaidersS1/StarfallPath",
      "old_artifact_id":14161823401,
      "new_route":ROUTE,"old_bridge_anchor":"P0D_CrystalCanyonAnchor",
      "new_bridge_anchor":"EXISTING_TEAM_OR_BR_TACTICAL_BATTLEFIELD",
      "original_switches":2,"original_timed_steps":10,
      "open_seconds":16,"reopen_cooldown":7,
      "occupancy_prevents_drop":True,"requires_authorized_real_client":True,
      "studio_only":True,
      "current_realm_owner_reused":True,"old_66_explorer_preserved":True,
      "original_65_sources":65,"unchanged_sources":64,
      "new_script_count":0,"new_remote_count":0,"new_game_owner_count":0,
      "new_score_damage_store_writers":0,
      "visual_and_gameplay_studio":"NOT_TESTED",
      "fun":"NO_GO","android15":"NOT_TESTED",
      "rollback":"Remove exactly this one RealmBattleCore overlay; preserve REAL66 explorer and OFF65/OFF63"
    }
    receipt_file.write_text(json.dumps(receipt,ensure_ascii=False,sort_keys=True,indent=2)+"\n",encoding="utf8")
    for route,row in rows.items():
        data=before[route][0].read_bytes()
        if len(data)!=row["bytes"] or hash_bytes(data)!=row["sha256"]:
            raise ValueError("RED_STARRY66_FINAL_65_SELECTED_SOURCE_DRIFT_"+route)
    print("GQ8_RC86_STARRY_PATH_10_STEPS_2_SWITCHES_ACTUAL_SINGLE_REALM_REAL66_65_SOURCE_PASS")


if __name__=="__main__":
    arg=argparse.ArgumentParser()
    arg.add_argument("--self-test",action="store_true")
    arg.add_argument("--project",type=Path)
    arg.add_argument("--receipt",type=Path)
    x=arg.parse_args()
    if x.self_test:self_test()
    else:
        if not x.project or not x.receipt:arg.error("--project/--receipt required")
        apply(x.project,x.receipt)
