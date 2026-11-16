import importlib.util
import pathlib
import unittest

ROOT=pathlib.Path(__file__).resolve().parents[3]
HERE=pathlib.Path(__file__).resolve().parents[1]
SRC=ROOT/"handoffs/P0D-PQG-SEVEN-HERO-PLAYABLE-20261116/EGGRUMBLE_NeutralStoneGiant.luau"
spec=importlib.util.spec_from_file_location("stomp",HERE/"apply_stomp_los.py")
stomp=importlib.util.module_from_spec(spec)
spec.loader.exec_module(stomp)


class SourceTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw=SRC.read_bytes()
        cls.original=cls.raw.decode("utf-8")
        cls.patched=stomp.patch(cls.original)

    def test_author_blob_pinned(self):
        self.assertEqual(stomp.blob_sha(self.raw),stomp.AUTHOR_SHA)

    def test_idempotent_denies(self):
        with self.assertRaisesRegex(AssertionError,"already patched"):
            stomp.patch(self.patched)

    def test_exact_minimal_delta(self):
        self.assertEqual(self.patched.replace(stomp.HELPER,"",1).replace(stomp.HIT_PATCH,stomp.HIT_ANCHOR,1),self.original)
        self.assertEqual(self.patched.count("h:TakeDamage(28)"),1)

    def test_real_wall_los_server_only(self):
        self.assertIn("params.RespectCanCollide=true",self.patched)
        self.assertIn("workspace:Raycast(origin,delta,params)==nil",self.patched)
        self.assertIn("stompVisible(model,at,c,root)",self.patched)
        self.assertIn("params.FilterDescendantsInstances={model,character}",self.patched)

    def test_preserve_phase_and_telegraph_and_attacker(self):
        for text in ("sessionActive()","authorized(player)","task.wait(2)","if d<=11","math.abs(root.Position.Y-at.Y)<=8","h:TakeDamage(28)","options.onDefeat"):
            self.assertIn(text,self.patched)

    def test_mutant_without_damage_guard_fails(self):
        bad=self.original.replace("h:TakeDamage(28)","h:TakeDamage(48)",1)
        with self.assertRaises(AssertionError):
            stomp.patch(bad)

    def test_mutant_changed_stomp_anchor_fails(self):
        bad=self.original.replace("if d<=11 and", "if d<=14 and",1)
        with self.assertRaises(AssertionError):
            stomp.patch(bad)

    def test_not_touch_other_sources(self):
        self.assertNotIn("RemoteEvent",stomp.HELPER)
        self.assertNotIn("DataStore",stomp.HELPER)
        self.assertNotIn("SetAttribute",stomp.HELPER)


if __name__=="__main__":
    unittest.main()
