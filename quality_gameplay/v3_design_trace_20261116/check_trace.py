#!/usr/bin/env python3
"""Evidence-preserving #470 design-to-game source QA.

This is NOT a gameplay script, Rojo Place, Studio session, or RC adoption.
It refuses a fabricated RC/FUN claim and detects missing/duplicated feature IDs.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
CATALOG = REPO / "rc_fastlane" / "FEATURE_CATALOG.json"
MATRIX = HERE / "DESIGN_TO_GAME_TRACE_MATRIX.json"
DOMAINS = {"CHARACTER", "FIELD", "BATTLE", "CASTLE", "NEUTRAL", "ITEM", "LOBBY", "BALANCE"}
GAP_TYPES = {"ABSENT", "STUB", "WRONG_BEHAVIOR", "PARTIAL", "REGRESSION", "EVIDENCE_MISSING"}
RELEASE_OVERRIDES = {"P0D-%03d" % i for i in range(8, 16)} | {"P0D-019"}
FIELDS = {
    "CONCEPT_ID", "DESIGN_SOURCE_URL_REV", "MUST_BEHAVE", "FEATURE_ID", "FB_ID",
    "RELEASE_REQUIRED", "RELEASE_CLAIM_HISTORICAL", "DOMAIN", "ACTUAL_RC_HEAD",
    "CATALOG_STAGE_CLAIM_HISTORICAL", "REAL_SOURCE_PATHS_SHA", "SOURCE_CANDIDATES",
    "ENGINE_PROOF", "DEVICE_PROOF", "ART_GATE", "COMPETITIVE_EVIDENCE",
    "GAP_TYPE", "GAP_REASON", "CLAIM_WRITER", "FIX_SHA", "NEXT_ACTION",
    "STATE", "V3_NEW_SOURCE_OFFICIAL_ADOPTED", "OWNER_ACCEPTED",
}
SHA40 = re.compile(r"^[a-f0-9]{40}$")


class TraceFailure(ValueError):
    pass


def require(ok: bool, why: str) -> None:
    if not ok:
        raise TraceFailure(why)


def git_blob_sha(raw: bytes) -> str:
    payload = b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw
    return hashlib.sha1(payload).hexdigest()


def validate(catalog: dict, matrix: dict, raw_catalog: bytes) -> dict:
    require(matrix.get("schema") == "P0D_DESIGN_TO_GAME_TRACE_MATRIX_V1", "schema mismatch")
    require(git_blob_sha(raw_catalog) == matrix.get("source_catalog_blob_sha"), "catalog git blob changed; refresh from current source")
    originals = catalog.get("rows")
    rows = matrix.get("rows")
    require(isinstance(originals, list) and len(originals) == 67, "catalog does not have 67 rows")
    require(isinstance(rows, list) and len(rows) == 67, "matrix must have all 67 rows")
    require(matrix.get("source_catalog_row_count") == len(originals), "catalog row count is stale")
    require({a["id"] for a in originals} == {b["CONCEPT_ID"] for b in rows}, "matrix feature ID set differs")
    require(len({a["id"] for a in originals}) == len(originals), "duplicate source catalog IDs")
    require(len({b["CONCEPT_ID"] for b in rows}) == len(rows), "duplicate matrix feature IDs")
    official = matrix.get("official_rc_observation", {})
    head = official.get("head")
    require(isinstance(head, str) and SHA40.fullmatch(head) is not None, "RC head SHA missing")
    require(official.get("head_source_build") == "SUCCESS", "historical RC build witness missing")
    require(official.get("verified_source_build_run", "").startswith("https://github.com/"), "official action URL missing")
    require(official.get("studio_play") == "NOT_TESTED", "do not fabricate engine evidence in snapshot")
    require(official.get("android") == "NOT_TESTED", "do not fabricate Android evidence in snapshot")
    require(official.get("owner_fun") == "NOT_TESTED", "do not fabricate owner acceptance in snapshot")
    staged = {"RC": 0, "SOURCE": 0, "IDEA": 0}
    by_domain = {x: 0 for x in DOMAINS}
    v3_rc = 0
    accepted = 0
    for original, r in zip(originals, rows):
        ident = original["id"]
        require(FIELDS.issubset(r), f"{ident}: required trace fields absent")
        require(r["CONCEPT_ID"] == ident and r["FEATURE_ID"] == ident, f"{ident}: ordered ID drift")
        require(r["MUST_BEHAVE"] == original["name"], f"{ident}: plan name altered")
        require(r["RELEASE_CLAIM_HISTORICAL"] == original["release"], f"{ident}: historical release altered")
        require(r["CATALOG_STAGE_CLAIM_HISTORICAL"] == original["stage"], f"{ident}: historical stage altered")
        require(r["RELEASE_REQUIRED"] is (original["release"] == "S1" or ident in RELEASE_OVERRIDES), f"{ident}: owner release override missing")
        require(r["ACTUAL_RC_HEAD"] == head, f"{ident}: evidence references another RC HEAD")
        require(r["DESIGN_SOURCE_URL_REV"].startswith("https://github.com/"), f"{ident}: source URL not pinned")
        require(r["DOMAIN"] in DOMAINS, f"{ident}: unknown quality domain")
        by_domain[r["DOMAIN"]] += 1
        require(r["GAP_TYPE"] in GAP_TYPES, f"{ident}: invalid gap type")
        require(bool(r["GAP_REASON"]) and bool(r["NEXT_ACTION"]) and bool(r["CLAIM_WRITER"]), f"{ident}: no owner/gap/action")
        require(r["ENGINE_PROOF"] in {"NOT_TESTED", "STUDIO_VERIFIED"}, f"{ident}: invalid engine proof")
        require(r["DEVICE_PROOF"] in {"NOT_TESTED", "ANDROID_VERIFIED"}, f"{ident}: invalid device proof")
        require(r["ART_GATE"] in {"ART_NO_GO", "ART_PASS"}, f"{ident}: invalid art gate")
        require(isinstance(r["REAL_SOURCE_PATHS_SHA"], list), f"{ident}: source manifest must be a list")
        for item in r["REAL_SOURCE_PATHS_SHA"]:
            require(SHA40.fullmatch(item.get("git_blob_sha", "")) is not None, f"{ident}: invalid candidate git blob")
            require(item.get("official_rc_adopted") is False, f"{ident}: candidate source cannot masquerade as RC")
            require(item.get("source_pr", "").startswith("#"), f"{ident}: missing original author PR")
        staged[original["stage"]] += 1
        adopted = r["V3_NEW_SOURCE_OFFICIAL_ADOPTED"]
        require(type(adopted) is bool and type(r["OWNER_ACCEPTED"]) is bool, f"{ident}: status must be boolean")
        if adopted:
            v3_rc += 1
            require(SHA40.fullmatch(r.get("FIX_SHA") or "") is not None, f"{ident}: official integration needs exact fix SHA")
            require(r.get("OFFICIAL_SAME_HEAD_RUN_URL", "").startswith("https://github.com/"), f"{ident}: same-head Actions proof missing")
            require(r.get("OFFICIAL_PLACE_BYTES", 0) > 0 and r.get("OFFICIAL_ZIP_BYTES", 0) > 0, f"{ident}: exact official binary sizes missing")
        if r["OWNER_ACCEPTED"]:
            accepted += 1
            require(adopted, f"{ident}: owner acceptance cannot precede official RC adoption")
            require(r["ENGINE_PROOF"] == "STUDIO_VERIFIED" and r["DEVICE_PROOF"] == "ANDROID_VERIFIED", f"{ident}: actual engine and Android proof missing")
            require(r["ART_GATE"] == "ART_PASS" and r["COMPETITIVE_EVIDENCE"], f"{ident}: art / competitive proof missing")
    require(all(by_domain.values()), "at least one of the eight domains has no rows")
    require(staged == matrix.get("historical_catalog_stats"), "historical RC/SOURCE/IDEA counts altered")
    require(matrix.get("verified_v3_new_official_adopted") == v3_rc, "V3 RC count inflated")
    require(matrix.get("verified_v3_owner_accepted") == accepted, "owner acceptance count inflated")
    return {"mapped": len(rows), "historical_claims": staged, "domains": dict(sorted(by_domain.items())),
            "verified_v3_official_adopted": v3_rc, "verified_owner_accepted": accepted}


def main() -> int:
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--catalog", type=Path, default=CATALOG)
    cli.add_argument("--matrix", type=Path, default=MATRIX)
    args = cli.parse_args()
    raw = args.catalog.read_bytes()
    report = validate(json.loads(raw), json.loads(args.matrix.read_text(encoding="utf-8")), raw)
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
