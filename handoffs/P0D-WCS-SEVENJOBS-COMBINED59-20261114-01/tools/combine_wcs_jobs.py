#!/usr/bin/env python3
"""Build one immutable 59-source PRIVATE candidate by composing:
  - exact official canonical 57 already assembled by #220's builder,
  - exact WCS F01 Source from official Draft PR #300 (one Script),
  - exact SevenJobs source from author Draft PR #297 (Game/HUD + one Module).

No writes to main or rc/p0d-s1-kids-rc01. This is only the #220 handoff input.
"""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile

ROOT = Path(__file__).resolve().parents[3]
WCS = ROOT / "rc_fastlane"
WCS_SOURCE = "server/WCS_CrystalCanyon.server.luau"
JOBS = ROOT / "_jobs" / "handoffs/P0D-RC-SEVEN-JOBS-PVE-V1-20261114-01"
JOBS_SOURCE = "server/SevenJobsRules.luau"
GAME = "server/Game.server.luau"
HUD = "client/HUD.client.luau"
AUTHOR_SHA = "98edf843fb8a8f6123c13a67745b216712bfe63d"
WCS_SHA = "db568966f9ef91159cd2489598e485e066064ec9"

def blob(raw: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()

def items(dist: Path) -> dict[str, bytes]:
    src = dist / "src"
    return {p.relative_to(src).as_posix():p.read_bytes()
            for p in sorted(src.rglob("*.luau"))}

def pinned_lock(dist: Path, before: dict[str, bytes], size: int) -> tuple[dict,dict]:
    pins = {name:blob(content) for name,content in sorted(before.items())}
    lock=json.loads((dist/"SOURCE_LOCK.json").read_text("utf8"))
    ext=json.loads((dist/"RC_FEATURE_LOCK.json").read_text("utf8"))
    assert len(before)==size
    assert lock["total_scripts"]==size and lock["blobs"]==pins, "SOURCE_LOCK_PIN_DRIFT"
    assert ext["total_sources"]==size and ext["source_gitblobs"]==pins, "FEATURE_LOCK_PIN_DRIFT"
    return lock,ext

def load_module(file: Path, name: str):
    spec=importlib.util.spec_from_file_location(name,file)
    assert spec is not None and spec.loader is not None, ("NO_AUTHORED_MODULE",file)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def combine(dist: Path) -> dict:
    assert JOBS.is_dir() and (JOBS/"tools/apply_seven_jobs.py").is_file(), "PINNED_AUTHOR_PR297_MISSING"
    assert WCS.is_dir() and (WCS/"apply_wcs_f01_c01.py").is_file(), "PR300_WCS_MODULE_MISSING"
    before57=items(dist)
    oldlock,oldext=pinned_lock(dist,before57,57)
    assert WCS_SOURCE not in before57 and JOBS_SOURCE not in before57
    assert GAME in before57 and HUD in before57
    original_project=(dist/"default.project.json").read_bytes()
    assert b'ScoutSpeciesPolicy' in before57[GAME] and b'SavedPvePolicy' in before57[GAME]
    # First apply the source-exact, independently OFF-switchable WCS from PR#300.
    wcs=load_module(WCS/"apply_wcs_f01_c01.py","p0d_author_pr300_wcs")
    assert wcs.FEATURE_ID=="WCS_F01_C01"
    assert wcs.apply(dist,"rich51",enabled_override=True) is True
    afterWCS=items(dist)
    pinned_lock(dist,afterWCS,58)
    assert len(afterWCS)==58
    assert sorted(set(afterWCS)-set(before57))==[WCS_SOURCE]
    assert all(afterWCS[k]==b for k,b in before57.items())
    assert blob(afterWCS[WCS_SOURCE])==wcs.FEATURE_GIT_BLOB

    # The author #297 7-job patch is exact-pinned to 57 original Game/HUD.
    # Run the unmodified author adapter on a disposable original57 sandbox,
    # not on the WCS58. That avoids relaxing source-count / SHA pins or
    # taking an old whole .rbxlx that could erase WCS.
    with tempfile.TemporaryDirectory(prefix="p0d_7jobs57_") as td:
        temp=Path(td)/"dist"
        shutil.copytree(dist,temp)
        (temp/"src"/WCS_SOURCE).unlink()
        (temp/"default.project.json").write_bytes(original_project)
        (temp/"SOURCE_LOCK.json").write_text(
            json.dumps(oldlock,indent=2,ensure_ascii=False)+"\n","utf8")
        (temp/"RC_FEATURE_LOCK.json").write_text(
            json.dumps(oldext,indent=2,ensure_ascii=False)+"\n","utf8")
        pinned_lock(temp,items(temp),57)
        jobs=load_module(JOBS/"tools/apply_seven_jobs.py","p0d_author_pr297_jobs")
        receipt=jobs.apply(temp)
        final_jobs=items(temp)
        assert len(final_jobs)==58
        assert sorted(set(final_jobs)-set(before57))==[JOBS_SOURCE]
        assert sorted(k for k in before57 if final_jobs[k]!=before57[k])==[HUD,GAME]
        assert all(final_jobs[k]==v for k,v in before57.items() if k not in (GAME,HUD))
        assert receipt["official_rc_adopted"] is False

        # Stage validated new final 59 inventory before writing WCS58.
        final59=dict(afterWCS)
        for name in (GAME,HUD,JOBS_SOURCE):
            final59[name]=final_jobs[name]
        assert len(final59)==59
        assert final59[WCS_SOURCE]==afterWCS[WCS_SOURCE]
        assert sorted(x for x in before57 if final59[x]!=before57[x])==[HUD,GAME]
        assert sorted(set(final59)-set(before57))==[JOBS_SOURCE,WCS_SOURCE]
        assert all(final59[x]==before57[x] for x in before57 if x not in (GAME,HUD))
        assert blob(final59[JOBS_SOURCE])=="a7253d36cb67df47d4ba65d35af212ed1eb7b5b2"
        assert final59[GAME].decode("utf8").count('remote.OnServerEvent:Connect(')==1
        assert final59[GAME].decode("utf8").count('remote.Name = "TrapRaidersS1Remote"')==1

        # Only private trial: both features explicitly on, independently
        # switchable off in Studio. Use original project attribute from PR#300.
        config=json.loads((dist/"default.project.json").read_text("utf8"))
        attrs=config["tree"]["ServerStorage"]["$attributes"]
        assert attrs["P0D_RC_ENABLE_WCS_F01_C01"] is True
        assert "P0D_RC_ENABLE_SEVEN_JOBS_PVE" not in attrs
        attrs["P0D_RC_ENABLE_SEVEN_JOBS_PVE"]=True

        # Validate originals/feature-lock inventory before the 3 source writes.
        latest=items(dist)
        pinned_lock(dist,latest,58)
        assert latest==afterWCS
        (dist/"src"/GAME).write_bytes(final59[GAME])
        (dist/"src"/HUD).write_bytes(final59[HUD])
        (dist/"src"/JOBS_SOURCE).write_bytes(final59[JOBS_SOURCE])
        (dist/"default.project.json").write_text(json.dumps(config,ensure_ascii=False,indent=2)+"\n","utf8")
        sourceLock,featureLock=pinned_lock_before_update=(
            json.loads((dist/"SOURCE_LOCK.json").read_text("utf8")),
            json.loads((dist/"RC_FEATURE_LOCK.json").read_text("utf8"))
        )
        pins={key:blob(raw) for key,raw in sorted(final59.items())}
        sourceLock["total_scripts"]=59
        sourceLock["blobs"]=pins
        sourceLock["rc_sevenjobs_plus_wcs_private59"]={
            "stage":"PRIVATE_CANDIDATE_NOT_OFFICIAL_RC",
            "wcs_author_commit":WCS_SHA,
            "jobs_author_commit":AUTHOR_SHA,
            "unchanged_original_scripts":55,
            "changed_existing_scripts":[GAME,HUD],
            "new_scripts":[JOBS_SOURCE,WCS_SOURCE],
            "wcs_original_unmodified":True,
            "one_game_remote_store":True,
            "engine_2client":"NOT_TESTED",
            "owner_FUN":"NOT_TESTED"}
        featureLock["total_sources"]=59
        featureLock["source_gitblobs"]=pins
        featureLock["feature_flags"]["SEVEN_JOBS_PVE_V1"]=True
        featureLock["combined_private_candidate"]="WCS_F01_C01 + SEVEN_JOBS_PVE_V1 NOT_RC"
        (dist/"SOURCE_LOCK.json").write_text(json.dumps(sourceLock,ensure_ascii=False,indent=2)+"\n","utf8")
        (dist/"RC_FEATURE_LOCK.json").write_text(json.dumps(featureLock,ensure_ascii=False,indent=2)+"\n","utf8")

    actual=items(dist)
    assert actual==final59 and len(actual)==59
    pinned_lock(dist,actual,59)
    summary={
        "status":"PRIVATE_RICH59_COMBINED_NATIVE_CANDIDATE_NOT_OFFICIAL_RC",
        "base_rc_head":"34d6d384d04ba1d4a394331a3e5c74f798e57a22",
        "author_wcs_pr300":WCS_SHA,
        "author_jobs_pr297":AUTHOR_SHA,
        "original_script_count":57,
        "total_script_count":59,
        "preserved_untouched_original_count":55,
        "two_existing_modified":[HUD,GAME],
        "two_new_scripts":[JOBS_SOURCE,WCS_SOURCE],
        "no_duplicated_game_remote":True,
        "two_independent_build_flags":True,
        "still_no_engine_studio_android_FUN":True,
        "no_main_or_rc_write":True
    }
    (dist/"P0D_WCS_JOBS59_RECEIPT.json").write_text(
        json.dumps(summary,ensure_ascii=False,indent=2)+"\n","utf8")
    print("P0D_WCS_PLUS_SEVEN_JOBS_ACTUAL_RICH57_TO_59_PRESERVE55_PASS")
    return summary

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--dist",type=Path,required=True)
    args=parser.parse_args()
    combine(args.dist)
