"""Original canonical rich51 source-preservation and dual switch admission tests.

Must run AFTER tools/assemble_two_switches.py --assemble in a clean checkout.
These tests are static SOURCE tests, NOT actual Roblox engine / FUN tests.
"""
import json
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
from assemble_two_switches import BASE,DIST,OLD,NEW,scripts,gitblob
from patch_sky import transform

class DualSwitchSourceChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.old=scripts(BASE)
        cls.new=scripts(DIST)
        cls.lock=json.loads((DIST/"SOURCE_LOCK.json").read_text("utf8"))
    def test_count_51(self):
        self.assertEqual(len(self.old),51)
        self.assertEqual(len(self.new),51)
    def test_same_source_names(self):
        self.assertEqual(set(self.old),set(self.new))
    def test_changed_only_three(self):
        self.assertEqual(sorted(p for p in self.old if self.old[p]!=self.new[p]),sorted(NEW))
    def test_original_48_byte_unchanged(self):
        self.assertEqual(sum(self.old[k]==self.new[k] for k in self.old),48)
    def test_no_game_or_store_change(self):
        for name in ["server/Game.server.luau","server/PersistentHatchStore.luau",
                     "server/MusouHorde.luau"]:
            self.assertIn(name,self.old)
            self.assertEqual(self.old[name],self.new[name])
    def test_single_authoritative_game(self):
        self.assertEqual(sum(k=="server/Game.server.luau" for k in self.new),1)
        g=self.new["server/Game.server.luau"].decode("utf8")
        self.assertEqual(g.count('remote.OnServerEvent:Connect('),1)
        self.assertEqual(g.count('remote.Name = "TrapRaidersS1Remote"'),1)
    def test_sha_lock_includes_every_script(self):
        self.assertEqual(self.lock["blobs"],{p:gitblob(data) for p,data in self.new.items()})
    def test_original_and_new_github_blobs(self):
        for k,v in OLD.items():self.assertEqual(gitblob(self.old[k]),v)
        for k,v in NEW.items():self.assertEqual(gitblob(self.new[k]),v)
    def test_sky_startup_default_on(self):
        s=self.new["server/H1FunWorld.server.luau"].decode()
        self.assertIn('ServerStorage:GetAttribute("P0D_RC_ENABLE_H1_SKYV5")~=false',s)
        self.assertNotIn("GetAttributeChangedSignal",s)
    def test_sky_blocks_only_sky_routes(self):
        s=self.new["server/H1FunWorld.server.luau"].decode()
        a=s.index('if skyEnabled then\npath("SKY_RAMP_RED"')
        b=s.index('end -- early SKY_RAMP/WALKWAY parts only')
        sea=s.index('local sea=box("COSMETIC_SEA"')
        c=s.index('if skyEnabled then\n-- Ground-dock V5')
        d=s.index('end -- late SKY_GROUND_DOCK')
        creatures=s.index('local creatures=Instance.new("Folder")')
        self.assertTrue(a<b<sea<c<d<creatures)
        self.assertIn("SKY_WALKWAY",s[a:b])
        self.assertIn("SKY_FORT_ESCAPE_BLUE",s[c:d])
        self.assertIn("SEA_LOW_CAUSEWAY",s[sea:c])
    def test_v4_server_off_stops_xp_and_pads(self):
        s=self.new["server/V4TrainingBridge.server.luau"].decode()
        for phrase in ["ServerStorage:GetAttribute(FEATURE_KEY)~=false",
                       "showPreviewPads(enabled)","record.scheduler.lastTick=now",
                       "if not enabled then","ReplicatedStorage:SetAttribute(PUBLIC_KEY,enabled)"]:
            self.assertIn(phrase,s)
    def test_v4_client_fails_closed(self):
        s=self.new["client/V4TrialOverlay.client.luau"].decode()
        self.assertIn("gui.Enabled=ReplicatedStorage:GetAttribute(PUBLIC_KEY)==true",s)
        self.assertIn("GetAttributeChangedSignal(PUBLIC_KEY)",s)
    def test_changed_sources_have_no_new_authority(self):
        for key in NEW:
            s=self.new[key].decode()
            for forbidden in ["GetDataStore(","UpdateAsync(","OnServerEvent:Connect(",
                              "MarketplaceService","PromptProductPurchase("]:
                self.assertNotIn(forbidden,s)
    def test_negative_modified_original_sky_rejected(self):
        x=self.old["server/H1FunWorld.server.luau"]+b"\n-- a third party mutated source"
        with self.assertRaisesRegex(ValueError,"ORIGINAL_H1_WORLD_SOURCE_DRIFT"):
            transform(x)
    def test_replay_boot_only_sky_transform_deterministic(self):
        old=self.old["server/H1FunWorld.server.luau"]
        self.assertEqual(transform(old),self.new["server/H1FunWorld.server.luau"])
    def test_no_fake_publication_claim(self):
        self.assertFalse(self.lock["official_rc_adopted"])
        self.assertFalse(self.lock["paid"])
        self.assertFalse(self.lock["published"])
        self.assertEqual(self.lock["studio_2client"],"NOT_TESTED")
        self.assertFalse(self.lock["six_skill_persistence"])
    def test_rollback_pinned_to_prior_source(self):
        self.assertEqual(self.lock["rollback_source_commit"],
                         "79123d35cd7afdd5f4f9941675bc2d2cf382ac4e")

if __name__=="__main__":unittest.main()
