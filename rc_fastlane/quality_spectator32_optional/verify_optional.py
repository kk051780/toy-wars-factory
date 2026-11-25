#!/usr/bin/env python3
"""Certify an RC-registered optional 32-source profile, never gameplay itself.

The pinned #634 selector separately verifies 31 unchanged source bytes/classes and
actual 32-script Rojo XML; this gate binds that proof to the canonical RC profile,
current 8-domain artifact, native callbacks and conservative rollout restrictions.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

PROFILE="eggrumble_v3_spectate32_studio"
AUTHOR="c39b2d3cc481052940b9d11a6fc695261a9b1e40"
DOMAIN_NAMES={"characters","field","battle","castle","neutral","items","lobby","balance"}
MARKERS=("NATIVE_SPECTATOR_REAL_CLIENT_LIFECYCLE_PASS",
         "NATIVE_SPECTATOR_CROSS_MODE_ISOLATION_PASS",
         "NATIVE_SPECTATOR_RESET_FLAG_PASS",
         "NATIVE_SPECTATOR_ARENA_REMOVAL_PASS")

def check(ok:bool,reason:str):
    if not ok:
        raise ValueError("RED_GQ470_OPTIONAL32_"+reason)

def contract(meta,active,base):
    check(meta.get("schema")=="P0D_GQ470_OPTIONAL32_SOURCE_PROFILE_V1","SCHEMA")
    check(meta.get("canonical_branch")=="rc/p0d-s1-kids-rc01","CANONICAL_BRANCH")
    check(meta.get("profile")==PROFILE and meta.get("base_profile")=="eggrumble_v3_31",
          "PROFILE")
    check(meta.get("source_count")==32 and meta.get("base_count")==31,"COUNTS")
    check(meta.get("enabled_as_optional_profile") is True and
          meta.get("default_selected") is False and
          meta.get("production_enabled") is False and
          meta.get("publish_authorized") is False and
          meta.get("studio_only_original") is True,"PUBLICATION_FENCE")
    author=meta.get("original_author",{})
    check(author.get("git_blob")==AUTHOR and
          author.get("commit")=="eb38aa60b69ed0bdd80fb7ea0dd10cf230345c20"
          and author.get("script_name")=="EGGRUMBLE_EliminatedSpectate"
          and author.get("class")=="LocalScript","ORIGINAL_AUTHOR_SOURCE_LOCK")
    check(meta.get("existing_prep_reuse",{}).get("commit")==
          "fed9cbb5680d40c68a2e1395e9b84276d7868fb9",
          "PINNED_EXISTING_PREP_634")
    check(meta.get("current_selected31")==
          "AUTO_SOURCE_EXACT_CURRENT_CANONICAL31_PLACE" and
          meta.get("current_selected31_resolver")==
          "rc_fastlane/quality_spectator32_optional/resolve_current31.py",
          "LATEST_31_AUTO_MATCH_NOT_SELECTED")
    check(active.get("active_profile")=="rich51","LIVE_S1_PROFILE_CHANGED")
    profiles=active.get("source_profiles",{})
    check(profiles.get("eggrumble_v3_31",{}).get("source_count")==31,
          "PREVIOUS_31_PROFILE_LOST")
    optional=profiles.get(PROFILE,{})
    check(optional.get("source_count")==32 and optional.get("default_selected") is False
          and optional.get("production_enabled") is False
          and optional.get("source_manifest")==
              "rc_fastlane/EGGRUMBLE_V3_SPECTATE32_OPTIONAL.json",
          "OPTIONAL_PROFILE_NOT_REGISTERED_SAFELY")
    check(base.get("profile")=="eggrumble_v3_31" and base.get("source_count")==31,
          "CANONICAL_31_MANIFEST_CHANGED")
    flags=base.get("feature_flags",{})
    check(len(flags)>=40 and all(v is True for v in flags.values()),
          "PREVIOUS_FEATURE_FLAG_DISABLED")
    for flag in ("LOBBY_QUEUE_ETA_615","MATCH_DEADLINE_DRAW_499","BEAST_REAL_ESCORT_618",
                 "ZOMBIE_GUARD_CASTLE_LEASH_582","ITEM_CURRENT_SESSION_525","BOT_SIEGE_TARGET_PACING_527",
                 "POSTWIN_LATE_CARRIER_DEATH_FREEZE_509","GQ81_CONFIRMED_HIT_042_V3_PORT_20261117"):
        check(flags.get(flag) is True,"NEWEST_AUTHOR_LOST_"+flag)
    return len(flags)

def verify(meta,active,base,receipt,gq8,match,native,mutants,place,head,event):
    flags=contract(meta,active,base)
    check(len(head)==40 and all(c in "0123456789abcdef" for c in head),
          "HEAD_NOT_40_SHA")
    check(meta.get("base_official_head")==
          "7b3e055bae93ea71a89f981c4e78e8ab72996ae9","BASE_HEAD_DRIFT")
    check(receipt.get("source_count")==32
          and receipt.get("rojo_source_class_exact")=="32/32"
          and receipt.get("existing_gameplay_sources_unchanged")==31
          and receipt.get("original_spectator_blob")==AUTHOR
          and receipt.get("formal_rc_adopted") is False,
          "ORIGINAL_634_NATIVE_ROJO_SOURCE_PROOF_FAILED")
    check(receipt.get("place_sha256")==hashlib.sha256(place).hexdigest() and
          receipt.get("place_bytes")==len(place),"ACTUAL_ROJO_BYTES_DIFFER")
    check(gq8.get("script_count")==31
          and gq8.get("verified_flag_count")==flags
          and set(gq8.get("domains",{}))==DOMAIN_NAMES
          and gq8.get("official_rc_head")==head,
          "GQ8_8_DOMAIN_32_FLAGS_31_ORIGINAL_PROOF")
    check(match.get("schema")=="GQ470_CANONICAL31_ACTUAL_PLACE_MATCH_V1" and
          match.get("actual_script_source_class_exact")==31 and
          match.get("current_project_source_count")==31 and
          match.get("matching_project_count",0)>=1 and
          match.get("original_selector_reused") is True and
          match.get("publish_authorized") is False,
          "CANONICAL_PLACE_SOURCE_MATCH_RECEIPT")
    check(match.get("current_canonical_place_sha256")==gq8.get("studio_place_sha256")
          and match.get("current_canonical_place_bytes")==gq8.get("studio_place_bytes"),
          "CURRENT31_NOT_ACTUAL_BUILT_GQ8_PLACE")
    for marker in MARKERS:
        check(marker in native,"ORIGINAL_REAL_LUAU_LIFECYCLE_"+marker)
    for mutant in ("elimination","mode","recovery"):
        check("REJECTED_"+mutant in mutants,"MUTANT_SURVIVED_"+mutant)
    official=event=="push"
    return {
       "schema":"P0D_GQ470_OPTIONAL32_SOURCE_PROFILE_TRUE_ROJO_V1",
       "head":head,"profile":PROFILE,
       "status":("OFFICIAL_RC_OPTIONAL32_SOURCE_PROFILE_NOT_PRIMARY"
                 if official else "PREMERGE_OPTIONAL32_CANDIDATE_NOT_FORMAL_RC"),
       "official_rc_branch_profile_registered":official,
       "default_selected":False,"production_enabled":False,
       "existing31_source_class_byte_exact":31,
       "source_count":32,"rojo_source_class_exact":"32/32",
       "canonical31_source_proof":match["current_canonical_place_sha256"],
       "canonical31_source_path":match["selected_project"],
       "place_bytes":len(place),"place_sha256":hashlib.sha256(place).hexdigest(),
       "gq8_eight_domains":"PASS","gq8_existing_enabled_flags":flags,
       "original_author_blob":AUTHOR,
       "real_original_native_lifecycle":"PASS",
       "mutant_rejections":"3/3",
       "studio_2client":"NOT_TESTED","android_15min":"NOT_TESTED",
       "owner_fun":"NO_GO","publish_authorized":False,
       "rollback":"Unselect registered optional32; existing 31 original Script Source/Class unchanged"
    }

def main():
    p=argparse.ArgumentParser()
    for key in ("manifest","active","base-manifest","intake-receipt","gq8-receipt",
                "match-receipt","native-log","mutation-log","place","out"):
        p.add_argument("--"+key,required=True,type=Path)
    p.add_argument("--head",required=True)
    p.add_argument("--event",required=True,choices=("push","pull_request"))
    a=p.parse_args()
    def read(path):
        return json.loads(path.read_text(encoding="utf-8"))
    result=verify(read(a.manifest),read(a.active),read(a.base_manifest),
                  read(a.intake_receipt),read(a.gq8_receipt),read(a.match_receipt),
                  a.native_log.read_text(encoding="utf-8"),
                  a.mutation_log.read_text(encoding="utf-8"),
                  a.place.read_bytes(),a.head,a.event)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,ensure_ascii=False,indent=2,sort_keys=True)+"\n",
                     encoding="utf-8")
    print("GQ470_OPTIONAL32_CURRENT31_PRESERVED_ROJO32_NATIVE_MUTANT_GQ8_PASS",
          result["place_bytes"])

if __name__=="__main__":
    main()
