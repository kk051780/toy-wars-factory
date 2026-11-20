--!strict
local B=require("./EGGRUMBLE_ControlBudgetPolicy")
assert(B.WINDOW_SECONDS==8 and B.MAX_SEEN_RECEIPTS_PER_AVATAR==72)
local state=B.new("round-7")
assert(state~=nil)
local receipt={
 epoch="round-7",targetAvatarKey="player42:avatar12",uniqueHitId="r7_hit_1",
 serverTimeSeconds=50,serverConfirmedHit=true,matchActive=true,epochCurrent=true,
 victimIsHuman=true,attackerIsHuman=true,sameTeam=false,spawnProtected=false,
 attackerAlive=true,targetAlive=true,role="MAGE",element="ICE",distanceStuds=18,
 visible=true,deviceTier="LOW",
 -- Malicious/hypothetically stale inputs must be ignored in favour of budget.
 targetHardCCCount8s=0,targetHardCCSeconds8s=0,targetControlImmunityUntil=0,
}
local first=B.consume(state,receipt)
assert(first and first.status=="FREEZE" and first.hardControl)
assert(B.consume(state,receipt)==nil)
receipt.uniqueHitId="r7_hit_2";receipt.serverTimeSeconds=50.5;receipt.element="LIGHTNING"
local second=B.consume(state,receipt)
assert(second and second.status=="SHOCK" and second.hardControl)
receipt.uniqueHitId="r7_hit_3";receipt.serverTimeSeconds=50.6;receipt.element="ICE"
local third=B.consume(state,receipt)
assert(third and third.status=="BRIEF_SLOW" and not third.hardControl)
receipt.serverTimeSeconds=50.4;receipt.uniqueHitId="r7_old"
assert(B.consume(state,receipt)==nil)
receipt.serverTimeSeconds=54;receipt.uniqueHitId="r7_immune"
assert(B.consume(state,receipt).status=="BRIEF_SLOW")
receipt.serverTimeSeconds=59;receipt.uniqueHitId="r7_later"
assert(B.consume(state,receipt).status=="FREEZE")
-- Closing a match or an avatar invalidates all past combat state.
assert(B.resetRound(state,"round-8"))
receipt.epoch="round-7";receipt.uniqueHitId="r7_stale"
assert(B.consume(state,receipt)==nil)
receipt.epoch="round-8";receipt.uniqueHitId="r8_1";receipt.serverTimeSeconds=60
assert(B.consume(state,receipt).status=="FREEZE")
assert(B.clearTarget(state,"player42:avatar12"))
receipt.uniqueHitId="r8_2"
assert(B.consume(state,receipt).status=="FREEZE")
-- Simultaneous victims have independent budgets.
receipt.targetAvatarKey="player43:avatar1";receipt.uniqueHitId="r8_3"
assert(B.consume(state,receipt).status=="FREEZE")
-- Faked receipt is never counted, and cannot block later genuine hits.
receipt.serverConfirmedHit=false;receipt.uniqueHitId="r8_fake"
assert(B.consume(state,receipt)==nil)
receipt.serverConfirmedHit=true
local recovered=B.consume(state,receipt)
assert(recovered and recovered.hardControl)
assert(B.consume(state,receipt)==nil)
-- All 7 roles and 8 elements still participate through single cue policy.
receipt.targetAvatarKey="player98:a1";receipt.serverTimeSeconds=100
local roles={"WARRIOR","MAGE","NINJA","TRAPPER","BUILDER","BEAST","ZOMBIE"}
local elements={"FIRE","ICE","LIGHTNING","WATER","WIND","EARTH","DIVINE","CURSE"}
local n=0
for _,role in ipairs(roles) do
 for _,el in ipairs(elements) do
  n=n+1
  receipt.role=role;receipt.element=el;receipt.uniqueHitId="r8_mix_"..tostring(n)
  receipt.serverTimeSeconds=100+n/10
  assert(B.consume(state,receipt)~=nil)
 end
end
assert(n==56)
receipt.uniqueHitId="r8_forged";receipt.sameTeam=true
assert(B.consume(state,receipt)==nil)
receipt.sameTeam=false;receipt.spawnProtected=true
assert(B.consume(state,receipt)==nil)
receipt.spawnProtected=false;receipt.serverTimeSeconds=math.huge
assert(B.consume(state,receipt)==nil)
print("GQ802_NATIVE_PVP_BUDGET_EPOCH_AVATAR_HIT_REPLAY_56_GATES_PASS")
