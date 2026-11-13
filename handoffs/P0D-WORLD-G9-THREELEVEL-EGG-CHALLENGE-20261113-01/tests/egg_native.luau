-- Native shipped original G9 egg-policy execution. No Roblox engine or physical avatar simulation.
local R=require("../src/G9EggRules")
local n=0
local function ok(value,msg)
 assert(value,msg)
 n+=1
end
local function use(state,act,team,uid,egg,dist,now)
 return R.apply(state,act,team,uid,egg,dist,now)
end
local s=R.new()
ok(s.home.RED and s.home.BLUE,"both home")
ok(s.carrier.RED==0 and s.carrier.BLUE==0,"no carrier")
ok(s.scores.RED==0 and s.scores.BLUE==0,"zero scores")
ok(s.winner=="","no winner")
ok(R.WIN_SCORE==3,"target 3")
ok(R.CARRY_LIMIT==45,"timeout45")
ok(R.MAX_DISTANCE_SQUARED==144,"range12")
ok(R.ACTION_COOLDOWN==.45,"action cooldown")
ok(R.other("RED")=="BLUE" and R.other("BLUE")=="RED","opponent map")
ok(R.other("GREEN")==nil,"invalid team map")
local yes,reason=use(s,"STEAL","RED",-1,"BLUE",120,10)
ok(yes and reason=="STOLEN","red steal blue")
ok(not s.home.BLUE and s.carrier.BLUE==-1,"blue carried")
yes,reason=use(s,"STEAL","BLUE",-2,"RED",120,10.2)
ok(yes and reason=="STOLEN","simultaneous blue steal red")
ok(not s.home.RED and s.carrier.RED==-2,"red carried")
yes,reason=use(s,"SCORE","RED",-1,"RED",100,11)
ok(not yes and reason=="OWN_EGG_MISSING","must rescue own egg")
yes,reason=use(s,"RESCUE","RED",-3,"RED",50,12)
ok(yes and reason=="RESCUED","third red saves red egg")
ok(s.home.RED and s.carrier.RED==0,"red egg home")
yes,reason=use(s,"SCORE","RED",-1,"RED",40,13)
ok(yes and reason=="SCORED","red score")
ok(s.scores.RED==1 and s.home.BLUE and s.carrier.BLUE==0,"score resets blue egg")
yes,reason=use(s,"SCORE","BLUE",-2,"BLUE",30,13.5)
ok(not yes and reason=="NO_ENEMY_EGG","blue cannot score without carry")
yes,reason=use(s,"STEAL","RED",-1,"RED",0,15)
ok(not yes and reason=="OWN_EGG","cannot steal own egg")
yes,reason=use(s,"STEAL","RED",-1,"BLUE",145,16)
ok(not yes and reason=="TOO_FAR","reject far theft")
yes,reason=use(s,"STEAL","RED",-1,"BLUE",144,17)
ok(yes and reason=="STOLEN","exact distance boundary")
yes,reason=use(s,"STEAL","RED",-3,"BLUE",2,18)
ok(not yes and reason=="ALREADY_TAKEN","cannot duplicate egg")
yes,reason=use(s,"RESCUE","BLUE",-2,"BLUE",12,18)
ok(yes and reason=="RESCUED","blue saves blue egg")
yes,reason=use(s,"RESCUE","BLUE",-2,"RED",4,19)
ok(not yes and reason=="WRONG_RESCUE_TEAM","cannot rescue enemy egg")
yes,reason=use(s,"RESCUE","RED",-1,"RED",4,19)
ok(not yes and reason=="NOT_STOLEN","no phantom rescue")
yes,reason=use(s,"STEAL","RED",-1,"BLUE",10,20)
ok(yes and reason=="STOLEN","second theft")
yes,reason=use(s,"SCORE","RED",-1,"RED",4,21)
ok(yes and reason=="SCORED" and s.scores.RED==2,"second point")
yes,reason=use(s,"STEAL","RED",-1,"BLUE",10,22)
ok(yes and reason=="STOLEN","third theft")
yes,reason=use(s,"SCORE","RED",-1,"RED",4,23)
ok(yes and reason=="ROUND_WIN" and s.winner=="RED","three score win")
yes,reason=use(s,"STEAL","BLUE",-2,"RED",5,24)
ok(not yes and reason=="ROUND_FINISHED","no post-win exploitation")
local new=R.new()
ok(new.winner=="" and new.scores.RED==0,"fresh rematch")
local scenarios={
 {"FAKE","RED",-1,"BLUE",3,30,"BAD_ACTION"},
 {"STEAL","GREEN",-1,"BLUE",3,30,"BAD_ACTOR"},
 {"STEAL","RED",0,"BLUE",3,30,"BAD_ACTOR"},
 {"STEAL","RED","-1","BLUE",3,30,"BAD_ACTOR"},
 {"STEAL","RED",-1,"GREEN",3,30,"BAD_ACTOR"},
 {"STEAL","RED",-1,"BLUE",-1,30,"TOO_FAR"},
 {"STEAL","RED",-1,"BLUE",145,30,"TOO_FAR"},
 {"STEAL","RED",-1,"BLUE",0/0,30,"TOO_FAR"},
 {"STEAL","RED",-1,"BLUE","0",30,"TOO_FAR"},
 {"STEAL","RED",-1,"BLUE",1e20,30,"TOO_FAR"},
 {"STEAL","RED",-1,"BLUE",2,-1,"INVALID_CLOCK"},
 {"STEAL","RED",-1,"BLUE",2,1e20,"INVALID_CLOCK"},
 {"SCORE","RED",-1,"BLUE",3,30,"WRONG_PAD"},
 {"SCORE","RED",-1,"RED",3,30,"NO_ENEMY_EGG"},
 {"RESCUE","BLUE",-2,"BLUE",3,30,"NOT_STOLEN"}
}
for _,t in ipairs(scenarios) do
 local fresh=R.new()
 local good,msg=use(fresh,t[1],t[2],t[3],t[4],t[5],t[6])
 ok(not good and msg==t[7],"malformed rejected "..t[7])
 ok(fresh.home.RED and fresh.home.BLUE and fresh.scores.RED==0,"rejection no side effects")
end
local sc=R.new()
yes,reason=use(sc,"STEAL","RED",-1,"BLUE",2,100)
ok(yes and reason=="STOLEN","carrier for expiry")
ok(R.expire(sc,144.99)==0 and sc.carrier.BLUE==-1,"not prematurely expire")
ok(R.expire(sc,145)==1 and sc.home.BLUE and sc.carrier.BLUE==0,"exact45 expiry")
ok(R.expire(sc,145)==0,"expiry idempotent")
yes,reason=use(sc,"STEAL","RED",-1,"BLUE",2,146)
ok(yes,"renew theft")
ok(R.release(sc,999)==0,"wrong player no reset")
ok(R.release(sc,-1)==1 and sc.home.BLUE,"carrier logout reset")
ok(R.release(sc,-1)==0,"release idempotent")
yes,reason=use(sc,"STEAL","RED",-1,"BLUE",2,147)
ok(yes,"third escape theft")
ok(R.expire(sc,0/0)==0,"invalid tick never expires")
ok(R.expire(sc,-1)==0,"negative tick never expires")
ok(R.release(sc,0)==0,"invalid uid never releases")
ok(R.release({},-1)==0,"malformed state no crash")
ok(R.expire({},145)==0,"malformed state no crash")
yes,reason=use({}, "STEAL","RED",-1,"BLUE",2,500)
ok(not yes and reason=="BAD_STATE","malformed state reject")
local cooldown=R.new()
yes,reason=use(cooldown,"STEAL","RED",-1,"BLUE",5,5)
ok(yes,"cooldown pickup")
yes,reason=use(cooldown,"SCORE","RED",-1,"RED",5,5.2)
ok(not yes and reason=="COOLDOWN","reject fast replay")
yes,reason=use(cooldown,"SCORE","RED",-1,"RED",5,4)
ok(not yes and reason=="COOLDOWN","reject clock rollback")
yes,reason=use(cooldown,"SCORE","RED",-1,"RED",5,5.5)
ok(yes and reason=="SCORED","allow after cooldown")
ok(cooldown.scores.RED==1,"verified point")
print("P0D_G9_REAL_NATIVE_EGG_TAG_STATE_MACHINE_PASS assertions="..tostring(n))
