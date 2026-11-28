do
local function inspectResult(expected,winText)
 local gui=playerGui:FindFirstChild("EGGRUMBLE_MatchResult")
 check(gui~=nil,"actual ResultService parents a GUI for the player")
 local card=gui:FindFirstChild("CompactResult")
 local caption=card:FindFirstChild("FinishAndReplay")
 check(caption and caption.Text==expected,"actual result caption uses the current match decision")
 check(caption:IsA("TextLabel"),"hint is informational and cannot queue a player")
 check(card:FindFirstChild("ResultTitle").Text:find(winText,1,true)~=nil,"original status is visible")
 check(card:FindFirstChild("VerifiedPersonalStats").Text:find("点",1,true)~=nil,"original scoring is displayed")
 return gui
end

function growthCases.result_deadline_and_manual_ready()
 local session=ready("RESULT_ACTUAL_TWO_PLAYER_READY")
 outsideField(session)
 parkOldSwarm(session)
 advanceTo(session.deadlineLease.start+900.01)
 check(session.rules.winner=="DRAW" and session.resultsDelivered,"true Host deadline and ResultService")
 local gui=inspectResult("時間切れ｜ロビーで「参加する」","引き分け")
 local count=#capturedSessions
 advanceTo(now+13)
 check(gui.Parent==nil and session.world.Parent==nil,"old card and world retire on their existing timers")
 advanceTo(now+13)
 equal(#capturedSessions,count,"caption does not change voluntary replay")
 ready("RESULT_ACTUAL_NEW_READY")
 return "deadline result, readable reason, no auto-queue, existing READY starts the next match"
end

local function onlyOwnSideSurvives(session)
 local rules=dependencies.EGGRUMBLE_CastleMatchRules
 local state=session.rules
 local owner=state.castles["42"]
 for id,castle in pairs(state.castles) do
  if id~="42" and (state.mode~="TEAM" or castle.team~=owner.team) then
   local strikes=0
   while castle.alive and strikes<15 do
    rules.damageCastle(state,id,"42",250)
    strikes+=1
   end
   check(not castle.alive,"original CastleMatchRules retired the opposing castle")
  end
 end
end

function growthCases.result_team_castle_win()
 local session=ready("RESULT_ACTUAL_TEAM_READY")
 onlyOwnSideSurvives(session)
 check(session.rules.winner==session.rules.castles["42"].team,"actual team victory")
 check(dependencies.EGGRUMBLE_MatchResultService.showIfFinished(session,{player,second},"TEAM"),
  "normal ResultService consumes the actual winner")
 local gui=inspectResult("片方の城が全滅｜ロビーで「参加する」","勝利")
 check(not dependencies.EGGRUMBLE_MatchResultService.showIfFinished(session,{player},"TEAM"),
  "repeated refresh does not publish an extra card")
 check(playerGui:FindFirstChild("EGGRUMBLE_MatchResult")==gui,"original card remains")
 return "real castle authority selects team winner, original result retains score and a brief replay hint"
end

function growthCases.result_br_castle_win()
 trigger(player,scenes:FindFirstChild("ROLE_MAGE"),"職業選択")
 trigger(second,scenes:FindFirstChild("ROLE_WARRIOR"),"職業選択")
 trigger(player,scenes:FindFirstChild("BATTLE_ROYALE_PORTAL"),"参加する")
 trigger(second,scenes:FindFirstChild("BATTLE_ROYALE_PORTAL"),"参加する")
 advanceTo(now+12.01)
 local session=capturedSessions[#capturedSessions]
 check(session and session.rules.mode=="BATTLE_ROYALE","real BR Host launch")
 onlyOwnSideSurvives(session)
 check(session.rules.winner=="42","actual BR winner")
 check(dependencies.EGGRUMBLE_MatchResultService.showIfFinished(session,{player,second},"BATTLE_ROYALE"),
  "normal ResultService receives BR end")
 inspectResult("最後の城が決定｜ロビーで「参加する」","勝利")
 return "BR uses its distinct last-castle reason and existing no-team result"
end
end
