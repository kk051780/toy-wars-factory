
local function rectangleForAuxiliary()
    local x,y=chainCast.Position.X,chainCast.Position.Y-chainCast.Size.Y
    return Rect.new(Vector2.new(x,y),Vector2.new(x+chainCast.Size.X,y+chainCast.Size.Y))
end

local function checkBoth()
    chainInBattle=false
    layoutTouchAttack()
    checkVisible()
    local withoutAbility=rectangleForAttack()
    chainInBattle=true
    layoutTouchAttack()
    checkVisible()
    local withAbility=rectangleForAttack()
    assert(withoutAbility.Min.X==withAbility.Min.X and withoutAbility.Min.Y==withAbility.Min.Y)
    assert(chainCast.Visible,"CHAIN_TOUCH_SLOT_MISSING")
    local c=rectangleForAuxiliary()
    assert(c.Min.Y>=72 and c.Max.X<=gui.AbsoluteSize.X-8 and c.Max.Y<=gui.AbsoluteSize.Y-8)
    assert(disjoint(c,rectFor(jump),8) and disjoint(c,rectFor(stick),8) and disjoint(c,withAbility,8))
    for _,button in ipairs(attackOccupied) do
        if button.Visible then assert(disjoint(c,rectFor(button),8)) end
    end
end

attackInBattle=true
UserInputService.TouchEnabled=true
checkBoth()

-- Tight portrait: actual jump, stick and water button remain available.
gui.AbsoluteSize=Vector2.new(320,260)
jump.AbsolutePosition=Vector2.new(240,182)
stick.AbsolutePosition=Vector2.new(0,168)
stick.AbsoluteSize=Vector2.new(135,92)
jobCast.AbsolutePosition=Vector2.new(150,172)
trapButton.Visible=false
windButton.Visible=false
netButton.Visible=false
rescueButton.Visible=false
checkBoth()

jump.Visible=false
layoutTouchAttack()
assert(attack.Visible and not chainCast.Visible,"CHAIN_TOUCH_NATIVE_FALLBACK_NO_OVERLAP")
UserInputService.TouchEnabled=false
layoutTouchAttack()
assert(attack.Visible and not chainCast.Visible,"CHAIN_NARROW_DESKTOP_NO_OVERLAP")
gui.AbsoluteSize=Vector2.new(960,620)
layoutTouchAttack()
assert(attack.Visible and chainCast.Visible)
print("ACTIVE_MAGE_025_TOUCH_PRIORITY_PORTRAIT_LANDSCAPE_AND_MISSING_NATIVE_PASS")
