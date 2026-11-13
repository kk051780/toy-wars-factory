#!/usr/bin/env python3
"""Static/provenance/negative-gate test; not Roblox engine and cannot prove physics."""
from pathlib import Path
import hashlib,json,re
ROOT=Path(__file__).resolve().parents[1]
def check(ok,msg):
 if not ok:raise ValueError(msg)
def blob(raw):
 return hashlib.sha1(b"blob "+str(len(raw)).encode()+bytes([0])+raw).hexdigest()
def source():
 m=json.loads((ROOT/"BUILD_MANIFEST.json").read_text(encoding="utf8"))
 check(m["schema"]=="P0D_G8_THREE_TIER_SAFE_TRAVEL_PRIVATE_SHA1_V1","schema")
 check(m["feature_ids"]==["WF-16","WF-17","WF-18"],"cards")
 check(m["source_scripts"]==2 and m["real_source_server_trips"]==5,"count")
 check(len(m["source_files"])==5,"files")
 seen=set()
 for f in m["source_files"]:
  path=f["path"]
  check(path not in seen and not Path(path).is_absolute() and ".." not in Path(path).parts,"path")
  check(len(path)<=140,"too deep")
  b=(ROOT/path).read_bytes()
  check(blob(b)==f["git_blob_sha1"] and len(b)==f["bytes"],"unlocked "+path)
  seen.add(path)
 check(seen=={"src/G8TravelRules.luau","src/G8World.server.luau","default.project.json","FIELD_CARDS.md","README.md"},"unexpected")
 return True
def contract(world=None,rules=None,project=None,doc=None):
 world=world if world is not None else (ROOT/"src/G8World.server.luau").read_text(encoding="utf8")
 rules=rules if rules is not None else (ROOT/"src/G8TravelRules.luau").read_text(encoding="utf8")
 doc=doc if doc is not None else (ROOT/"FIELD_CARDS.md").read_text(encoding="utf8")
 project=project if project is not None else json.loads((ROOT/"default.project.json").read_text(encoding="utf8"))
 for name in ("if not RunService:IsStudio() then return end","G8_PRIVATE_3LEVEL_TRAVEL","G8_Private_Harbor_Spawn",
              "G8_SEA_GLASS_ROOF","G8_SKY_CASTLE_KEEP","G8_PORT_HARBOR_DECK",
              'part("G8_"..id.."_FLOOR",{76,2,76}',"G8_"+"SEA"+"_"+"GLASS_SIDE",
              'part("G8_"..id.."_SIDE_RAIL_"','part("G8_"..id.."_END_RAIL_"',
              'prompt.Triggered:Connect(function(player)','player.Character','FindFirstChild("HumanoidRootPart")',
              'FindFirstChildOfClass("Humanoid")','delta:Dot(delta)','Rules.validate(link.from,link.to',
              'Rules.destination(link.to)','character:PivotTo(CFrame.new(dst.x,dst.y,dst.z))',
              'hrp.AssemblyLinearVelocity=Vector3.zero','Players.PlayerRemoving:Connect',
              'prompt.MaxActivationDistance=12','prompt.KeyboardKeyCode=Enum.KeyCode.E',
              'prompt.ObjectText="みんな無料"','lastTrip[player]=now'):
  check(name in world,"world fails "+name)
 for x in ('R.MAX_DISTANCE_SQUARED=196','R.COOLDOWN=1.6',
           'PORT={SEA=true}', 'SEA={PORT=true,SKY=true}', 'SKY={PORT=true,SEA=true}',
           'R.NODES={', 'SEA={x=0,y=-28,z=150}', 'SKY={x=0,y=48,z=300}',
           'R.validate(from: any,dest: any','R.destination(dest: any)',
           'distSquared>R.MAX_DISTANCE_SQUARED','now-lastUsed<R.COOLDOWN',
           'health<=0','R.symmetricAccess'):
  check(x in rules,"rules fails "+x)
 for dangerous in ('RemoteEvent','FireServer(','DataStoreService','MarketplaceService','TeleportService',
                   'Humanoid:TakeDamage','Workspace.Gravity','_G.', 'loadstring','HttpService',
                   'BindToClose','OnServerEvent','Humanoid.WalkSpeed'):
  check(dangerous not in world and dangerous not in rules,"unapproved "+dangerous)
 links=re.findall(r'\{from="([A-Z]+)",to="([A-Z]+)",short="[^"]+",dx=-?\d+\}',world)
 check(links==[("PORT","SEA"),("SEA","PORT"),("SEA","SKY"),("SKY","SEA"),("SKY","PORT")],"real links")
 for a,b in links:
  check(f'{a}=' in rules and f'{b}=true' in rules,"graph route")
 for x in ("WF-16","WF-17","WF-18","Counterplay","Fail-safe","3秒ルール",
           "NOT_TESTED","Studio","海底","天空","スマホ","実コード"):
  check(x in doc,"design cards "+x)
 server=project["tree"]["ServerScriptService"]["G8_Three_Level_Demo"]
 check(server["G8TravelRules"]["$path"]=="src/G8TravelRules.luau","rules mount")
 check(server["G8World"]["$path"]=="src/G8World.server.luau","server mount")
 check("ReplicatedStorage" not in project["tree"] and "StarterPlayer" not in project["tree"],"not isolated")
 return True
if __name__=="__main__":
 source();contract()
 print("G8_THREE_REAL_LEVELS_FIVE_STRICT_TRIPS_NO_GAME_AUTHORITY_SOURCE_PASS")

