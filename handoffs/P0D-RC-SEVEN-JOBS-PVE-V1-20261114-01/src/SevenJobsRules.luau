--!strict
-- P0D Seven Jobs PvE MVP: pure server job policy. No Roblox globals,
-- no score/egg/HP/Store ownership, no client-supplied damage/target/position.
local R={}
R.ORDER={"WARRIOR","MAGE","NINJA","TRAPPER","BUILDER","BEAST_TAMER","NECROMANCER"}
R.DETAILS={
 WARRIOR={label="戦士",skill="重撃",cooldown=8,damage=40,kind="FRONT",color={248,170,78}},
 MAGE={label="魔法使い",skill="三連魔法",cooldown=14,damage=16,kind="FAN",color={111,161,255}},
 NINJA={label="忍者",skill="影刃",cooldown=10,damage=24,kind="FLANK",color={170,140,246}},
 TRAPPER={label="罠師",skill="範囲衝撃罠",cooldown=14,damage=12,kind="RING",color={236,118,204}},
 BUILDER={label="建築士",skill="仮設砲台",cooldown=18,damage=14,kind="TURRET",color={243,207,113}},
 BEAST_TAMER={label="魔獣使い",skill="魔獣突進",cooldown=15,damage=23,kind="BEAST",color={100,218,146}},
 NECROMANCER={label="ゾンビ使い",skill="亡者行進",cooldown=18,damage=14,kind="ZOMBIES",color={122,213,106}},
}
function R.valid(job:any):boolean
 return type(job)=="string" and R.DETAILS[job]~=nil
end
function R.canSelect(input:any):boolean
 return type(input)=="table" and input.studio==true
  and input.phase=="LOBBY" and (input.team=="RED" or input.team=="BLUE")
  and R.valid(input.job) and input.occupied~=true
  and type(input.now)=="number" and type(input.last)=="number"
  and input.now-input.last>=1
end
function R.canUse(input:any):boolean
 if type(input)~="table" or input.studio~=true or input.phase~="ACTIVE"
  or (input.team~="RED" and input.team~="BLUE")
  or input.alive~=true or input.carrying==true or input.bound==true
  or not R.valid(input.job) or type(input.now)~="number" or type(input.last)~="number"
  or input.now~=input.now or input.last~=input.last then return false end
 return input.now-input.last>=R.DETAILS[input.job].cooldown
end
function R.safeWall(x:any,z:any,nearObjective:boolean):boolean
 return type(x)=="number" and type(z)=="number" and x==x and z==z
   and math.abs(x)<60 and math.abs(z)<37 and not nearObjective
end
return R
