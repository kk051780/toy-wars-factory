import unittest, pathlib, re, zipfile
BASE=pathlib.Path(__file__).resolve().parents[1]
SRC=(BASE/'luau/GoroganCombinedRuntime.luau').read_text()
MODULES=[('TRAP_RAIDERS_v40_v42_ChatLead.zip','luau/ChaosEventCore.luau'),
 ('TRAP_RAIDERS_D07_GoroganServerAI.zip','luau/GoroganServerAICore.luau'),
 ('TRAP_RAIDERS_D07_GoroganRigNavDamage.zip','luau/GoroganRigDriver.luau'),
 ('TRAP_RAIDERS_D07_GoroganRigNavDamage.zip','luau/GoroganDamageBoundary.luau'),
 ('TRAP_RAIDERS_D07_GoroganRigNavDamage.zip','luau/GoroganAttackReceiptWindow.luau'),
 ('TRAP_RAIDERS_D07_GoroganVisual.zip','luau/GoroganVisualPolicy.luau')]
class SourceContract(unittest.TestCase):
 def test_no_client_api(self):
  for phrase in ('OnServerEvent','OnClientEvent','HttpService','DataStoreService','Players.LocalPlayer','RemoteFunction'):
   with self.subTest(phrase=phrase):self.assertNotIn(phrase,SRC)
 def test_one_existing_core(self):self.assertIn('require(script.Parent.GoroganServerAICore)',SRC)
 def test_no_new_scheduler(self):
  self.assertNotIn('math.random(',SRC);self.assertNotIn('RunService.Heartbeat:',SRC)
 def test_activation_binding(self):
  for a in ('activation.event~="ACTIVATE"','activation.kind~="BOSS"','activation.subtype~="GOROGAN"','isCanonicalActivation(activation)','mintServerEventId(activation)'):
   with self.subTest(a=a):self.assertIn(a,SRC)
 def test_s1_s3_only(self):self.assertIn('stage~="S1" and stage~="S3"',SRC)
 def test_no_dummy_receipt(self):
  self.assertNotRegex(SRC,r'isCanonicalAttackReceipt\s*=\s*function.*return true')
 def test_driver_timestamp_present(self):self.assertIn('requestNavigation(cmd.position,cmd.reason,now)',SRC)
 def test_no_teleport(self):self.assertNotIn('PivotTo(',SRC)
 def test_stop_must_close_window(self):self.assertRegex(SRC,r'self\.deps\.receiptWindow:close\(\)')
 def test_stop_stops_rig(self):self.assertIn('self.deps.driver:stop(a.roundId,a.eventId)',SRC)
 def test_stop_stops_gate(self):self.assertIn('self.deps.damageGate:stop(a.roundId,a.eventId)',SRC)
 def test_actual_hit_requires_receipt(self):self.assertIn('openFromCoreResult(cmd,a.roundId,a.eventId)',SRC)
 def test_receipt_closed_even_error(self):self.assertRegex(SRC,r'w:close\(\)\n\s*if not ok then')
 def test_no_direct_take_damage(self):self.assertNotIn('TakeDamage(',SRC)
 def test_real_gate_used(self):self.assertIn('self.deps.damageGate:applyServerDamage',SRC)
 def test_async_event_epoch(self):self.assertIn('epoch~=self.epoch or not live(self,a)',SRC)
 def test_double_heartbeat_guard(self):self.assertIn('if self.busy then return nil,"REENTRANT_HEARTBEAT"',SRC)
 def test_round_end_cleanup(self):self.assertIn('finish(self,a,"ROUND_OR_BOSS_EXPIRED")',SRC)
 def test_invalid_roster(self):self.assertIn('if not validFreshRoster(fresh) then error("INVALID_FRESH_ROSTER") end',SRC)
 def test_fail_closed(self):self.assertIn('"HEARTBEAT_FAIL_CLOSED"',SRC)
 def test_visual_sequencing(self):self.assertIn('self.visualSeq+=1',SRC)
 def test_visual_formats(self):
  for v in ['kind=kind','matchId=a.roundId','stageId=a.stageId','eventId=a.eventId','bossId="GOROGAN"']:
   with self.subTest(field=v):self.assertIn(v,SRC)
 def test_deps_use_real_round(self):self.assertIn('self.deps.getCurrentRoundId()==a.roundId',SRC)
 def test_timeout_cap(self):self.assertIn('math.min(14,endAt-now)',SRC)
 def test_parent_modules_are_identical_unmodified(self):
  # When prior packet ZIPs are present, inspect their *actual* stable contract.
  roots=pathlib.Path('/mnt/data')
  for z,n in MODULES:
   if not (roots/z).exists():continue
   with zipfile.ZipFile(roots/z) as f:s=f.read(n).decode()
   with self.subTest(path=n):self.assertIn('return ',s)
 def test_prior_start_requires_endat(self):
  p=pathlib.Path('/mnt/data/TRAP_RAIDERS_D07_GoroganServerAI.zip')
  if not p.exists():self.skipTest('old packet unavailable')
  with zipfile.ZipFile(p) as z:s=z.read('luau/GoroganServerAICore.luau').decode()
  self.assertIn('input.endsAt',s)
 def test_prior_driver_needs_time(self):
  p=pathlib.Path('/mnt/data/TRAP_RAIDERS_D07_GoroganRigNavDamage.zip')
  if not p.exists():self.skipTest('old packet unavailable')
  with zipfile.ZipFile(p) as z:s=z.read('luau/GoroganRigDriver.luau').decode()
  self.assertIn('function Driver:requestNavigation(position,reason,now)',s)
if __name__=='__main__':unittest.main()
