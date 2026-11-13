#!/usr/bin/env python3
"""Fail-closed source provenance and geometric-source QA. Studio physics not simulated."""
from pathlib import Path
import hashlib,json,math,re,subprocess
ROOT=Path(__file__).resolve().parents[1]
REPO=ROOT.parents[1]
BASE="3c537a551e173fffaf0e1039c90d04250313c6d8"
ORIGINAL="handoffs/P0D-H1-COMPOSITE-20261113-01/src/"
WORLD_BLOB="cc764b9caaa293ff747489e02e607af4502ddca4"
D18={
"src/client/D18Batch8Catalog.luau":"41079553d2141940fc3fee57b23969e292770614",
"src/client/D18MascotGuideRules.luau":"328b8a4d70261e633f163a5e166822a29d7eb1ba",
"src/client/D18MascotGuide.client.luau":"39a2e35e4b2e8635d6d87359cd86f783aedf8756"}
def check(ok,msg):
 if not ok:raise ValueError(msg)
def git(*args):
 return subprocess.check_output(["git",*args],cwd=REPO)
def blob(raw):
 return hashlib.sha1(b"blob "+str(len(raw)).encode()+bytes([0])+raw).hexdigest()
def verify_source():
 d=json.loads((ROOT/"BUILD_MANIFEST.json").read_text(encoding="utf8"))
 check(d.get("schema")=="P0D_H1_D18_WIND_WALLCLEAR_REAL_UNPUBLISHED_SRC_LOCK_V1","schema")
 check(d.get("source_count")==28 and d.get("original_25_count")==25,"source counts")
 src=d.get("source_files")
 check(isinstance(src,list) and len(src)==28,"script count")
 seen=set()
 for item in src:
  p=item["path"]
  check(p.startswith("src/") and ".." not in Path(p).parts and p not in seen,"unsafe or duplicate")
  check(p.endswith(".luau"),"not Luau")
  raw=(ROOT/p).read_bytes()
  check(blob(raw)==item["blob_sha1"] and len(raw)==item["bytes"],"source change "+p)
  seen.add(p)
 for p,sha in D18.items():
  check(p in seen and blob((ROOT/p).read_bytes())==sha,"D18 source lost "+p)
 world="src/server/H1FunWorld.server.luau"
 check(blob((ROOT/world).read_bytes())==WORLD_BLOB,"unvetted world overlay")
 originals=git("ls-tree","-r","--name-only",BASE,ORIGINAL).decode().splitlines()
 originals=[x for x in originals if x.endswith(".luau")]
 check(len(originals)==25,"base composite scripts")
 for path in originals:
  rel=path[len(ORIGINAL):]
  check(("src/"+rel) in seen,"base missing "+rel)
  if rel=="server/H1FunWorld.server.luau":continue
  check((ROOT/"src"/rel).read_bytes()==git("show",BASE+":"+path),"original game/role module overwritten "+rel)
 check(set(D18)|{"src/"+p[len(ORIGINAL):] for p in originals}==seen,"unclaimed source")
 return True
PATH_RE=re.compile(r'path\("([^"]+)",Vector3\.new\(([^)]+)\),Vector3\.new\(([^)]+)\),\s*(\d+)\s*,')
def paths(source):
 a={}
 for name,s,t,w in PATH_RE.findall(source):
  check(name not in a,"duplicate path")
  cv=lambda v:tuple(float(x.strip()) for x in v.split(","))
  a[name]=(cv(s),cv(t),float(w))
 return a
def overlap(a,b):
 return min(a[1],b[1])>max(a[0],b[0])
def geometry(source=None):
 src=source if source is not None else (ROOT/"src/server/H1FunWorld.server.luau").read_text(encoding="utf8")
 mapcode=(ROOT/"src/server/MapBuilder.luau").read_text(encoding="utf8")
 for t in ('Vector3.new(40, 14, 5)','Vector3.new(sign * 103, 7, z)','for _, z in ipairs({-44, 44})'):
  check(t in mapcode,"map wall contract "+t)
 p=paths(src)
 expected={"SKY_RAMP_RED","SKY_WALKWAY","SKY_RAMP_BLUE","SEA_LOW_CAUSEWAY","SEA_ENTRY_RED","SEA_ENTRY_BLUE"}
 check(set(p)==expected,"six actual connected segments")
 hits=[]
 for name,(a,b,w) in p.items():
  length=math.dist(a,b);horizontal=math.hypot(a[0]-b[0],a[2]-b[2])
  check(12<=length<220 and horizontal>0,"route length "+name)
  check(abs(a[1]-b[1])<=.55*horizontal,"slope "+name)
  check(10<=w<=18,"safe path width")
  check(all(abs(v[0])<=125 and abs(v[2])<=69 and v[1]>=-30 for v in (a,b)),"bounds")
  intervals=((min(a[0],b[0])-w/2,max(a[0],b[0])+w/2),
      (min(a[1],b[1])-2,max(a[1],b[1])+2),
      (min(a[2],b[2])-w/2,max(a[2],b[2])+w/2))
  for team in ("RED","BLUE"):
   for wz in (-44,44):
    wall_x=(-123,-83) if team=="RED" else (83,123)
    wall=(wall_x,(0,14),(wz-2.5,wz+2.5))
    if all(overlap(i,j) for i,j in zip(intervals,wall)):hits.append((name,team,wz))
 check(not hits,"SOLID_CASTLE_WALL_ROUTE_CONTACT "+repr(hits))
 check(p["SKY_RAMP_RED"][1]==p["SKY_WALKWAY"][0],"sky join red")
 check(p["SKY_WALKWAY"][1]==p["SKY_RAMP_BLUE"][0],"sky join blue")
 check(p["SEA_LOW_CAUSEWAY"][0]==p["SEA_ENTRY_RED"][0],"sea join red")
 check(p["SEA_LOW_CAUSEWAY"][1]==p["SEA_ENTRY_BLUE"][0],"sea join blue")
 check(p["SEA_ENTRY_RED"][0][0]<0 and p["SEA_ENTRY_BLUE"][0][0]>0,"symmetric teams")
 check(p["SEA_LOW_CAUSEWAY"][0][2]-p["SEA_LOW_CAUSEWAY"][2]/2>-69,"arena boundary")
 for name in ("SKY_RAMP_RED","SKY_RAMP_BLUE"):
  a,b,w=p[name]
  check(min(a[2],b[2])-w/2>26,"score pad occluded")
 for name in ("SEA_ENTRY_RED","SEA_ENTRY_BLUE"):
  a,b,w=p[name]
  check(max(abs(a[0]),abs(b[0]))+w/2<83,"sea entry wall")
 for marker in ('RunService:IsStudio()','FreeToAllRoles','TacticalAlternativeRoute','Models.create("SPACE"','Models.create("CELESTIAL"'):
  check(marker in src,"world marker "+marker)
 for forbidden in ('Instance.new("RemoteEvent")','MarketplaceService','DataStoreService','Humanoid:TakeDamage'):
  check(forbidden not in src,"world authority violation")
 return p
def contract(local=None,rules=None,project=None):
 local=local if local is not None else (ROOT/"src/client/D18MascotGuide.client.luau").read_text(encoding="utf8")
 rules=rules if rules is not None else (ROOT/"src/client/D18MascotGuideRules.luau").read_text(encoding="utf8")
 project=project if project is not None else json.loads((ROOT/"default.project.json").read_text(encoding="utf8"))
 for mark in ('if not RunService:IsStudio() then return end','D18Batch8Catalog','ProximityPrompt','OnClientEvent','CanCollide=false','CanTouch=false','CanQuery=false','state.lastHintName~=current.partName','current.partName'):
  check(mark in local,"guide contract "+mark)
 for bad in ('FireServer(','DataStoreService','MarketplaceService','Instance.new("RemoteEvent")','Humanoid:TakeDamage'):
  check(bad not in local and bad not in rules,"guide server authority violation "+bad)
 for mark in ('s.kind~="SNAPSHOT"','s.serial < previousSerial','update<=previousUpdate','if carrying then "SCORE_PAD" else "EGG"','if carrying then s.team else enemy'):
  check(mark in rules,"guide read-only contract "+mark)
 client=project["tree"]["StarterPlayer"]["StarterPlayerScripts"]
 check(set(client)>={"D18Batch8Catalog","D18MascotGuide","D18MascotGuideRules","TrapRaidersHUD","TrapRaidersCoach"},"project locals")
 check(client["D18MascotGuide"]["$path"]=="src/client/D18MascotGuide.client.luau","guide path")
 check(client["D18MascotGuideRules"]["$path"]=="src/client/D18MascotGuideRules.luau","guide rules path")
 check(client["D18Batch8Catalog"]["$path"]=="src/client/D18Batch8Catalog.luau","catalog path")
 check(project["tree"]["ServerScriptService"]["TrapRaidersS1"]["$path"]=="src/server","single game server")
 game=(ROOT/"src/server/Game.server.luau").read_text(encoding="utf8")
 hud=(ROOT/"src/client/HUD.client.luau").read_text(encoding="utf8")
 wind=(ROOT/"src/server/S1RaiderWindRules.luau").read_text(encoding="utf8")
 check('S1RaiderWindRules' in game and 'WIND_BURST' in game and 'WIND_BURST' in hud,"real wind role")
 check('Wind.COOLDOWN = 18' in wind and 'Wind.DURATION = 2.5' in wind and 'Wind.SPEED = 27' in wind,"role constants")
 check('TrapRaidersS1Remote' in game and 'RemoteEvent' in game,"real S1 authority")
 return True
if __name__=="__main__":
 verify_source()
 roads=geometry()
 contract()
 print("P0D_H1_UNIFIED_SOURCE_PROVENANCE_PASS original25 exactly except approved world + 3 exact D18 =>28")
 print("P0D_H1_CASTLE_WALL_GEOMETRY_STATIC_PASS routes="+str(len(roads))+" source_wall_overlap=0")
 print("P0D_H1_ONE_GAME_WIND_MASCOT_NO_SECOND_REMOTE_PASS")
