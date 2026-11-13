-- Actual Luau CLI assertions (not Roblox Studio engine).
local R = require("../src/RumbleLinkCueRules")
local assertions=0
local function check(ok, label)
 assertions+=1
 assert(ok, label)
end
local function p(serial, seq, kind, team, now)
 return {roundId="R"..tostring(serial), roundSerial=serial, seq=seq,
   kind=kind or "SCOUT_ASSIST", team=team or "BLUE", expiresAt=now+2}
end
local s=R.new()
check(R.accept(s,p(1,1,"SCOUT_ASSIST","BLUE",10),10,"BLUE")~=nil,"first")
check(R.accept(s,p(1,1,"SCOUT_ASSIST","BLUE",13),13,"BLUE")==nil,"dup")
check(R.accept(s,p(1,2,"SEA_ESCORT","BLUE",13),13,"BLUE")~=nil,"sea")
check(R.accept(s,p(1,3,"TRAP_GUARD","RED",16),16,"BLUE")==nil,"enemy")
check(R.accept(s,p(1,3,"TRAP_GUARD","BLUE",16),16,"BLUE")~=nil,"guard")
check(R.accept(s,p(1,4,"CASTLE_RECAPTURE","BLUE",19),19,"BLUE")~=nil,"castle")
check(R.accept(s,p(1,5,nil,"BLUE",20),20,"BLUE")==nil,"throttle")
check(R.accept(s,p(2,1,nil,"BLUE",21),21,"BLUE")~=nil,"round advance")
check(R.accept(s,p(1,6,nil,"BLUE",24),24,"BLUE")==nil,"old round replay")
local fake=p(2,2,nil,"BLUE",24)
fake.roundId="FORGED"
check(R.accept(s,fake,24,"BLUE")==nil,"same epoch different ID")
local invalid=p(3,1,nil,"BLUE",26)
invalid.roundSerial=0
check(R.accept(s,invalid,26,"BLUE")==nil,"zero epoch")
invalid=p(3,1,nil,"BLUE",26)
invalid.roundSerial=1.5
check(R.accept(s,invalid,26,"BLUE")==nil,"noninteger")
invalid=p(3,1,nil,"BLUE",26)
invalid.expiresAt=25
check(R.accept(s,invalid,26,"BLUE")==nil,"expired")
invalid=p(3,1,nil,"BLUE",26)
invalid.expiresAt=31
check(R.accept(s,invalid,26,"BLUE")==nil,"future")
invalid=p(3,1,nil,"BLUE",26)
invalid.seq=0
check(R.accept(s,invalid,26,"BLUE")==nil,"bad seq")
check(R.accept(s,nil,26,"BLUE")==nil,"nil")
print("RUMBLE_LINK_NATIVE_LUAU_PASS",assertions)
