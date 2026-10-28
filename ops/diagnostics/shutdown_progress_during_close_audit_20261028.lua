-- Independent diagnostic only: canonical server + injected slow successful store.
-- No actual engine/API timing is claimed.
local H=dofile('tests/roblox_server_harness.lua')
local path='src/ToyWarsServer.server.lua'
local function copy(v)
    if type(v)~='table' then return v end
    local t={}; for k,x in pairs(v) do t[k]=copy(x) end; return t
end
local function run(count,latency,heartbeatDuringClose)
    local records={}
    local closed,spawn,closing,clock
    local started,committed={},{}
    local store={}
    function store:GetAsync(key) return copy(records[key]) end
    function store:UpdateAsync(key,transform)
        if closing then
            started[#started+1]={key=key,time=clock()}
            coroutine.yield(latency)
        end
        local updated,ids,meta=transform(copy(records[key]),nil)
        if updated==nil then return nil end
        records[key]=copy(updated)
        if closing then committed[#committed+1]={key=key,time=clock()} end
        return copy(updated)
    end
    local original=loadfile
    _G.loadfile=function(file,mode,env)
        if file==path and env then
            local getService=env.game.GetService
            env.game.GetService=function(self,name)
                if name=='DataStoreService' then return {GetDataStore=function() return store end} end
                return getService(self,name)
            end
            env.game.BindToClose=function(_,fn) closed=fn end
            spawn=env.task.spawn;clock=env.os.clock
        end
        if env==nil then return original(file,mode) end
        return original(file,mode,env)
    end
    local ok,h=pcall(H.new,path);_G.loadfile=original;assert(ok,h)
    for i=1,count do
        local p=h:addPlayer(h:newPlayer())
        assert(p:FindFirstChild('leaderstats'),'normal admission')
        p:FindFirstChild('leaderstats'):FindFirstChild('Coins').Value=350
    end
    assert(closed,'real canonical BindToClose must register')
    closing=true;spawn(closed)
    if heartbeatDuringClose then
        h:advance(1)
        h.runService.Heartbeat:Fire(0.3)
        local p=h.playerList[1]
        local value=p:FindFirstChild('leaderstats'):FindFirstChild('Coins').Value
        print('SHUTDOWN_GAMEPLAY_DURING_SAVE coins='..value..' expected frozen=350')
        assert(value>350,'reproduction requires actual canonical gameplay mutation while closing')
        h:advance(29)
    else h:advance(30) end
    local saved=0
    for _,record in pairs(records) do if record.coins==350 and record.sessionOwner==nil then saved=saved+1 end end
    print(string.format('SHUTDOWN_AT_30 players=%d latency=%.1f started=%d committed=%d saved=%d',count,latency,#started,#committed,saved))
    local atDeadline=saved
    h:advance(count*latency+1)
    local all=0
    for _,record in pairs(records) do if record.coins==350 then all=all+1 end end
    print(string.format('SHUTDOWN_AFTER_EXTRA_TIME players=%d saved=%d last_commit=%.1f',count,all,committed[#committed].time))
    return atDeadline,all
end
run(1,8,true)
local single=run(1,8)
assert(single==1,'single player control should save before deadline')
local quick=run(4,0.1)
assert(quick==4,'fast service control should save all players')
local deadline,eventual=run(4,8)
assert(deadline==3 and eventual==4,'reproduction: sequential last save misses 30-second bound')
print('REPRODUCED shutdown sequential-save deadline loss: 3/4 saved at30,4/4 only at32; simulated service timing, not real Roblox')
