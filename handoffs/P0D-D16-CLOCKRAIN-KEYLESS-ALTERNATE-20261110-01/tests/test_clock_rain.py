"""Python policy tests and Luau safety-shape assertions, not Roblox Studio tests."""
import pathlib
import sys
import unittest
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
from reference import ClockRain
S = (ROOT / "luau" / "ClockRainVisualPolicy.luau").read_text(encoding="utf-8")
R = (ROOT / "luau" / "ClockRainClientRenderer.luau").read_text(encoding="utf-8")

def valid(**kwargs):
    s = dict(server_event_approved=True, event_name="CLOCK_RAIN", phase="ACTIVATE",
             match_id="r1", epoch=1, sequence=1, now=102.0,
             event_started_at=101.0, duration=12.0, reduced_motion=False)
    s.update(kwargs)
    return s

class ReferenceTests(unittest.TestCase):
    def test_start_and_expiry(self):
        p=ClockRain()
        self.assertEqual(p.start(valid()), "STARTED")
        self.assertEqual(p.step(112.9,"r1",1),("FRAME",12))
        self.assertEqual(p.step(113,"r1",1),("CLEARED",0))

    def test_low_motion(self):
        p=ClockRain()
        self.assertEqual(p.start(valid(reduced_motion=True)),"STARTED")
        self.assertEqual(p.step(103,"r1",1),("FRAME",4))

    def test_unauthorized(self):
        self.assertEqual(ClockRain().start(valid(server_event_approved=False)),"REJECTED")

    def test_wrong_event(self):
        self.assertEqual(ClockRain().start(valid(event_name="METEOR")),"REJECTED")

    def test_bad_phase(self):
        self.assertEqual(ClockRain().start(valid(phase="WARNING")),"REJECTED")

    def test_stale_start(self):
        self.assertEqual(ClockRain().start(valid(now=104)),"REJECTED")

    def test_future_start(self):
        self.assertEqual(ClockRain().start(valid(now=100)),"REJECTED")

    def test_duration_bound(self):
        self.assertEqual(ClockRain().start(valid(duration=13)),"REJECTED")

    def test_duplicate(self):
        p=ClockRain()
        self.assertEqual(p.start(valid()),"STARTED")
        p.stop()
        self.assertEqual(p.start(valid()),"REJECTED")

    def test_new_sequence(self):
        p=ClockRain()
        self.assertEqual(p.start(valid()),"STARTED")
        p.stop()
        self.assertEqual(p.start(valid(sequence=2)),"STARTED")

    def test_round_reset(self):
        p=ClockRain()
        p.start(valid())
        self.assertEqual(p.step(104,"wrong",1),("CLEARED",0))

    def test_reject_missing_data(self):
        self.assertEqual(ClockRain().start({}),"REJECTED")

class SourceSafetyTests(unittest.TestCase):
    def test_default_off(self):
        self.assertIn("active = false",S)
    def test_caps(self):
        self.assertIn("and 4 or 12",S)
    def test_duration(self):
        self.assertIn("s.duration > 12.0",S)
    def test_no_event_lottery(self):
        self.assertNotIn("math.random",S+R)
    def test_no_network_listener(self):
        self.assertNotIn("OnClientEvent",S+R)
        self.assertNotIn("FireServer",S+R)
    def test_no_hits(self):
        self.assertIn("p.CanCollide = false",R)
        self.assertIn("p.CanTouch = false",R)
        self.assertIn("p.CanQuery = false",R)
    def test_no_auto_scheduler(self):
        self.assertNotIn("RenderStepped",S+R)
        self.assertNotIn("Heartbeat",S+R)
    def test_cleanup(self):
        self.assertIn("self.model:Destroy()",R)
    def test_no_active_sounds(self):
        self.assertNotIn("SoundService",S+R)

if __name__=="__main__":
    unittest.main()
