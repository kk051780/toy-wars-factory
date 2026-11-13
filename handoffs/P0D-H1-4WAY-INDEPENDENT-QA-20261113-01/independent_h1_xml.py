#!/usr/bin/env python3
"""Independent cross-contract test of an ACTUAL Rojo-generated H1 private Studio Place.
Author #255 game and protected #220 RC are read-only. Never claim Studio test.
"""
import argparse,collections,hashlib,math,re,xml.etree.ElementTree as ET
from pathlib import Path
FIXED={"Game":"adecfee41a594bdd54393050b4890a5733a536ce",
"H1FunWorld":"cc764b9caaa293ff747489e02e607af4502ddca4",
"MapBuilder":"94655d019fdf9798fa24a350ebf49f8290465ac0",
"S1RaiderWindRules":"7d5706774b874759e7ab994dc0654c3ae9a46502",
"TrapRaidersHUD":"6d273404800e1d25fb1405bc52249b3ab47c1b41",
"D18Batch8Catalog":"41079553d2141940fc3fee57b23969e292770614",
"D18MascotGuideRules":"328b8a4d70261e633f163a5e166822a29d7eb1ba",
"D18MascotGuide":"39a2e35e4b2e8635d6d87359cd86f783aedf8756"}
ROUTES={"SKY_RAMP_RED","SKY_WALKWAY","SKY_RAMP_BLUE","SEA_LOW_CAUSEWAY","SEA_ENTRY_RED","SEA_ENTRY_BLUE"}
RX=re.compile(r'path\("([^"]+)",\s*Vector3\.new\((-?[\d.]+),(-?[\d.]+),(-?[\d.]+)\),\s*Vector3\.new\((-?[\d.]+),(-?[\d.]+),(-?[\d.]+)\),\s*([\d.]+)')
def ensure(ok,msg):
    assert ok,msg
def read(place):
    source={};cls={}
    for it in ET.parse(place).iter("Item"):
        cl=it.attrib.get("class")
        if cl not in ("Script","ModuleScript","LocalScript"):continue
        ps=it.find("Properties")
        ensure(ps is not None,"Properties missing")
        name=next((p.text for p in ps if p.attrib.get("name")=="Name"),None)
        code=next((p.text or "" for p in ps if p.attrib.get("name")=="Source"),None)
        ensure(name and code and name not in source,"missing/duplicate script")
        source[name]=code;cls[name]=cl
    ensure(len(source)==28,"incorrect complete game count")
    ensure(collections.Counter(cls.values())=={"Script":2,"LocalScript":4,"ModuleScript":22},"wrong server/client kind")
    return source,cls
def paths(world):
    found={}
    for m in RX.finditer(world):
        name=m.group(1);ensure(name not in found,"duplicate route")
        vals=list(map(float,m.groups()[1:]))
        found[name]=(vals[:3],vals[3:6],vals[6])
    ensure(set(found)==ROUTES,"not six routes")
    for key,(a,b,width) in found.items():
        ensure(8<=width<=20,"route width")
        ensure(all(-120<=p[0]<=120 and -65<=p[2]<=65 for p in (a,b)),"bounds")
        dx=b[0]-a[0];dz=b[2]-a[2]
        ensure(math.hypot(dx,dz)>=12 and abs(b[1]-a[1])<=.55*math.hypot(dx,dz),"ramp incline")
        xl,xu=min(a[0],b[0])-width/2,max(a[0],b[0])+width/2
        zl,zu=min(a[2],b[2])-width/2,max(a[2],b[2])+width/2
        for wx0,wx1 in ((-123,-83),(83,123)):
            for wz0,wz1 in ((-46.5,-41.5),(41.5,46.5)):
                ensure(not(xu>wx0 and xl<wx1 and zu>wz0 and zl<wz1),
                       "DECK_WALL_OVERLAP_"+key)
    ensure(found["SKY_RAMP_RED"][1]==found["SKY_WALKWAY"][0],"red sky join")
    ensure(found["SKY_RAMP_BLUE"][0]==found["SKY_WALKWAY"][1],"blue sky join")
    ensure(found["SEA_ENTRY_RED"][0]==found["SEA_LOW_CAUSEWAY"][0],"red sea join")
    ensure(found["SEA_ENTRY_BLUE"][0]==found["SEA_LOW_CAUSEWAY"][1],"blue sea join")
    return found
def audit(s,c,exact=True):
    if exact:
        for key,expected in FIXED.items():
            data=s[key].encode("utf8")
            got=hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()
            ensure(got==expected,"GIT_BLOB_MISMATCH_"+key)
    G=s["Game"];H=s["TrapRaidersHUD"];W=s["H1FunWorld"]
    D=s["D18MascotGuide"];R=s["D18MascotGuideRules"]
    ensure(c["Game"]=="Script" and c["H1FunWorld"]=="Script","wrong server")
    ensure(c["D18MascotGuide"]=="LocalScript" and c["TrapRaidersHUD"]=="LocalScript","wrong client")
    for q in ['remote.Name = "TrapRaidersS1Remote"','remote.OnServerEvent:Connect(','local function tickRound()']:
        ensure(G.count(q)==1,"DUPLICATE_GAME_AUTHORITY_"+q)
    for q in ['local CANONICAL_S1_ENABLED = false','local D07_D08_RELEASE_REVIEW_APPROVED = false',
        'elseif data.action == "WIND_BURST" then applyWind(player, data)',
        'Rules.validSeq(data.seq, lastSeq[player] or 0)',
        'WindRules.canActivate',
        'stopWind(player) -- cannot carry an egg at burst speed',
        'stopWind(player) -- Guardian trap always cancels Raider wind.',
        'if position.Y < -30 or math.abs(position.X) > 130','or math.abs(position.Z) > 76']:
        ensure(q in G,"SERVER_GUARD_MISSING_"+q)
    for q in ['s.role ~= "RAIDER"','s.carrying == true','s.slowed == true']:
        ensure(q in s["S1RaiderWindRules"],"WIND_DENIAL_MISSING_"+q)
    for q in ['s.role ~= "GUARDIAN"','s.carrying == true']:
        ensure(q in s["S1TrapRules"],"TRAP_DENIAL_MISSING_"+q)
    ensure('action("WIND_BURST", nil)' in H and 'action("PLACE_TRAP", nil)' in H and 'WIZARD' not in H,"WRONG_HUD_ACTION")
    ensure('if not RunService:IsStudio() then' in W and 'if not RunService:IsStudio() then return end' in D,"H1_STUDIO_GATE_MISSING")
    for q in ['Models.create("SPACE",creatures)','Models.create("CELESTIAL",creatures)','NoRewardNoD18Ownership']:
        ensure(q in W,"MISSING_OR_REWARDING_NEUTRAL_"+q)
    for q in ['Catalog.get("TRCA-BE-063")','ProximityPrompt','prompt.Triggered:Connect',
        'local nextView=Rules.accept(message,previousSerial,previousUpdate)',
        'ARENA:FindFirstChild(view.destinationTeam.."_CASTLE")']:
        ensure(q in D,"D18_NOT_PLAY_SCENE_CONNECTED_"+q)
    for q in ['s.kind~="SNAPSHOT"','local destTeam=if carrying then s.team else enemy',
      'local objective=if carrying then "SCORE_PAD" else "EGG"']:
        ensure(q in R,"D18_SERVER_SNAPSHOT_ROUTING_INCORRECT_"+q)
    ensure('name .. "_EGG"' in s["MapBuilder"] and 'name .. "_SCORE_PAD"' in s["MapBuilder"],"OBJECTIVES_MISSING")
    for name in ("D18MascotGuide","D18MascotGuideRules","D18Batch8Catalog","H1FunWorld"):
        for bad in ('DataStoreService','MarketplaceService','Instance.new("RemoteEvent")','Humanoid:TakeDamage','remote:FireServer'):
            ensure(bad not in s[name],"OTHER_GAMEPLAY_AUTHORITY_"+name+"_"+bad)
    paths(W)
def mutant_check(src,classes):
    cases=[
    ("Game",'local CANONICAL_S1_ENABLED = false','local CANONICAL_S1_ENABLED = true'),
    ("Game",'stopWind(player) -- cannot carry an egg at burst speed','-- removed wind cancel'),
    ("Game",'stopWind(player) -- Guardian trap always cancels Raider wind.','-- removed trap counter'),
    ("S1RaiderWindRules",'s.role ~= "RAIDER"','s.role ~= "GUARDIAN"'),
    ("S1RaiderWindRules",'s.carrying == true','false'),
    ("S1TrapRules",'s.role ~= "GUARDIAN"','s.role ~= "RAIDER"'),
    ("D18MascotGuideRules",'local destTeam=if carrying then s.team else enemy','local destTeam=enemy'),
    ("D18MascotGuide",'local nextView=Rules.accept(message,previousSerial,previousUpdate)','local nextView=message'),
    ("H1FunWorld",'if not RunService:IsStudio() then','if false then'),
    ("H1FunWorld",'Vector3.new(-86,0,32.5)','Vector3.new(-86,0,43)'),
    ("H1FunWorld",'path("SEA_ENTRY_RED"','blocked("SEA_ENTRY_RED"'),
    ("H1FunWorld",'Models.create("CELESTIAL",creatures)','Models.create("SPACE",creatures)'),
    ("D18MascotGuide",'prompt.Triggered:Connect','prompt.Disabled:Connect'),
    ("TrapRaidersHUD",'action("WIND_BURST", nil)','action("WIZARD", nil)'),
    ("H1FunWorld",'world.Parent=arena','Instance.new("RemoteEvent")\nworld.Parent=arena'),
    ("D18MascotGuide",'local root=Instance.new("Folder")','game:GetService("MarketplaceService")\nlocal root=Instance.new("Folder")')]
    for key,old,new in cases:
        ensure(old in src[key],"missing mutation anchor")
        s=dict(src);s[key]=s[key].replace(old,new,1)
        try:audit(s,classes,False)
        except AssertionError:continue
        raise AssertionError("unsafe mutation accepted:"+key+" "+old)
    return len(cases)
def main():
    p=argparse.ArgumentParser();p.add_argument("--place",required=True);args=p.parse_args()
    file=Path(args.place)
    src,classes=read(file);audit(src,classes)
    bad=mutant_check(src,classes)
    print("P0D_H1_4WAY_INDEPENDENT_ACTUAL_XML_PASS 28/28 GitBlob8/8 Routes6/6 UnsafeMutants%d/%d"%(bad,bad))
    print("RBXLX_BYTES",file.stat().st_size,"RBXLX_SHA256",hashlib.sha256(file.read_bytes()).hexdigest())
    print("STUDIO_2CLIENT_MOBILE_HUMAN_FUN=NOT_TESTED")
if __name__=="__main__":main()
