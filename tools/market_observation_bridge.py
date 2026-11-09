"""#109 market-preflight output -> existing system_idea_pipeline observation shape.

No GitHub writes, execution authority, trusted source authentication, or idea
promotion. A valid digest is only local consistency, not a signed attestation.
"""
from __future__ import annotations

from hashlib import sha256
import json
import math
from typing import Any

try:
    from .market_source_preflight import (Rejected, SCHEMA, KINDS, preflight,
        canonical_url, utc, check_published, CLAIM_ID, HYPOTHESIS,
        METRIC_UNITS, valid_metric_number)
except ImportError:
    from market_source_preflight import (Rejected, SCHEMA, KINDS, preflight,
        canonical_url, utc, check_published, CLAIM_ID, HYPOTHESIS,
        METRIC_UNITS, valid_metric_number)

REPORT_KEYS = {"schema", "as_of", "authority", "authorized_actions", "claims_sha256", "claims"}
CLAIM_KEYS = {"claim_id", "claim_kind", "hypothesis_id", "metric", "source_type",
              "transcript_verified", "transcript_verification_claimed_by_input",
              "observation", "host_authenticated", "player_effect_proven"}
OBS_KEYS = {"source_url", "checked_at", "observed_fact", "limitation",
            "source_kind", "published_at"}


def observation_bundle_from_report(report: Any):
    # A mutable caller object must never be re-read after validation. Turn it
    # into a detached plain JSON snapshot and validate/copy from that snapshot.
    try:
        encoded = json.dumps(report, ensure_ascii=False, sort_keys=True,
                             separators=(",", ":"), allow_nan=False)
        if len(encoded) > 1_048_576:
            raise Rejected("oversized report JSON")
        report = json.loads(encoded)
    except Rejected:
        raise
    except (ValueError, TypeError, OverflowError, RecursionError, RuntimeError):
        raise Rejected("invalid report JSON") from None
    if type(report) is not dict or set(report) != REPORT_KEYS:
        raise Rejected("report schema mismatch")
    if report["schema"] != SCHEMA or report["authority"] != "READ_ONLY_UNTRUSTED_INPUT":
        raise Rejected("unknown report authority or version")
    if report["authorized_actions"] != []:
        raise Rejected("report cannot carry execution actions")
    # This function also accepts an externally supplied report. A caller can
    # freely rehash that report, so the digest is never a substitute for the
    # original preflight's URL/date/metric/claim invariants.
    as_of = utc(report["as_of"])
    from datetime import datetime, timezone
    if as_of > datetime.now(timezone.utc):
        raise Rejected("as_of later than runtime UTC")
    claims = report["claims"]
    if type(claims) is not list or not 1 <= len(claims) <= 20:
        raise Rejected("one idea may hold only 1-20 evidence observations")
    try:
        plain = json.dumps(claims, ensure_ascii=False, sort_keys=True,
                           separators=(",", ":"), allow_nan=False)
    except (TypeError, ValueError, OverflowError):
        raise Rejected("invalid report JSON") from None
    if type(report["claims_sha256"]) is not str or report["claims_sha256"] != sha256(plain.encode("utf-8")).hexdigest():
        raise Rejected("local report digest mismatch")
    seen, seen_observations, observations, claim_ids = set(), set(), [], []
    for row in claims:
        if type(row) is not dict or set(row) != CLAIM_KEYS:
            raise Rejected("claim output schema mismatch")
        if row["host_authenticated"] is not False or row["player_effect_proven"] is not False or row["transcript_verified"] is not False:
            raise Rejected("untrusted report cannot assert proof or host verification")
        if type(row["transcript_verification_claimed_by_input"]) is not bool:
            raise Rejected("invalid transcription claim field")
        source_type = row["source_type"]
        if type(source_type) is not str or source_type not in KINDS:
            raise Rejected("unknown origin kind")
        if type(row["claim_kind"]) is not str or row["claim_kind"] not in KINDS[source_type][1]:
            raise Rejected("claim kind does not match source")
        if type(row["observation"]) is not dict or set(row["observation"]) != OBS_KEYS:
            raise Rejected("observation schema mismatch")
        obs = row["observation"]
        if obs["source_kind"] != KINDS[source_type][0]:
            raise Rejected("inconsistent source classification")
        if any(type(obs[k]) is not str or len(obs[k]) > 2000 or len(obs[k]) < 3
               for k in ("observed_fact", "limitation")):
            raise Rejected("invalid observation text")
        if type(row["claim_id"]) is not str or not CLAIM_ID.fullmatch(row["claim_id"]) or row["claim_id"] in seen:
            raise Rejected("invalid or duplicate claim ID")
        if obs["source_url"] != canonical_url(obs["source_url"], source_type):
            raise Rejected("noncanonical source URL")
        checked = utc(obs["checked_at"])
        if checked > as_of or checked.isoformat().replace("+00:00", "Z") != obs["checked_at"]:
            raise Rejected("invalid checked timestamp")
        check_published(obs["published_at"], checked)
        hypothesis = row["hypothesis_id"]
        if hypothesis is not None and (type(hypothesis) is not str or not HYPOTHESIS.fullmatch(hypothesis)):
            raise Rejected("invalid hypothesis ID")
        metric = row["metric"]
        if metric is not None:
            if type(metric) is not dict or set(metric) != {"value", "unit"}:
                raise Rejected("invalid metric shape")
            value, unit = metric["value"], metric["unit"]
            if (not valid_metric_number(value)
                    or type(unit) is not str or unit not in METRIC_UNITS):
                raise Rejected("invalid metric value/unit")
            if (unit != "PERCENT_CHANGE" and value < 0) or row["claim_kind"] not in {"SELF_REPORTED", "PUBLIC_SNAPSHOT"}:
                raise Rejected("metric not permitted for this claim")
        warnings = ""
        if source_type == "YOUTUBE_CREATOR":
            warnings += " | Transcript NOT host-verified; input assertion is untrusted."
        if row["claim_kind"] == "SELF_REPORTED":
            warnings += " | Self-reported figures NOT independently verified."
        if row["claim_kind"] == "PUBLIC_SNAPSHOT":
            warnings += " | Third-party snapshot; NOT Roblox-confirmed revenue."
        if warnings and not obs["limitation"].endswith(warnings):
            raise Rejected("required source caveat missing")
        seen.add(row["claim_id"])
        # The report is caller-supplied; a recomputed digest must not permit
        # the same source, claim and observation time under a different ID.
        claim_sig = (obs["source_url"], obs["checked_at"],
                     row["claim_kind"], obs["observed_fact"])
        if claim_sig in seen_observations:
            raise Rejected("duplicate canonical observation")
        seen_observations.add(claim_sig)
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
