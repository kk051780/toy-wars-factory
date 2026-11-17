#!/usr/bin/env python3
"""Actual extracted original #503 pure LOD function executed in Native Luau.
Mutant changes 40-stud near protection to zero; native must flag regression.
"""
import argparse
from pathlib import Path
from patch_fx import mapping,TARGET,PURE
NATIVE='''local assertCase=function(v,msg) assert(v,msg) end
<<FUNCTION>>
assertCase(fxShouldHide("FLASH",1000,true,true,128,false)==false,"GQ503_CORE_PROTECTED")
assertCase(fxShouldHide("ULTIMATE",1000,true,true,128,false)==false,"GQ503_ULTIMATE_PROTECTED")
assertCase(fxShouldHide("SECONDARY",15,true,true,128,false)==false,"GQ503_NEAR_MUTANT_RED")
assertCase(fxShouldHide("SECONDARY",40,true,true,128,false)==false,"GQ503_NEAR_40")
assertCase(fxShouldHide("SECONDARY",200,true,false,0,false)==true,"GQ503_TOUCH_DISTANCE")
assertCase(fxShouldHide("SECONDARY",90,false,false,0,false)==false,"GQ503_DESKTOP_NEAR")
assertCase(fxShouldHide("SECONDARY",95,true,false,0,false)==true,"GQ503_TOUCH_FAR")
assertCase(fxShouldHide("SECONDARY",56,true,true,0,false)==false,"GQ503_REDUCED_HYSTERESIS")
assertCase(fxShouldHide("SECONDARY",60,true,true,0,false)==true,"GQ503_REDUCED_FAR")
assertCase(fxShouldHide("SECONDARY",90,true,false,100,false)==true,"GQ503_CROWD_BUDGET")
assertCase(fxShouldHide("SECONDARY",100,true,false,0,true)==true,"GQ503_HYSTERESIS_STABLE_HIDDEN")
assertCase(fxShouldHide("SECONDARY",0/0,true,false,0,false)==false,"GQ503_NAN_FAIL_VISIBLE")
print("GQ503_ORIGINAL_FX_LOD_NATIVE12_CASES_PASS")
'''
def generate(project:Path,out:Path,mutant:Path):
 _,all=mapping(project.resolve(strict=True))
 src=all[TARGET].read_text(encoding="utf8")
 if src.count(PURE)!=1:raise ValueError("RED_NO_CURRENT_SOURCE_PURE_LOD")
 out.write_text(NATIVE.replace("<<FUNCTION>>",PURE),encoding="utf8")
 altered=PURE.replace('if kind~="SECONDARY" then return false end','if false then return false end')
 if altered==PURE:raise ValueError("RED_MUTANT_NO_GUARD")
 mutant.write_text(NATIVE.replace("<<FUNCTION>>",altered),encoding="utf8")
 print("GQ503_EXACT_SOURCE_FX_BUDGET_NATIVE_AND_MUTANT_READY")
if __name__=="__main__":
 a=argparse.ArgumentParser()
 a.add_argument("--project",type=Path,required=True)
 a.add_argument("--out",type=Path,required=True)
 a.add_argument("--mutant",type=Path,required=True)
 q=a.parse_args();generate(q.project,q.out,q.mutant)
