--!strict
-- Real ROBLOX Studio ONLY evidence observer. No simulated Studio PASS:
-- All lines below are unreachable until OWNER manually enables in an isolated copy.
-- This never teleports players, changes combat, gravity, ownership or rewards.
local ENABLE_G5_STUDIO_EVIDENCE = false
if not ENABLE_G5_STUDIO_EVIDENCE then return end

local RunService = game:GetService("RunService")
assert(RunService:IsStudio(), "G5_PROBE_CANNOT_RUN_IN_LIVE_ROBLOX")
assert(workspace:FindFirstChild("TRAP_RAIDERS_S1")==nil,"G5_PROBE_CANNOT_OVERLAP_OFFICIAL_S1")
local Players=game:GetService("Players")
local Scene=require(script.Parent.WorldLinkScene)
local Plan=require(script.Parent.G5StudioCheckpointPlan)
local okPlan, reason=Plan.validate()
assert(okPlan,reason)
local scene=Scene.build(workspace)
local folder=scene.folder
local stamp=0
local stageByPlayer={}
local lastByPlayer={}
local completedByPlayer={}
local routeStartedAtByPlayer={}
local characterConns={}
local connectionList={}
local readyEmitted=false

local function emit(kind: string, extra: string)
    stamp+=1
    print(string.format("G5_REAL_STUDIO_LOCAL_EVIDENCE seq=%d event=%s %s",stamp,kind,extra))
end

emit("BOOT","studio=true live=false test_place_only=true status=COLLECTING")
emit("LIMITS","mobile=NOT_TESTED child_review=NOT_TESTED live_published=false egg_and_combat=NOT_TESTED")
emit("SOURCE","WorldLinkScene=ORIGINAL_EXACT_G5_CODE QA_probe=READONLY_DISABLED_BY_DEFAULT")

-- Authentic physics query against actual Roblox Workspace (never a fake Native test).
-- Engine contact/ground results are REQUIRED before accepting any physical-walk gate.
local physical={}
local raySpecs={
    "SEA_BRIDGE_FreePortWalk","SEA_BUBBLE_A_DryRamp","SEA_BUBBLE_B_DryRamp",
    "SKY_RAINBOW_A_Lower","SKY_RAINBOW_A_Upper",
    "SKY_RAINBOW_B_Lower","SKY_RAINBOW_B_Upper"
}
local params=RaycastParams.new()
params.FilterType=Enum.RaycastFilterType.Include
params.FilterDescendantsInstances={folder}
params.IgnoreWater=true
local physicalCount=0
for _,name in ipairs(raySpecs) do
    local path=folder:FindFirstChild(name)
    if path and path:IsA("BasePart") then
        local hit=workspace:Raycast(path.Position+Vector3.new(0,10,0),Vector3.new(0,-25,0),params)
        local pass=hit~=nil and hit.Instance==path and hit.Normal.Y>=0.90
            and path.CanCollide and path.Anchored
        physical[name]=pass
        if pass then physicalCount+=1 end
        emit("RAYCAST",string.format("route=%s result=%s normal_y=%s",name,
            pass and "PASS" or "FAIL",hit and string.format("%.3f",hit.Normal.Y) or "NONE"))
    else
        physical[name]=false
        emit("RAYCAST","route="..name.." result=FAIL reason=MISSING_PART")
    end
end
local allPhysical=physicalCount==#raySpecs
emit("PHYSICS_SUMMARY",string.format("real_workspace_raycast=%d/%d result=%s",
    physicalCount,#raySpecs,allPhysical and "PASS" or "FAIL"))

local function fresh(player)
    stageByPlayer[player]={}
    completedByPlayer[player]={}
    lastByPlayer[player]=nil
    routeStartedAtByPlayer[player]={}
    for _,id in ipairs(Plan.ROUTE_ORDER) do
        stageByPlayer[player][id]=1
    end
end

local function validRoot(player)
    local ch=player.Character
    if not ch or not ch.Parent then return nil end
    local human=ch:FindFirstChildOfClass("Humanoid")
    local root=ch:FindFirstChild("HumanoidRootPart")
    if not human or human.Health<=0 or not root or not root:IsA("BasePart")
        or root.Anchored then return nil end
    return root
end

local function activeClientCount()
    local num=0
    for _,p in ipairs(Players:GetPlayers()) do
        if validRoot(p) then num+=1 end
    end
    return num
end

local function attemptFullEvidence()
    if readyEmitted or not allPhysical or activeClientCount()<2 then return end
    local uniqueWalkers=0
    local aggregated={}
    for _,p in ipairs(Players:GetPlayers()) do
        if validRoot(p) and completedByPlayer[p] then
            local hasCompleted=false
            for id,done in pairs(completedByPlayer[p]) do
                if done==true then
                    aggregated[id]=true
                    hasCompleted=true
                end
            end
            if hasCompleted then uniqueWalkers+=1 end
        end
    end
    if uniqueWalkers<2 then return end
    for _,id in ipairs(Plan.ROUTE_ORDER) do
        if not aggregated[id] then return end
    end
    readyEmitted=true
    emit("GATE","real_studio_two_active_clients=true actual_rays=7/7 actual_routes_out_and_return=5/5 two_distinct_walkers=true result=PASS")
    emit("STILL_PENDING","actual_phone_touch=NOT_TESTED measured_fps=NOT_TESTED real_egg_carry=NOT_TESTED owner_release=NOT_AUTHORIZED")
end

local function tickPlayer(player, now)
    if not stageByPlayer[player] then fresh(player) end
    local root=validRoot(player)
    if not root then
        lastByPlayer[player]=nil
        return
    end
    local pos=root.Position
    local old=lastByPlayer[player]
    if old then
        local elapsed=now-old.time
        if elapsed>0.001 and (pos-old.pos).Magnitude / elapsed > Plan.MAX_SPEED_STUDS_PER_SEC then
            fresh(player)
            emit("SUSPECT_MOVEMENT",string.format("player_local=%s action=RESET_ROUTE_CHECKPOINTS",
                tostring(player.UserId)))
            lastByPlayer[player]={pos=pos,time=now}
            return
        end
    end
    lastByPlayer[player]={pos=pos,time=now}
    for _,id in ipairs(Plan.ROUTE_ORDER) do
        if completedByPlayer[player][id]~=true then
            local stage=stageByPlayer[player][id]
            local started=routeStartedAtByPlayer[player][id]
            if started and now-started > Plan.LIMIT_PER_ROUTE_SECONDS then
                stage=1
                stageByPlayer[player][id]=1
                routeStartedAtByPlayer[player][id]=nil
                emit("ROUTE_TIMEOUT",string.format("player_local=%s route=%s checkpoint_reset=true",
                    tostring(player.UserId),id))
            end
            local nextStage,complete=Plan.advance(id,stage,pos.X,pos.Y,pos.Z)
            if nextStage~=stage then
                if stage==1 then routeStartedAtByPlayer[player][id]=now end
                stageByPlayer[player][id]=nextStage
                local list=Plan.ROUTES[id]
                local label=list[stage] and list[stage].label or "END"
                emit("CHECKPOINT",string.format("player_local=%s route=%s stage=%d/%d cue=%s",
                    tostring(player.UserId),id,stage,#list,label))
            end
            if complete then
                completedByPlayer[player][id]=true
                emit("ROUTE_COMPLETE",string.format("player_local=%s route=%s outbound_and_return=PASS",
                    tostring(player.UserId),id))
            end
        end
    end
end

local function bindPlayer(player)
    fresh(player)
    characterConns[player]=player.CharacterRemoving:Connect(function()
        fresh(player)
        emit("CHARACTER","respawn_or_death=true route_checkpoints_reset=true")
    end)
end
for _,player in ipairs(Players:GetPlayers()) do bindPlayer(player) end
table.insert(connectionList,Players.PlayerAdded:Connect(function(player)
    bindPlayer(player)
    emit("PLAYER","join=one_client status=WAITING_FOR_PHYSICAL_WALK")
end))
table.insert(connectionList,Players.PlayerRemoving:Connect(function(player)
    local c=characterConns[player]
    if c then c:Disconnect(); characterConns[player]=nil end
    stageByPlayer[player]=nil
    completedByPlayer[player]=nil
    lastByPlayer[player]=nil
    routeStartedAtByPlayer[player]=nil
    emit("PLAYER","leave=one_client status=EVIDENCE_NOT_PERSISTED")
end))
local accumulator=0
table.insert(connectionList,RunService.Heartbeat:Connect(function(dt)
    accumulator+=math.clamp(dt,0,0.25)
    if accumulator<Plan.SAMPLE_INTERVAL then return end
    accumulator=0
    local now=os.clock()
    for _,p in ipairs(Players:GetPlayers()) do tickPlayer(p,now) end
    attemptFullEvidence()
end))

game:BindToClose(function()
    for _,connection in ipairs(connectionList) do connection:Disconnect() end
    for player,connection in pairs(characterConns) do
        connection:Disconnect()
        characterConns[player]=nil
    end
    emit("SHUTDOWN",string.format("active_clients=%d full_scene_gate_pass=%s",
        activeClientCount(),tostring(readyEmitted)))
    if folder and folder.Parent then folder:Destroy() end
end)
