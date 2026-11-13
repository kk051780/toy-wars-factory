--!strict
-- EGG RAID RUMBLE: one game lobby selection. Pure rule, NO players service/remote/score.
local R={}
R.CLASSIC="CLASSIC"
R.SCORE="SCORE_5"
R.RATE_LIMIT=.4

function R.validMode(mode:any): boolean
    return mode=="CLASSIC" or mode=="SCORE_5"
end

function R.canVote(phase:any,mode:any,isStudio:any,now:any,previousAt:any): boolean
    if phase~="LOBBY" and phase~="COUNTDOWN" then return false end
    if not R.validMode(mode) then return false end
    if isStudio~=true and mode==R.SCORE then return false end
    if type(now)~="number" or now~=now or now<0 or now==math.huge then return false end
    if type(previousAt)~="number" or previousAt~=previousAt then return false end
    return now-previousAt>=R.RATE_LIMIT
end

function R.tally(votes:any,roster:any): (string,number,number)
    if type(votes)~="table" or type(roster)~="table" then
        return R.CLASSIC,0,0
    end
    local seen={}
    local classic=0
    local five=0
    for _,id in ipairs(roster) do
        if id~=nil and not seen[id] then
            seen[id]=true
            local vote=votes[id]
            if vote==R.CLASSIC then classic+=1
            elseif vote==R.SCORE then five+=1 end
        end
    end
    -- No vote / same votes = familiar Classic; children never start unexpected mode.
    return if five>classic then R.SCORE else R.CLASSIC,classic,five
end

return R
