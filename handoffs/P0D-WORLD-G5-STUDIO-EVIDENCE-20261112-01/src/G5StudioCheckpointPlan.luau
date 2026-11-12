--!strict
-- Engine-independent 5 FREE bidirectional walkthrough scripts. Used by the real
-- Studio-only server observer; native Luau can test the EXACT same Plan source.
local Plan = {}
Plan.VERSION = "G5_STUDIO_CHECKPOINTS_V1"
Plan.MAX_SPEED_STUDS_PER_SEC = 58
Plan.SAMPLE_INTERVAL = 0.20
Plan.LIMIT_PER_ROUTE_SECONDS = 300

local function p(x: number, y: number, z: number, radius: number, label: string)
    return {x=x,y=y,z=z,radius=radius,label=label}
end
local hub = p(0,3,0,14,"草原へ戻った")
local bridge = p(-68,3,-15,12,"あおい橋")
local dock = p(-108,3,-15,12,"港")
local seaBlue = p(-156.5,-10,-15,12,"あわの坂")
local seaBlueCastle = p(-205,-20,-15,14,"海底城の青い入口")
local seaGreen = p(-104.5,-10,30,12,"みどりの坂")
local seaGreenCastle = p(-205,-20,30,14,"海底城の緑の入口")
local skyYellowLow = p(57.5,14,-33,12,"黄色の坂")
local skyYellowHigh = p(135,38,-33,12,"黄色の上り坂")
local skyYellowCastle = p(175,50,-33,14,"天空城・黄色")
local skyPurpleLow = p(57.5,14,33,12,"紫の坂")
local skyPurpleHigh = p(135,38,33,12,"紫の上り坂")
local skyPurpleCastle = p(175,50,33,14,"天空城・紫")

Plan.ROUTES = {
    SEA_BRIDGE = {hub, bridge, dock, bridge, hub},
    SEA_BUBBLE_A = {hub, bridge, dock, seaBlue, seaBlueCastle, seaBlue, dock, bridge, hub},
    SEA_BUBBLE_B = {hub, seaGreen, seaGreenCastle, seaGreen, hub},
    SKY_RAINBOW_A = {hub, skyYellowLow, skyYellowHigh, skyYellowCastle, skyYellowHigh, skyYellowLow, hub},
    SKY_RAINBOW_B = {hub, skyPurpleLow, skyPurpleHigh, skyPurpleCastle, skyPurpleHigh, skyPurpleLow, hub},
}
Plan.ROUTE_ORDER = {"SEA_BRIDGE","SEA_BUBBLE_A","SEA_BUBBLE_B","SKY_RAINBOW_A","SKY_RAINBOW_B"}

local function finite(x: number): boolean
    return type(x)=="number" and x==x and x > -math.huge and x < math.huge
end

function Plan.advance(routeId: string, stage: number, x: number, y: number, z: number): (number, boolean)
    local route = Plan.ROUTES[routeId]
    if not route or not finite(stage) or stage < 1 or stage % 1 ~= 0 then return 1,false end
    if not (finite(x) and finite(y) and finite(z)) then return stage,false end
    if stage > #route then return stage,true end
    local current=route[stage]
    local dx,dy,dz=x-current.x,y-current.y,z-current.z
    if dx*dx+dy*dy+dz*dz > current.radius*current.radius then
        return stage,false
    end
    local nextStage=stage+1
    return nextStage,nextStage>#route
end

function Plan.validate(): (boolean,string)
    if #Plan.ROUTE_ORDER ~= 5 then return false,"wrong number of route IDs" end
    local keys={}
    for _,id in ipairs(Plan.ROUTE_ORDER) do
        if keys[id] or not Plan.ROUTES[id] then return false,"unknown or repeated route" end
        keys[id]=true
        local list=Plan.ROUTES[id]
        if #list < 5 or #list > 10 then return false,"impossible checkpoint plan" end
        if list[1]~=hub or list[#list]~=hub then return false,"must begin and return to free hub" end
        for i,pt in ipairs(list) do
            if not (finite(pt.x) and finite(pt.y) and finite(pt.z) and finite(pt.radius)
                and pt.radius >= 8 and pt.radius <= 15 and #pt.label >= 2) then
                return false,"invalid cue or checkpoint"
            end
            if i>1 and i<#list then
                if pt==hub then return false,"premature hub completing route" end
            end
        end
    end
    return true,"five routes with checkable walk out and return"
end

return Plan
