--!strict
-- P0D_SAVED_BEAST_EVOLUTION_V1: pure original-Game-only DEV mastery adapter.
-- No remote, DataStore writer, profile migration, PvP attack, currency or items.
local XP=require(script.Parent:WaitForChild("SessionSixSkillXPPreview"))
local Beast={}
Beast.MAX_BONUS=1.20
local tiers={
    {level=30,power=1.20,kind="MYTHIC"},
    {level=20,power=1.15,kind="ELITE"},
    {level=10,power=1.10,kind="AWAKENED"},
    {level=5,power=1.05,kind="TRAINED"},
}
function Beast.saved(record:any): (number,number,string)
    if type(record)~="table" or type(record.totalsMicro)~="table" then
        return 1,1,"NONE"
    end
    local view=XP.viewXP(record.totalsMicro.BEAST)
    if view.valid~=true or type(view.level)~="number" then
        return 1,1,"NONE"
    end
    for _,tier in ipairs(tiers) do
        if view.level>=tier.level then
            return tier.power,view.level,tier.kind
        end
    end
    return 1,view.level,"NONE"
end
function Beast.choose(sessionMultiplier:any,savedMultiplier:any): number
    -- Existing dojo multiplier remains and cannot be reduced by stored mastery.
    -- New saved bonus is NOT stacked or multiplied with any session bonus.
    local session=if type(sessionMultiplier)=="number" and sessionMultiplier==sessionMultiplier
        and sessionMultiplier~=math.huge and sessionMultiplier~=-math.huge
        then math.clamp(sessionMultiplier,1,Beast.MAX_BONUS) else 1
    local saved=if type(savedMultiplier)=="number" and savedMultiplier==savedMultiplier
        and savedMultiplier~=math.huge and savedMultiplier~=-math.huge
        then math.clamp(savedMultiplier,1,Beast.MAX_BONUS) else 1
    return math.max(session,saved)
end
return Beast
