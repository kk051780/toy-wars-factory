--!strict
-- GQ802 DW-STAGE-FACTORY: Pure, deterministic SERVER-ONLY stage planning.
-- This file deliberately does NOT create Parts, own weather or network endpoints,
-- change global gravity/time, teleport players or modify existing castle/egg owners.
local M = {}
M.VERSION = "DW_STAGE_V1"
M.MAX_PLAYERS = 16

local MODULUS = 2147483647
local MULTIPLIER = 48271
local SLOTS = {
    {id="CENTER",gridX=0,gridZ=0,kind="CROSS",safeRoute="CENTER_GROUND"},
    {id="NORTH",gridX=0,gridZ=-1,kind="GROUND",safeRoute="NORTH_GROUND"},
    {id="SOUTH",gridX=0,gridZ=1,kind="GROUND",safeRoute="SOUTH_GROUND"},
    {id="SEA",gridX=0,gridZ=2,kind="PORT",safeRoute="SOUTH_GROUND"},
    {id="SKY",gridX=0,gridZ=-2,kind="SKYPORT",safeRoute="NORTH_GROUND"},
    {id="WONDER",gridX=1,gridZ=0,kind="POCKET",safeRoute="CENTER_GROUND"},
}
-- Each prefab has the same certified footprint and universal ground access for
-- its slot; special movements are OPTIONAL advantages with clear counter routes.
-- These are identifiers for future artist-created PREFABS, not 3D runtime yet.
local CATALOG = {
    CENTER={
        {"CASTLE_PLAZA","REGAL",1,1,"PLAZA_SIGIL"},
        {"STAR_CRATER","COSMOS",0.75,1,"ASTEROID_RELIC"},
        {"CLOCK_GARDEN","TIME",1,0.75,"CLOCK_SEED"},
        {"CANDY_MIRROR","DREAM",1,1,"MIRROR_PRISM"},
    },
    NORTH={
        {"CLOUD_STAIR","HEAVEN",0.85,1,"CLOUD_BOOTS"},
        {"SKY_BRIDGE","SKY",1,1,"WIND_FEATHER"},
        {"CRYSTAL_PASS","ICE",1,1,"ICE_PRISM"},
        {"METEOR_PATH","COSMOS",1,1,"STAR_COMPASS"},
    },
    SOUTH={
        {"EMBER_PASS","UNDERWORLD",1,1,"EMBER_ORB"},
        {"ROOT_TUNNEL","FOREST",1,1,"FOREST_HEART"},
        {"UNDERSEA_GLASS","SEA",1,1,"SEA_PEARL"},
        {"SAND_CLOCK_PATH","TIME",1,0.9,"CLOCK_SEED"},
    },
    SEA={
        {"BUBBLE_HARBOR","SEA",1,1,"SEA_PEARL"},
        {"CORAL_CITY","SEA",1,1,"CORAL_SHELL"},
        {"GHOST_DOCK","DREAM",1,1,"GHOST_LANTERN"},
        {"TIDAL_CAVERN","SEA",1,1,"TIDE_COMPASS"},
    },
    SKY={
        {"NEBULA_DOCK","COSMOS",0.85,1,"STAR_COMPASS"},
        {"RAINBOW_ISLAND","HEAVEN",1,1,"CLOUD_BOOTS"},
        {"BEAST_ROOST","SKY",1,1,"BEAST_EGG"},
        {"FLYING_CLOCK","TIME",1,0.85,"CLOCK_SEED"},
    },
    WONDER={
        {"ZERO_G_DOME","COSMOS",0.55,1,"GRAVITY_ORB"},
        {"HALO_PLAYGROUND","HEAVEN",0.9,1,"HALO_PRISM"},
        {"SHADOW_CARNIVAL","UNDERWORLD",1,1,"SHADOW_MARBLE"},
        {"SLOW_TIME_BUBBLE","TIME",1,0.6,"CLOCK_SEED"},
        {"CANDY_METEOR","DREAM",1,1,"CANDY_STAR"},
    },
}
local WEATHERS = {"CLEAR","RAIN","STORM","SNOW","METEOR","AURORA"}
local function validInteger(value:any, minimum:number, maximum:number):boolean
    return type(value)=="number" and value==value and value>=minimum
        and value<=maximum and value%1==0
end
local function nextRandom(state:number):number
    return (state*MULTIPLIER)%MODULUS
end
local function nextOption(state:number, count:number):(number,number)
    local nextState=nextRandom(state)
    return nextState,1+(nextState%count)
end
local function createTile(slot:any, definition:any):any
    return {
        slot=slot.id, gridX=slot.gridX, gridZ=slot.gridZ,
        prefabId=definition[1], theme=definition[2],
        -- Scope is metadata only. Only #223's local-gravity authority can apply it.
        localGravityHint=definition[3], localTimeVfxHint=definition[4],
        itemHint=definition[5], optionalFantasy=true,
        footprintCells=1, connectWest=true, connectEast=true,
        universalGroundRoute=slot.safeRoute,
        recoveryExit=slot.safeRoute, noPaidAccess=true,
    }
end
local function makeWeather(id:string, startsAt:number):any
    return {
        id=id, startsAtSeconds=startsAt,
        warningSeconds=if id=="STORM" or id=="METEOR" then 3 else 0,
        effectOwner="EXISTING_REALM_WEATHER_ONLY",
        serverOwnsDamage=true, safeGroundAlternative=true,
    }
end
function M.build(seed:any, mode:any, playerCount:any):(any,string?)
    if not validInteger(seed,1,MODULUS-1) then return nil,"INVALID_SERVER_SEED" end
    if mode~="TEAM" and mode~="BR" then return nil,"INVALID_MODE" end
    if not validInteger(playerCount,2,M.MAX_PLAYERS) then return nil,"INVALID_PLAYER_COUNT" end
    local state=seed
    local tiles={}
    local uniqueTheme={}
    for _,slot in ipairs(SLOTS) do
        local candidates=CATALOG[slot.id]
        local index
        state,index=nextOption(state,#candidates)
        local tile=createTile(slot,candidates[index])
        tiles[#tiles+1]=tile
        uniqueTheme[tile.theme]=true
    end
    local weatherIndex
    state,weatherIndex=nextOption(state,#WEATHERS)
    local first=WEATHERS[weatherIndex]
    local secondIndex
    state,secondIndex=nextOption(state,#WEATHERS-1)
    if secondIndex>=weatherIndex then secondIndex=secondIndex+1 end
    local second=WEATHERS[secondIndex]
    -- Three phases preserve opening understanding and avoid a server-specific
    -- random storm at spawn. They only SELECT; Realm Core applies actual weather.
    local schedule={makeWeather("CLEAR",0),makeWeather(first,120),makeWeather(second,240)}
    local routeCount=0
    for _,slot in ipairs(SLOTS) do
        if slot.id=="CENTER" or slot.id=="NORTH" or slot.id=="SOUTH" then
            routeCount=routeCount+1
        end
    end
    local manifest={
        version=M.VERSION, source="SERVER_SEED_ONLY", seed=seed, mode=mode,
        playerCount=playerCount, tileCount=#tiles, tiles=tiles,
        weather=schedule, guaranteedGroundRoutes=routeCount,
        castleAnchors="PRESERVE_EXISTING_HOST_CASTLES",
        eggAnchors="PRESERVE_EXISTING_HOST_EGGS",
        fieldOrigin="RESOLVED_BY_EXISTING_MAP_BUILDER",
        worldClockAuthority="EXISTING_ROUND_CLOCK",
        globalGravityChange=false, globalTimeChange=false,
        sourceOnlyNoPhysicalMap=true,
        uniqueThemeCount=0,
    }
    for _ in pairs(uniqueTheme) do manifest.uniqueThemeCount=manifest.uniqueThemeCount+1 end
    -- Not a cryptographic signature: the server must exclusively build and hold
    -- the manifest; clients may only render a read-only description.
    return manifest,nil
end
function M.validate(manifest:any):boolean
    if type(manifest)~="table" or manifest.version~=M.VERSION then return false end
    local expected=M.build(manifest.seed,manifest.mode,manifest.playerCount)
    if not expected or manifest.source~=expected.source or manifest.tileCount~=expected.tileCount
        or manifest.uniqueThemeCount~=expected.uniqueThemeCount
        or manifest.fieldOrigin~=expected.fieldOrigin or manifest.worldClockAuthority~=expected.worldClockAuthority
        or type(manifest.tiles)~="table" or #manifest.tiles~=#expected.tiles
        or type(manifest.weather)~="table" or #manifest.weather~=#expected.weather
        or manifest.castleAnchors~=expected.castleAnchors
        or manifest.eggAnchors~=expected.eggAnchors
        or manifest.globalGravityChange~=false or manifest.globalTimeChange~=false
        or manifest.sourceOnlyNoPhysicalMap~=true
        or manifest.guaranteedGroundRoutes~=3 then return false end
    for i,tile in ipairs(expected.tiles) do
        local candidate=manifest.tiles[i]
        if type(candidate)~="table" or candidate.slot~=tile.slot
            or candidate.prefabId~=tile.prefabId
            or candidate.gridX~=tile.gridX or candidate.gridZ~=tile.gridZ
            or candidate.connectEast~=true or candidate.connectWest~=true
            or candidate.universalGroundRoute~=tile.universalGroundRoute
            or candidate.recoveryExit~=tile.recoveryExit
            or candidate.noPaidAccess~=true
            or candidate.localGravityHint~=tile.localGravityHint
            or candidate.localTimeVfxHint~=tile.localTimeVfxHint
            or candidate.itemHint~=tile.itemHint then return false end
    end
    for i,w in ipairs(expected.weather) do
        local check=manifest.weather[i]
        if type(check)~="table" or check.id~=w.id
            or check.startsAtSeconds~=w.startsAtSeconds
            or check.warningSeconds~=w.warningSeconds
            or check.effectOwner~=w.effectOwner
            or check.serverOwnsDamage~=true
            or check.safeGroundAlternative~=true then return false end
    end
    return true
end
return M
