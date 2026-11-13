"""Starfall Path: isolated source lock, independent OFF rollback and no duplicate writers.

Native compiler and Rojo SourceExact are separately run in GitHub Actions.
These Python tests are not Roblox engine/physics or real Studio tests.
"""
import json
import tempfile
import unittest
from pathlib import Path
import apply_star_path as star

class StarPathIntegration(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.dist=Path(self.temp.name)
        src=self.dist/"src"/"server"
        src.mkdir(parents=True)
        for name in ("Game.server.luau","WCS_CrystalCanyon.server.luau",
                     "SevenJobsRules.luau","EggRelayPolicy.luau"):
            (src/name).write_text("-- original "+name+"\n",encoding="utf8")
        for i in range(56):
            (src/("Stable%02d.luau"%i)).write_text("-- original%d\n"%i,encoding="utf8")
        self.original=star.sources(self.dist)
        assert len(self.original)==60
        pins={p:star.blob(v) for p,v in self.original.items()}
        self.source_lock={
            "total_scripts":60,"blobs":pins,
            "rc_wcs_f01_c01_overlay":{"id":"WCS_F01_C01"},
            "rc_seven_jobs_pve_overlay":{"id":"SEVEN_JOBS_PVE_V1"},
            "relay_classic_preview":{"feature_id":"EGG_RELAY_CLASSIC_V1"}
        }
        (self.dist/"SOURCE_LOCK.json").write_text(json.dumps(self.source_lock),encoding="utf8")
        (self.dist/"RC_FEATURE_LOCK.json").write_text(json.dumps({
            "total_sources":60,"source_gitblobs":pins,"feature_flags":{"EGG_RELAY_CLASSIC_V1":True}}),encoding="utf8")
        self.project={"tree":{
            "ServerScriptService":{"TrapRaidersS1":{"$path":"src/server"}},
            "ServerStorage":{
                "$className":"ServerStorage",
                "$attributes":{"P0D_RC_ENABLE_WCS_F01_C01":True},
                "P0D_RC_ENABLE_EGG_RELAY_CLASSIC":{"$className":"BoolValue","$properties":{"Value":True}}
            }
        }}
        (self.dist/"default.project.json").write_text(json.dumps(self.project),encoding="utf8")
    def test_real_author_script_pinned(self):
        self.assertEqual(star.blob(star.SOURCE.read_bytes()),star.SOURCE_BLOB)
        self.assertIn("not occupied()",star.SOURCE.read_text("utf8"))
    def test_integrates_just_one_studio_path_without_other_writes(self):
        self.assertTrue(star.apply(self.dist,"rich51",True))
        after=star.sources(self.dist)
        self.assertEqual(len(after),61)
        self.assertEqual({p:after[p] for p in self.original},self.original)
        self.assertEqual(after[star.DEST],star.SOURCE.read_bytes())
        project=json.loads((self.dist/"default.project.json").read_text("utf8"))
        self.assertTrue(project["tree"]["ServerStorage"]["$attributes"][star.RUNTIME_ATTRIBUTE])
        self.assertEqual(json.loads((self.dist/"SOURCE_LOCK.json").read_text("utf8"))["total_scripts"],61)
        self.assertEqual(json.loads((self.dist/"RC_FEATURE_LOCK.json").read_text("utf8"))["total_sources"],61)
    def test_off_preserves_exact_original60(self):
        before=(self.dist/"default.project.json").read_bytes()
        self.assertFalse(star.apply(self.dist,"rich51",False))
        self.assertEqual(star.sources(self.dist),self.original)
        self.assertEqual((self.dist/"default.project.json").read_bytes(),before)
    def test_fallback_profiles_never_add(self):
        self.assertFalse(star.apply(self.dist,"rich47",True))
        self.assertFalse(star.apply(self.dist,"legacy21",True))
        self.assertEqual(star.sources(self.dist),self.original)
    def test_duplicate_source_refused(self):
        self.assertTrue(star.apply(self.dist,"rich51",True))
        with self.assertRaises(AssertionError):
            star.apply(self.dist,"rich51",True)
    def test_original_source_drift_refused_before_write(self):
        lock=self.dist/"SOURCE_LOCK.json"
        data=json.loads(lock.read_text("utf8"));data["blobs"]["server/Game.server.luau"]="bad"
        lock.write_text(json.dumps(data),encoding="utf8")
        with self.assertRaisesRegex(AssertionError,"RC60_SOURCE_DRIFT"):
            star.apply(self.dist,"rich51",True)
        self.assertEqual(star.sources(self.dist),self.original)
    def test_missing_previous_wcs_refused(self):
        path=self.dist/"src/server/WCS_CrystalCanyon.server.luau"
        path.unlink()
        with self.assertRaises(AssertionError):
            star.apply(self.dist,"rich51",True)
        self.assertNotIn(star.DEST,star.sources(self.dist))
    def test_missing_boot_flag_source_defaults_off(self):
        content=star.SOURCE.read_text("utf8")
        self.assertIn('GetAttribute("P0D_RC_ENABLE_STARRY_PATH_V1")~=true',content)
        self.assertNotIn('GetAttribute("P0D_RC_ENABLE_STARRY_PATH_V1")==false',content)
        self.assertIn('if not RunService:IsStudio() then return end',content)
    def test_safety_no_damage_reward_save_remote(self):
        content=star.SOURCE.read_text("utf8")
        for term in ("TakeDamage(","UpdateAsync(","GetDataStore(","RemoteEvent",
                     "OnServerEvent:Connect(","MarketplaceService","horde:hit("):
            self.assertNotIn(term,content)
    def test_fails_on_duplicate_boot_attr(self):
        project=self.dist/"default.project.json"
        data=json.loads(project.read_text("utf8"))
        data["tree"]["ServerStorage"]["$attributes"][star.RUNTIME_ATTRIBUTE]=False
        project.write_text(json.dumps(data),encoding="utf8")
        with self.assertRaisesRegex(AssertionError,"DUPLICATE_BOOT_ATTRIBUTE"):
            star.apply(self.dist,"rich51",True)
        self.assertEqual(star.sources(self.dist),self.original)

if __name__=="__main__":
    unittest.main()
