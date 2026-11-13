--!nocheck
-- H1 D18 display-only companion: original Batch8 dragon helps a child find REAL map egg / score pad.
-- Runs ONLY in owner's private Roblox Studio. Does not send Remotes or alter gameplay.
local RunService=game:GetService("RunService")
if not RunService:IsStudio() then return end
local Players=game:GetService("Players")
local ReplicatedStorage=game:GetService("ReplicatedStorage")
local player=Players.LocalPlayer
if not player then return end

local Catalog=require(script.Parent:WaitForChild("D18Batch8Catalog",10))
local Rules=require(script.Parent:WaitForChild("D18MascotGuideRules",10))
local Compass=require(script.Parent:WaitForChild("D18ObjectiveCompassRules",10))
if not Catalog or not Rules or not Compass then return end
local ARENA=workspace:WaitForChild("TRAP_RAIDERS_S1",30)
local remote=ReplicatedStorage:WaitForChild("TrapRaidersS1Remote",30)
if not ARENA or not remote then
    warn("D18 local guide: existing authoritative S1 map/Remote missing")
    return
end
if workspace:FindFirstChild("H1_D18_LOCAL_MASCOT") then
    warn("D18 local guide: local visual already exists")
    return
end

local root=Instance.new("Folder")
root.Name="H1_D18_LOCAL_MASCOT"
root:SetAttribute("PreviewOnly",true)
root:SetAttribute("NoGameplayAuthority",true)
root.Parent=workspace
local state=nil
local current=nil
local previousSerial=-1
local previousUpdate=-1
local accumulator=0
local age=0
-- The compass only appears after the user asks the mascot. No passive compass or extra actions.
local playerGui=player:WaitForChild("PlayerGui",20)
if not playerGui then return end
local guideGui=Instance.new("ScreenGui")
guideGui.Name="H1D18ObjectiveCompass"
guideGui.ResetOnSpawn=false
guideGui.IgnoreGuiInset=false
guideGui.DisplayOrder=15
guideGui.Parent=playerGui
local panel=Instance.new("Frame")
panel.Name="CompassPanel"
panel.Position=UDim2.new(.02,0,.30,0)
panel.Size=UDim2.fromOffset(184,65)
panel.BackgroundColor3=Color3.fromRGB(33,43,68)
panel.BackgroundTransparency=.13
panel.BorderSizePixel=0
panel.Visible=false
panel.Active=false
panel.Parent=guideGui
local corner=Instance.new("UICorner")
corner.CornerRadius=UDim.new(0,11)
corner.Parent=panel
local arrow=Instance.new("TextLabel")
arrow.Name="BearingArrow"
arrow.Size=UDim2.fromOffset(55,55)
arrow.Position=UDim2.fromOffset(3,5)
arrow.BackgroundTransparency=1
arrow.Text="↑"
arrow.TextSize=42
arrow.Font=Enum.Font.GothamBold
arrow.TextColor3=Color3.fromRGB(255,227,116)
arrow.Parent=panel
local instruction=Instance.new("TextLabel")
instruction.Name="ObjectiveName"
instruction.Position=UDim2.fromOffset(58,6)
instruction.Size=UDim2.fromOffset(120,53)
instruction.BackgroundTransparency=1
instruction.Font=Enum.Font.GothamBold
instruction.TextSize=14
instruction.TextColor3=Color3.fromRGB(255,255,255)
instruction.TextWrapped=true
instruction.Text="方向だけの目印"
instruction.Parent=panel
local function hideCompass()
    panel.Visible=false
end
local function dropMascot()
    hideCompass()
    if state then
        state.model:Destroy()
        state=nil
    end
end
local function destinationPart(view)
    local castle=ARENA:FindFirstChild(view.destinationTeam.."_CASTLE")
    if not castle then return nil end
    local part=castle:FindFirstChild(view.partName)
    if not part or not part:IsA("BasePart") then return nil end
    return part
end
local function updateCompass()
    if not state or not current or state.hintUntil<0 then hideCompass(); return false end
    local goal=destinationPart(current)
    local character=player.Character
    local avatar=character and character:FindFirstChild("HumanoidRootPart")
    local camera=workspace.CurrentCamera
    if not goal or not avatar or not avatar:IsA("BasePart") or not camera then
        hideCompass()
        return false
    end
    local delta=goal.Position-avatar.Position
    local look=camera.CFrame.LookVector
    local right=camera.CFrame.RightVector
    local angle=Compass.angleDegrees(right.X,right.Z,look.X,look.Z,delta.X,delta.Z)
    if angle==nil then hideCompass(); return false end
    arrow.Rotation=angle
    instruction.Text=Compass.title(current.carrying) or "方向だけの目印"
    panel.Visible=true
    return true
end

local function speak()
    if not state or not current then return end
    if current.phase~="ACTIVE" and current.phase~="COUNTDOWN" then return end
    local now=os.clock()
    if now-state.lastSpeak<2 then return end
    state.lastSpeak=now
    state.tapUntil=now+1.35
    state.hintUntil=now+6
    state.lastHintName=current.partName
    updateCompass()
    state.label.Text=if current.carrying then "🥚 やじるしで自分の台へ！" else "🐲 やじるしで敵の卵へ！"
    state.label.TextColor3=Color3.fromRGB(255,238,141)
end

local function spawnMascot(team)
    local castle=ARENA:FindFirstChild(team.."_CASTLE")
    local spawn=castle and castle:FindFirstChild(team.."_SPAWN")
    if not spawn or not spawn:IsA("BasePart") then return false end
    local modelData=Catalog.get("TRCA-BE-063")
    if not modelData or #modelData.parts>24 then return false end
    local startPos=spawn.Position+Vector3.new(0,2,-10)
    local lookPos=Vector3.new(0,startPos.Y,startPos.Z)
    local origin=CFrame.lookAt(startPos,lookPos)
    local model=Instance.new("Model")
    model.Name="D18_Original_Lava_Dragon_ClientOnly"
    model:SetAttribute("OriginalD18ID","TRCA-BE-063")
    model:SetAttribute("PreviewOnly",true)
    local parts={}
    for _,spec in ipairs(modelData.parts) do
        local p=Instance.new("Part")
        p.Name=spec.name
        p.Shape=Enum.PartType[spec.shape]
        p.Size=Vector3.new(spec.size[1],spec.size[2],spec.size[3])
        local rgb=modelData.palette[spec.color]
        p.Color=Color3.fromRGB(rgb[1],rgb[2],rgb[3])
        p.Material=Enum.Material.SmoothPlastic
        p.Anchored=true
        p.CanCollide=false
        p.CanTouch=false
        p.CanQuery=false
        p.CastShadow=false
        p.Parent=model
        table.insert(parts,{part=p,spec=spec})
    end
    local anchor=Instance.new("Part")
    anchor.Name="MascotPromptAnchor"
    anchor.Size=Vector3.new(1,1,1)
    anchor.Transparency=1
    anchor.Anchored=true
    anchor.CanCollide=false
    anchor.CanTouch=false
    anchor.CanQuery=false
    anchor.CFrame=origin*CFrame.new(0,1.1,0)
    anchor.Parent=model
    local prompt=Instance.new("ProximityPrompt")
    prompt.Name="D18EggHintPrompt"
    prompt.ActionText="たまごの道をきく"
    prompt.ObjectText="熔炉の角竜"
    prompt.KeyboardKeyCode=Enum.KeyCode.E
    prompt.MaxActivationDistance=14
    prompt.HoldDuration=0
    prompt.RequiresLineOfSight=false
    prompt.Parent=anchor
    local gui=Instance.new("BillboardGui")
    gui.Name="D18MascotBubble"
    gui.Size=UDim2.fromOffset(235,64)
    gui.StudsOffsetWorldSpace=Vector3.new(0,2.6,0)
    gui.MaxDistance=55
    gui.AlwaysOnTop=true
    gui.Parent=anchor
    local label=Instance.new("TextLabel")
    label.Name="EggGuideText"
    label.Size=UDim2.fromScale(1,1)
    label.BackgroundColor3=Color3.fromRGB(38,44,74)
    label.BackgroundTransparency=.12
    label.TextColor3=Color3.fromRGB(251,247,225)
    label.TextScaled=true
    label.TextWrapped=true
    label.Font=Enum.Font.GothamBold
    label.Text="🐲 たまごの道を教えるよ！"
    label.Parent=gui
    local corner=Instance.new("UICorner")
    corner.CornerRadius=UDim.new(0,12)
    corner.Parent=label
    state={
        team=team,model=model,definition=modelData,parts=parts,
        origin=origin,anchor=anchor,prompt=prompt,label=label,
        lastSpeak=-100,tapUntil=-1,hintUntil=-1,lastHintName=nil
    }
    model.Parent=root
    prompt.Triggered:Connect(function() speak() end)
    print("D18_MASCOT_LOCAL_GUIDE_STUDIO_ONLY; no server authority")
    return true
end

local function render(now)
    if not state then return end
    local bob=math.sin(age*2.2)*.11
    local tap=(now<state.tapUntil)
    local pose=if tap then state.definition.pose_offsets.tap else state.definition.pose_offsets.idle
    local turn=CFrame.Angles(0,math.sin(age*.95)*.10,0)
    for _,slot in ipairs(state.parts) do
        local s=slot.spec
        local o=pose[s.group] or {}
        local wave=if s.group=="tail" then math.sin(age*3.2)*9 else 0
        slot.part.CFrame=state.origin*turn
            *CFrame.new(s.position[1],s.position[2]+bob,s.position[3])
            *CFrame.Angles(math.rad(s.rotation[1]),math.rad(s.rotation[2]),math.rad(s.rotation[3]+wave))
            *CFrame.new(0,o.dy or 0,0)
            *CFrame.Angles(0,0,math.rad(o.rz or 0))
    end
    state.anchor.CFrame=state.origin*CFrame.new(0,1.1+bob,0)
    if state.hintUntil>0 and now>=state.hintUntil then
        state.hintUntil=-1
        hideCompass()
        state.label.Text="🐲 たまごの道を教えるよ！"
        state.label.TextColor3=Color3.fromRGB(251,247,225)
    elseif state.hintUntil>0 then
        -- Follow the child's actual avatar and camera while the short hint is active.
        updateCompass()
    end
end

local remoteConn=remote.OnClientEvent:Connect(function(message)
    local nextView=Rules.accept(message,previousSerial,previousUpdate)
    if not nextView then return end
    previousSerial=nextView.serial
    if nextView.updateId~=nil then previousUpdate=nextView.updateId end
    current=nextView
    if current.phase~="ACTIVE" and current.phase~="COUNTDOWN" then
        dropMascot()
        return
    end
    if not state or state.team~=current.team then
        dropMascot()
        spawnMascot(current.team)
    elseif state.hintUntil>0 and state.lastHintName~=current.partName then
        -- Retarget only on a real change to the server-authoritative objective.
        state.lastHintName=current.partName
        updateCompass()
    end
end)
local beat=RunService.Heartbeat:Connect(function(dt)
    if not root.Parent then return end
    if type(dt)~="number" or dt<=0 or dt>.5 then return end
    age+=dt
    accumulator+=dt
    if accumulator<.09 then return end
    accumulator=0
    render(os.clock())
end)
script.Destroying:Connect(function()
    beat:Disconnect()
    remoteConn:Disconnect()
    dropMascot()
    guideGui:Destroy()
    root:Destroy()
end)
