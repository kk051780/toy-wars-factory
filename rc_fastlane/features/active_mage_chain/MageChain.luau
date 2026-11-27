--!strict
-- MAGE-025. Only server-owned neutral records are passed to these selectors.
local Chain = {}

Chain.cooldown = 20
Chain.energy = 40
Chain.tellSeconds = 0.24
Chain.targetsByStage = table.freeze({1, 2, 3, 4, 5})
Chain.hopByStage = table.freeze({4, 5, 6, 7, 8})

export type Neutral = {id: number, model: Model, pos: Vector3, hp: number}

function Chain.seed(origin: Vector3, mobs: {Neutral}, allowed: (Neutral) -> boolean): Neutral?
    local chosen: Neutral? = nil
    local nearest = math.huge
    for _, neutral in ipairs(mobs) do
        if neutral.hp <= 0 then continue end
        local distance = (neutral.pos - origin).Magnitude
        if (distance < nearest or (chosen and distance == nearest and neutral.id < chosen.id))
            and allowed(neutral) then
            chosen, nearest = neutral, distance
        end
    end
    return chosen
end

function Chain.path(first: Neutral, mobs: {Neutral}, stage: number,
        clear: (Vector3, Vector3) -> boolean): {Neutral}
    local index = stage + 1
    local limit, reach = Chain.targetsByStage[index], Chain.hopByStage[index]
    if first.hp <= 0 or not limit or not reach then return {} end
    local selected = {first}
    local visited = {[first.model] = true}
    while #selected < limit do
        local origin = selected[#selected].pos
        local nextNeutral = Chain.seed(origin, mobs, function(candidate)
            return not visited[candidate.model] and (candidate.pos - origin).Magnitude <= reach
                and clear(origin, candidate.pos)
        end)
        if not nextNeutral then break end
        visited[nextNeutral.model] = true
        table.insert(selected, nextNeutral)
    end
    return selected
end

return table.freeze(Chain)
