#!/usr/bin/env python3
"""Read-only independent QA on the POST-JAPANESE-HUD official S1 RC commit.

This must reject any official tree drift. 19 original game Luau source blobs
remain identical to the 30-file candidate. The 20th HUD is the exact native-
tested RESULTS-only copy from the separately verified 33-file composite.
Actual D07 native security replay runs against NEW official RC itself.
"""
import argparse
import sys
import subprocess

import native_actual_official_rc_gate as base

RC="5dc6c958ea5549b1e859d6d250e6179e731181fb"
OLD_RC="fffdda7024def24b6ce756c39fa6e0c2fa35b288"
BASE_SOURCE="b103389e2089f9ff5a08984fe2f8f6f02aa8b1bc"
COMPOSITE="0ca2b7ea9f29aa79727b2e7e53a01af093df5b90"
COMPOSITE_ROOT="handoffs/P0D-S1-FTUE-RESULT-COMPOSITE-20261112-01/candidate/"
OLD_ROOT="handoffs/P0D-S1-FTUE-ON-D07D08-SPATIAL-LOBBY-20261112-01/candidate/"
SOURCE_TREE="01aede07b64973a32ba02647c10a9e8b8f8c3285"
NEW_HUD_SHA="458a23e83d261c51b3bec174e36e183960532f8c"
OLD_HUD_SHA="7a699f35cd3f5e7cf6178f7a45a71d0ead3247c5"
HUD="src/client/HUD.client.luau"

def guard_flags(game,release,selection,receipt,subtree):
    base.guard(game.count("local CANONICAL_S1_ENABLED = false")==1,
               "CANONICAL_FLAG_NOT_OFF")
    base.guard(game.count("local D07_D08_RELEASE_REVIEW_APPROVED = false")==1,
               "D07_REVIEW_FLAG_NOT_OFF")
    base.guard(game.count("remote.OnServerEvent:Connect(")==1,
               "DUPLICATED_NETWORK_AUTHORITY")
    base.guard(release["first_release_authorized"] is False and
               release["monetization_enabled"] is False and
               release["roblox_studio_2client"]=="NOT_TESTED_CURRENT_RC",
               "FORGED_RELEASE_STATUS")
    base.guard(release["source_git_tree_sha"]==SOURCE_TREE and
               release["source_hud_overlay_commit"]==COMPOSITE and
               release["source_original_luau_files_unchanged"]==19 and
               release["client_hud_source_updated_exact"] is True,
               "STALE_OR_FORGED_HUD_STATUS")
    base.guard(selection["source_git_tree_sha"]==subtree and
               selection["source_candidate_fixed_sha"]==BASE_SOURCE and
               selection["source_import_commit"]==base.IMPORT_COMMIT and
               selection["selected_result_hud_composite_commit"]==COMPOSITE and
               selection["selected_result_hud_blob_sha1"]==NEW_HUD_SHA and
               selection["source_and_flags"]["CANONICAL_S1_ENABLED"] is False and
               selection["source_and_flags"]["D07_D08_RELEASE_REVIEW_APPROVED"] is False,
               "FORGED_FINAL_RC_SOURCE_SELECTION")
    hud=receipt["selected_client_result_hud"]
    base.guard(receipt["previous_rc_commit"]==base.OLD_RC and
               receipt["import_commit"]==base.IMPORT_COMMIT and
               receipt["candidate_source_commit"]==BASE_SOURCE and
               receipt["src_subtree_sha"]==subtree and
               receipt["source_luau_count"]==20 and
               receipt["owner_public_release_approved"] is False and
               receipt["independent_actual_RC_QA"]=="NOT_TESTED" and
               hud["source_commit"]==COMPOSITE and
               hud["source_blob_sha1"]==NEW_HUD_SHA and
               hud["base_blob_sha1"]==OLD_HUD_SHA,
               "FORGED_RC_HUD_RECEIPT")

def verify_exact_diff(repo):
    latest=base.reltree(repo,RC,base.RC_ROOT)
    prior=base.reltree(repo,OLD_RC,base.RC_ROOT)
    existing={p:sha for p,sha in prior.items() if p.startswith("src/")}
    current={p:sha for p,sha in latest.items() if p.startswith("src/")}
    base.guard(len(existing)==20 and len(current)==20,
               "NOT_EXACTLY_TWENTY_LUAU")
    delta={p for p in existing if current.get(p)!=existing[p]}
    base.guard(delta=={HUD},"UNEXPECTED_GAME_SOURCE_CHANGE "+str(sorted(delta)))
    base.guard(existing[HUD]==OLD_HUD_SHA and current[HUD]==NEW_HUD_SHA,
               "HUD_SCOPE_OR_SOURCE_MISMATCH")
    first={p:sha for p,sha in base.reltree(repo,BASE_SOURCE,OLD_ROOT).items()
           if p.startswith("src/")}
    composite={p:sha for p,sha in base.reltree(repo,COMPOSITE,COMPOSITE_ROOT).items()
               if p.startswith("src/")}
    base.guard(set(first)==set(current)==set(composite),
               "SOURCE_LUAU_INVENTORY_DIFFERENCE")
    base.guard(current==composite,"RC_DIFFERS_FROM_NATIVE_TESTED_FULL_COMPOSITE")
    unchanged=0
    for path in current:
        if path==HUD: continue
        base.guard(first[path]==current[path],
                   "UNEXPECTED_NON_HUD_MODIFICATION "+path)
        unchanged+=1
    base.guard(unchanged==19,"EXPECTED_NINETEEN_ORIGINAL_SOURCES")
    print("P0D_OFFICIAL_RC_UPDATED_HUD_DIFF_PASS unchanged_original=19/19 patched_HUD=1/1 exact_native_tested_composite=20/20")

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--repo",required=True)
    parser.add_argument("--luau",required=True)
    args=parser.parse_args()
    base.RC=RC
    base.CAND=COMPOSITE
    base.CAND_ROOT=COMPOSITE_ROOT
    base.SOURCE_SHA=SOURCE_TREE
    base.guard_flags=guard_flags
    verify_exact_diff(args.repo)
    base.verify(args.repo)
    base.actual_native_against_rc(args.repo,args.luau)
    print("P0D_LATEST_OFFICIAL_RC_NATIVE_QA_PASS immutable_commit="+RC)
    return 0

if __name__=="__main__":
    try: sys.exit(main())
    except (OSError,RuntimeError,ValueError,UnicodeError,subprocess.TimeoutExpired) as e:
        print("P0D_LATEST_OFFICIAL_RC_NATIVE_BLOCKED "+str(e),file=sys.stderr)
        sys.exit(1)
