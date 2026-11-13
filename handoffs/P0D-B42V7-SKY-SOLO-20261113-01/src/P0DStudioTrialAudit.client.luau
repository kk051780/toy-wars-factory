--!strict
-- P0D owner-private Studio diagnostic: read-only Client, NO gameplay authority.
local RunService=game:GetService("RunService")
if not RunService:IsStudio() then return end
local Players=game:GetService("Players")
local ReplicatedStorage=game:GetService("ReplicatedStorage")
local player=Players.LocalPlayer
if player==nil then return end
-- Diagnostics ONLY. Visible on the OWNER's private Studio display; never changes the game.
local panel: TextLabel?=nil
local function status(stage:string)
    if panel then panel.Text="Studio試遊の確認（非公開）\n"..stage.."\n判定は本人の実プレイで" end
end
task.spawn(function()
    local gui=player:WaitForChild("PlayerGui",15)
    if not gui then return end
    local existing=gui:FindFirstChild("P0DStudioTrialAudit")
    if existing then existing:Destroy() end
    local screen=Instance.new("ScreenGui")
    screen.Name="P0DStudioTrialAudit"
    screen.ResetOnSpawn=false
    screen.IgnoreGuiInset=false
    screen.DisplayOrder=110
    local label=Instance.new("TextLabel")
    label.Name="ReadOnlyStatus"
    label.Size=UDim2.fromOffset(296,92)
    label.AnchorPoint=Vector2.new(1,1)
    label.Position=UDim2.new(1,-9,1,-12)
    label.BackgroundColor3=Color3.fromRGB(15,30,44)
    label.BackgroundTransparency=.16
    label.TextColor3=Color3.fromRGB(248,250,255)
    label.TextScaled=false
    label.TextSize=13
    label.TextXAlignment=Enum.TextXAlignment.Left
    label.TextYAlignment=Enum.TextYAlignment.Center
    label.TextWrapped=true
    label.Active=false
    label.Text="Studio試遊の確認（非公開）\n0/4 試合開始待ち\n判定は本人の実プレイで"
    label.Parent=screen
    screen.Parent=gui
    panel=label
end)
local n=0
local function log(kind:string,msg:string,warning:boolean?)
    if n>=110 then return end
    n+=1
    local line="[P0D_STUDIO_FUN_CHECK] "..kind.." | "..msg
    if warning then warn(line) else print(line) end
end
log("START","Private local Studio diagnostic only; NOT a real FUN/physics pass")
local remote=ReplicatedStorage:WaitForChild("TrapRaidersS1Remote",30)
if not remote or not remote:IsA("RemoteEvent") then
    log("BLOCKED","Original remote missing after 30 seconds",true)
    return
end
local activeSeen=false
local carried=false
local scored=false
local lastPhase=""
local lastStep=""
local lastCarry=""
local lastScore=-1
local lastSerial=-1
local lastMode=""
local skyDeck: BasePart?=nil
local skyWithEggSerial=-1
local scoreAfterSkySerial=-1
local activeSerial=-1
local carriedSerial=-1
local skyCarryEgg="" -- exact authoritative snapshot egg ID seen on deck
local skyCarryCharacter: Model?=nil
-- SOURCE_QA_NATIVE_BEGIN: Pure predicates used by the ACTUAL Studio client observer.
-- They are read-only proof gates, not combat/egg/server authority.
local function qualifiesSkyScore(scoreRose: boolean, currentCarry: string,
    previousCarry: string, skyEgg: string, population: number,
    sameCharacter: boolean, sameRound: boolean): boolean
    return scoreRose and currentCarry=="" and previousCarry==skyEgg
        and skyEgg~="" and population==1 and sameCharacter and sameRound
end
local function invalidatesSkyRoute(visited: boolean, completed: boolean,
    currentCarry: string, skyEgg: string, sameCharacter: boolean,
    phase: string): boolean
    return visited and not completed
        and (currentCarry~=skyEgg or not sameCharacter or phase~="ACTIVE")
end
-- SOURCE_QA_NATIVE_END
local function refreshStatus()
    if lastSerial<0 or activeSerial~=lastSerial then
        status("0/4 サーバーの試合開始を待機中")
    elseif carriedSerial~=lastSerial then
        status("1/4 敵の卵を取る（サーバー確認待ち）")
    elseif skyWithEggSerial~=lastSerial then
        status("2/4 卵を持って天空城の床へ登る")
    elseif scoreAfterSkySerial~=lastSerial then
        status("3/4 自陣へ帰って卵を納品する")
    else
        status("4/4 同一卵・天空城接地・ソロ得点確認！\n坂の通行と楽しさは本人が判定")
    end
end
-- Passive server-authored snapshots: NEVER sends remotes or grants rewards.
remote.OnClientEvent:Connect(function(msg:any)
    if type(msg)~="table" or msg.kind~="SNAPSHOT" then return end
    local serial=if type(msg.serial)=="number" then msg.serial else -1
    local phase=if type(msg.phase)=="string" then msg.phase else "UNKNOWN"
    local team=if msg.team=="RED" or msg.team=="BLUE" then msg.team else "NONE"
    local mode=if type(msg.scoreMode)=="string" then msg.scoreMode else "UNKNOWN"
    local carry=if type(msg.carrying)=="string" then msg.carrying else ""
    local score=if type(msg.scores)=="table" and type(msg.scores[team])=="number"
        then msg.scores[team] else -1
    if serial~=lastSerial then
        log("ROUND","serial="..tostring(serial).." team="..team)
        lastSerial=serial;lastScore=-1;lastCarry="";lastStep=""
        activeSerial=-1;carriedSerial=-1;skyWithEggSerial=-1;scoreAfterSkySerial=-1
        skyCarryEgg="";skyCarryCharacter=nil
        carried=false;scored=false
    end
    if phase=="ACTIVE" then activeSeen=true;activeSerial=serial end
    if phase~=lastPhase or mode~=lastMode then
        log("PHASE",phase.." mode="..mode.." RED="..tostring(msg.redPlayers)
            .." BLUE="..tostring(msg.bluePlayers).." remaining="..tostring(msg.time))
        lastPhase=phase;lastMode=mode
        if phase=="RESULTS" then
            log("RESULT","winner="..tostring(msg.winner).." reason="..tostring(msg.reason)
                .." carry_seen="..tostring(carried).." score_seen="..tostring(scored))
        end
    end
    local previousCarry=lastCarry
    if carry~=lastCarry then
        if carry~="" then
            carried=true;carriedSerial=serial
            log("EGG_CARRIED","server-confirmed owner="..carry.." by team="..team)
        elseif lastCarry~="" then
            log("EGG_RELEASED","check next SCORE_CONFIRMED; drop is not a score")
        end
        lastCarry=carry
    end
    local scoreRose=lastScore>=0 and score>lastScore
    local population=if type(msg.redPlayers)=="number" and type(msg.bluePlayers)=="number"
        then msg.redPlayers+msg.bluePlayers else -1
    local ownerStillSame=skyCarryCharacter~=nil and player.Character==skyCarryCharacter
    local validSameEggDeposit=qualifiesSkyScore(scoreRose,carry,previousCarry,
        skyCarryEgg,population,ownerStillSame,
        skyWithEggSerial==serial and activeSerial==serial)
    if scoreRose then
        scored=true
        log("SCORE_CONFIRMED","team="..team.." score="..tostring(score))
        if validSameEggDeposit then
            scoreAfterSkySerial=serial
            log("SCORE_AFTER_SKY","single-player, same-server-egg carry->sky-raycast->deposit receipt; real walking/FUN still owner-verified")
        else
            log("SCORE_NOT_QUALIFIED","score changed without continuous identical sky egg + real single-player deposit")
        end
    end
    -- If the egg changes or disappears before a valid score snapshot, reset the sky
    -- checkpoint. Never let a drop -> re-pickup -> unrelated score produce a false 4/4.
    if invalidatesSkyRoute(skyWithEggSerial==serial,
        scoreAfterSkySerial==serial,carry,skyCarryEgg,ownerStillSame,phase) then
        skyWithEggSerial=-1
        skyCarryEgg=""
        skyCarryCharacter=nil
        log("ROUTE_RESET","egg lost/swapped, respawned or match left ACTIVE before deposit")
    end
    lastScore=score
    local first90=msg.first90
    local step=if type(first90)=="table" and first90.visible==true
        and type(first90.step)=="string" then first90.step else "HIDDEN"
    if step~=lastStep then
        log("FIRST90","step="..step)
        lastStep=step
    end
    refreshStatus()
end)
-- Client-side physical position observation with server-owned carrying snapshot.
-- This is NOT proof of continuous egg transport: OWNER must manually observe the walk.
task.spawn(function()
    while player.Parent~=nil do
        task.wait(.35)
        local deck=skyDeck
        if deck and deck.Parent and lastSerial>=0 and activeSerial==lastSerial
            and skyWithEggSerial~=lastSerial and lastCarry~=""
            and #Players:GetPlayers()==1 then
            local character=player.Character
            local hum=if character then character:FindFirstChildOfClass("Humanoid") else nil
            local root=if character then character:FindFirstChild("HumanoidRootPart") else nil
            if hum and root and root:IsA("BasePart") and hum.Health>0
                and hum.FloorMaterial~=Enum.Material.Air then
                local pos=root.Position
                local top=deck.Position.Y+deck.Size.Y/2
                if math.abs(pos.X-deck.Position.X)<=deck.Size.X/2-2
                    and math.abs(pos.Z-deck.Position.Z)<=deck.Size.Z/2-2
                    and pos.Y>=top+1 and pos.Y<=top+6 then
                    local rayParams=RaycastParams.new()
                    rayParams.FilterType=Enum.RaycastFilterType.Exclude
                    rayParams.FilterDescendantsInstances={character}
                    rayParams.IgnoreWater=true
                    local hit=workspace:Raycast(pos,Vector3.new(0,-9,0),rayParams)
                    if hit and hit.Instance==deck then
                        skyWithEggSerial=lastSerial
                        skyCarryEgg=lastCarry
                        skyCarryCharacter=character
                        log("SKY_WITH_EGG","grounded character raycast hit exact physical island deck while original server snapshot reported egg="..skyCarryEgg)
                        refreshStatus()
                    end
                end
            end
        end
    end
end)
-- Replica inspection is a scene construction check, never a walkability proof.
task.spawn(function()
    local arena=workspace:WaitForChild("TRAP_RAIDERS_S1",30)
    if not arena then log("BLOCKED","Original arena missing",true);return end
    local world=arena:WaitForChild("H1_FUN_WORLD",20)
    if not world then log("BLOCKED","Original SkyCastle overlay missing",true);return end
    local needed={
        "SKY_RAMP_RED","SKY_WALKWAY","SKY_RAMP_BLUE","FLOATING_SKY_ISLAND",
        "SKY_FORT_ENTRY_RED","SKY_FORT_ENTRY_BLUE",
        "SKY_FORT_ESCAPE_RED","SKY_FORT_ESCAPE_BLUE"
    }
    local count=0
    for _,name in ipairs(needed) do
        local p=world:FindFirstChild(name)
        if p and p:IsA("BasePart") and p.CanCollide then
            count+=1
        else log("BLOCKED","physical part missing or noncollidable "..name,true) end
    end
    local deck=world:FindFirstChild("FLOATING_SKY_ISLAND")
    if deck and deck:IsA("BasePart") and deck.CanCollide then skyDeck=deck end
    local top=if deck and deck:IsA("BasePart")
        then deck.Position.Y+deck.Size.Y/2 else -999
    log("SKY_SOURCE","replicated collidable parts="..tostring(count)
        .."/"..tostring(#needed).." deck_topY="..tostring(top)
        .." (real movement NOT_TESTED)")
    for _,team in ipairs({"RED","BLUE"}) do
        local base=arena:FindFirstChild(team.."_CASTLE")
        local egg=if base then base:FindFirstChild(team.."_EGG") else nil
        local pad=if base then base:FindFirstChild(team.."_SCORE_PAD") else nil
        local e=if egg then egg:FindFirstChildOfClass("ProximityPrompt") else nil
        local p=if pad then pad:FindFirstChildOfClass("ProximityPrompt") else nil
        log("OBJECTIVE_SOURCE",team.." egg="..tostring(egg~=nil)
            .." pad="..tostring(pad~=nil).." pickupPrompt="..tostring(e~=nil)
            .." scorePrompt="..tostring(p~=nil))
        if not egg or not pad or not e or not p then
            log("BLOCKED","Original objective source missing for "..team,true)
        end
    end
end)
task.delay(120,function()
    if not activeSeen then
        log("BLOCKED","No authoritative ACTIVE snapshot after 120 seconds",true)
    else
        log("CHECKPOINT","ACTIVE seen, egg_carried="..tostring(carried)
            ..", score_confirmed="..tostring(scored)
            ..", sky_egg="..tostring(skyWithEggSerial==lastSerial)
            ..", score_after_sky="..tostring(scoreAfterSkySerial==lastSerial)
            ..", same_egg_required=true, one_player_required=true"
            ..". Owner must physically walk/carry/play and judge FUN.")
    end
end)
