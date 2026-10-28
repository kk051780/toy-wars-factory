-- Canonical server prompt-distance configuration fence, with 1-stud accepted lag allowance.
-- Native Lua mock only. No real engine, network or touch-input verification.
local H=dofile("tests/roblox_server_harness.lua")
local file="src/ToyWarsServer.server.lua"
local pinned="8a0f8816870fa4854b71c23d223728589303070a"
local passed,failed=0,0
local function eq(a,b,label)
 assert(a==b,(label or "value")..": expected "..tostring(b)..", got "..tostring(a))
end
local function check(name,fn)
 local ok,err=pcall(fn)
 if ok then passed=passed+1;print("PASS "..name)
 else failed=failed+1;print("FAIL "..name..": "..tostring(err)) end
end
local function oldSource()
 local p=assert(io.popen("git show "..pinned..":"..file.." 2>/dev/null","r"))
 local s=p:read("*a")
 assert(p:close() and #s==39993,"pinned previous main required")
 return s
end
local function fixture(source)
 local original=loadfile
 if source then
  _G.loadfile=function(path,mode,env)
   if path==file and env then return assert(load(source,"@PINNED_PROMPT_RANGE","t",env)) end
   if env==nil then return original(path,mode) end
   return original(path,mode,env)
  end
 end
 local ok,h=pcall(H.new,file)
 _G.loadfile=original
 assert(ok,h)
 local p=h:addPlayer(h:newPlayer(h:character()))
 h:advance(0.11)
 return h,p
end
local function scenario(kind,distance,configured,source)
 local h,p=fixture(source)
 local prompt,pad=h:prompt(p,kind=="upgrade" and "UpgradeStation" or "guardonSelector")
 eq(prompt.MaxActivationDistance,12,"initial configured range")
 if configured then prompt.MaxActivationDistance=configured end
 local root=p.Character:FindFirstChild("HumanoidRootPart")
 root.Position=h.vector(pad.Position.X+distance,pad.Position.Y,pad.Position.Z)
 local coins=assert(p:FindFirstChild("leaderstats"):FindFirstChild("Coins"))
 if kind=="upgrade" then coins.Value=65 end
 prompt.Triggered:Fire(p) -- forged event bypasses client activation range
 local r={coins=coins.Value,level=h:status(p,"FactoryLevel").Value,
  selected=h:status(p,"SelectedToy").Value}
 h:removePlayer(p)
 return r
end
check("accepted default 12+1 stud tolerance remains unchanged",function()
 eq(scenario("selector",12.5).selected,"GUARDON","selector")
 local u=scenario("upgrade",12.5);eq(u.level,2,"upgrade");eq(u.coins,0,"coins")
end)
check("reconfigured selector range 5+1 rejects forged distance 6.5",function()
 eq(scenario("selector",6.5,5).selected,"PON","reconfigured selector")
end)
check("reconfigured upgrade range 5+1 rejects forged distance 6.5",function()
 local u=scenario("upgrade",6.5,5);eq(u.level,1,"level");eq(u.coins,65,"coins")
end)
check("reconfigured 5+1 boundary still permits both actions",function()
 eq(scenario("selector",6,5).selected,"GUARDON","selector")
 local u=scenario("upgrade",6,5);eq(u.level,2,"level");eq(u.coins,0,"coins")
end)
check("pinned main ignores narrower configured range (negative control)",function()
 local source=oldSource()
 eq(scenario("selector",6.5,5,source).selected,"GUARDON","old selector")
 local u=scenario("upgrade",6.5,5,source);eq(u.level,2,"old upgrade");eq(u.coins,0,"old coins")
end)
print(string.format("AUTO_PROMPT_DISTANCE_SUMMARY %d passed / %d failed",passed,failed))
if failed>0 then os.exit(1) end
