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
    def test_authored_arena_bounds_and_original_seven_area_ownership(self):
        # Read exactly the pinned #482 author Game/BotActors, not a QA fantasy map.
        host=mod.HOST.read_text(encoding="utf-8")
        bots=(mod.AUTHOR/"EGGRUMBLE_BotActors.luau").read_text(encoding="utf-8")
        world=(HERE/"EGGRUMBLE_CarrierWorldTell.luau").read_text(encoding="utf-8")
        policy=(HERE/"EGGRUMBLE_CarrierTellPolicy.luau").read_text(encoding="utf-8")
        self.assertIn('worldX=mode=="TEAM" and -620 or 620',host)
        self.assertIn('Vector3.new(890,2,1050)',host)
        self.assertIn('floor=block(session.world,"TacticalBattlefield"',host)
        self.assertIn('label.StudsOffset=Vector3.new(0,3.3,0)',bots)
        self.assertIn('head=makePart(model,"Head",base.Position+Vector3.new(0,2.25,0)',bots)
        self.assertIn('session.world:FindFirstChild("TacticalBattlefield")',world)
        self.assertIn('Policy.inArenaXZ(',world)
        self.assertIn('if aiActor then 10.2 else 4',world)
        self.assertIn('Policy.ARENA_HALO_STUDS = 10',policy)
        self.assertNotIn('RemoteEvent',world)
        self.assertNotIn('TakeDamage',world)

    def test_policy_phase_egg_death_guards(self):
        src=(HERE/"EGGRUMBLE_CarrierTellPolicy.luau").read_text()
        for critical in ('phase ~= "ACTIVE"','winner ~= nil','avatarAlive ~= true','castle.alive ~= true','eggs >= 1','eggs <= Policy.MAX_CARRIED_EGGS','eggs%1 == 0'):
            self.assertIn(critical,src)

if __name__=="__main__":
    unittest.main()
