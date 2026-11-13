--!nocheck
-- H1 + V4 combined OWNER-private Studio trial. Original 47 scripts are byte-immutable.
-- This is a SECONDARY PREVIEW ONLY, not an egg/combat/Store/score authority.
-- Only the original V4 author Scheduler + SessionSixSkillXPPreview decide session XP.
local RunService = game:GetService("RunService")
if not RunService:IsStudio() then return end
local Players = game:GetService("Players")
local Scheduler = require(script.Parent:WaitForChild("FocusTrainingScheduler"))
local Model = require(script.Parent:WaitForChild("SessionSixSkillXPPreview"))
assert(#Scheduler.DISCIPLINES == 6 and #Model.SKILLS == 6, "SIX_SKILL_SOURCE_DRIFT")
local arena = workspace:WaitForChild("TRAP_RAIDERS_S1", 45)
if not arena then warn("[P0D_V4_BRIDGE] NO_ORIGINAL_ARENA"); return end
assert(not arena:FindFirstChild("PRIVATE_V4_SKILL_BRIDGE"), "DUPLICATE_V4_BRIDGE")
local folder = Instance.new("Folder")
folder.Name = "PRIVATE_V4_SKILL_BRIDGE"
folder:SetAttribute("StudioOnly",true)
folder:SetAttribute("SessionXPOnly",true)
folder:SetAttribute("NoSavedXP",true)
folder:SetAttribute("NoCombatBuff",true)
folder.Parent = arena

local positions = {
    BEAST={56,-15}, WEAPON={56,15},
    MAGIC={54,-49}, ZOMBIE={54,49},
    VEHICLE={74,-49}, BUILDING={74,49}
}
local labels = {MAGIC="魔法",ZOMBIE="ゾンビ",VEHICLE="乗り物",BUILDING="建築"}
local colors = {
    MAGIC=Color3.fromRGB(115,155,255),
    ZOMBIE=Color3.fromRGB(117,214,109),
    VEHICLE=Color3.fromRGB(245,185,90),
    BUILDING=Color3.fromRGB(185,148,250)
}
for _,side in ipairs({"RED","BLUE"}) do
    local sign = side=="RED" and -1 or 1
    for skill,display in pairs(labels) do
        local at = positions[skill]
        local pad = Instance.new("Part")
        pad.Name = "PRIVATE_V4_"..side.."_"..skill
        pad.Size = Vector3.new(10,0.22,10)
        pad.Position = Vector3.new(sign*at[1],-0.74,at[2])
        pad.Anchored=true; pad.CanCollide=false; pad.CanTouch=false; pad.CanQuery=false
        pad.Material=Enum.Material.Neon; pad.Color=colors[skill]
        pad.Transparency=0.18; pad:SetAttribute("PreviewOnly",true)
        pad.Parent=folder
        local gui = Instance.new("BillboardGui")
        gui.Name="V4_PREVIEW_SIGN"; gui.Size=UDim2.fromOffset(174,50)
        gui.StudsOffsetWorldSpace=Vector3.new(0,4,0)
        gui.MaxDistance=80; gui.AlwaysOnTop=true;gui.Parent=pad
        local text=Instance.new("TextLabel")
        text.Size=UDim2.fromScale(1,1);text.BackgroundColor3=Color3.fromRGB(24,29,47)
        text.BackgroundTransparency=.2;text.TextColor3=Color3.fromRGB(250,250,250)
        text.TextScaled=true;text.Font=Enum.Font.GothamBold
        text.Text=display.." 道場\n体験XP・保存なし"
        text.Parent=gui
    end
end
folder:SetAttribute("NewPadsCount",8)

local records={}
local function studioId(player)
    if player.UserId>0 then return player.UserId end
    return 800000000 + math.abs(math.floor(player.UserId))
end
local function init(player)
    local now=os.time()
    records[player]={
        scheduler=Scheduler.newState(studioId(player),now,nil),
        totals=Model.new(),friends={},checkedAt=0,
    }
    player:SetAttribute("P0D_V4_StudioNoSave",true)
end
for _,p in ipairs(Players:GetPlayers()) do init(p) end
Players.PlayerAdded:Connect(init)
Players.PlayerRemoving:Connect(function(p) records[p]=nil end)

local function verifiedFriends(player,record,now)
    if player.UserId<=0 or now-record.checkedAt<30 then return end
    record.checkedAt=now
    task.spawn(function()
        local result={}
        for _,other in ipairs(Players:GetPlayers()) do
            if other~=player and other.UserId>0 then
                local ok,friend=pcall(function() return player:IsFriendsWith(other.UserId) end)
                if ok and friend then result[other.UserId]=true end
            end
        end
        if records[player]==record then record.friends=result end
    end)
end
local function friendCount(record,player)
    local count=0
    for _,other in ipairs(Players:GetPlayers()) do
        if other~=player and other.UserId>0 and record.friends[other.UserId]==true then
            count+=1
        end
    end
    return math.min(4,count)
end
local function standingOn(player)
    local team=player.Team and player.Team.Name
    if team~="RED" and team~="BLUE" then return nil end
    local character=player.Character
    if not character then return nil end
    local root=character:FindFirstChild("HumanoidRootPart")
    local human=character:FindFirstChildOfClass("Humanoid")
    if not root or not human or human.Health<=0 then return nil end
    local sign=team=="RED" and -1 or 1
    for _,skill in ipairs(Scheduler.DISCIPLINES) do
        local at=positions[skill]
        local px,pz=sign*at[1],at[2]
        local dx,dz=root.Position.X-px,root.Position.Z-pz
        if dx*dx+dz*dz<=25 and math.abs(root.Position.Y-1)<10 then
            return skill
        end
    end
    return nil
end
local function publish(player,record,skill,friends)
    local status=Scheduler.getStatus(record.scheduler,false)
    player:SetAttribute("P0D_V4_Active",skill~=nil)
    player:SetAttribute("P0D_V4_Mode",status.mode)
    player:SetAttribute("P0D_V4_Current",status.skill)
    player:SetAttribute("P0D_V4_Selected",skill or "")
    player:SetAttribute("P0D_V4_Remaining",status.freeRemaining)
    player:SetAttribute("P0D_V4_Friends",friends)
    local levels=Model.snapshot(record.totals)
    for _,s in ipairs(Model.SKILLS) do
        local view=levels[s]
        player:SetAttribute("P0D_V4_"..s.."_LV",view.level)
        player:SetAttribute("P0D_V4_"..s.."_XP",view.xp)
        player:SetAttribute("P0D_V4_"..s.."_NEXT",view.xpToNext)
    end
end
task.spawn(function()
    while folder.Parent and RunService:IsStudio() do
        task.wait(1)
        local now=os.time()
        for _,player in ipairs(Players:GetPlayers()) do
            local record=records[player]
            if record then
                verifiedFriends(player,record,now)
                local skill=standingOn(player)
                local friends=friendCount(record,player)
                if skill and record.scheduler.selectedSkill~=skill then
                    record.scheduler=Scheduler.selectSkill(record.scheduler,skill)
                end
                local nextState,segments=Scheduler.settle(record.scheduler,now,skill~=nil,friends,false)
                local nextTotals,errorName=Model.apply(record.totals,segments)
                if nextTotals then
                    record.scheduler=nextState
                    record.totals=nextTotals
                else
                    warn("[P0D_V4_BRIDGE] SESSION_PREVIEW_BLOCKED",errorName)
                    -- Fail closed: never claim XP on invalid segments.
                    record.scheduler.lastTick=now
                end
                publish(player,record,skill,friends)
            end
        end
    end
end)
print("[P0D_V4_BRIDGE] SIX_SESSION_XP_PREVIEW_ONLY; no durable XP/paid/combat power")
