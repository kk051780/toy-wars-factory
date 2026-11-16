import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("carrier_composer",HERE/"compose.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

class TestCarrierWorldTell(unittest.TestCase):
    def test_source_composed_exact_only_additions(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)/"private"
            receipt = mod.compose(out)
            self.assertEqual(receipt["author_source_count"],21)
            self.assertEqual(receipt["private_source_count"],23)
            self.assertFalse(receipt["official_rc_integrated"])
            project=json.loads((out/"EGGRUMBLE_CARRIER_TELL_PRIVATE.project.json").read_text())
            server=project["tree"]["ServerScriptService"]
            self.assertIn("EGGRUMBLE_CarrierWorldTell",server)
            self.assertIn("EGGRUMBLE_CarrierTellPolicy",server)
            new=(out/"EGGRUMBLE_LobbyCastleModesPreview.server.luau").read_text()
            old=mod.HOST.read_text()
            restored = new.replace(mod.REQUIRE_ANCHOR+"\n"+mod.ADD_REQUIRE,mod.REQUIRE_ANCHOR,1)
            restored = restored.replace(mod.START_ANCHOR+"\n"+mod.ADD_START,mod.START_ANCHOR,1)
            self.assertEqual(restored,old)
            for label,sha in receipt["source_sha256"].items():
                path=out/server[label]["$path"] if label in server else out/project["tree"]["StarterPlayer"]["StarterPlayerScripts"][label]["$path"]
                self.assertEqual(hashlib.sha256(path.resolve().read_bytes()).hexdigest(),sha)
    def test_no_duplicate_slices_or_unsafe_events(self):
        src=(HERE/"EGGRUMBLE_CarrierWorldTell.luau").read_text()
        for banned in ("RemoteEvent","DataStore","TakeDamage","ProximityPrompt","Humanoid.WalkSpeed","while true do","BindToRenderStep"):
            self.assertNotIn(banned,src)
        self.assertIn("session.rules.castles",src)
        self.assertIn("session.world.Parent",src)
        self.assertIn("session.rules.winner",src)
        self.assertIn("task.wait(Policy.POLL_SECONDS)",src)
        self.assertIn("destroyRecord(record)",src)
    def test_policy_phase_egg_death_guards(self):
        src=(HERE/"EGGRUMBLE_CarrierTellPolicy.luau").read_text()
        for critical in ('phase ~= "ACTIVE"','winner ~= nil','avatarAlive ~= true','castle.alive ~= true','eggs >= 1','eggs <= Policy.MAX_CARRIED_EGGS','eggs%1 == 0'):
            self.assertIn(critical,src)

if __name__=="__main__":
    unittest.main()
