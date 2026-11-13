--!strict
-- P0D H1 / ISOLATED Studio-only neutral encounters. ONE Game.server drives tick/hit.
-- No RemoteEvent, no task scheduler, no XP/egg/score/damage-player authority.
local Combat=require(script.Parent:WaitForChild("MusouCombatRules"))
local Horde = {}
Horde.__index = Horde
local MINIONS = 8
local ELITE_HP = 72
local MINION_HP = 24
local MAX_ACTIVE = 9
local function horizontal(a: Vector3,b: Vector3): (Vector3,number)
    local v=Vector3.new(b.X-a.X,0,b.Z-a.Z)
    local d=v.Magnitude
    return (if d>0.001 then v/d else Vector3.new(1,0,0)),d
end
local function makeBody(folder: Folder, id: number, elite: boolean, p: Vector3)
    local model=Instance.new("Model")
    model.Name=if elite then "MUSOU_ELITE_TELEGRAPH" else "MUSOU_MINION_"..tostring(id)
    local body=Instance.new("Part")
    body.Name="Core"
    body.Anchored=true
    body.CanCollide=false
    body.CanTouch=false
    body.CanQuery=false
    body.Material=Enum.Material.SmoothPlastic
    body.Shape=Enum.PartType.Block
    body.Size=if elite then Vector3.new(4,5,3) else Vector3.new(2.6,3.3,2)
    body.Color=if elite then Color3.fromRGB(120,75,175) else Color3.fromRGB(68,151,107)
    body.CFrame=CFrame.new()
    body.Parent=model
    model.PrimaryPart=body
    local head=Instance.new("Part")
    head.Name="Head"
    head.Anchored=true
    head.CanCollide=false
    head.CanTouch=false
    head.CanQuery=false
    head.Shape=Enum.PartType.Ball
    head.Size=if elite then Vector3.new(3.2,3.2,3.2) else Vector3.new(2.3,2.3,2.3)
    head.Color=if elite then Color3.fromRGB(218,177,100) else Color3.fromRGB(174,214,135)
    head.Position=Vector3.new(0,if elite then 3.8 else 2.9,0)
    head.Parent=model
    for sign=-1,1,2 do
        local eye=Instance.new("Part")
        eye.Name="Eye"
        eye.Shape=Enum.PartType.Ball
        eye.Anchored=true
        eye.CanCollide=false
        eye.CanTouch=false
        eye.CanQuery=false
        eye.Size=Vector3.new(.32,.4,.2)
        eye.Color=Color3.fromRGB(30,30,42)
        eye.Position=Vector3.new(sign*(if elite then .75 else .55),if elite then 4.15 else 3.2,-1.1)
        eye.Parent=model
    end
    local gui=Instance.new("BillboardGui")
    gui.Name="CombatCue"
    gui.AlwaysOnTop=true
    gui.Size=UDim2.fromOffset(110,43)
    gui.StudsOffsetWorldSpace=Vector3.new(0,if elite then 6.5 else 4.8,0)
    gui.Parent=body
    local text=Instance.new("TextLabel")
    text.Size=UDim2.fromScale(1,1)
    text.BackgroundTransparency=.25
    text.BackgroundColor3=Color3.fromRGB(16,19,31)
    text.TextColor3=Color3.fromRGB(255,251,237)
    text.TextScaled=true
    text.Text=if elite then "⚠ 精鋭" else "中立兵"
    text.Parent=gui
    model.Parent=folder
    model:PivotTo(CFrame.new(p))
    return model,body,text
end
local function groundTop(world: Instance,x: number,z: number): number
    -- Read actual original MapBuilder walkable parts, not a hard-coded
    -- assumed Y. Source-map arena center -3, size4 -> ground top -1;
    -- road center -.85, thickness .3 -> drivable top -.70.
    local arena=world:FindFirstChild("GrassArena")
    assert(arena and arena:IsA("BasePart"),"MUSOU_SOURCE_MAP_ARENA_REQUIRED")
    local y=arena.Position.Y+arena.Size.Y*.5
    local road=world:FindFirstChild("CenterRoad")
    if road and road:IsA("BasePart")
        and math.abs(x-road.Position.X)<=road.Size.X*.5
        and math.abs(z-road.Position.Z)<=road.Size.Z*.5 then
        y=math.max(y,road.Position.Y+road.Size.Y*.5)
    end
    return y
end
function Horde.new(world: Instance)
    local folder=Instance.new("Folder")
    folder.Name="EGG_RUMBLE_NEUTRAL_MUSOU_EXPERIMENT"
    folder.Parent=world
    return setmetatable({folder=folder,world=world,mobs={},round=-1,lastTick=0,kills=0},Horde)
end
function Horde:clear()
    for _,m in ipairs(self.mobs) do m.model:Destroy() end
    table.clear(self.mobs)
end
function Horde:reset(round: number,now: number)
    self:clear()
    self.round=round
    self.lastTick=now
    self.kills=0
    -- Center routes within the original 250x142 arena, NOT remote fantasy scenery.
    for i=1,MAX_ACTIVE do
        local elite=(i==MAX_ACTIVE)
        local x=if elite then 0 else ((i-1)%4-1.5)*16
        local z=if elite then 0 else (if i<=4 then -18 else 18)
        -- Spawn one body-height above the REAL playable floor (not levitating).
        -- CenterRoad and GrassArena are unchanged original MapBuilder parts.
        local feetY=groundTop(self.world,x,z)
        local halfBody=if elite then 2.5 else 1.65
        local base=Vector3.new(x,feetY+halfBody,z)
        local model,body,cue=makeBody(self.folder,i,elite,base)
        table.insert(self.mobs,{
            model=model,body=body,cue=cue,pos=base,home=base,
            hp=if elite then ELITE_HP else MINION_HP,
            maxHp=if elite then ELITE_HP else MINION_HP,
            elite=elite,deadUntil=0,attackAt=0,tellUntil=0,
            target=nil,flashUntil=0,
        })
    end
end
function Horde:livingCount(): number
    local n=0
    for _,m in ipairs(self.mobs) do if m.hp>0 then n+=1 end end
    return n
end
function Horde:hit(origin: Vector3,facing: Vector3,damage: number,now: number,ignore: Instance?): (number,number)
    if self.round<0 then return 0,0 end
    local direction=Vector3.new(facing.X,0,facing.Z)
    direction=if direction.Magnitude>.001 then direction.Unit else Vector3.new(1,0,0)
    local touched=0
    local defeated=0
    local params=RaycastParams.new()
    params.FilterType=Enum.RaycastFilterType.Exclude
    params.FilterDescendantsInstances=if ignore then {ignore,self.folder} else {self.folder}
    for _,m in ipairs(self.mobs) do
        if m.hp>0 and touched<6 then
            local unit,dist=horizontal(origin,m.pos)
            local vertical=origin.Y-m.pos.Y
            local facingDot=direction:Dot(unit)
            if Combat.canSweep(dist,vertical,facingDot,true) then
                local ray=workspace:Raycast(origin,m.pos-origin,params)
                if Combat.canSweep(dist,vertical,facingDot,ray==nil) then
                    touched+=1
                    local dealt=math.max(1,math.min(math.floor(damage),40))
                    m.hp=math.max(0,m.hp-dealt)
                    m.flashUntil=now+.18
                    m.body.Color=Color3.fromRGB(253,231,111)
                    -- Real server-owned short knockback; no ragdoll or physics ownership.
                    local nextPos=m.pos+unit*math.min(2,math.max(0,dist*.12))
                    local homeDist=(nextPos-m.home).Magnitude
                    if homeDist<22 then
                        m.pos=nextPos
                        m.model:PivotTo(CFrame.new(nextPos))
                    end
                    if m.hp<=0 then
                        defeated+=1
                        self.kills+=1
                        -- Kill is atomic for this one server-owned NPC: cancel ANY
                        -- windup/target so a dead elite cannot strike after respawn.
                        m.tellUntil=0
                        m.target=nil
                        m.deadUntil=now+8
                        m.attackAt=now+9.5
                        m.cue.Text=if m.elite then "💥 精鋭撃破！" else "💥 撃破！"
                        m.model:PivotTo(CFrame.new(m.pos+Vector3.new(0,-30,0)))
                    else
                        m.cue.Text=(if m.elite then "精鋭 " else "中立 ")..tostring(m.hp).."/"..tostring(m.maxHp)
                    end
                end
            end
        end
    end
    return touched,defeated
end
function Horde:tick(now: number,players: {Player},healthy: (Player)->(boolean,BasePart?,Humanoid?)): {any}
    local dt=math.clamp(now-self.lastTick,0,.65)
    self.lastTick=now
    local impacts={}
    for _,m in ipairs(self.mobs) do
        if m.hp<=0 then
            if now>=m.deadUntil then
                m.hp=m.maxHp
                m.pos=m.home
                m.attackAt=now+1.5 -- fair re-entry; no instant hit on respawn
                m.tellUntil=0
                m.target=nil
                m.flashUntil=0
                m.body.Color=if m.elite then Color3.fromRGB(120,75,175) else Color3.fromRGB(68,151,107)
                m.model:PivotTo(CFrame.new(m.home))
                m.cue.Text=if m.elite then "⚠ 精鋭" else "中立兵"
            end
        else
            local nearest=nil
            local nearestDist=26
            for _,p in ipairs(players) do
                local ok,root=healthy(p)
                if ok and root then
                    local _,dist=horizontal(m.pos,root.Position)
                    if Combat.canAcquire(dist,root.Position.Y-m.pos.Y)
                        and dist<nearestDist then
                        nearestDist=dist
                        nearest=p
                    end
                end
            end
            -- NPC damage must respect height and solid walls; visual mobs cannot
            -- hit someone on another level or behind a fortress wall.
            local function canStrike(target: Player,elite: boolean): boolean
                local ok,root=healthy(target)
                if not ok or not root then return false end
                local _,dist=horizontal(m.pos,root.Position)
                local params=RaycastParams.new()
                params.FilterType=Enum.RaycastFilterType.Exclude
                params.FilterDescendantsInstances={self.folder}
                local obstruction=workspace:Raycast(m.pos,root.Position-m.pos,params)
                local visible=obstruction==nil
                    or (target.Character~=nil and obstruction.Instance:IsDescendantOf(target.Character))
                return Combat.canMobStrike(dist,root.Position.Y-m.pos.Y,visible,elite)
            end
            if m.elite and m.tellUntil>0 and now>=m.tellUntil then
                local target=m.target
                local ok: boolean=false
                local root: BasePart?=nil
                if target then ok,root=healthy(target) end
                if ok and root and target and canStrike(target,true) then
                    table.insert(impacts,{player=target,damage=11,kind="ELITE"})
                end
                m.tellUntil=0
                m.target=nil
                m.attackAt=now+4
                m.cue.Text="精鋭：回避できた？"
            elseif m.elite and nearest and now>=m.attackAt and m.tellUntil==0 and nearestDist<12 then
                m.tellUntil=now+1.5
                m.target=nearest
                m.cue.Text="⚠ 1.5秒後に強撃！"
                m.body.Color=Color3.fromRGB(238,83,75)
            elseif not m.elite and nearest and now>=m.attackAt
                and canStrike(nearest,false) then
                table.insert(impacts,{player=nearest,damage=3,kind="MINION"})
                m.attackAt=now+2.5
            end
            if now>=m.flashUntil and m.tellUntil==0 then
                m.body.Color=if m.elite then Color3.fromRGB(120,75,175) else Color3.fromRGB(68,151,107)
            end
            if nearest and nearestDist>4.5 and m.tellUntil==0 then
                local ok,root=healthy(nearest)
                if ok and root then
                    local unit=horizontal(m.pos,root.Position)
                    local nextPos=m.pos+unit*math.min(nearestDist-4.5,dt*(if m.elite then 2.8 else 3.4))
                    if (nextPos-m.home).Magnitude<22 then
                        -- Never cross a solid wall for chase. Do not pathfind hundreds of units.
                        local params=RaycastParams.new()
                        params.FilterType=Enum.RaycastFilterType.Exclude
                        params.FilterDescendantsInstances={self.folder}
                        local obstacle=workspace:Raycast(m.pos, nextPos-m.pos,params)
                        if not obstacle then
                            m.pos=nextPos
                            m.model:PivotTo(CFrame.lookAt(nextPos,nextPos+unit))
                        end
                    end
                end
            end
        end
    end
    return impacts
end
Horde.MAX_ACTIVE=MAX_ACTIVE
Horde.MINIONS=MINIONS
return Horde
