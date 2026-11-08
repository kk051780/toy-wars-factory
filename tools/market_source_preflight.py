"""Read-only source-claim preflight for TOY WARS #109 MARKET_INTELLIGENCE.

Offline only. This validates user-supplied observations, not source authenticity.
It cannot fetch pages, send messages, authorize source writes, evaluate profitability,
create experiments, control Studio or promote an idea past research planning.
Output observations match tools.system_idea_pipeline.capture's observation keys.
"""
from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
from urllib.parse import parse_qs, urlsplit
import ipaddress
import json
import math
import re
import sys

SCHEMA = "MARKET_SOURCE_PREFLIGHT_V1"
KINDS = {
    "ROBLOX_OFFICIAL": ("PRIMARY_OFFICIAL", {"OFFICIAL_RULE"}),
    "YOUTUBE_CREATOR": ("DEVELOPER_CASE", {"TITLE_ONLY", "SELF_REPORTED", "OPINION"}),
    "PUBLIC_ROBLOX_CHART": ("SECONDARY_REPORT", {"PUBLIC_SNAPSHOT"}),
    "COMMUNITY_REPORT": ("COMMUNITY_REACTION", {"OPINION", "PUBLIC_SNAPSHOT"}),
}
METRIC_UNITS = {"CCU", "VISITS", "ROBUX", "USD", "JPY", "PERCENT_CHANGE", "MINUTES"}
RECORD_KEYS = {
    "claim_id", "source_type", "url", "published_at", "checked_at", "claim",
    "claim_kind", "limitation", "hypothesis_id", "metric", "transcript_verified"
}
CLAIM_ID = re.compile(r"[A-Z][A-Z0-9_-]{2,79}\Z")
VIDEO_ID = re.compile(r"[A-Za-z0-9_-]{11}\Z")
HYPOTHESIS = re.compile(r"[A-Z][A-Z0-9_-]{2,79}\Z")

class Rejected(ValueError):
    pass

def require(ok, message):
    if not ok:
        raise Rejected(message)

def utc(value):
    require(type(value) is str, "timestamp must be string")
    try:
        date = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        raise Rejected("invalid timestamp") from None
    require(date.tzinfo is not None, "timestamp must include time zone")
    return date.astimezone(timezone.utc)

def public_https(value):
    require(type(value) is str and 1 <= len(value) <= 2048, "invalid URL")
    try:
        u = urlsplit(value)
        host = u.hostname
        require(u.scheme == "https" and host is not None and u.port in (None, 443),
                "HTTPS URL with standard port required")
        require(not u.username and not u.password and not u.fragment,
                "URL credentials and fragments prohibited")
        require(not any(c.isspace() or ord(c) < 32 for c in value),
                "URL control/space prohibited")
        host = host.lower().rstrip(".")
        require(bool(re.fullmatch(r"[a-z0-9.-]+", host))
                and "." in host and not host.startswith(".") and ".." not in host,
                "not a public DNS hostname")
        require(not host.endswith((".local", ".internal", ".localhost", ".test")),
                "local/private hostname")
        try:
            ipaddress.ip_address(host)
        except ValueError:
            pass
        else:
            raise Rejected("raw IP address prohibited")
        require(u.path.startswith("/") or u.path == "", "invalid path")
        return u, host
    except ValueError as e:
        if isinstance(e, Rejected):
            raise
        raise Rejected("invalid URL") from None

def canonical_url(value, source_type):
    u, host = public_https(value)
    if source_type == "ROBLOX_OFFICIAL":
        require(host == "create.roblox.com", "official URL must be Creator Hub")
        require(not u.query, "official rule URL must be canonical")
        return "https://create.roblox.com" + (u.path or "/")
    if source_type == "YOUTUBE_CREATOR":
        if host == "youtu.be":
            vid = u.path.strip("/")
        elif host in ("youtube.com", "www.youtube.com", "m.youtube.com"):
            if u.path == "/watch":
                matches = parse_qs(u.query, keep_blank_values=True).get("v", [])
                require(len(matches) == 1, "ambiguous YouTube video ID")
                vid = matches[0]
            elif u.path.startswith("/shorts/"):
                vid = u.path.removeprefix("/shorts/").strip("/")
            else:
                raise Rejected("not a YouTube watch/shorts link")
        else:
            raise Rejected("wrong creator host")
        require(VIDEO_ID.fullmatch(vid) is not None, "invalid YouTube video ID")
        return "https://www.youtube.com/watch?v=" + vid
    require(host not in ("youtube.com", "youtu.be", "www.youtube.com", "create.roblox.com"),
            "use the matching specialized source type")
    require(not u.query, "strip tracking/query parameters from non-YouTube source")
    return "https://" + host + (u.path or "/")

def check_published(value, checked):
    if value == "NOT_AVAILABLE":
        return
    require(type(value) is str, "invalid publication date")
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        try:
            date = datetime.strptime(value, "%Y-%m-%d").date()
        except ValueError:
            raise Rejected("invalid publication day") from None
        require(date <= checked.date(), "publication later than check")
    else:
        require(utc(value) <= checked, "publication later than check")

def preflight(packet):
    require(type(packet) is dict and set(packet) == {"schema", "as_of", "records"},
            "packet schema mismatch")
    require(packet["schema"] == SCHEMA, "unsupported schema")
    as_of = utc(packet["as_of"])
    items = packet["records"]
    require(type(items) is list and 1 <= len(items) <= 100,
            "1-100 source claims required")
    seen_ids, seen_claims, normalized = set(), set(), []
    for row in items:
        require(type(row) is dict and set(row) == RECORD_KEYS, "claim schema mismatch")
        key = row["claim_id"]
        require(type(key) is str and CLAIM_ID.fullmatch(key), "invalid claim ID")
        require(key not in seen_ids, "duplicate claim ID")
        seen_ids.add(key)
        source_type = row["source_type"]
        require(type(source_type) is str and source_type in KINDS, "unknown source type")
        source_kind, allowed_claims = KINDS[source_type]
        claim_kind = row["claim_kind"]
        require(type(claim_kind) is str and claim_kind in allowed_claims,
                "claim inconsistent with source type")
        url = canonical_url(row["url"], source_type)
        checked = utc(row["checked_at"])
        require(checked <= as_of, "checked timestamp in future")
        check_published(row["published_at"], checked)
        for field in ("claim", "limitation"):
            value = row[field]
            require(type(value) is str and 3 <= len(value) <= 2000,
                    "claim/limitation must be 3-2000 characters")
        hypothesis = row["hypothesis_id"]
        require(hypothesis is None or (type(hypothesis) is str and HYPOTHESIS.fullmatch(hypothesis)),
                "invalid hypothesis reference")
        transcript = row["transcript_verified"]
        require(type(transcript) is bool, "transcript flag must be bool")
        require(source_type == "YOUTUBE_CREATOR" or transcript is False,
                "transcript flag is only for videos")
        metric = row["metric"]
        if metric is not None:
            require(type(metric) is dict and set(metric) == {"value", "unit"},
                    "metric schema mismatch")
            val, unit = metric["value"], metric["unit"]
            require(type(val) in (int, float) and math.isfinite(val)
                    and abs(val) <= 1e15, "invalid finite numeric metric")
            require(type(unit) is str and unit in METRIC_UNITS, "invalid metric unit")
            if unit != "PERCENT_CHANGE":
                require(val >= 0, "negative metric")
            require(claim_kind in {"SELF_REPORTED", "PUBLIC_SNAPSHOT"},
                    "title/opinion/rule must not assert numeric outcomes")
        claim_sig = (url, key, claim_kind)
        require(claim_sig not in seen_claims, "duplicate canonical claim")
        seen_claims.add(claim_sig)
        limitation = row["limitation"]
        if source_type == "YOUTUBE_CREATOR":
            limitation += " | Transcript NOT host-verified; input assertion is untrusted."
        if claim_kind == "SELF_REPORTED":
            limitation += " | Self-reported figures NOT independently verified."
        if claim_kind == "PUBLIC_SNAPSHOT":
            limitation += " | Third-party snapshot; NOT Roblox-confirmed revenue."
        obs = {
            "source_url": url,
            "checked_at": checked.isoformat().replace("+00:00", "Z"),
            "observed_fact": row["claim"],
            "limitation": limitation[:2000],
            "source_kind": source_kind,
            "published_at": row["published_at"],
        }
        normalized.append({
            "claim_id": key, "claim_kind": claim_kind,
            "hypothesis_id": hypothesis, "metric": metric,
            "source_type": source_type, "transcript_verified": False,
            "transcript_verification_claimed_by_input": transcript,
            "observation": obs,
            "host_authenticated": False,
            "player_effect_proven": False,
        })
    normalized.sort(key=lambda x: x["claim_id"])
    payload = json.dumps(normalized, ensure_ascii=False, sort_keys=True,
                         separators=(",", ":"), allow_nan=False)
    return {
        "schema": SCHEMA, "as_of": as_of.isoformat().replace("+00:00", "Z"),
        "authority": "READ_ONLY_UNTRUSTED_INPUT",
        "authorized_actions": [],
        "claims_sha256": sha256(payload.encode("utf-8")).hexdigest(),
        "claims": normalized,
    }

def main():
    try:
        packet = json.load(sys.stdin)
        print(json.dumps(preflight(packet), ensure_ascii=False, sort_keys=True))
    except (Rejected, ValueError, TypeError, json.JSONDecodeError) as e:
        # Never echo untrusted content/URLs in errors.
        print("REJECTED: " + ("invalid input JSON" if isinstance(e, json.JSONDecodeError) else str(e)),
              file=sys.stderr)
        return 2
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
