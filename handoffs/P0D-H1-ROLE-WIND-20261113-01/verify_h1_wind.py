#!/usr/bin/env python3
"""H1 Raider wind exact-source / genuine Luau / actual Rojo QA. No Roblox Studio claims."""
import argparse,collections,hashlib,json,pathlib,subprocess,tempfile,xml.etree.ElementTree as ET
P=pathlib.Path("releases/P0D_S1_KIDS_RC01")
BASE="3120b9d3c0a5ec58c9f2613c5d186f3493b54f83"
ALLOWED={
"releases/P0D_S1_KIDS_RC01/BUILD_MANIFEST.json",
"releases/P0D_S1_KIDS_RC01/src/server/Game.server.luau",
"releases/P0D_S1_KIDS_RC01/src/server/S1RaiderWindRules.luau",
"releases/P0D_S1_KIDS_RC01/src/client/HUD.client.luau"}
def source_check():
    diff=subprocess.check_output(["git","diff","--name-only",BASE,"HEAD","--",str(P)],text=True)
    assert set(diff.splitlines())==ALLOWED, ("source_diff",diff)
    files=json.loads((P/"BUILD_MANIFEST.json").read_text(encoding="utf8"))["files"]
    assert len(files)==38 and len({f["path"] for f in files})==38
    for f in files:
        path=pathlib.PurePosixPath(f["path"])
        assert not path.is_absolute() and ".." not in path.parts
        data=(P/path).read_bytes()
        assert hashlib.sha256(data).hexdigest()==f["sha256"] and len(data)==f["size"],f
    game=(P/"src/server/Game.server.luau").read_text(encoding="utf8")
    hud=(P/"src/client/HUD.client.luau").read_text(encoding="utf8")
    wind=(P/"src/server/S1RaiderWindRules.luau").read_text(encoding="utf8")
    for term in ('local WindRules = require','local function applyWind','WIND_BURST','windCooldown','windActive',
        'stopWind(player) -- cannot carry an egg at burst speed',
        'stopWind(player) -- Guardian trap always cancels Raider wind.',
        'CANONICAL_S1_ENABLED = false','D07_D08_RELEASE_REVIEW_APPROVED = false'):
        assert term in game,term
    assert game.count('remote.Name = "TrapRaidersS1Remote"')==1
    assert hud.count('action("WIND_BURST", nil)')==2
    # Egg-carrier/cooldown UX must match the existing server-failclosed policy.
    assert 'trapButton.Active = s.phase == "ACTIVE" and s.role == "GUARDIAN"' in hud
    assert 'not carryingEgg and trapCooldown == 0' in hud
    assert 'windButton.Active = s.phase == "ACTIVE" and s.role == "RAIDER"' in hud
    assert 'not carryingEgg and windCooldown == 0 and s.windActive ~= true' in hud
    assert '🥚 卵運搬中' in hud and '風走り不可' in hud
    assert 's.role ~= "RAIDER"' in wind and 's.carrying == true' in wind
    print("P0D_H1_WIND_SOURCE_MANIFEST_38_OF_38_PASS")

def xml_check(filepath):
    tree=ET.parse(filepath)
    source=[]
    for item in tree.iter("Item"):
        if item.attrib.get("class") not in ("Script","LocalScript","ModuleScript"):continue
        props=item.find("Properties")
        assert props is not None
        val=next((p.text or "" for p in props if p.attrib.get("name")=="Source"),None)
        assert val is not None
        source.append(val)
    scripts=list((P/"src").rglob("*.luau"))
    assert len(scripts)==22 and len(source)==22,(len(scripts),len(source))
    assert collections.Counter(source)==collections.Counter(f.read_text(encoding="utf8") for f in scripts)
    print("P0D_H1_WIND_REAL_ROJO_22_OF_22_EMBEDDED_SOURCE_PASS")

TEST=r"""
local W = Wind
local function copy(x) local y={} for k,v in pairs(x) do y[k]=v end return y end
local s={phase="ACTIVE",team="RED",role="RAIDER",alive=true,carrying=false,
    slowed=false,active=false,now=20,lastAt=-math.huge,x=0,y=5,z=0}
assert(W.canActivate(s))
local b=copy(s);b.team="BLUE";assert(W.canActivate(b))
local function reject(k,v) local a=copy(s);a[k]=v;assert(not W.canActivate(a),k) end
reject("role","GUARDIAN");reject("team","NONE");reject("alive",false)
reject("phase","LOBBY");reject("phase","RESULTS")
reject("carrying",true);reject("slowed",true);reject("active",true)
reject("x",121);reject("x",-121);reject("z",66);reject("z",-66)
reject("y",0);reject("y",13);reject("now",0/0);reject("x",0/0);reject("lastAt",0/0)
local cool=copy(s);cool.lastAt=3;assert(not W.canActivate(cool))
local ready=copy(s);ready.lastAt=2;assert(W.canActivate(ready))
assert(W.COOLDOWN==18 and W.DURATION==2.5 and W.SPEED==27)
print("P0D_H1_WIND_NATIVE_POSITIVE_AND_NEGATIVE_PASS")
"""
BAD=[('s.role ~= "RAIDER"',"false"),('s.carrying == true',"false"),
('s.slowed == true',"false"),('s.active == true',"false"),('s.alive ~= true',"false"),
("s.now - s.lastAt < Wind.COOLDOWN","false"),("math.abs(s.x) > 120","false"),
("math.abs(s.z) > 65","false"),("s.y < 1","false")]
def native_check(luau):
    code=(P/"src/server/S1RaiderWindRules.luau").read_text(encoding="utf8")
    assert code.rstrip().endswith("return Wind")
    pre=code.rstrip()[:-len("return Wind")]
    def run(src):
        with tempfile.TemporaryDirectory() as td:
            f=pathlib.Path(td)/"wind_test.luau"
            f.write_text(src+"\n"+TEST+"\n",encoding="utf8")
            return subprocess.run([luau,str(f)],capture_output=True,text=True)
    p=run(pre)
    assert p.returncode==0,(p.stdout,p.stderr)
    print(p.stdout.strip())
    for key,new in BAD:
        assert pre.count(key)==1,key
        p=run(pre.replace(key,new,1))
        assert p.returncode!=0,("unsafe mutation accepted",key)
    print("P0D_H1_WIND_NATIVE_9_OF_9_UNSAFE_MUTANTS_REJECTED")
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--place")
    p.add_argument("--luau")
    a=p.parse_args()
    source_check()
    if a.place: xml_check(a.place)
    if a.luau: native_check(a.luau)
