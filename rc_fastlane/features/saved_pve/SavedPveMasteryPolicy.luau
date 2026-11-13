--!strict
-- P0D_SAVED_PVE_MASTERY_V1.
-- Pure policy; only the original server Game may call this after confirming
-- a DEV Store profile. Player attributes and client Remote data are NOT sources.
-- PvE MINION attack only. Never changes PvP, score, HP, XP, XP writes or Store.
local XP=require(script.Parent:WaitForChild("SessionSixSkillXPPreview"))
local Policy={}
Policy.MAX_MULTIPLIER=1.20
Policy.TIERS={
    {level=30,multiplier=1.20,name="MASTER"},
    {level=20,multiplier=1.15,name="ELITE"},
    {level=10,multiplier=1.10,name="ADEPT"},
    {level=5,multiplier=1.05,name="TRAINEE"},
}
function Policy.fromTraining(record:any): (number,string)
    if type(record)~="table" or type(record.totalsMicro)~="table" then
        return 1,"NONE"
    end
    local value=record.totalsMicro.WEAPON
    local viewed=XP.viewXP(value)
    if viewed.valid~=true or type(viewed.level)~="number" then
        return 1,"NONE"
    end
    for _,tier in ipairs(Policy.TIERS) do
        if viewed.level>=tier.level then
            return tier.multiplier,tier.name
        end
    end
    return 1,"NONE"
end
function Policy.mergeWithEarned(existing:any, saved:any): number
    if type(existing)~="number" or existing~=existing
        or existing==math.huge or existing==-math.huge then return 1 end
    if type(saved)~="number" or saved~=saved
        or saved==math.huge or saved==-math.huge then return math.clamp(existing,1,3.8) end
    -- Strongest wins, never multiply two buffs; preserve existing 3.8x minion cap.
    return math.clamp(math.max(existing,math.clamp(saved,1,Policy.MAX_MULTIPLIER)),1,3.8)
end
return Policy
