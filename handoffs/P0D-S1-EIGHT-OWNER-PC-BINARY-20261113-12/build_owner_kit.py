#!/usr/bin/env python3
"""Build actual eight-safe OWNER PC handoff from ORIGINAL immutable CI artifact.

ONLY runs on GitHub Actions or explicit local read-only downloads. No Studio,
publishing, main updates, writes to existing user folders, or network calls.
"""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import os
import stat
import sys
import tempfile
import zipfile

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]/"releases/P0D_S1_KIDS_RC01"
ROJO_VERIFIER=HERE.parents[1]/"handoffs/P0D-S1-EIGHT-SAFE-HUD-FULL-REVIEW-20261113-11/verify_real_rojo.py"
import owner_pc as safe

def source_real_xml(raw: bytes) -> None:
    if not ROJO_VERIFIER.is_file():
        raise safe.Blocked("ORIGINAL_EIGHT_REVIEW_VERIFIER_MISSING")
    spec=importlib.util.spec_from_file_location("_locked_eight_rojo_real",ROJO_VERIFIER)
    if spec is None or spec.loader is None:
        raise safe.Blocked("UNREADABLE_ORIGINAL_ROJO_VERIFIER")
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    expected=module.expected_sources()
    module.verify_place(raw,expected)
    print("P0D_EIGHT_OWNER_ACTUAL_FULL_21_OF_21_SOURCE_BYTES_PASS")
    module.adversarial_controls(raw,expected)
    print("P0D_EIGHT_OWNER_ACTUAL_12_OF_12_BAD_XML_MUTANTS_REJECTED")

def compose(artifacts: Path, output: Path, staging: Path) -> dict:
    if not artifacts.is_dir() or artifacts.is_symlink():
        raise safe.Blocked("ORIGINAL_CI_ARTIFACT_DIR_INVALID")
    if not staging.is_dir() or staging.is_symlink():
        raise safe.Blocked("NEW_TEMP_STAGING_DIR_MISSING")
    expected={safe.PLACE,safe.RECEIPT}
    names={p.name for p in artifacts.iterdir()}
    if names!=expected:
        raise safe.Blocked("ORIGINAL_CI_ARTIFACT_FILE_SET_NOT_TWO")
    for item in artifacts.iterdir():
        if item.is_symlink() or not item.is_file():
            raise safe.Blocked("ORIGINAL_CI_ARTIFACT_SYMLINK_OR_DIR")
    orig=(artifacts/safe.PLACE).read_bytes()
    if len(orig)!=safe.ORIGINAL_BYTES or hashlib.sha256(orig).hexdigest()!=safe.ORIGINAL_SHA256:
        raise safe.Blocked("WRONG_ORIGINAL_REAL_CI_GAME")
    source_real_xml(orig)
    dst=staging/"P0D_EIGHT_OWNER_PC_BUNDLE_FILES"
    dst.mkdir(mode=0o700,exist_ok=False)
    originals={safe.PLACE:orig,safe.RECEIPT:(artifacts/safe.RECEIPT).read_bytes()}
    for name in safe.FILES:
        data=originals[name] if name in originals else (HERE/name).read_bytes()
        if name not in originals and (HERE/name).is_symlink():
            raise safe.Blocked("SOURCE_BUNDLE_SYMLINK")
        with (dst/name).open("xb") as f:
            f.write(data)
    manifest={
      "format":safe.MANIFEST_FORMAT,
      "files":{name:{"sha256":safe.sha((dst/name).read_bytes()),
                     "size":(dst/name).stat().st_size} for name in safe.FILES},
      "place_sha256":safe.ORIGINAL_SHA256,
      "studio_tested":False,
      "owner_publish_approved":False
    }
    (dst/safe.MANIFEST).write_text(
        json.dumps(manifest,ensure_ascii=False,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    good=safe.verify_files(safe.verify_folder(dst))
    if output.exists() or output.is_symlink() or not output.parent.is_dir():
        raise safe.Blocked("NO_OVERWRITE_OUTPUT_OR_PARENT_MISSING")
    # Build reproducible flat archive: exact file membership, no external paths.
    with output.open("xb") as dest:
        with zipfile.ZipFile(dest,"w",compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
            for name in (*safe.FILES,safe.MANIFEST):
                zi=zipfile.ZipInfo(name,date_time=(2026,11,13,0,0,0))
                zi.create_system=3
                zi.external_attr=(stat.S_IFREG|0o644)<<16
                zi.compress_type=zipfile.ZIP_DEFLATED
                z.writestr(zi,(dst/name).read_bytes(),compress_type=zipfile.ZIP_DEFLATED,compresslevel=9)
    again=safe.verify_zip(output)
    if again!=safe.verify_folder(dst):
        raise safe.Blocked("ARCHIVE_VS_STAGE_BYTES_MISMATCH")
    summary={"status":"EIGHT_ACTUAL_OWNER_BINARY_QA_ZIP_CREATED_NOT_STUDIO",
             "owner_pc_zip":str(output),"owner_pc_zip_sha256":safe.sha(output.read_bytes()),
             "owner_pc_zip_bytes":output.stat().st_size,
             "real_place_sha256":safe.ORIGINAL_SHA256,"real_place_bytes":safe.ORIGINAL_BYTES,
             "original_ci_run":safe.CI_RUN,"original_ci_artifact":safe.CI_ARTIFACT,
             "actual_scripts_exact":21,"bad_xml_mutants_rejected":12,
             "real_2client_studio":"NOT_TESTED","real_mobile":"NOT_TESTED",
             "scenario_count":30,"public_release_approved":False,
             "source_folder":str(dst)}
    print(json.dumps(summary,ensure_ascii=False,sort_keys=True,indent=2))
    return summary

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--original-artifact-dir",type=Path,required=True)
    p.add_argument("--output-zip",type=Path,required=True)
    p.add_argument("--scratch-parent",type=Path,required=True)
    a=p.parse_args(argv)
    try:
        if not a.scratch_parent.is_dir() or a.scratch_parent.is_symlink():
            raise safe.Blocked("SCRATCH_PARENT_INVALID")
        with tempfile.TemporaryDirectory(prefix="p0d_eight_owner_pc_",dir=a.scratch_parent) as tmp:
            compose(a.original_artifact_dir,a.output_zip,Path(tmp))
    except (safe.Blocked,ValueError,OSError,UnicodeError) as exc:
        print("P0D_EIGHT_OWNER_PC_BINARY_BUILD_BLOCKED "+str(exc),file=sys.stderr)
        return 2
    return 0

if __name__=="__main__":
    sys.exit(main())
