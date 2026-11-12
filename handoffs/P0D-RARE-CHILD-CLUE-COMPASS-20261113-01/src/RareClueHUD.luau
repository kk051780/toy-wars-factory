--!strict
-- Non-interactive, per-player add-on to the ORIGINAL session-only discovery HUD.
-- A single child-readable clue row, with no RemoteEvent and no score effects.
local Clue = require(script.Parent.RareCluePolicy)
local HintHUD = {}
HintHUD.MODE = "TEST_HUB" -- never pretend rare animals are at world castles in this QA Place

function HintHUD.update(player:Player,book):boolean
    local gui=player:FindFirstChildOfClass("PlayerGui")
    local root=gui and gui:FindFirstChild("RareDiscoverySessionBook")
    local panel=root and root:FindFirstChild("NotebookPanel")
    if not panel then return false end
    local hint=panel:FindFirstChild("NextGentleClue")
    if not hint then return false end
    local guidance=Clue.next(book,HintHUD.MODE)
    hint.Text=guidance.title.."\n"..guidance.text
    hint.TextColor3=Color3.fromRGB(245,246,214)
    hint.TextWrapped=true
    return true
end

function HintHUD.mount(player:Player,book):boolean
    local gui=player:FindFirstChildOfClass("PlayerGui")
    local root=gui and gui:FindFirstChild("RareDiscoverySessionBook")
    local panel=root and root:FindFirstChild("NotebookPanel")
    if not panel then return false end
    local existing=panel:FindFirstChild("NextGentleClue")
    if not existing then
        local clue=Instance.new("TextLabel")
        clue.Name="NextGentleClue"
        clue.Size=UDim2.new(1,-16,0,58)
        clue.Position=UDim2.fromOffset(8,177)
        clue.BackgroundTransparency=1
        clue.TextXAlignment=Enum.TextXAlignment.Left
        clue.TextYAlignment=Enum.TextYAlignment.Center
        clue.TextScaled=true
        clue.TextWrapped=true
        clue.Font=Enum.Font.GothamBold
        clue.Parent=panel
    end
    -- Original four book rows stay untouched. Never stack hint overlays.
    panel.Size=UDim2.fromOffset(222,244)
    return HintHUD.update(player,book)
end

return HintHUD
