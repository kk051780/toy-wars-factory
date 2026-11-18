--!strict
-- Physical annex geometry only, reuses immutable #803 stage manifest data.
-- No Game/Combat/Weather/HP/Castle/Egg/Item/Remote/Teleport authority.
local M={}
M.CELL_STEP=120
M.PAD_SIZE=108
M.MAX_PARTS=48
local ORDER={"CENTER","NORTH","SOUTH","SEA","SKY","WONDER"}
local function finite(v:any):boolean
 return type(v)=="number" and v==v and math.abs(v)<1000000
end
function M.plan(manifest:any,frame:any):(any,string?)
 if type(manifest)~="table" or manifest.version~="DW_STAGE_V1"
  or manifest.source~="SERVER_SEED_ONLY" or manifest.tileCount~=6
  or type(manifest.tiles)~="table" or #manifest.tiles~=6
  or manifest.guaranteedGroundRoutes~=3 or manifest.castleAnchors~="PRESERVE_EXISTING_HOST_CASTLES"
  or manifest.eggAnchors~="PRESERVE_EXISTING_HOST_EGGS"
  or manifest.globalGravityChange~=false or manifest.globalTimeChange~=false
 then return nil,"BAD_MANIFEST_AUTHORITY" end
 if type(frame)~="table" then return nil,"BAD_BATTLEFIELD" end
 for _,name in ipairs({"x","y","z","halfX","halfZ"}) do
  if not finite(frame[name]) then return nil,"BAD_BATTLEFIELD" end
 end
 if frame.halfX<300 or frame.halfZ<350 then return nil,"BAD_BATTLEFIELD_SIZE" end
 local anchorX=frame.x+frame.halfX+108
 local tiles={}
 local seen={}
 for i,tile in ipairs(manifest.tiles) do
  local id=ORDER[i]
  if type(tile)~="table" or tile.slot~=id
   or type(tile.prefabId)~="string" or type(tile.theme)~="string"
   or type(tile.itemHint)~="string" or type(tile.gridX)~="number"
   or type(tile.gridZ)~="number" or tile.noPaidAccess~=true
   or tile.recoveryExit~=tile.universalGroundRoute
  then return nil,"BAD_TILE" end
  local gridX=if id=="WONDER" then 1 else 0
  local gridZ=if id=="NORTH" then -1 elseif id=="SOUTH" then 1
   elseif id=="SEA" then 2 elseif id=="SKY" then -2 else 0
  if tile.gridX~=gridX or tile.gridZ~=gridZ or seen[id] then
   return nil,"BAD_TILE_ORDER"
  end
  seen[id]=true
  tiles[#tiles+1]={
   slot=id,prefabId=tile.prefabId,theme=tile.theme,itemHint=tile.itemHint,
   x=anchorX+gridX*M.CELL_STEP, y=frame.y-0.6,
   z=frame.z+gridZ*M.CELL_STEP,
   size=M.PAD_SIZE, safeExit=tile.recoveryExit,
  }
 end
 -- Certified bridges: three independent grounded entries from core east edge;
 -- four north/south cell seams plus the WONDER cross-lane connector.
 -- No castle/egg moving or terrain replacement.
 local bridges={}
 for _,i in ipairs({1,2,3}) do
  local tile=tiles[i]
  local x1=frame.x+frame.halfX-8
  local x2=tile.x-M.PAD_SIZE/2+6
  if x2<=x1 then return nil,"BAD_EAST_LINK" end
  bridges[#bridges+1]={kind="GROUND",x=(x1+x2)/2,y=tile.y,z=tile.z,
   sizeX=x2-x1+12,sizeZ=18}
 end
 for _,z in ipairs({-1.5,-0.5,0.5,1.5}) do
  bridges[#bridges+1]={kind="SEAM",x=anchorX,y=frame.y-0.6,
   z=frame.z+z*M.CELL_STEP,sizeX=28,sizeZ=M.CELL_STEP-M.PAD_SIZE+18}
 end
 bridges[#bridges+1]={kind="WONDER",x=anchorX+M.CELL_STEP/2,y=frame.y-0.6,
  z=frame.z,sizeX=M.CELL_STEP-M.PAD_SIZE+18,sizeZ=28}
 local result={tiles=tiles,bridges=bridges,maxParts=M.MAX_PARTS,
  groundEntrances=3,sourceSeed=manifest.seed,
  weatherOwner="EXISTING_REALM_WEATHER_ONLY",
  noNewAuthority=true}
 return result,nil
end
return M
