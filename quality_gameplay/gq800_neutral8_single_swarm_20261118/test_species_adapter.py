from pathlib import Path
import re
import unittest

ROOT=Path(__file__).resolve().parent
SOURCE=(ROOT/"EGGRUMBLE_SwarmCombat.luau").read_text(encoding="utf-8")

class Neutral8SingleAuthority(unittest.TestCase):
 def test_eight_species_and_policy_reuse(self):
  self.assertIn('NeutralFinisherPolicy.listSpecies()',SOURCE)
  for value in ('ACORN_IMP','BABY_GOLEM','BANNER_KNIGHT','ICE_SLIME','SHY_WRAITH','SPARK_GOBLIN','SPIKE_BOAR','TINY_SHIELD'):
   self.assertIn(value,SOURCE)
  self.assertIn('NeutralFinisherPolicy.species(speciesId)',SOURCE)
  self.assertIn('NeutralFinisherPolicy.select(',SOURCE)
 def test_single_spawn_damage_and_credit_authority(self):
  self.assertEqual(SOURCE.count('function Swarm.start(session:any)'),1)
  self.assertEqual(SOURCE.count('local function addEnemy('),1)
  self.assertEqual(SOURCE.count('h:TakeDamage(damage)'),1)
  self.assertEqual(SOURCE.count('credit(id)'),1) # single death callback
  self.assertEqual(SOURCE.count('local LIMIT=110'),1)
  self.assertEqual(SOURCE.count('local NEUTRAL_HEALTH=32'),1)
  self.assertIn('assert(RunService:IsStudio()',SOURCE)
 def test_no_duplicate_remote_store_or_enemy_rig(self):
  for token in ('RemoteEvent','DataStoreService','MarketplaceService','FireServer(', 'GetAsync(', 'ProcessReceipt'):
   self.assertNotIn(token,SOURCE)
  self.assertEqual(SOURCE.count('local accent=piece('),1)
  self.assertIn('root.CanTouch=false',SOURCE)
  self.assertIn('p.CanCollide=false',SOURCE)
 def test_actual_ko_and_line_of_sight(self):
  self.assertIn('ko=h.Health<=0',SOURCE)
  self.assertIn('if h.Health<before then',SOURCE)
  self.assertIn('lineOfSightToNeutral(origin,attacker,model)',SOURCE)
  self.assertIn('if cue.kind=="KO" then',SOURCE)
  self.assertIn('MAX_LOS_RAYS_PER_ATTACK=48',SOURCE)


 def test_real_3d_hit_motions_low_budget(self):
  composer=(ROOT/"compose_real43.py").read_text(encoding="utf-8")
  self.assertIn('local TweenService=game:GetService("TweenService")',SOURCE)
  self.assertIn("local function playActualReaction(model:Model,cue:any)",SOURCE)
  self.assertEqual(SOURCE.count("playActualReaction(model,cue)"),1)
  self.assertIn('model:GetAttribute("EGGRUMBLE_MotionSerial")==serial',SOURCE)
  self.assertIn('now-last<.16',SOURCE)
  self.assertIn('Size=base*factor',SOURCE)
  self.assertIn('Size=base,',SOURCE)
  self.assertIn('local TweenService=game:GetService("TweenService")',composer)
  # Use existing SpeciesAccent: no per-hit new Parts, no second KO authority.
  self.assertEqual(SOURCE.count('local accent=piece('),1)
  self.assertEqual(SOURCE.count('h:TakeDamage(damage)'),1)
  for motion in ("BOW_STUMBLE","SHIELD_TUMBLE","ROLLING_BOAR","JUMP_SPIN",
                 "PUFF_SMOKE","JELLY_WOBBLE","SPARK_SPRINT","FLAT_THEN_POP"):
   self.assertIn(motion,SOURCE)

 def test_only_confirmed_hp_loss_counts_hit_and_ko_credit(self):
  # An invulnerable ForceField/zero damage cannot count as a real hit.
  start=SOURCE.index('    h:TakeDamage(damage)')
  guard=SOURCE.index('    if h.Health>=before then',start)
  feedback=SOURCE.index('    ImpactFeedback.hit(',guard)
  self.assertLess(start,guard)
  self.assertLess(guard,feedback)
  self.assertIn('local oldAttacker=h:GetAttribute("LastAttackerId")',SOURCE)
  self.assertIn('h:SetAttribute("LastAttackerId",oldAttacker)\n     continue',SOURCE)
  composer=(ROOT/"compose_real43.py").read_text(encoding="utf-8")
  self.assertIn('FAILED_DAMAGE_CREDIT_RESTORE',composer)
  self.assertIn('cue_start=\'    local before=h.Health\'',composer)

if __name__=="__main__":
 unittest.main()
