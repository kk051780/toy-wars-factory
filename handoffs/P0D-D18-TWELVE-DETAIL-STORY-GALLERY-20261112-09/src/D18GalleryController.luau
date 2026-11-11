-- Opt-in LOCAL-ONLY collector preview. Does not read or set ownership/reward/entitlement.
-- Import this ModuleScript and call .mount(PlayerGui) only in an approved isolated preview.
local Catalog = require(script.Parent:WaitForChild("D18GalleryCatalog"))
local Preview = require(script.Parent:WaitForChild("D18DetailedGalleryPreview"))
local Story = require(script.Parent:WaitForChild("D18StoryBeats"))
local Gallery = {}
local CATEGORIES = { "すべて", "魔獣", "魔法", "乗り物", "武器", "ゾンビ", "罠" }
local BG = Color3.fromRGB(20, 24, 39)
local CARD = Color3.fromRGB(34, 41, 62)
local TEXT = Color3.fromRGB(248, 247, 251)
local SUBTLE = Color3.fromRGB(192, 203, 226)
local ACCENT = Color3.fromRGB(245, 191, 103)

local function label(parent, text, name, position, size, font, textSize, color)
    local view = Instance.new("TextLabel")
    view.Name = name
    view.Position = position
    view.Size = size
    view.BackgroundTransparency = 1
    view.Text = text
    view.TextColor3 = color or TEXT
    view.TextSize = textSize or 17
    view.Font = font or Enum.Font.Gotham
    view.TextXAlignment = Enum.TextXAlignment.Left
    view.TextYAlignment = Enum.TextYAlignment.Center
    view.TextWrapped = true
    view.Parent = parent
    return view
end

local function button(parent, name, text, position, size)
    local view = Instance.new("TextButton")
    view.Name = name
    view.Position = position
    view.Size = size
    view.BackgroundColor3 = CARD
    view.BorderSizePixel = 0
    view.AutoButtonColor = true
    view.Text = text
    view.TextColor3 = TEXT
    view.TextSize = 15
    view.Font = Enum.Font.GothamBold
    view.TextWrapped = true
    view.Parent = parent
    local corner = Instance.new("UICorner")
    corner.CornerRadius = UDim.new(0, 8)
    corner.Parent = view
    return view
end

function Gallery.mount(playerGui)
    assert(playerGui and playerGui:IsA("PlayerGui"), "PlayerGui required")
    assert(playerGui:FindFirstChild("D18LocalCollectionGallery") == nil, "gallery already mounted")
    local state = { category = "すべて", favorites = {}, favoriteOnly = false, selected = "TRCA-BE-018", yaw = 0, pose = "idle", far = false, chapter = 1, closed = false }
    local gui = Instance.new("ScreenGui")
    gui.Name = "D18LocalCollectionGallery"
    gui.ResetOnSpawn = false
    gui.DisplayOrder = 60
    gui.IgnoreGuiInset = false
    gui.ZIndexBehavior = Enum.ZIndexBehavior.Sibling
    gui.Parent = playerGui
    state.gui = gui

    local panel = Instance.new("Frame")
    panel.Name = "GalleryPanel"
    panel.AnchorPoint = Vector2.new(0.5, 0.5)
    panel.Position = UDim2.fromScale(.5, .5)
    panel.Size = UDim2.new(1, -20, 1, -20)
    panel.BackgroundColor3 = BG
    panel.BorderSizePixel = 0
    panel.Parent = gui
    local limit = Instance.new("UISizeConstraint")
    limit.MaxSize = Vector2.new(720, 730)
    limit.MinSize = Vector2.new(265, 330)
    limit.Parent = panel
    local corner = Instance.new("UICorner")
    corner.CornerRadius = UDim.new(0, 12)
    corner.Parent = panel

    label(panel,"キャラクター図鑑｜おためし", "Header", UDim2.fromScale(.04,.012), UDim2.fromScale(.78,.065), Enum.Font.GothamBold, 19)
    local close = button(panel,"Close","×",UDim2.fromScale(.89,.02),UDim2.fromScale(.08,.06))
    label(panel,"12体を無料プレビュー ／ 所持・解放状況ではありません", "FairNotice",UDim2.fromScale(.04,.078),UDim2.fromScale(.92,.05),Enum.Font.Gotham,12,SUBTLE)

    local tabs = Instance.new("ScrollingFrame")
    tabs.Name = "Categories"
    tabs.Position = UDim2.fromScale(.03,.138)
    tabs.Size = UDim2.fromScale(.94,.08)
    tabs.ScrollBarThickness = 3
    tabs.ScrollingDirection = Enum.ScrollingDirection.X
    tabs.CanvasSize = UDim2.fromOffset(0,0)
    tabs.AutomaticCanvasSize = Enum.AutomaticSize.X
    tabs.BackgroundTransparency = 1
    tabs.Parent = panel
    local tabLayout = Instance.new("UIListLayout")
    tabLayout.FillDirection = Enum.FillDirection.Horizontal
    tabLayout.SortOrder = Enum.SortOrder.LayoutOrder
    tabLayout.Padding = UDim.new(0, 5)
    tabLayout.Parent = tabs

    local viewport = Instance.new("ViewportFrame")
    viewport.Name = "Preview3D"
    viewport.Position = UDim2.fromScale(.03,.228)
    viewport.Size = UDim2.fromScale(.94,.38)
    viewport.BorderSizePixel = 0
    viewport.BackgroundColor3 = CARD
    viewport.Parent = panel
    local viewerCorner = Instance.new("UICorner")
    viewerCorner.CornerRadius = UDim.new(0, 8)
    viewerCorner.Parent = viewport

    -- A quiet, readable chapter indicator; no particles or auto-running timers.
    local chapterBadge = label(viewport,"ものがたり 1/3", "StoryChapter", UDim2.fromScale(.03,.025), UDim2.fromScale(.76,.09), Enum.Font.GothamBold, 13, ACCENT)

    local selectedName = label(panel,"", "SelectedName", UDim2.fromScale(.04,.615), UDim2.fromScale(.93,.045), Enum.Font.GothamBold,19)
    local selectedMeta = label(panel,"", "SelectedMeta", UDim2.fromScale(.04,.657), UDim2.fromScale(.93,.04), Enum.Font.Gotham,13,SUBTLE)
    local selectedStory = label(panel,"", "SelectedStory", UDim2.fromScale(.04,.697), UDim2.fromScale(.93,.055), Enum.Font.Gotham,13,TEXT)
    local favorite = button(panel,"Favorite","☆ お気に入り",UDim2.fromScale(.04,.758),UDim2.fromScale(.35,.07))
    local favoriteMode = button(panel,"FavoriteFilter","☆だけ表示",UDim2.fromScale(.41,.758),UDim2.fromScale(.30,.07))
    local rotate = button(panel,"Rotate","↻ まわす",UDim2.fromScale(.73,.758),UDim2.fromScale(.23,.07))
    local storyNext = button(panel,"StoryNext","つぎの物語",UDim2.fromScale(.04,.831),UDim2.fromScale(.29,.055))
    local poseButton = button(panel,"Pose","姿勢:待機",UDim2.fromScale(.35,.831),UDim2.fromScale(.29,.055))
    local lodButton = button(panel,"Lod","画質:詳細",UDim2.fromScale(.66,.831),UDim2.fromScale(.29,.055))
    local status = label(panel,"", "SessionNotice",UDim2.fromScale(.04,.890),UDim2.fromScale(.9,.027),Enum.Font.Gotham,11,SUBTLE)

    local grid = Instance.new("ScrollingFrame")
    grid.Name = "CharacterCards"
    grid.Position = UDim2.fromScale(.03,.927)
    grid.Size = UDim2.fromScale(.94,.065)
    grid.ScrollBarThickness = 4
    grid.ScrollingDirection = Enum.ScrollingDirection.X
    grid.CanvasSize = UDim2.fromOffset(0,0)
    grid.AutomaticCanvasSize = Enum.AutomaticSize.X
    grid.BackgroundTransparency = 1
    grid.Parent = panel
    local layout = Instance.new("UIListLayout")
    layout.Name = "CardFlow"
    layout.FillDirection = Enum.FillDirection.Horizontal
    layout.SortOrder = Enum.SortOrder.LayoutOrder
    layout.Padding = UDim.new(0,6)
    layout.Parent = grid

    local function filtered()
        return Catalog.filter(state.category,state.favoriteOnly,state.favorites)
    end
    local function renderSelected()
        local row = Catalog.byId(state.selected)
        if row == nil then
            selectedName.Text = "選べるキャラがありません"
            selectedMeta.Text = "分類またはお気に入り条件を変更してください"
            selectedStory.Text = ""
            chapterBadge.Text = "ものがたり なし"
            storyNext.Text = "つぎの物語"
            Preview.dispose(viewport)
            favorite.Text = "☆ お気に入り"
            return
        end
        selectedName.Text = row.name
        selectedMeta.Text = row.category .. " ／ " .. row.rarity .. " ／ " .. row.world
        local beat = Story.get(row.id, state.chapter)
        selectedStory.Text = beat and beat.text or row.story
        chapterBadge.Text = beat and ("ものがたり " .. tostring(beat.chapter) .. "/3") or "ものがたり なし"
        storyNext.Text = beat and ("つぎへ " .. tostring(beat.chapter) .. "/3") or "つぎの物語"
        favorite.Text = state.favorites[row.id] and "★ お気に入り中" or "☆ お気に入り"
        local model, detailOrError = Preview.render(viewport,row,state.yaw,state.pose,state.far)
        if not model then
            selectedStory.Text = "詳細3Dの表示失敗: " .. tostring(detailOrError)
        end
    end
    local function render()
        if state.closed then return end
        local available = filtered()
        local found = false
        for _, row in ipairs(available) do
            if row.id == state.selected then found = true end
        end
        if not found then
            state.selected = available[1] and available[1].id or ""
            state.yaw = 0
            state.pose = "idle"
            state.far = false
            state.chapter = 1
            poseButton.Text = "姿勢:待機"
            lodButton.Text = "画質:詳細"
        end
        for _, child in ipairs(grid:GetChildren()) do
            if child:IsA("TextButton") then child:Destroy() end
        end
        for n, row in ipairs(available) do
            local card = button(grid,row.id, row.name .. (state.favorites[row.id] and " ★" or ""), UDim2.fromOffset(0,0),UDim2.fromOffset(130,45))
            card.LayoutOrder = n
            card.BackgroundColor3 = row.id == state.selected and Color3.fromRGB(78,92,132) or CARD
            card.Activated:Connect(function()
                state.selected = row.id
                state.yaw = 0
                state.pose = "idle"
                state.far = false
                state.chapter = 1
                poseButton.Text = "姿勢:待機"
                lodButton.Text = "画質:詳細"
                render()
            end)
        end
        status.Text = "表示 "..tostring(#available).."/12体 ／ ☆はこの画面だけ・保存されません"
        favoriteMode.Text = state.favoriteOnly and "★全部表示へ" or "☆だけ表示"
        renderSelected()
    end
    for i, category in ipairs(CATEGORIES) do
        local tab = button(tabs,"Category"..tostring(i),category,UDim2.fromOffset(0,0),UDim2.fromOffset(75,37))
        tab.LayoutOrder = i
        tab.Activated:Connect(function()
            state.category = category
            render()
        end)
    end
    favorite.Activated:Connect(function()
        if state.selected == "" then return end
        if state.favorites[state.selected] then state.favorites[state.selected] = nil
        else state.favorites[state.selected] = true end
        render()
    end)
    favoriteMode.Activated:Connect(function()
        state.favoriteOnly = not state.favoriteOnly
        render()
    end)
    -- Story has exactly three stages: introduction, difficulty, hopeful resolution.
    -- Source-controlled original 3D factory poses map to idle/loss/win.
    storyNext.Activated:Connect(function()
        if state.closed or state.selected == "" then return end
        local nextChapter = Story.next(state.chapter)
        if not nextChapter then return end
        local beat = Story.get(state.selected, nextChapter)
        if not beat then return end
        state.chapter = nextChapter
        state.pose = beat.pose
        poseButton.Text = if beat.pose == "idle" then "姿勢:待機" elseif beat.pose == "loss" then "姿勢:敗北" else "姿勢:勝利"
        renderSelected()
    end)
    local POSES = {"idle","tap","win","loss"}
    local POSE_LABELS = {idle="待機",tap="タップ",win="勝利",loss="敗北"}
    poseButton.Activated:Connect(function()
        local index = table.find(POSES,state.pose) or 1
        state.pose = POSES[index % #POSES + 1]
        poseButton.Text = "姿勢:" .. POSE_LABELS[state.pose]
        renderSelected()
    end)
    lodButton.Activated:Connect(function()
        state.far = not state.far
        lodButton.Text = if state.far then "画質:軽量" else "画質:詳細"
        renderSelected()
    end)
    rotate.Activated:Connect(function()
        state.yaw = (state.yaw + 45) % 360
        renderSelected()
    end)
    close.Activated:Connect(function()
        state.closed = true
        Preview.dispose(viewport)
        gui:Destroy()
    end)
    function state.destroy()
        if state.closed then return end
        state.closed = true
        Preview.dispose(viewport)
        gui:Destroy()
    end
    render()
    return state
end
return Gallery
