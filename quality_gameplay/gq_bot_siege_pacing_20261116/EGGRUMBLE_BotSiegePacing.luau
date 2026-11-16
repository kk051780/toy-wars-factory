--!strict
-- EGGRUMBLE V3 GQ: bot-only target-level siege pacing for TEAM and BR.
-- No new Game, Remote, castle HP authority, bot, or scene. Optional and reversible.
local Pace = {}
Pace.MIN_SECONDS_PER_CASTLE = 7.0

function Pace.allow(session:any, targetId:any, botId:any, now:number):boolean
 if type(session) ~= "table" or type(session.rules) ~= "table" then return false end
 local rules = session.rules
 if rules.phase ~= "ACTIVE" or rules.winner ~= nil then return false end
 if (session.mode ~= "TEAM" and session.mode ~= "BATTLE_ROYALE")
  or rules.mode ~= session.mode then return false end
 if type(now) ~= "number" or now ~= now or math.abs(now) == math.huge or now < 0 then return false end
 local castles = rules.castles
 if type(castles) ~= "table" then return false end
 local target = castles[tostring(targetId)]
 local attacker = castles[tostring(botId)]
 if not target or not target.alive or not attacker or not attacker.alive
  or not attacker.isAI or target.id == attacker.id then return false end
 if session.mode == "TEAM" and target.team == attacker.team then return false end

 -- Immediate rollback to original author behavior, without changing Game/Rules.
 if session.gqBotSiegePacingEnabled == false then return true end

 -- One server-side allowance per TARGET castle across ALL bots, never per bot.
 -- State stays inside this match session. A fresh TEAM/BR match starts clean.
 local lastByCastle = session._gqLastBotSiegeByCastle
 if not lastByCastle then
  lastByCastle = {}
  session._gqLastBotSiegeByCastle = lastByCastle
 end
 local key = tostring(targetId)
 local last = lastByCastle[key]
 if last ~= nil and (now < last or now - last < Pace.MIN_SECONDS_PER_CASTLE) then
  return false
 end
 lastByCastle[key] = now
 return true
end

return Pace
