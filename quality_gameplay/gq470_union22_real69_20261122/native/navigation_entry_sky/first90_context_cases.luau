local flag="P0D_ENABLE_PRIVATE_FIRST90_DEPLOY_CUES"
local function equal(actual,expected,label)
 if actual~=expected then error(label..": "..tostring(actual).." / "..tostring(expected),2) end
end
local function show(t,starter)
 local watching,visible=displayWindow(t,starter)
 return tostring(watching).."/"..tostring(visible)
end
local function reset()
 deployedAt=nil;firstDeploymentAt=nil;player.attrs={};workspace.attrs={}
end

reset()
equal(show(89.99,0),"true/true","original sparse lobby window")
equal(show(90,0),"true/false","quiet lobby observes late start")
equal(show(180,0),"false/false","finite pending limit")
print("FIRST90_DELAYED_QUEUES_ARE_QUIET_AND_BOUNDED_PASS")

reset()
player.attrs.EGGRUMBLE_SelectedRole="NINJA";player.attrs.EGGRUMBLE_QueuedMode="TEAM"
equal(cue(117),"1/3  チーム戦の開始を待とう","selection and queue is not a deployment")
equal(firstDeploymentAt,nil,"queue spends no field cue timer")
player.attrs.EGGRUMBLE_Role="NINJA"
equal(cue(118),"［攻撃／技A］で攻撃\n［技］で固有技を選ぶ","delayed real combat gets first attack prompt")
equal(show(118,0),"true/true","real first deploy resumes the hint")
equal(cue(140),"2/3  卵を奪う／敵の城を攻める","duration measured from deployment")
equal(show(207.9,0),"true/true","late deployment still yields full 90 seconds")
equal(show(208,0),"false/false","exact 90 second limit once deployed")
print("FIRST90_LATE_DEPLOY_SEES_ATTACK_AND_OBJECTIVE_TIMING_PASS")

reset()
player.attrs={EGGRUMBLE_SelectedRole="ZOMBIE",EGGRUMBLE_QueuedMode="BATTLE_ROYALE",EGGRUMBLE_Role="ZOMBIE",
 EGGRUMBLE_CarryingEgg=true}
equal(cue(60),"卵を運搬中\n青緑の印が自分の納入先","own deposit after actual custody, ahead of generic hint")
player.attrs.EGGRUMBLE_CarryingEgg=nil
equal(cue(61),"［攻撃／技A］で攻撃\n［技］で固有技を選ぶ","missing egg does not assert scoring")
player.attrs.EGGRUMBLE_Eliminated=true;player.attrs.EGGRUMBLE_CarryingEgg=true
equal(cue(65),"","eliminated avatar shows no delivery hint")
equal(show(150.001,0),"false/false","later respawn never restarts first-match budget")
print("FIRST90_ACTUAL_CUSTODY_OVERRIDES_AND_ELIMINATION_CLEARS_PASS")

reset()
workspace.attrs[flag]=false
player.attrs={EGGRUMBLE_SelectedRole="NINJA",EGGRUMBLE_QueuedMode="TEAM",EGGRUMBLE_Role="NINJA",
 EGGRUMBLE_CarryingEgg=true}
equal(cue(88),"［攻撃／技A］で攻撃\n［技］で固有技を選ぶ","flag OFF uses original sequence")
equal(show(90,0),"false/false","flag OFF uses original startup timeout")
equal(firstDeploymentAt,nil,"flag OFF creates no new timing state")
print("FIRST90_LIVE_OFF_RESTORES_LEGACY_TIMING_AND_HINTS_PASS")
