--!strict
-- Source-created moving neutral "creature" models, not D18 canonical characters.
-- Their parts are noncolliding and damage-free; one per server encounter.
local Policy = require(script.Parent.RareEncounterPolicy)
local M = {}
local function col(r:number,g:number,b:number): Color3
    return Color3.fromRGB(r,g,b)
end
local styles = {
    SPACE={body=col(114,170,251),accent=col(220,180,255),eye=col(255,255,255)},
    CELESTIAL={body=col(241,245,255),accent=col(252,197,124),eye=col(78,108,189)},
    EMBER={body=col(242,114,61),accent=col(255,209,112),eye=col(44,38,67)},
    ECLIPSE={body=col(113,111,220),accent=col(254,214,98),eye=col(255,255,255)},
}
function M.create(id:string, parent:Instance)
    assert(Policy.CREATURES[id]~=nil,"UNKNOWN_NEUTRAL_REALM")
    assert(parent~=nil and parent:IsA("Instance"),"NEUTRAL_REQUIRES_OWN_FOLDER")
    local style=styles[id]
    local model=Instance.new("Model")
    model.Name="RARE_NEUTRAL_"..id
    model:SetAttribute("NonCanonicalD18",true)
    model:SetAttribute("NoDropsNoCurrencyNoDamage",true)
    model:SetAttribute("MonsterAIStatus","NONCOMBAT_MOVING_VISUAL")
    model.Parent=parent

    local pieces=0
    local function part(name:string,size:Vector3,position:Vector3,
        tint:Color3,ball:boolean):Part
        pieces+=1
        assert(pieces<=12,"RARE_NEUTRAL_PART_BUDGET")
        local p=Instance.new("Part")
        p.Name=name
        p.Size=size
        p.Position=position
        p.Color=tint
        p.Anchored=true
        p.CanCollide=false
        p.CanQuery=false
        p.CanTouch=false
        p.CastShadow=false
        p.Material=Enum.Material.SmoothPlastic
        if ball then p.Shape=Enum.PartType.Ball end
        p.Parent=model
        return p
    end
    local body
    if id=="SPACE" then
        body=part("STAR_WHALE_BODY",Vector3.new(19,8,10),
            Vector3.new(0,0,0),style.body,true)
        part("TAIL",Vector3.new(7,6,8),Vector3.new(-12,1,0),style.accent,true)
        part("FIN_LEFT",Vector3.new(8,2,8),Vector3.new(0,2,-7),style.accent,true)
        part("FIN_RIGHT",Vector3.new(8,2,8),Vector3.new(0,2,7),style.accent,true)
        part("HEAD_GLOW",Vector3.new(6,5,7),Vector3.new(9,1,0),style.accent,true)
    elseif id=="CELESTIAL" then
        body=part("PEGASUS_BODY",Vector3.new(13,6,7),
            Vector3.new(0,0,0),style.body,true)
        part("GOLDEN_MANED_HEAD",Vector3.new(6,6,5),
            Vector3.new(9,3,0),style.accent,true)
        part("WING_1",Vector3.new(10,3,11),Vector3.new(-2,5,-7),style.accent,true)
        part("WING_2",Vector3.new(10,3,11),Vector3.new(-2,5,7),style.accent,true)
        for i,z in ipairs({-2,2}) do
            part("LEG_"..i,Vector3.new(2,7,2),Vector3.new(3,-5,z),
                style.body,false)
        end
    elseif id=="EMBER" then
        body=part("MOLE_BODY",Vector3.new(12,8,10),
            Vector3.new(0,0,0),style.body,true)
        part("NOSE",Vector3.new(4,3,4),Vector3.new(7,2,0),style.accent,true)
        part("PAW_LEFT",Vector3.new(5,2,3),Vector3.new(4,-3,-6),style.accent,true)
        part("PAW_RIGHT",Vector3.new(5,2,3),Vector3.new(4,-3,6),style.accent,true)
        part("BACK_SPIKE",Vector3.new(3,5,3),Vector3.new(-3,6,0),style.accent,true)
    else
        body=part("TWILIGHT_BODY",Vector3.new(12,11,9),
            Vector3.new(0,0,0),style.body,true)
        part("SUN_FACE",Vector3.new(6,8,6),Vector3.new(5,4,-4),style.accent,true)
        part("MOON_FACE",Vector3.new(6,8,6),Vector3.new(5,4,4),style.body,true)
        part("SUN_WING",Vector3.new(8,3,8),Vector3.new(-4,2,-7),style.accent,true)
        part("MOON_WING",Vector3.new(8,3,8),Vector3.new(-4,2,7),style.body,true)
    end
    part("FRIENDLY_EYE_LEFT",Vector3.new(2,2,2),
        Vector3.new(7,3,-3),style.eye,true)
    part("FRIENDLY_EYE_RIGHT",Vector3.new(2,2,2),
        Vector3.new(7,3,3),style.eye,true)
    model.PrimaryPart=body
    local gui=Instance.new("BillboardGui")
    gui.Name="VisibleRareDiscoveryCue"
    gui.Size=UDim2.fromOffset(245,70)
    gui.StudsOffsetWorldSpace=Vector3.new(0,10,0)
    gui.MaxDistance=120
    gui.AlwaysOnTop=true
    gui.Parent=body
    local label=Instance.new("TextLabel")
    label.Name="FriendlyRareName"
    label.Size=UDim2.fromScale(1,1)
    label.Font=Enum.Font.GothamBold
    label.TextScaled=true
    label.TextColor3=col(255,255,255)
    label.BackgroundColor3=col(43,49,93)
    label.BackgroundTransparency=0.12
    label.Text=Policy.CREATURES[id].cue.."\n"..Policy.CREATURES[id].name
    label.Parent=gui

    local prompt=Instance.new("ProximityPrompt")
    prompt.Name="RareDiscoveryPrompt"
    prompt.ObjectText=Policy.CREATURES[id].name
    prompt.ActionText="みつけた！"
    prompt.HoldDuration=0.4
    prompt.MaxActivationDistance=12
    prompt.RequiresLineOfSight=false
    prompt.Parent=body
    model:SetAttribute("ActualModelParts",pieces)
    return {model=model,prompt=prompt,body=body,id=id,originalParts=pieces}
end
function M.update(encounter,base:Vector3,elapsed:number)
    assert(encounter and encounter.model and encounter.model.Parent,
        "NO_ACTIVE_NEUTRAL_MODEL")
    local path=Policy.motion(encounter.id,elapsed)
    local destination=base+Vector3.new(path.x,path.y,path.z)
    encounter.model:PivotTo(CFrame.new(destination))
    encounter.model:SetAttribute("CreatureMood",path.description)
    encounter.model:SetAttribute("VisualHideAlpha",path.alpha)
    for _,item in ipairs(encounter.model:GetChildren()) do
        if item:IsA("BasePart") then item.Transparency=path.alpha end
    end
    return path
end
return M
