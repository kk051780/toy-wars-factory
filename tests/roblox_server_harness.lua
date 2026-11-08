-- Minimal deterministic services for executing the entire server script in Lua 5.4.
-- No physics, replication, rendering, network, or Roblox Studio is modeled.
local H = {}
local vectorMT = {}
vectorMT.__index = function(v, key)
    if key == "Magnitude" then return math.sqrt(v.X*v.X + v.Y*v.Y + v.Z*v.Z) end
end
local function vector(x,y,z) return setmetatable({X=x,Y=y,Z=z},vectorMT) end
vectorMT.__sub = function(a,b) return vector(a.X-b.X,a.Y-b.Y,a.Z-b.Z) end
local function frame(x,y,z)
    return {Position=type(x)=="table" and x or vector(x or 0,y or 0,z or 0)}
end
-- Direction-only deterministic mock; not Roblox engine rendering or physics.
local function lookAt(origin,target)
    local dx,dy,dz=target.X-origin.X,target.Y-origin.Y,target.Z-origin.Z
    local len=math.sqrt(dx*dx+dy*dy+dz*dz)
    assert(len>0,"lookAt requires distinct positions")
    return {Position=origin,LookVector=vector(dx/len,dy/len,dz/len)}
end

local fixtureSerial = 0
local function copyData(value)
    if type(value)~="table" then return value end
    local copy={}
    for key,item in pairs(value) do copy[key]=copyData(item) end
    return copy
end

function H.new(serverFile, existingCount, options)
    options=options or {}
    fixtureSerial=fixtureSerial+1
    local fixtureId=fixtureSerial
    local h = {now=0, queue={}, serial=0, warnings={}, playerList={}, nextId=0}
    local function resume(thread,...)
        local ok, delay = coroutine.resume(thread,...)
        if not ok then error(debug.traceback(thread,tostring(delay)),0) end
        if coroutine.status(thread) ~= "dead" then
            assert(type(delay)=="number" and delay>=0,"unsupported scheduler yield")
            h.serial=h.serial+1
            h.queue[#h.queue+1]={thread=thread,time=h.now+delay,serial=h.serial}
        end
    end
    local function spawn(fn,...) resume(coroutine.create(fn),...) end
    local function signal()
        local s = {listeners={}}
        function s:Connect(fn)
            local c = {Connected=true,fn=fn}
            function c:Disconnect() self.Connected=false end
            self.listeners[#self.listeners+1]=c
            return c
        end
        function s:Fire(...)
            local copy={table.unpack(self.listeners)}
            for _, c in ipairs(copy) do if c.Connected then spawn(c.fn,...) end end
        end
        return s
    end
    function h:advance(duration)
        local target=self.now+duration
        local count=0
        while true do
            local index
            for i,item in ipairs(self.queue) do
                if item.time<=target and (not index or item.time<self.queue[index].time or
                    (item.time==self.queue[index].time and item.serial<self.queue[index].serial)) then index=i end
            end
            if not index then break end
            local item=table.remove(self.queue,index)
            self.now=item.time
            resume(item.thread)
            count=count+1
            assert(count<1000,"unexpected scheduler loop")
        end
        self.now=target
    end

    local methods = {}
    local objectMT = {}
    objectMT.__index = function(o,key) return methods[key] or o._props[key] end
    objectMT.__newindex = function(o,key,value)
        local props=o._props
        if key=="Parent" then
            local old=props.Parent
            if old then
                for i,c in ipairs(old._children) do if c==o then table.remove(old._children,i);break end end
            end
            props.Parent=value
            if value then value._children[#value._children+1]=o end
        elseif key=="CFrame" then props.CFrame=value;props.Position=value.Position
        elseif key=="Position" then props.Position=value;props.CFrame=frame(value)
        else props[key]=value end
    end
    local function instance(class)
        local o=setmetatable({_props={ClassName=class,Name=class},_children={},_pivotCount=0},objectMT)
        if class=="Player" then o.CharacterAdded=signal() end
        if class=="ProximityPrompt" then o.Triggered=signal() end
        if class=="RemoteEvent" then o.OnServerEvent=signal() end
        if class=="IntValue" then o.Value=0 end
        if class=="StringValue" then o.Value="" end
        return o
    end
    function methods:FindFirstChild(name)
        for _,c in ipairs(self._children) do if c.Name==name then return c end end
    end
    function methods:WaitForChild(name,timeout)
        local found=self:FindFirstChild(name)
        if found then return found end
        assert(timeout,"fixture missing required object: "..name)
        coroutine.yield(timeout)
        return self:FindFirstChild(name)
    end
    function methods:GetChildren() return {table.unpack(self._children)} end
    function methods:IsA(class)
        return self.ClassName==class or (class=="BasePart" and (self.ClassName=="Part" or self.ClassName=="SpawnLocation"))
    end
    function methods:Destroy()
        for _,child in ipairs(self:GetChildren()) do child:Destroy() end
        self.Parent=nil
    end
    function methods:PivotTo(cf)
        self._pivotCount=self._pivotCount+1
        self._lastPivot=cf
        local root=self:FindFirstChild("HumanoidRootPart")
        if root then root.Position=cf.Position end
    end
    function methods:GetPlayers() return {table.unpack(h.playerList)} end
    h.players=instance("Players");h.players.PlayerAdded=signal();h.players.PlayerRemoving=signal()
    h.storage=instance("ReplicatedStorage")
    h.workspace=instance("Workspace")
    h.runService={Heartbeat=signal(),IsStudio=function() return options.studio==true end}
    h.remote=instance("RemoteEvent");h.remote.Name="ToyWarsSelectUnit";h.remote.Parent=h.storage
    local module=instance("ModuleScript");module.Name="ToyWarsBalance";module.Parent=h.storage
    local balance=assert(loadfile("src/ToyWarsBalance.lua"))()
    function h:character(position,withRoot)
        local character=instance("Model")
        if withRoot~=false then self:addRoot(character,position or vector(0,0,0)) end
        return character
    end
    function h:addRoot(character,position)
        local root=instance("Part");root.Name="HumanoidRootPart";root.Position=position;root.Parent=character
        return root
    end
    function h:newPlayer(character)
        self.nextId=self.nextId+1
        local p=instance("Player");p.UserId=self.nextId;p.DisplayName="Fixture"..self.nextId;p.Character=character
        return p
    end
    function h:addPlayer(player)
        player.Parent=self.players
        self.playerList[#self.playerList+1]=player
        self.players.PlayerAdded:Fire(player)
        return player
    end
    function h:removePlayer(player)
        -- PlayerRemoving fires before removal from Players, matching the documented event order.
        self.players.PlayerRemoving:Fire(player)
        for i,p in ipairs(self.playerList) do if p==player then table.remove(self.playerList,i);break end end
        player.Parent=nil
    end
    function h:respawn(player,character)
        player.Character=character;player.CharacterAdded:Fire(character)
    end
    function h:workshop(player)
        local world=self.workspace:FindFirstChild("ToyWarsWorld")
        return world and world:FindFirstChild("Workshop_"..player.UserId)
    end
    function h:status(player,key)
        local folder=player:FindFirstChild("ToyWarsStatus")
        return folder and folder:FindFirstChild(key)
    end
    function h:prompt(player,name)
        local plot=assert(self:workshop(player),"workshop missing")
        local pad=assert(plot:FindFirstChild(name),"pad missing")
        for _,child in ipairs(pad:GetChildren()) do if child.ClassName=="ProximityPrompt" then return child,pad end end
        error("prompt missing")
    end
    function h:mapCount()
        local n=0
        for _,child in ipairs(self.workspace:FindFirstChild("ToyWarsWorld"):GetChildren()) do
            if child.Name:match("^Workshop_") then n=n+1 end
        end
        return n
    end
    for _=1,existingCount or 0 do
        local p=h:newPlayer();p.Parent=h.players;h.playerList[#h.playerList+1]=p
    end
    local enums=setmetatable({},{__index=function(t,key)
        local value=setmetatable({},{__index=function(_,item) return key.."."..item end})
        rawset(t,key,value);return value
    end})
    -- Successful deterministic persistence for ordinary gameplay fixtures.
    -- Storage is isolated per H.new; failure/overlap specs may inject their own
    -- services. This models values/metadata, not real requests or concurrency.
    local stores={}
    local function keyInfo(record)
        if not record then return nil end
        local ids,metadata=copyData(record.ids),copyData(record.metadata)
        return {GetUserIds=function() return copyData(ids) end,
            GetMetadata=function() return copyData(metadata) end}
    end
    local dataStoreService={}
    function dataStoreService:GetDataStore(name,scope)
        if options.storeOpenFail then error("injected store open unavailable") end
        assert(type(name)=="string" and #name>0,"store name required")
        local storeKey=name.."\0"..(scope or "global")
        if stores[storeKey] then return stores[storeKey] end
        local records={}
        local store={}
        function store:GetAsync(key)
            h.storeReads=(h.storeReads or 0)+1
            if options.storeReadFail then error("injected store read unavailable") end
            local record=records[key]
            return record and copyData(record.value),keyInfo(record)
        end
        function store:UpdateAsync(key,transform)
            h.storeUpdates=(h.storeUpdates or 0)+1
            if options.storeWriteFail then error("injected claim write failure") end
            local record=records[key]
            local updated,ids,metadata=transform(record and copyData(record.value),keyInfo(record))
            if updated==nil then return nil end
            -- Roblox removes associations omitted from a successful transform.
            records[key]={value=copyData(updated),ids=copyData(ids or {}),metadata=copyData(metadata or {})}
            return copyData(updated),keyInfo(records[key])
        end
        stores[storeKey]=store
        return store
    end
    local guidSerial=0
    local httpService={GenerateGUID=function(_,braces)
        guidSerial=guidSerial+1
        local guid=string.format("%08x-0000-4000-8000-%012x",fixtureId,guidSerial)
        return braces and ("{"..guid.."}") or guid
    end}
    local services={Players=h.players,ReplicatedStorage=h.storage,RunService=h.runService,
        DataStoreService=dataStoreService,HttpService=httpService}
    h.services=services
    -- Explicit shutdown callback capture only for explicit lifecycle mock tests.
    local gameStub={GetService=function(_,name) return assert(services[name],"unsupported service") end}
    if options.captureShutdown then
        function gameStub:BindToClose(callback)
            assert(type(callback)=="function","shutdown callback must be a function")
            assert(not h.shutdownCallback,"duplicate shutdown registration")
            h.shutdownCallback=callback
        end
    end
    local env=setmetatable({
        game=gameStub,
        workspace=h.workspace,Instance={new=instance},Enum=enums,
        Vector3={new=vector},CFrame={new=frame,lookAt=lookAt},Color3={fromRGB=function(...) return {...} end},
        UDim={new=function(...) return {...} end},UDim2={fromOffset=function(...) return {...} end,fromScale=function(...) return {...} end},
        task={spawn=spawn,wait=function(duration) return coroutine.yield(duration or 0) end},
        os={clock=function() return h.now end,time=function() return math.floor(h.now) end},
        require=function(value) assert(value==module,"unsupported require");return balance end,
        print=function() end,warn=function(...) h.warnings[#h.warnings+1]={...} end,
    },{__index=_G})
    assert(loadfile(serverFile or "src/ToyWarsServer.server.lua","t",env))()
    h.vector=vector
    return h
end
return H
