--!strict
-- H2 five-egg SCORE_MODE adapter owned by the ONE existing Game.server.luau.
-- ModuleScript, NOT a second enabled Script, no RemoteEvent / DataStore.
-- DO NOT set live score mode on without OWNER/sole RC approval.
local H2={}
local M=require(script.Parent:WaitForChild("H2ScoreRules"))

local function teamName(p)
    local t=p.Team
    return if t and (t.Name=="RED" or t.Name=="BLUE") then t.Name else "NONE"
end
local function canInteract(p: Player,pos: Vector3,dist: number)
    local c=p.Character
    local root=c and c:FindFirstChild("HumanoidRootPart")
    local h=c and c:FindFirstChildOfClass("Humanoid")
    return root~=nil and root:IsA("BasePart") and h~=nil and h.Health>0
        and (root.Position-pos).Magnitude<=dist
end

function H2.new(args)
    local map=args.map
    local folder=Instance.new("Folder")
    folder.Name="H2_FIVE_EGGS_SAME_GAME"
    folder:SetAttribute("PrivateStudioOnly",true)
    folder:SetAttribute("OriginalGameIsSoleScoreOwner",true)
    folder:SetAttribute("HumanStudioFunQA","NOT_TESTED")
    folder.Parent=map.model
    local objects={}
    local function newEgg(id,pos,label)
        local egg=Instance.new("Part")
        egg.Name="H2_EGG_"..id
        egg.Anchored=true; egg.CanCollide=false; egg.CanTouch=false
        egg.CanQuery=true; egg.Shape=Enum.PartType.Ball
        egg.Size=Vector3.new(4,5,4)
        egg.Position=pos
        egg.Color=Color3.fromRGB(251,228,111)
        egg.Material=Enum.Material.Neon
        egg.Parent=folder
        local p=Instance.new("ProximityPrompt")
        p.ActionText="🥚 卵をもつ"
        p.ObjectText=label
        p.HoldDuration=0.25
        p.MaxActivationDistance=args.distance
        p.RequiresLineOfSight=false
        p.Enabled=false
        p.Parent=egg
        return egg,p
    end
    local function register(id,part,prompt)
        objects[id]={part=part,prompt=prompt,home=part.Position,drop=nil}
        -- In H2 only, existing RED/BLUE original egg prompts are reused, not duplicated.
    end
    register("RED_1",map.teams.RED.egg,map.teams.RED.eggPrompt)
    register("BLUE_1",map.teams.BLUE.egg,map.teams.BLUE.eggPrompt)
    local red2,rp2=newEgg("RED_2",Vector3.new(-98,2.5,20),"赤の2番目の卵")
    register("RED_2",red2,rp2)
    local blue2,bp2=newEgg("BLUE_2",Vector3.new(98,2.5,20),"青の2番目の卵")
    register("BLUE_2",blue2,bp2)
    local centre,cp=newEgg("CENTRE_1",Vector3.new(0,2.5,0),"中央の幻の卵")
    centre.Color=Color3.fromRGB(186,132,252)
    register("CENTRE_1",centre,cp)
    local state=nil
    local serial=0
    local nextSeq:{[Player]:number}={}
    local enabled=false

    local function idFor(p:Player)
        return tostring(p.UserId)
    end
    local function authPlayer(p:Player)
        if not state or state.phase=="FINISHED" then return false end
        if teamName(p)=="NONE" then return false end
        local info=state.players[idFor(p)]
        if not info then
            if not M.addPlayer(state,idFor(p),teamName(p),serial) then return false end
        else
            if info.team~=teamName(p) then return false end
        end
        return true
    end
    local function stepSeq(p:Player)
        nextSeq[p]=(nextSeq[p] or 0)+1
        return nextSeq[p]
    end
    local function refresh()
        for id,entry in pairs(objects) do
            local egg=state and state.eggs[id]
            if not egg then
                entry.prompt.Enabled=false
                entry.part.Transparency=if id=="RED_1" or id=="BLUE_1" then 0 else 1
            else
                if egg.place=="CARRIED" then
                    entry.part.Transparency=1
                    entry.prompt.Enabled=false
                else
                    local pos=entry.home
                    if egg.place=="DROPPED" then
                        pos=entry.drop or entry.home
                    elseif egg.place=="VAULT" and egg.vault~=egg.owner then
                        if egg.vault=="RED" or egg.vault=="BLUE" then
                            local vault=map.teams[egg.vault].scorePad.Position
                            local offset=if id=="CENTRE_1" then 11
                                elseif string.find(id,"_2",1,true) then -13 else 13
                            pos=vault+Vector3.new(0,3,offset)
                        end
                    end
                    entry.part.Position=pos
                    entry.part.Transparency=0
                    entry.prompt.Enabled=enabled and
                        (state.phase=="ACTIVE" or (state.phase=="OVERTIME" and egg.owner=="NEUTRAL"))
                end
            end
        end
        for _,team in ipairs({"RED","BLUE"}) do
            map.teams[team].scorePrompt.Enabled=enabled and state~=nil and
                (state.phase=="ACTIVE" or state.phase=="OVERTIME")
        end
        if state then args.onScores(state.scores) end
    end
    local function notify()
        refresh()
        args.broadcast()
    end

    local adapter={}
    function adapter.reset(matchSerial,allPlayers)
        serial=matchSerial
        state=M.new(serial)
        if not state then error("H2_SCORE_EPOCH_INVALID") end
        table.clear(nextSeq)
        for _,p in ipairs(allPlayers) do
            if teamName(p)~="NONE" then
                M.addPlayer(state,idFor(p),teamName(p),serial)
            end
        end
        for _,entry in pairs(objects) do entry.drop=nil end
        enabled=true
        refresh()
    end
    function adapter.enable(allow)
        enabled=allow==true
        refresh()
    end
    function adapter.onJoin(p)
        if not state or state.phase=="FINISHED" then return end
        authPlayer(p)
    end
    function adapter.onRespawn(p)
        if not state then return end
        M.respawnPlayer(state,serial,idFor(p))
    end
    function adapter.onDrop(p)
        if not state then return end
        local info=state.players[idFor(p)]
        if not info or not info.carrying then return end
        local eggId=info.carrying
        local entry=objects[eggId]
        if entry then
            local char=p.Character
            local root=char and char:FindFirstChild("HumanoidRootPart")
            local pos=if root and root:IsA("BasePart") then root.Position
                else entry.home
            -- Return to a bounded reachable position rather than replicate
            -- arbitrary far client/player coordinates into arena egg objects.
            if math.abs(pos.X)>118 or math.abs(pos.Z)>62 or pos.Y<0 or pos.Y>26 then
                pos=entry.home
            else
                pos=Vector3.new(pos.X,2.5,pos.Z)
            end
            entry.drop=pos
        end
        M.removePlayer(state,serial,idFor(p))
        notify()
    end
    function adapter.snapshot(_p)
        if not state then
            return {scoreMode=true,scorePhase="LOBBY",eggCount=5,
                scoreTime=M.REGULATION,eggs={}}
        end
        local summaries={}
        for _,id in ipairs(M.EGGS) do
            local egg=state.eggs[id]
            local ownerTeam=egg.owner
            local holderTeam=""
            if egg.holder and state.players[egg.holder] then
                holderTeam=state.players[egg.holder].team
            end
            summaries[id]={owner=ownerTeam,place=egg.place,
                vault=egg.vault or "",holderTeam=holderTeam}
        end
        return {scoreMode=true,scorePhase=state.phase,eggCount=5,
            scoreTime=if state.phase=="OVERTIME" then
                math.max(0,270-state.now)
                else math.max(0,240-state.now),
            eggs=summaries}
    end
    function adapter.tick(elapsedSeconds)
        if not state then return nil end
        if state.phase=="FINISHED" then
            return {winner=state.winner or "DRAW",reason=state.finishReason or "SCORE"}
        end
        if M.advance(state,serial,math.max(0,math.floor(elapsedSeconds))) then
            refresh()
            if state.phase=="FINISHED" then
                return {winner=state.winner or "DRAW",reason=state.finishReason or "SCORE"}
            end
        end
        return nil
    end
    function adapter.isCarrying(p)
        local info=state and state.players[idFor(p)]
        return info and info.carrying or nil
    end

    for id,entry in pairs(objects) do
        entry.prompt.Triggered:Connect(function(p:Player)
            if not enabled or not authPlayer(p) then return end
            if not canInteract(p,entry.part.Position,args.distance) then return end
            local info=state.players[idFor(p)]
            if info and info.alive~=true then return end
            local success=M.event(state,serial,idFor(p),stepSeq(p),"PICK",id,true)
            if not success then return end
            entry.drop=nil
            args.onPick(p,id)
            notify()
        end)
    end
    for _,team in ipairs({"RED","BLUE"}) do
        map.teams[team].scorePrompt.Triggered:Connect(function(p:Player)
            if not enabled or not authPlayer(p) or teamName(p)~=team then return end
            if not canInteract(p,map.teams[team].scorePad.Position,args.distance) then return end
            local id=adapter.isCarrying(p)
            if not id then return end
            local success=M.event(state,serial,idFor(p),stepSeq(p),"DEPOSIT",id,true)
            if not success then return end
            args.onDeposit(p,id)
            notify()
        end)
    end
    refresh()
    return adapter
end
return H2
