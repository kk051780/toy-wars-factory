--!strict
-- FB020-A private 7-job tangible weapons + distinct 3-step neutral PvE M1.
-- No Remote, PlayerHP, egg, score, reward or DataStore authority.
-- Game.server is the only accept/seq/cooldown/damage/KO authority.
local R={}
local METAL=Color3.fromRGB(196,216,238)
local GOLD=Color3.fromRGB(249,195,96)
local DARK=Color3.fromRGB(44,54,76)
local JOBS={
    WARRIOR={label="大剣",rgb={248,167,66},length=4.3},
    MAGE={label="魔法杖",rgb={96,166,255},length=4.6},
    NINJA={label="双短剣",rgb={165,113,244},length=2.0},
    TRAPPER={label="罠弩",rgb={235,116,204},length=2.2},
    BUILDER={label="大槌",rgb={246,204,99},length=3.6},
    BEAST_TAMER={label="長槍",rgb={91,210,134},length=5.0},
    NECROMANCER={label="死霊鎌",rgb={127,213,109},length=4.4},
}
local state=setmetatable({},{__mode="k"})
local function addPart(model:Model,name:string,grip:BasePart,size:Vector3,
    offset:CFrame,color:Color3,shape:Enum.PartType?,neon:boolean?)
    local p=Instance.new("Part")
    p.Name=name
    p.Size=size
    p.Material=if neon then Enum.Material.Neon else Enum.Material.Metal
    p.Color=color
    p.Shape=shape or Enum.PartType.Block
    p.CanCollide=false
    p.CanTouch=false
    p.CanQuery=false
    p.Massless=true
    p.CastShadow=false
    p.Anchored=false
    p.CFrame=grip.CFrame*offset
    p.Parent=model
    local link=Instance.new("WeldConstraint")
    link.Part0=grip
    link.Part1=p
    link.Parent=p
    return p
end
local function createWeapon(character:Model,hand:BasePart,job:string,suffix:string)
    local info=JOBS[job]
    local theme=Color3.fromRGB(info.rgb[1],info.rgb[2],info.rgb[3])
    local model=Instance.new("Model")
    model.Name="P0D_JOB_HELD_WEAPON_"..suffix
    local grip=Instance.new("Part")
    grip.Name="WeaponGrip"
    grip.Size=Vector3.new(.35,1.25,.35)
    grip.Material=Enum.Material.Metal
    grip.Color=DARK
    grip.CanCollide=false;grip.CanTouch=false;grip.CanQuery=false
    grip.Massless=true;grip.Anchored=false
    grip.CFrame=hand.CFrame*CFrame.new(0,-.85,-.3)
    grip.Parent=model
    local weld=Instance.new("WeldConstraint")
    weld.Part0=hand;weld.Part1=grip;weld.Parent=grip
    if job=="WARRIOR" then
        addPart(model,"GreatswordBlade",grip,Vector3.new(.72,info.length,.24),CFrame.new(0,2.65,0),METAL,nil,false)
        addPart(model,"Sunedge",grip,Vector3.new(.16,3.7,.34),CFrame.new(0,2.65,0),theme,nil,true)
        addPart(model,"Crossguard",grip,Vector3.new(2.0,.3,.45),CFrame.new(0,.65,0),GOLD,nil,false)
    elseif job=="MAGE" then
        addPart(model,"RuneStaff",grip,Vector3.new(.34,info.length,.34),CFrame.new(0,2.25,0),theme,Enum.PartType.Cylinder,false)
        addPart(model,"SpellOrb",grip,Vector3.new(1.25,1.25,1.25),CFrame.new(0,4.75,0),theme,Enum.PartType.Ball,true)
        addPart(model,"ManaRing",grip,Vector3.new(1.4,.16,1.4),CFrame.new(0,4.05,0),GOLD,Enum.PartType.Cylinder,false)
    elseif job=="NINJA" then
        addPart(model,"ShadowBlade",grip,Vector3.new(.34,2.0,.18),CFrame.new(0,1.55,0),METAL,nil,false)
        addPart(model,"ShadowEdge",grip,Vector3.new(.11,1.85,.25),CFrame.new(.19,1.55,0),theme,nil,true)
        addPart(model,"DaggerGuard",grip,Vector3.new(.8,.17,.4),CFrame.new(0,.63,0),DARK,nil,false)
    elseif job=="TRAPPER" then
        addPart(model,"TrapLauncher",grip,Vector3.new(.6,2.15,.75),CFrame.new(0,1.55,0),DARK,nil,false)
        addPart(model,"CrossbowLimbs",grip,Vector3.new(2.4,.27,.4),CFrame.new(0,2.4,0),METAL,nil,false)
        addPart(model,"LoadedBolt",grip,Vector3.new(.17,2.2,.19),CFrame.new(0,2.0,-.32),theme,nil,true)
    elseif job=="BUILDER" then
        addPart(model,"HammerShaft",grip,Vector3.new(.48,3.6,.48),CFrame.new(0,1.9,0),DARK,nil,false)
        addPart(model,"SiegeHammerHead",grip,Vector3.new(2.45,.95,1.05),CFrame.new(0,3.75,0),METAL,nil,false)
        addPart(model,"HammerRune",grip,Vector3.new(2.5,.16,1.1),CFrame.new(0,3.85,0),theme,nil,true)
    elseif job=="BEAST_TAMER" then
        addPart(model,"BeastSpearShaft",grip,Vector3.new(.33,4.9,.33),CFrame.new(0,2.4,0),DARK,nil,false)
        addPart(model,"SpearPoint",grip,Vector3.new(.64,1.2,.4),CFrame.new(0,5.4,0),theme,nil,true)
        addPart(model,"TamerRibbon",grip,Vector3.new(.15,1.2,.35),CFrame.new(.43,3.4,0),GOLD,nil,false)
    else
        addPart(model,"NecroScytheShaft",grip,Vector3.new(.33,4.3,.33),CFrame.new(0,2.4,0),DARK,nil,false)
        addPart(model,"BoneSickle",grip,Vector3.new(2.2,.4,.35),CFrame.new(1.0,4.5,0),METAL,nil,false)
        addPart(model,"CursedEdge",grip,Vector3.new(1.5,.23,.28),CFrame.new(1.3,4.7,0),theme,nil,true)
        addPart(model,"DeathOrb",grip,Vector3.new(.7,.7,.7),CFrame.new(0,4.0,0),theme,Enum.PartType.Ball,true)
    end
    model.Parent=character
end
function R.clear(character:Model?)
    if not character then return end
    for _,child in ipairs(character:GetChildren()) do
        if child:IsA("Model") and child.Name:sub(1,20)=="P0D_JOB_HELD_WEAPON_" then
            child:Destroy()
        end
    end
end
function R.equip(character:Model?,job:string):boolean
    if not character or not JOBS[job] then return false end
    R.clear(character)
    local right=character:FindFirstChild("RightHand") or character:FindFirstChild("Right Arm")
    if not right or not right:IsA("BasePart") then return false end
    createWeapon(character,right,job,"RIGHT")
    if job=="NINJA" then
        local left=character:FindFirstChild("LeftHand") or character:FindFirstChild("Left Arm")
        if left and left:IsA("BasePart") then
            createWeapon(character,left,job,"LEFT")
        end
    end
    return true
end
-- Each profile is a real 3-stage strike performed on distinct positions and
-- angles, not seven cosmetic labels on the same generic attack. Only Game
-- supplies the authenticated current player, root, cooldown and Horde callback.
local PATTERNS={
 WARRIOR={{{a=-22,s=1,m=.72}},{{a=22,s=1,m=.80}},{{a=-30,s=0,m=.82},{a=0,s=1,m=.95},{a=30,s=0,m=.82}}},
 MAGE={{{a=0,s=7,m=.60}},{{a=-25,s=5,m=.60},{a=25,s=5,m=.60}},{{a=-38,s=7,m=.58},{a=0,s=9,m=.65},{a=38,s=7,m=.58}}},
 NINJA={{{a=-12,s=5,m=.72}},{{a=12,s=7,m=.72}},{{a=-18,s=4,m=.71},{a=18,s=8,m=.71}}},
 TRAPPER={{{a=-30,s=5,m=.61}},{{a=30,s=5,m=.61}},{{a=-75,s=5,m=.45},{a=0,s=7,m=.52},{a=75,s=5,m=.45}}},
 BUILDER={{{a=0,s=2,m=1.13}},{{a=-15,s=3,m=.95}},{{a=-28,s=3,m=.8},{a=28,s=3,m=.8}}},
 BEAST_TAMER={{{a=0,s=8,m=.78}},{{a=-9,s=8,m=.74},{a=9,s=8,m=.74}},{{a=0,s=10,m=.84},{a=28,s=4,m=.58}}},
 NECROMANCER={{{a=-42,s=1,m=.61}},{{a=42,s=1,m=.61}},{{a=-45,s=1,m=.55},{a=0,s=4,m=.62},{a=45,s=1,m=.55}}},
}
local Debris=game:GetService("Debris")
local function unitFacing(direction:Vector3):Vector3
    local d=Vector3.new(direction.X,0,direction.Z)
    return if d.Magnitude>.01 then d.Unit else Vector3.new(1,0,0)
end
function R.comboStage(player:Player,job:string,now:number):number
    if not JOBS[job] then return 0 end
    local prior=state[player]
    local nextStage=if prior and prior.job==job and now-prior.time>=0
        and now-prior.time<=2.4 then prior.stage%3+1 else 1
    state[player]={job=job,stage=nextStage,time=now}
    return nextStage
end
function R.resetPlayer(player:Player)
    state[player]=nil
end
function R.strike(job:string,stage:number,origin:Vector3,look:Vector3,
    baseDamage:number,hitCallback:(Vector3,Vector3,number)->(number,number)):(number,number)
    local stages=PATTERNS[job]
    if not stages or stage<1 or stage>3 or stage%1~=0 then return 0,0 end
    local facing=unitFacing(look)
    local touched,kos=0,0
    for _,shot in ipairs(stages[stage]) do
        local r=math.rad(shot.a)
        local dir=Vector3.new(facing.X*math.cos(r)-facing.Z*math.sin(r),0,
            facing.X*math.sin(r)+facing.Z*math.cos(r))
        -- Distinct visible short attack arc at the SAME server-owned hit direction.
        -- No hitboxes or damage authority; real Horde:hit is still called below.
        local arc=Instance.new("Part")
        arc.Name="P0D_M1_HIT_ARC_"..job
        arc.Size=Vector3.new(if job=="WARRIOR" then 6 elseif job=="NINJA" then 2.5 else 4,
            .18, if job=="BEAST_TAMER" then 5 else 2.3)
        arc.Anchored=true;arc.CanCollide=false;arc.CanTouch=false;arc.CanQuery=false
        arc.CastShadow=false
        arc.Material=Enum.Material.Neon
        local color=JOBS[job].rgb
        arc.Color=Color3.fromRGB(color[1],color[2],color[3])
        arc.Transparency=.38
        local impact=origin+dir*(shot.s+2)
        arc.CFrame=CFrame.lookAt(impact,impact+dir)
        arc.Parent=workspace
        Debris:AddItem(arc,.20)
        local h,k=hitCallback(origin+dir*shot.s,dir,math.clamp(baseDamage*shot.m,1,40))
        touched+=h
        kos+=k
    end
    return touched,kos
end
return R
