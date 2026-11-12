--!strict
-- OWNER-ONLY disposable unpublished Studio 2-client observation bench.
-- DEFAULT OFF. This is a deterministic QA schedule, NOT real spawn odds.
local ENABLE_RARE_DISCOVERY_STUDIO_BOOK = false
if not ENABLE_RARE_DISCOVERY_STUDIO_BOOK then return end

local RunService=game:GetService("RunService")
assert(RunService:IsStudio(),"RARE_BOOK_NO_LIVE_ROBLOX")
assert(RunService:IsServer(),"RARE_BOOK_SERVER_ONLY")
assert(workspace:FindFirstChild("TRAP_RAIDERS_S1")==nil,"RARE_BOOK_NO_OFFICIAL_RC")
local Players=game:GetService("Players")
local Scene=require(script.Parent.RareRealmScene)
local Models=require(script.Parent.RareEncounterModels)
local Policy=require(script.Parent.RareEncounterPolicy)
local Book=require(script.Parent.RareDiscoveryBook)
local HUD=require(script.Parent.RareDiscoveryHUD)
local Plan=require(script.Parent.RareDiscoveryQAPlan)
local Clue=require(script.Parent.RareCluePolicy)
local ClueHUD=require(script.Parent.RareClueHUD)
local goodBook,bookWhy=Book.validate()
local goodPlan,planWhy=Plan.validate()
local goodClue,clueWhy=Clue.validate()
assert(goodBook and goodPlan and goodClue,bookWhy.." / "..planWhy.." / "..clueWhy)

local map=Scene.build(workspace)
local layer=Instance.new("Folder")
layer.Name="RARE_DISCOVERY_BENCH_ONLY"
layer:SetAttribute("DeterministicNonProduction",true)
layer:SetAttribute("D18CanonStatus","NOT_ADOPTED")
layer:SetAttribute("Rewards","NONE")
layer.Parent=map.folder

local books={}
local eligibleAt={}
local lastMovement={}
local characterConns={}
local active=nil
local promptConn=nil
local connections={}
local serialTwoClient={}
local allCompleteLogged=false
local base=os.clock()
local accumulated=0

local function emit(kind:string,detail:string)
    print("RARE_DISCOVERY_REAL_STUDIO_WITNESS event="..kind.." "..detail..
        " rewards=NONE D18=NOT_ADOPTED PRODUCTION=FALSE")
end

local function clearActive()
    if promptConn then promptConn:Disconnect();promptConn=nil end
    if active and active.visual and active.visual.model then
        active.visual.model:Destroy()
    end
    active=nil
end

local function playerValidNear(player:Player,body:BasePart,now:number):boolean
    if not player or not player:IsDescendantOf(Players) or
        not books[player] or not active or not active.visual.prompt.Enabled or
        not body or not body.Parent then return false end
    if (eligibleAt[player] or math.huge)>now then return false end
    local ch=player.Character
    if not ch then return false end
    local humanoid=ch:FindFirstChildOfClass("Humanoid")
    local root=ch:FindFirstChild("HumanoidRootPart")
    if not humanoid or humanoid.Health<=0 or not root or
        not root:IsA("BasePart") or root.Anchored then return false end
    return (root.Position-body.Position).Magnitude<=Policy.MIN_INTERACTION_DISTANCE
end

local function activeUserCount():number
    local count=0
    for _,player in ipairs(Players:GetPlayers()) do
        local c=player.Character
        local root=c and c:FindFirstChild("HumanoidRootPart")
        local humanoid=c and c:FindFirstChildOfClass("Humanoid")
        if root and humanoid and humanoid.Health>0 then count+=1 end
    end
    return count
end

local function checkTwoClientFullBook()
    if allCompleteLogged or activeUserCount()<2 then return end
    local count=0
    for _,player in ipairs(Players:GetPlayers()) do
        if books[player] and books[player].count==4 then count+=1 end
    end
    if count>=2 then
        allCompleteLogged=true
        emit("TWO_CLIENT_INDEPENDENT_BOOK_4_OF_4",
            "status=PASS independent_real_player_count>=2 server_near_prompt_observed=true")
        emit("REMAINS_UNTESTED",
            "mobile_touch_FPS=NOT_MEASURED physics_comfort=NOT_MEASURED official_S1=NOT_INTEGRATED")
    end
end

local function show(id:string,serial:number,elapsed:number)
    assert(active==nil,"BENCH_SINGLE_NEUTRAL_ACTIVE")
    local p=Plan.point(id)
    assert(p~=nil,"QA_BENCH_UNKNOWN_WORLD")
    local visual=Models.create(id,layer)
    active={id=id,serial=serial,startTime=elapsed,basePosition=p,visual=visual,
        twoClients={},twoClientPrinted=false}
    visual.prompt.Enabled=false
    Models.update(visual,p,0)
    promptConn=visual.prompt.Triggered:Connect(function(player)
        local current=active
        if not current or current.serial~=serial or not current.visual.model.Parent then return end
        local now=os.clock()
        local lifetime=now-base-current.startTime
        if lifetime<Plan.PROMPT_DELAY_SECONDS or
           lifetime>=Plan.EXPOSURE_SECONDS or
           not playerValidNear(player,current.visual.body,now) then
            emit("REJECTED_PROMPT","reason=invalid_timing_distance_or_character")
            return
        end
        local previous=books[player]
        local nextBook,result=Book.accept(previous,id,serial)
        if result=="NEW" then
            books[player]=nextBook
            HUD.update(player,nextBook)
            ClueHUD.update(player,nextBook)
            current.twoClients[player]=true
            emit("NEW_DISCOVERY","realm="..id.." progress="..Book.progress(nextBook)..
                " no_inventory=true")
            local n=0
            for participant in pairs(current.twoClients) do
                if participant:IsDescendantOf(Players) and books[participant] then n+=1 end
            end
            if n>=2 and not current.twoClientPrinted then
                current.twoClientPrinted=true
                serialTwoClient[serial]=true
                emit("TWO_REAL_CLIENT_SAME_CREATURE",
                    "realm="..id.." distinct_live_clients>=2 no_stored_user_ids=true")
            end
            checkTwoClientFullBook()
        elseif result=="ALREADY_SEEN" or result=="REPEAT" then
            emit("IGNORED_DUPLICATE","realm="..id)
        else
            emit("BLOCKED_DISCOVERY","reason="..result)
        end
    end)
    emit("CREATURE_VISIBLE","realm="..id.." slot="..tostring(serial)..
        " deterministic_QA_bench=true original_real_randomness=NOT_TESTED")
end

local function register(player:Player)
    books[player]=Book.fresh()
    eligibleAt[player]=os.clock()+1
    lastMovement[player]=nil
    characterConns[player]=player.CharacterRemoving:Connect(function()
        eligibleAt[player]=os.clock()+1.5
        lastMovement[player]=nil
    end)
    task.spawn(function()
        local gui=player:WaitForChild("PlayerGui",10)
        if gui and player:IsDescendantOf(Players) and books[player] then
            HUD.mount(player,books[player])
            ClueHUD.mount(player,books[player])
            emit("SESSION_HUD_MOUNTED","personal_book=0/4 no_saved_data=true")
        end
    end)
end
for _,player in ipairs(Players:GetPlayers()) do register(player) end
table.insert(connections,Players.PlayerAdded:Connect(register))
table.insert(connections,Players.PlayerRemoving:Connect(function(player)
    if characterConns[player] then
        characterConns[player]:Disconnect()
        characterConns[player]=nil
    end
    books[player]=nil
    eligibleAt[player]=nil
    lastMovement[player]=nil
    if active then active.twoClients[player]=nil end
    emit("LEFT","session_data_discarded=true")
end))

table.insert(connections,RunService.Heartbeat:Connect(function(dt)
    accumulated+=math.clamp(dt,0,0.25)
    if accumulated<0.20 then return end
    accumulated=0
    local now=os.clock()
    local elapsed=now-base
    local id,slot=Plan.at(elapsed)
    if active and (id~=active.id or slot+1~=active.serial) then
        emit("CREATURE_EXPIRED","realm="..active.id)
        clearActive()
    end
    if id and not active then show(id,slot+1,elapsed) end
    for _,player in ipairs(Players:GetPlayers()) do
        local char=player.Character
        local root=char and char:FindFirstChild("HumanoidRootPart")
        local h=char and char:FindFirstChildOfClass("Humanoid")
        if root and root:IsA("BasePart") and h and h.Health>0 then
            local old=lastMovement[player]
            if old then
                local seconds=now-old.time
                if seconds>0.01 and (root.Position-old.pos).Magnitude/seconds>80 then
                    eligibleAt[player]=now+2
                    emit("SUSPECT_MOVEMENT",
                        "prompt_blocked_for_2s=true neither_move_nor_teleport_player=true")
                end
            end
            lastMovement[player]={time=now,pos=root.Position}
        else
            lastMovement[player]=nil
        end
    end
    if active then
        local life=elapsed-active.startTime
        Models.update(active.visual,active.basePosition,life)
        active.visual.prompt.Enabled=life>=Plan.PROMPT_DELAY_SECONDS
            and life<Plan.EXPOSURE_SECONDS
    end
    checkTwoClientFullBook()
end))

emit("BOOT","studio_only=true 2clients_recommended=true 4_test_slots_in_104s=true")
emit("LIMIT","not_real_rarity=true not_D18_collection=true no_inventory=true no_remote=true")
game:BindToClose(function()
    for _,c in ipairs(connections) do c:Disconnect() end
    for player,c in pairs(characterConns) do
        c:Disconnect()
        characterConns[player]=nil
    end
    clearActive()
    for player in pairs(books) do books[player]=nil end
    if map.folder and map.folder.Parent then map.folder:Destroy() end
    emit("STOP","local_witness_complete=true no_real_mobile_QA_claim=true")
end)
