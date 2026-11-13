-- P0D native Luau Rule unit cases, no Roblox engine required.
local R=require("../src/client/D18MascotGuideRules")
local function snap(team,carrying,serial,update)
    return {kind="SNAPSHOT",team=team,carrying=carrying,serial=serial,updateId=update,phase="ACTIVE"}
end
local n=0
local function ok(x) assert(x);n+=1 end
local red=R.accept(snap("RED","",1,2),-1,-1)
ok(red~=nil)
ok(red.partName=="BLUE_EGG")
ok(red.objective=="EGG")
ok(red.destinationTeam=="BLUE")
local blue=R.accept(snap("BLUE","",1,2),-1,-1)
ok(blue.partName=="RED_EGG")
local carryRed=R.accept(snap("RED","BLUE",1,3),1,2)
ok(carryRed.partName=="RED_SCORE_PAD")
ok(carryRed.carrying==true)
local carryBlue=R.accept(snap("BLUE","RED",1,3),1,2)
ok(carryBlue.partName=="BLUE_SCORE_PAD")
ok(R.accept(snap("GREEN","",1,2),-1,-1)==nil)
ok(R.accept(snap("RED","",0,4),1,2)==nil)
ok(R.accept(snap("RED","",1,2),1,2)==nil)
ok(R.accept(snap("RED","",1,1),1,2)==nil)
ok(R.accept(snap("RED","",1,nil),1,2)==nil)
local bad=snap("RED","",1,2)
bad.phase="UNKNOWN"
ok(R.accept(bad,-1,-1)==nil)
bad=snap("RED","",1,2);bad.kind="EVENT"
ok(R.accept(bad,-1,-1)==nil)
bad=snap("RED","",1,2);bad.carrying=nil
ok(R.accept(bad,-1,-1)==nil)
bad=snap("RED","",1,2);bad.updateId=2.5
ok(R.accept(bad,-1,-1)==nil)
bad=snap("RED","",1,2);bad.serial=0/0
ok(R.accept(bad,-1,-1)==nil)
local nextRound=R.accept(snap("BLUE","",2,5),1,4)
ok(nextRound and nextRound.partName=="RED_EGG")
local legacy=R.accept(snap("RED","",0,nil),-1,-1)
ok(legacy and legacy.partName=="BLUE_EGG")
print("D18_NATIVE_GUIDE_RULES_PASS assertions="..tostring(n))
