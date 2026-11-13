-- P0D H1 D18 canonical exploration landmarks, private Studio-only CLIENT VISUAL.
-- NO Game.server override; no win, inventory, coins, loot, trap, real jump, or network.
local RunService=game:GetService("RunService")
if not RunService:IsStudio() then return end

local Players=game:GetService("Players")
local Workspace=game:GetService("Workspace")
local player=Players.LocalPlayer
if not player then return end

local Catalog=require(script.Parent:WaitForChild("D18Batch10Catalog"))
local BEAST_ID="TRCA-BE-108" -- Original 七鈴の王獣, #271 fixed source
local PAD_ID="TRCA-TR-090" -- Original 時砂跳ね台, decorative ONLY
local beast=Catalog.get(BEAST_ID)
local pad=Catalog.get(PAD_ID)
assert(beast and beast.name=="七鈴の王獣")
assert(pad and pad.name=="時砂跳ね台")

-- Mirrored RED and BLUE teams; both can use the original main egg game freely.
-- Original #262 physical routes: SKY ends at (±62,0,+18), SEA at (±60,0,-22).
-- Landmarks are set to the side of the route, never with physical collision.
local SPOTS={
    {id=BEAST_ID,x=-58,z=30,kind="SKY",label="そらの道の近く"},
    {id=BEAST_ID,x=58,z=30,kind="SKY",label="そらの道の近く"},
    {id=PAD_ID,x=-58,z=-35,kind="SEA",label="うみの道の近く"},
    {id=PAD_ID,x=58,z=-35,kind="SEA",label="うみの道の近く"},
}
local MODEL_IN_DIST=76
local MODEL_OUT_DIST=86
local MAX_NEARBY_MODELS=2 -- client cap; server S1 world still unchanged
local models={}
local discovered={} -- Session-only; never persistent or authoritative.
local discoveredCount=0
local root=Instance.new("Folder")
root.Name="P0D_H1_D18_LOCAL_DECORATIONS_STUDIO_ONLY"
root.Parent=Workspace
local gui=Instance.new("ScreenGui")
gui.Name="P0D_H1_D18_SESSION_DISCOVERY_ONLY"
gui.ResetOnSpawn=false
gui.IgnoreGuiInset=false
gui.DisplayOrder=8
gui.Parent=player:WaitForChild("PlayerGui")
local banner=Instance.new("TextLabel")
banner.Name="DiscoveryNotice"
banner.AnchorPoint=Vector2.new(1,0)
banner.Position=UDim2.new(1,-12,0,92)
banner.Size=UDim2.fromOffset(236,66)
banner.BackgroundColor3=Color3.fromRGB(35,45,80)
banner.BackgroundTransparency=.18
banner.TextColor3=Color3.fromRGB(252,242,208)
banner.TextWrapped=true
banner.TextScaled=true
banner.Font=Enum.Font.GothamBold
banner.Visible=false
banner.Parent=gui
local corner=Instance.new("UICorner")
corner.CornerRadius=UDim.new(0,10)
corner.Parent=banner
local bannerUntil=0
local function flash(message)
    banner.Text=message
    banner.Visible=true
    bannerUntil=os.clock()+2.8
end
local function validSpec(part)
    if type(part)~="table" or type(part.position)~="table" or type(part.size)~="table" then return false end
    if type(part.shape)~="string" or not Enum.PartType[part.shape] then return false end
    for _,v in ipairs(part.position) do
        if type(v)~="number" or v~=v or math.abs(v)>8 then return false end
    end
    for _,v in ipairs(part.size) do
        if type(v)~="number" or v~=v or v<0.06 or v>6 then return false end
    end
    return #part.position==3 and #part.size==3 and #part.rotation==3
end
local function build(index,spot)
    local definition=Catalog.get(spot.id)
    if not definition then return nil end
    local m=Instance.new("Model")
    m.Name="D18_LANDMARK_"..spot.kind.."_"..tostring(index)
    m:SetAttribute("P0DPreviewOnly",true)
    m:SetAttribute("P0DNonAuthoritative",true)
    local origin=CFrame.new(spot.x,1.5,spot.z)
    for _,spec in ipairs(definition.parts) do
        if validSpec(spec) then
            local p=Instance.new("Part")
            p.Name=spec.name
            p.Anchored=true
            p.CanCollide=false
            p.CanTouch=false
            p.CanQuery=false
            p.CastShadow=false
            p.Shape=Enum.PartType[spec.shape]
            p.Size=Vector3.new(spec.size[1],spec.size[2],spec.size[3])
            local col=definition.palette[spec.color]
            if col then p.Color=Color3.fromRGB(col[1],col[2],col[3]) end
            p.Material=Enum.Material.SmoothPlastic
            local rot=spec.rotation
            p.CFrame=origin*CFrame.new(spec.position[1],spec.position[2],spec.position[3])
                *CFrame.Angles(math.rad(rot[1]),math.rad(rot[2]),math.rad(rot[3]))
            p.Parent=m
        end
    end
    -- Invisible interaction anchor is noncolliding, query off and anchored.
    local anchor=Instance.new("Part")
    anchor.Name="OnlyLocalExplorePromptAnchor"
    anchor.Size=Vector3.new(2,2,2)
    anchor.CFrame=origin*CFrame.new(0,1,0)
    anchor.Transparency=1
    anchor.Anchored=true
    anchor.CanCollide=false
    anchor.CanQuery=false
    anchor.CanTouch=false
    anchor.Parent=m
    local prompt=Instance.new("ProximityPrompt")
    prompt.ActionText="みつける"
    prompt.ObjectText=definition.name.."（道しるべ）"
    prompt.KeyboardKeyCode=Enum.KeyCode.E
    prompt.HoldDuration=0
    prompt.MaxActivationDistance=16
    prompt.RequiresLineOfSight=false
    prompt.Parent=anchor
    prompt.Triggered:Connect(function(who)
        -- Client-only UI; there is no trusted collection, reward or gameplay action.
        if who ~= nil and who ~= player then return end
        if not discovered[spot.id] then
            discovered[spot.id]=true
            discoveredCount+=1
        end
        local where=if spot.kind=="SKY" then "そらの道は、近道のひとつ！" else "うみの道も、敵が通れるよ！"
        flash("✨ "..definition.name.." 発見 "..tostring(discoveredCount).."/2\n"..where)
    end)
    m.Parent=root
    return m
end

local function distance2(character,spot)
    local rootPart=character and character:FindFirstChild("HumanoidRootPart")
    if not rootPart or not rootPart:IsA("BasePart") then return math.huge end
    local p=rootPart.Position
    local dx=p.X-spot.x
    local dz=p.Z-spot.z
    return dx*dx+dz*dz
end

local elapsed=0
local connection
connection=RunService.Heartbeat:Connect(function(dt)
    if not gui.Parent or not root.Parent then
        if connection then connection:Disconnect() end
        return
    end
    if banner.Visible and os.clock()>=bannerUntil then banner.Visible=false end
    elapsed+=dt
    if elapsed<.65 then return end
    elapsed=0
    local character=player.Character
    local sorted={}
    for i,spot in ipairs(SPOTS) do
        table.insert(sorted,{index=i,spot=spot,d2=distance2(character,spot)})
    end
    table.sort(sorted,function(a,b) return a.d2<b.d2 end)
    local allowed={}
    local active=0
    for _,entry in ipairs(sorted) do
        if entry.d2<MODEL_IN_DIST*MODEL_IN_DIST and active<MAX_NEARBY_MODELS then
            allowed[entry.index]=true
            active+=1
        end
    end
    for i,model in pairs(models) do
        if not allowed[i] or sorted==nil then
            model:Destroy()
            models[i]=nil
        end
    end
    for i,spot in ipairs(SPOTS) do
        if allowed[i] and models[i]==nil then
            models[i]=build(i,spot)
        end
    end
end)
gui.Destroying:Connect(function()
    if connection then connection:Disconnect() end
    root:Destroy()
end)
print("P0D_H1_D18_CHARACTER_LANDMARKS_LOCAL_PREVIEW_ONLY_NOT_GAMEPLAY_QA")
