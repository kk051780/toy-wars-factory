#!/usr/bin/env python3
"""Strict source/UX safety checks. These do NOT simulate Roblox Studio engine physics."""
from pathlib import Path
import json,hashlib,subprocess
ROOT=Path(__file__).resolve().parents[1]
REPO=ROOT.parents[1]
ORIGIN="6d12ab03ce823ea41f85600b97890f1c84fbe8af"
OLD="handoffs/P0D-H1-D18-WIND-WORLD-WALLCLEAR-20261113-01/src/"
EDIT="client/D18MascotGuide.client.luau"
NEW="client/D18ObjectiveCompassRules.luau"
def fail(ok,msg):
 if not ok: raise ValueError(msg)
def git(*args):
 return subprocess.check_output(["git",*args],cwd=REPO)
def blob(b):
 return hashlib.sha1(b"blob "+str(len(b)).encode()+bytes([0])+b).hexdigest()
def verify_source():
 m=json.loads((ROOT/"BUILD_MANIFEST.json").read_text(encoding="utf8"))
 fail(m["schema"]=="P0D_H1_D18_OBJECTIVE_COMPASS_PRIVATE_SOURCE_LOCK_V1","schema")
 fail(m["original_h1_full_game_sha"]==ORIGIN,"source SHA")
 old=[p for p in git("ls-tree","-r","--name-only",ORIGIN,OLD).decode().splitlines() if p.endswith(".luau")]
 fail(len(old)==28,"original 28")
 for p in old:
  rel=p[len(OLD):]
  current=(ROOT/"src"/rel).read_bytes()
  if rel!=EDIT: fail(current==git("show",ORIGIN+":"+p),"original changed "+rel)
 fail((ROOT/"src"/NEW).exists(),"new compass missing")
 fail((ROOT/"src"/EDIT).read_bytes()!=git("show",ORIGIN+":"+OLD+EDIT),"no guide change")
 paths=set()
 for f in m["source_files"]:
  p=f["path"]
  fail(p.startswith("src/") and ".." not in Path(p).parts and p not in paths,"unsafe path")
  b=(ROOT/p).read_bytes()
  fail(blob(b)==f["git_blob_sha1"] and len(b)==f["bytes"],"manifest incorrect "+p)
  paths.add(p)
 fail(len(paths)==29 and m["real_script_count"]==29,"29 sources exact")
 fail(paths==({"src/"+p[len(OLD):] for p in old}|{"src/"+NEW}),"unexpected source")
 return True
def verify_contract(client=None,compass=None,project=None):
 client=client if client is not None else (ROOT/"src/client/D18MascotGuide.client.luau").read_text(encoding="utf8")
 compass=compass if compass is not None else (ROOT/"src/client/D18ObjectiveCompassRules.luau").read_text(encoding="utf8")
 project=project if project is not None else json.loads((ROOT/"default.project.json").read_text(encoding="utf8"))
 checks=(
  'if not RunService:IsStudio() then return end','D18ObjectiveCompassRules',
  'H1D18ObjectiveCompass','ProximityPrompt','OnClientEvent','CanCollide=false',
  'CanTouch=false','CanQuery=false','state.hintUntil=now+6',
  'goal.Position-avatar.Position','camera.CFrame.LookVector','camera.CFrame.RightVector',
  'Compass.angleDegrees','arrow.Rotation=angle','state.lastHintName~=current.partName',
  'guideGui:Destroy()','panel.Visible=false','panel.Visible=true')
 for name in checks:fail(name in client,"client gate "+name)
 for bad in ('FireServer(', 'Instance.new("RemoteEvent")', 'DataStoreService','MarketplaceService','Humanoid:TakeDamage','spawn(function'):
  fail(bad not in client and bad not in compass,"forbidden new authority "+bad)
 for name in ('math.atan2','if not (finite(rx)','target<0.25','heading<0.0001',
              'Compass.title','"じぶんの台の方向"','"敵の卵の方向"'):
  fail(name in compass,"pure math gate "+name)
 fail('drawPath(' not in client and 'clearHints(' not in client,"old fake breadcrumb still drawn")
 fail('local delta=goal.Position-avatar.Position' in client,"needs moving avatar, not static mascot anchor")
 fail('panel.Position=UDim2.new(.02,0,.30,0)' in client,"safe mobile panel top-left")
 fail('panel.Active=false' in client,"prevent mobile input capture")
 sp=project["tree"]["StarterPlayer"]["StarterPlayerScripts"]
 fail(sp.get("D18ObjectiveCompassRules",{}).get("$path")=="src/client/D18ObjectiveCompassRules.luau","compass Rojo wire")
 fail(sp.get("D18MascotGuide",{}).get("$path")=="src/client/D18MascotGuide.client.luau","existing guide wire")
 fail(project["tree"]["ServerScriptService"]["TrapRaidersS1"]["$path"]=="src/server","server original")
 game=(ROOT/"src/server/Game.server.luau").read_text(encoding="utf8")
 fail(game.count('remote.Name = "TrapRaidersS1Remote"')==1,"one match authority")
 return True
if __name__=="__main__":
 verify_source();verify_contract()
 print("P0D_H1_D18_COMPASS_27_ORIGINAL_BYTE_EXACT_1_REPLACED_1_ADDED_29_TOTAL_PASS")

