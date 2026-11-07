-- Entire canonical server inside Lua 5.4 service mocks. NOT Roblox 3D or engine proof.
local H=dofile("tests/roblox_server_harness.lua")
local B=dofile("src/ToyWarsBalance.lua")
local okCount,badCount=0,0
local function up(fn,name)
    for i=1,80 do
        local k,v=debug.getupvalue(fn,i)
        if not k then break end
        if k==name then return v end
    end
    error("missing upvalue "..name)
end
local function fixture()
    local h=H.new(os.getenv("TWF_SERVER_FILE") or "src/ToyWarsServer.server.lua")
    local p=h:addPlayer(h:newPlayer())
    local beat=assert(h.runService.Heartbeat.listeners[1]).fn
    local simulate=up(beat,"simulate")
    local s=assert(up(beat,"sessions")[p])
    local plot=assert(h:workshop(p))
    s.productionTimer=1.2;s.productionCycle=1.2
    s.waveBreak=100
    return h,p,s,plot,simulate
end
local function check(name,fn)
    local ok,err=pcall(fn)
    if ok then okCount=okCount+1;print("PASS "..name)
    else badCount=badCount+1;print("FAIL "..name..": "..tostring(err)) end
end
check("every printer gets a pooled non-colliding neon progress bar",function()
    local _,_,s,plot=fixture()
    local bar=assert(plot:FindFirstChild("ToyPrinterProgress"))
    assert(bar.Material=="Material.Neon" and bar.Anchored==true)
    assert(bar.CanCollide==false and bar.Size.X==0.2)
    assert(bar.Parent==plot and bar.Position.Z==-46)
    assert(bar.Position.X<s.x)
end)
check("first manufacture cycle advances in quantized real time",function()
    local _,_,s,plot,simulate=fixture()
    simulate(s,0.3)
    local bar=plot:FindFirstChild("ToyPrinterProgress")
    assert(bar.Size.X==0.2+0.66*2 and s.printerProgressTick==2)
    assert(s.printerText.Text:find("20%%") and s.productionTimer>0)
end)
check("midcycle unchanged tick never rewrites part size or CFrame",function()
    local _,_,s,plot,simulate=fixture()
    simulate(s,0.3)
    local bar=plot:FindFirstChild("ToyPrinterProgress")
    local beforeSize,beforeFrame,beforeLabel=bar.Size,bar.CFrame,s.printerText.Text
    simulate(s,0.01)
    assert(bar.Size==beforeSize and bar.CFrame==beforeFrame and s.printerText.Text==beforeLabel)
end)
check("print completion actually builds a toy and restarts visual cycle",function()
    local _,_,s,plot,simulate=fixture()
    local first=s.coins.Value
    simulate(s,1.2)
    assert(s.productionCycle==B.productionInterval(1))
    assert(s.productionTimer==3.0 and s.printerProgressTick==0)
    assert(s.printerText.Text:find("NEXT PRINT 3.0s",1,true))
    local allies=0
    for _,e in ipairs(s.entities) do if e.alive and e.side=="ally" then allies=allies+1 end end
    assert(allies==1 and s.coins.Value<first+10)
    assert(plot:FindFirstChild("ToyPrinterProgress").Size.X==0.2)
end)
check("upgraded level speeds NEXT print and label only",function()
    local _,_,s,_,simulate=fixture()
    s.productionCycle=3.0;s.productionTimer=1.0;s.level.Value=6
    simulate(s,0.5)
    assert(s.productionCycle==3 and s.productionTimer==0.5)
    simulate(s,0.5)
    assert(s.productionCycle==B.productionInterval(6))
    assert(s.productionCycle==1.5 and s.printerProgressTick==0)
    assert(s.printerText.Text:find("NEXT PRINT 1.5s",1,true))
end)
check("full field still displays scheduling, never spawns extra toys",function()
    local _,_,s,_,simulate=fixture()
    local add=up(simulate,"addEntity")
    for i=1,B.MAX_FIELD_UNITS do assert(add(s,"pon","ally")) end
    local before=#s.entities
    simulate(s,1.2)
    assert(#s.entities==before)
    assert(s.productionCycle==B.productionInterval(1) and s.printerProgressTick==0)
end)
check("not enough coins cannot buy a toy, bar remains scheduling only",function()
    local _,_,s,_,simulate=fixture()
    s.selected="tankuru";s.coins.Value=0
    simulate(s,1.2)
    assert(#s.entities==0 and s.coins.Value<48)
    assert(s.printerProgressTick==0)
end)
check("bar keeps one stable instance across repeated prints",function()
    local _,_,s,plot,simulate=fixture()
    local bar=plot:FindFirstChild("ToyPrinterProgress")
    local originalCount=#plot:GetChildren()
    simulate(s,1.2)
    s.productionTimer=0
    simulate(s,0.01)
    assert(plot:FindFirstChild("ToyPrinterProgress")==bar)
    assert(#plot:GetChildren()==originalCount)
end)
check("each player workshop has isolated timer and bar object",function()
    local h,p,s,plot,simulate=fixture()
    local other=h:addPlayer(h:newPlayer())
    local another=assert(h:workshop(other))
    local bar=plot:FindFirstChild("ToyPrinterProgress")
    local otherBar=another:FindFirstChild("ToyPrinterProgress")
    simulate(s,0.5)
    assert(bar~=otherBar and otherBar.Size.X==0.2)
    assert(bar.Position.X~=otherBar.Position.X)
end)
check("expired or inactive session cannot animate the printer",function()
    local _,_,s,plot,simulate=fixture()
    s.active=false
    local bar=plot:FindFirstChild("ToyPrinterProgress")
    simulate(s,0.3)
    assert(bar.Size.X==0.2 and s.printerProgressTick==-1)
end)
check("loss reset returns visual cycle to one second",function()
    local _,_,s,plot,simulate=fixture()
    s.productionTimer=100;s.productionCycle=100
    s.baseHP.Value=0
    simulate(s,0.1)
    assert(s.productionTimer==1 and s.productionCycle==1)
    assert(s.printerProgressTick==-1)
    simulate(s,0.1)
    assert(s.printerProgressTick==1)
    assert(plot:FindFirstChild("ToyPrinterProgress").Size.X>0.2)
end)
print(string.format("PRINTER_3D_PROGRESS_SUMMARY %d passed / %d failed; canonical Lua mocks only",okCount,badCount))
if badCount>0 then os.exit(1) end
