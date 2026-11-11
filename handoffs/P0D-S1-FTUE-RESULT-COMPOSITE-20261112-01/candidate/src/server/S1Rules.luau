--!strict
-- Pure server authority helpers. No client-provided damage, score or coordinates.
local Rules = {}
function Rules.opponent(team: string): string
    if team == "RED" then return "BLUE" end
    if team == "BLUE" then return "RED" end
    return "NONE"
end
function Rules.validSeq(seq: any, previous: number): boolean
    return type(seq) == "number" and seq == seq and seq % 1 == 0
        and seq > previous and seq >= 1 and seq <= 1000000000
end
function Rules.canInteract(phase: string, playerTeam: string, objectTeam: string,
    distance: number, maxDistance: number, alive: boolean): boolean
    return phase == "ACTIVE" and alive and (playerTeam == "RED" or playerTeam == "BLUE")
        and (objectTeam == "RED" or objectTeam == "BLUE")
        and distance >= 0 and distance <= maxDistance
end
function Rules.canSteal(phase: string, team: string, eggTeam: string,
    distance: number, alive: boolean, carrying: boolean, eggAtBase: boolean,
    maxDistance: number): boolean
    return Rules.canInteract(phase, team, eggTeam, distance, maxDistance, alive)
        and team ~= eggTeam and not carrying and eggAtBase
end
function Rules.canScore(phase: string, team: string, padTeam: string,
    distance: number, alive: boolean, carriedEggTeam: string?, ownEggAtBase: boolean,
    maxDistance: number): boolean
    return Rules.canInteract(phase, team, padTeam, distance, maxDistance, alive)
        and team == padTeam and carriedEggTeam == Rules.opponent(team) and ownEggAtBase
end
function Rules.canAttack(now: number, previousTime: number,
    phase: string, alive: boolean, cooldown: number): boolean
    return phase == "ACTIVE" and alive and now >= previousTime
        and now - previousTime >= cooldown
end
function Rules.damageCandidate(dx: number, dot: number, reach: number): boolean
    return dx <= reach and dx >= 0 and dot >= 0.1
end
function Rules.winner(scores: {[string]: number}, castles: {[string]: number}, cap: number): string?
    if scores.RED >= cap or castles.BLUE <= 0 then return "RED" end
    if scores.BLUE >= cap or castles.RED <= 0 then return "BLUE" end
    return nil
end
return Rules
