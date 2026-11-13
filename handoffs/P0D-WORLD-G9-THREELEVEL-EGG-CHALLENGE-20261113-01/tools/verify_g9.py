#!/usr/bin/env python3
"""G9 source provenance and negative regression assurance, not Roblox engine movement."""
from pathlib import Path
import hashlib,json,subprocess,re
ROOT=Path(__file__).resolve().parents[1]
REPO=ROOT.parents[1]
G8_SHA="bc096bea0400a19b7129dd0bc920697f983603f5"
G8_ROOT="handoffs/P0D-WORLD-G8-TRILAYER-TRANSPORT-20261113-01/src/"
def check(ok,msg):
 if not ok:raise ValueError(msg)
def git(*args):
 return subprocess.check_output(["git",*args],cwd=REPO)
def blob(raw):
 return hashlib.sha1(b"blob "+str(len(raw)).encode()+bytes([0])+raw).hexdigest()
def lock():
 m=json.loads((ROOT/"BUILD_MANIFEST.json").read_text(encoding="utf8"))
 check(m["schema"]=="P0D_G9_STANDALONE_THREE_LEVEL_EGG_TAG_PRIVATE_V1","schema")
 check(m["original_g8_sha"]==G8_SHA,"G8 pin")
 check(m["native_script_count"]==4 and m["game_integrated"]==False,"scope")
 check(m["field_cards"]==["WF-19","WF-20","WF-21"],"3 cards")
 targets={
  "src/G8TravelRules.luau","src/G8World.server.luau",
  "src/G9EggRules.luau","src/G9EggGame.server.luau",
  "default.project.json","FIELD_CARDS.md","README.md"
 }
 entries=m["source_files"]
 check(len(entries)==len(targets),"manifest size")
 paths=set()
 for f in entries:
  path=f["path"]
  check(path in targets and path not in paths,"unrecognized path "+path)
  data=(ROOT/path).read_bytes()
  check(blob(data)==f["git_blob_sha1"] and len(data)==f["bytes"],"SHA/bytes mismatch "+path)
  paths.add(path)
 check(paths==targets,"manifest missing")
 for name in ("G8TravelRules.luau","G8World.server.luau"):
  current=(ROOT/"src"/name).read_bytes()
  old=git("show",f"{G8_SHA}:{G8_ROOT}{name}")
  check(current==old,"original G8 source changed "+name)
 check(len(list((ROOT/"src").glob("*.luau")))==4,"source script count")
 return True
def contract(rule=None,server=None,world=None,project=None):
 rule=rule if rule is not None else (ROOT/"src/G9EggRules.luau").read_text(encoding="utf8")
 server=server if server is not None else (ROOT/"src/G9EggGame.server.luau").read_text(encoding="utf8")
 world=world if world is not None else (ROOT/"src/G8World.server.luau").read_text(encoding="utf8")
 project=project if project is not None else json.loads((ROOT/"default.project.json").read_text(encoding="utf8"))
 for name in (
   "R.WIN_SCORE=3","R.ACTION_COOLDOWN=.45","R.CARRY_LIMIT=45","R.MAX_DISTANCE_SQUARED=144",
   "function R.apply(state: any,action: any,team: any,userId: any,eggTeam: any,dist2: any,now: any)",
   'action~="STEAL" and action~="SCORE" and action~="RESCUE"',
   'state.carrier[eggTeam]=userId','if not state.home[team] then return false,"OWN_EGG_MISSING" end',
   'if state.carrier[enemy]~=userId then return false,"NO_ENEMY_EGG" end',
   'state.scores[team]+=1','if state.scores[team]>=R.WIN_SCORE then',
   'if eggTeam~=team then return false,"WRONG_RESCUE_TEAM" end',
   'if not finite(dist2) or dist2<0 or dist2>R.MAX_DISTANCE_SQUARED',
   'now-last<R.ACTION_COOLDOWN',
   'function R.release(state: any,userId: any)',
   'function R.expire(state: any,now: any)',
   'now-state.since[egg]>=R.CARRY_LIMIT',
   'return if team=="RED" then "BLUE" else "RED"',
 ):
  check(name in rule,"rule gate missing "+name)
 for name in (
   "if not RunService:IsStudio() then return end",
   'Workspace:WaitForChild("G8_PRIVATE_3LEVEL_TRAVEL",25)',
   "G9_PRIVATE_EGG_TAG_RAID",
   'pickup.Triggered:Connect(function(player)',
   'score.Triggered:Connect(function(player)',
   'tag.Triggered:Connect(function(rescuer)',
   'scout.Triggered:Connect(function(player)',
   'FindFirstChild("HumanoidRootPart")',
   'hum.Health<=0',
   'dist2(hrp.Position,egg.Position)',
   'dist2(hrp.Position,pad.Position)',
   'dist2(rescueRoot.Position,carrierRoot.Position)',
   'Rules.apply(state,"STEAL"',
   'Rules.apply(state,"SCORE"',
   'Rules.apply(state,"RESCUE"',
   'teamSizes.RED<=teamSizes.BLUE',
   'state=Rules.new()',
   'Rules.release(state,player.UserId)',
   'Rules.expire(state,os.clock())',
   'root.Name="G9_PRIVATE_EGG_TAG_RAID"',
   'G9DefenderTagRescue',
   'G9_SKY_PUBLIC_LOOKOUT',
   'if now-lastScout<10 then return end',
   'lookoutUntil=now+7',
   'gameToken+=1',
   'task.delay(6,function()',
 ):
  check(name in server,"server gate missing "+name)
 for disallowed in (
   'Instance.new("RemoteEvent")', 'FireServer(', 'OnServerEvent',
   'DataStoreService','MarketplaceService','HttpService','TeleportService',
   'Humanoid:TakeDamage','AssemblyLinearVelocity=Vector3.new(','_G.',
   'Workspace.Gravity', 'loadstring(', 'Debris:AddItem',
 ):
  check(disallowed not in server and disallowed not in rule,"new authority "+disallowed)
 for team in ("RED","BLUE"):
  check('team=="'+team+'"' in server,"team missing "+team)
 check('if not RunService:IsStudio() then return end' in world,"original G8 game release guard")
 check(world.count('prompt.Triggered:Connect(function(player)')==1,"real G8 trip preserved")
 check('Rules.validate(link.from,link.to' in world,"G8 verified portal still server verified")
 check('if state.carrier[team]==userId then return false,"ALREADY_CARRYING" end' in rule,
       "two-way simultaneous egg steal must be allowed")
 server_mount=project["tree"]["ServerScriptService"]["G9_Three_Level_Play"]
 check(len(server_mount)==5,"no other data model authority")
 for name in ("G8TravelRules","G8World","G9EggRules","G9EggGame"):
  check(server_mount[name]["$path"].startswith("src/"),"mount "+name)
 check("ReplicatedStorage" not in project["tree"] and "StarterPlayer" not in project["tree"],"standalone server only")
 return True
if __name__=="__main__":
 lock();contract()
 print("G9_ORIGINAL_G8_TWO_BYTE_EXACT_AND_NEW_TWO_GAME_AUTHORITY_SAFE_SOURCE_LOCK_PASS")

