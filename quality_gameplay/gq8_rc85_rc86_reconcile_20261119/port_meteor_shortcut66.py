#!/usr/bin/env python3
"""Original RC86 MeteorFourth V1 -> single current V3 Realm, no Game fork.

The original MeteorFourth script (artifact 14161823401) implemented a fourth
temporary path with 55s quiet / 5s warning / 22s physical passage, at most
12 star segments, NEVER retracting underneath players. Old CrystalCanyon
anchors are not present in the V3 world. Port its *safe timed-route gameplay*
to a separated lane of the current real TEAM/BR tactical battlefield.
"""
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path

ROUTE="ServerScriptService/EGGRUMBLE_RealmBattleCore"
FEATURE="GQ8_RC86_METEOR_SHORTCUT_SINGLE_REALM_REAL66_20261119"
OLD=''' installLegacyStarPath()
 -- A physical underwater cavern reachable by everyone. Water is represented'''
PORT=r''' -- GQ8_RC86_METEOR_SHORTCUT_SINGLE_REALM_REAL66_20261119
 -- Original MeteorFourth weather-route timing and bridge safety, V3 adaptation.
 -- This is a separate lane from the inherited ten-step Starfall path,
 -- not an additional storm authority, Game/Score/Remote or damage source.
 local function installLegacyMeteorRoute()
  if not RunService:IsStudio() or core:FindFirstChild("GQ8_RC86_MeteorShortcut") then return end
  if not core:FindFirstChild("GQ8_RC86_StarfallPath")
   or floor.Size.X<600 or floor.Size.Z<500 then return end
  local stage=Instance.new("Folder")
  stage.Name="GQ8_RC86_MeteorShortcut"
  stage:SetAttribute("FeatureId","METEOR_FOURTH_V1")
  stage:SetAttribute("OriginalQuietSeconds",55)
  stage:SetAttribute("OriginalWarningSeconds",5)
  stage:SetAttribute("OriginalOpenSeconds",22)
  stage:SetAttribute("NewGameRemoteScoreStoreOwners",0)
  stage:SetAttribute("TemporaryBridgeParts",12)
  stage.Parent=core
  -- Thirty studs apart from the original Starfall lane and away from arena edge.
  -- The original old CrystalCanyon anchors are absent; use existing safe floor.
  local center=Vector3.new(x,y+12,z-145)
  local segments={}
  for i=1,12 do
   local dx=-27.5+(i-1)*5
   local tile=part(stage,"MeteorBridge_"..tostring(i),
    CFrame.new(center+Vector3.new(dx,0,0)),
    Vector3.new(6,1.3,11),Color3.fromRGB(85,201,255),false,1)
   tile.Material=Enum.Material.Neon;tile.CanTouch=false;tile.CanQuery=false
   table.insert(segments,tile)
  end
  for side=-1,1,2 do
   -- Each team approaches a permanent staircase, not an inaccessible sky deck.
   for i=1,6 do
    local s=part(stage,"MeteorAccess_"..tostring(side).."_"..tostring(i),
     CFrame.new(center+Vector3.new(side*(33+(i-1)*6),-(i-1)*2,0)),
     Vector3.new(7,1.4,11),Color3.fromRGB(66,116,158),true)
    s.CanTouch=false
   end
  end
  local messageAnchor=part(stage,"MeteorWarningAnchor",
   CFrame.new(center+Vector3.new(0,8,0)),Vector3.new(1,1,1),
   Color3.fromRGB(251,221,154),false,1)
  messageAnchor.CanQuery=false
  local billboard=Instance.new("BillboardGui")
  billboard.Name="MeteorRouteSignal"
  billboard.Adornee=messageAnchor;billboard.AlwaysOnTop=true
  billboard.Size=UDim2.fromOffset(300,70)
  billboard.MaxDistance=260;billboard.Parent=messageAnchor
  local label=Instance.new("TextLabel")
  label.Name="Message";label.Size=UDim2.fromScale(1,1)
  label.BackgroundColor3=Color3.fromRGB(16,28,48)
  label.BackgroundTransparency=.2
  label.TextColor3=Color3.fromRGB(255,241,157)
  label.Font=Enum.Font.GothamBold;label.TextScaled=true
  label.Text="";label.Parent=billboard
  local open=false
  local function occupied()
   for _,player in ipairs(Players:GetPlayers()) do
    local character=player.Character
    local root=character and character:FindFirstChild("HumanoidRootPart")
    local human=character and character:FindFirstChildOfClass("Humanoid")
    if root and human and human.Health>0 then
     local rel=root.Position-center
     if math.abs(rel.X)<=32 and math.abs(rel.Z)<=9
      and rel.Y>=-4 and rel.Y<=10 then return true end
    end
   end
   return false
  end
  local function setRoute(enabled)
   open=enabled
   for _,tile in ipairs(segments) do
    tile.CanCollide=enabled
    tile.CanQuery=enabled
    tile.Transparency=if enabled then .08 else 1
   end
   stage:SetAttribute("PathOpen",enabled)
  end
  setRoute(false)
  task.spawn(function()
   while state.active and world.Parent and stage.Parent==core do
    task.wait(55)
    if not state.active or not world.Parent or stage.Parent~=core then break end
    label.Text="☄️ 5秒後に流星の道が出現!"
    task.wait(5)
    if not state.active or not world.Parent or stage.Parent~=core then break end
    setRoute(true)
    label.Text="🌠 流星ショートカット! 22秒!"
    task.wait(22)
    label.Text="🌠 安全確認中"
    -- Original RC86 bridge safety: no player may fall through a withdrawn tile.
    while state.active and world.Parent and stage.Parent==core and occupied() do
     task.wait(.5)
    end
    if not state.active or not world.Parent or stage.Parent~=core then break end
    setRoute(false)
    label.Text=""
   end
  end)
 end
 installLegacyMeteorRoute()
'''
NEW=''' installLegacyStarPath()
'''+PORT+''' -- A physical underwater cavern reachable by everyone. Water is represented'''

def digest(raw:bytes)->str:return hashlib.sha256(raw).hexdigest()

def patch(source:str)->str:
    if source.count(OLD)!=1 or FEATURE in source:
        raise ValueError("RED_METEOR66_PREVIOUS_STARRY_FEATURE_MISSING_OR_DOUBLE")
    for term in (
       "GQ8_RC86_STARRY_PATH_SINGLE_REALM_REAL66_20261119",
       'local function eligible(p,mode,world)',
       'local function install(world)',
       'local RunService = game:GetService("RunService")',
       'REAL65_LATE_HOST_WATCH_V1',
    ):
        if source.count(term)!=1:
            raise ValueError("RED_METEOR66_SINGLE_REALM_SOURCE_DRIFT_"+term[:24])
    out=source.replace(OLD,NEW,1)
    if out.replace(NEW,OLD,1)!=source or out.count(FEATURE)!=1:
        raise ValueError("RED_METEOR66_UNRELATED_CHANGE")
    for forbidden in ("RemoteEvent",":TakeDamage(","ProcessReceipt","DataStoreService","Instance.new(\"Script\")"):
        if source.count(forbidden)!=out.count(forbidden):
            raise ValueError("RED_METEOR66_SECOND_AUTHORITY")
    return out

def selftest():
    base="\n".join((
      'local RunService = game:GetService("RunService")',
      'local function eligible(p,mode,world)',
      'local function install(world)',
      'REAL65_LATE_HOST_WATCH_V1',
      'GQ8_RC86_STARRY_PATH_SINGLE_REALM_REAL66_20261119',
      OLD
    ))
    out=patch(base)
    for marker in ('task.wait(55)','task.wait(5)','task.wait(22)',
                   'while state.active and world.Parent and stage.Parent==core and occupied()',
                   'stage:SetAttribute("TemporaryBridgeParts",12)',
                   'local center=Vector3.new(x,y+12,z-145)'):
        assert marker in out,marker
    assert out.replace(NEW,OLD,1)==base
    for mutation in (out,base.replace('installLegacyStarPath()','installWrong()'),
                     base.replace('REAL65_LATE_HOST_WATCH_V1',''),
                     base+OLD):
        try:patch(mutation)
        except ValueError:pass
        else:raise AssertionError("RED_METEOR66_MUTANT_ACCEPTED")
    print("GQ8_OLD_RC86_METEOR_ROUTE_SEMANTICS_NEGATIVE_MUTATIONS_PASS")

def apply(project:Path,receipt:Path):
    p=json.loads(project.read_text(encoding="utf8"))
    r=json.loads(receipt.read_text(encoding="utf8"))
    selected={row["route"]:row for row in r.get("sources",[])}
    if p.get("name")!="EGGRUMBLE_REAL65_PRIVATE_STUDIO" or len(selected)!=65 or len(r["sources"])!=65:
        raise ValueError("RED_METEOR66_ORIGINAL65_PROFILE")
    if not r.get("rc86_starry_path") or not r.get("rc85_dojo_lobby_training") or r.get("rc86_meteor_shortcut"):
        raise ValueError("RED_METEOR66_PARENTS_OR_DOUBLE")
    if ROUTE not in selected or selected[ROUTE]["class"]!="Script":
        raise ValueError("RED_METEOR66_MISSING_CURRENT_REALM")
    original={}
    for route,row in selected.items():
        node=p["tree"]
        for seg in route.split("/"):node=node[seg]
        f=project.parent/node["$path"]
        data=f.read_bytes()
        if digest(data)!=row["sha256"] or len(data)!=row["bytes"]:
            raise ValueError("RED_METEOR66_PARENT_SHA_CLASS_"+route)
        original[route]=(f,data)
    file,data=original[ROUTE]
    updated=patch(data.decode("utf8")).encode("utf8")
    file.write_bytes(updated)
    selected[ROUTE]["sha256"]=digest(updated)
    selected[ROUTE]["bytes"]=len(updated)
    if sum(f.read_bytes()!=old for f,old in original.values())!=1:
        raise ValueError("RED_METEOR66_NOT_EXACT_ONE_ROUTE")
    r["rc86_meteor_shortcut"]={
      "feature_id":FEATURE,"original_flag":"METEOR_FOURTH_V1",
      "original_rc86_artifact":14161823401,
      "source":"ServerScriptService/TrapRaidersS1/MeteorFourth",
      "selected_live_script":ROUTE,"studio_only":True,
      "parent_starry_path_preserved":True,"legacy_explorer66_preserved":True,
      "quiet_seconds":55,"warning_seconds":5,"open_seconds":22,
      "original_timed_segments":12,"no_retract_while_occupied":True,
      "arena_modes":["TEAM","BATTLE_ROYALE"],"all_original65_selected":True,
      "unchanged_script_sources":64,"new_script_count":0,
      "new_remote":0,"new_score_store_damage_authority":0,
      "studio_engine":"NOT_TESTED","android":"NOT_TESTED","fun":"NO_GO",
      "rollback":"Revert only this original Realm overlay; keep previous Starfall, Realm4/Shard6, dojo, OFF63"}
    receipt.write_text(json.dumps(r,ensure_ascii=False,sort_keys=True,indent=2)+"\n",encoding="utf8")
    for route,row in selected.items():
        f=original[route][0];raw=f.read_bytes()
        if len(raw)!=row["bytes"] or digest(raw)!=row["sha256"]:
            raise ValueError("RED_METEOR66_FINAL_SOURCE_CONTRACT_"+route)
    print("GQ8_RC86_METEOR_SHORTCUT_55_5_22_SAFE_REAL66_SINGLE_REALM_PASS")

if __name__=="__main__":
    args=argparse.ArgumentParser()
    args.add_argument("--self-test",action="store_true")
    args.add_argument("--project",type=Path)
    args.add_argument("--receipt",type=Path)
    a=args.parse_args()
    if a.self_test:selftest()
    else:
        if not a.project or not a.receipt:args.error("missing project / receipt")
        apply(a.project,a.receipt)
