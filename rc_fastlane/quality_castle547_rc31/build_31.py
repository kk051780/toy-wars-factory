#!/usr/bin/env python3
"""PR #547 immutable original author -> current 31-source Host -> Native/Rojo true Place."""
import argparse
import json
from pathlib import Path
import subprocess

import select_original_castle_boards as s


def run(*args):
    subprocess.run(list(map(str, args)), check=True)


def build(base: Path, out: Path, compiler: Path, rojo: Path) -> dict:
    author = Path("_gq547_original/quality_gameplay/v3_castle_board_distance_20261116")
    run("python3","-B","-m","unittest","discover","-v","-s",author/"tests","-p","test_contract.py")
    run("python3","-B","-m","unittest","discover","-v","-s",
        Path("rc_fastlane/quality_castle547_rc31"),"-p","test_selection.py")
    old_receipt = json.loads(Path("artifacts/gq539_official_select/GQ539_SELECTED31_RECEIPT.json")
                             .read_text(encoding="utf-8"))
    if not (old_receipt["script_count"] == 31
            and old_receipt["modified_source_count"] == 1
            and old_receipt["rollback_byte_exact"]):
        raise ValueError("RED prior #539 original host receipt changed")
    new = s.select(base, out, old_receipt["host_after_blob"])
    project = out/"GQ547_SELECTED31.project.json"
    _, actual = s.source_mapping(project)
    for source in actual.values():
        with open("/dev/null", "wb") as discard:
            subprocess.run([str(compiler),"--text",str(source)], stdout=discard, check=True)
    print("GQ547_SOURCE_31_NATIVE_COMPILER_PASS", flush=True)
    place = out/"GQ547_SELECTED31_TRUE_ROJO.rbxlx"
    run(rojo, "build", project, "-o", place)
    proof = s.verify(base, project, place)
    if not (proof["rojo_exact"] == "31/31"
            and proof["unchanged_other_scripts"] == 30
            and proof["rollback_byte_exact"]
            and new["modified_existing_scripts"] == 1
            and new["unchanged_existing_scripts"] == 30):
        raise ValueError("RED source/native/Rojo proof failed")
    if new["author547_fixed_head"] != s.AUTHOR_SHA:
        raise ValueError("RED original author fixed head drift")
    (out/"GQ547_ROJO_SOURCE_CLASS_RECEIPT.json").write_text(
        json.dumps(proof, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print("GQ547_ORIGINAL_CASTLE_CORE_VAULT_ONE_HOST_30_OTHERS_EXACT",
          proof["place_bytes"],proof["place_sha256"],flush=True)
    return proof


if __name__ == "__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--base",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--luau",type=Path,default=Path("/tmp/gq530_all31_native/luau-compile"))
    p.add_argument("--rojo",type=Path,default=Path("/tmp/gq530-all31-rojo"))
    args=p.parse_args()
    print(json.dumps(build(args.base,args.out,args.luau,args.rojo),indent=2))
