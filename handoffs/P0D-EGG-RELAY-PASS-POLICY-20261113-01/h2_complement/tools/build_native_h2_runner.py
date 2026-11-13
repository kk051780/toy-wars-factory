#!/usr/bin/env python3
"""SOURCE-LOCKED native Luau H2 test generator, from exact canonical RC56 H2.
Used by isolated feature QA workflow; not by official #220 canonical RC.
"""
from pathlib import Path
import argparse, hashlib, subprocess, tempfile
ROOT=Path(__file__).resolve().parents[1]
ORIGINAL=ROOT/"tests/H2FiveEggRules.AUTHOR_LOCKED.luau"
PATCH=ROOT/"H2OnlyRelayV2.patch"
CASES=ROOT/"tests/native_h2_relay_cases.luau"
BASE_BLOB="0999d69391c176b9b95b04c5444d822e63d7ce04"
PATCH_BLOB="68f3df613ad548ab56e755adf91d797a979e8552"
CASES_BLOB="164558206f7c24215c18631b803d4e5b4d88815a"
RESULT_BLOB="a3cc4894db6db04f760e1cd615c2ec5c9444734f"
EXPECTED_CASES=48

def blob(data:bytes)->str:
    return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\\0"+data).hexdigest()

def checked(path:Path, expected:str)->bytes:
    data=path.read_bytes()
    assert blob(data)==expected,("SOURCE_LOCK_MISMATCH",str(path))
    return data

def build(output:Path)->str:
    source=checked(ORIGINAL,BASE_BLOB)
    checked(PATCH,PATCH_BLOB)
    cases=checked(CASES,CASES_BLOB)
    assert cases.count(b'check("') == 21,"NATIVE_TEST_SOURCE_CASES_DRIFT"
    assert b'assert(n==48,' in cases and b'P0D_H2_RELAY_NATIVE_48_OF_48_PASS' in cases
    with tempfile.TemporaryDirectory() as temp:
        work=Path(temp)
        current=work/"H2FiveEggRules.luau"
        current.write_bytes(source)
        for trailing in (["--dry-run"],[]):
            result=subprocess.run([
                "patch","-p1","--fuzz=0","--batch","--forward",
                "--reject-file=-","-d",str(work),"-i",str(PATCH.resolve()),
                *trailing],capture_output=True,text=True)
            assert result.returncode==0,("EXACT_PATCH_REJECTED",result.stdout,result.stderr)
        result=current.read_bytes()
        assert blob(result)==RESULT_BLOB,"PATCHED_H2_BLOB_DRIFT"
        # Test strict reversal, including provenance to exact original source.
        undone=subprocess.run(["patch","-R","-p1","--fuzz=0","--batch",
            "--reject-file=-","-d",str(work),"-i",str(PATCH.resolve())],
            capture_output=True,text=True)
        assert undone.returncode==0,("PATCH_ROLLBACK_FAILED",undone.stderr)
        assert current.read_bytes()==source,"ORIGINAL_NOT_FULLY_RECOVERED"
    code="-- GENERATED EXACT original H2 + V2 patch. Native Luau CLI ONLY; NOT STUDIO.\\n"
    code+="local Rules=(function()\\n"+result.decode("utf-8")+"end)()\\n"
    code+=cases.decode("utf-8")
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(code,encoding="utf-8")
    return hashlib.sha256(code.encode("utf-8")).hexdigest()

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--out",required=True,type=Path)
    args=parser.parse_args()
    sha=build(args.out)
    print("H2_NATIVE_48_RUNNER_SOURCE_LOCK_AND_EXACT_ROLLBACK_PASS",sha)
