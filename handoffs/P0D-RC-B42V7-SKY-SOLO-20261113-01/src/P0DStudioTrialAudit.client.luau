--!strict
-- P0D owner-private Studio diagnostic: read-only Client, NO gameplay authority.
local RunService=game:GetService("RunService")
if not RunService:IsStudio() then return end
local Players=game:GetService("Players")
local ReplicatedStorage=game:GetService("ReplicatedStorage")
if Players.LocalPlayer==nil then return end
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
    end
    if phase~=lastPhase or mode~=lastMode then
        log("PHASE",phase.." mode="..mode.." RED="..tostring(msg.redPlayers)
            .." BLUE="..tostring(msg.bluePlayers).." remaining="..tostring(msg.time))
        lastPhase=phase;lastMode=mode
        if phase=="ACTIVE" then activeSeen=true end
        if phase=="RESULTS" then
            log("RESULT","winner="..tostring(msg.winner).." reason="..tostring(msg.reason)
                .." carry_seen="..tostring(carried).." score_seen="..tostring(scored))
        end
    end
    if carry~=lastCarry then
        if carry~="" then
            carried=true
            log("EGG_CARRIED","server-confirmed owner="..carry.." by team="..team)
        elseif lastCarry~="" then
            log("EGG_RELEASED","check next SCORE_CONFIRMED; drop is not a score")
        end
        lastCarry=carry
    end
    if lastScore>=0 and score>lastScore then
        scored=true
        log("SCORE_CONFIRMED","team="..team.." score="..tostring(score))
    end
    lastScore=score
    local first90=msg.first90
    local step=if type(first90)=="table" and first90.visible==true
        and type(first90.step)=="string" then first90.step else "HIDDEN"
    if step~=lastStep then
        log("FIRST90","step="..step)
        lastStep=step
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
            ..". Owner must physically walk/carry/play and judge FUN.")
    end
end)
