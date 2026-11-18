--!strict
-- BATTLE-ATTR-VFX / #765 lane2. Visual metadata only; never decides damage.
-- A trusted existing SERVER combat owner may set Player.EGGRUMBLE_VisualCue:
--     "FIRE|ADVANTAGE|123" (monotonic integer per player).
-- The client must treat this as a visual hint, NEVER as combat authority.
local M={}
M.FEATURE_ID="BATTLE_ATTR_VFX_20261118"
local ELEMENTS={
 FIRE={label="炎",mark="三叉炎",shape="FORK",rgb={248,116,55}},
 WATER={label="水",mark="二重水輪",shape="RINGS",rgb={64,174,239}},
 LIGHTNING={label="雷",mark="稲妻折線",shape="BOLT",rgb={244,211,63}},
 WIND={label="風",mark="風車羽根",shape="PINWHEEL",rgb={151,225,167}},
 EARTH={label="土",mark="岩片",shape="SHARD",rgb={173,127,79}},
 ICE={label="氷",mark="氷晶",shape="CRYSTAL",rgb={166,222,246}},
 DIVINE={label="神",mark="光輪",shape="HALO",rgb={239,219,158}},
 CURSE={label="悪",mark="封呪鎖",shape="CHAIN",rgb={180,124,217}},
}
local OUTCOMES={
 NEUTRAL={label="等倍",symbol="＝"},
 ADVANTAGE={label="有利",symbol="＋"},
 RESISTED={label="軽減",symbol="－"},
 IMMUNE={label="無効",symbol="×"},
 WEAKNESS={label="弱点",symbol="！"},
}
function M.resolve(element:any,outcome:any,lowSpec:any):any
 if type(element)~="string" or type(outcome)~="string" then return nil end
 local e=ELEMENTS[element]
 local o=OUTCOMES[outcome]
 if not e or not o then return nil end
 local low=(lowSpec==true)
 return {
  element=element,outcome=outcome,label=e.label,mark=e.mark,
  shape=e.shape,rgb={e.rgb[1],e.rgb[2],e.rgb[3]},
  outcomeLabel=o.label,outcomeSymbol=o.symbol,
  text=e.label.."・"..o.label,
  parts=low and 2 or 4,
  range=low and 48 or 76,
  lifetime=0.42,
 }
end
function M.parse(raw:any,lowSpec:any):any
 if type(raw)~="string" or #raw>64 then return nil end
 local element,outcome,sequence=string.match(raw,"^([A-Z]+)|([A-Z]+)|([0-9]+)$")
 if not element then return nil end
 local n=tonumber(sequence)
 if not n or n~=n or n<1 or n>2147483647 then return nil end
 local cue=M.resolve(element,outcome,lowSpec)
 if not cue then return nil end
 cue.sequence=n
 return cue
end
return M
