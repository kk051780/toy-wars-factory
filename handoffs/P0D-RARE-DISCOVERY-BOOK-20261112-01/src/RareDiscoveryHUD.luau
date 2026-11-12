--!strict
-- Mobile-friendly, noninteractive server-replicated per-player session notebook.
-- Never sends client "found" decisions to the server or grants inventory.
local Book = require(script.Parent.RareDiscoveryBook)
local HUD = {}
local COLOR_BG = Color3.fromRGB(25,35,75)
local COLOR_TEXT = Color3.fromRGB(255,251,230)
local COLOR_FOUND = Color3.fromRGB(180,246,189)

local function line(name:string,parent:Instance,y:number,height:number):TextLabel
    local text=Instance.new("TextLabel")
    text.Name=name
    text.Size=UDim2.new(1,-16,0,height)
    text.Position=UDim2.fromOffset(8,y)
    text.BackgroundTransparency=1
    text.TextColor3=COLOR_TEXT
    text.TextXAlignment=Enum.TextXAlignment.Left
    text.TextYAlignment=Enum.TextYAlignment.Center
    text.TextScaled=true
    text.Font=Enum.Font.GothamBold
    text.Parent=parent
    return text
end
function HUD.mount(player: Player,book)
    local playerGui=player:FindFirstChildOfClass("PlayerGui")
    if not playerGui then return nil end
    local old=playerGui:FindFirstChild("RareDiscoverySessionBook")
    if old then old:Destroy() end
    local gui=Instance.new("ScreenGui")
    gui.Name="RareDiscoverySessionBook"
    gui.IgnoreGuiInset=false
    gui.ResetOnSpawn=false
    gui.DisplayOrder=24
    gui.Parent=playerGui
    local panel=Instance.new("Frame")
    panel.Name="NotebookPanel"
    panel.AnchorPoint=Vector2.new(1,0)
    panel.Position=UDim2.new(1,-12,0,70)
    panel.Size=UDim2.fromOffset(222,191)
    panel.BackgroundColor3=COLOR_BG
    panel.BackgroundTransparency=0.08
    panel.BorderSizePixel=0
    panel.Parent=gui
    local corners=Instance.new("UICorner")
    corners.CornerRadius=UDim.new(0,12)
    corners.Parent=panel
    local title=line("Title",panel,8,27)
    title.Text="発見ずかん 0/4"
    local subtitle=line("SessionOnly",panel,37,17)
    subtitle.Font=Enum.Font.Gotham
    subtitle.Text="このテスト中だけの記録"
    for n=1,4 do
        line("Creature_"..n,panel,56+(n-1)*29,26)
    end
    HUD.update(player,book)
    return gui
end
function HUD.update(player:Player,book)
    local gui=player:FindFirstChildOfClass("PlayerGui")
    if not gui then return false end
    local root=gui:FindFirstChild("RareDiscoverySessionBook")
    if not root then return false end
    local panel=root:FindFirstChild("NotebookPanel")
    if not panel then return false end
    local title=panel:FindFirstChild("Title")
    if not title then return false end
    title.Text=Book.progress(book)
    for n,item in ipairs(Book.list(book)) do
        local label=panel:FindFirstChild("Creature_"..n)
        if label then
            label.Text=item.text
            label.TextColor3=item.found and COLOR_FOUND or COLOR_TEXT
        end
    end
    return true
end
return HUD
