"""Execute the selected surf constructor under Native Luau with instrumented parts."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess

from prepare import NEW, OLD, patch, unpatch


HARNESS = r"""
local parts={}
local Instance={new=function(class)
 assert(class=="Part")
 local p={Shape="Block",CastShadow=true,CanQuery=true,Destroying={Connect=function(_,fn)
  assert(type(fn)=="function")
 end}}
 table.insert(parts,p)
 return p
end}
local Enum={SurfaceType={Smooth="Smooth"},Material={SmoothPlastic="Matte"},PartType={Cylinder="Cylinder"}}
local Vector3={new=function(x,y,z) return {X=x,Y=y,Z=z} end}
local Color3={fromRGB=function(r,g,b) return {R=r,G=g,B=b} end}
local poses={}
poses.__mul=function(p,r) return {X=p.X,Y=p.Y,Z=p.Z,Yaw=r.Yaw} end
local CFrame={new=function(x,y,z) return setmetatable({X=x,Y=y,Z=z,Yaw=0},poses) end,
 Angles=function(rx,ry,rz)
  assert(rx==0 and rz==0)
  return {Yaw=ry}
 end}
local scene={}
local x,y,shoreZ=140,20,200
"""

CHECK = r"""
local function inspect(start)
 table.clear(parts)
 local live=populate(start)
 assert(live==start+6 and #parts==6)
 for i,p in ipairs(parts) do
  assert(p.Name=="ShoreFoam_"..i and p.Parent==scene)
  assert(p.Anchored and not p.CanCollide and not p.CanTouch)
  assert(p.Material=="Matte" and p.Size.Y==0.10)
  assert(p.CFrame.X==x-265+(i-1)*106)
  assert(math.abs(p.CFrame.Y-y-0.21)<1e-7)
  local yaw=p.CFrame.Yaw
  local halfZ=(p.Size.X*math.abs(math.sin(yaw))+p.Size.Z*math.abs(math.cos(yaw)))/2
  assert(p.CFrame.Z-halfZ>shoreZ-83, "public dock overlap")
  if selected then
   assert(p.Shape=="Cylinder" and not p.CanQuery and not p.CastShadow and p.Transparency==.33)
   assert(p.CFrame.Z~=shoreZ-63 and yaw~=0 and p.Color.R<225)
   assert((yaw>0)==(i%2==0))
  else
   assert(p.Shape=="Block" and p.CanQuery and p.Transparency==.19)
   assert(p.CFrame.Z==shoreZ-63 and yaw==0 and p.Color.R==225)
  end
 end
end
inspect(0)
inspect(89)
local accepted,why=pcall(populate,90)
assert(not accepted and string.find(why,"EGGRUMBLE_LSS_PART_BUDGET",1,true))
print("SHOREFOAM_6_PARTS_DOCK_CLEAR_AND_95_LIMIT_PASS",selected)
"""


def selected_region(source: str, start: str, stop: str) -> str:
    assert source.count(start) == 1
    return source[source.index(start):source.index(stop, source.index(start))]


def make_program(source: str, candidate: bool) -> str:
    body = NEW if candidate else OLD
    assert source.count(body) == 1 and source.count("local MAX_PARTS_PER_WORLD = 95") == 1
    assert source.count("params.RespectCanCollide=true") == 2
    assert source.count("overlap.RespectCanCollide=true") == 1
    block = selected_region(source, "local function block(", "local function prompt(")
    put = selected_region(source, " local function put(", " local function station(")
    flag = "true" if candidate else "false"
    return (HARNESS + block + f"local selected={flag}\n"
            + "local MAX_PARTS_PER_WORLD=95\nlocal function populate(liveParts)\n"
            + put + body + "\n return liveParts\nend\n" + CHECK)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    cli = argparse.ArgumentParser(description=__doc__)
    for option in ("off", "on", "luau", "out"):
        cli.add_argument("--" + option, type=Path, required=True)
    args = cli.parse_args()
    baseline = args.off.read_bytes().decode("utf-8")
    selected = args.on.read_bytes().decode("utf-8")
    assert patch(baseline) == selected and unpatch(selected) == baseline
    args.out.mkdir(parents=True, exist_ok=False)
    logs = {}
    for arm, source in (("OFF", baseline), ("ON", selected)):
        program = args.out / (arm + ".luau")
        program.write_bytes(make_program(source, arm == "ON").encode())
        result = subprocess.run([str(args.luau.resolve()), str(program.resolve())],
                                capture_output=True, check=True)
        assert b"SHOREFOAM_6_PARTS_DOCK_CLEAR_AND_95_LIMIT_PASS" in result.stdout
        (args.out / (arm + ".log")).write_bytes(result.stdout)
        logs[arm] = {"program_sha256": sha(program), "stdout": result.stdout.decode().strip()}
    evidence = {"limits": "Native instrumented Part APIs, Studio visibility and Android NOT_TESTED",
                "off_source_sha256": sha(args.off), "on_source_sha256": sha(args.on),
                "native_sha256": sha(args.luau), "results": logs}
    (args.out / "receipt.json").write_bytes((json.dumps(evidence, indent=2) + "\n").encode())
    print("SHOREFOAM_NATIVE_ON_OFF_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
