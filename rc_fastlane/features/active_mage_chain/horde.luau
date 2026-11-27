-- The chain uses the same damage, knockback, KO receipts, and neutral pool as other attacks.
function Horde:mageChainLineOfSight(character: Model)
    local params=RaycastParams.new()
    params.FilterType=Enum.RaycastFilterType.Exclude
    params.FilterDescendantsInstances={character,self.folder}
    return function(from: Vector3,to: Vector3): boolean
        return workspace:Raycast(from,to-from,params)==nil
    end
end

function Horde:mageChainSeed(origin: Vector3,direction: Vector3,clear,previousSeed)
    if self.round<0 then return nil end
    return MageChain.seed(origin,self.mobs,function(neutral)
        if previousSeed and neutral~=previousSeed then return false end
        local unit,dist=horizontal(origin,neutral.pos)
        return (neutral.pos-origin).Magnitude<=Combat.SWEEP_RANGE
            and Combat.canSweep(dist,neutral.pos.Y-origin.Y,direction:Dot(unit),true)
            and clear(origin,neutral.pos)
    end)
end

function Horde:castMageChain(first,origin: Vector3,damage: number,now: number,stage: number,clear)
    if self.round<0 then return 0,0,{} end
    -- A link must see the previous neutral and the caster. A corner stays cover.
    local path=MageChain.path(first,self.mobs,stage,function(previous,target)
        return clear(previous,target) and clear(origin,target)
    end)
    local positions={}
    for index,neutral in ipairs(path) do positions[index]=neutral.pos end
    local previous=origin
    local defeated=0
    for index,neutral in ipairs(path) do
        local impact=positions[index]
        local unit,dist=horizontal(previous,impact)
        if self:damageNeutral(neutral,unit,dist,damage,now) then defeated+=1 end
        previous=impact
    end
    return #path,defeated,positions
end
