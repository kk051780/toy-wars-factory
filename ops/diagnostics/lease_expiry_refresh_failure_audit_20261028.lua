-- Read-only diagnostic: execute canonical full servers with a shared fake store.
local H=dofile('tests/roblox_server_harness.lua')
local path='src/ToyWarsServer.server.lua'
local now=0
local function copy(v)
    if type(v)~='table' then return v end
    local t={};for k,x in pairs(v) do t[k]=copy(x) end;return t
end
local store={data={['p:1']={version=1,revision=0,coins=200,wave=2,defeated=3,factoryLevel=1}}}
function store:GetAsync(key) return copy(self.data[key]) end
function store:UpdateAsync(key,transform)
    if self.failWrites then error('injected refresh transport failure') end
    local updated=transform(copy(self.data[key]),nil)
    if updated==nil then return nil end
    self.data[key]=copy(updated);return copy(updated)
end
local function fixture()
    local original=loadfile
    _G.loadfile=function(file,mode,env)
        if file==path and env then
            local get=env.game.GetService
            env.game.GetService=function(self,name)
                if name=='DataStoreService' then return {GetDataStore=function() return store end} end
                return get(self,name)
            end
            env.os.time=function() return now end
        end
        if env==nil then return original(file,mode) end
        return original(file,mode,env)
    end
    local ok,h=pcall(H.new,path);_G.loadfile=original;assert(ok,h)
    return h
end
local function coins(p) return assert(assert(p:FindFirstChild('leaderstats')):FindFirstChild('Coins')) end
local a=fixture();local pa=a:addPlayer(a:newPlayer())
coins(pa).Value=350
local oldOwner=store.data['p:1'].sessionOwner
assert(oldOwner and store.data['p:1'].sessionLeaseUntil==180)
now=181;store.failWrites=true
a.runService.Heartbeat:Fire(0.3)
print('AFTER_EXPIRED_REFRESH_FAILURE visible_coins='..coins(pa).Value..' old_lease='..store.data['p:1'].sessionLeaseUntil..' warnings='..#a.warnings)
assert(coins(pa).Value>350,'old expired session still progresses after refresh failure')
store.failWrites=false
local b=fixture();local pb=b:addPlayer(b:newPlayer())
assert(store.data['p:1'].sessionOwner~=oldOwner,'later session claims expired record')
assert(coins(pb).Value==200,'later session loads last stored progress')
local before=coins(pa).Value
a.runService.Heartbeat:Fire(0.3)
print('WHILE_NEW_OWNER_ACTIVE old_session_coins='..coins(pa).Value..' new_session_coins='..coins(pb).Value)
assert(coins(pa).Value>before,'old session still advances while another owner exists')
a:removePlayer(pa)
print('OLD_FINAL_SAVE stored_coins='..store.data['p:1'].coins..' warnings='..#a.warnings)
assert(store.data['p:1'].coins==200,'old progress cannot save after ownership changed')
print('REPRODUCED expired session + refresh failure permits unsavable old gameplay; deterministic mock, not Roblox')
