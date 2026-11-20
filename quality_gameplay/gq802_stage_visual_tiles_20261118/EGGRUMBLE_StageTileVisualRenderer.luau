--!nonstrict
-- GQ802 server-only physical visual renderer. This is NOT a second MapBuilder.
-- The existing battlefield remains the only collidable ground/route authority.
local M={}
local FOLDER_NAME="GQ802_VISUAL_TILE_STAGE_V1"
local SHAPES={Block=Enum.PartType.Block,Ball=Enum.PartType.Ball,
 Cylinder=Enum.PartType.Cylinder}

function M.render(world,originalFloor,manifest,stagePolicy,blueprint)
 if typeof(world)~="Instance" or typeof(originalFloor)~="Instance"
    or not originalFloor:IsA("BasePart") or not originalFloor:IsDescendantOf(world)
    or not world:IsDescendantOf(workspace) then return nil,"INVALID_HOST_WORLD" end
 if originalFloor.Size.X<600 or originalFloor.Size.Z<600 then
    return nil,"LEGACY_ARENA_TOO_SMALL" end
 if world:FindFirstChild(FOLDER_NAME) then return nil,"DUPLICATE_STAGE" end
 if type(blueprint)~="table" or type(blueprint.plan)~="function" then
    return nil,"NO_TRUSTED_BLUEPRINT" end
 local plan,errorCode=blueprint.plan(manifest,stagePolicy)
 if not plan or not plan.visualOnly or not plan.usesLegacyGroundRoutes
     or not plan.preservesCastleAndEggs or plan.partCount>42 then
    return nil,errorCode or "UNSAFE_VISUAL_PLAN" end
 -- Render inside one disposable world-owned folder. Never change the
 -- existing field, castle parts, egg prompts, neutral spawns, or item authority.
 local root=Instance.new("Folder")
 root.Name=FOLDER_NAME
 local step=math.min(originalFloor.Size.X,originalFloor.Size.Z)/5
 local made=0
 local ok,reason=pcall(function()
  for _,tile in ipairs(plan.tiles) do
   local cell=Instance.new("Model")
   cell.Name="Tile_"..tostring(tile.slot).."_"..tostring(tile.prefabId)
   cell.Parent=root
   local localX=tile.gridX*step
   local localZ=tile.gridZ*step
   for _,spec in ipairs(tile.parts) do
    if spec.canCollide or spec.canTouch or spec.canQuery
       or not spec.anchored or not SHAPES[spec.shape] then
       error("RED_UNSAFE_VISUAL_SPEC") end
    local p=Instance.new("Part")
    p.Name=spec.name
    p.Anchored=true
    p.CanCollide=false
    p.CanTouch=false
    p.CanQuery=false
    p.CastShadow=false
    p.Material=Enum.Material.SmoothPlastic
    p.Shape=SHAPES[spec.shape]
    p.Transparency=spec.transparency
    p.Color=Color3.fromRGB(spec.rgb[1],spec.rgb[2],spec.rgb[3])
    p.Size=Vector3.new(spec.sx,spec.sy,spec.sz)
    p.CFrame=originalFloor.CFrame*CFrame.new(localX+spec.dx,
        originalFloor.Size.Y/2+spec.dy,localZ+spec.dz)
    p.Parent=cell
    made+=1
   end
  end
  if made~=plan.partCount then error("RED_PART_COUNT_DRIFT") end
 end)
 if not ok then
  root:Destroy()
  return nil,"VISUAL_RENDER_FAILED:"..tostring(reason)
 end
 if not world.Parent or not originalFloor:IsDescendantOf(world) then
  root:Destroy()
  return nil,"MATCH_WORLD_DETACHED"
 end
 root:SetAttribute("SourceSeed",manifest.seed)
 root:SetAttribute("VisualOnly",true)
 root:SetAttribute("PartCount",made)
 root.Parent=world
 return root,nil
end

-- Host controls round destruction. No Heartbeat, remote, datastores or listeners.
function M.clear(world)
 if typeof(world)~="Instance" then return end
 local existing=world:FindFirstChild(FOLDER_NAME)
 if existing then existing:Destroy() end
end
return M
