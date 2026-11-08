"""Local report boundary tests; do not promote to a trusted host receipt."""
import copy
from hashlib import sha256
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))
from market_source_preflight import preflight, Rejected
from market_observation_bridge import prepare_observation_bundle, observation_bundle_from_report


def packet(count=1):
    def item(i):
        return {
            "claim_id":f"CLAIM_{i:03}", "source_type":"YOUTUBE_CREATOR",
            "url":f"https://youtu.be/{i:011d}", "published_at":"2026-10-10",
            "checked_at":"2026-11-09T08:00:00Z",
            "claim":f"Creator claimed this claim number {i}",
            "claim_kind":"TITLE_ONLY", "limitation":"No direct source transcript.",
            "hypothesis_id":"H_001", "metric":None,
            "transcript_verified":False,
        }
    return {"schema":"MARKET_SOURCE_PREFLIGHT_V1", "as_of":"2026-11-09T09:00:00Z",
            "records":[item(i) for i in range(count)]}


def signed_local(report):
    # Deliberately shows a caller can rehash untrusted contents; still NOT authority.
    report["claims_sha256"]=sha256(json.dumps(report["claims"],ensure_ascii=False,
       sort_keys=True,separators=(",", ":"),allow_nan=False).encode()).hexdigest()
    return report


class BridgeTests(unittest.TestCase):
    def assertRejected(self, report):
        with self.assertRaises(Rejected):
            observation_bundle_from_report(report)

    def test_input_through_bridge(self):
        result=prepare_observation_bundle(packet())
        self.assertEqual(result["stage"],"PRE_VALIDATED_LOCAL_ONLY")
        self.assertEqual(result["authenticity"],"UNVERIFIED")
        self.assertEqual(result["write_approval"],False)
        self.assertEqual(result["claim_ids"],["CLAIM_000"])
        self.assertEqual(set(result["observations"][0]), {"source_url","checked_at","observed_fact",
                   "limitation","source_kind","published_at"})

    def test_pipeline_observation_limit_20_ok(self):
        result=prepare_observation_bundle(packet(20))
        self.assertEqual(len(result["observations"]),20)

    def test_pipeline_observation_limit_21_fails(self):
        with self.assertRaises(Rejected):prepare_observation_bundle(packet(21))

    def test_tamper_digest_fails(self):
        report=preflight(packet())
        report["claims"][0]["observation"]["observed_fact"]="fake"
        self.assertRejected(report)

    def test_caller_rehash_does_not_authorize(self):
        report=preflight(packet())
        report["claims"][0]["observation"]["observed_fact"]="unverified text"
        result=observation_bundle_from_report(signed_local(report))
        self.assertEqual(result["authenticity"],"UNVERIFIED")
        self.assertFalse(result["write_approval"])

    def test_forged_authority_fails(self):
        r=preflight(packet());r["authority"]="TRUSTED_EXECUTOR"
        self.assertRejected(r)

    def test_forged_actions_fails(self):
        r=preflight(packet());r["authorized_actions"]=["WRITE_MAIN"]
        self.assertRejected(r)

    def test_forged_host_authentication_fails_even_with_digest(self):
        r=preflight(packet());r["claims"][0]["host_authenticated"]=True
        self.assertRejected(signed_local(r))

    def test_forged_player_effect_fails_even_with_digest(self):
        r=preflight(packet());r["claims"][0]["player_effect_proven"]=True
        self.assertRejected(signed_local(r))

    def test_forged_transcript_fails_even_with_digest(self):
        r=preflight(packet());r["claims"][0]["transcript_verified"]=True
        self.assertRejected(signed_local(r))

    def test_wrong_classification_fails_even_with_digest(self):
        r=preflight(packet());r["claims"][0]["observation"]["source_kind"]="PRIMARY_OFFICIAL"
        self.assertRejected(signed_local(r))

    def test_extra_fields_fails(self):
        r=preflight(packet());r["claims"][0]["owner_approval"]=True
        self.assertRejected(signed_local(r))

    def test_duplicate_ids_fails(self):
        r=preflight(packet(2));r["claims"][1]["claim_id"]="CLAIM_000"
        self.assertRejected(signed_local(r))

    def test_unsorted_ids_fails(self):
        r=preflight(packet(2));r["claims"].reverse()
        self.assertRejected(signed_local(r))

    def test_forged_local_url_rehashed_is_rejected(self):
        r=preflight(packet());r["claims"][0]["observation"]["source_url"]="https://127.0.0.1/"
        self.assertRejected(signed_local(r))

    def test_forged_lookalike_youtube_url_rejected(self):
        r=preflight(packet());r["claims"][0]["observation"]["source_url"]="https://youtube.com.attacker.example/watch?v=00000000000"
        self.assertRejected(signed_local(r))

    def test_forged_unstandard_youtube_url_rejected(self):
        r=preflight(packet());r["claims"][0]["observation"]["source_url"]="https://youtu.be/00000000000"
        self.assertRejected(signed_local(r))

    def test_future_checked_at_rehashed_rejected(self):
        r=preflight(packet());r["claims"][0]["observation"]["checked_at"]="2030-01-01T00:00:00Z"
        self.assertRejected(signed_local(r))

    def test_unzoned_checked_at_rehashed_rejected(self):
        r=preflight(packet());r["claims"][0]["observation"]["checked_at"]="2026-11-09T08:00:00"
        self.assertRejected(signed_local(r))

    def test_future_publication_rehashed_rejected(self):
        r=preflight(packet());r["claims"][0]["observation"]["published_at"]="2028-01-01"
        self.assertRejected(signed_local(r))

    def test_fake_metric_rehashed_rejected(self):
        r=preflight(packet());r["claims"][0]["metric"]={"value":-15,"unit":"CCU"}
        self.assertRejected(signed_local(r))

    def test_fake_metric_nan_rehashed_rejected(self):
        r=preflight(packet());r["claims"][0]["metric"]={"value":float("nan"),"unit":"CCU"}
        self.assertRejected(r)

    def test_fake_metric_bool_rehashed_rejected(self):
        r=preflight(packet());r["claims"][0]["metric"]={"value":True,"unit":"CCU"}
        self.assertRejected(signed_local(r))

    def test_fake_claim_kind_rehashed_rejected(self):
        r=preflight(packet());r["claims"][0]["claim_kind"]="OFFICIAL_RULE"
        self.assertRejected(signed_local(r))

    def test_fake_hypothesis_rehashed_rejected(self):
        r=preflight(packet());r["claims"][0]["hypothesis_id"]="../../HACK"
        self.assertRejected(signed_local(r))

    def test_forged_source_warning_rehashed_rejected(self):
        r=preflight(packet());r["claims"][0]["observation"]["limitation"]="No direct source transcript."
        self.assertRejected(signed_local(r))

    def test_required_warning_survives_long_limitation(self):
        raw=packet();raw["records"][0]["limitation"]="X"*1998
        r=preflight(raw)
        self.assertLessEqual(len(r["claims"][0]["observation"]["limitation"]),2000)
        self.assertIn("Transcript NOT host-verified",r["claims"][0]["observation"]["limitation"])
        self.assertEqual(prepare_observation_bundle(raw)["authenticity"],"UNVERIFIED")

    def test_transcript_claim_input_not_reified_as_verified(self):
        raw=packet();raw["records"][0]["transcript_verified"]=True
        result=prepare_observation_bundle(raw)
        self.assertEqual(result["authenticity"],"UNVERIFIED")


if __name__=="__main__":unittest.main()
