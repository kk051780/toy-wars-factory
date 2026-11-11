--!strict
-- Original, engine-independent map route contract. Every route is FREE for all roles.
local Routes = {}
Routes.NODES = {
    LAND = {name="はじまりの草原", icon="🏰", height=2},
    SEA_DOCK = {name="青い港", icon="⚓", height=2},
    SEA_CASTLE = {name="海底ガラス城", icon="🐠", height=-22},
    SKY_CASTLE = {name="雲の浮遊城", icon="☁", height=49},
}
Routes.LINKS = {
    {id="SEA_BRIDGE", from="LAND", to="SEA_DOCK", direction="both", mode="walk", free=true, label="港へ", child_cue="あおい橋", counterplay="見える橋で守れる"},
    {id="SEA_BUBBLE_A", from="SEA_DOCK", to="SEA_CASTLE", direction="both", mode="walk", free=true, label="あわの階段", child_cue="あわをたどる", counterplay="入口が見える"},
    {id="SEA_BUBBLE_B", from="LAND", to="SEA_CASTLE", direction="both", mode="walk", free=true, label="ひみつの海底路", child_cue="みどりの矢印", counterplay="出口で待ち伏せできる"},
    {id="SKY_RAINBOW_A", from="LAND", to="SKY_CASTLE", direction="both", mode="walk", free=true, label="空の坂道", child_cue="きいろの坂", counterplay="空から見える"},
    {id="SKY_RAINBOW_B", from="LAND", to="SKY_CASTLE", direction="both", mode="walk", free=true, label="雲のうら道", child_cue="むらさきの坂", counterplay="鐘で接近が分かる"},
}
Routes.VERSION = "WORLD_LINK_G5_V1"
function Routes.edgesFrom(name)
    if Routes.NODES[name] == nil then return {} end
    local result = {}
    for _, e in ipairs(Routes.LINKS) do
        if e.from == name then
            table.insert(result, {id=e.id,nextNode=e.to})
        elseif e.to == name and e.direction == "both" then
            table.insert(result, {id=e.id,nextNode=e.from})
        end
    end
    return result
end
function Routes.reachable(from: string, target: string): boolean
    if Routes.NODES[from] == nil or Routes.NODES[target] == nil then return false end
    local seen: {[string]: boolean} = {[from]=true}
    local queue: {string}={from}
    local head=1
    while head <= #queue do
        local node=queue[head]; head += 1
        if node==target then return true end
        for _, edge in ipairs(Routes.edgesFrom(node)) do
            if not seen[edge.nextNode] then
                seen[edge.nextNode]=true
                table.insert(queue,edge.nextNode)
            end
        end
    end
    return false
end
function Routes.validate(): (boolean, string)
    local seen={}
    for _, e in ipairs(Routes.LINKS) do
        if seen[e.id] then return false,"duplicate route: "..e.id end
        seen[e.id]=true
        if Routes.NODES[e.from]==nil or Routes.NODES[e.to]==nil then return false,"orphan route" end
        if e.free~=true or e.mode~="walk" or e.direction~="both" then return false,"route not fair" end
        if #e.child_cue<2 or #e.counterplay<2 then return false,"missing kid cue or defense" end
    end
    for id in pairs(Routes.NODES) do
        if not Routes.reachable("LAND",id) then return false,"island unreachable: "..id end
        if not Routes.reachable(id,"LAND") then return false,"cannot return: "..id end
    end
    return true,"all routes reachable by free walking"
end
return Routes
