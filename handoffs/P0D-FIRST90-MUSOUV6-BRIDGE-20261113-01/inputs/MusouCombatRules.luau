--!strict
-- Pure shared server hit gates for the isolated MUSOU H1 candidate.
-- No Roblox Instance, no client data, no damage/score/XP authority.
local R={}
R.SWEEP_RANGE=13
R.SWEEP_MAX_VERTICAL=5
R.MOB_AGGRO_RANGE=26
R.MOB_AGGRO_MAX_VERTICAL=6
R.MINION_MELEE_RANGE=5
R.ELITE_MELEE_RANGE=9
R.MELEE_MAX_VERTICAL=4
local function finite(x:any):boolean
    return type(x)=="number" and x==x and x>-1e8 and x<1e8
end
function R.canAcquire(distance:any,dy:any):boolean
    return finite(distance) and distance>=0 and distance<=R.MOB_AGGRO_RANGE
        and finite(dy) and math.abs(dy)<=R.MOB_AGGRO_MAX_VERTICAL
end
function R.canSweep(distance:any,vertical:any,facing:any,visible:any):boolean
    return finite(distance) and distance>=0 and distance<=R.SWEEP_RANGE
        and finite(vertical) and math.abs(vertical)<=R.SWEEP_MAX_VERTICAL
        and finite(facing) and facing>=.1 and facing<=1.001
        and visible==true
end
function R.canMobStrike(distance:any,vertical:any,visible:any,elite:any):boolean
    local reach=if elite==true then R.ELITE_MELEE_RANGE else R.MINION_MELEE_RANGE
    return finite(distance) and distance>=0 and distance<=reach
        and finite(vertical) and math.abs(vertical)<=R.MELEE_MAX_VERTICAL
        and visible==true
end
return R
