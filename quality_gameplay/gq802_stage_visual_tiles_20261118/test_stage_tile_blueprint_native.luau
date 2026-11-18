--!strict
-- Native actual Luau execution against immutable owner #803 real manifest policy.
local stage=require("./EGGRUMBLE_StageManifestPolicy")
local blueprint=require("./EGGRUMBLE_StageTileBlueprintPolicy")
assert(blueprint.VERSION=="DW_VISUAL_TILE_V1")
assert(blueprint.catalogCount()==25)
local encountered={}
local distinct={}
local renderedSamples=0
for seed=1,180 do
 local manifest=stage.build(seed,"TEAM",16)
 local plan,err=blueprint.plan(manifest,stage)
 assert(plan and not err,err)
 assert(plan.seed==seed and plan.sourceVersion=="DW_STAGE_V1")
 assert(plan.weatherOwner=="EXISTING_REALM_WEATHER_ONLY")
 assert(plan.partCount==36 and plan.partCount<=blueprint.MAX_PARTS)
 assert(plan.collisionParts==0 and plan.visualOnly)
 assert(plan.preservesCastleAndEggs and plan.usesLegacyGroundRoutes)
 assert(#plan.tiles==6)
 local again=blueprint.plan(stage.build(seed,"TEAM",16),stage)
 local signature={}
 for i,tile in ipairs(plan.tiles) do
  assert(tile.prefabId==again.tiles[i].prefabId)
  assert(tile.gridX==again.tiles[i].gridX and tile.gridZ==again.tiles[i].gridZ)
  assert(tile.decorativeOnly and #tile.parts==6)
  encountered[tile.prefabId]=true
  signature[#signature+1]=tile.prefabId
  for _,part in ipairs(tile.parts) do
   assert(part.anchored and not part.canCollide and not part.canTouch and not part.canQuery)
   assert(part.shape=="Block" or part.shape=="Ball" or part.shape=="Cylinder")
   assert(part.transparency>=0 and part.transparency<=1)
   assert(part.sx>0 and part.sy>0 and part.sz>0)
   assert(#part.rgb==3)
   for _,channel in ipairs(part.rgb) do assert(channel>=0 and channel<=255) end
  end
 end
 distinct[table.concat(signature,"|")]=true
 renderedSamples+=1
end
local seen=0
for _ in pairs(encountered) do seen+=1 end
assert(seen==25)
local variety=0
for _ in pairs(distinct) do variety+=1 end
assert(variety>=90)
local br=stage.build(2001,"BR",2)
assert(blueprint.plan(br,stage))
-- Host must reject modified/fake stages even when a piece has an allowed ID.
br.tiles[1].itemHint="PAID_ONLY"
assert(blueprint.plan(br,stage)==nil)
br=stage.build(2001,"BR",2)
br.weather[1].effectOwner="NEW_SECOND_WEATHER_OWNER"
assert(blueprint.plan(br,stage)==nil)
br=stage.build(2001,"BR",2)
br.eggAnchors="MOVE_EGGS"
assert(blueprint.plan(br,stage)==nil)
br=stage.build(2001,"BR",2)
br.tiles[1].prefabId="CUSTOM_CLIENT_TILE"
assert(blueprint.plan(br,stage)==nil)
assert(blueprint.plan({},stage)==nil)
assert(blueprint.plan({},{} )==nil)
assert(blueprint.plan(stage.build(1,"TEAM",16),nil)==nil)
print("GQ802_TILE_VISUAL_NATIVE_180_SEEDS_25_VARIANTS_36_NONCOLLIDING_PARTS_MUTANTS_PASS",
 renderedSamples,seen,variety)
