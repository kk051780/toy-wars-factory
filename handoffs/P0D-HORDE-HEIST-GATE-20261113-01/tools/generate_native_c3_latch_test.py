#!/usr/bin/env python3
"""Source-bound native Luau exec of C3's original 34 + new epoch latch guards."""
from pathlib import Path
import argparse,runpy
ROOT=Path(__file__).resolve().parents[1]
path=ROOT/"tools/generate_native_solo_test.py"
old=runpy.run_path(str(path))
original_test=old["TESTS"]
assert "EXPECTED_34_ASSERTIONS" in original_test
source=(ROOT/"src/StudioSoloLatchRulesC3.luau").read_text("utf-8")
new_tests=r'''
eq(Solo.activePractice(true,true,1,1,0),true)
eq(Solo.activePractice(true,true,1,0,1),true)
eq(Solo.activePractice(false,true,1,1,0),false)
eq(Solo.activePractice(false,false,1,1,0),false)
eq(Solo.activePractice(true,false,1,1,0),false)
eq(Solo.activePractice(true,false,2,1,1),false)
eq(Solo.activePractice(true,true,2,1,1),false)
eq(Solo.activePractice(true,true,2,2,0),false)
eq(Solo.activePractice(true,true,1,0,0),false)
eq(Solo.activePractice(true,true,1,1,1),false)
eq(Solo.activePractice(true,true,0,0,0),false)
eq(Solo.activePractice(true,true,1.5,1,0),false)
eq(Solo.activePractice(true,true,1,0/0,0),false)
eq(Solo.activePractice(true,true,1,math.huge,0),false)
eq(Solo.activePractice("true",true,1,1,0),false)
eq(Solo.activePractice(true,nil,1,1,0),false)
assert(count==50,"C3_SOLO_NATIVE_EXPECTED_50_ASSERTIONS "..tostring(count))
print("P0D_C3_SOLO_LATCH_50_NATIVE_ASSERTIONS_PASS")
'''
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--write",type=Path,required=True)
    args=p.parse_args()
    args.write.write_text("local Solo=(function()\n"+source+"\nend)()\n"+
                          original_test+new_tests,encoding="utf-8")
    print("P0D_C3_NATIVE_REAL_SOLO_LATCH_WRITTEN")
if __name__=="__main__":main()
