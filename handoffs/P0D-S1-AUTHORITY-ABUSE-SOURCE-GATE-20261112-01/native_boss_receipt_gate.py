#!/usr/bin/env python3
"""Native Luau exercise of exact original S1 GoroganAttackReceiptWindow.

No Roblox engine, networking or final damage authority is emulated here.
The runner checks the real 1828-byte Luau module by Git blob SHA first.
"""
from __future__ import annotations

import argparse
import hashlib
import pathlib
import re
import subprocess
import sys
import tempfile

SOURCE_COMMIT = "b103389e2089f9ff5a08984fe2f8f6f02aa8b1bc"
SOURCE_PATH = (
    "handoffs/P0D-S1-FTUE-ON-D07D08-SPATIAL-LOBBY-20261112-01/"
    "candidate/src/server/GoroganAttackReceiptWindow.luau"
)
SOURCE_BLOB = "bc8e4e954c06c1db8778649a84cda135ff56e9d1"

SCENARIOS = r'''
local checks = 0
local function expect(condition, code)
    checks += 1
    if not condition then error("ASSERT_" .. code .. "_N" .. tostring(checks), 0) end
end
local function cmd(roundId,eventId,attackId,x,y,z)
    return {
        kind = "STOMP_RESOLVE", roundId=roundId, eventId=eventId,
        attackId=attackId, center={x=x,y=y,z=z}
    }
end
local function rejected(packet,roundId,eventId,code)
    local gate=Window.new()
    local ok=gate:openFromCoreResult(packet,roundId,eventId)
    expect(ok==false, code.."_REJECT")
    expect(gate:attests(roundId,eventId,1)==false, code.."_NOT_OPEN")
    expect(gate:center(roundId,eventId,1)==nil, code.."_NO_CENTER")
end

local gate=Window.new()
expect(gate:attests("r1","e1",1)==false,"empty_window_attests")
expect(gate:center("r1","e1",1)==nil,"empty_window_center")
gate:close()
expect(gate:attests("r1","e1",1)==false,"close_empty")
rejected(nil,"r1","e1","nil_packet")
rejected(false,"r1","e1","false_packet")
rejected({},"r1","e1","empty_packet")
local badkind=cmd("r1","e1",1,0,0,0);badkind.kind="STOMP_WARNING"
rejected(badkind,"r1","e1","not_stomp_resolve")
local nopacket=cmd("r1","e1",1,0,0,0)
rejected(nopacket,"r2","e1","round_mismatch")
rejected(nopacket,"r1","e2","event_mismatch")
rejected(nopacket,"","e1","empty_round")
rejected(nopacket,"r1","","empty_event")
rejected(nopacket,"r:1","e1","punctuation_round")
rejected(nopacket,"r1","e:1","punctuation_event")
rejected(cmd(string.rep("r",65),"e1",1,0,0,0),string.rep("r",65),"e1","long_round")
rejected(cmd("r1",string.rep("e",65),1,0,0,0),"r1",string.rep("e",65),"long_event")

for _,a in ipairs({-10,-1,0,0.1,0.5,1.5,3.1,4,5,10,math.huge,-math.huge}) do
    rejected(cmd("r1","e1",a,0,0,0),"r1","e1","attack_bad")
end
for _,a in ipairs({"1",false,true,{}}) do
    rejected(cmd("r1","e1",a,0,0,0),"r1","e1","attack_type")
end
rejected(cmd("r1","e1",0/0,0,0,0),"r1","e1","attack_nan")

local invalidCenters={
    {x=0/0,y=0,z=0},{x=math.huge,y=0,z=0},
    {x=-math.huge,y=0,z=0},{x="0",y=0,z=0},
    {x=0,y=0/0,z=0},{x=0,y=math.huge,z=0},
    {x=0,y=0,z=0/0},{x=0,y=0,z=math.huge},
    {x=2048.1,y=0,z=0},{x=-2048.1,y=0,z=0},
    {x=0,y=-100.1,z=0},{x=0,y=700.1,z=0},
    {x=0,y=0,z=2048.1},{x=0,y=0,z=-2048.1},
}
for _,center in ipairs(invalidCenters) do
    local p=cmd("r1","e1",1,0,0,0);p.center=center
    rejected(p,"r1","e1","bad_center")
end
local emptycenter=cmd("r1","e1",1,0,0,0);emptycenter.center=nil
rejected(emptycenter,"r1","e1","missing_center")
local wrongcenter=cmd("r1","e1",1,0,0,0);wrongcenter.center="0"
rejected(wrongcenter,"r1","e1","wrong_center_type")

-- Valid Core STOMP receipt: strictly one active window, exact 3-part identity.
for r=1,64 do
    for a=1,3 do
        local rid="round_"..tostring(r)
        local eid="event_"..tostring(r)
        local packet=cmd(rid,eid,a,100+r,14+a,-(100+r))
        local w=Window.new()
        local ok=w:openFromCoreResult(packet,rid,eid)
        expect(ok==true,"valid_receipt")
        expect(w:attests(rid,eid,a)==true,"attests_exact")
        expect(w:attests(rid,eid,a+1)==false,"wrong_attack")
        expect(w:attests(rid.."_fake",eid,a)==false,"wrong_round")
        expect(w:attests(rid,eid.."_fake",a)==false,"wrong_event")
        expect(w:center(rid,eid,a+1)==nil,"wrong_center_attack")
        local center=w:center(rid,eid,a)
        expect(center~=nil and center.X==100+r and center.Y==14+a and center.Z==-(100+r),"trusted_center")
        local ok2=w:openFromCoreResult(packet,rid,eid)
        expect(ok2==false,"overlap_rejected")
        w:close()
        expect(w:attests(rid,eid,a)==false,"closed_attest")
        expect(w:center(rid,eid,a)==nil,"closed_center")
        local reopened=w:openFromCoreResult(packet,rid,eid)
        expect(reopened==true,"new_window_allowed")
        w:close()
    end
end
if checks<1700 then error("TOO_FEW_ASSERTIONS:"..tostring(checks),0) end
print("P0D_NATIVE_BOSS_RECEIPT_PASS assertions="..tostring(checks))
'''
MUTATIONS = [
    ("forged_core_resolve", 'cmd.kind~="STOMP_RESOLVE"', "false"),
    ("overlapping_stomp_window", "self.active~=nil", "false"),
    ("invalid_attack_id4", "cmd.attackId>3", "false"),
    ("nan_attack_center", "not finite(cmd.center.x)", "false"),
    ("stale_open_after_close", "    self.active=nil\nend\nreturn Window", "    -- self.active=nil\nend\nreturn Window"),
]


def original(repo: str) -> str:
    result = subprocess.run(
        ["git", "-C", repo, "show", f"{SOURCE_COMMIT}:{SOURCE_PATH}"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
    )
    if result.returncode != 0:
        raise RuntimeError("FIXED_SOURCE_NOT_FOUND")
    data = result.stdout
    sha = hashlib.sha1(
        b"blob " + str(len(data)).encode("ascii") + b"\0" + data
    ).hexdigest()
    if sha != SOURCE_BLOB:
        raise RuntimeError("SOURCE_GIT_BLOB_NOT_MATCHED " + sha)
    return data.decode("utf-8")


def run_native(luau: str, path: pathlib.Path, source: str) -> tuple[int, str]:
    program = (
        'local Vector3={new=function(x,y,z) return {X=x,Y=y,Z=z} end}\n'
        "local Window=(function()\n" + source + "\nend)()\n" + SCENARIOS
    )
    path.write_text(program, encoding="utf-8")
    proc = subprocess.run(
        [luau, str(path)], capture_output=True, text=True, check=False, timeout=20
    )
    return proc.returncode, proc.stdout + proc.stderr


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    parser.add_argument("--luau", required=True)
    args = parser.parse_args()
    src = original(args.repo)
    with tempfile.TemporaryDirectory(prefix="p0d_boss_receipt_") as tmp:
        path = pathlib.Path(tmp) / "native_boss_receipt.luau"
        code, output = run_native(args.luau, path, src)
        match = re.search(r"P0D_NATIVE_BOSS_RECEIPT_PASS assertions=(\d+)", output)
        if code != 0 or not match or int(match.group(1)) < 1700:
            raise RuntimeError("AUTHENTIC_MODULE_NATIVE_FAILED: " + output[-500:])
        print(match.group(0))
        for name, before, after in MUTATIONS:
            if src.count(before) != 1:
                raise RuntimeError("BAD_MUTATION_ANCHOR " + name)
            code, output = run_native(args.luau, path, src.replace(before, after, 1))
            if code == 0 or "P0D_NATIVE_BOSS_RECEIPT_PASS" in output:
                raise RuntimeError("UNDETECTED_SECURITY_MUTATION " + name)
            if "ASSERT_" not in output:
                raise RuntimeError("MUTATION_NOT_CAUGHT_BY_TEST " + name + " " + output[-300:])
            print("MUTATION_REJECTED " + name)
        print("P0D_NATIVE_BOSS_RECEIPT_NEGATIVE_CONTROLS=" + str(len(MUTATIONS)))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (RuntimeError, UnicodeError, OSError, subprocess.TimeoutExpired) as error:
        print("P0D_BOSS_RECEIPT_GATE_BLOCKED " + str(error), file=sys.stderr)
        sys.exit(1)
