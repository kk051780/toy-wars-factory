#!/usr/bin/env python3
"""Run real extracted original Host deposit callback in pinned native Luau VM."""
import argparse
import subprocess
import tempfile
from pathlib import Path

START = ' prompt(deposit,"卵を納入","自分の城",function(p)'
END = " local vault=block("

def extract(source: str) -> str:
    if source.count(START) != 1:
        raise ValueError("HOST_DEPOSIT_CALLBACK_MISSING")
    beginning = source.index(START)
    ending = source.find(END, beginning)
    if ending < 0:
        raise ValueError("HOST_DEPOSIT_END_MISSING")
    fragment = source[beginning:ending]
    if fragment.count('if ok then session.refresh() end') != 1:
        raise ValueError("SUCCESS_ONLY_REFRESH_NOT_PRESENT")
    return fragment


def run(source_file: Path, luau: Path) -> str:
    fragment = extract(source_file.read_text(encoding="utf-8"))
    prefix = """
local callback
local deposit={}
local entry={id="7"}
local current={alive=true,heldEggs=2,vaultEggs=3}
local calls=0
local fail=false
local session={rules={castles={["7"]=current}}}
function session.refresh() calls+=1 end
local Rules={}
function Rules.depositEggs(state,owner,count)
 if fail then error("injected deposit transaction error") end
 local c=state.castles[owner]
 assert(c.alive and c.heldEggs>=count)
 c.heldEggs-=count
 c.vaultEggs+=count
end
local function prompt(part,action,label,fn)
 assert(part==deposit)
 callback=fn
end
"""
    suffix = """
assert(type(callback)=="function")
local function fresh(eggs,alive)
 current={alive=alive,heldEggs=eggs,vaultEggs=3}
 session.rules={castles={["7"]=current}}
 calls=0
 fail=false
end
fresh(2,true)
callback({UserId=7})
assert(current.heldEggs==0 and current.vaultEggs==5 and calls==1,"SUCCESS_UPDATE_ONCE")
fresh(1,true)
callback({UserId=8})
assert(current.heldEggs==1 and calls==0,"FOREIGN_OWNER_BLOCK")
fresh(1,false)
callback({UserId=7})
assert(current.heldEggs==1 and calls==0,"DEAD_OWNER_BLOCK")
fresh(0,true)
callback({UserId=7})
assert(current.vaultEggs==3 and calls==0,"EMPTY_CARRIER_BLOCK")
fresh(1,true)
fail=true
callback({UserId=7})
assert(current.heldEggs==1 and calls==0,"FAILED_DEPOSIT_NO_REFRESH")
fresh(1,true)
session.rules=nil
callback({UserId=7})
assert(calls==0,"MISSING_MATCH_RULES_BLOCK")
fresh(1,true)
callback({UserId=7})
callback({UserId=7})
assert(current.heldEggs==0 and calls==1,"REPEATED_PROMPT_NO_DUPLICATE")
print("GQ_DEPOSIT_REFRESH_ACTUAL_CALLBACK_NATIVE_7_7_PASS")
"""
    with tempfile.TemporaryDirectory() as d:
        f = Path(d) / "real_deposit_callback_runner.luau"
        f.write_text(prefix + fragment + suffix, encoding="utf-8")
        p = subprocess.run([str(luau), str(f)], capture_output=True, text=True, check=False)
        if p.returncode or "GQ_DEPOSIT_REFRESH_ACTUAL_CALLBACK_NATIVE_7_7_PASS" not in p.stdout:
            raise RuntimeError(f"NATIVE_LUAU_FAILED code={p.returncode}: {p.stdout} {p.stderr}")
        return p.stdout.strip()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--luau", type=Path, required=True)
    args = parser.parse_args()
    print(run(args.source, args.luau))
