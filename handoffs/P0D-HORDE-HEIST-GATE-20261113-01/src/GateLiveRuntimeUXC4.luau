--!strict
-- Isolated unpublished B42+V7 preview adapter; never a second Game/Remote.
-- Requires existing original authoritative Game round, Horde, and H1 sea.
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local GateRules = require(script.Parent:WaitForChild("GateRules"))
local EliteKOBridge = require(script.Parent:WaitForChild("EliteKOBridge"))
local GateVisual = require(script.Parent:WaitForChild("GateVisual"))
local GateRouteOverlay = require(script.Parent:WaitForChild("GateRouteOverlay"))
local GateLiveRuntime = {}
GateLiveRuntime.__index = GateLiveRuntime

function GateLiveRuntime.new(arena: Instance)
    return setmetatable({arena=arena,round=nil,rules=nil,route=nil,
        objective=nil,lastPhase=nil,missingSceneNoted=false},GateLiveRuntime)
end

function GateLiveRuntime:startRound(epoch: number, now: number)
    -- The old barriers disappear before the new round respawn settles.
    if self.route then
        GateRouteOverlay.render(self.route,GateVisual,{phase="OPEN",passable=true})
        self.route.model:Destroy()
    end
    self.route=nil
    self.objective=nil
    self.lastPhase=nil
    self.missingSceneNoted=false
    if RunService:IsStudio() then
        print("[P0D_GATE_QA] NEW_ROUND epoch="..tostring(epoch))
    end
    self.round=epoch
    self.rules=GateRules.new(tostring(epoch))
end

function GateLiveRuntime:beforeHit(horde)
    if not RunService:IsStudio() or self.rules==nil or self.round~=horde.round then
        return nil
    end
    return EliteKOBridge.capture(horde)
end

function GateLiveRuntime:afterHit(horde,receipt,now: number)
    if receipt==nil or self.rules==nil or self.round~=horde.round then return false end
    if EliteKOBridge.didConfirmEliteKO(horde,receipt) then
        local accepted=self.rules:onEliteKO(tostring(self.round),true,now)
        if accepted then
            print("[P0D_GATE_QA] ELITE_KO_CONFIRMED epoch="..tostring(self.round))
        end
        return accepted
    end
    return false
end

local function livingCharacters()
    local result = {}
    for _,player in ipairs(Players:GetPlayers()) do
        local char=player.Character
        local hum=char and char:FindFirstChildOfClass("Humanoid")
        if hum and hum.Health>0 and char then table.insert(result,char) end
    end
    return result
end

local function countsWithinBox(cf: CFrame,size: Vector3,characters)
    if #characters==0 then return 0 end
    local overlap=OverlapParams.new()
    overlap.FilterType=Enum.RaycastFilterType.Include
    overlap.FilterDescendantsInstances=characters
    overlap.MaxParts=0 -- no truncation of character parts
    local hits=workspace:GetPartBoundsInBox(cf,size,overlap)
    local found={}
    for _,part in ipairs(hits) do
        for _,char in ipairs(characters) do
            if part:IsDescendantOf(char) then found[char]=true end
        end
    end
    local count=0
    for _ in pairs(found) do count+=1 end
    return count
end

local function doorOccupancy(route)
    local chars=livingCharacters()
    if #chars==0 then return 0 end
    local visited={}
    for _,model in ipairs(route.doors) do
        local part=model.PrimaryPart
        if not part then return 128 end -- fail open if geometry corrupted
        local overlap=OverlapParams.new()
        overlap.FilterType=Enum.RaycastFilterType.Include
        overlap.FilterDescendantsInstances=chars
        overlap.MaxParts=0
        for _,p in ipairs(workspace:GetPartBoundsInBox(part.CFrame,
                -- Existing Game ticks every 0.5s: include at least 10 studs of
                -- arrival margin along DOOR normal (local Z => WORLD X).
                -- The real doorway is 1.2 deep; +20 gives 10.6 each side.
                part.Size+Vector3.new(4,4,20),overlap)) do
            for _,char in ipairs(chars) do
                if p:IsDescendantOf(char) then visited[char]=true end
            end
        end
    end
    local count=0
    for _ in pairs(visited) do count+=1 end
    return math.min(count,128)
end

local function createObjectiveBillboard(parent: Instance): TextLabel
    -- Pure replicated WORLD signage; no HUD script and no second Remote.
    -- It is mounted ONLY after the actual source-validated SEA route exists.
    local marker=Instance.new("Part")
    marker.Name="S2_ELITE_GATE_OBJECTIVE_SIGN"
    marker.Size=Vector3.new(1,1,1)
    marker.Position=Vector3.new(0,16,-13)
    marker.Anchored=true
    marker.Transparency=1
    marker.CanCollide=false
    marker.CanQuery=false
    marker.CanTouch=false
    marker.Parent=parent
    local gui=Instance.new("BillboardGui")
    gui.Name="Objective"
    gui.AlwaysOnTop=false
    gui.MaxDistance=145
    gui.Size=UDim2.fromOffset(300,78)
    gui.Parent=marker
    local label=Instance.new("TextLabel")
    label.Name="Message"
    label.Size=UDim2.fromScale(1,1)
    label.Font=Enum.Font.GothamBold
    label.TextScaled=true
    label.TextWrapped=true
    label.TextColor3=Color3.fromRGB(255,250,235)
    label.BackgroundColor3=Color3.fromRGB(32,47,82)
    label.BackgroundTransparency=.18
    label.Text="精鋭を倒そう！海の近道が開く"
    label.Parent=gui
    return label
end

local function updateObjective(label: TextLabel?,phase: string)
    if not label then return end
    if phase=="WARNING" then
        label.Text="精鋭撃破！あと少しで海の近道OPEN"
    elseif phase=="OPEN" then
        label.Text="海の近道OPEN！赤青どちらも通れる"
    elseif phase=="WAIT_CLEAR" then
        label.Text="通行中！門は安全のため開いている"
    elseif phase=="CLOSED" then
        label.Text="海の門は閉じた！草原から迂回しよう"
    elseif phase=="ROUND_END" then
        label.Text="ラウンド終了！次の試合へ"
    else
        label.Text="精鋭を倒そう！海の近道が開く"
    end
end

-- Before constructing opaque stone arms, do not place walls through any living avatar.
local function safeToMount()
    local chars=livingCharacters()
    if #chars==0 then return true end
    for _,side in ipairs({-1,1}) do
        local x=side*36
        if countsWithinBox(CFrame.new(x,6,-16),
                Vector3.new(7,16,72),chars)>0 then return false end
    end
    return true
end

function GateLiveRuntime:tick(now: number,epoch: number,phase: string)
    if not RunService:IsStudio() or self.rules==nil or self.round~=epoch then return end
    if phase~="ACTIVE" then
        if self.route then
            -- Never end a match by sealing a moving player's route.
            GateRouteOverlay.render(self.route,GateVisual,{phase="OPEN",passable=true})
            updateObjective(self.objective,"ROUND_END")
            if self.lastPhase~="ROUND_END" then
                self.lastPhase="ROUND_END"
                print("[P0D_GATE_QA] ROUND_END_SAFE_OPEN epoch="..tostring(epoch))
            end
        end
        return
    end
    if self.route==nil and safeToMount() then
        local route,err=GateRouteOverlay.create(self.arena,GateVisual)
        if route then
            self.route=route
            self.objective=createObjectiveBillboard(route.model)
            self.lastPhase=nil
            print("[P0D_GATE_QA] SEA_GATES_MOUNTED epoch="..tostring(epoch).." count=2")
        elseif not self.missingSceneNoted then
            self.missingSceneNoted=true
            print("[P0D_GATE_QA] SEA_SOURCE_NOT_READY "..tostring(err))
        end
        -- A missing/changed H1 route never creates a cosmetic gate.
    end
    if self.route then
        local count=doorOccupancy(self.route)
        if self.rules:step(tostring(epoch),now,count) then
            local snapshot=self.rules:snapshot()
            GateRouteOverlay.render(self.route,GateVisual,snapshot)
            updateObjective(self.objective,snapshot.phase)
            if self.lastPhase~=snapshot.phase then
                self.lastPhase=snapshot.phase
                local door1=self.route.doors[1].PrimaryPart
                local door2=self.route.doors[2].PrimaryPart
                print("[P0D_GATE_QA] epoch="..tostring(epoch)
                    .." phase="..snapshot.phase
                    .." occupants="..tostring(count)
                    .." door1_collide="..tostring(door1 and door1.CanCollide)
                    .." door2_collide="..tostring(door2 and door2.CanCollide))
            end
        else
            -- Reject malformed sensor input by leaving the existing state.
        end
    else
        self.rules:step(tostring(epoch),now,0)
    end
end

return GateLiveRuntime
