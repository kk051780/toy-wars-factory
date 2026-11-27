local function touchAttackPosition(view: Vector2, jump: Rect, occupied: {Rect}): (Vector2?, number)
    local size = math.clamp(math.floor(math.min(view.X, view.Y) * .23), 56, 74)
    local gap = 8
    local minX = math.floor(view.X * .36)
    local middleX = (jump.Min.X + jump.Max.X - size) / 2
    local middleY = (jump.Min.Y + jump.Max.Y - size) / 2
    local left = jump.Min.X - size - gap
    local top = jump.Min.Y - size - gap
    local right = jump.Max.X + gap
    local bottom = jump.Max.Y + gap
    local inboard = left - size - gap
    local points = {
        Vector2.new(left, middleY), Vector2.new(middleX, top), Vector2.new(right, middleY),
        Vector2.new(middleX, bottom), Vector2.new(left, top), Vector2.new(right, top),
        Vector2.new(left, bottom), Vector2.new(right, bottom),
        Vector2.new(inboard, middleY), Vector2.new(inboard, top), Vector2.new(inboard, bottom),
    }
    local function intersects(point: Vector2, obstacle: Rect): boolean
        return point.X < obstacle.Max.X + gap and point.X + size + gap > obstacle.Min.X
            and point.Y < obstacle.Max.Y + gap and point.Y + size + gap > obstacle.Min.Y
    end
    for _, point in points do
        if point.X < minX or point.Y < 72 or point.X + size > view.X - gap or point.Y + size > view.Y - gap then
            continue
        end
        local free = true
        for _, rect in occupied do
            if intersects(point, rect) then
                free = false
                break
            end
        end
        if free then return point, size end
    end
    -- In narrow portrait layouts the other abilities may occupy the adjacent slots.
    -- Step upward past each actual overlapping control, starting at the right edge.
    local columns = {view.X - size - gap, left, math.floor(view.X * .60)}
    for _, x in columns do
        if x < minX or x + size > view.X - gap then continue end
        local y = view.Y - size - gap
        while y >= 72 do
            local point = Vector2.new(x, y)
            local clearedY = if intersects(point, jump) then jump.Min.Y - size - gap else y
            for _, rect in occupied do
                if intersects(point, rect) then clearedY = math.min(clearedY, rect.Min.Y - size - gap) end
            end
            if clearedY == y then return point, size end
            y = clearedY
        end
    end
    return nil, size
end
