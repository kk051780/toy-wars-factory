--!strict
-- PRIVATE Studio ONLY: one-player egg + horde/gate practice (no PvP opponent).
-- Original published/live S1 requirements are never relaxed.
local Solo = {}

local function natural(n)
    return type(n)=="number" and n==n and n>=0 and n<math.huge
        and n%1==0
end

function Solo.isPractice(isStudio: boolean,players: number,red: number,blue: number): boolean
    if isStudio~=true or not natural(players) or not natural(red)
        or not natural(blue) then return false end
    return players==1 and ((red==1 and blue==0) or (red==0 and blue==1))
end

-- Public/two-player logic is identical to the frozen B42 source.
function Solo.canStart(isStudio: boolean,players: number,minPlayers: number,
    red: number,blue: number): boolean
    if not natural(players) or not natural(minPlayers)
        or not natural(red) or not natural(blue) then return false end
    if players>=minPlayers and red>0 and blue>0 then return true end
    return Solo.isPractice(isStudio,players,red,blue)
end

-- The non-participating team does not cause an immediate TEAM_EMPTY result
-- while one person practices; real TEAM_EMPTY works unchanged with >=2 players.
function Solo.allowTeamEmptyResult(isStudio: boolean,players: number,
    red: number,blue: number): boolean
    return not Solo.isPractice(isStudio,players,red,blue)
end

return Solo
