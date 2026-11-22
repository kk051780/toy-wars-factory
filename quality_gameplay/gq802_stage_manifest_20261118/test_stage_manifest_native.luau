--!strict
-- Executed by native pinned Luau; tests deliberately mutate each dangerous boundary.
local M=require("./EGGRUMBLE_StageManifestPolicy")
assert(M.VERSION=="DW_STAGE_V1" and M.MAX_PLAYERS==16)
local layouts={}
local worlds={}
local stormCount=0
for seed=1,180 do
    local manifest,err=M.build(seed,"TEAM",16)
    assert(manifest and not err and M.validate(manifest))
    local nextManifest=M.build(seed,"TEAM",16)
    assert(M.validate(nextManifest))
    assert(#manifest.tiles==6 and #manifest.weather==3)
    assert(manifest.guaranteedGroundRoutes==3)
    assert(manifest.castleAnchors=="PRESERVE_EXISTING_HOST_CASTLES")
    assert(manifest.eggAnchors=="PRESERVE_EXISTING_HOST_EGGS")
    assert(not manifest.globalGravityChange and not manifest.globalTimeChange)
    assert(manifest.weather[1].id=="CLEAR" and manifest.weather[1].startsAtSeconds==0)
    local ids={}
    for index,tile in ipairs(manifest.tiles) do
        assert(tile.prefabId==nextManifest.tiles[index].prefabId)
        assert(tile.connectWest and tile.connectEast and tile.noPaidAccess)
        assert(tile.recoveryExit==tile.universalGroundRoute)
        assert(tile.localGravityHint>0 and tile.localGravityHint<=1)
        assert(tile.localTimeVfxHint>0 and tile.localTimeVfxHint<=1)
        ids[#ids+1]=tile.prefabId
        worlds[tile.theme]=true
    end
    layouts[table.concat(ids,"/")]=true
    local weather=manifest.weather
    assert(weather[2].startsAtSeconds==120 and weather[3].startsAtSeconds==240)
    assert(weather[2].id~=weather[3].id)
    assert(weather[2].id==nextManifest.weather[2].id)
    for _,w in ipairs(weather) do
        assert(w.effectOwner=="EXISTING_REALM_WEATHER_ONLY")
        assert(w.serverOwnsDamage and w.safeGroundAlternative)
        if w.id=="STORM" then
            stormCount=stormCount+1
            assert(w.warningSeconds>=3)
        end
    end
end
local unique=0
for _ in pairs(layouts) do unique=unique+1 end
assert(unique>=90)
for _,world in ipairs({"COSMOS","HEAVEN","UNDERWORLD","TIME","SEA","DREAM"}) do
    assert(worlds[world])
end
assert(stormCount>0)
local sample=M.build(729,"BR",2)
assert(sample and sample.mode=="BR" and M.validate(sample))
local invalidSeeds={0,-1,2147483647,0.5,math.huge,-math.huge}
for _,bad in ipairs(invalidSeeds) do
    local result,reason=M.build(bad,"TEAM",2)
    assert(result==nil and reason=="INVALID_SERVER_SEED")
end
assert(M.build("3","TEAM",2)==nil)
assert(M.build(3,"FAKE",2)==nil)
assert(M.build(3,"TEAM",17)==nil)
assert(M.build(3,"TEAM",1)==nil)
assert(M.build(3,"TEAM",2.5)==nil)
sample.tiles[1].prefabId="INJECTED"
assert(not M.validate(sample))
sample=M.build(729,"BR",2)
sample.tiles[2].connectEast=false
assert(not M.validate(sample))
sample=M.build(729,"BR",2)
sample.tiles[1].localGravityHint=0
assert(not M.validate(sample))
sample=M.build(729,"BR",2)
sample.weather[2].warningSeconds=-3
assert(not M.validate(sample))
sample=M.build(729,"BR",2)
sample.castleAnchors="MOVE_CASTLE"
assert(not M.validate(sample))
sample=M.build(729,"BR",2)
sample.globalGravityChange=true
assert(not M.validate(sample))
print("GQ802_NATIVE_180_SEEDS_LAYOUTS_WEATHER_FAIR_ROUTES_MUTATIONS_PASS")
