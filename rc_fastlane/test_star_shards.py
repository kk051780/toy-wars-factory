"""Private62 six-shard session quest: deterministic source admission and safety tests.

Does NOT claim actual Roblox Studio engine/2client success.
"""
import json
import tempfile
import unittest
from pathlib import Path
import apply_star_shards as shard

class StarShardsAdmission(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.dist=Path(self.temp.name)
        server=self.dist/"src"/"server"
        server.mkdir(parents=True)
        names=("Game.server.luau","WCS_CrystalCanyon.server.luau",
               "SevenJobsRules.luau","EggRelayPolicy.luau")
        for name in names:
            (server/name).write_text("-- fixture "+name+"\n",encoding="utf8")
        (server/"StarfallPath.server.luau").write_bytes(
            (Path(shard.__file__).resolve().parent/"features/star_path/StarfallPath.server.luau").read_bytes())
        for i in range(56):
            (server/("Stable_%02d.luau"%i)).write_text("-- stable source "+str(i)+"\n",encoding="utf8")
        self.before=shard.sources(self.dist)
        assert len(self.before)==61
        pins={p:shard.blob(v) for p,v in sorted(self.before.items())}
        self.lock={
            "total_scripts":61,"blobs":pins,
            "rc_wcs_f01_c01_overlay":{"id":"WCS_F01_C01"},
            "rc_seven_jobs_pve_overlay":{"id":"SEVEN_JOBS_PVE_V1"},
            "relay_classic_preview":{"feature_id":"EGG_RELAY_CLASSIC_V1"},
            "rc_star_path_overlay":{"id":"STARRY_PATH_V1"}
        }
        (self.dist/"SOURCE_LOCK.json").write_text(json.dumps(self.lock),encoding="utf8")
        (self.dist/"RC_FEATURE_LOCK.json").write_text(json.dumps({
            "total_sources":61,"source_gitblobs":pins,
            "feature_flags":{"STARRY_PATH_V1":True}}),encoding="utf8")
        self.cfg={"tree":{
            "ServerScriptService":{"TrapRaidersS1":{"$path":"src/server"}},
            "ServerStorage":{
                "$className":"ServerStorage",
                "$attributes":{"P0D_RC_ENABLE_WCS_F01_C01":True,
                               "P0D_RC_ENABLE_STARRY_PATH_V1":True},
                "P0D_RC_ENABLE_EGG_RELAY_CLASSIC":{"$className":"BoolValue","$properties":{"Value":True}}
            }
        }}
        (self.dist/"default.project.json").write_text(json.dumps(self.cfg),encoding="utf8")

    def test_on_adds_one_shard_script_and_preserves_all_real_prior_script_bodies(self):
        self.assertTrue(shard.apply(self.dist,"rich51",True))
        after=shard.sources(self.dist)
        self.assertEqual(len(after),62)
        self.assertEqual({p:after[p] for p in self.before},self.before)
        self.assertEqual(after[shard.DEST],shard.SOURCE.read_bytes())
        cfg=json.loads((self.dist/"default.project.json").read_text("utf8"))
        self.assertIs(cfg["tree"]["ServerStorage"]["$attributes"][shard.ATTR],True)
        self.assertEqual(json.loads((self.dist/"SOURCE_LOCK.json").read_text("utf8"))["total_scripts"],62)
        self.assertEqual(json.loads((self.dist/"RC_FEATURE_LOCK.json").read_text("utf8"))["total_sources"],62)

    def test_off_preserves_every_byte_of_original_61_and_project_and_locks(self):
        paths=[self.dist/"default.project.json",self.dist/"SOURCE_LOCK.json",self.dist/"RC_FEATURE_LOCK.json"]
        before=[p.read_bytes() for p in paths]
        self.assertFalse(shard.apply(self.dist,"rich51",False))
        self.assertEqual(shard.sources(self.dist),self.before)
        self.assertEqual([p.read_bytes() for p in paths],before)

    def test_fallback_never_adds_to_rich47_or_legacy(self):
        self.assertFalse(shard.apply(self.dist,"rich47",True))
        self.assertFalse(shard.apply(self.dist,"legacy21",True))
        self.assertEqual(shard.sources(self.dist),self.before)

    def test_second_admission_refused(self):
        self.assertTrue(shard.apply(self.dist,"rich51",True))
        with self.assertRaises(AssertionError):
            shard.apply(self.dist,"rich51",True)

    def test_changed_old_game_lock_refused(self):
        p=self.dist/"SOURCE_LOCK.json"
        x=json.loads(p.read_text("utf8"))
        x["blobs"]["server/Game.server.luau"]="bad"
        p.write_text(json.dumps(x),encoding="utf8")
        with self.assertRaisesRegex(AssertionError,"SHARDS_PREVIOUS_SOURCE_LOCK_DRIFT"):
            shard.apply(self.dist,"rich51",True)
        self.assertEqual(shard.sources(self.dist),self.before)

    def test_changed_original_star_script_refused(self):
        p=self.dist/"src/server/StarfallPath.server.luau"
        p.write_text("-- malicious star overwrite\n",encoding="utf8")
        with self.assertRaisesRegex(AssertionError,"STAR_PARENT_SOURCE_DRIFT"):
            shard.apply(self.dist,"rich51",True)
        self.assertFalse((self.dist/"src"/shard.DEST).exists())

    def test_missing_original_star_level_refused(self):
        (self.dist/"src/server/StarfallPath.server.luau").unlink()
        with self.assertRaises(AssertionError):
            shard.apply(self.dist,"rich51",True)

    def test_missing_boot_attribute_refused_without_writing(self):
        p=self.dist/"default.project.json"
        obj=json.loads(p.read_text("utf8"))
        del obj["tree"]["ServerStorage"]["$attributes"]["P0D_RC_ENABLE_STARRY_PATH_V1"]
        p.write_text(json.dumps(obj),encoding="utf8")
        with self.assertRaises(AssertionError):
            shard.apply(self.dist,"rich51",True)
        self.assertEqual(shard.sources(self.dist),self.before)

    def test_duplicate_shard_boot_flag_refused(self):
        p=self.dist/"default.project.json"
        obj=json.loads(p.read_text("utf8"))
        obj["tree"]["ServerStorage"]["$attributes"][shard.ATTR]=False
        p.write_text(json.dumps(obj),encoding="utf8")
        with self.assertRaisesRegex(AssertionError,"SHARDS_DUPLICATE_RUNTIME_FLAG"):
            shard.apply(self.dist,"rich51",True)
        self.assertEqual(shard.sources(self.dist),self.before)

    def test_feature_lock_drift_refused(self):
        p=self.dist/"RC_FEATURE_LOCK.json"
        x=json.loads(p.read_text("utf8"))
        x["total_sources"]=99
        p.write_text(json.dumps(x),encoding="utf8")
        with self.assertRaisesRegex(AssertionError,"SHARDS_PREVIOUS_FEATURE_LOCK_DRIFT"):
            shard.apply(self.dist,"rich51",True)
        self.assertEqual(shard.sources(self.dist),self.before)

    def test_collector_waits_longer_than_starfall_actual_boot_budget(self):
        import re
        root=Path(shard.__file__).resolve().parent
        wcs=(root/"features/wcs_f01_c01/WCS_CrystalCanyon.server.luau").read_text("utf8")
        bridge=(root/"features/star_path/StarfallPath.server.luau").read_text("utf8")
        collector=shard.SOURCE.read_text("utf8")
        waits=[r'arena=Workspace:WaitForChild\("TRAP_RAIDERS_S1",(\d+)\)',
               r'sky=arena:WaitForChild\("H1_FUN_WORLD",(\d+)\)',
               r'sky:WaitForChild\("SKY_WALKWAY",(\d+)\)']
        wcs_budget=0
        for pattern in waits:
            matches=re.findall(pattern,wcs)
            self.assertEqual(len(matches),1)
            wcs_budget+=int(matches[0])
        start=re.findall(r'Workspace:WaitForChild\("P0D_CrystalCanyonAnchor",(\d+)\)',bridge)
        canyon=re.findall(r'Workspace:WaitForChild\("P0D_WCS_CrystalCanyon",(\d+)\)',bridge)
        ready=re.findall(r'canyon:WaitForChild\("ShortcutBridge",(\d+)\)',bridge)
        collector_wait=re.findall(r'Workspace:WaitForChild\("P0D_STARRY_PATH",(\d+)\)',collector)
        self.assertEqual((len(start),len(canyon),len(ready),len(collector_wait)),(1,1,1,1))
        self.assertGreaterEqual(int(start[0]),wcs_budget+5)
        self.assertGreaterEqual(int(collector_wait[0]),int(start[0])+int(canyon[0])+int(ready[0])+10)
        self.assertEqual(shard.PRIOR_STAR_BLOB,shard.blob(bridge.encode("utf8")))

    def test_script_native_policy_markers_and_server_authority(self):
        raw=shard.SOURCE.read_bytes()
        self.assertEqual(shard.blob(raw),shard.SOURCE_GIT_BLOB)
        txt=raw.decode("utf8")
        self.assertIn('-- BEGIN_P0D_STAR_SHARDS_POLICY',txt)
        self.assertIn('-- END_P0D_STAR_SHARDS_POLICY',txt)
        self.assertIn('local locations={1,3,5,6,8,10}',txt)
        self.assertIn('local TOTAL=6',txt)
        self.assertIn('if not stone.CanCollide then return end',txt)
        self.assertIn('stage:GetAttribute("PathOpen")~=true',txt)
        self.assertIn('if not RunService:IsStudio() then return end',txt)
        self.assertIn('GetAttribute("P0D_RC_ENABLE_STAR_SHARDS_V1")~=true',txt)
        for banned in ("UpdateAsync(","SetAsync(","TakeDamage(","Instance.new(\"RemoteEvent\")",
                       "MarketplaceService","GetDataStore(","OnServerEvent:Connect("):
            self.assertNotIn(banned,txt)

if __name__=="__main__":
    unittest.main()
