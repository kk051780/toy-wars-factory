#!/usr/bin/env python3
"""Execute source-exact Luau 3-track progression and reject intentional bad rules."""
import argparse,hashlib,pathlib,re,subprocess,sys,tempfile
ROOT=pathlib.Path(__file__).resolve().parents[1]
POLICY=ROOT/"src/ProgressionRules.luau"
ORIGINAL_BLOB="a72830b039a46ca02d02f6aab7d6a4805bec8860"
TEST=r'''
local P=(function()
__SOURCE_EXACT__
end)()
local n=0
local function eq(got,want,id)
 n+=1
 if got~=want then error("LV_ASSERT_"..id.." got="..tostring(got).." expected="..tostring(want),0) end
end
eq(P.PLAYER_MAX_LEVEL,50,"season_player_level_cap")
eq(P.MASTERY_MAX_LEVEL,10,"equipped_collectible_mastery_cap")
eq(P.XP_CAP_PER_ROUND,150,"per_match_xp_hard_cap")
eq(P.MIN_ELIGIBLE_SECONDS,60,"afk_short_session_prevented")
eq(P.xpToNext(1),60,"starter_fast_lvl2")
eq(P.xpToNext(2),100,"player_lv2_to3")
eq(P.xpToNext(3),140,"player_lv3_to4")
eq(P.xpToNext(4),180,"player_lv4_to5")
eq(P.xpToNext(50),0,"max_player_level_no_more")
eq(P.masteryToNext(1),24,"mastery_first_unlock")
eq(P.masteryToNext(2),36,"mastery_second_unlock")
eq(P.masteryToNext(10),0,"max_mastery_no_more")
eq(P.newProfile(0),nil,"zero_userid_refused")
eq(P.newProfile(0/0),nil,"nan_userid_refused")
eq(P.newRound("a",0,"SCORE",nil,nil),nil,"zero_id_round_denied")
eq(P.newRound("a",1,"NOT_MODE",nil,nil),nil,"forged_mode_denied")
eq(P.newRound("",1,"CLASSIC",nil,nil),nil,"empty_round_id_denied")
eq(P.newRound("a",1,"SCORE","BEAST_CLOUD",false),nil,"equip_unowned_denied")
eq(P.newRound("a",1,"SCORE","BEAST_CLOUD",nil),nil,"equip_unverified_denied")
local p=P.newProfile(101)
eq(p.level,1,"account_starts_lv1")
eq(p.xp,0,"account_starts_zero_xp")
eq(p.settledCount,0,"no_previous_rewards")
local r=P.newRound("serverA:1",101,"CLASSIC",nil,nil)
eq(P.focusLevel(r),1,"round_starts_focus1")
eq(P.recordEvent(r,"ghost","PICKUP",false),false,"server_unconfirmed_pickup_denied")
eq(P.recordEvent(r,"pick1","PICKUP",true),true,"legitimate_pickup_awards_xp")
eq(P.recordEvent(r,"pick1","PICKUP",true),false,"same_action_id_replay_denied")
eq(P.recordEvent(r,"pick2","PICKUP",true),true,"second_pickup_allowed")
eq(P.recordEvent(r,"pick3","PICKUP",true),false,"pickup_cap_two_per_round")
eq(P.focusLevel(r),1,"focus_needs25_not20")
eq(P.previewXp(r,"LOSS",59,true),0,"no_short_match_replay")
eq(P.previewXp(r,"LOSS",60,false),0,"false_result_authority_refused")
eq(P.previewXp(r,"HACK",240,true),0,"invalid_result_denied")
eq(P.previewXp(r,"LOSS",60,true),70,"base50_plus_two_pickups")
eq(P.commit(p,r,"LOSS",59,true),nil,"too_short_does_not_settle")
local receipt=P.commit(p,r,"LOSS",240,true)
eq(receipt.grantedXp,70,"full_match_earned70")
eq(receipt.accountLevelBefore,1,"start_lv1")
eq(receipt.accountLevelAfter,2,"first_match_lv2")
eq(receipt.focusLevel,1,"match_focus_no_threshold")
eq(receipt.gameplayStatsIncreased,false,"no_HPDamageSpeed_buff")
eq(receipt.requiresPaidPurchase,false,"no_paid_xp")
eq(P.playerMilestone(2),"WELCOME_BANNER","level2_cosmetic_reward")
eq(p.level,2,"account_correct_lvl2")
eq(p.xp,10,"carry_remaining_xp")
eq(p.settledCount,1,"one_settlement")
eq(P.commit(p,r,"LOSS",240,true),nil,"same_closed_round_no_double_grant")
local spoof=P.newRound("serverA:1",101,"CLASSIC",nil,nil)
eq(P.recordEvent(spoof,"a","DEPOSIT",true),true,"same_id_new_object_action")
eq(P.commit(p,spoof,"WIN",240,true),nil,"new_round_object_old_id_replay_denied")
eq(p.settledCount,1,"no_duplicate_settlement")
local afk=P.newRound("serverA:2",101,"SCORE","BEAST_CLOUD",true)
eq(P.recordEvent(afk,"ability1","EQUIP_USE",true),true,"owned_equipped_real_use")
eq(P.recordEvent(afk,"ability2","EQUIP_USE",true),false,"one_use_xp_cap")
eq(P.previewXp(afk,"WIN",240,true),0,"equip_only_cannot_farm_xp")
eq(P.commit(p,afk,"WIN",240,true),nil,"equip_only_no_settlement")
eq(p.mastery.BEAST_CLOUD,nil,"AFK_cannot_farm_mastery")
local full=P.newRound("serverA:3",101,"SCORE","BEAST_CLOUD",true)
eq(P.recordEvent(full,"p1","PICKUP",true),true,"full_pick1")
eq(P.recordEvent(full,"p2","PICKUP",true),true,"full_pick2")
eq(P.recordEvent(full,"d1","DEPOSIT",true),true,"full_deposit1")
eq(P.recordEvent(full,"d2","DEPOSIT",true),true,"full_deposit2")
eq(P.recordEvent(full,"d3","DEPOSIT",true),false,"deposit_cap_two")
eq(P.recordEvent(full,"rc1","RECOVER",true),true,"full_recapture")
eq(P.recordEvent(full,"rc2","RECOVER",true),false,"recapture_cap_one")
eq(P.recordEvent(full,"e1","ESCORT",true),true,"escort_real1")
eq(P.recordEvent(full,"e2","ESCORT",true),true,"escort_real2")
eq(P.recordEvent(full,"e3","ESCORT",true),false,"escort_cap_two")
eq(P.recordEvent(full,"g1","DEFEND",true),true,"defend_real1")
eq(P.recordEvent(full,"g2","DEFEND",true),true,"defend_real2")
eq(P.recordEvent(full,"g3","DEFEND",true),false,"defend_cap_two")
eq(P.recordEvent(full,"item1","EQUIP_USE",true),true,"equipped_beast_used_once")
eq(P.focusLevel(full),3,"tactical_focus_max3")
eq(P.previewXp(full,"WIN",240,true),150,"xp_cap150_even_many_events")
eq(P.previewXp(full,"DRAW",240,true),150,"xp_cap150_when_draw")
local f=P.commit(p,full,"WIN",240,true)
eq(f.grantedXp,150,"grant_never_over150")
eq(f.accountLevelAfter,3,"account_lv3_after_second_meaningful_round")
eq(p.xp,60,"player_xp_residual_at_lv3")
eq(f.focusLevel,3,"focus3_in_match_receipt")
eq(f.masteryLevelBefore,1,"collectible_starts_mastery1")
eq(f.masteryLevelAfter,1,"one_used_match_no_premature_m2")
eq(p.mastery.BEAST_CLOUD.xp,12,"mastery_xp12")
local follow=P.newRound("serverA:4",101,"CLASSIC","BEAST_CLOUD",true)
eq(P.recordEvent(follow,"item2","EQUIP_USE",true),true,"real_use_another_round")
eq(P.recordEvent(follow,"pickupA","PICKUP",true),true,"eligible_objective_activity")
local z=P.commit(p,follow,"LOSS",240,true)
eq(z.grantedXp,72,"equipped_use_plus_objective_even_when_lose")
eq(z.masteryLevelAfter,2,"earned_second_mastery_after2_real_uses")
eq(p.mastery.BEAST_CLOUD.xp,0,"mastery_residual_zero")
eq(z.gameplayStatsIncreased,false,"mastery_cosmetic_no_win_buff")
eq(P.masteryMilestone(3),"CREATURE_PALETTE","mastery3_cosmetic")
eq(P.masteryMilestone(6),"ALTERNATE_ANIMATION","mastery6_cosmetic")
eq(P.masteryMilestone(10),"MASTERY_TITLE","mastery10_cosmetic")
eq(P.playerMilestone(5),"PERSONAL_NEST_DECOR","player5_own_nest")
eq(P.playerMilestone(10),"TEAM_EMOTE","player10_emote")
eq(P.playerMilestone(20),"MOUNT_TRAIL_COSMETIC","player20_mount_trail")
eq(P.playerMilestone(30),"CASTLE_FLAG_COSMETIC","player30_flag")
eq(P.playerMilestone(50),"MASTER_AURA_COSMETIC","player50_aura")
local noItem=P.newRound("serverA:5",101,"SCORE",nil,nil)
eq(P.recordEvent(noItem,"a","EQUIP_USE",true),false,"unowned_or_unequipped_use_denied")
eq(P.recordEvent(noItem,"b","DEPOSIT",true),true,"normal_deposit_even_no_item")
local noItemReceipt=P.commit(p,noItem,"DRAW",270,true)
eq(noItemReceipt.grantedXp,80,"loss_draw_win_non_punitive")
eq(noItemReceipt.masteryLevelAfter,nil,"no_gear_no_mastery")
local other=P.newProfile(202)
local rOther=P.newRound("serverA:3",202,"SCORE",nil,nil)
eq(P.recordEvent(rOther,"p1","PICKUP",true),true,"action_id_scope_per_player")
eq(P.commit(other,rOther,"WIN",240,true).accountLevelAfter,2,"other_player_independent")
eq(other.settledCount,1,"other_player_account_isolated")
local wrong=P.newRound("serverA:6",202,"SCORE",nil,nil)
eq(P.recordEvent(wrong,"x","PICKUP",true),true,"different_user_round_good")
eq(P.commit(p,wrong,"WIN",240,true),nil,"cross_user_profile_rejected")
eq(P.recordEvent(full,"new","PICKUP",true),false,"closed_round_no_new_events")
local badConfirm=P.newRound("serverA:7",101,"SCORE",nil,nil)
eq(P.recordEvent(badConfirm,"x","PICKUP",true),true,"eligible_before_unconfirmed_result")
eq(P.commit(p,badConfirm,"WIN",240,false),nil,"spoof_finish_denied")
eq(P.previewXp(badConfirm,"WIN",361,true),0,"unbounded_round_time_denied")
eq(P.previewXp(badConfirm,"WIN",0/0,true),0,"nan_time_denied")
eq(P.recordEvent(badConfirm,"","PICKUP",true),false,"empty_event_id_denied")
eq(P.recordEvent(badConfirm,"xx","FAKE_ACTION",true),false,"untrusted_event_type_denied")
local high=P.newProfile(303)
high.level=50
high.xp=0
local mr=P.newRound("serverA:8",303,"SCORE",nil,nil)
eq(P.recordEvent(mr,"z","PICKUP",true),true,"lv50_plays")
eq(P.commit(high,mr,"WIN",240,true).accountLevelAfter,50,"account_level_capped50")
eq(high.xp,0,"cap_no_overflow")
local master=P.newProfile(404)
master.mastery.RARE_BEAST={level=10,xp=0}
local maxR=P.newRound("serverA:9",404,"CLASSIC","RARE_BEAST",true)
eq(P.recordEvent(maxR,"zz","EQUIP_USE",true),true,"maxed_equipped_beast_used")
eq(P.recordEvent(maxR,"p","PICKUP",true),true,"maxed_round_real_objective")
eq(P.commit(master,maxR,"LOSS",240,true).masteryLevelAfter,10,"mastery_cap10")
eq(master.mastery.RARE_BEAST.xp,0,"mastery_xp_capped")
local fullLedger=P.newProfile(505)
fullLedger.settledCount=P.MAX_RECORDED_ROUNDS
local ledgerRound=P.newRound("serverA:10",505,"CLASSIC",nil,nil)
eq(P.recordEvent(ledgerRound,"pi","PICKUP",true),true,"last_ledger_candidate")
eq(P.commit(fullLedger,ledgerRound,"WIN",240,true),nil,"ledger_full_fails_closed_not_silent_evict")
eq(P.recordEvent(badConfirm,"a","DEPOSIT",true),true,"valid_event_after_failed_result")
if n<90 then error("TOO_FEW_REAL_LUAU_LEVEL_TESTS_"..tostring(n),0) end
print("P0D_LEVEL_PROGRESSION_NATIVE_PASS_"..tostring(n))
'''
MUTANTS=[
 ("replay_objective",'if round.events[eventId]==true then return false end','if false then return false end'),
 ("unbounded_event_cap",'if count>=rule.cap or round.acceptedActions>=20 then return false end','if false then return false end'),
 ("afk_equip_only",'if round.objectiveEvents<1 then return 0 end','if false then return 0 end'),
 ("duplicate_session_reward",'profile.claimedRoundIds[round.id]~=nil','false'),
 ("fake_unequipped_mastery",'kind=="EQUIP_USE" and round.equippedItemId==nil','false'),
 ("win_by_longer_undue_session",'P.MIN_ELIGIBLE_SECONDS = 60','P.MIN_ELIGIBLE_SECONDS = 0'),
 ("too_much_xp_per_round",'P.XP_CAP_PER_ROUND = 150','P.XP_CAP_PER_ROUND = 10000'),
 ("newbie_no_early_progress",'return 60+40*(level-1)','return 600+40*(level-1)'),
 ("equip_mastery_grind",'round.masteryXp+=12','round.masteryXp+=120'),
 ("paid_or_stat_benefit",'gameplayStatsIncreased=false','gameplayStatsIncreased=true'),
]
def gitblob(data):
 return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()
def run(luau,source):
 with tempfile.TemporaryDirectory(prefix="egg_rumble_lv_native_") as td:
  path=pathlib.Path(td)/"genuine_levels.luau"
  path.write_text(TEST.replace("__SOURCE_EXACT__",source),encoding="utf-8")
  result=subprocess.run([str(luau),str(path)],capture_output=True,text=True,timeout=30)
  return result.returncode,result.stdout+result.stderr
def main():
 args=argparse.ArgumentParser();args.add_argument("--luau",type=pathlib.Path,required=True)
 a=args.parse_args()
 raw=POLICY.read_bytes()
 if gitblob(raw)!=ORIGINAL_BLOB:
  raise RuntimeError("ORIGINAL_PROGRESSION_SOURCE_GIT_BLOB_CHANGED "+gitblob(raw))
 source=raw.decode("utf-8")
 result,text=run(a.luau,source)
 matched=re.search(r"P0D_LEVEL_PROGRESSION_NATIVE_PASS_(\d+)",text)
 if result or not matched or int(matched.group(1))<90:
  raise RuntimeError("ACTUAL_LEVEL_NATIVE_POLICY_FAILED "+text[-1800:])
 print(matched.group(0))
 for name,old,new in MUTANTS:
  if source.count(old)!=1: raise RuntimeError("BAD_MUTATION_ANCHOR_"+name+" count="+str(source.count(old)))
  code,log=run(a.luau,source.replace(old,new,1))
  if code==0 or "LV_ASSERT_" not in log:
   raise RuntimeError("UNSAFE_XP_MUTATION_SURVIVED_"+name+" "+log[-1100:])
  print("P0D_LEVEL_POLICY_MUTANT_REJECTED "+name)
 print("P0D_LEVEL_POLICY_UNSAFE_MUTANTS_PASS_"+str(len(MUTANTS)))
 print("P0D_LEVEL_GAME_SERVER_REAL_INTEGRATION_DATASTORE_MOBILE_FUN_NOT_TESTED")
if __name__=="__main__":
 try:main()
 except (OSError,AssertionError,RuntimeError,subprocess.TimeoutExpired) as e:
  print("P0D_LEVEL_NATIVE_QA_BLOCKED "+str(e),file=sys.stderr)
  sys.exit(1)
