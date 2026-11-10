import copy
import importlib.util
import math
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("progress_view", ROOT / "reference" / "progress_view.py")
model = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(model)
JOBS = [f"job{i}" for i in range(1, 8)]


def fixture():
    return {"authority": "SERVER", "playerId": "p001", "matchId": "round7", "epoch": 5,
            "roundActive": True, "level": 3, "levelXp": 10, "levelRequiredXp": 40,
            "sessionOnly": True, "saved": False,
            "mastery": {id: {"level": 1, "xp": 7, "requiredXp": 20} for id in JOBS}}


SENTINEL = object()
def run(s=SENTINEL, *, viewer="p001", match="round7", epoch=5, jobs=None):
    return model.project(fixture() if s is SENTINEL else s, viewer, match, epoch, JOBS if jobs is None else jobs)


class ViewContract(unittest.TestCase):
    def assert_reject(self, s, code):
        value, error = run(s)
        self.assertIsNone(value)
        self.assertEqual(error, code)

    def test_happy_path(self):
        view, err = run()
        self.assertIsNone(err)
        self.assertEqual(view["levelLabel"], "Lv 3/25")
        self.assertEqual(view["levelFraction"], 0.25)
        self.assertEqual(len(view["jobs"]), 7)
        self.assertEqual(view["jobs"][0]["fraction"], 0.35)
        self.assertFalse(view["grantsGameplayStats"])

    def test_does_not_mutate_snapshot(self):
        s = fixture(); before = copy.deepcopy(s)
        v, e = run(s)
        self.assertIsNone(e); self.assertEqual(s, before)
        v["jobs"][0]["level"] = 5
        self.assertEqual(s["mastery"][JOBS[0]]["level"], 1)

    def test_level_max(self):
        s = fixture(); s.update(level=25, levelXp=0, levelRequiredXp=0)
        v,e = run(s)
        self.assertIsNone(e); self.assertTrue(v["maxLevel"]); self.assertEqual(v["levelFraction"],1)

    def test_mastery_max(self):
        s = fixture(); s["mastery"][JOBS[0]] = {"level":5,"xp":0,"requiredXp":0}
        v,e = run(s)
        self.assertIsNone(e); self.assertEqual(v["jobs"][0]["fraction"],1)

    def test_job_order_is_allowlist_order(self):
        rev = JOBS[::-1]
        v,e = run(jobs=rev)
        self.assertIsNone(e); self.assertEqual([j["jobId"] for j in v["jobs"]], rev)

    def test_session_saved_false(self):
        v,e = run(); self.assertTrue(v["sessionOnly"]); self.assertFalse(v["saved"])

    def test_saved_true_is_only_echo(self):
        s = fixture(); s["saved"] = True
        v,e = run(s)
        self.assertIsNone(e); self.assertTrue(v["saved"])

    def test_wrong_viewer(self):
        v,e = run(viewer="attacker")
        self.assertIsNone(v); self.assertEqual(e,"INVALID_SNAPSHOT_IDENTITY")

    def test_wrong_match(self):
        v,e = run(match="old")
        self.assertIsNone(v); self.assertEqual(e,"INVALID_SNAPSHOT_IDENTITY")

    def test_wrong_epoch(self):
        v,e = run(epoch=6)
        self.assertIsNone(v); self.assertEqual(e,"INVALID_SNAPSHOT_IDENTITY")

    def test_invalid_context(self):
        for viewer in ["", "a"*97, "x y", None]:
            v,e = run(viewer=viewer); self.assertEqual(e,"INVALID_CONTEXT")
        for epoch in [-1,True,0.5,float("inf")]:
            v,e = run(epoch=epoch); self.assertEqual(e,"INVALID_CONTEXT")

    def test_disallow_client_authority(self):
        s=fixture();s["authority"]="CLIENT"; self.assert_reject(s,"INVALID_SNAPSHOT_IDENTITY")

    def test_disallow_inactive_round(self):
        s=fixture();s["roundActive"]=False; self.assert_reject(s,"INVALID_SNAPSHOT_IDENTITY")

    def test_invalid_snapshots(self):
        for item in [None, [], 8, {"level": 3}]:
            v,e=run(item);self.assertEqual(e,"INVALID_SNAPSHOT_IDENTITY")

    def test_level_out_of_range(self):
        for level in [0,26,-2,1.5,True,float("nan")]:
            s=fixture();s["level"]=level;self.assert_reject(s,"INVALID_PROGRESSION")

    def test_invalid_level_progress(self):
        for xp,required in [(-1,10),(10,0),(10,10),(11,10),(0,-1),(float("nan"),1),(0,float("inf")),(True,10),(0,1_000_000_001)]:
            s=fixture();s["levelXp"]=xp;s["levelRequiredXp"]=required;self.assert_reject(s,"INVALID_LEVEL_XP")

    def test_level25_must_be_zero_zero(self):
        for xp,required in [(0,1),(2,0),(2,3)]:
            s=fixture();s.update(level=25,levelXp=xp,levelRequiredXp=required)
            self.assert_reject(s,"INVALID_LEVEL_XP")

    def test_job_allowlist_invalid(self):
        for jobs in [[], JOBS[:6], JOBS+["job8"], JOBS[:6]+[JOBS[0]], ["xx xx"]+JOBS[1:], [None]+JOBS[1:]]:
            v,e = run(jobs=jobs);self.assertIsNone(v);self.assertEqual(e,"INVALID_JOB_ALLOWLIST")

    def test_unknown_job(self):
        s=fixture();s["mastery"]["job8"]={"level":1,"xp":0,"requiredXp":20}
        self.assert_reject(s,"UNKNOWN_JOB")

    def test_missing_job(self):
        s=fixture();del s["mastery"][JOBS[1]];self.assert_reject(s,"INVALID_JOB_COUNT")

    def test_invalid_mastery(self):
        for value in [None, 3, {"level":-1,"xp":0,"requiredXp":3}, {"level":6,"xp":0,"requiredXp":3}, {"level":True,"xp":0,"requiredXp":3}]:
            s=fixture();s["mastery"][JOBS[1]]=value;self.assert_reject(s,"INVALID_MASTERY")

    def test_invalid_mastery_progress(self):
        for xp,required in [(-1,5),(5,5),(10,5),(0,0),(float("nan"),3),(0,-1)]:
            s=fixture();s["mastery"][JOBS[1]]={"level":2,"xp":xp,"requiredXp":required}
            self.assert_reject(s,"INVALID_MASTERY_XP")

    def test_mastery5_must_be_zero_zero(self):
        s=fixture();s["mastery"][JOBS[0]]={"level":5,"xp":1,"requiredXp":0}
        self.assert_reject(s,"INVALID_MASTERY_XP")

    def test_source_module_has_no_side_effect_apis(self):
        text=(ROOT/"src"/"ProgressViewModel.luau").read_text(encoding="utf-8")
        for term in ["DataStoreService", "RemoteEvent.new", "Instance.new", "UpdateAsync", "SetAsync", "grantXP", "Humanoid.Health", "MarketplaceService"]:
            self.assertNotIn(term, text)
        self.assertIn("return M", text)

    def test_no_weak_clamp_that_masks_bad_data(self):
        s=fixture();s["levelXp"]=500;s["levelRequiredXp"]=100
        self.assert_reject(s,"INVALID_LEVEL_XP")

    def test_stale_epoch_in_snapshot_rejected(self):
        s=fixture();s["epoch"]=4
        self.assert_reject(s,"INVALID_SNAPSHOT_IDENTITY")

    def test_luau_contract_pins(self):
        text=(ROOT/"src"/"ProgressViewModel.luau").read_text(encoding="utf-8")
        for symbol in ["snapshot.playerId ~= viewerId", "snapshot.matchId ~= expectedMatchId", "snapshot.epoch ~= expectedEpoch", "snapshot.roundActive ~= true", "snapshot.authority ~= \"SERVER\"", "validProgress", "maxLevel", "jobCount = 7", "grantsGameplayStats = false"]:
            self.assertIn(symbol,text)


if __name__ == "__main__":
    unittest.main()
