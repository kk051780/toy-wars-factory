--!strict
-- Pure and engine-independent rendering policy. Never used for game/attack authority.
local R={}
local DECORATIVE={
 WarGod_FlyingSlash=true,
 Mage_CrystalStorm=true,
 Assassin_ShadowAfterimage=true,
 Esper_PsiOrbit=true,
 MadScientist_RailShot=true,
 Beast_FangClaw=true,
 CurseMaster_SoulFlame=true,
}
R.DISTANCE_CULL=125
function R.isDecorative(name:string):boolean
 return DECORATIVE[name]==true
end
function R.newState()
 return {low=false,slow=0,fast=0}
end
function R.sample(state:{low:boolean,slow:number,fast:number}, fps:number)
 if fps<=34 then
  state.slow+=1;state.fast=0
  if state.slow>=2 then state.low=true end
 elseif fps>=47 then
  state.fast+=1;state.slow=0
  if state.fast>=2 then state.low=false end
 else
  state.slow=0;state.fast=0
 end
 return state.low
end
function R.shouldCull(name:string,distance:number,low:boolean,forcedReduced:boolean):boolean
 return DECORATIVE[name]==true and distance>=R.DISTANCE_CULL and (low or forcedReduced)
end
return R
