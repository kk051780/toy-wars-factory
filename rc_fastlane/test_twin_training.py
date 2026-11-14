"""Actual canonical64 TwinBiomes -> private65 session creature training acceptance.

These are source-lock and switch/negative tests, NOT live Roblox physics tests.
"""
import json
import tempfile
import unittest
from pathlib import Path
import apply_twin_training as training

class CreatureTrainingAdmission(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.dist=Path(tmp.name)
        server=self.dist/"src/server"
        server.mkdir(parents=True)
        base=Path(training.__file__).resolve().parent/"features/twin_biomes/TwinBiomes.server.luau"
        (server/"TwinBiomes.server.luau").write_bytes(base.read_bytes())
        (server/"Game.server.luau").write_text(
           "-- game fixture\nremote.OnServerEvent:Connect(function() end)\n",encoding="utf8")
        for i in range(62):
            (server/f"Stable_{i:02d}.luau").write_text("-- pinned "+str(i)+"\n",encoding="utf8")
        self.before=training.sources(self.dist)
        assert len(self.before)==64
        pins={p:training.blob(v) for p,v in sorted(self.before.items())}
        lock={"blobs":pins,"total_scripts":64,
             "rc_twin_biomes_overlay":{"id":"TWIN_BIOMES_4NPC_V1",
                                      "source_gitblob":training.BASE_BLOB}}
        features={"total_sources":64,"source_gitblobs":pins,
                  "feature_flags":{"TWIN_BIOMES_4NPC_V1":True}}
        cfg={"tree":{"ServerScriptService":{"TrapRaidersS1":{"$path":"src/server"}},
             "ServerStorage":{"$className":"ServerStorage",
                 "P0D_ENABLE_TWIN_BIOMES_V1":{"$className":"BoolValue","$properties":{"Value":True}}}}}
        (self.dist/"SOURCE_LOCK.json").write_text(json.dumps(lock),encoding="utf8")
        (self.dist/"RC_FEATURE_LOCK.json").write_text(json.dumps(features),encoding="utf8")
        (self.dist/"default.project.json").write_text(json.dumps(cfg),encoding="utf8")
        self.meta=[self.dist/x for x in ("SOURCE_LOCK.json","RC_FEATURE_LOCK.json","default.project.json")]

    def test_01_origin_actual_official_twin_author_pinned(self):
        self.assertEqual(training.blob(self.before[training.TWIN]),training.BASE_BLOB)
    def test_02_unchanged_old_build_when_training_switch_off(self):
        before=[p.read_bytes() for p in self.meta]
        self.assertFalse(training.apply(self.dist,"rich51",False))
        self.assertEqual(self.before,training.sources(self.dist))
        self.assertEqual(before,[p.read_bytes() for p in self.meta])
    def test_03_legacy_profiles_off_and_byte_exact(self):
        self.assertFalse(training.apply(self.dist,"rich47",True))
        self.assertFalse(training.apply(self.dist,"legacy21",True))
        self.assertEqual(self.before,training.sources(self.dist))
    def test_04_on_changes_exactly_one_body_and_adds_one_module(self):
        self.assertTrue(training.apply(self.dist,"rich51",True))
        after=training.sources(self.dist)
        self.assertEqual(len(after),65)
        self.assertEqual({p:after[p] for p in self.before if p!=training.TWIN},
                         {p:raw for p,raw in self.before.items() if p!=training.TWIN})
        self.assertEqual(after[training.TWIN],training.TRAINED.read_bytes())
        self.assertEqual(after[training.MODULE],training.POLICY.read_bytes())
    def test_05_on_locks_and_rojo_project_exact(self):
        previous=self.meta[-1].read_bytes()
        self.assertTrue(training.apply(self.dist,"rich51",True))
        self.assertEqual(self.meta[-1].read_bytes(),previous)
        pins={p:training.blob(v) for p,v in training.sources(self.dist).items()}
        a=json.loads(self.meta[0].read_text("utf8"))
        b=json.loads(self.meta[1].read_text("utf8"))
        self.assertEqual(a["total_scripts"],65)
        self.assertEqual(b["total_sources"],65)
        self.assertEqual(a["blobs"],pins)
        self.assertEqual(b["source_gitblobs"],pins)
        self.assertIs(b["feature_flags"][training.FEATURE],True)
    def test_06_missing_game_fails_without_writing(self):
        (self.dist/"src/server/Game.server.luau").unlink()
        with self.assertRaises(AssertionError): training.apply(self.dist,"rich51",True)
        self.assertFalse((self.dist/"src"/training.MODULE).exists())
    def test_07_edited_game_source_refused_before_mutation(self):
        (self.dist/"src/server/Game.server.luau").write_text(
            "remote.OnServerEvent:Connect(function() end)\n-- changed",encoding="utf8")
        with self.assertRaisesRegex(AssertionError,"SOURCE_LOCK_DRIFT"):
            training.apply(self.dist,"rich51",True)
    def test_08_edited_twin_source_refused(self):
        (self.dist/"src"/training.TWIN).write_text("-- unrecognized\n",encoding="utf8")
        with self.assertRaisesRegex(AssertionError,"OFFICIAL_TWIN_AUTHOR_SOURCE_DRIFT"):
            training.apply(self.dist,"rich51",True)
        self.assertFalse((self.dist/"src"/training.MODULE).exists())
    def test_09_missing_real_boot_flag_refused(self):
        x=json.loads(self.meta[2].read_text("utf8"))
        del x["tree"]["ServerStorage"]["P0D_ENABLE_TWIN_BIOMES_V1"]
        self.meta[2].write_text(json.dumps(x),encoding="utf8")
        with self.assertRaises(AssertionError):training.apply(self.dist,"rich51",True)
        self.assertEqual(training.sources(self.dist),self.before)
    def test_10_duplicate_training_refused(self):
        training.apply(self.dist,"rich51",True)
        with self.assertRaises(AssertionError):training.apply(self.dist,"rich51",True)
    def test_11_source_lock_fail_closed(self):
        x=json.loads(self.meta[0].read_text("utf8"))
        x["total_scripts"]=100
        self.meta[0].write_text(json.dumps(x),encoding="utf8")
        with self.assertRaisesRegex(AssertionError,"SOURCE_LOCK_DRIFT"):
            training.apply(self.dist,"rich51",True)
    def test_12_feature_lock_fail_closed(self):
        x=json.loads(self.meta[1].read_text("utf8"))
        x["total_sources"]=100
        self.meta[1].write_text(json.dumps(x),encoding="utf8")
        with self.assertRaisesRegex(AssertionError,"FEATURE_LOCK_DRIFT"):
            training.apply(self.dist,"rich51",True)
    def test_13_training_real_source_original_author_blob_pins(self):
        self.assertEqual(training.blob(training.TRAINED.read_bytes()),training.TRAINED_BLOB)
        self.assertEqual(training.blob(training.POLICY.read_bytes()),training.POLICY_BLOB)
        self.assertIn("awardPractice(player,info,npc,crest)",training.TRAINED.read_text("utf8"))
    def test_14_pure_policy_no_store_no_remote_no_payments(self):
        raw=training.POLICY.read_text("utf8")
        self.assertIn("local MAX_PRACTICE = 7",raw)
        self.assertIn("local REPEAT_WAIT_SECONDS = 20",raw)
        for bad in ("DataStoreService","UpdateAsync(","RemoteEvent","MarketplaceService","SetAttribute("):
            self.assertNotIn(bad,raw)
    def test_15_training_preserves_single_original_game_authority(self):
        self.assertTrue(training.apply(self.dist,"rich51",True))
        src=training.sources(self.dist)
        self.assertEqual(sum(k=="server/Game.server.luau" for k in src),1)
        self.assertEqual(src["server/Game.server.luau"],self.before["server/Game.server.luau"])
        self.assertNotIn("OnServerEvent:Connect(",src[training.TWIN].decode("utf8"))
    def test_16_client_security_and_session_only_evolution(self):
        raw=training.TRAINED.read_text("utf8")
        self.assertIn('player:SetAttribute("P0D_TwinEvolved_"..info.id,true)',raw)
        self.assertIn("practiceByPlayer[p] = nil",raw)
        self.assertIn("Training.effectSeconds(level)",raw)
        self.assertNotIn("GetDataStore(",raw)

if __name__=="__main__":
    unittest.main()
