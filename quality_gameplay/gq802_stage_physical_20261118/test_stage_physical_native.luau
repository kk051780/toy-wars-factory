--!strict
-- Real pure Luau stage author #803 + this precise physical placement adapter.
local Stage=require("./EGGRUMBLE_StageManifestPolicy")
local Geometry=require("./EGGRUMBLE_StagePhysicalPlan")
local frame={x=0,y=10,z=0,halfX=380,halfZ=420}
local layouts={}
for seed=1,180 do
 local m,err=Stage.build(seed,"TEAM",16)
 assert(m and err==nil and Stage.validate(m),"VALID_POLICY_MANIFEST")
 local plan,e=Geometry.plan(m,frame)
 assert(plan and e==nil and #plan.tiles==6,"SIX_PHYSICAL_CELLS")
 assert(#plan.bridges==8 and plan.groundEntrances==3,"THREE_LAND_ROUTES_EIGHT_BRIDGES")
 assert(plan.maxParts<=48 and plan.noNewAuthority,"MOBILE_BUDGET")
 assert(plan.weatherOwner=="EXISTING_REALM_WEATHER_ONLY","SINGLE_WEATHER_AUTHORITY")
 for i,tile in ipairs(plan.tiles) do
  assert(tile.x-tile.size/2>frame.x+frame.halfX+24,"DO_NOT_OVERLAP_CASTLES_EGGS_FIELD")
  assert(tile.safeExit==m.tiles[i].universalGroundRoute,"SAFE_GROUND_EXIT")
  assert(tile.prefabId==m.tiles[i].prefabId and tile.itemHint==m.tiles[i].itemHint,"PREFAB_ITEM_METADATA")
 end
 for i=1,3 do
  assert(plan.bridges[i].kind=="GROUND","THREE_INDEPENDENT_GROUND_ENTRIES")
  assert(plan.bridges[i].sizeX>15 and plan.bridges[i].sizeZ>=18,"PLAYER_WALKABLE")
 end
 layouts[table.concat({plan.tiles[1].prefabId,plan.tiles[2].prefabId,plan.tiles[3].prefabId,
  plan.tiles[4].prefabId,plan.tiles[5].prefabId,plan.tiles[6].prefabId},"/")]=true
end
local count=0
for _ in pairs(layouts) do count+=1 end
assert(count>=90,"STAGE_VARIATION_90")
local sample=Stage.build(900,"BR",2)
assert(Geometry.plan(sample,frame)~=nil,"BR_TWOPLAYER")
sample.tiles[1].slot="FAKE"
assert(Geometry.plan(sample,frame)==nil,"REJECT_REORDERED_TILE")
sample=Stage.build(900,"TEAM",8)
sample.tiles[3].gridX=5
assert(Geometry.plan(sample,frame)==nil,"REJECT_UNSAFE_GRID")
sample=Stage.build(900,"TEAM",8)
sample.castleAnchors="MOVE_CASTLES"
assert(Geometry.plan(sample,frame)==nil,"NO_CASTLE_AUTHORITY")
sample=Stage.build(900,"TEAM",8)
sample.globalGravityChange=true
assert(Geometry.plan(sample,frame)==nil,"NO_GLOBAL_GRAVITY_CHANGE")
sample=Stage.build(900,"TEAM",8)
assert(Geometry.plan(sample,{x=0,y=0,z=0,halfX=3,halfZ=6})==nil,"NO_TINY_WORLD")
print("GQ802_STAGE_PHYSICAL_180_SEED_6_CELL_3_ROUTE_MUTANT_SAFE_NATIVE_PASS")
