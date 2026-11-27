-- Use the built Private layout and policy with representative standard control geometry.
local vectorMT={}
local Vector2={new=function(x,y) return setmetatable({X=x,Y=y},vectorMT) end}
function vectorMT.__eq(a,b) return a.X==b.X and a.Y==b.Y end
function vectorMT.__add(a,b) return Vector2.new(a.X+b.X,a.Y+b.Y) end
function vectorMT.__sub(a,b) return Vector2.new(a.X-b.X,a.Y-b.Y) end
local UDim2={fromOffset=Vector2.new}
local view=(function()
__POLICY__
end)()
local UserInputService={TouchEnabled=true}
local workspace={CurrentCamera={ViewportSize=Vector2.new(677,338)}}
local gui={AbsolutePosition=Vector2.new(17,29),AbsoluteSize=Vector2.new(677,280)}
local leftHanded=false
local player={GetAttribute=function() return leftHanded end}
local jump={Visible=true,AbsoluteSize=Vector2.new(70,70)}
local touch={Enabled=true}
local controls={Visible=true}
function jump:IsA(k) return k=="GuiButton" end
function touch:IsA(k) return k=="ScreenGui" end
function controls:IsA(k) return k=="GuiObject" end
function touch:FindFirstChild(n) if n=="TouchControlFrame" then return controls end end
function controls:FindFirstChild(n) if n=="JumpButton" then return jump end end
local playerGui={FindFirstChild=function(_,n) if n=="TouchGui" then return touch end end}
local actions={ATTACK={},DODGE={},MUSOU={},INVUL={},ITEM={},SKILL={},JUMP={}}
local skillUse,mapBox,statusBox,progress,growthFooter,drawer={},{},{},{},{},{}
local mapExpanded=false
local redraws=0
local function redraw() redraws+=1 end
__HUD_LAYOUT__

local function verifySeparation(jumpCenter,baseline)
    local pos=actions.ATTACK.Position
    local half=actions.ATTACK.Size.X/2
    local at=jump.AbsolutePosition-gui.AbsolutePosition
    assert(pos.X~=baseline.x or pos.Y~=baseline.y)
    assert(pos.X-half>=0 and pos.Y-half>=0)
    assert(pos.X+half<=gui.AbsoluteSize.X and pos.Y+half<=gui.AbsoluteSize.Y)
    assert(pos.X+half+5<=at.X or pos.X-half-5>=at.X+jump.AbsoluteSize.X
        or pos.Y+half+5<=at.Y or pos.Y-half-5>=at.Y+jump.AbsoluteSize.Y)
end
local function scene(w,h,safeH,hand)
    workspace.CurrentCamera.ViewportSize=Vector2.new(w,h)
    gui.AbsoluteSize=Vector2.new(w,safeH)
    leftHanded=hand=="LEFT"
    local original=view.layout(w,h,hand).anchors
    local baseline=original.ATTACK
    local center=Vector2.new(baseline.x,baseline.y)
    jump.AbsolutePosition=gui.AbsolutePosition+center-Vector2.new(35,35)
    updateLayout()
    verifySeparation(center,baseline)
    assert(actions.DODGE.Position.X==original.DODGE.x and actions.DODGE.Position.Y==original.DODGE.y)
    local old=redraws
    updateLayout()
    assert(redraws==old)
    jump.AbsolutePosition=gui.AbsolutePosition+Vector2.new(0,0)
    jump.Visible=false
    updateLayout()
    assert(actions.ATTACK.Position.X==baseline.x and actions.ATTACK.Position.Y==baseline.y)
    jump.Visible=true
end
scene(677,338,280,"RIGHT")
scene(359,632,574,"RIGHT")
scene(677,338,280,"LEFT")
UserInputService.TouchEnabled=false
updateLayout()
local desk=view.layout(677,338,"LEFT").anchors
assert(actions.ATTACK.Position.X==desk.ATTACK.x and actions.ATTACK.Position.Y==desk.ATTACK.y)
print("PRIVATE_NATIVE_EXISTING_POLICY_TOUCH_JUMP_CACHE_SAFE_INSET_PASS")
