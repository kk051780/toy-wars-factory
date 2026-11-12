--!strict
-- Real source-built guide beacons for the OWNER's private two-client Studio QA.
-- One CURRENT visible waypoint out of four; noncolliding and never reward-bearing.
-- This does NOT change production rare spawn odds or any real-world castle routes.
local Plan = require(script.Parent.RareDiscoveryQAPlan)
local Policy = require(script.Parent.RareEncounterPolicy)
local Guides = {}
Guides.VERSION="P0D_RARE_HUB_ACTIVE_WAYFINDING_V1"
Guides.MARKERS = {
    SPACE={title="★ ほしくじら",color=Color3.fromRGB(142,193,251)},
    CELESTIAL={title="★ にじのペガサス",color=Color3.fromRGB(250,222,150)},
    EMBER={title="★ マグマモグラ",color=Color3.fromRGB(246,150,100)},
    ECLIPSE={title="★ ふたつのかおのげんじゅう",color=Color3.fromRGB(185,160,251)},
}
function Guides.validate(): (boolean,string)
    if #Plan.ORDER~=4 then return false,"wrong four slot schedule" end
    local used={}
    for _,id in ipairs(Plan.ORDER) do
        local p=Plan.BASES[id]
        local d=Guides.MARKERS[id]
        if not p or not d or used[id] or
            math.abs(p.x)>40 or math.abs(p.z)>40 or
            #d.title<6 or not Policy.CREATURES[id] then
            return false,"unsafe free hub waypoint"
        end
        used[id]=true
    end
    return true,"four safe FREE_TEST_HUB original sign locations"
end
function Guides.mount(sceneFolder:Instance)
    assert(sceneFolder and sceneFolder:IsA("Folder"),"GUIDES_REQUIRE_OWNED_SCENE")
    local valid,reason=Guides.validate()
    assert(valid,reason)
    assert(sceneFolder:FindFirstChild("P0D_RARE_QA_CURRENT_GUIDES")==nil,
        "GUIDES_CANNOT_DUPLICATE")
    local folder=Instance.new("Folder")
    folder.Name="P0D_RARE_QA_CURRENT_GUIDES"
    folder.Parent=sceneFolder
    folder:SetAttribute("S2OwnerTestOnly",true)
    folder:SetAttribute("RewardsOrCoins","NONE")
    folder:SetAttribute("ModifiesWorldPhysics",false)
    local markers={}
    for _,id in ipairs(Plan.ORDER) do
        local base=Plan.point(id)
        assert(base,"UNKNOWN_QA_WORLD_ID")
        local marker=Instance.new("Part")
        marker.Name="GUIDE_"..id
        marker.Size=Vector3.new(2,2,2)
        marker.Position=Vector3.new(base.X,5,base.Z)
        marker.Anchored=true
        marker.Transparency=1
        marker.CanCollide=false
        marker.CanTouch=false
        marker.CanQuery=false
        marker.CastShadow=false
        marker.Parent=folder
        local gui=Instance.new("BillboardGui")
        gui.Name="CurrentCreatureOnly"
        gui.Size=UDim2.fromOffset(280,96)
        gui.StudsOffsetWorldSpace=Vector3.new(0,7,0)
        gui.MaxDistance=140
        gui.AlwaysOnTop=true
        gui.Enabled=false
        gui.Parent=marker
        local label=Instance.new("TextLabel")
        label.Name="ChildCurrentRealmGuide"
        label.Size=UDim2.fromScale(1,1)
        label.Text="いまは ここ！\n"..Guides.MARKERS[id].title
        label.TextScaled=true
        label.TextWrapped=true
        label.Font=Enum.Font.GothamBold
        label.TextColor3=Color3.fromRGB(255,255,255)
        label.BackgroundColor3=Guides.MARKERS[id].color
        label.BackgroundTransparency=0.15
        label.Parent=gui
        markers[id]={marker=marker,gui=gui,label=label}
    end
    local state={folder=folder,markers=markers,lastId=nil}
    function state:show(currentId:string)
        local found=markers[currentId]~=nil
        for _,id in ipairs(Plan.ORDER) do
            markers[id].gui.Enabled=found and id==currentId
        end
        self.lastId=found and currentId or nil
        return found
    end
    function state:clear()
        for _,id in ipairs(Plan.ORDER) do
            markers[id].gui.Enabled=false
        end
        self.lastId=nil
    end
    function state:destroy()
        self:clear()
        if folder.Parent then folder:Destroy() end
    end
    return state
end
return Guides
