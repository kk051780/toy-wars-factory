import importlib.util
from pathlib import Path
import unittest

spec=importlib.util.spec_from_file_location("opt",Path(__file__).with_name("verify_optional.py"))
opt=importlib.util.module_from_spec(spec)
spec.loader.exec_module(opt)

def fixture():
    meta={
        "schema":"P0D_GQ470_OPTIONAL32_SOURCE_PROFILE_V1",
        "canonical_branch":"rc/p0d-s1-kids-rc01",
        "profile":opt.PROFILE,"base_profile":"eggrumble_v3_31",
        "source_count":32,"base_count":31,"enabled_as_optional_profile":True,
        "default_selected":False,"production_enabled":False,
        "publish_authorized":False,"studio_only_original":True,
        "original_author":{"git_blob":opt.AUTHOR,
          "commit":"eb38aa60b69ed0bdd80fb7ea0dd10cf230345c20",
          "script_name":"EGGRUMBLE_EliminatedSpectate","class":"LocalScript"},
        "existing_prep_reuse":{"commit":"fed9cbb5680d40c68a2e1395e9b84276d7868fb9"},
        "current_selected31":"AUTO_SOURCE_EXACT_CURRENT_CANONICAL31_PLACE",
        "current_selected31_resolver":"rc_fastlane/quality_spectator32_optional/resolve_current31.py",
        "base_official_head":"7b3e055bae93ea71a89f981c4e78e8ab72996ae9"}
    active={"active_profile":"rich51","source_profiles":{
        "eggrumble_v3_31":{"source_count":31},
        opt.PROFILE:{"source_count":32,"default_selected":False,
                     "production_enabled":False,
                     "source_manifest":"rc_fastlane/EGGRUMBLE_V3_SPECTATE32_OPTIONAL.json"}}}
    flags={"FLAG_"+str(i):True for i in range(32)}
    flags.update(dict.fromkeys(["LOBBY_QUEUE_ETA_615","MATCH_DEADLINE_DRAW_499",
                "BEAST_REAL_ESCORT_618","ZOMBIE_GUARD_CASTLE_LEASH_582",
                "ITEM_CURRENT_SESSION_525","BOT_SIEGE_TARGET_PACING_527",
                "POSTWIN_LATE_CARRIER_DEATH_FREEZE_509",
                "GQ81_CONFIRMED_HIT_042_V3_PORT_20261117"],True))
    base={"profile":"eggrumble_v3_31","source_count":31,"feature_flags":flags}
    return meta,active,base

class Optional32ContractTests(unittest.TestCase):
    def test_current_studio_only_optional_is_valid(self):
        self.assertEqual(opt.contract(*fixture()),40)

    def test_never_auto_enable_or_publish(self):
        for field in ("default_selected","production_enabled","publish_authorized"):
            m,a,b=fixture()
            m[field]=True
            with self.assertRaisesRegex(ValueError,"RED_GQ470"): opt.contract(m,a,b)

    def test_never_replace_primary_s1_or_v3_31(self):
        m,a,b=fixture()
        a["active_profile"]=opt.PROFILE
        with self.assertRaises(ValueError): opt.contract(m,a,b)
        m,a,b=fixture()
        a["source_profiles"]["eggrumble_v3_31"]["source_count"]=32
        with self.assertRaises(ValueError): opt.contract(m,a,b)

    def test_author_blob_and_current_feature_fences(self):
        m,a,b=fixture()
        m["original_author"]["git_blob"]="0"*40
        with self.assertRaises(ValueError): opt.contract(m,a,b)
        for f in ("LOBBY_QUEUE_ETA_615","MATCH_DEADLINE_DRAW_499",
                  "BEAST_REAL_ESCORT_618","ZOMBIE_GUARD_CASTLE_LEASH_582",
                  "ITEM_CURRENT_SESSION_525","BOT_SIEGE_TARGET_PACING_527",
                  "POSTWIN_LATE_CARRIER_DEATH_FREEZE_509","GQ81_CONFIRMED_HIT_042_V3_PORT_20261117"):
            m,a,b=fixture();b["feature_flags"][f]=False
            with self.assertRaises(ValueError): opt.contract(m,a,b)

    def test_cannot_select_previous_wall_only_31_or_drop_hit_port(self):
        m,a,b=fixture()
        m["current_selected31"]="artifacts/gq515_official_select/GQ522_WALL_SELECTED31.project.json"
        with self.assertRaisesRegex(ValueError,"RED_GQ470"):opt.contract(m,a,b)
        m,a,b=fixture()
        b["feature_flags"]["GQ81_CONFIRMED_HIT_042_V3_PORT_20261117"]=False
        with self.assertRaisesRegex(ValueError,"RED_GQ470"):opt.contract(m,a,b)

    def test_no_false_32_if_script_count_drifted(self):
        m,a,b=fixture();m["source_count"]=31
        with self.assertRaises(ValueError):opt.contract(m,a,b)

if __name__=="__main__":
    unittest.main()
