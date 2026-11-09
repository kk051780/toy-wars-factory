"""Contract checks: #109 market evidence feeds the existing idea vault, advisory only.

No network, account access, GitHub writes, Studio calls or authenticated source claims.
This is real integration with tools.system_idea_pipeline.capture, not a mock.
"""
from __future__ import annotations

from hashlib import sha256
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.market_observation_bridge import prepare_observation_bundle
from tools.market_source_preflight import Rejected
from tools.system_idea_pipeline import capture, validate_record, IdeaValidationError

CHECKED = "2026-11-08T00:00:00Z"
AS_OF = "2026-11-08T12:00:00Z"
CAPTURED = "2026-11-08T13:00:00Z"
PROJECT = "toy-wars-factory"


def scope():
    return {
        "repository": "fixture/toy-wars-factory",
        "tasks": {
            role: sha256((PROJECT + role).encode()).hexdigest()[:32]
            for role in ("WORKER", "META", "REVIEWER")
        },
    }


def row(claim_id, source_type, url, claim_kind, claim, limitation,
        published_at="NOT_AVAILABLE", metric=None):
    return {
        "claim_id": claim_id,
        "source_type": source_type,
        "url": url,
        "published_at": published_at,
        "checked_at": CHECKED,
        "claim": claim,
        "claim_kind": claim_kind,
        "limitation": limitation,
        "hypothesis_id": "H_MARKET_001",
        "metric": metric,
        "transcript_verified": False,
    }


def packet(*rows):
    return {
        "schema": "MARKET_SOURCE_PREFLIGHT_V1",
        "as_of": AS_OF,
        "records": list(rows),
    }


def official():
    return row(
        "CLAIM_OFFICIAL_001", "ROBLOX_OFFICIAL",
        "https://create.roblox.com/docs/discovery",
        "OFFICIAL_RULE",
        "Roblox Creator Hub documents discovery and engagement signal categories.",
        "Official documentation does not demonstrate our game attracts or retains players.",
    )


def creator():
    return row(
        "CLAIM_CREATOR_001", "YOUTUBE_CREATOR",
        "https://youtu.be/ABCDEFGHI01?si=tracker",
        "SELF_REPORTED",
        "A developer reports 1200 visits, but independently verified data is absent.",
        "Unverified creator claims, not official analytics.",
        metric={"value": 1200, "unit": "VISITS"},
    )


def capture_idea(bundle, source_ref):
    return capture(
        idea_id="WEB20261108_MARKET_INTAKE",
        project_id=PROJECT,
        origin="WEB_RESEARCH",
        original_text="Consider an original child-friendly prototype to test early session engagement.",
        source_ref=source_ref,
        captured_at=CAPTURED,
        observations=bundle["observations"],
        scope=scope(),
    )


class MarketToIdeaIntegrationTests(unittest.TestCase):
    def test_real_official_capture_accepts_six_observation_fields(self):
        bundle = prepare_observation_bundle(packet(official()))
        record = capture_idea(bundle, "https://create.roblox.com/docs/discovery")
        self.assertIs(validate_record(record), record)
        self.assertEqual(record["origin"], "WEB_RESEARCH_IDEA")
        self.assertEqual(record["stage"], "CAPTURED")
        self.assertEqual(record["events"], [])
        self.assertEqual(record["observations"], bundle["observations"])
        self.assertEqual(
            record["observations"][0]["source_kind"], "PRIMARY_OFFICIAL"
        )
        self.assertEqual(
            record["observations"][0]["source_url"],
            "https://create.roblox.com/docs/discovery",
        )
        self.assertEqual(bundle["authenticity"], "UNVERIFIED")
        self.assertIs(bundle["write_approval"], False)

    def test_real_creator_capture_preserves_unverified_caveat(self):
        bundle = prepare_observation_bundle(packet(creator()))
        record = capture_idea(bundle, "https://www.youtube.com/watch?v=ABCDEFGHI01")
        self.assertIs(validate_record(record), record)
        obs = record["observations"][0]
        self.assertEqual(
            obs["source_url"], "https://www.youtube.com/watch?v=ABCDEFGHI01"
        )
        self.assertEqual(obs["source_kind"], "DEVELOPER_CASE")
        self.assertIn("Self-reported figures NOT independently verified", obs["limitation"])
        self.assertIn("Transcript NOT host-verified", obs["limitation"])
        self.assertNotIn("metric", obs)
        self.assertEqual(record["stage"], "CAPTURED")
        self.assertEqual(record["events"], [])

    def test_multisource_record_validates_in_existing_pipeline(self):
        bundle = prepare_observation_bundle(packet(official(), creator()))
        record = capture_idea(bundle, "https://create.roblox.com/docs/discovery")
        self.assertIs(validate_record(record), record)
        self.assertEqual(len(record["observations"]), 2)
        self.assertEqual(
            {item["source_kind"] for item in record["observations"]},
            {"PRIMARY_OFFICIAL", "DEVELOPER_CASE"},
        )
        self.assertIs(bundle["write_approval"], False)

    def test_input_and_record_are_detached(self):
        raw = packet(official())
        bundle = prepare_observation_bundle(raw)
        record = capture_idea(bundle, "https://create.roblox.com/docs/discovery")
        original = record["observations"][0]["observed_fact"]
        raw["records"][0]["claim"] = "Replaced after validation"
        bundle["observations"][0]["observed_fact"] = "Mutated after capture"
        self.assertEqual(record["observations"][0]["observed_fact"], original)
        self.assertIs(validate_record(record), record)

    def test_invalid_capture_origin_cannot_promote_evidence(self):
        bundle = prepare_observation_bundle(packet(creator()))
        with self.assertRaises(IdeaValidationError):
            capture(
                idea_id="WEB20261108_MARKET_INTAKE",
                project_id=PROJECT,
                origin="DERIVED",
                original_text="Attempt to skip provenance with a fake derived source.",
                source_ref="https://www.youtube.com/watch?v=ABCDEFGHI01",
                captured_at=CAPTURED,
                observations=bundle["observations"],
                scope=scope(),
            )

    def test_market_limit_21_fails_before_pipeline_capture(self):
        common = official()
        rows = [
            dict(common, claim_id=f"CLAIM_OFFICIAL_{i:03}",
                 claim=f"Distinct official claim number {i} on public engagement.")
            for i in range(21)
        ]
        with self.assertRaises(Rejected):
            prepare_observation_bundle(packet(*rows))


if __name__ == "__main__":
    unittest.main()
