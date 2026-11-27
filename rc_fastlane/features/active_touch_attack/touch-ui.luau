local attackOccupied = {trapButton, windButton, netButton, rescueButton, relayButton, scoutButton, jobCast, awakenButton}
local attackDesktopSize, attackDesktopPosition, attackDesktopText = attack.Size, attack.Position, attack.Text
local touchActive = false
local attackInBattle = false
local function restoreDesktopAttack()
    if touchActive then
        attack.Size, attack.Position, attack.Text = attackDesktopSize, attackDesktopPosition, attackDesktopText
        touchActive = false
    end
end
local function layoutTouchAttack()
    if not UserInputService.TouchEnabled and not touchActive then return end
    local touchGui = player:FindFirstChildOfClass("PlayerGui")
    local native = touchGui and touchGui:FindFirstChild("TouchGui")
    local frame = native and native:FindFirstChild("TouchControlFrame")
    local jump = frame and frame:FindFirstChild("JumpButton")
    local useTouch = UserInputService.TouchEnabled and native and native:IsA("ScreenGui") and native.Enabled
        and frame and frame:IsA("GuiObject") and frame.Visible
        and jump and jump:IsA("GuiButton") and jump.Visible and jump.AbsoluteSize.X > 0 and jump.AbsoluteSize.Y > 0
    if not useTouch then
        restoreDesktopAttack()
        attack.Visible = attackInBattle
        return
    end
    if not attackInBattle or not jump or not jump:IsA("GuiButton") then return end
    local origin = gui.AbsolutePosition
    local at = jump.AbsolutePosition - origin
    local occupied = {}
    for _, control in attackOccupied do
        if control.Visible then
            local low = control.AbsolutePosition - origin
            table.insert(occupied, Rect.new(low, low + control.AbsoluteSize))
        end
    end
    local stick = frame and frame:FindFirstChild("DynamicThumbstickFrame")
    if stick and stick:IsA("GuiObject") and stick.Visible then
        local low = stick.AbsolutePosition - origin
        table.insert(occupied, Rect.new(low, low + stick.AbsoluteSize))
    end
    local position, size = touchAttackPosition(gui.AbsoluteSize, Rect.new(at, at + jump.AbsoluteSize), occupied)
    if position then
        touchActive = true
        attack.Size = UDim2.fromOffset(size, size)
        attack.Position = UDim2.fromOffset(position.X, position.Y + size)
        attack.Text = "攻撃"
        attack.Visible = true
    else
        -- A viewport with no usable slot must leave the platform controls available.
        touchActive = true
        attack.Visible = false
    end
end
gui:GetPropertyChangedSignal("AbsoluteSize"):Connect(function()
    task.defer(layoutTouchAttack)
end)
UserInputService:GetPropertyChangedSignal("TouchEnabled"):Connect(layoutTouchAttack)
