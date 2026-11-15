--!nocheck
-- P0D FB020-B private Trapper pair teleport: real server world portal pads.
-- Existing Game owns class selection, authenticated skill seq, egg/score/HP.
-- This service NEVER creates a Remote, changes score, or accepts client position.
-- V5.5-inspired safety semantics; not a byte-copy of author's local V5.5.
local Service={}
local RunService=game:GetService("RunService")
local Players=game:GetService("Players")
local Debris=game:GetService("Debris")
local active={}
local disarmed=setmetatable({},{__mode="k"})
local lastTransit=setmetatable({},{__mode="k"})
local connection=nil
local counter=0
local LIFE=40
local MAX_USES=3
local EXIT_RADIUS=6
local REACH=4.4
local MIN_SPACING=16
local RIDE_COOLDOWN=2.5

local function enabled()
    return RunService:IsStudio()
        or (game.PrivateServerId~=""
            and workspace:GetAttribute("P0D_PRIVATE_TRAPPER_WARP")==true)
end

local function delPads(record)
    if not record then return end
    if record.first and record.first.Parent then record.first:Destroy() end
    if record.second and record.second.Parent then record.second:Destroy() end
end

local function teamName(player)
    local t=player.Team
    return if t and (t.Name=="RED" or t.Name=="BLUE") then t.Name else "NONE"
end

local function nearPortal(player,root,team,radius)
    for owner,rec in pairs(active) do
        if rec.team==team and rec.first and rec.second
            and rec.first.Parent and rec.second.Parent then
            for _,pad in ipairs({rec.first,rec.second}) do
                local a=root.Position
                local b=pad.Position
                local dx=a.X-b.X
                local dz=a.Z-b.Z
                if dx*dx+dz*dz<=radius*radius and math.abs(a.Y-b.Y)<9 then
                    return true
                end
            end
        end
    end
    return false
end

local function stopPollingIfEmpty()
    if next(active)==nil and connection then
        connection:Disconnect()
        connection=nil
    end
end

function Service.clearOwner(owner)
    local record=active[owner]
    if not record then return end
    active[owner]=nil
    delPads(record)
    for p,tag in pairs(disarmed) do
        if tag==record then disarmed[p]=nil end
    end
    stopPollingIfEmpty()
end

function Service.clearAll()
    for owner in pairs(active) do
        local r=active[owner]
        active[owner]=nil
        delPads(r)
    end
    for p in pairs(disarmed) do disarmed[p]=nil end
    for p in pairs(lastTransit) do lastTransit[p]=nil end
    if connection then connection:Disconnect();connection=nil end
end

local function makePad(owner,team,index,where,folder)
    counter+=1
    local model=Instance.new("Part")
    model.Name="P0D_TRAPPER_PORTAL_"..team.."_"..tostring(index).."_"..tostring(counter)
    model.Size=Vector3.new(7,.28,7)
    model.Shape=Enum.PartType.Cylinder
    model.CFrame=CFrame.new(where)
    model.Anchored=true
    model.CanCollide=false
    model.CanTouch=false
    model.CanQuery=false
    model.Material=Enum.Material.Neon
    model.Color=if team=="RED" then Color3.fromRGB(255,93,141)
        else Color3.fromRGB(85,207,255)
    model.Transparency=.22
    model:SetAttribute("P0D_PortalTeam",team)
    model:SetAttribute("P0D_PortalOwner",owner.UserId)
    model.Parent=folder
    return model
end

local function getRoot(player)
    local character=player.Character
    if not character then return nil end
    local humanoid=character:FindFirstChildOfClass("Humanoid")
    local root=character:FindFirstChild("HumanoidRootPart")
    if not humanoid or humanoid.Health<=0 or not root
        or not root:IsA("BasePart") then return nil end
    return root,character
end

local function eligiblePair(rec,now)
    return enabled() and now<rec.expires
        and rec.owner.Parent==Players
        and teamName(rec.owner)==rec.team
        and rec.first and rec.first.Parent
        and (not rec.second or rec.second.Parent~=nil)
end

local function tick(dt)
    if not enabled() then Service.clearAll();return end
    local now=os.clock()
    for owner,rec in pairs(active) do
        if not eligiblePair(rec,now) then
            Service.clearOwner(owner)
        end
    end
    if not connection then return end
    -- Tick at ~8 Hz regardless of server FPS and active player count.
    local acc=Service._acc or 0
    acc+=math.max(0,math.min(dt,.3))
    Service._acc=acc
    if acc<.12 then return end
    Service._acc=0
    for _,passenger in ipairs(Players:GetPlayers()) do
        local team=teamName(passenger)
        local root,character=getRoot(passenger)
        if root and team~="NONE" then
            local blocked=disarmed[passenger]
            if blocked then
                -- Do not re-arm until passenger PHYSICALLY leaves EVERY allied
                -- endpoint, including endpoints of overlapping portal pairs.
                if not nearPortal(passenger,root,team,EXIT_RADIUS) then
                    disarmed[passenger]=nil
                end
            else
                for owner,rec in pairs(active) do
                    if rec.team==team and rec.second and rec.second.Parent
                        and rec.remaining>0 and now<rec.expires
                        and type(rec.canRide)=="function"
                        and rec.canRide(passenger,team,rec.serial)==true
                        and now-(lastTransit[passenger] or -math.huge)>=RIDE_COOLDOWN then
                        local from=nil
                        local dest=nil
                        if (root.Position-rec.first.Position).Magnitude<=REACH+2 then
                            from=rec.first;dest=rec.second
                        elseif (root.Position-rec.second.Position).Magnitude<=REACH+2 then
                            from=rec.second;dest=rec.first
                        end
                        if from and dest then
                            local target=CFrame.new(dest.Position+Vector3.new(0,3.8,0))
                            local ok=pcall(function() character:PivotTo(target) end)
                            if ok then
                                -- Failed PivotTo is not charged; successful
                                -- teleport neutralizes leftover sprint momentum.
                                pcall(function()
                                    root.AssemblyLinearVelocity=Vector3.zero
                                    root.AssemblyAngularVelocity=Vector3.zero
                                end)
                                rec.remaining-=1
                                lastTransit[passenger]=now
                                disarmed[passenger]=rec
                                if rec.remaining<=0 then
                                    Service.clearOwner(owner)
                                end
                            end
                            break
                        end
                    end
                end
            end
        else
            disarmed[passenger]=nil
        end
    end
end

-- Called ONLY by existing Game's authenticated TRAPPER JOB_SKILL.
-- Place 1 creates entrance; next successful use at least 16 studs away makes
-- the pair. All coordinates are derived from authenticated server root/facing.
function Service.place(owner,team,origin,facing,folder,serial,canRide)
    if not enabled() or teamName(owner)~=team
        or (team~="RED" and team~="BLUE")
        or not folder or not folder.Parent or type(canRide)~="function"
        or typeof(origin)~="Vector3" or typeof(facing)~="Vector3" then return false end
    local root=getRoot(owner)
    if not root or (root.Position-origin).Magnitude>3 then return false end
    if owner:GetAttribute("P0D_LateJoinSpectator")==true then return false end
    local d=Vector3.new(facing.X,0,facing.Z)
    if d.Magnitude<.1 then return false end
    local pos=root.Position+d.Unit*7
    if math.abs(pos.X)>104 or math.abs(pos.Z)>60 then return false end
    for _,mark in ipairs({Vector3.new(-98,0,-20),Vector3.new(98,0,-20),
        Vector3.new(-82,0,20),Vector3.new(82,0,20),
        Vector3.new(-107,0,0),Vector3.new(107,0,0)}) do
        local off=Vector3.new(pos.X-mark.X,0,pos.Z-mark.Z)
        if off.Magnitude<15 then return false end
    end
    local where=Vector3.new(pos.X,.45,pos.Z)
    local now=os.clock()
    local record=active[owner]
    if record and record.second then
        Service.clearOwner(owner)
        record=nil
    end
    if record and (record.first.Position-where).Magnitude<MIN_SPACING then
        return false
    end
    if not record then
        record={owner=owner,team=team,first=nil,second=nil,
            expires=now+LIFE,remaining=MAX_USES,serial=serial,canRide=canRide}
        active[owner]=record
        record.first=makePad(owner,team,1,where,folder)
    else
        record.canRide=canRide
        record.second=makePad(owner,team,2,where,folder)
        record.expires=now+LIFE
        record.serial=serial
        -- A team may have only one live pair. Clear only same-team owners.
        for other,old in pairs(active) do
            if other~=owner and old.team==team then Service.clearOwner(other) end
        end
    end
    if not connection then
        Service._acc=0
        connection=RunService.Heartbeat:Connect(tick)
    end
    return true
end

workspace:GetAttributeChangedSignal("P0D_PRIVATE_TRAPPER_WARP"):Connect(function()
    if not enabled() then Service.clearAll() end
end)
Players.PlayerRemoving:Connect(function(player)
    Service.clearOwner(player)
    disarmed[player]=nil
    lastTransit[player]=nil
end)
return Service
