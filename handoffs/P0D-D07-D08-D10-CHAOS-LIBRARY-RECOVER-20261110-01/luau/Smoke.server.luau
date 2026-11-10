--!strict
-- Isolated Roblox Studio reference smoke test. Requires manual module paths.
local source = script.Parent
local chaos = require(source.ChaosEventCore)
local bosses = require(source.NeutralBossControlCore)
local timeCore = require(source.TimeSafetyCore)
local progress = require(source.FairProgressionFallback)
local state = chaos.new("test_m1", "S1", 0)
local boss = bosses.new("test_m1")
local time = timeCore.new("test_m1")
local p = progress.new("test_scope")
assert(select(2, chaos.classify(65,"S1")) == "GOROGAN")
local out, ev = chaos.advance(state, 20, 60, 65, true)
assert(out.phase == "TELEGRAPH" and ev.event == "WARNING")
assert(bosses.spawn(boss,"GOROGAN",20) == true)
local ok, reason = bosses.command(boss,20,1,"BLUE",{matchId="test_m1",team="BLUE",userId=1,
    serverRosterConfirmed=true,alive=true,hasRelicOrFreeTamerSkill=true,inNeutralZone=true,carryingEgg=false})
assert(ok == true and reason == "DIRECTED")
local recorded = timeCore.record(time,1,1,{x=1,y=2,z=3}, {matchId="test_m1",alive=true,
    safeFloor=true,carryingEgg=false})
assert(recorded == true)
local pos, note = timeCore.rewind(time,3,1,{matchId="test_m1",userId=1,alive=true,
    activeMatch=true,serverRosterConfirmed=true,carryingEgg=false},function(_,_) return true end)
assert(pos and pos.x == 1 and note == "RECALL_POSITION_ONLY")
local awarded, rewardStatus = progress.finalize(p,{matchId="m1",scope="test_scope",userId=1,
    job="WARRIOR",serverRoundFinalized=true,rosterConfirmed=true,duration=60,activeSeconds=20,
    meaningfulActionConfirmed=true,won=true,eggDelivered=true,
    assistTypes={DEFENSE=true,ESCORT=true,SUPPORT=true}})
assert(awarded and awarded.xpAwarded == 104 and awarded.masteryAwarded == 57 and rewardStatus == "FINALIZED")
print("TRAP_RAIDERS_OFFLINE_PACKET_SMOKE_PASS (isolated fixture, NOT live game)")
