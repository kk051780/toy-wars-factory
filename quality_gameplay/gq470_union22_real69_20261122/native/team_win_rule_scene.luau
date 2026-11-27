local function buildBoardPair(refresh)
 local boards={TEAM={Text="TEAM｜全味方城陥落で敗北"},BATTLE_ROYALE={Text="BR｜最後の城が勝者"}}
 local queues={TEAM={},BATTLE_ROYALE={}}
 local sessions={}
 local started={}
 local now=100
 local update=refresh(boards,queues,sessions,started,function() return now end)
 local function check(region,tail)
  update("TEAM")
  update("BATTLE_ROYALE")
  assert(boards.TEAM.Text=="TEAM｜敵全城破壊で勝ち\n"..tail,"TEAM_WIN_RULE_MISSING_"..region)
  assert(boards.BATTLE_ROYALE.Text=="BR｜最後の城が勝者\n"..tail,"BR_LABEL_DRIFT_"..region)
 end
 return function()
  check("IDLE","参加する｜1人でも開始")
  for _,mode in {"TEAM","BATTLE_ROYALE"} do
   queues[mode]={11,22,33}
   started[mode]=97
  end
  check("WAITING","3/16人｜開始まで9秒")
  now=130
  check("EXPIRED_VISUAL","3/16人｜開始まで0秒")
  assert(next(sessions)==nil and queues.TEAM[3]==33 and queues.BATTLE_ROYALE[3]==33)
  for _,mode in {"TEAM","BATTLE_ROYALE"} do sessions[mode]={phase="ACTIVE"} end
  check("ACTIVE","試合中｜次の試合を待つ")
  assert(sessions.TEAM.phase=="ACTIVE" and sessions.BATTLE_ROYALE.phase=="ACTIVE")
  assert(#queues.TEAM==3 and #queues.BATTLE_ROYALE==3)
  boards.TEAM=nil
  update("TEAM")
 end
end

__HOST_REFRESH_PROGRAMS__

local before,reason=pcall(buildBoardPair(beforeRefresh))
assert(not before and string.find(reason,"TEAM_WIN_RULE_MISSING_IDLE",1,true),"OLD_NOTICE_CONTROL_NOT_RED")
buildBoardPair(afterRefresh)()
print("PRIVATE_TEAM_WIN_BOARD_ACTUAL_HOST_OFF_RED_ON_8_CASES_PASS")
