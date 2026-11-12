--!strict
-- Original standalone low-poly 3D scene: cosmic, celestial, ember, eclipse.
-- Does not place real NPCs, loot, character powers or physics tricks.
local Catalog = require(script.Parent.RareRealmCatalog)
local Scene = {}

local function rgb(r:number,g:number,b:number): Color3
    return Color3.fromRGB(r,g,b)
end

function Scene.build(world: Workspace)
    assert(world and world:IsA("Workspace"), "REALM_REQUIRES_WORKSPACE")
    assert(world:FindFirstChild("TRAP_RAIDERS_S1")==nil,"REALM_NEVER_OVERLAP_OFFICIAL_S1")
    assert(world:FindFirstChild("P0D_FourRareRealms")==nil,"REALM_DUPLICATE_DENIED")
    local valid,reason=Catalog.validate()
    assert(valid,reason)

    local folder=Instance.new("Folder")
    folder.Name="P0D_FourRareRealms"
    folder.Parent=world
    folder:SetAttribute("WorldScope","S2_PLUS_ISOLATED_PREVIEW")
    folder:SetAttribute("RareNPCSpawnStatus","NO_AI_OR_DROP_ONLY_SCULPTURE")
    folder:SetAttribute("RealStudioQA","NOT_TESTED")

    local count=0
    local physicalCount=0
    local function p(name:string,size:Vector3,position:Vector3,
        color:Color3,solid:boolean,material:Enum.Material?,opacity:number?):Part
        count+=1
        assert(count<=Catalog.MAX_SCENE_PARTS,"REALM_PART_BUDGET_EXCEEDED")
        local item=Instance.new("Part")
        item.Name=name
        item.Size=size
        item.Position=position
        item.Anchored=true
        item.CanCollide=solid
        item.CanTouch=false
        item.CanQuery=solid
        item.Color=color
        item.Material=material or Enum.Material.SmoothPlastic
        item.Transparency=opacity or 0
        item.Parent=folder
        if solid then physicalCount+=1 end
        return item
    end
    local function ball(name:string,size:Vector3,position:Vector3,color:Color3,alpha:number?)
        local item=p(name,size,position,color,false,Enum.Material.Neon,alpha)
        item.Shape=Enum.PartType.Ball
        item.CastShadow=false
        return item
    end
    local function road(name:string, start:Vector3, finish:Vector3,
        width:number,color:Color3):Part
        local delta=finish-start
        local length=delta.Magnitude
        assert(length>=60 and length<=200,"REALM_ROUTE_LENGTH_OUT_OF_RANGE")
        assert(math.abs(delta.Y)/math.sqrt(delta.X*delta.X+delta.Z*delta.Z)<0.25,
            "REALM_ROUTE_TOO_STEEP")
        local mid=(start+finish)*0.5
        local item=p(name,Vector3.new(width,2,length),mid,color,true)
        item.CFrame=CFrame.lookAt(mid,finish)
        item:SetAttribute("FreeToAllJobs",true)
        item:SetAttribute("BackAndForth",true)
        return item
    end
    local function sign(name:string,at:Vector3,label:string,color:Color3)
        local stem=p(name,Vector3.new(1,6,1),at,color,false,Enum.Material.Neon)
        local gui=Instance.new("BillboardGui")
        gui.Name="RareWorldChildGuide"
        gui.Size=UDim2.fromOffset(225,66)
        gui.StudsOffsetWorldSpace=Vector3.new(0,6,0)
        gui.MaxDistance=140
        gui.AlwaysOnTop=true
        gui.Parent=stem
        local text=Instance.new("TextLabel")
        text.Name="ChildReadableLabel"
        text.Size=UDim2.fromScale(1,1)
        text.Text=label
        text.TextScaled=true
        text.Font=Enum.Font.GothamBold
        text.TextColor3=rgb(255,255,255)
        text.BackgroundColor3=rgb(28,36,82)
        text.BackgroundTransparency=0.1
        text.Parent=gui
    end
    local function castle(id:string,base:Vector3,main:Color3)
        p(id.."_CASTLE_DECK",Vector3.new(47,2,38),
            base+Vector3.new(0,2,4),main,true)
        for n,dx in ipairs({-18,18}) do
            p(id.."_TOWER_"..n,Vector3.new(7,21,7),
                base+Vector3.new(dx,13,-9),rgb(227,233,254),true)
            p(id.."_TOWER_CROWN_"..n,Vector3.new(10,3,10),
                base+Vector3.new(dx,25,-9),main,false,Enum.Material.Neon)
        end
        ball(id.."_CASTLE_BEACON",Vector3.new(8,8,8),
            base+Vector3.new(0,22,10),main,0.2)
    end
    -- These are STATIC sculptural silhouettes. Never claim real rare neutral NPC spawn.
    local function sculpture(id:string,base:Vector3,primary:Color3,accent:Color3)
        local at=base+Vector3.new(4,20,26)
        ball(id.."_RARE_SCULPTURE_BODY",Vector3.new(22,11,12),at,primary,0.08)
        ball(id.."_RARE_SCULPTURE_HEAD",Vector3.new(10,10,10),
            at+Vector3.new(13,3,0),accent)
        ball(id.."_RARE_SCULPTURE_EYE_1",Vector3.new(2,2,2),
            at+Vector3.new(17,5,4),rgb(255,255,255))
        ball(id.."_RARE_SCULPTURE_EYE_2",Vector3.new(2,2,2),
            at+Vector3.new(17,5,-4),rgb(255,255,255))
        for i,side in ipairs({-1,1}) do
            ball(id.."_RARE_SCULPTURE_WING_"..i,
                Vector3.new(15,4,10),at+Vector3.new(-1,6,side*11),accent,0.2)
        end
        sign(id.."_RARE_ONLY_SCULPTURE_NOTE",base+Vector3.new(4,5,25),
            "★ めずらしい ぞう\nいきもの は これから",accent)
    end

    local center=rgb(81,186,126)
    p("FREE_4WORLD_HUB",Vector3.new(110,2,110),Vector3.new(0,0,0),
        center,true,Enum.Material.Grass)
    local spawn=Instance.new("SpawnLocation")
    spawn.Name="FourRealmsFreeSpawn"
    spawn.Neutral=true
    spawn.Enabled=true
    spawn.Size=Vector3.new(12,1,12)
    spawn.Position=Vector3.new(0,2,0)
    spawn.Anchored=true
    spawn.Parent=folder
    sign("HUB_CHILD_GUIDE",Vector3.new(0,5,13),
        "← ほし  ☆  まかい\n↑ そら   ↓ たいようとつき",rgb(245,227,145))

    local islands={}
    local roads={}
    local sunMoonPanels={}
    for _,id in ipairs(Catalog.ORDER) do
        local data=Catalog.WORLDS[id]
        local base=Vector3.new(data.center.x,data.center.y,data.center.z)
        local color=rgb(data.color.r,data.color.g,data.color.b)
        local platform=p(id.."_FREE_REALM_ISLAND",Vector3.new(112,2,112),
            base,color,true,Enum.Material.SmoothPlastic)
        platform:SetAttribute("NeverPaidAccess",true)
        islands[id]=platform
        local x,z=data.center.x,data.center.z
        local u,v
        if id=="SPACE" then
            u=road(data.forward,Vector3.new(50,2,-22),Vector3.new(x-54,2,-22),17,color)
            v=road(data.side,Vector3.new(50,2,22),Vector3.new(x-54,2,22),17,
                rgb(84,194,232))
        elseif id=="EMBER" then
            u=road(data.forward,Vector3.new(-50,2,-22),Vector3.new(x+54,2,-22),17,color)
            v=road(data.side,Vector3.new(-50,2,22),Vector3.new(x+54,2,22),17,
                rgb(139,143,156))
        elseif id=="CELESTIAL" then
            u=road(data.forward,Vector3.new(-22,2,50),Vector3.new(-22,data.center.y+2,z-54),17,color)
            v=road(data.side,Vector3.new(22,2,50),Vector3.new(22,data.center.y+2,z-54),17,
                rgb(223,244,253))
        else
            u=road(data.forward,Vector3.new(-22,2,-50),Vector3.new(-22,2,z+54),17,
                rgb(248,210,101))
            v=road(data.side,Vector3.new(22,2,-50),Vector3.new(22,2,z+54),17,
                rgb(103,117,252))
        end
        roads[id]={u,v}
        castle(id,base,color)
        sign(id.."_WORLD_NAME",base+Vector3.new(-3,6,-46),data.label,color)
        sign(id.."_TACTIC_GUIDE",base+Vector3.new(33,6,21),
            "★ ふたつの みち\nどちらでも いける",color)
        sculpture(id,base,color,rgb(247,226,156))

        for i=1,9 do
            local theta=(i/9)*math.pi*2
            local radius=32+(i%3)*10
            local y=base.Y+10+(i%4)*8
            local bx=base.X+math.cos(theta)*radius
            local bz=base.Z+math.sin(theta)*radius
            if id=="SPACE" then
                ball(id.."_COSMIC_STAR_"..i,
                    Vector3.new(3+i%3,3+i%3,3+i%3),Vector3.new(bx,y,bz),
                    (i%2==0) and rgb(94,225,247) or rgb(242,171,252))
            elseif id=="CELESTIAL" then
                ball(id.."_FLOATING_CLOUD_"..i,
                    Vector3.new(19+i%3,5,10),Vector3.new(bx,y+9,bz),
                    rgb(245,250,255),0.24)
            elseif id=="EMBER" then
                local ember=p(id.."_LAVA_CRYSTAL_"..i,
                    Vector3.new(6,13+i%4*3,6),Vector3.new(bx,base.Y+8,bz),
                    rgb(255,122,48),false,Enum.Material.Neon,0.18)
                ember:SetAttribute("DecorativeSafeNoDamage",true)
            else
                ball(id.."_ECLIPSE_SPARK_"..i,
                    Vector3.new(6,6,6),Vector3.new(bx,y,bz),
                    (i%2==0) and rgb(250,220,126) or rgb(108,123,250),0.2)
            end
        end
        if id=="SPACE" then
            local dome=ball("SPACE_WF13_FUTURE_ZERO_G_VISUAL_ONLY",
                Vector3.new(29,29,29),base+Vector3.new(-30,20,30),
                rgb(112,96,247),0.79)
            dome:SetAttribute("ActualGravityForce","NOT_INSTALLED_REQUIRE_WF13_SEPARATE_QA")
        elseif id=="CELESTIAL" then
            ball("CELESTIAL_PRISM_CLOUD_BELL_VISUAL",
                Vector3.new(13,16,13),base+Vector3.new(0,31,-24),rgb(255,245,159),0.22)
        elseif id=="EMBER" then
            ball("EMBER_GEAR_RELIC_DECORATIVE",
                Vector3.new(20,20,20),base+Vector3.new(-30,20,30),
                rgb(255,173,80),0.18)
        elseif id=="ECLIPSE" then
            local s=ball("ECLIPSE_SUN_DECORATIVE",Vector3.new(22,22,22),
                base+Vector3.new(-26,27,24),rgb(255,210,85))
            local m=ball("ECLIPSE_MOON_DECORATIVE",Vector3.new(22,22,22),
                base+Vector3.new(26,27,24),rgb(98,133,246))
            sunMoonPanels={s,m}
            s:SetAttribute("ColorCycleAffectsCollision",false)
            m:SetAttribute("ColorCycleAffectsCollision",false)
        end
    end
    folder:SetAttribute("SourcePartBudget",Catalog.MAX_SCENE_PARTS)
    folder:SetAttribute("ActualPartCount",count)
    folder:SetAttribute("SourcePhysicalPartCount",physicalCount)
    return {folder=folder,spawn=spawn,islands=islands,roads=roads,
        eclipsePanels=sunMoonPanels,totalParts=count,solidParts=physicalCount}
end
return Scene
