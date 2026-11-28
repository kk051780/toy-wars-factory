do
function growthCases.private_round_custody()
 local session=ready("PRIVATE_TWO_PLAYER_TEAM_READY")
 local state=session.rules
 local self=state.castles["42"]
 local target=state.castles["43"]
 local ally,enemy=nil,nil
 for id,castle in pairs(state.castles) do
  if castle.isAI then
   if castle.team==self.team then ally=id else enemy=id end
  end
 end
 check(ally and enemy,"actual roster reserves allied and opposing AI positions")
 local rules=dependencies.EGGRUMBLE_CastleMatchRules
 local score=dependencies.EGGRUMBLE_ScoreBalance
 local received=self.depositedEggs
 local stock=target.vaultEggs
 local team=state.teamDeposits[self.team]
 local beforeInventory=rules.auditEggConservation(state).total
 local vault=session.castleModels["43"].model:FindFirstChild("EggVault")
 local deposit=session.castleModels["42"].model:FindFirstChild("OwnEggDeposit")
 trigger(player,vault,"敵の卵を奪取")
 equal(self.heldEggs,1,"one authorized enemy egg in human custody")
 equal(target.vaultEggs,stock-1,"enemy castle lost exactly one egg")
 local pre
 for _,row in ipairs(score.build(state,session.swarm.kills).rows) do if row.id=="42" then pre=row end end
 equal(pre.pendingSteals,1,"steal pending until physical own deposit")
 equal(pre.securedSteals,0,"no raid score before deposit")
 advanceTo(now+1.1)
 trigger(player,deposit,"卵を納入")
 equal(self.heldEggs,0,"own deposit transfers custody")
 equal(self.depositedEggs,received+1,"real server deposit")
 check(state.teamDeposits[self.team]>=team+1,"actual team score includes the human deposit")
 local after
 for _,row in ipairs(score.build(state,session.swarm.kills).rows) do if row.id=="42" then after=row end end
 equal(after.securedSteals,1,"authoritative score grants one secured raid")
 check(after.objectiveScore>pre.objectiveScore,"actual score includes the secured egg")
 advanceTo(now+1.1)
 trigger(player,deposit,"卵を納入")
 equal(self.depositedEggs,received+1,"empty second deposit changes no score")
 check(rules.auditEggConservation(state).valid and rules.auditEggConservation(state).total==beforeInventory,
  "real authoritative castle and field egg stock remains conserved")
 pass("PRIVATE_HUMAN_EGG_AND_SCORE","real Host enemy vault→own deposit→one secured objective bonus, no duplicate")
 local oldHorde=session.world:FindFirstChild("NeutralHorde")
 outsideField(session)
 parkOldSwarm(session)
 finishAndClose(session,oldHorde)
 local count=#capturedSessions
 advanceTo(now+12.1)
 equal(#capturedSessions,count,"old match never enqueues human on result")
 local next=ready("PRIVATE_VOLUNTARY_SECOND_ROUND")
 check(next~=session and next.isCurrentHuman(player),"only new READY starts another actual round")
 return "actual PRIVATE selection→TEAM READY with AI roster→enemy egg→human deposit/score→results/lobby→voluntary replay"
end
end
