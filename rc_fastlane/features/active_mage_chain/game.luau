function SevenJobs.showChainArc(parent: Instance,from: Vector3,positions: {Vector3},tell: boolean)
    if #positions==0 then return end
    -- One noninteractive holder, at most five short Beam links.
    local effect=Instance.new("Part")
    effect.Name=if tell then "P0D_MAGE_CHAIN_TELL" else "P0D_MAGE_CHAIN_HIT"
    effect.Size=Vector3.new(.1,.1,.1)
    effect.Transparency=1
    effect.Anchored=true
    effect.CanCollide=false
    effect.CanTouch=false
    effect.CanQuery=false
    effect.CastShadow=false
    effect.CFrame=CFrame.new(from)
    local previous=Instance.new("Attachment")
    previous.Parent=effect
    for _,position in ipairs(positions) do
        local endpoint=Instance.new("Attachment")
        endpoint.Position=position-from
        endpoint.Parent=effect
        local beam=Instance.new("Beam")
        beam.Attachment0=previous
        beam.Attachment1=endpoint
        beam.Color=ColorSequence.new(Color3.fromRGB(255,222,120),Color3.fromRGB(255,248,208))
        beam.Transparency=NumberSequence.new(if tell then .65 else .16)
        beam.Width0=if tell then .09 else .26
        beam.Width1=if tell then .06 else .15
        beam.FaceCamera=true
        beam.LightEmission=.24
        beam.Parent=effect
        previous=endpoint
    end
    effect.Parent=parent
    game:GetService("Debris"):AddItem(effect,if tell then SevenJobs.Chain.tellSeconds else .22)
end

function SevenJobs.useMageChain(player: Player,data: any)
    if not SevenJobs.chainSelected(player) or not Rules.validSeq(data.seq,lastSeq[player] or 0) then return end
    lastSeq[player]=data.seq
    local now=serverNow()
    local state=SevenJobs.activeGrowth(player)
    local character=player.Character
    local alive,root=healthy(player)
    if not state or not character or not alive or not root or carry[player]~=nil or slowed[player]~=nil
        or not SevenJobs.growthCastReady(player,state,now) then return end
    local config=SevenJobs.Chain
    if SevenJobs.chainCooldown(state,now)>0 or state.energy<config.energy then return end
    local facing=root.CFrame.LookVector
    local direction=Vector3.new(facing.X,0,facing.Z)
    if direction.Magnitude<.001 then return end
    direction=direction.Unit
    local origin=root.Position
    local clear=horde:mageChainLineOfSight(character)
    local first=horde:mageChainSeed(origin,direction,clear)
    if not first then return end
    local stage=SevenJobs.Growth.stage(state)
    local selectedAt=sevenJobLastChoose[player]
    local side=getTeamName(player)
    state.energy-=config.energy
    state.lastChain=now
    SevenJobs.showChainArc(map.model,origin,{first.pos},true)
    remote:FireClient(player,snapshotFor(player))
    task.delay(config.tellSeconds,function()
        local impactNow=serverNow()
        local living,current=healthy(player)
        if not living or current~=root or player.Character~=character
            or not SevenJobs.chainSelected(player) or SevenJobs.activeGrowth(player)~=state
            or sevenJobLastChoose[player]~=selectedAt or getTeamName(player)~=side
            or carry[player]~=nil or slowed[player]~=nil
            or not SevenJobs.growthCastReady(player,state,impactNow)
            or (root.Position-origin).Magnitude>6 then return end
        local impactOrigin=root.Position
        -- The original warned target must remain the authorized seed. No hidden retargeting.
        if horde:mageChainSeed(impactOrigin,direction,clear,first)~=first then return end
        local impact={first=first,stage=stage,clear=clear,positions={}}
        local hits=sevenJobStrike(player,impactOrigin,direction,SevenJobs.DETAILS.MAGE.damage,
            nil,nil,true,nil,impact)
        if hits==0 then return end
        SevenJobs.showChainArc(map.model,impactOrigin,impact.positions,false)
        remote:FireClient(player,snapshotFor(player))
    end)
end
