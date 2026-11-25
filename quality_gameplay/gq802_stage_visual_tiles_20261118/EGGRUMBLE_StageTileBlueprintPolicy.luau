--!strict
-- GQ802 B lane: original low-cost physical-visual tile blueprint data.
-- No damage, navigation, gravity, weather, shop, item, spawn or score authority.
local M={}
M.VERSION="DW_VISUAL_TILE_V1"
M.MAX_PARTS=42
M.CELL_COUNT=6
local ORDER={"CENTER","NORTH","SOUTH","SEA","SKY","WONDER"}
-- 25 authored visual variants. Color/geometry distinguish rare thematic silhouettes.
-- Values: primary rgb, accent rgb, silhouette shape, relative height.
local PRESETS={
 CASTLE_PLAZA={{181,153,94},{249,226,157},"TOWER",17},
 STAR_CRATER={{65,79,142},{152,220,255},"SPHERE",12},
 CLOCK_GARDEN={{156,122,81},{248,226,143},"RING",14},
 CANDY_MIRROR={{218,142,207},{132,223,235},"SPIRE",18},
 CLOUD_STAIR={{177,203,235},{255,251,218},"STEP",13},
 SKY_BRIDGE={{109,173,206},{221,252,255},"ARC",11},
 CRYSTAL_PASS={{119,188,221},{236,251,255},"SPIRE",20},
 METEOR_PATH={{94,90,164},{255,204,118},"SPHERE",15},
 EMBER_PASS={{142,70,64},{253,146,99},"SPIRE",18},
 ROOT_TUNNEL={{74,117,79},{200,217,108},"ARC",14},
 UNDERSEA_GLASS={{63,130,160},{136,241,222},"DOME",12},
 SAND_CLOCK_PATH={{196,150,108},{242,209,127},"RING",17},
 BUBBLE_HARBOR={{80,157,186},{200,248,251},"DOME",10},
 CORAL_CITY={{210,116,142},{125,232,190},"SPIRE",17},
 GHOST_DOCK={{107,115,152},{218,228,247},"ARC",14},
 TIDAL_CAVERN={{49,143,150},{163,244,237},"DOME",13},
 NEBULA_DOCK={{93,102,187},{174,220,255},"SPHERE",16},
 RAINBOW_ISLAND={{181,160,234},{253,243,196},"DOME",11},
 BEAST_ROOST={{133,103,77},{228,174,107},"TOWER",18},
 FLYING_CLOCK={{125,143,190},{251,219,137},"RING",14},
 ZERO_G_DOME={{81,98,167},{182,245,255},"DOME",13},
 HALO_PLAYGROUND={{226,205,145},{255,251,224},"RING",15},
 SHADOW_CARNIVAL={{100,56,107},{222,106,190},"TOWER",16},
 SLOW_TIME_BUBBLE={{124,183,184},{255,215,160},"SPHERE",12},
 CANDY_METEOR={{232,155,192},{252,235,118},"STEP",15},
}
local function part(name,kind,dx,dy,dz,sx,sy,sz,rgb,alpha)
 return {name=name,shape=kind,dx=dx,dy=dy,dz=dz,
   sx=sx,sy=sy,sz=sz,rgb={rgb[1],rgb[2],rgb[3]},
   transparency=alpha,anchored=true,canCollide=false,canTouch=false,canQuery=false}
end
function M.plan(manifest:any,stagePolicy:any):(any,string?)
 -- Mandatory exact original #803 policy must perform full recomposition validation
 -- on the server (not trusting a client supplied or mutated manifest).
 if type(stagePolicy)~="table" or type(stagePolicy.validate)~="function"
    or not stagePolicy.validate(manifest) then return nil,"INVALID_SERVER_MANIFEST" end
 if manifest.source~="SERVER_SEED_ONLY" or manifest.tileCount~=M.CELL_COUNT
    or manifest.castleAnchors~="PRESERVE_EXISTING_HOST_CASTLES"
    or manifest.eggAnchors~="PRESERVE_EXISTING_HOST_EGGS" then
     return nil,"UNSAFE_STAGE_OWNERSHIP"
 end
 local plan={version=M.VERSION,seed=manifest.seed,sourceVersion=manifest.version,
   tiles={},partCount=0,collisionParts=0,weatherOwner="EXISTING_REALM_WEATHER_ONLY",
   preservesCastleAndEggs=true,usesLegacyGroundRoutes=true,visualOnly=true}
 for index,tile in ipairs(manifest.tiles) do
  if index>M.CELL_COUNT or tile.slot~=ORDER[index] then return nil,"UNKNOWN_CELL" end
  local preset=PRESETS[tile.prefabId]
  if not preset then return nil,"UNKNOWN_PREFAB" end
  local primary,accent,silhouette,height=preset[1],preset[2],preset[3],preset[4]
  local details={
    part("TileFloorArt","Block",0,0.06,0,48,0.12,48,primary,0.52),
    part("RelicPedestal","Block",0,0.85,0,10,1.7,10,primary,0.1),
    part("RelicMonument",silhouette=="DOME" and "Ball" or silhouette=="SPHERE" and "Ball" or
       silhouette=="RING" and "Cylinder" or "Block",0,height/2+1.8,0,
       silhouette=="STEP" and 12 or 7,height,7,accent,0.20),
    part("LeftTrailMark","Block",-18,0.18,0,3,0.20,15,accent,0.42),
    part("RightTrailMark","Block",18,0.18,0,3,0.20,15,accent,0.42),
    part("ThemeBeacon","Ball",0,height+3,0,4,4,4,accent,0.40),
  }
  -- Every tile is visible from the existing safe walkways. The physical
  -- geometry is non-colliding deliberately, so it cannot trap egg carriers.
  local entry={slot=tile.slot,prefabId=tile.prefabId,theme=tile.theme,
    gridX=tile.gridX,gridZ=tile.gridZ,visualVariant=silhouette,parts=details,
    itemHint=tile.itemHint,decorativeOnly=true}
  plan.partCount+=#details
  plan.tiles[index]=entry
 end
 if #plan.tiles~=M.CELL_COUNT or plan.partCount>M.MAX_PARTS then
  return nil,"VISUAL_PART_BUDGET_EXCEEDED"
 end
 return plan,nil
end
function M.catalogCount():number
 local n=0
 for _ in pairs(PRESETS) do n+=1 end
 return n
end
return M
