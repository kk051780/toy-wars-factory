#!/usr/bin/env python3
"""Run actual unmodified replay Luau functions in a small deterministic native VM service mock.

This harness is only for headless developer tests; not a Roblox Studio simulation.
"""
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "EGGRUMBLE_RoundReplay.luau"
TESTS = ROOT / "tests" / "EGGRUMBLE_RoundReplayNative.spec.luau"

PRELUDE = r'''-- Minimal headless substitute for the exact Roblox services the replay module uses.
local playersService={active={}}
function playersService:GetPlayerByUserId(userId:number):any
 return self.active[userId]
end
local studio=true
local runService={}
function runService:IsStudio() return studio end
local game={}
function game:GetService(name:string)
 if name=="Players" then return playersService end
 if name=="RunService" then return runService end
 error("replay unexpectedly requested Roblox service "..name)
end
local pending={}
local task={}
function task.delay(seconds:number,fn:()->())
 table.insert(pending,{seconds=seconds,fn=fn})
end
local CFrame={}
function CFrame.new(position:any) return {position=position} end
'''

def main(out: Path) -> None:
    source=SOURCE.read_text(encoding="utf-8").rstrip()
    trailer="\nreturn Replay"
    if not source.endswith(trailer):
        raise RuntimeError("The real replay module no longer ends with return Replay")
    if 'function Replay.schedule(' not in source or 'function Replay.resetHuman(' not in source:
        raise RuntimeError("Required replay function was removed or renamed")
    source=source[:-len(trailer)]
    tests=TESTS.read_text(encoding="utf-8")
    out.write_text(PRELUDE+"\n"+source+"\n\n"+tests+"\n",encoding="utf-8")

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--out",required=True,type=Path)
    args=parser.parse_args()
    main(args.out)
    print("Generated real-source native Luau round replay harness:",args.out)
