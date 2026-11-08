"""Adversarial offline tests for the separate #109 source preflight."""
import copy
import json
import math
import subprocess
import sys
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))
from market_source_preflight import Rejected, preflight

NOW = "2026-11-09T09:00:00Z"

def row(**updates):
    v = {
        "claim_id":"CLAIM_001",
        "source_type":"YOUTUBE_CREATOR",
        "url":"https://youtu.be/ABCDEFGHI01?t=73",
        "published_at":"2026-11-01",
        "checked_at":"2026-11-08T20:00:00+09:00",
        "claim":"A creator claims a mobile game attracted visitors.",
        "claim_kind":"SELF_REPORTED",
        "limitation":"Not a Roblox official analytics export.",
        "hypothesis_id":"H_001",
        "metric":{"value":1000,"unit":"VISITS"},
        "transcript_verified":False,
    }
    v.update(updates)
    return v

def packet(*records):
    return {"schema":"MARKET_SOURCE_PREFLIGHT_V1","as_of":NOW,"records":list(records)}

class SourcePreflightTests(unittest.TestCase):
    def rejected(self, obj):
        with self.assertRaises(Rejected):
            preflight(obj)

    def test_valid_youtube_normalization(self):
        out=preflight(packet(row()))
        c=out["claims"][0]
        self.assertEqual(c["observation"]["source_url"],"https://www.youtube.com/watch?v=ABCDEFGHI01")
        self.assertEqual(c["observation"]["checked_at"],"2026-11-08T11:00:00Z")
        self.assertFalse(c["host_authenticated"])
        self.assertFalse(c["player_effect_proven"])
        self.assertEqual(out["authorized_actions"],[])
        self.assertIn("NOT host-verified",c["observation"]["limitation"])

    def test_normal_youtube_watch_and_shorts(self):
        for url in ("https://www.youtube.com/watch?v=ABCDEFGHI01&si=xxx",
                    "https://m.youtube.com/watch?v=ABCDEFGHI01",
                    "https://youtube.com/shorts/ABCDEFGHI01"):
            with self.subTest(url=url):
                self.assertEqual(preflight(packet(row(url=url)))["claims"][0]["observation"]["source_url"],
                                 "https://www.youtube.com/watch?v=ABCDEFGHI01")

    def test_deterministic_digest_order_independent(self):
        a=row()
        b=row(claim_id="CLAIM_002",url="https://youtu.be/ZZZZZZZZZZZ",metric=None)
        self.assertEqual(preflight(packet(a,b))["claims_sha256"],preflight(packet(b,a))["claims_sha256"])

    def test_duplicate_id_fails(self):
        self.rejected(packet(row(),row(url="https://youtu.be/ZZZZZZZZZZZ")))

    def test_duplicate_extra_field_fails(self):
        a=row();a["is_authenticated"]=True
        self.rejected(packet(a))

    def test_duplicate_packet_field_fails(self):
        a=packet(row());a["exec"]="run"
        self.rejected(a)

    def test_future_check_fails(self):
        self.rejected(packet(row(checked_at="2026-12-09T09:00:00Z")))

    def test_naive_check_fails(self):
        self.rejected(packet(row(checked_at="2026-11-08T19:00:00")))

    def test_publication_after_check_fails(self):
        self.rejected(packet(row(published_at="2026-11-10")))

    def test_bad_date_fails(self):
        self.rejected(packet(row(published_at="2026-02-30")))

    def test_wrong_url_scheme_fails(self):
        self.rejected(packet(row(url="http://youtu.be/ABCDEFGHI01")))

    def test_ip_url_fails(self):
        a=row(source_type="PUBLIC_ROBLOX_CHART",claim_kind="PUBLIC_SNAPSHOT",url="https://127.0.0.1/",
              transcript_verified=False)
        self.rejected(packet(a))

    def test_local_hostname_fails(self):
        self.rejected(packet(row(source_type="COMMUNITY_REPORT",claim_kind="OPINION",
                                 url="https://host.internal/report",metric=None)))

    def test_url_credentials_fails(self):
        self.rejected(packet(row(url="https://a@youtu.be/ABCDEFGHI01")))

    def test_url_fragment_fails(self):
        self.rejected(packet(row(url="https://youtu.be/ABCDEFGHI01#attack")))

    def test_ambiguous_video_id_fails(self):
        self.rejected(packet(row(url="https://youtube.com/watch?v=ABCDEFGHI01&v=ZZZZZZZZZZZ")))

    def test_invalid_youtube_host_fails(self):
        self.rejected(packet(row(url="https://youtube.com.evil.example/watch?v=ABCDEFGHI01")))

    def test_official_wrong_host_fails(self):
        self.rejected(packet(row(source_type="ROBLOX_OFFICIAL",url="https://create.roblox.com.evil.example/",
                                 claim_kind="OFFICIAL_RULE",metric=None)))

    def test_official_rule_not_allowed_metrics(self):
        self.rejected(packet(row(source_type="ROBLOX_OFFICIAL",url="https://create.roblox.com/docs/discovery",
                                 claim_kind="OFFICIAL_RULE")))

    def test_title_must_not_assert_metrics(self):
        self.rejected(packet(row(claim_kind="TITLE_ONLY")))

    def test_official_rule_valid_mapping(self):
        c=preflight(packet(row(source_type="ROBLOX_OFFICIAL",url="https://create.roblox.com/docs/discovery",
                    claim_kind="OFFICIAL_RULE",metric=None)))["claims"][0]
        self.assertEqual(c["observation"]["source_kind"],"PRIMARY_OFFICIAL")

    def test_chart_mapping_and_not_verified(self):
        c=preflight(packet(row(source_type="PUBLIC_ROBLOX_CHART",
              url="https://stats.example.org/roblox/2026-11-08",
              claim_kind="PUBLIC_SNAPSHOT")))["claims"][0]
        self.assertEqual(c["observation"]["source_kind"],"SECONDARY_REPORT")
        self.assertIn("NOT Roblox-confirmed revenue",c["observation"]["limitation"])

    def test_nan_inf_bool_metrics_fail(self):
        for x in (float("nan"),float("inf"),-float("inf"),True,"100"):
            with self.subTest(x=x):
                self.rejected(packet(row(metric={"value":x,"unit":"VISITS"})))

    def test_negative_nonpercent_fails(self):
        self.rejected(packet(row(metric={"value":-4,"unit":"CCU"})))

    def test_negative_percent_ok(self):
        c=preflight(packet(row(metric={"value":-4,"unit":"PERCENT_CHANGE"})))["claims"][0]
        self.assertEqual(c["metric"]["value"],-4)

    def test_blank_metric_unit_fails(self):
        self.rejected(packet(row(metric={"value":3,"unit":""})))

    def test_transcript_boolean_only(self):
        self.rejected(packet(row(transcript_verified="yes")))

    def test_user_claimed_transcript_never_host_verifies(self):
        c=preflight(packet(row(transcript_verified=True)))["claims"][0]
        self.assertFalse(c["transcript_verified"])
        self.assertTrue(c["transcript_verification_claimed_by_input"])
        self.assertFalse(c["host_authenticated"])

    def test_empty_and_oversized_fails(self):
        self.rejected(packet())
        self.rejected(packet(*[row(claim_id=f"CLAIM_{i:03}") for i in range(101)]))

    def test_truncation_of_limit_and_extra_label(self):
        c=preflight(packet(row(limitation="X"*1999)))["claims"][0]
        self.assertLessEqual(len(c["observation"]["limitation"]),2000)

    def test_cli_rejects_input_without_echoing_secret(self):
        exe=Path(__file__).resolve().parents[1]/"tools"/"market_source_preflight.py"
        bad=packet(row(url="https://a:b@youtu.be/ABCDEFGHI01"))
        proc=subprocess.run([sys.executable,"-S",str(exe)],input=json.dumps(bad),text=True,
                            capture_output=True,timeout=10)
        self.assertEqual(proc.returncode,2)
        self.assertNotIn("a:b",proc.stderr)

if __name__ == "__main__":
    unittest.main()
