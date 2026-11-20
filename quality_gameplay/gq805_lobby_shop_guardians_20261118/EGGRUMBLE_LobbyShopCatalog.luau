--!strict
-- GQ805 deterministic *candidate catalog*. Existing #482 CastleShopCatalog/Store remain authoritative.
-- No real product IDs, DataStore, Robux transactions, or damage effects in this file.
local M={}
local roles={
 WARRIOR={{"SHIELD_KNIGHT","鉄壁の騎士","PROUD","BIG_SHIELD","BLOCK","ARMOR_CLINK",200},
          {"WAR_BANNER","突撃の旗兵","BRAVE","WAR_BANNER","CHARGE","BATTLE_CRY",420}},
 MAGE={{"ICE_MAGE","氷晶の魔導兵","SHY","ICE_WAND","SLOW","CRYSTAL_CHIME",220},
       {"STAR_HEALER","星灯の癒し兵","KIND","STAR_LANTERN","SUPPORT","HEAL_BELL",420}},
 NINJA={{"SHADOW_SCOUT","影の斥候","CURIOUS","TWIN_DAGGERS","REVEAL","SHADOW_STEP",250},
        {"PHANTOM_DUELIST","幻影の剣士","QUIET","SHADOW_SABER","AMBUSH","DASH_WHIP",440}},
 TRAPPER={{"PSY_PUPPET","ふわふわ念動兵","PLAYFUL","FLOATING_CUBES","PUSH","ORBIT_POP",250},
          {"GRAVITY_KEEPER","重力の守り手","STOIC","GRAVITY_ORB","SLOW","GRAVITY_BASS",460}},
 BUILDER={{"CLOCK_GOLEM","歯車ゴーレム","PATIENT","BRASS_HAMMER","KNOCKBACK","GEAR_BONK",260},
          {"SPRING_ARTILLERY","跳躍砲兵","MISCHIEVOUS","SPRING_LAUNCHER","PUSH","SPRING_BOING",470}},
 BEAST={{"GUARD_WOLF","守護魔狼","LOYAL","FANG_ARMOR","CHASE","HOWL",280},
        {"ARMORED_BEAST","装甲の森獣","GENTLE","STONE_HORNS","TANK","STOMP",480}},
 ZOMBIE={{"CURSE_SOLDIER","呪印兵","QUIET","CURSE_BANNER","DEBUFF","CURSE_CHIME",290},
         {"WRAITH_BEARER","亡霊旗手","MYSTERIOUS","GHOST_LANTERN","DECOY","GHOST_CHIRP",490}},
}
local catalog={}
for role,guardians in pairs(roles) do
 for index,g in ipairs(guardians) do
  local id="GUARD_"..g[1]
  catalog[id]={
   id=id,category="GUARDIAN",role=role,label=g[2],personality=g[3],
   weapon=g[4],behavior=g[5],cue=g[6],battlePoints=g[7],
   robuxKey=id,robuxProductId=nil,paidOnly=false,damageMultiplier=1,
   activeCastleCap=2,summonsPerMatchCap=3,guardianSlotCost=if index==1 then 1 else 2,
   personalityAnimation=if index==1 then "IDLE_LOOK_AND_REACT" else "IDLE_CELEBRATE_AND_REACT",
   unlockTier=1,
  }
 end
end
local extras={
 {"WEAPON_FIRE_SWORD","WEAPON","炎紋の剣",280,"WARRIOR"},
 {"WEAPON_ICE_STAFF","WEAPON","氷晶の杖",300,"MAGE"},
 {"WEAPON_PSI_ORB","WEAPON","念動輪",310,"TRAPPER"},
 {"ABILITY_CURSE_CHAIN","ABILITY","呪印の鎖",440,"ZOMBIE"},
 {"ABILITY_SEISMIC_WAVE","ABILITY","大地の波動",450,"WARRIOR"},
 {"BEAST_CLOUD_WOLF","BEAST","空駆け魔狼",650,"BEAST"},
 {"BEAST_ROCK_TORTOISE","BEAST","岩甲の守獣",680,"BEAST"},
 {"CASTLE_SAKURA","CASTLE","桜の城",380,"ANY"},
 {"CASTLE_SKY","CASTLE","天空石の城",450,"ANY"},
 {"COSMETIC_WAR_FLAG","COSMETIC","戦国旗セット",220,"ANY"},
}
for _,x in ipairs(extras) do
 catalog[x[1]]={id=x[1],category=x[2],label=x[3],battlePoints=x[4],role=x[5],
  robuxKey=x[1],robuxProductId=nil,paidOnly=false,damageMultiplier=1,
  cosmeticOnly=x[2]=="CASTLE" or x[2]=="COSMETIC",unlockTier=1}
end
local starter="GUARD_SHIELD_KNIGHT"
local function copy(t:any):any
 local n={} for k,v in pairs(t) do n[k]=v end return n
end
function M.get(id:string):any
 local v=catalog[id]
 return if v then copy(v) else nil
end
function M.list(category:string?):{any}
 local items={}
 for _,v in pairs(catalog) do
  if category==nil or v.category==category then table.insert(items,copy(v)) end
 end
 table.sort(items,function(a:any,b:any) return a.id<b.id end)
 return items
end
function M.freeStarter():string return starter end
function M.tier(level:number):any
 if type(level)~="number" or level~=level or level<1 then return nil end
 local tier=if level>=25 then 3 elseif level>=10 then 2 else 1
 return {tier=tier,label=({"ルーキー","ベテラン","覚醒"})[tier],
  silhouette=({"BASIC","ARMORED","RUNIC"})[tier],
  animation=({"WAVE","BATTLE_POSE","HALO_CELEBRATE"})[tier],
  -- Level changes look + available tactical style, never paid castle HP/active unit cap.
  paidBonusHP=0,paidBonusDamage=0}
end
function M.canEquip(itemId:string,role:string,level:number,owned:any):boolean
 local e=catalog[itemId]
 if not e or not M.tier(level) then return false end
 if e.role~="ANY" and e.role~=role then return false end
 if e.id==starter then return true end
 return type(owned)=="table" and owned[itemId]==true
end
function M.guardianCount():number
 return #M.list("GUARDIAN")
end
function M.count():number return #M.list() end
M.CASTLE_HP_MULTIPLIER_FROM_PAYMENT=1
M.MAX_GUARDIANS_ACTIVE=2
M.MAX_GUARDIAN_SUMMONS_PER_MATCH=3
M.STARTER_ID=starter
return M
