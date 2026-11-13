--!strict
-- P0D PRODUCT STUDIO original STAR JUMP option. Only active in a LOCAL unpublished Studio trial.
-- Adds two real ProximityPrompt physical-launch opportunities: chase OR escape.
-- Owns NO match, egg, score, HP, role, trap, creature inventory, reward or Remote.
local RunService = game:GetService("RunService")
if not RunService:IsStudio() then return end
local Players = game:GetService("Players")
local Policy = require(script.Parent:WaitForChild("H2StarLaunchPolicy"))
local arena = workspace:WaitForChild("TRAP_RAIDERS_S1",30)
if not arena then warn("H2_STAR_JUMP_NO_EXISTING_S1_ARENA"); return end
assert(arena:FindFirstChild("H2_STAR_JUMP_PADS") == nil, "H2_NO_DUPLICATE_STAR_PAD_SYSTEM")
local folder = Instance.new("Folder")
folder.Name = "H2_STAR_JUMP_PADS"
folder:SetAttribute("StudioOnly",true)
folder:SetAttribute("NoGameplayRoundAuthority",true)
folder:SetAttribute("RealStudio2ClientQA","NOT_TESTED")
folder.Parent = arena

local lastUse: {[Player]:number} = {}
local function platform(name:string,pos:Vector3,color:Color3): Part
    local pad = Instance.new("Part")
    pad.Name=name
    pad.Anchored=true; pad.CanCollide=true; pad.CanTouch=false; pad.CanQuery=true
    pad.Size=Vector3.new(10,1.2,10)
    pad.Position=pos
    pad.Color=color; pad.Material=Enum.Material.Neon
    pad.Parent=folder
    local marker = Instance.new("BillboardGui")
    marker.Name="KID_READABLE_JUMP_SIGN"
    marker.Size=UDim2.fromOffset(190,58)
    marker.StudsOffsetWorldSpace=Vector3.new(0,4,0)
    marker.MaxDistance=95
    marker.AlwaysOnTop=true
    marker.Parent=pad
    local label=Instance.new("TextLabel")
    label.Size=UDim2.fromScale(1,1)
    label.Text="⭐ 星のジャンプ台\nタップ / Eで とびだせ！"
    label.TextColor3=Color3.new(1,1,1)
    label.BackgroundColor3=Color3.fromRGB(28,31,76)
    label.BackgroundTransparency=0.12
    label.TextScaled=true
    label.Font=Enum.Font.GothamBold
    label.Parent=marker
    return pad
end

local function wire(side:string)
    local x=if side == "RED" then -Policy.PAD_X else Policy.PAD_X
    local pad=platform("H2_STAR_PAD_"..side,
        Vector3.new(x,Policy.PAD_Y,Policy.PAD_Z),
        if side == "RED" then Color3.fromRGB(255,173,129)
            else Color3.fromRGB(136,197,255))
    pad:SetAttribute("FreeForBothTeams",true)
    local prompt=Instance.new("ProximityPrompt")
    prompt.Name="STAR_JUMP_ONE_TAP"
    prompt.ActionText="とびだせ！"
    prompt.ObjectText="星のジャンプ台"
    prompt.MaxActivationDistance=Policy.MAX_DISTANCE
    prompt.RequiresLineOfSight=false
    prompt.HoldDuration=0
    prompt.KeyboardKeyCode=Enum.KeyCode.E
    prompt.Parent=pad
    prompt.Triggered:Connect(function(player: Player)
        -- Client prompt activation must be revalidated SERVER-side.
        if not player or player.Parent~=Players then return end
        local character=player.Character
        local root=character and character:FindFirstChild("HumanoidRootPart")
        local humanoid=character and character:FindFirstChildOfClass("Humanoid")
        if not (root and root:IsA("BasePart") and humanoid and humanoid:IsA("Humanoid")) then return end
        local team=player.Team and player.Team.Name or "NONE"
        local now=os.clock()
        local p=root.Position
        if not Policy.canLaunch({
            team=team,pad=side,healthy=humanoid.Health>0,
            grounded=humanoid.FloorMaterial~=Enum.Material.Air,
            seated=humanoid.Sit,now=now,lastAt=lastUse[player] or -math.huge,
            x=p.X,y=p.Y,z=p.Z,
        }) then return end
        local speed=Policy.velocityFor(side)
        if not speed then return end
        lastUse[player]=now
        -- Direction is a FIXED server-side pad property, not chosen by client.
        root.AssemblyLinearVelocity=Vector3.new(speed.x,speed.y,speed.z)
    end)
end
wire("RED")
wire("BLUE")
Players.PlayerRemoving:Connect(function(player) lastUse[player]=nil end)
print("P0D_H2_STAR_JUMP_STUDIO_OPTION_AVAILABLE; REAL_PHYSICS_PHONE_FUN_NOT_TESTED")
