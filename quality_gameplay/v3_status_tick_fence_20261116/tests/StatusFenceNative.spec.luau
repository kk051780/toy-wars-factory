--!strict
-- Run from native Luau CLI with sibling StatusFence.luau. Not Studio QA.
local M=require("./StatusFence")
local castle={alive=true}
local round={phase="ACTIVE",winner=nil,castles={["123"]=castle}}
local function check(want:boolean,r:any,id:any,c:any,same:any,alive:any)
 assert(M.canTick(r,round,id,c,same,alive)==want,"status tick boundary mismatch")
end
check(true,round,"123",castle,true,true)
check(false,{phase="ACTIVE",winner=nil,castles=round.castles},"123",castle,true,true)
round.phase="FINISHED";check(false,round,"123",castle,true,true);round.phase="ACTIVE"
round.winner="RED";check(false,round,"123",castle,true,true);round.winner=nil
castle.alive=false;check(false,round,"123",castle,true,true);castle.alive=true
check(false,round,"123",castle,false,true)
check(false,round,"123",castle,true,false)
check(false,round,"999",castle,true,true)
check(false,round,123,castle,true,true)
check(false,round,"123",{alive=true},true,true)
local old=round.castles
round.castles={["123"]=castle};check(true,round,"123",castle,true,true)
round.castles=nil;check(false,round,"123",castle,true,true)
round.castles=old
assert(M.canTick(nil,round,"123",castle,true,true)==false)
print("GQ_V3_STATUS_TICK_FENCE_NATIVE_13_CASES_PASS")
