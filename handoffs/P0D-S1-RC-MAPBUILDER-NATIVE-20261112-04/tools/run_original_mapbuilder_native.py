#!/usr/bin/env python3
"""Actual official S1 MapBuilder Roblox instance/geometry native Luau QA.

Executes whole original MapBuilder & Config at immutable Git blob SHAs, in
official native Luau with ONLY external Roblox instance/vector fakes. Tests
two-castle map placement, goals and disabled prompts, and 6 source mutations.
No real Roblox Studio, physics, mobile, map collisions or publication.
"""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import re
import subprocess
import sys
from tempfile import TemporaryDirectory

OFFICIAL_RC = "5dc6c958ea5549b1e859d6d250e6179e731181fb"
ROOT = "releases/P0D_S1_KIDS_RC01/"
BLOBS = {
    "MapBuilder": ("src/server/MapBuilder.luau", "d2127b8c20c8abd880a21f84aeeb706feeb14ce8"),
    "Config": ("src/shared/Config.luau", "ef10e4288e4732588116cd3e55d3d871ca803ff4"),
}

FAKES = r'''
-- Pure service/type doubles only. No project MapBuilder logic is rewritten.
local allNodes={}
local V={}
function V.new(x,y,z) return {X=x,Y=y,Z=z,__type="Vector3"} end
local Vector3=V
local CFrame={new=function(x,y,z) return {Position=V.new(x,y,z),__type="CFrame"} end}
local Color3={fromRGB=function(r,g,b) return {R=r,G=g,B=b,__type="Color3"} end,
 new=function(r,g,b) return {R=r,G=g,B=b,__type="Color3"} end}
local UDim2={fromOffset=function(x,y) return {x=x,y=y} end,
 fromScale=function(x,y) return {x=x,y=y} end}
local UDim={new=function(a,b) return {a=a,b=b} end}
local enumGroup=setmetatable({}, {__index=function(_,key) return key end})
local Enum={Material=enumGroup,Font=enumGroup,PartType=enumGroup}
local workspace={children={},ClassName="Workspace"}
function workspace:FindFirstChild(name)
 for _,obj in ipairs(self.children) do if obj.Name==name then return obj end end
 return nil
end
local Instance={}
function Instance.new(class)
 if class~="Part" and class~="Folder" and class~="BillboardGui"
   and class~="TextLabel" and class~="ProximityPrompt" then
   error("UNEXPECTED_MAP_BUILDER_CLASS "..tostring(class))
 end
 local n={ClassName=class,children={}}
 setmetatable(n,{
  __newindex=function(self,k,v)
    rawset(self,k,v)
    if k=="Parent" then
      if type(v)~="table" or type(v.children)~="table" then
        error("BAD_MAP_PARENT_"..tostring(class))
      end
      table.insert(v.children,self)
    end
  end
 })
 function n:FindFirstChild(name)
  for _,c in ipairs(self.children) do if c.Name==name then return c end end
  return nil
 end
 table.insert(allNodes,n)
 return n
end
local tests=0
local function eq(actual,expected,tag)
 tests+=1
 if actual~=expected then
  error("MAP_BUILDER_ASSERT_"..tag.." got="..tostring(actual).." expected="..tostring(expected),0)
 end
end
local function isNode(obj,class,tag)
 tests+=1
 if type(obj)~="table" or obj.ClassName~=class then
  error("MAP_BUILDER_ASSERT_"..tag.."_class",0)
 end
end
local function count(cls)
 local n=0
 for _,obj in ipairs(allNodes) do if obj.ClassName==cls then n+=1 end end
 return n
end
'''
TEST = r'''
local map=MapBuilder.build(Config)
isNode(map.model,"Folder","world_folder")
eq(map.model.Name,"TRAP_RAIDERS_S1","world_folder_name")
eq(workspace:FindFirstChild("TRAP_RAIDERS_S1"),map.model,"exact_workspace_mount")
eq(count("Part"),27,"expected_twentyseven_real_parts")
eq(count("Folder"),3,"one_world_and_two_castle_folders")
eq(count("ProximityPrompt"),4,"exact_four_interact_prompts")
eq(count("BillboardGui"),8,"eight_objective_billboards")
eq(count("TextLabel"),8,"eight_billboard_labels")
eq(count("RemoteEvent"),0,"no_second_remote")
eq(count("Script"),0,"no_second_game_script")
local floor=map.model:FindFirstChild("GrassArena")
isNode(floor,"Part","grass_arena_exists")
eq(floor.Size.X,250,"arena_horizontal_extent")
eq(floor.Size.Z,142,"arena_vertical_extent")
eq(floor.Position.Y,-3,"arena_floor_level")
local road=map.model:FindFirstChild("CenterRoad")
isNode(road,"Part","center_road_exists")
eq(road.Size.Z,24,"center_road_corridor")
eq(road.Position.Z,0,"corridor_alignment")
for _,side in ipairs({"RED","BLUE"}) do
 local d=if side=="RED" then -1 else 1
 local t=map.teams[side]
 isNode(t.core,"Part",side.."_castle_core")
 isNode(t.egg,"Part",side.."_egg")
 isNode(t.scorePad,"Part",side.."_delivery_pad")
 isNode(t.eggPrompt,"ProximityPrompt",side.."_egg_prompt")
 isNode(t.scorePrompt,"ProximityPrompt",side.."_score_prompt")
 eq(t.core.Position.X,d*107,side.."_castle_core_exact_x")
 eq(t.core.Position.Y,6.5,side.."_castle_core_exact_y")
 eq(t.egg.Position.X,d*98,side.."_egg_exact_x")
 eq(t.egg.Position.Z,-20,side.."_egg_exact_z")
 eq(t.scorePad.Position.X,d*82,side.."_pad_exact_x")
 eq(t.scorePad.Position.Z,20,side.."_pad_exact_z")
 eq(t.spawn.Position.X,d*68,side.."_spawn_exact_x")
 eq(t.spawn.Position.Y,5,side.."_spawn_exact_y")
 eq(t.spawn.Position.Z,0,side.."_spawn_exact_z")
 eq(t.eggPrompt.Parent,t.egg,side.."_egg_prompt_real_parent")
 eq(t.scorePrompt.Parent,t.scorePad,side.."_score_prompt_real_parent")
 eq(t.eggPrompt.Enabled,false,side.."_egg_disabled_until_active")
 eq(t.scorePrompt.Enabled,false,side.."_score_disabled_until_active")
 eq(t.eggPrompt.MaxActivationDistance,10,side.."_egg_prompt_distance")
 eq(t.scorePrompt.MaxActivationDistance,10,side.."_score_prompt_distance")
 eq(t.eggPrompt.HoldDuration,0.35,side.."_egg_prompt_hold")
 eq(t.scorePrompt.HoldDuration,0.35,side.."_score_prompt_hold")
 eq(t.egg.Anchored,true,side.."_egg_anchored")
 eq(t.scorePad.Anchored,true,side.."_pad_anchored")
 eq(t.core.Anchored,true,side.."_castle_core_anchored")
 eq(t.egg.CanCollide,false,side.."_egg_noncollidable")
 eq(t.scorePad.CanCollide,false,side.."_score_pad_noncollidable")
 eq(t.egg.CanTouch,false,side.."_egg_nonphysical_touch")
 eq(t.scorePad.CanTouch,false,side.."_pad_nonphysical_touch")
 eq(t.egg.CanQuery,true,side.."_egg_queryable")
 eq(t.scorePad.CanQuery,true,side.."_pad_queryable")
 -- Eggs, scoring pads, spawn and castle core are inside arena boundaries.
 for _,node in ipairs({t.egg,t.scorePad,t.core}) do
  local x,z=node.Position.X,node.Position.Z
  tests+=1
  if math.abs(x)>=125 or math.abs(z)>=71 then
   error("MAP_BUILDER_ASSERT_"..side.."_objective_outside_arena",0)
  end
 end
end
-- Source must fail-closed rather than overwriting an already-present Place map.
local passed,err=pcall(function() MapBuilder.build(Config) end)
eq(passed,false,"second_authoritative_map_refused")
tests+=1
if type(err)~="string" or not string.find(err,"S1_MAP_ALREADY_EXISTS",1,true) then
 error("MAP_BUILDER_ASSERT_duplicate_map_error",0)
end
-- Every original physical part remains anchored, queryable and touch-off.
for _,obj in ipairs(allNodes) do
 if obj.ClassName=="Part" then
  eq(obj.Anchored,true,"part_anchor_"..obj.Name)
  eq(obj.CanTouch,false,"part_no_touch_"..obj.Name)
  eq(obj.CanQuery,true,"part_query_"..obj.Name)
 end
end
if tests<135 then error("MAP_BUILDER_TOO_FEW_ACTUAL_CHECKS "..tostring(tests),0) end
print("P0D_NATIVE_ACTUAL_OFFICIAL_MAPBUILDER_PASS assertions="..tostring(tests))
'''
MUTATIONS = [
    ("unauthorized_egg_prompt_in_lobby", "p.Enabled = false", "p.Enabled = true",
     "MAP_BUILDER_ASSERT_RED_egg_disabled_until_active"),
    ("egg_placed_in_center", "Vector3.new(sign * 98, 2.5, -20)",
     "Vector3.new(sign * 16, 2.5, -20)", "MAP_BUILDER_ASSERT_RED_egg_exact_x"),
    ("spawn_outside_intended_castle", "CFrame.new(sign * 68, 5, 0)",
     "CFrame.new(sign * 196, 5, 0)", "MAP_BUILDER_ASSERT_RED_spawn_exact_x"),
    ("all_parts_unanchored", "p.Anchored = true", "p.Anchored = false",
     "MAP_BUILDER_ASSERT_RED_egg_anchored"),
    ("all_parts_touch_enabled", "p.CanTouch = false", "p.CanTouch = true",
     "MAP_BUILDER_ASSERT_RED_egg_nonphysical_touch"),
    ("all_eggs_block_player", "p.CanCollide = collide ~= false", "p.CanCollide = true",
     "MAP_BUILDER_ASSERT_RED_egg_noncollidable"),
]

def sha1_blob(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()

def original_files(repo: str) -> dict[str, str]:
    actual = {}
    for key, (path, digest) in BLOBS.items():
        p = subprocess.run(
            ["git", "-C", repo, "show", OFFICIAL_RC + ":" + ROOT + path],
            capture_output=True, check=False
        )
        if p.returncode:
            raise RuntimeError("OFFICIAL_RC_NOT_FETCHABLE_" + key)
        if sha1_blob(p.stdout) != digest:
            raise RuntimeError("OFFICIAL_RC_BLOB_INVALID_" + key)
        actual[key] = p.stdout.decode("utf-8")
    return actual

def build(native: dict[str, str]) -> str:
    return (FAKES
        + "local Config=(function()\n"+native["Config"]+"\nend)()\n"
        + "local MapBuilder=(function()\n"+native["MapBuilder"]+"\nend)()\n"
        + TEST)

def run(luau: str, path: Path, modules: dict[str, str]) -> tuple[int, str]:
    path.write_text(build(modules), encoding="utf-8")
    p = subprocess.run([luau, str(path)], capture_output=True, text=True,
                       check=False, timeout=30)
    return p.returncode, p.stdout + p.stderr

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True)
    ap.add_argument("--luau", required=True)
    args = ap.parse_args()
    modules = original_files(args.repo)
    with TemporaryDirectory(prefix="p0d_native_true_map_") as temp:
        source = Path(temp) / "original_mapbuilder_and_config.luau"
        code, output = run(args.luau, source, modules)
        matches = re.search(r"P0D_NATIVE_ACTUAL_OFFICIAL_MAPBUILDER_PASS assertions=(\d+)", output)
        if code or matches is None or int(matches.group(1)) < 135:
            raise RuntimeError("OFFICIAL_RC_TRUE_MAPBUILDER_NATIVE_FAILED " + output[-1300:])
        print(matches.group(0))
        for tag, old, new, must_fail in MUTATIONS:
            src = modules["MapBuilder"]
            if src.count(old) != 1:
                raise RuntimeError("MUTATION_SOURCE_NONUNIQUE_" + tag)
            mutated = dict(modules)
            mutated["MapBuilder"] = src.replace(old, new, 1)
            code, out = run(args.luau, source, mutated)
            if code == 0 or must_fail not in out:
                raise RuntimeError("MAP_MUTATION_ESCAPED_" + tag + " " + out[-600:])
            print("P0D_MAP_NATIVE_SOURCE_MUTATION_BLOCKED " + tag)
        print("P0D_NATIVE_ACTUAL_MAPBUILDER_NEGATIVE_CONTROLS=" + str(len(MUTATIONS)))
        print("P0D_ACTUAL_OFFICIAL_MAP_SOURCE_SHA_LOCK_PASS")

if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, UnicodeError, OSError, subprocess.TimeoutExpired) as error:
        print("P0D_MAP_NATIVE_BLOCKED " + str(error), file=sys.stderr)
        sys.exit(1)
