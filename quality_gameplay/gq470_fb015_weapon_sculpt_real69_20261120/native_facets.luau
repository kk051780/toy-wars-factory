local function vec(x, y, z)
    return {X = x, Y = y, Z = z}
end
local function matrixProduct(a, b)
    local result = {}
    for row = 0, 2 do
        for col = 1, 3 do
            result[row * 3 + col] = a[row * 3 + 1] * b[col]
                + a[row * 3 + 2] * b[3 + col] + a[row * 3 + 3] * b[6 + col]
        end
    end
    return result
end
local identity = {1, 0, 0, 0, 1, 0, 0, 0, 1}
local function transform(a, p)
    return vec(a[1]*p.X+a[2]*p.Y+a[3]*p.Z, a[4]*p.X+a[5]*p.Y+a[6]*p.Z, a[7]*p.X+a[8]*p.Y+a[9]*p.Z)
end
local frameMethods = {}
local function frame(p, r)
    return setmetatable({p = p, r = r}, frameMethods)
end
frameMethods.__mul = function(a, b)
    local p = transform(a.r, b.p)
    return frame(vec(a.p.X+p.X, a.p.Y+p.Y, a.p.Z+p.Z), matrixProduct(a.r,b.r))
end
local function angles(x, y, z)
    local cx, sx = math.cos(x), math.sin(x)
    local cy, sy = math.cos(y), math.sin(y)
    local cz, sz = math.cos(z), math.sin(z)
    local rx = {1,0,0,0,cx,-sx,0,sx,cx}
    local ry = {cy,0,sy,0,1,0,-sy,0,cy}
    local rz = {cz,-sz,0,sz,cz,0,0,0,1}
    return frame(vec(0,0,0), matrixProduct(matrixProduct(rx,ry),rz))
end
local function instance(kind)
    local object = {Name = kind, ClassName = kind, children = {}, attrs = {}}
    function object:IsA(class)
        return class==kind or (class=="BasePart" and (kind=="Part" or kind=="WedgePart"))
    end
    function object:FindFirstChild(name)
        for _, child in ipairs(self.children) do
            if child.Name==name and child.Parent==self then return child end
        end
        return nil
    end
    function object:Destroy()
        for _, child in ipairs(self.children) do child:Destroy() end
        self.Parent = false
    end
    function object:SetAttribute(name, value)
        self.attrs[name] = value
    end
    return setmetatable(object, {__newindex = function(self, key, value)
        if key=="Parent" and value then table.insert(value.children, self) end
        rawset(self, key, value)
    end})
end
local env = setmetatable({
    CFrame = {
        new = function(x,y,z) return frame(vec(x,y,z),identity) end,
        Angles = angles,
    },
    Vector3 = {new = vec},
    Color3 = {fromRGB = function(r,g,b) return {r,g,b} end},
    Enum = {Material = {Metal = "Metal", Neon = "Neon"}, PartType = {Block = "Block", Cylinder = "Cylinder"}},
    Instance = {new = instance},
}, {__index = getfenv()})
local roleCases = {
    {"WARRIOR",5}, {"MAGE",4}, {"NINJA",5}, {"TRAPPER",4}, {"BUILDER",5}, {"BEAST",4}, {"ZOMBIE",5},
}
local function scan(version, source)
    local evaluated = assert(loadstring(source))
    setfenv(evaluated,env)
    local weapons = evaluated()
    local total = 0
    for _, case in ipairs(roleCases) do
        local role,num = case[1],case[2]
        local character = instance("Model")
        local grip = instance("Part")
        grip.Name = "RightHand"
        grip.CFrame = frame(vec(0,0,0),identity)
        grip.Parent = character
        local player = {Character = character}
        assert(weapons.attach(player,role))
        local first = assert(character:FindFirstChild("EGGRUMBLE_ClassWeapon"))
        assert(not weapons.attach(player,"UNKNOWN") and first.Parent==character)
        grip.Name = "Right Arm"
        assert(weapons.attach(player,role))
        assert(first.Parent==false)
        local selected = assert(character:FindFirstChild("EGGRUMBLE_ClassWeapon"))
        assert(selected.attrs.Role==role and selected.attrs.VisualParts==num and #selected.children==num)
        for _, item in ipairs(selected.children) do
            local weld = assert(item:FindFirstChild("EGGRUMBLE_SafeGrip"))
            assert(weld.ClassName=="WeldConstraint" and weld.Part0==grip and weld.Part1==item)
            assert(not item.Anchored and not item.CanCollide and not item.CanTouch and not item.CanQuery and not item.CastShadow)
            assert(item.Massless and item.Parent==selected)
            local p,s,r = item.CFrame.p,item.Size,item.CFrame.r
            local row = {version,role,item.Name,item.ClassName,item.Shape or "Wedge",item.Material,
                         item.Transparency or 0,item.Reflectance or 0,p.X,p.Y,p.Z,s.X,s.Y,s.Z}
            for _, value in ipairs(item.Color) do table.insert(row,value) end
            for _, value in ipairs(r) do table.insert(row,value) end
            print(table.concat(row,"\t"))
            total+=1
        end
        weapons.clear(player)
        assert(not character:FindFirstChild("EGGRUMBLE_ClassWeapon"))
    end
    assert(total==32)
end
