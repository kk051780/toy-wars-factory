--!nocheck
-- P0D H1: additive game integration. S1 remains sole round/egg/HP owner.
-- Exact original #232 creature Model + Policy modules are its siblings.
local RunService=game:GetService("RunService")
local Models=require(script.Parent:WaitForChild("RareEncounterModels"))
if not RunService:IsStudio() then
    warn("H1 private Studio source only; refused live execution")
    return
end
local arena=workspace:WaitForChild("TRAP_RAIDERS_S1",30)
if not arena then warn("H1 needs original S1 arena"); return end
assert(not arena:FindFirstChild("H1_FUN_WORLD"),"H1 duplicate overlay")
local world=Instance.new("Folder")
world.Name="H1_FUN_WORLD"
world:SetAttribute("PreviewOnly",true)
world:SetAttribute("NoNewGameAuthority",true)
world:SetAttribute("RealStudioQA","NOT_TESTED")
world.Parent=arena
local function rgb(r,g,b) return Color3.fromRGB(r,g,b) end
local count=0
local function part(name,size,cf,color,solid,mat)
    count+=1
    assert(count<=85,"H1_SCENE_PART_BUDGET")
    local p=Instance.new("Part")
    p.Name=name; p.Size=size; p.CFrame=cf
    p.Anchored=true; p.CanCollide=solid; p.CanTouch=false
    p.CanQuery=solid; p.Color=color
    p.Material=mat or Enum.Material.SmoothPlastic
    p.Parent=world
    return p
end
local function box(name,size,pos,color,solid,mat)
    return part(name,size,CFrame.new(pos),color,solid,mat)
end
local function path(name,a,b,width,color)
    local d=b-a
    assert(d.Magnitude>=12 and d.Magnitude<220,"H1_BAD_ROUTE")
    assert(math.abs(d.Y)<=0.55*math.sqrt(d.X^2+d.Z^2),"H1_RAMP_TOO_STEEP")
    local p=part(name,Vector3.new(width,2,d.Magnitude),
        CFrame.lookAt((a+b)*0.5,b),color,true)
    p:SetAttribute("FreeToAllRoles",true)
    p:SetAttribute("TacticalAlternativeRoute",true)
end
local function orb(name,pos,size,color,alpha)
    local p=box(name,size,pos,color,false,Enum.Material.Neon)
    p.Shape=Enum.PartType.Ball; p.Transparency=alpha; p.CastShadow=false
end
local function sign(name,pos,message)
    local anchor=box(name,Vector3.new(1,1,1),pos,rgb(255,255,255),false)
    anchor.Transparency=1
    local gui=Instance.new("BillboardGui")
    gui.Size=UDim2.fromOffset(220,65)
    gui.StudsOffsetWorldSpace=Vector3.new(0,4,0)
    gui.MaxDistance=130; gui.AlwaysOnTop=true; gui.Parent=anchor
    local text=Instance.new("TextLabel")
    text.Size=UDim2.fromScale(1,1)
    text.Text=message; text.TextScaled=true; text.Font=Enum.Font.GothamBold
    text.TextColor3=rgb(255,255,255)
    text.BackgroundColor3=rgb(36,47,87)
    text.BackgroundTransparency=0.2; text.Parent=gui
end
-- Existing 8-safe arena is 250x142. No alteration of eggs, castles or spawns.
-- TWO REAL PHYSICAL ALTERNATIVE ROUTES plus original center ground route.
path("SKY_RAMP_RED",Vector3.new(-91,0,43),Vector3.new(-52,16,43),15,rgb(143,216,255))
path("SKY_WALKWAY",Vector3.new(-52,16,43),Vector3.new(52,16,43),18,rgb(218,244,255))
path("SKY_RAMP_BLUE",Vector3.new(52,16,43),Vector3.new(91,0,43),15,rgb(143,216,255))
box("SKY_SAFETY_RAIL_1",Vector3.new(104,3,1),Vector3.new(0,19,33.5),rgb(119,176,225),true)
box("SKY_SAFETY_RAIL_2",Vector3.new(104,3,1),Vector3.new(0,19,52.5),rgb(119,176,225),true)
sign("SKY_SIGN_RED",Vector3.new(-78,5,43),"☁ そらのみち\nみんなで使えるよ")
sign("SKY_SIGN_BLUE",Vector3.new(78,5,43),"☁ そらのみち\n上から回り込もう")
local sea=box("COSMETIC_SEA",Vector3.new(222,0.2,29),Vector3.new(0,-0.72,-49),
    rgb(40,155,218),false,Enum.Material.Neon)
sea.Transparency=0.35
path("SEA_LOW_CAUSEWAY",Vector3.new(-99,0,-45),Vector3.new(99,0,-45),15,
    rgb(245,202,123))
sign("SEA_SIGN_RED",Vector3.new(-77,2,-48),"🌊 うみのみち\n敵も通れる")
sign("SEA_SIGN_BLUE",Vector3.new(77,2,-48),"🌊 うみのみち\n卵を運ぼう")
for i=-2,2 do
    orb("SEA_FOAM_"..tostring(i),Vector3.new(i*38,0,-60),
        Vector3.new(12,1.2,6),rgb(175,231,255),0.3)
end
-- Decorative distant sky castle; never pretends to be real S1 castle core.
box("FLOATING_SKY_ISLAND",Vector3.new(56,8,30),Vector3.new(0,62,43),
    rgb(103,194,151),false,Enum.Material.Grass)
for i,x in ipairs({-20,20}) do
    box("FLOATING_TOWER_"..i,Vector3.new(10,25,10),
        Vector3.new(x,79,43),rgb(238,240,252),false,Enum.Material.Marble)
    orb("FLOATING_TOWER_LIGHT_"..i,Vector3.new(x,93,43),
        Vector3.new(12,5,12),rgb(255,221,128),0.15)
end
orb("SKY_CROWN_BEACON",Vector3.new(0,101,43),
    Vector3.new(12,12,12),rgb(250,213,98),0.1)
for i=1,8 do
    orb("CLOUD_"..i,Vector3.new((i-4.5)*25,49+(i%3)*6,62),
        Vector3.new(25,7,12),rgb(245,248,255),0.3)
end
-- EXACT original #232 moving noncombat model implementation, not new AI.
local creatures=Instance.new("Folder")
creatures.Name="ORIGINAL_MOVING_FANTASY_CREATURES"
creatures.Parent=world
local whale=Models.create("SPACE",creatures)
local pegasus=Models.create("CELESTIAL",creatures)
for _,item in ipairs({whale,pegasus}) do
    item.model:SetAttribute("VisualPreviewOnly",true)
    item.model:SetAttribute("NoRewardNoD18Ownership",true)
    item.prompt.Triggered:Connect(function(player)
        if player then
            player:SetAttribute("H1_Found_"..item.id,true) -- session only
        end
    end)
end
local elapsed=0
local throttle=0
local beat
beat=RunService.Heartbeat:Connect(function(dt)
    if not world.Parent then beat:Disconnect(); return end
    if dt<=0 or dt>0.5 then return end
    elapsed+=dt; throttle+=dt
    if throttle<0.12 then return end
    throttle=0
    Models.update(whale,Vector3.new(-12,8,-18),elapsed)
    Models.update(pegasus,Vector3.new(36,9,12),elapsed)
end)
script.Destroying:Connect(function()
    if beat then beat:Disconnect() end
end)
world:SetAttribute("H1SceneParts",count)
world:SetAttribute("OriginalMovingCreatures",2)
print("P0D_H1_INTEGRATED_WORLD_ACTIVE; STUDIO_2CLIENT_MOBILE_NOT_TESTED")
