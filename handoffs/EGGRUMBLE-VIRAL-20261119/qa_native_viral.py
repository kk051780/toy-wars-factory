#!/usr/bin/env python3
"""Generate exact-source-derived Luau CLI assertions + static gate, no mocked feature source."""
from pathlib import Path
import argparse
import json

root = Path(__file__).resolve().parents[2]
model = root / "releases/P0D_S1_KIDS_RC01/src/shared/ViralMomentPolicy.luau"
client = root / "releases/P0D_S1_KIDS_RC01/src/client/ViralMomentCapture.client.luau"
project = root / "releases/P0D_S1_KIDS_RC01/default.project.json"

def static_gate():
    source = model.read_text()
    user = client.read_text()
    m = json.loads(project.read_text())
    mapped = m["tree"]["StarterPlayer"]["StarterPlayerScripts"]
    assert mapped["TrapRaidersHUD"]["$path"] == "src/client/HUD.client.luau"
    assert mapped["TrapRaidersCoach"]["$path"] == "src/client/FirstMinuteCoach.client.luau"
    assert mapped["ViralMomentCapture"]["$path"] == "src/client/ViralMomentCapture.client.luau"
    assert m["tree"]["ReplicatedStorage"]["TrapRaidersShared"]["$path"] == "src/shared"
    assert source.count("function Moment.consume") == 1
    assert "recordSeconds" in source and "COMEBACK" in source and "LAST_STAND" in source
    assert "local armed = false" in user and "StartVideoCaptureAsync" in user
    assert "PromptSaveCapturesToGallery" in user and "StopVideoCapture" in user
    assert "CanCollide = false" in user and "CanTouch = false" in user
    for forbidden in ("FireServer(", "RemoteEvent.new", "DataStoreService", "MarketplaceService",
                      "HttpService", "TeleportService", "UploadCaptureAsync(",
                      "StartUploadCaptureAsync(", "PromptShareCapture(", "SocialService",
                      "https://", "http://"):
        assert forbidden not in user, "RED_CLIENT_EXTERNAL_AUTHORITY_" + forbidden
    for forbidden in ("FireServer(", "TakeDamage(", "Humanoid", "Instance.new(",
                      "RemoteEvent", "DataStoreService", "MarketplaceService"):
        assert forbidden not in source, "RED_VIEWMODEL_GAMEPLAY_WRITER_" + forbidden
    print("GQ8_VIRAL_STATIC_EXISTING_HUD_GAME_REMOTE_PRESERVED")

TEST = r'''
local function snap(serial, phase, team, carrying, red, blue, redhp, bluehp, winner)
  return {kind="SNAPSHOT",serial=serial,phase=phase,team=team,
    carrying=carrying,winner=winner,scores={RED=red,BLUE=blue},
    hp={RED=redhp,BLUE=bluehp},maxHp=300}
end
local m = Moment.new()
local p0 = snap(11,"ACTIVE","RED","",0,0,300,300,"")
assert(Moment.consume(m,p0,1)==nil,"bootstrap must not invent a capture")
local theft = snap(11,"ACTIVE","RED","BLUE",0,0,300,300,"")
local a = Moment.consume(m,theft,6)
assert(a and a.kind=="EGG_STEAL" and a.recordSeconds==15,"real own egg pick cue")
assert(Moment.consume(m,theft,6.5)==nil,"duplicate must not refire")
local wrong = snap(11,"ACTIVE","RED","BLUE",0,0,300,300,"")
wrong.kind="CLIENT_HINT"
assert(Moment.consume(m,wrong,7)==nil,"no invented client event")
local score = snap(11,"ACTIVE","RED","",1,0,300,300,"")
local b=Moment.consume(m,score,10)
assert(b and b.kind=="TEAM_SCORE","team score increment cue, not private credit")
local danger = snap(11,"ACTIVE","RED","",1,0,55,300,"")
local c=Moment.consume(m,danger,15)
assert(c and c.kind=="LAST_STAND","castle danger threshold")
local victory=snap(11,"RESULTS","RED","",1,0,55,300,"RED")
local d=Moment.consume(m,victory,16)
assert(d and d.kind=="COMEBACK","server-confirmed comeback wins over cooldown")
assert(Moment.consume(m,victory,17)==nil,"one result cue only")
local stale = snap(10,"ACTIVE","RED","BLUE",10,0,300,300,"")
assert(Moment.consume(m,stale,18)==nil,"stale match rejected")
local p1=snap(12,"ACTIVE","BLUE","",0,0,300,300,"")
assert(Moment.consume(m,p1,21)==nil,"new epoch bootstrap quiet")
local enemyScores=snap(12,"ACTIVE","BLUE","",1,0,300,300,"")
assert(Moment.consume(m,enemyScores,22)==nil,"opponent score is not our moment")
local loseresult=snap(12,"RESULTS","BLUE","",1,0,300,300,"RED")
assert(Moment.consume(m,loseresult,23)==nil,"no fake victory")
local m2=Moment.new()
assert(Moment.consume(m2,snap(1,"ACTIVE","BLUE","",0,0,300,300,""),1)==nil)
local bad = snap(1,"ACTIVE","BLUE","RED",0,0,300,300,"")
bad.maxHp=0
assert(Moment.consume(m2,bad,4)==nil,"invalid health must be rejected")
local good = snap(1,"ACTIVE","BLUE","RED",0,0,300,300,"")
assert(Moment.consume(m2,good,5).kind=="EGG_STEAL","valid after invalid")
print("GQ8_VIRAL_POLICY_REAL_SOURCE_NATIVE_PASS")
'''

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--out",required=True)
    args=parser.parse_args()
    static_gate()
    source=model.read_text()
    assert source.rstrip().endswith("return Moment")
    code = source + "\n" + TEST
    # Use the unmodified, full live source in the runtime test.
    # In standalone Luau script local 'Moment' is returned from a wrapper:
    code = "local Moment = (function()\n" + source + "\nend)()\n" + TEST
    dest=Path(args.out)
    dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(code)
    print("GQ8_VIRAL_NATIVE_SOURCE_GATED")

if __name__=="__main__":
    main()
