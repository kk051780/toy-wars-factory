--!strict
-- OWNED PRIVATE ROBLOX STUDIO PLACE ONLY. Disabled by default.
-- Actual creature creation/animation happens only if the OWNER flips the
-- flag inside an unpublished, backed-up test clone. Not D18/real economy.
local ENABLE_RARE_NEUTRAL_STUDIO_PREVIEW = false
if not ENABLE_RARE_NEUTRAL_STUDIO_PREVIEW then return end

local RunService = game:GetService("RunService")
assert(RunService:IsStudio(),"RARE_NEUTRAL_NO_LIVE_GAME")
assert(workspace:FindFirstChild("TRAP_RAIDERS_S1")==nil,
    "RARE_NEUTRAL_NO_OFFICIAL_S1_OVERLAP")
local Players = game:GetService("Players")
local Catalog=require(script.Parent.RareRealmCatalog)
local Scene=require(script.Parent.RareRealmScene)
local Policy=require(script.Parent.RareEncounterPolicy)
local Models=require(script.Parent.RareEncounterModels)
local valid,reason=Policy.validate()
assert(valid,reason)

local map=Scene.build(workspace)
local layer=Instance.new("Folder")
layer.Name="RARE_NEUTRAL_SERVER_ENCOUNTERS"
layer.Parent=map.folder
layer:SetAttribute("NoDropsNoCurrency",true)
layer:SetAttribute("NoPaidOdds",true)
layer:SetAttribute("D18CanonNotAdopted",true)

local rng=Random.new()
local started=os.clock()
local stepState=Policy.newState()
local current=nil
local foundBy={}
local promptConnection=nil
local heartbeatConnection=nil
local removingConnection=nil
local acc=0

local function report(eventName:string,detail:string)
    print("P0D_RARE_NEUTRAL_STUDIO_LOCAL event="..eventName.." "..detail..
        " rewards=NONE canon_D18=NOT_ADOPTED")
end

local function removeCurrent()
    if promptConnection then promptConnection:Disconnect();promptConnection=nil end
    if current and current.encounter and current.encounter.model then
        current.encounter.model:Destroy()
    end
    current=nil
    foundBy={}
end

local function validPlayerNear(player,body): boolean
    if not player or not player:IsDescendantOf(Players) then return false end
    local char=player.Character
    if not char then return false end
    local human=char:FindFirstChildOfClass("Humanoid")
    local root=char:FindFirstChild("HumanoidRootPart")
    if not human or human.Health<=0 or not root or not root:IsA("BasePart") then
        return false
    end
    return (root.Position-body.Position).Magnitude<=Policy.MIN_INTERACTION_DISTANCE
end

local function activate(id:string,serial:number,now:number)
    assert(current==nil,"NEUTRAL_SINGLE_GLOBAL_ACTIVE")
    local canonical=Catalog.WORLDS[id]
    assert(canonical~=nil,"ENCOUNTER_WORLD_NOT_IN_ORIGINAL_MAP")
    local encounter=Models.create(id,layer)
    local pivot=Vector3.new(canonical.center.x,canonical.center.y,canonical.center.z)
    current={encounter=encounter,pivot=pivot,id=id,serial=serial,born=now}
    foundBy={}
    encounter.prompt.Enabled=false
    Models.update(encounter,pivot,0)
    promptConnection=encounter.prompt.Triggered:Connect(function(player)
        if not current or current.serial~=serial
            or not current.encounter.prompt.Enabled
            or not validPlayerNear(player,current.encounter.body)
            or foundBy[player] then return end
        foundBy[player]=true
        report("DISCOVERED",
            "realm="..id.." player=LOCAL_STUDIO_ONLY first_discovery=true no_reward=true")
    end)
    report("SPAWN",
        "realm="..id.." active_global=1 preview_chance_per_45s=0.12 no_real_drop=true")
end

removingConnection=Players.PlayerRemoving:Connect(function(player)
    foundBy[player]=nil
end)
heartbeatConnection=RunService.Heartbeat:Connect(function(dt)
    acc+=math.clamp(dt,0,0.25)
    if acc<0.2 then return end
    acc=0
    local now=os.clock()-started
    -- RNG is server-owned. This is NOT client-claimed randomness.
    local nextState,event=Policy.step(stepState,now,rng:NextNumber())
    stepState=nextState
    if event.kind=="DESPAWN" then
        report("DESPAWN","realm="..tostring(event.id).." active_global=0")
        removeCurrent()
    elseif event.kind=="SPAWN" then
        if not current then activate(event.id,event.serial,now) end
    elseif event.kind=="RNG_INVALID" or event.kind=="INVALID" then
        report("BLOCKED","reason="..event.kind)
    end
    if current then
        local life=now-current.born
        if life>=0 then
            Models.update(current.encounter,current.pivot,life)
            current.encounter.prompt.Enabled=life>=Policy.TELEGRAPH_SECONDS
        end
    end
end)

report("BOOT","private_Studio_only=true start_in_test_clone=true one_global_neutral=true")
report("LIMITS","actual_2client_qa=NOT_TESTED phone_FPS=NOT_TESTED real_drop_AI=NOT_TESTED")
game:BindToClose(function()
    if heartbeatConnection then heartbeatConnection:Disconnect() end
    if removingConnection then removingConnection:Disconnect() end
    removeCurrent()
    if map.folder and map.folder.Parent then map.folder:Destroy() end
    report("STOP","private_preview_cleaned=true")
end)
