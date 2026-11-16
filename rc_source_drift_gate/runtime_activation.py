#!/usr/bin/env python3
"""Independent actual-author-source activation boundary for the live 26-script RC candidate.

Only source text/allowlisted module locations. Does not modify or start the
Studio-only V3 host, and NEVER equates native/Rojo success to production runtime.
"""
from __future__ import annotations

import hashlib
import re
from typing import Mapping

# Actor/component sources are owned by original V3 author #482. Only this
# separate GQ branch's evaluator may change. Existing production Game stays sole
# authority until an approved owner creates a safe single-host adapter.
REQUIRED_RUNTIME_SOURCES = {
    "EGGRUMBLE_LobbyCastleModesPreview": (
        "character", "field", "battle", "castle_egg", "neutral", "item", "lobby", "balance",
    ),
    "EGGRUMBLE_BotActors": ("field", "battle", "castle_egg", "neutral", "item"),
    "EGGRUMBLE_SevenRoleCombat": ("character", "battle", "castle_egg", "neutral"),
    "EGGRUMBLE_RoundReplay": ("character", "item", "lobby", "balance"),
    "EGGRUMBLE_MatchResultService": ("castle_egg", "lobby", "balance"),
}

# Source-anchored guards, not comments or test assertions from separate tools.
EARLY_RETURN = re.compile(
    r"\bif\s+not\s+RunService\s*:\s*IsStudio\s*\(\s*\)\s+then\s+return(?:\s+end|\b)"
)
ASSERT_STUDIO = re.compile(r"\bassert\s*\(\s*RunService\s*:\s*IsStudio\s*\(\s*\)")


def guard_lines(source: str) -> list[dict]:
    """Identify executable production-incompatible Studio-only guards."""
    found: list[dict] = []
    for number, raw in enumerate(source.splitlines(), 1):
        # V3 uses -- for comments. Ignore comment-only lines and comments
        # after guards. Never count a descriptive comment as proof.
        active = raw.split("--", 1)[0].strip()
        kind = ("STUDIO_ONLY_EARLY_RETURN" if EARLY_RETURN.search(active)
                else "STUDIO_ONLY_RUNTIME_ASSERT" if ASSERT_STUDIO.search(active)
                else None)
        if kind:
            found.append({"line": number, "kind": kind, "excerpt": active[:170]})
    return found


def evaluate_runtime_activation(sources: Mapping[str, str]) -> dict:
    """Fail closed for missing authority sources, but never pretend we ran Studio.

    A clean textual guard scan is only UNKNOWN, never production GO: external
    Game/Remote/Store/2-client Android verification still remains required.
    """
    missing = sorted(set(REQUIRED_RUNTIME_SOURCES) - set(sources))
    evidence = []
    impacted: set[str] = set()
    for name, domains in REQUIRED_RUNTIME_SOURCES.items():
        value = sources.get(name)
        if not isinstance(value, str) or not value.strip():
            if name not in missing:
                missing.append(name)
            continue
        for event in guard_lines(value):
            impacted.update(domains)
            evidence.append({
                "owner_module": name,
                "source_sha256": hashlib.sha256(value.encode("utf-8")).hexdigest(),
                "domains": list(domains),
                **event,
            })
    return {
        "schema": "EGGRUMBLE_RUNTIME_ACTIVATION_V1",
        "source_guard_inspection": "COMPLETE" if not missing else "MISSING_OWNER_SOURCE",
        "production_runtime": (
            "BLOCKED_STUDIO_ONLY_GAME_HOST" if evidence
            else "NOT_VERIFIED_FAIL_CLOSED"
        ),
        "studio_runtime": "NOT_EXECUTED_BY_STATIC_GATE",
        "eight_domain_production_impact": sorted(impacted),
        "missing_sources": sorted(missing),
        "guards": evidence,
        "guard_count": len(evidence),
        "remediation_owner": (
            "#482 ORIGINAL gameplay + #220 SOLE official Game/Remote/Store writer; "
            "require a single-host adapter, never delete IsStudio guards blindly"
        ),
        "source_admission_policy": (
            "RECORD_YELLOW_DEBT_IN_PRIVATE_RC_IF_REVERSIBLE; "
            "DO_NOT_ASSERT_ANDROID_OR_PUBLIC_PLAYABLE"
        ),
        "product_go": False,
        "official_rc_integrated": "UNVERIFIED_REQUIRES_AUTHENTICATED_220_ACK",
    }
