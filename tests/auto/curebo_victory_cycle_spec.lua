-- Actual PR98+CUREBO and PR179+VICTORY joint game lifecycle test, native Lua 5.4 not Roblox Studio.
local H=dofile("tests/roblox_server_harness.lua")
local B=dofile("src/ToyWarsBalance.lua")
local function up(fn,name)
    for i=1,70 do local k,v=debug.getupvalue(fn,i);if not k then break end;if k==name then return v end end
    error("missing canonical upvalue "..name)
end
local h=H.new()
local p=h:addPlayer(h:newPlayer())
local heartbeat=h.runService.Heartbeat.listeners[1].fn
local state=assert(up(heartbeat,"sessions")[p])
local add=up(up(heartbeat,"simulate"),"addEntity")
local guardon=assert(add(state,"guardon","ally"))
local curebo=assert(add(state,"curebo","ally"))
local gm,cm=guardon.model,curebo.model
assert(gm.Parent and cm.Parent,"the two real 3D toy models exist")
guardon.health=50
curebo.cooldown=100
state.wave.Value=B.MAX_WAVE
state.enemyTarget=B.waveSize(B.MAX_WAVE)
state.enemiesMade=state.enemyTarget
state.enemyTimer=20
state.waveBreak=0
state.productionTimer=20
state.baseHP.Value=31
state.coins.Value=200
local level,kills=state.level.Value,state.kills.Value
h.runService.Heartbeat:Fire(0.3)
assert(h:status(p,"RoundOutcome").Value=="VICTORY","50th wave result is authoritative")
assert(state.wave.Value==1 and state.baseHP.Value==100,"new run has wave1 and full vault")
assert(#state.entities==0 and not gm.Parent and not cm.Parent,"both toy 3D models removed")
assert(state.coins.Value>=200+B.waveReward(B.MAX_WAVE),"coins include final-wave reward")
assert(state.level.Value==level and state.kills.Value==kills,"factory level and KOs preserved")
assert(state.waveBreak==5 and state.productionTimer==1,"new cycle restart cadence")
assert(not curebo.alive and not guardon.alive,"previous cycle actors are no longer active")
state.selected="curebo"
state.selectedValue.Value="CUREBO"
for _=1,5 do h.runService.Heartbeat:Fire(0.3) end
assert(#state.entities>=1 and state.entities[1].id=="curebo","new cycle can print fresh CUREBO")
assert(state.entities[1]~=curebo and state.entities[1].model.Parent,"fresh toy model is distinct")
print("AUTO_CUREBO_VICTORY_CYCLE_INTEGRATION_SUMMARY 1 passed / 0 failed; native Lua server mock, NOT Studio")
