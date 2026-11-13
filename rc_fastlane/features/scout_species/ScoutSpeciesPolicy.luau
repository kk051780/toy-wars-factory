--!strict
-- P0D SCOUT SPECIES V1. Reuses the THREE already owned scout cosmetics.
-- Single source of bounded assault/guard balance; no Game/Remote/Store state.
local Species={}
local VARIANTS={
    default={name="まもりのスカウト",role="BALANCED",strikeScale=1,interval=12,maxStrikes=1,guardExtraHits=0,guardSeconds=5},
    forest={name="森のスカウト",role="SWIFT",strikeScale=.58,interval=2.3,maxStrikes=2,guardExtraHits=1,guardSeconds=5},
    star={name="星のスカウト",role="BURST",strikeScale=1.12,interval=12,maxStrikes=1,guardExtraHits=2,guardSeconds=5},
}
function Species.kind(cosmetic:any): string
    if cosmetic=="forest" then return "forest" end
    if cosmetic=="star" then return "star" end
    return "default"
end
function Species.label(kind:any,branch:any): string
    local data=VARIANTS[kind]
    if not data then return "スカウト" end
    if branch=="ASSAULT" then return data.name.."・攻撃型" end
    if branch=="GUARD" then return data.name.."・守護型" end
    return data.name
end
function Species.attack(kind:any,stage:any): (number,number,number)
    local data=VARIANTS[kind] or VARIANTS.default
    if type(stage)~="number" or stage~=stage or stage%1~=0 or stage<2 or stage>3 then
        return 0,12,0
    end
    local base=if stage>=3 then 40 else 26
    return base*data.strikeScale,data.interval,data.maxStrikes
end
function Species.guard(kind:any,stage:any): (number,number)
    local data=VARIANTS[kind] or VARIANTS.default
    if type(stage)~="number" or stage~=stage or stage%1~=0 or stage<2 or stage>3 then
        return 0,0
    end
    return (if stage>=3 then 5 else 3)+data.guardExtraHits,data.guardSeconds
end
return Species
