--!strict
-- D18 ORIGINAL EXACT SOURCE MODEL GALLERY. Local client ViewportFrame only, opt-in.
-- Each 'D18DetailModels/<group>' folder contains BYTE-UNCHANGED original factory+catalog modules.
-- The caller provides an entry with its 12-canon IDs; unknown IDs fail closed.
local Preview = {}
local modules = script.Parent:WaitForChild("D18DetailModels")
local MAP = {
    ["TRCA-BE-018"] = {"Mascots", "MascotPreviewFactory", 21},
    ["TRCA-ZO-054"] = {"Mascots", "MascotPreviewFactory", 16},
    ["TRCA-BE-072"] = {"Moon", "MoonGiraffeShowcase", 18},
    ["TRCA-SP-027"] = {"Resonance", "ShowcaseFactory", 15},
    ["TRCA-VE-090"] = {"Resonance", "ShowcaseFactory", 21},
    ["TRCA-TR-009"] = {"Star", "D18ShowcaseFactory", 18},
    ["TRCA-WE-045"] = {"Star", "D18ShowcaseFactory", 16},
    ["TRCA-SP-081"] = {"Trio", "D18ShowcaseFactory", 13},
    ["TRCA-VE-036"] = {"Trio", "D18ShowcaseFactory", 20},
    ["TRCA-ZO-108"] = {"Trio", "D18ShowcaseFactory", 21},
    ["TRCA-TR-063"] = {"FinalV8", "ShowcaseFactory", 21},
    ["TRCA-WE-099"] = {"FinalV8", "ShowcaseFactory", 27},
}
local active = setmetatable({}, {__mode = "k"})
local loaded = {}
local allowedPoses = {idle=true,tap=true,win=true,loss=true}
local function factoryFor(id)
    local spec = MAP[id]
    if not spec then return nil, "UNKNOWN_CHARACTER_ID" end
    local folder = modules:FindFirstChild(spec[1])
    local source = folder and folder:FindFirstChild(spec[2])
    if not source or not source:IsA("ModuleScript") then return nil, "SOURCE_MODULE_MISSING" end
    local key = spec[1]
    if loaded[key] then return loaded[key],nil end
    local ok, value = pcall(require, source)
    if not ok or type(value) ~= "table" then return nil, "SOURCE_REQUIRE_FAILED" end
    for _, method in ipairs({"Build", "SetPose", "SetLod", "Destroy", "GetStatus"}) do
        if type(value[method]) ~= "function" then return nil, "SOURCE_API_INCOMPLETE" end
    end
    loaded[key]=value
    return value,nil
end
function Preview.dispose(viewport)
    local rec = active[viewport]
    active[viewport]=nil
    if rec then
        -- Crucial: some untouched original factories have strong live counters.
        -- Destroy() must be called, not just viewport:ClearAllChildren().
        pcall(rec.factory.Destroy, rec.model)
    end
    if viewport and viewport:IsA("ViewportFrame") then
        viewport.CurrentCamera=nil
        for _, child in ipairs(viewport:GetChildren()) do
            if child:IsA("WorldModel") or child:IsA("Camera") then
                child:Destroy()
            end
        end
    end
end
function Preview.render(viewport,entry,yawDegrees,pose,far)
    assert(viewport and viewport:IsA("ViewportFrame"), "ViewportFrame required")
    Preview.dispose(viewport)
    if type(entry)~="table" or type(entry.id)~="string" then return nil,"INVALID_ENTRY" end
    local spec=MAP[entry.id]
    if not spec then return nil,"UNKNOWN_CHARACTER_ID" end
    if type(yawDegrees)~="number" or yawDegrees~=yawDegrees or math.abs(yawDegrees)>360000 then
        return nil,"INVALID_YAW"
    end
    if type(pose)~="string" or not allowedPoses[pose] then return nil,"INVALID_POSE" end
    if type(far)~="boolean" then return nil,"INVALID_LOD" end
    local factory,err=factoryFor(entry.id)
    if not factory then return nil,err end
    local world=Instance.new("WorldModel")
    world.Name="D18OriginalDetailPreviewOnly"
    world.Parent=viewport
    local stage=Instance.new("Folder")
    stage.Name="OriginalFactoryParent"
    stage.Parent=world  -- existing factories require Folder/Model/Workspace, never WorldModel directly
    local ok, model=pcall(function()
        if spec[1]=="Moon" then return factory.Build(stage,CFrame.new()) end
        return factory.Build(stage,entry.id,CFrame.new())
    end)
    if not ok or not model or not model:IsA("Model") or not model:IsDescendantOf(world) then
        if model and typeof(model)=="Instance" and model:IsA("Model") then pcall(factory.Destroy,model) end
        Preview.dispose(viewport)
        return nil,"ORIGINAL_SOURCE_BUILD_FAILED"
    end
    active[viewport]={factory=factory,model=model}
    local count=0
    for _, item in ipairs(model:GetDescendants()) do
        if item:IsA("BasePart") then
            count+=1
            if not item.Anchored or item.CanCollide or item.CanTouch or item.CanQuery then
                Preview.dispose(viewport)
                return nil,"SOURCE_SAFETY_REJECTED"
            end
        end
    end
    if count~=spec[3] then
        Preview.dispose(viewport)
        return nil,"SOURCE_PART_COUNT_DRIFT"
    end
    local poseOK, poseResult=pcall(factory.SetPose,model,pose)
    local lodOK, lodResult=pcall(factory.SetLod,model,far)
    if not poseOK or poseResult~=true or not lodOK or lodResult~=true then
        Preview.dispose(viewport)
        return nil,"SOURCE_POSE_OR_LOD_REJECTED"
    end
    -- Bounds-driven camera, recomputed after pose and rotation. Rotate around model visual center.
    local boundsCF,boundsSize=model:GetBoundingBox()
    local center=boundsCF.Position
    local turn=CFrame.new(center)*CFrame.Angles(0,math.rad(yawDegrees),0)*CFrame.new(-center)
    model:PivotTo(turn*model:GetPivot())
    boundsCF,boundsSize=model:GetBoundingBox()
    center=boundsCF.Position
    local extent=math.max(boundsSize.X,boundsSize.Y,boundsSize.Z)
    local camera=Instance.new("Camera")
    camera.FieldOfView=35
    camera.CFrame=CFrame.lookAt(center+Vector3.new(extent*1.5,extent*.85,math.max(7,extent*3)),center)
    camera.Parent=viewport
    viewport.CurrentCamera=camera
    viewport.BackgroundColor3=Color3.fromRGB(19,24,43)
    viewport.Ambient=Color3.fromRGB(195,199,217)
    viewport.LightColor=Color3.fromRGB(255,248,224)
    viewport.LightDirection=Vector3.new(-1,-1,-1)
    return model,factory.GetStatus(model)
end
function Preview.ids()
    local list={}
    for id,_ in pairs(MAP) do table.insert(list,id) end
    table.sort(list)
    return list
end
return Preview
