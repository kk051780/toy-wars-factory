import pathlib,unittest,zipfile,hashlib,re
ROOT=pathlib.Path(__file__).resolve().parents[1]
BRIDGE=(ROOT/'luau/CanonicalEventBridge.luau').read_text()
STUB=(ROOT/'luau/CanonicalEventServerAdapter.server.luau').read_text()
OLD=pathlib.Path('/mnt/data/TRAP_RAIDERS_v40_v42_ChatLead.zip')
class LuauContract(unittest.TestCase):
 def test_no_rng_duplicated(self):self.assertNotRegex(BRIDGE,r'\bmath\.random\b|\bRandom\.new\b|\bNextInteger\b')
 def test_old_core_reused(self):
  for s in ('self.core.new','self.core.advance','serverRoll','rollUsed'):
   self.assertIn(s,BRIDGE)
 def test_disabled_default(self):self.assertIn('config.enabled == true',BRIDGE);self.assertIn('ENABLE_AFTER_PC_SINGLE_CHOICE_AUDIT = false',STUB)
 def test_no_remote_receiver(self):self.assertNotIn('OnServerEvent',BRIDGE);self.assertNotIn('OnServerInvoke',BRIDGE)
 def test_no_gameplay_mutations(self):
  for bad in ('TakeDamage','Humanoid:MoveTo','DataStore','FireAllClients('):self.assertNotIn(bad,BRIDGE)
 def test_alias_block(self):self.assertIn('RAIGALD_LIGARDO_ALIAS_REVIEW_REQUIRED',BRIDGE)
 def test_old_stage_literals(self):
  if not OLD.exists():self.skipTest('old local reference not mounted')
  with zipfile.ZipFile(OLD) as z:src=z.read('luau/ChaosEventCore.luau')
  self.assertEqual(hashlib.sha256(src).hexdigest(),'f6d6901a8dcb61cec1095e383e485950144d39ea43737c9b33d4351a66e88726')
  self.assertIn(b'S2 = "RAIGALD"',src)
 def test_cleanup_on_warning(self):self.assertIn('if cur.activated or cur.warned then',BRIDGE)
 def test_stale_protection(self):
  for s in ('TIME_REVERSED','ROUND_REPLAY_DENIED','ROUND_REPLACED','RETIRED_ROUND_LIMIT_REACHED','TRUSTED_CALLBACK_FAILED'):self.assertIn(s,BRIDGE)
 def test_weather_handler_failclosed(self):self.assertIn('WEATHER_RUNTIME_MISSING',BRIDGE)
 def test_one_choice(self):self.assertIn('DUPLICATE_ROLL',BRIDGE)
 def test_epoch(self):self.assertIn('snapshot.epoch',BRIDGE)
 def test_activation_guard(self):self.assertIn('ACTIVATE_WITHOUT_WARNING',BRIDGE)
 def test_required_callbacks(self):
  for s in ('onCleanup','onWarning','onBossActivate','onWeatherActivate'):self.assertIn(s,BRIDGE)
 def test_no_automatic_loop(self):self.assertNotIn('RunService.Heartbeat:Connect',STUB)
 def test_return(self):self.assertTrue(BRIDGE.rstrip().endswith('return Bridge'))
if __name__=='__main__':unittest.main()
