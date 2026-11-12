--!strict
-- Only for an OWNER-enabled unpublished Roblox Studio observation bench.
-- This schedule is NOT the real rare-spawn policy; no "12%" gameplay claim.
local Plan = {}
Plan.VERSION = "P0D_RARE_2CLIENT_STUDIO_QA_BENCH_V1"
Plan.SLOT_SECONDS = 26
Plan.EXPOSURE_SECONDS = 23
Plan.PROMPT_DELAY_SECONDS = 2
Plan.ORDER = {"SPACE","CELESTIAL","EMBER","ECLIPSE"}
Plan.BASES = {
    SPACE = {x=25,y=-4,z=25},
    CELESTIAL = {x=-25,y=-4,z=25},
    EMBER = {x=-25,y=-4,z=-25},
    ECLIPSE = {x=25,y=-4,z=-25},
}
function Plan.at(elapsed:number)
    if type(elapsed)~="number" or elapsed~=elapsed or
        elapsed<0 or elapsed==math.huge or elapsed==-math.huge then
        return nil,0
    end
    local slot=math.floor(elapsed/Plan.SLOT_SECONDS)
    if slot>=4 then return nil,slot end
    local timeInSlot=elapsed-slot*Plan.SLOT_SECONDS
    if timeInSlot>=Plan.EXPOSURE_SECONDS then return nil,slot end
    return Plan.ORDER[slot+1],slot
end
function Plan.point(id:string): Vector3?
    local p=Plan.BASES[id]
    if not p then return nil end
    return Vector3.new(p.x,p.y,p.z)
end
function Plan.validate()
    if #Plan.ORDER~=4 or Plan.EXPOSURE_SECONDS>=Plan.SLOT_SECONDS or
       Plan.PROMPT_DELAY_SECONDS<1 or Plan.SLOT_SECONDS<20 then
        return false,"unsafe timing"
    end
    for i,id in ipairs(Plan.ORDER) do
        if not Plan.BASES[id] or select(1,Plan.at((i-1)*Plan.SLOT_SECONDS))~=id then
            return false,"world order mismatch"
        end
    end
    if select(1,Plan.at(4*Plan.SLOT_SECONDS))~=nil then
        return false,"benchmark must stop after four types"
    end
    return true,"exactly four deterministic unpublished visual observations"
end
return Plan
