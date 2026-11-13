"""Offline WCS 57->58 exact-source integration unit + negative tests (NOT Studio physics)."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import apply_wcs_f01_c01 as wcs

class WCSIntegration(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.dist = Path(self.temp.name)
        src = self.dist / "src" / "server"
        src.mkdir(parents=True)
        (src / "Game.server.luau").write_text('-- original game\n',encoding="utf8")
        for i in range(56):
            (src / ("safe%02d.luau" % i)).write_text("-- original %d\n" % i,encoding="utf8")
        data=wcs.sources(self.dist)
        (self.dist/"SOURCE_LOCK.json").write_text(json.dumps({
            "total_scripts":57,"blobs":{p:wcs.git_blob(v) for p,v in data.items()},
            "rc_scout_species_overlay":{"id":"SCOUT_SPECIES_V1"}
        }),encoding="utf8")
        (self.dist/"RC_FEATURE_LOCK.json").write_text(json.dumps({
            "total_sources":57,"source_gitblobs":{p:wcs.git_blob(v) for p,v in data.items()},
            "feature_flags":{"SCOUT_SPECIES_V1":True}
        }),encoding="utf8")
        (self.dist/"default.project.json").write_text(json.dumps({
            "tree":{"ServerScriptService":{"TrapRaidersS1":{"$path":"src/server"}}}
        }),encoding="utf8")
        self.before=data

    def test_on_adds_exactly_one_and_preserves_game(self):
        self.assertTrue(wcs.apply(self.dist,"rich51",True))
        after=wcs.sources(self.dist)
        self.assertEqual(len(after),58)
        self.assertEqual({p:after[p] for p in self.before},self.before)
        self.assertEqual(after[wcs.DEST_REL],wcs.FEATURE_PATH.read_bytes())
        lock=json.loads((self.dist/"SOURCE_LOCK.json").read_text("utf8"))
        self.assertEqual(lock["total_scripts"],58)
        self.assertEqual(lock["blobs"],{p:wcs.git_blob(v) for p,v in after.items()})
        self.assertEqual(json.loads((self.dist/"RC_FEATURE_LOCK.json").read_text("utf8"))["total_sources"],58)

    def test_off_preserves_all_57(self):
        self.assertFalse(wcs.apply(self.dist,"rich51",False))
        self.assertEqual(wcs.sources(self.dist),self.before)

    def test_other_profiles_never_add_script(self):
        self.assertFalse(wcs.apply(self.dist,"rich47",True))
        self.assertFalse(wcs.apply(self.dist,"legacy21",True))
        self.assertEqual(wcs.sources(self.dist),self.before)

    def test_second_admission_fails_closed(self):
        self.assertTrue(wcs.apply(self.dist,"rich51",True))
        with self.assertRaises(AssertionError):
            wcs.apply(self.dist,"rich51",True)

    def test_drifted_source_lock_blocks_write(self):
        lockfile=self.dist/"SOURCE_LOCK.json"
        obj=json.loads(lockfile.read_text("utf8"));obj["blobs"]["server/Game.server.luau"]="deadbeef"
        lockfile.write_text(json.dumps(obj),encoding="utf8")
        with self.assertRaises(AssertionError):
            wcs.apply(self.dist,"rich51",True)
        self.assertEqual(wcs.sources(self.dist),self.before)

    def test_missing_sky_map_in_project_fails_closed(self):
        p=self.dist/"default.project.json"
        p.write_text(json.dumps({"tree":{"ServerScriptService":{}}}),encoding="utf8")
        with self.assertRaises(KeyError):
            wcs.apply(self.dist,"rich51",True)
        self.assertEqual(wcs.sources(self.dist),self.before)

    def test_author_blob_and_runtime_safety(self):
        raw=wcs.FEATURE_PATH.read_bytes()
        self.assertEqual(wcs.git_blob(raw),wcs.FEATURE_GIT_BLOB)
        s=raw.decode("utf8")
        self.assertIn('if not RunService:IsStudio() then',s)
        self.assertIn('ServerStorage:GetAttribute("P0D_RC_ENABLE_WCS_F01_C01")==false',s)
        self.assertIn("playerIsInGateClosureZone()",s)
        self.assertIn("nextOpenAllowed = os.clock() + REOPEN_COOLDOWN",s)
        self.assertNotIn("nextOpenAllowed = now + OPEN_SECONDS + REOPEN_COOLDOWN",s)

    def test_no_extra_game_remote_store_or_paid_writes(self):
        s=wcs.FEATURE_PATH.read_text("utf8")
        for forbidden in ('GetDataStore(', 'UpdateAsync(', 'Instance.new("RemoteEvent")',
                          'OnServerEvent:Connect(', 'horde:hit(', 'MarketplaceService',
                          'PromptProductPurchase(', 'TakeDamage('):
            self.assertNotIn(forbidden,s)
if __name__ == "__main__":
    unittest.main()
