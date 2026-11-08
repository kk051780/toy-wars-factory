"""#109 market-preflight output -> existing system_idea_pipeline observation shape.

No GitHub writes, execution authority, trusted source authentication, or idea
promotion. A valid digest is only local consistency, not a signed attestation.
"""
from __future__ import annotations

from hashlib import sha256
import json
from typing import Any

try:
    from .market_source_preflight import Rejected, SCHEMA, KINDS, preflight
except ImportError:
    from market_source_preflight import Rejected, SCHEMA, KINDS, preflight

REPORT_KEYS = {"schema", "as_of", "authority", "authorized_actions", "claims_sha256", "claims"}
CLAIM_KEYS = {"claim_id", "claim_kind", "hypothesis_id", "metric", "source_type",
              "transcript_verified", "transcript_verification_claimed_by_input",
              "observation", "host_authenticated", "player_effect_proven"}
OBS_KEYS = {"source_url", "checked_at", "observed_fact", "limitation",
            "source_kind", "published_at"}


def observation_bundle_from_report(report: Any):
    if type(report) is not dict or set(report) != REPORT_KEYS:
        raise Rejected("report schema mismatch")
    if report["schema"] != SCHEMA or report["authority"] != "READ_ONLY_UNTRUSTED_INPUT":
        raise Rejected("unknown report authority or version")
    if report["authorized_actions"] != []:
        raise Rejected("report cannot carry execution actions")
    claims = report["claims"]
    if type(claims) is not list or not 1 <= len(claims) <= 20:
        raise Rejected("one idea may hold only 1-20 evidence observations")
    plain = json.dumps(claims, ensure_ascii=False, sort_keys=True,
                       separators=(",", ":"), allow_nan=False)
    if report["claims_sha256"] != sha256(plain.encode("utf-8")).hexdigest():
        raise Rejected("local report digest mismatch")
    seen, observations, claim_ids = set(), [], []
    for row in claims:
        if type(row) is not dict or set(row) != CLAIM_KEYS:
            raise Rejected("claim output schema mismatch")
        if row["host_authenticated"] is not False or row["player_effect_proven"] is not False or row["transcript_verified"] is not False:
            raise Rejected("untrusted report cannot assert proof or host verification")
        if type(row["transcript_verification_claimed_by_input"]) is not bool:
            raise Rejected("invalid transcription claim field")
        if row["source_type"] not in KINDS:
            raise Rejected("unknown origin kind")
        if type(row["observation"]) is not dict or set(row["observation"]) != OBS_KEYS:
            raise Rejected("observation schema mismatch")
        obs = row["observation"]
        if obs["source_kind"] != KINDS[row["source_type"]][0]:
            raise Rejected("inconsistent source classification")
        if any(type(obs[k]) is not str or len(obs[k]) > 2000 or len(obs[k]) < 3
               for k in ("observed_fact", "limitation")):
            raise Rejected("invalid observation text")
        if type(row["claim_id"]) is not str or row["claim_id"] in seen:
            raise Rejected("duplicate claim ID")
        seen.add(row["claim_id"])
        claim_ids.append(row["claim_id"])
        observations.append(dict(obs))
    if claim_ids != sorted(claim_ids):
        raise Rejected("claims not in canonical ID order")
    return {
        "schema": "MARKET_OBSERVATION_BUNDLE_V1",
        "stage": "PRE_VALIDATED_LOCAL_ONLY",
        "authenticity": "UNVERIFIED",
        "write_approval": False,
        "claim_ids": claim_ids,
        "observations": observations,
    }


def prepare_observation_bundle(packet: Any):
    """The single supported entry: re-run local strict preflight then adapt."""
    return observation_bundle_from_report(preflight(packet))
