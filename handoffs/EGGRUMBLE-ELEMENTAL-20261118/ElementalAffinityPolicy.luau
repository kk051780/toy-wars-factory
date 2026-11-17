--!strict
-- GQ8_ELEMENT_AFFINITY_20261118: pure, side-effect-free battle affinity policy.
-- No HP, Combat, Swarm, Store, Game, Remote or Score authority.
-- Existing V3 role IDs and script count remain unchanged until #220 admits.
local M = {}

export type Element = "FIRE" | "WATER" | "ICE" | "WIND" | "EARTH"
 | "LIGHTNING" | "DIVINE" | "CURSE"
export type Region = "LAND" | "SEA" | "SUBSEA" | "SKY"
export type Weather = "CLEAR" | "WIND" | "RAIN" | "THUNDER"
 | "SNOW" | "HEAT" | "CURSE_FOG" | "HOLY_AURA"

M.ORDER = {"FIRE","WATER","ICE","WIND","EARTH","LIGHTNING","DIVINE","CURSE"}
-- Attack > defense in a closed ring; counterplay exists for every base element.
local dominates: {[string]: string} = {
 FIRE="ICE", ICE="WIND", WIND="EARTH",
 EARTH="LIGHTNING", LIGHTNING="WATER", WATER="FIRE"
}
M.DISPLAY = {
 FIRE={ja="炎",icon="🔥",shape="flame",palette="orange"},
 WATER={ja="水",icon="💧",shape="bubble",palette="blue"},
 ICE={ja="氷",icon="❄",shape="crystal",palette="cyan"},
 WIND={ja="風",icon="🌀",shape="spiral",palette="mint"},
 EARTH={ja="土",icon="◆",shape="shard",palette="umber"},
 LIGHTNING={ja="雷",icon="⚡",shape="zigzag",palette="yellow"},
 DIVINE={ja="神",icon="✧",shape="halo",palette="gold"},
 CURSE={ja="悪",icon="☾",shape="sigil",palette="violet"},
}
function M.isValid(value: any): boolean
 return typeof(value)=="string" and M.DISPLAY[value] ~= nil
end
function M.matchup(attack: string, defense: string): number
 if not M.isValid(attack) or not M.isValid(defense) then return 1 end
 if attack==defense then return 1 end
 -- God and curse are tactical opposites, not blanket upgrades.
 if (attack=="DIVINE" and defense=="CURSE")
  or (attack=="CURSE" and defense=="DIVINE") then return 1.25 end
 if attack=="DIVINE" or attack=="CURSE"
  or defense=="DIVINE" or defense=="CURSE" then return 1 end
 if dominates[attack]==defense then return 1.25 end
 if dominates[defense]==attack then return .80 end
 return 1
end
function M.environment(attack: string, region: string, weather: string): number
 if not M.isValid(attack) then return 1 end
 -- Water prevents almost all realm-only fire undersea; weather does not override it.
 if region=="SUBSEA" then
  if attack=="FIRE" then return .15 end
  if attack=="LIGHTNING" then return 1.25 end
  if attack=="WATER" then return 1.10 end
  if attack=="ICE" then return 1.05 end
 elseif region=="SEA" then
  if attack=="FIRE" then return .70 end
  if attack=="LIGHTNING" then return 1.15 end
  if attack=="WATER" then return 1.10 end
 elseif region=="SKY" then
  if attack=="WIND" then return 1.10 end
  if attack=="EARTH" then return .95 end
 end
 if weather=="THUNDER" and attack=="LIGHTNING" then return 1.15 end
 if weather=="RAIN" and attack=="FIRE" then return .85 end
 if weather=="RAIN" and attack=="WATER" then return 1.10 end
 if weather=="SNOW" and attack=="ICE" then return 1.12 end
 if weather=="HEAT" and attack=="FIRE" then return 1.12 end
 if weather=="WIND" and attack=="WIND" then return 1.10 end
 if weather=="HOLY_AURA" and attack=="DIVINE" then return 1.10 end
 if weather=="CURSE_FOG" and attack=="CURSE" then return 1.10 end
 return 1
end
function M.resolve(attack: string, defense: string, region: string, weather: string)
 local affinity=M.matchup(attack,defense)
 local terrain=M.environment(attack,region,weather)
 -- Universal cap prevents stacked element advantages from one-shot chains.
 -- The underwater fire exception intentionally permits lower than .65.
 local total=math.clamp(affinity*terrain,
  attack=="FIRE" and region=="SUBSEA" and .15 or .65, 1.35)
 local classification=if total>=1.16 then "ADVANTAGE"
  elseif total<=.84 then "RESIST"
  else "NEUTRAL"
 return {affinity=affinity,terrain=terrain,total=total,
  classification=classification,attack=attack,defense=defense}
end
function M.visibleTell(element: string, result: string): string
 local x=M.DISPLAY[element]
 if not x then return "通常" end
 local suffix=if result=="ADVANTAGE" then "有利"
  elseif result=="RESIST" then "軽減" else "通常"
 return x.ja.."・"..suffix
end
return M
