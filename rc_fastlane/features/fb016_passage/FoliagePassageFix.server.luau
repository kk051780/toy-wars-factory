--!strict
-- FB-016 P0: RC78 owner's Studio report: large leafy/grass geometry blocks movement/sight.
-- Additive, reversible source. Never changes Game, eggs, damage, HP, saves or rounds.
local RunService=game:GetService("RunService")
if not RunService:IsStudio() then return end
local root=workspace:WaitForChild("TRAP_RAIDERS_S1",90)
if not root then return end
if root:GetAttribute("FB016_FOLIAGE_PASSAGE_FIX") then return end

local function decorativeFoliage(n:string):boolean
    return string.sub(n,1,13)=="FOREST_CROWN_"
        or string.sub(n,1,13)=="FOREST_TRUNK_"
        or string.sub(n,1,9)=="LeafMass_"
        or string.sub(n,1,13)=="BrushCluster_"
        or string.sub(n,1,10)=="RootFlare_"
        or string.sub(n,1,11)=="PALM_FROND_"
        or string.sub(n,1,17)=="COAST_PALM_TRUNK_"
end
local fixed=0
local function makePassable(obj:Instance)
    if not obj:IsA("BasePart") or not decorativeFoliage(obj.Name) then return end
    -- Only decorative woodland trees/leaf clumps. Castle gate, bridges,
    -- objectives, buildings, ground, terrain and real physical platforms stay solid.
    obj.CanCollide=false
    obj.CanTouch=false
    obj.CanQuery=false
    fixed+=1
end
for _,obj in ipairs(root:GetDescendants()) do makePassable(obj) end
root.DescendantAdded:Connect(makePassable)

-- The FB011 shoreline ground fragments have 4-stud sheer GRASS side faces.
-- Waterline / feet navigation should not hit a 4-stud vertical cliff.
-- Preserve each grass fragment's x,z footprint and exact top surface (-1).
-- Wait until the ocean ground masking step finishes to avoid racing its cloning.
local sea=root:WaitForChild("FB011_REAL_OCEAN_CHANNEL_V2",90)
local coastRepaired=false
if sea then
    local deadline=os.clock()+20
    while sea:GetAttribute("BuildComplete")~=true and os.clock()<deadline do
        task.wait(.1)
    end
    if sea:GetAttribute("BuildComplete")==true then
        local names={"SOUTH_MAINLAND","NORTH_HIGHLANDS","WEST_COAST_FLANK","EAST_COAST_FLANK"}
        local valid=true
        for _,name in ipairs(names) do
            local p=sea:FindFirstChild(name)
            if not p or not p:IsA("BasePart") or
                math.abs(p.Size.Y-4)>.1 or math.abs(p.Position.Y+3)>.1 then
                valid=false
                break
            end
        end
        if valid then
            for _,name in ipairs(names) do
                local p=sea:FindFirstChild(name) :: BasePart
                local oldTop=p.Position.Y+p.Size.Y/2
                p.Size=Vector3.new(p.Size.X,1,p.Size.Z)
                p.Position=Vector3.new(p.Position.X,oldTop-.5,p.Position.Z)
                p.CanCollide=true
                p.CanQuery=true
                p.CanTouch=false
            end
            coastRepaired=true
        else
            warn("FB016_SHORELINE_GEOMETRY_DRIFT_NO_MUTATION")
        end
    end
end
root:SetAttribute("FB016_FOLIAGE_PASSAGE_FIX",true)
root:SetAttribute("FB016_FOLIAGE_DECOR_COLLISIONS_REMOVED",fixed)
root:SetAttribute("FB016_SHORELINE_CLIFF_THINNED",coastRepaired)
root:SetAttribute("FB016_OWNER_STUDIO_RETEST","REQUIRED")
print("FB016_FOLIAGE_PASSAGE_APPLIED",fixed,coastRepaired)
