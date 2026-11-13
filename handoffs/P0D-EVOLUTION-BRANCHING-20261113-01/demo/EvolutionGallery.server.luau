--!strict
-- Independent original PRIVATE Studio-only visual evolution gallery.
-- NO original H1/H2 Game, inventory, FX authority, purchases or persistent save.
local RunService=game:GetService("RunService")
if not RunService:IsStudio() then return end
local Players=game:GetService("Players")
local world=Instance.new("Folder")
world.Name="EggRumbleOriginalEvolutionGallery"
world.Parent=workspace
local STEPS={
    {x=-56,stage=0,branch="NONE",name="幼体",sub="卵から生まれた小竜",
        base=Color3.fromRGB(114,224,180),s=0.85},
    {x=-28,stage=1,branch="NONE",name="成長体",sub="熟練Lv3・翼が成長",
        base=Color3.fromRGB(102,211,164),s=1.22},
    {x=0,stage=2,branch="ASSAULT",name="紅蓮進化",sub="熟練Lv6・攻撃分岐",
        base=Color3.fromRGB(251,107,80),s=1.45},
    {x=28,stage=2,branch="GUARD",name="蒼潮進化",sub="熟練Lv6・守備分岐",
        base=Color3.fromRGB(82,184,249),s=1.45},
    {x=56,stage=3,branch="ASSAULT",name="天龍神話体",sub="熟練Lv10・伝説の姿",
        base=Color3.fromRGB(250,181,70),s=2.05},
}
local function buildPart(parent,name,size,cf,color,shape,material)
    local p=Instance.new("Part")
    p.Name=name;p.Anchored=true;p.CanCollide=false;p.CanTouch=false
    p.CanQuery=false;p.CastShadow=true;p.Size=size;p.CFrame=cf;p.Color=color
    p.Material=material or Enum.Material.SmoothPlastic
    if shape then p.Shape=shape end
    p.Parent=parent
    return p
end
local function wedge(parent,name,size,cf,color)
    local w=Instance.new("WedgePart")
    w.Name=name;w.Size=size;w.CFrame=cf;w.Anchored=true
    w.CanCollide=false;w.CanTouch=false;w.CanQuery=false
    w.Color=color;w.Material=Enum.Material.SmoothPlastic
    w.Parent=parent
    return w
end
local function sign(p,title,subtitle)
    local bb=Instance.new("BillboardGui")
    bb.Name="EvolutionSign";bb.Size=UDim2.fromOffset(310,100)
    bb.StudsOffsetWorldSpace=Vector3.new(0,6,0)
    bb.AlwaysOnTop=true;bb.MaxDistance=170;bb.Parent=p
    local text=Instance.new("TextLabel")
    text.Size=UDim2.fromScale(1,1);text.BackgroundTransparency=.24
    text.BackgroundColor3=Color3.fromRGB(15,31,52)
    text.TextColor3=Color3.fromRGB(255,255,255)
    text.TextStrokeTransparency=.75
    text.TextScaled=true;text.Font=Enum.Font.GothamBold
    text.Text=title.."\n"..subtitle;text.Parent=bb
    local corner=Instance.new("UICorner")
    corner.CornerRadius=UDim.new(0,10)
    corner.Parent=text
end
buildPart(world,"IslandPlatform",Vector3.new(166,2,63),CFrame.new(0,-1,0),
    Color3.fromRGB(73,143,114),nil,Enum.Material.Grass)
buildPart(world,"CelestialBackdrop",Vector3.new(164,38,3),CFrame.new(0,18,-29),
    Color3.fromRGB(56,82,134),nil,Enum.Material.SmoothPlastic)
local spawn=Instance.new("SpawnLocation")
spawn.Name="GallerySpawn"
spawn.Size=Vector3.new(11,1,11)
spawn.Anchored=true;spawn.CanCollide=true
spawn.Position=Vector3.new(0,0.8,24)
spawn.Neutral=true;spawn.Color=Color3.fromRGB(109,184,238)
spawn.Parent=world

local displayModels={}
for index,info in ipairs(STEPS) do
    local pedestal=buildPart(world,"StagePedestal"..index,
        Vector3.new(17,1.7,19),CFrame.new(info.x,1,0),
        Color3.fromRGB(43,64,93),nil,Enum.Material.Slate)
    sign(pedestal,info.name,info.sub)
    local model=Instance.new("Model")
    model.Name="OriginalDragonEvolutionStage"..index
    local scale=info.s
    local pos=Vector3.new(info.x,6.7,0)
    local body=buildPart(model,"Body",Vector3.new(5,3,5)*scale,CFrame.new(pos),
        info.base,Enum.PartType.Ball)
    local headPos=pos+Vector3.new(0,1.7,-1.6)*scale
    buildPart(model,"Head",Vector3.new(3.8,3.4,3.7)*scale,CFrame.new(headPos),
        info.base,Enum.PartType.Ball)
    for _,sgn in ipairs({-1,1}) do
        local eyeOffset=Vector3.new(sgn*.91,.36,-1.65)*scale
        buildPart(model,"Eye"..sgn,Vector3.new(.48,.6,.48)*scale,
            CFrame.new(headPos+eyeOffset),Color3.fromRGB(23,32,57),Enum.PartType.Ball)
        local hornCf=CFrame.new(headPos+Vector3.new(sgn*1.0,1.8,.15)*scale)*
            CFrame.Angles(0,0,math.rad(sgn*17))
        wedge(model,"Horn"..sgn,Vector3.new(.8,1.9,1.2)*scale,hornCf,
            Color3.fromRGB(249,237,197))
        buildPart(model,"Foot"..sgn,Vector3.new(1.4,1.1,2.0)*scale,
            CFrame.new(pos+Vector3.new(sgn*1.5,-1.25,-.7)*scale),
            Color3.fromRGB(44,108,99),Enum.PartType.Ball)
        if info.stage>=1 then
            local wingBase=pos+Vector3.new(sgn*3.6,1.15,.6)*scale
            wedge(model,"Wing"..sgn,Vector3.new(3.6,.55,3.3)*scale,
                CFrame.new(wingBase)*CFrame.Angles(0,math.rad(sgn*15),math.rad(sgn*21)),
                info.stage==3 and Color3.fromRGB(250,239,156) or
                    Color3.fromRGB(200,242,240))
        end
        if info.stage>=2 then
            local spikeBase=pos+Vector3.new(sgn*1.3,.1,1.8)*scale
            wedge(model,"BackSpike"..sgn,Vector3.new(1.0,2.0,1.3)*scale,
                CFrame.new(spikeBase)*CFrame.Angles(math.rad(-14),0,0),
                info.branch=="ASSAULT" and Color3.fromRGB(252,210,98) or
                    Color3.fromRGB(117,233,248))
        end
    end
    local tail=buildPart(model,"Tail",Vector3.new(.85,1.0,4.2)*scale,
        CFrame.new(pos+Vector3.new(0,-.5,3)*scale)*CFrame.Angles(math.rad(18),0,0),
        info.base,Enum.PartType.Cylinder)
    if info.stage==3 then
        local aura=Instance.new("Highlight")
        aura.Name="MythicGlow";aura.FillColor=Color3.fromRGB(255,221,105)
        aura.FillTransparency=.82;aura.OutlineColor=Color3.fromRGB(255,252,196)
        aura.Parent=model
        local light=Instance.new("PointLight")
        light.Color=Color3.fromRGB(255,210,91);light.Brightness=1.5
        light.Range=18;light.Parent=body
        local stars=Instance.new("ParticleEmitter")
        stars.Name="MythicSparks"
        stars.Texture="rbxasset://textures/particles/sparkles_main.dds"
        stars.Rate=9;stars.Lifetime=NumberRange.new(.45,1)
        stars.Speed=NumberRange.new(.4,1.8)
        stars.Size=NumberSequence.new(.28)
        stars.Parent=body
    end
    model.PrimaryPart=body;model.Parent=world
    displayModels[index]={model=model,pivot=model:GetPivot(),phase=index*.85}
end
local elapsed=0
local acc=0
RunService.Heartbeat:Connect(function(dt)
    elapsed+=dt;acc+=dt
    if acc<.08 then return end
    acc=0
    for _,entry in ipairs(displayModels) do
        if entry.model.Parent then
            local y=math.sin(elapsed*1.65+entry.phase)*.3
            entry.model:PivotTo(entry.pivot*CFrame.new(0,y,0)*
                CFrame.Angles(0,math.sin(elapsed*.63+entry.phase)*.10,0))
        end
    end
end)
print("EVOLUTION_GALLERY_STUDIO_PRIVATE_SOURCE_ONLY - no game XP/loot/ability grant")
