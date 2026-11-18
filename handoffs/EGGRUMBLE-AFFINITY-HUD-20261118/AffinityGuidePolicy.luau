-- BATTLE-765 LANE3: read-only educational view-model. No damage, hit or account authority.
-- Matchup descriptions are from #765 and #766, not a second damage formula.
local Policy = {}
local DETAILS = {
 FIRE={name="火",glyph="炎",strong="ICE",weak="WATER"},
 WATER={name="水",glyph="泡",strong="FIRE",weak="LIGHTNING"},
 LIGHTNING={name="雷",glyph="稲妻",strong="WATER",weak="EARTH"},
 WIND={name="風",glyph="渦",strong="EARTH",weak="ICE"},
 EARTH={name="土",glyph="岩",strong="LIGHTNING",weak="WIND"},
 ICE={name="氷",glyph="結晶",strong="WIND",weak="FIRE"},
 DIVINE={name="神",glyph="光輪",strong="CURSE",weak="CURSE"},
 CURSE={name="悪",glyph="呪印",strong="DIVINE",weak="DIVINE"},
}
local VERIFIED_SKILL_TO_ELEMENT = {
 MAGE={A="ICE",B="FIRE",C="LIGHTNING"},
 WARRIOR={C="DIVINE"},
 ZOMBIE={C="CURSE"},
}
function Policy.describe(element)
 if type(element)~="string" then return nil end
 local d=DETAILS[element]
 if not d then return nil end
 local a,b=DETAILS[d.strong],DETAILS[d.weak]
 return {
  element=element,
  name=d.name,glyph=d.glyph,
  advantage=d.strong,disadvantage=d.weak,
  shortLabel=d.name.." / "..d.glyph,
  matchup="有利: "..a.name.."　注意: "..b.name,
  special=(element=="DIVINE" or element=="CURSE") and "神と悪は互いに弱点。通常6属性には基本等倍" or nil,
 }
end
function Policy.fromVerifiedServerCast(signature,actualRole)
 if type(signature)~="string" or type(actualRole)~="string" then return nil end
 -- Never infer an effect from unsupported skills, a role mismatch, invalid or replayable sequence.
 local sigRole,skill,seqText=string.match(signature,"^([A-Z]+):([ABC]):([1-9]%d*)$")
 if sigRole~=actualRole or not seqText or #seqText>10 then return nil end
 local seq=tonumber(seqText)
 if not seq or seq>2147483647 then return nil end
 local skills=VERIFIED_SKILL_TO_ELEMENT[sigRole]
 local element=skills and skills[skill]
 if not element then return nil end
 return Policy.describe(element),seq
end
function Policy.help()
 return "火→氷→風→土→雷→水→火 / 神と悪は相互弱点"
end
return Policy
