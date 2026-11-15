#!/usr/bin/env python3
"""P0D scoped multi-writer admission PREVIEW. Does not authorize GitHub writes.

A PREVIEW is not a security boundary. Production use must load the registry
from a protected coordinator branch with a trusted GitHub token, fetch
GitHub actor/PR changed files/CI HEAD live, verify branch rules and audit
independent reviewer evidence. NEVER trust this script's JSON alone.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from fnmatch import fnmatchcase
import json
from pathlib import PurePosixPath
import re
from typing import Any

SHA = re.compile(r"[0-9a-f]{40}\Z")
HIGH_RISK = ("Game.server.luau", "Remote", "Store", "HUD", "MapBuilder",
             "FEATURE_REGISTRY", "FEATURE_SWITCHES", ".github/workflows/")
ACTIVE = {"GRANTED", "SOURCE_WIP", "PREP_READY", "HANDOFF_PENDING"}

def reason(key: str) -> ValueError:
    return ValueError(key)

def pathok(value: Any) -> str:
    if not isinstance(value, str) or not value or len(value)>240 or "\\" in value or value.startswith("/"):
        raise reason("INVALID_PATH")
    p=PurePosixPath(value)
    if "." in p.parts or ".." in p.parts or "//" in value or value != str(p):
        raise reason("INVALID_PATH")
    return value

def inside(path: str, scope: str) -> bool:
    pathok(path)
    if scope.endswith("/**"):
        base=pathok(scope[:-3])
        return path.startswith(base + "/")
    if any(c in scope for c in "*?[]"):
        raise reason("UNSUPPORTED_SCOPE_GLOB")
    return path == pathok(scope)

def overlapping(a: str,b: str) -> bool:
    if a.endswith("/**") and b.endswith("/**"):
        x,y=a[:-3],b[:-3]
        return x == y or x.startswith(y+"/") or y.startswith(x+"/")
    if a.endswith("/**"):
        return inside(b,a)
    if b.endswith("/**"):
        return inside(a,b)
    return a==b

def iso(s: str) -> datetime:
    try:
        x=datetime.fromisoformat(s.replace("Z","+00:00"))
    except (ValueError, AttributeError):
        raise reason("INVALID_LEASE_DATE")
    if x.tzinfo is None:
        raise reason("MISSING_LEASE_TIMEZONE")
    return x.astimezone(timezone.utc)

def expect_sha(value: Any, label: str):
    if not isinstance(value,str) or not SHA.fullmatch(value):
        raise reason("INVALID_SHA_"+label)
    return value

def assess(registry: dict, candidate: dict, observation: dict, now: datetime) -> dict:
    """Check candidate against separately asserted live evidence. NOT AUTHORIZATION."""
    try:
        if now.tzinfo is None:
            raise reason("NOW_TIMEZONE_REQUIRED")
        if registry.get("schema") != "P0D_EXCLUSIVE_CLAIMS_V1":
            raise reason("UNTRUSTED_CLAIM_SCHEMA")
        if registry.get("release")!="P0D-S1-KIDS-RC01":
            raise reason("WRONG_RELEASE")
        if not isinstance(registry.get("claims"),list):
            raise reason("INVALID_CLAIM_LIST")
        expected=expect_sha(observation.get("official_head"),"RC")
        source=expect_sha(candidate.get("source_head"),"SOURCE")
        base=expect_sha(candidate.get("base_rc"),"BASE")
        if base != expected:
            raise reason("STALE_BASE_REBASE_REQUIRED")
        if candidate.get("branch") in ("main", "rc/p0d-s1-kids-rc01") or not str(candidate.get("branch","")).startswith(("feature/","fix/")):
            raise reason("WRITER_CANNOT_USE_SHARED_BRANCH")
        if observation.get("source_head")!=source:
            raise reason("SOURCE_HEAD_DRIFT")
        if observation.get("ci_source_head")!=source or observation.get("source_ci")!="success":
            raise reason("NO_VERIFIED_SOURCE_HEAD_CI")
        if observation.get("high_severity_findings") not in (0,):
            raise reason("HIGH_SEVERITY_QA_UNCLEAR")
        paths=observation.get("changed_files")
        if not isinstance(paths,list) or not paths or len(set(paths))!=len(paths):
            raise reason("CHANGED_PATHS_INVALID")
        for path in paths:
            pathok(path)
        actor=observation.get("authenticated_actor_id")
        if not isinstance(actor,int) or actor<=0:
            raise reason("GH_ACTOR_UNVERIFIED")
        if observation.get("independent_reviewer_actor_id")==actor or not isinstance(observation.get("independent_reviewer_actor_id"),int):
            raise reason("INDEPENDENT_REVIEW_MISSING")
        if observation.get("reviewed_source_head")!=source:
            raise reason("STALE_REVIEW")
        if observation.get("claims_guard_result")!="CLAIM_SCOPE_PASS_NOT_RC_ADOPTION":
            raise reason("CLAIM_GUARD_NOT_PASS")
        grants=[c for c in registry["claims"] if c.get("state") in ACTIVE]
        claim_id=candidate.get("claim_id")
        matches=[c for c in grants if c.get("claim_id")==claim_id]
        if len(matches)!=1:
            raise reason("NO_UNIQUE_COORDINATOR_GRANT")
        grant=matches[0]
        if grant.get("owner")!=candidate.get("owner") or grant.get("feature_id")!=candidate.get("feature_id"):
            raise reason("CLAIM_OWNER_OR_FEATURE_MISMATCH")
        if grant.get("authenticated_actor_id")!=actor:
            raise reason("ACTOR_NOT_IN_GRANT")
        if iso(grant.get("expires_at"))<=now.astimezone(timezone.utc):
            raise reason("LEASE_EXPIRED")
        scopes=grant.get("target_paths")
        if not isinstance(scopes,list) or not scopes:
            raise reason("EMPTY_TARGET_SCOPES")
        if any(not any(inside(p,s) for s in scopes) for p in paths):
            raise reason("CHANGED_PATH_OUTSIDE_CLAIM")
        # Shared authority paths need explicit exclusive class and one active
        # claim only. Different names cannot silently create duplicate Game.
        if any(any(k in p for k in HIGH_RISK) for p in paths) and grant.get("authority_lock")!="EXCLUSIVE":
            raise reason("SHARED_AUTHORITY_LOCK_REQUIRED")
        for other in grants:
            if other is grant:
                continue
            if other.get("feature_id")==grant.get("feature_id"):
                raise reason("DUPLICATE_FEATURE_GRANTED")
            if set(other.get("resources",[])) & set(grant.get("resources",[])):
                raise reason("DUPLICATE_RESOURCE_GRANTED")
            if any(overlapping(a,b) for a in scopes for b in other.get("target_paths",[])):
                raise reason("OVERLAPPING_ACTIVE_CLAIMS")
        # Runtime branch protection/role proof must be from GitHub, not claimed
        # by this JSON. Failure here blocks production even if all QA is green.
        if observation.get("official_branch_protected") is not True or observation.get("coordinator_branch_protected") is not True:
            raise reason("PROTECTED_BRANCH_NOT_ENFORCED")
        if observation.get("protected_registry_blob_sha")!=observation.get("live_registry_blob_sha") or not isinstance(observation.get("protected_registry_blob_sha"),str):
            raise reason("REGISTRY_SHA_NOT_PINNED")
        expect_sha(observation["protected_registry_blob_sha"],"REGISTRY")
        if registry.get("multiwriter_production_enabled") is not True:
            raise reason("PRODUCTION_NOT_ENABLED_BY_TRUSTED_COORDINATOR")
        if observation.get("github_trusted_runner") is not True:
            raise reason("RUNNER_IDENTITY_UNVERIFIED")
        if observation.get("github_branch_rules_verified") is not True:
            raise reason("BRANCH_RULES_UNVERIFIED")
        return {"schema":"P0D_MULTIWRITER_PREVIEW_V1","decision":"EVIDENCE_READY_NOT_AUTHORIZATION",
                "claim_id":claim_id,"actor_id":actor,"expected_rc_head":expected,
                "source_head":source,"changed_files":paths,"requires_nonforce_atomic_cas":True,
                "independent_live_authorization_still_required":True}
    except (ValueError, TypeError, KeyError) as ex:
        return {"schema":"P0D_MULTIWRITER_PREVIEW_V1","decision":"HOLD",
                "reason":str(ex), "rc_written":False}

def main() -> int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--registry",required=True)
    p.add_argument("--candidate",required=True)
    p.add_argument("--observation",required=True)
    p.add_argument("--now",default=None)
    a=p.parse_args()
    try:
        with open(a.registry,encoding="utf8") as f: reg=json.load(f)
        with open(a.candidate,encoding="utf8") as f: c=json.load(f)
        with open(a.observation,encoding="utf8") as f: o=json.load(f)
        ans=assess(reg,c,o,iso(a.now) if a.now else datetime.now(timezone.utc))
    except (ValueError,OSError,json.JSONDecodeError) as ex:
        ans={"schema":"P0D_MULTIWRITER_PREVIEW_V1","decision":"HOLD","reason":str(ex),"rc_written":False}
    print(json.dumps(ans,ensure_ascii=False,indent=2))
    return 0 if ans["decision"]=="EVIDENCE_READY_NOT_AUTHORIZATION" else 2

if __name__=="__main__":
    raise SystemExit(main())
