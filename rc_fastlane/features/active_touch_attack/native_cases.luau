-- Exact current layout and hit feedback, with platform rectangles in a Native input scene.
local vectorMT={}
local Vector2={new=function(x,y) return setmetatable({X=x,Y=y},vectorMT) end}
function vectorMT.__add(a,b) return Vector2.new(a.X+b.X,a.Y+b.Y) end
function vectorMT.__sub(a,b) return Vector2.new(a.X-b.X,a.Y-b.Y) end
local Rect={}
function Rect.new(a,b) return {Min=a,Max=b} end
local UDim2={fromOffset=function(x,y) return {X=x,Y=y} end}
local Color3={fromRGB=function(...) return {...} end}
local registered={}
local function signal(label)
    return {Connect=function(_,callback) registered[label]=callback end}
end
local function frame(kind,x,y,width,height)
    local f={kind=kind,Visible=true,Enabled=true,AbsolutePosition=Vector2.new(x,y),
        AbsoluteSize=Vector2.new(width,height),children={}}
    function f:IsA(class) return class==self.kind or class=="GuiObject" and self.kind~="ScreenGui" end
    function f:FindFirstChild(key) return self.children[key] end
    function f:GetPropertyChangedSignal(key) return signal(key) end
    return f
end

local gui=frame("ScreenGui",0,0,320,568)
local jump=frame("GuiButton",242,468,70,70)
local stick=frame("GuiObject",0,408,144,160)
local touchFrame=frame("GuiObject",0,0,320,568)
touchFrame.children.JumpButton=jump
touchFrame.children.DynamicThumbstickFrame=stick
local native=frame("ScreenGui",0,0,320,568)
native.children.TouchControlFrame=touchFrame
local playerGui=frame("ScreenGui",0,0,320,568)
playerGui.children.TouchGui=native
local player={FindFirstChildOfClass=function() return playerGui end}
local UserInputService={TouchEnabled=true,GetPropertyChangedSignal=function(_,key) return signal(key) end}
local timers={}
local task={
    defer=function(callback) callback() end,
    delay=function(seconds,callback)
        assert(seconds==.28)
        table.insert(timers,callback)
    end,
}
local remote={OnClientEvent=signal("attackResult")}
local lastSerial=4
local attack={Parent=gui,Visible=true,Text="⚔ 攻撃\nFキー",
    Size=UDim2.fromOffset(126,88),Position=UDim2.fromOffset(180,552),
    BackgroundColor3=Color3.fromRGB(211,75,72)}
local trapButton=frame("GuiButton",180,384,110,74)
local windButton=frame("GuiButton",55,384,110,74)
local netButton=frame("GuiButton",180,321,110,62)
local rescueButton=frame("GuiButton",55,321,115,62)
local relayButton=frame("GuiButton",10,383,112,58)
local scoutButton=frame("GuiButton",10,441,110,68)
local jobCast=frame("GuiButton",150,480,94,71)
local awakenButton=frame("GuiButton",95,309,100,60)
relayButton.Visible=false
scoutButton.Visible=false
awakenButton.Visible=false

__EXACT_ATTACK_FEEDBACK__
__EXACT_TOUCH_LAYOUT__

local function rectangleForAttack()
    local x,y=attack.Position.X,attack.Position.Y-attack.Size.Y
    return Rect.new(Vector2.new(x,y),Vector2.new(x+attack.Size.X,y+attack.Size.Y))
end
local function disjoint(a,b,gap)
    return a.Max.X+gap<=b.Min.X or b.Max.X+gap<=a.Min.X
        or a.Max.Y+gap<=b.Min.Y or b.Max.Y+gap<=a.Min.Y
end
local function rectFor(control)
    return Rect.new(control.AbsolutePosition,control.AbsolutePosition+control.AbsoluteSize)
end
local function checkVisible()
    assert(attack.Visible)
    local a=rectangleForAttack()
    assert(a.Min.X>=0 and a.Min.Y>=72 and a.Max.X<=gui.AbsoluteSize.X-8 and a.Max.Y<=gui.AbsoluteSize.Y-8)
    assert(disjoint(a,rectFor(jump),8) and disjoint(a,rectFor(jobCast),8))
    for _,button in ipairs(attackOccupied) do
        if button.Visible then assert(disjoint(a,rectFor(button),8)) end
    end
end
local desktop=rectangleForAttack()
assert(not disjoint(desktop,rectFor(jobCast),0))
attackInBattle=true
layoutTouchAttack()
checkVisible()
assert(attack.Text=="攻撃")
registered.attackResult({kind="P0D_ATTACK_RESULT",status="HIT",serial=4,seq=7})
assert(attack.Text=="⚔ 命中!")
layoutTouchAttack()
assert(attack.Text=="⚔ 命中!")
registered.attackResult({kind="P0D_ATTACK_RESULT",status="MISS",serial=4,seq=8})
assert(attack.Text=="⚔ 空振り")
registered.AbsoluteSize()
assert(attack.Text=="⚔ 空振り")
timers[1]()
assert(attack.Text=="⚔ 空振り")
timers[2]()
assert(attack.Text=="攻撃")
print("ACTIVE_TOUCH_Q_F_JUMP_AND_FEEDBACK_TIMER_PASS")

relayButton.Visible=true
windButton.Visible=false
layoutTouchAttack()
checkVisible()
relayButton.Visible=false
windButton.Visible=true
-- Landscape repositions the standard and existing controls before the snapshot.
gui.AbsoluteSize=Vector2.new(740,360)
jump.AbsolutePosition=Vector2.new(650,263)
trapButton.AbsolutePosition=Vector2.new(600,176)
windButton.AbsolutePosition=Vector2.new(475,176)
netButton.AbsolutePosition=Vector2.new(600,113)
rescueButton.AbsolutePosition=Vector2.new(475,113)
jobCast.AbsolutePosition=Vector2.new(150,272)
layoutTouchAttack()
checkVisible()
registered.attackResult({kind="P0D_ATTACK_RESULT",status="HIT",serial=4,seq=9})
UserInputService.TouchEnabled=false
registered.TouchEnabled()
assert(attack.Visible and attack.Size.X==126 and attack.Position.X==180 and attack.Text=="⚔ 命中!")
timers[3]()
assert(attack.Text=="⚔ 攻撃\nFキー")
attackInBattle=false
layoutTouchAttack()
assert(not attack.Visible)
print("ACTIVE_TOUCH_ROTATION_RELAY_DESKTOP_AND_LOBBY_PASS")
