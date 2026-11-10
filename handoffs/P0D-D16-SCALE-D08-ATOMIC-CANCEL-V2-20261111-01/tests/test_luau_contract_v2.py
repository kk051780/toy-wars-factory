"""Source-only assertions; not a Luau compiler or Roblox Studio test."""
import pathlib,unittest
SRC=(pathlib.Path(__file__).resolve().parents[1]/'luau'/'D16ScaleD08GateV2.luau').read_text(encoding='utf-8')

class LuauContract(unittest.TestCase):
    def test_named_interface(self):
        for x in ['function Gate.new','function Gate:onWeatherActivate','function Gate:onCleanup','function Gate:snapshot','function Gate:stop','function Gate:_closeActive','function Gate:_cancelPending','function Gate:_isCurrent']:
            with self.subTest(x=x):self.assertIn(x,SRC)
    def test_cancel_generation(self):
        self.assertIn('self.cancelGeneration += 1',SRC)
    def test_precancel_before_pending_close(self):
        self.assertIn('if pending ~= nil and sameEnvelope(pending, e) then',SRC)
        self.assertIn('return true, "CANCELLED_PENDING"',SRC)
    def test_canceled_after_begin_rollback(self):
        self.assertIn('self:_closeActive("CANCELLED_AFTER_BEGIN")',SRC)
    def test_stop_calls_core_close(self):
        b=SRC.split('function Gate:stop()',1)[1]
        self.assertIn('self:_cancelPending()',b)
        self.assertIn('self:_closeActive("OWNER_STOP")',b)
    def test_snapshot_uses_generation(self):
        b=SRC.split('function Gate:snapshot()',1)[1].split('function Gate:onCleanup',1)[0]
        self.assertIn('self.cancelGeneration ~= token',b)
    def test_all_callback_boundaries_guarded(self):
        b=SRC.split('function Gate:onWeatherActivate',1)[1].split('function Gate:snapshot',1)[0]
        self.assertGreaterEqual(b.count('if not self:_isCurrent(token, pending)'),5)
    def test_no_side_effectful_remote(self):
        for x in ['Instance.new','OnServerEvent','FireClient','TakeDamage','Humanoid','AssemblyLinearVelocity','SetPrimaryPartCFrame','math.random','task.spawn','task.delay','Heartbeat:Connect','game:GetService','MarketplaceService']:
            with self.subTest(x=x):self.assertNotIn(x,SRC)
    def test_d08_is_solo_authority(self):
        self.assertIn('D08',SRC)
        self.assertNotIn('Random.new',SRC)
    def test_no_default_mapping(self):
        self.assertIn('NO_EXPLICIT_MAPPING',SRC)
        self.assertIn('UNAPPROVED_SUBTYPE',SRC)
        self.assertNotIn('WX02_SMALL = "MINI_ALL"',SRC)
        self.assertNotIn('WX03_CROWN = "GIANT_ONE"',SRC)
    def test_state_immutable_during_callback(self):
        self.assertIn('Only validated primitives cross a potentially yielding callback boundary.',SRC)
    def test_clock_backwards(self):
        self.assertIn('CLOCK_BACKWARDS',SRC)
    def test_fail_closed_cleanup(self):
        self.assertIn('CORE_CLOSE_FAILED',SRC)

if __name__=='__main__':unittest.main()
