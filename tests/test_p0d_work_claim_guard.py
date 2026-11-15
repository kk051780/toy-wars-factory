import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from p0d_work_claim_guard import check

H = "a" * 40
B = "b" * 40
NOW = datetime(2026, 11, 15, 0, 0, tzinfo=timezone.utc)


def row(claim="CLAIM-1", feat="ART-CASTLE", owner="PREP-ONE", resources=None, paths=None, expires="2026-11-16T00:00:00Z"):
    return {"claim_id": claim, "feature_id": feat, "owner": owner, "resources": resources or ["ART-CASTLE"],
            "target_paths": paths or ["releases/P0D_S1_KIDS_RC01/src/server/World*.luau"],
            "state": "GRANTED", "expires_at": expires}


def registry(rows=None):
    return {"schema": "P0D_EXCLUSIVE_CLAIMS_V1", "aliases": {"CASTLE_3D": "ART_CASTLE", "WORLD_CASTLE": "ART_CASTLE",
            "SEA_BIOME": "ART_SEA"}, "claims": rows if rows is not None else [row()]}


def cand(**kwargs):
    return {**{"claim_id": "CLAIM-1", "feature_id": "ART-CASTLE", "owner": "PREP-ONE",
            "resources": ["WORLD_CASTLE"], "source_head": B, "base_rc": H}, **kwargs}


PATH = ["releases/P0D_S1_KIDS_RC01/src/server/WorldArt.luau"]


class ClaimGuardTests(unittest.TestCase):
    def test_authorized_scope(self):
        a = check(registry(), cand(), PATH, H, NOW)
        self.assertEqual(a["result"], "CLAIM_SCOPE_PASS_NOT_RC_ADOPTION")

    def test_missing_claim_fails(self):
        with self.assertRaisesRegex(ValueError, "CLAIM_NOT_GRANTED"):
            check(registry([]), cand(), PATH, H, NOW)

    def test_different_owner_fails(self):
        with self.assertRaisesRegex(ValueError, "OWNER_MISMATCH"):
            check(registry(), cand(owner="PREP-TWO"), PATH, H, NOW)

    def test_same_feature_claim_conflict_fails(self):
        r = registry([row(), row(claim="CLAIM-2", owner="PREP-TWO", paths=["other/path.luau"])])
        with self.assertRaisesRegex(ValueError, "REGISTRY_CONFLICT"):
            check(r, cand(), PATH, H, NOW)

    def test_different_alias_but_same_resource_fails(self):
        r = registry([row(), row(claim="CLAIM-2", feat="DIFFERENT", owner="PREP-TWO", resources=["CASTLE_3D"], paths=["other/path.luau"])])
        with self.assertRaisesRegex(ValueError, "REGISTRY_CONFLICT"):
            check(r, cand(), PATH, H, NOW)

    def test_overlapping_paths_block_different_features(self):
        r = registry([row(), row(claim="CLAIM-2", feat="ART-SEA", owner="PREP-TWO", resources=["ART-SEA"], paths=PATH)])
        with self.assertRaisesRegex(ValueError, "REGISTRY_CONFLICT"):
            check(r, cand(), PATH, H, NOW)

    def test_distinct_features_parallel(self):
        r = registry([row(), row(claim="CLAIM-2", feat="ART-SEA", owner="PREP-TWO", resources=["ART-SEA"], paths=["releases/P0D_S1_KIDS_RC01/src/client/WaterArt.luau"])])
        self.assertEqual(check(r, cand(), PATH, H, NOW)["changed_files"], 1)

    def test_expired_claim_never_auto_reassign(self):
        r = registry([row(expires="2026-11-14T00:00:00Z")])
        with self.assertRaisesRegex(ValueError, "STALE_CLAIM"):
            check(r, cand(), PATH, H, NOW)

    def test_changed_file_outside_scope(self):
        with self.assertRaisesRegex(ValueError, "CHANGED_FILES_EXCEED_GRANT"):
            check(registry(), cand(), PATH + ["src/server/Game.server.luau"], H, NOW)

    def test_unreserved_resource(self):
        with self.assertRaisesRegex(ValueError, "RESOURCE_SCOPE_EXCEEDS_GRANT"):
            check(registry(), cand(resources=["ART-SEA"]), PATH, H, NOW)

    def test_old_rc_base_fails(self):
        with self.assertRaisesRegex(ValueError, "STALE_RC_BASE"):
            check(registry(), cand(base_rc=B), PATH, H, NOW)

    def test_no_diff_file_list_fails(self):
        with self.assertRaisesRegex(ValueError, "MISSING_CHANGED_PATHS"):
            check(registry(), cand(), [], H, NOW)

    def test_duplicate_claim_id_fails(self):
        r = registry([row(), row(claim="CLAIM-1", feat="ART-SEA", resources=["ART-SEA"], paths=["other/path.luau"])])
        with self.assertRaisesRegex(ValueError, "DUPLICATE_CLAIM_ID"):
            check(r, cand(), PATH, H, NOW)

    def test_malicious_path_fails(self):
        with self.assertRaisesRegex(ValueError, "INVALID_TARGET_PATH"):
            check(registry(), cand(), ["../../secrets.txt"], H, NOW)

    def test_closed_claim_does_not_authorize_candidate(self):
        r = registry([{**row(), "state": "RC_INTEGRATED"}])
        with self.assertRaisesRegex(ValueError, "CLAIM_NOT_GRANTED"):
            check(r, cand(), PATH, H, NOW)

    def test_glob_overlap_is_conservative(self):
        r = registry([row(), row(claim="CLAIM-2", feat="ART-SEA", resources=["ART-SEA"], paths=["releases/P0D_S1_KIDS_RC01/src/server/*.luau"])])
        with self.assertRaisesRegex(ValueError, "REGISTRY_CONFLICT"):
            check(r, cand(), PATH, H, NOW)


if __name__ == "__main__":
    unittest.main()
