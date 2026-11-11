#!/usr/bin/env python3
"""Native test of full real MapBuilder with ONLY Japanese presentational text diff.

Imports the immutable independent original MapBuilder native QA oracle and
executes both original physical geometry tests and added Japanese sign tests.
Official game source and sole RC are never edited. Native Roblox API doubles
do not substitute actual Studio/mobile testing.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
from tempfile import TemporaryDirectory

RC = "5dc6c958ea5549b1e859d6d250e6179e731181fb"
BASE_MAP_BLOB = "d2127b8c20c8abd880a21f84aeeb706feeb14ce8"
BASE_CONFIG_BLOB = "ef10e4288e4732588116cd3e55d3d871ca803ff4"
ORACLE_COMMIT = "c71d209c56ff3bb33ed0eb2628886b69c2541e81"
ORACLE_BLOB = "e059a7874f5563c017f45a8bf01bed9bbba36b9f"
ORACLE_PATH = ("handoffs/P0D-S1-RC-MAPBUILDER-NATIVE-20261112-04/"
               "tools/run_original_mapbuilder_native.py")
ROOT = Path(__file__).resolve().parent.parent
CAND_PATH = ROOT / "candidate/src/server/MapBuilder.luau"
MANIFEST = ROOT / "BUILD_MANIFEST.json"
PATCH = [
    ('name .. " CASTLE HP"',
     '(if name == "RED" then "赤チームの城" else "青チームの城")'),
    ('"Steal egg"', '"卵を取る"'),
    ('name .. " treasure"',
     '(if name == "RED" then "赤チームの卵" else "青チームの卵")'),
    ('name .. " EGG"',
     '(if name == "RED" then "赤チームの卵" else "青チームの卵")'),
    ('"Deliver egg"', '"卵を届ける"'),
    ('name .. " scoring pad"',
     '(if name == "RED" then "赤の納品台" else "青の納品台")'),
    ('"DELIVER HERE"', '"卵はここへ！"'),
    ('name .. " SPAWN"',
     '(if name == "RED" then "赤チームのスタート" else "青チームのスタート")'),
]

NATIVE_JP = r'''
local function findSign(part)
 local bb=part:FindFirstChild("StatusLabel")
 isNode(bb,"BillboardGui","expected_label")
 local txt=bb.children[1]
 isNode(txt,"TextLabel","expected_text")
 return txt.Text
end
for _,side in ipairs({"RED","BLUE"}) do
 local t=map.teams[side]
 local isRed=side=="RED"
 eq(t.eggPrompt.ActionText,"卵を取る",side.."_egg_prompt_jp_action")
 eq(t.eggPrompt.ObjectText,if isRed then "赤チームの卵" else "青チームの卵",side.."_egg_prompt_jp_object")
 eq(t.scorePrompt.ActionText,"卵を届ける",side.."_score_prompt_jp_action")
 eq(t.scorePrompt.ObjectText,if isRed then "赤の納品台" else "青の納品台",side.."_score_prompt_jp_object")
 eq(findSign(t.core),if isRed then "赤チームの城" else "青チームの城",side.."_castle_jp_sign")
 eq(findSign(t.egg),if isRed then "赤チームの卵" else "青チームの卵",side.."_egg_jp_sign")
 eq(findSign(t.scorePad),"卵はここへ！",side.."_score_jp_sign")
 local castle=map.model:FindFirstChild(side.."_CASTLE")
 isNode(castle,"Folder",side.."_castle_container")
 local spawn=castle:FindFirstChild(side.."_SPAWN")
 isNode(spawn,"Part",side.."_spawn_part")
 eq(findSign(spawn),if isRed then "赤チームのスタート" else "青チームのスタート",side.."_spawn_jp_sign")
 eq(t.eggPrompt.HoldDuration,0.35,side.."_unchanged_hold")
 eq(t.eggPrompt.MaxActivationDistance,10,side.."_unchanged_prompt_distance")
end
print("P0D_NATIVE_JP_MAP_SIGN_ACCEPTANCE_PASS assertions=20")
'''
NEGATIVE = [
    ("english_steal", '"卵を取る"', '"Steal egg"', "MAP_BUILDER_ASSERT_RED_egg_prompt_jp_action"),
    ("english_deliver", '"卵を届ける"', '"Deliver egg"', "MAP_BUILDER_ASSERT_RED_score_prompt_jp_action"),
    ("wrong_side_color", '"赤の納品台"', '"中立の納品台"', "MAP_BUILDER_ASSERT_RED_score_prompt_jp_object"),
    ("english_3d_label", '"卵はここへ！"', '"DELIVER HERE"', "MAP_BUILDER_ASSERT_RED_score_jp_sign"),
    ("wrong_castle_sign", '"赤チームの城"', '"敵の城"', "MAP_BUILDER_ASSERT_RED_castle_jp_sign"),
    ("map_position_change", "Vector3.new(sign * 98, 2.5, -20)",
     "Vector3.new(sign * 18, 2.5, -20)", "MAP_BUILDER_ASSERT_RED_egg_exact_x"),
    ("enable_prompts_in_lobby", "p.Enabled = false", "p.Enabled = true",
     "MAP_BUILDER_ASSERT_RED_egg_disabled_until_active"),
]

def guard(valid, reason):
    if not valid:
        raise RuntimeError(reason)

def blob(data):
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()

def git_bytes(repo, commit, path, want):
    proc = subprocess.run(["git", "-C", repo, "show", commit + ":" + path],
                          capture_output=True, check=False, timeout=25)
    guard(proc.returncode == 0, "FIXED_SOURCE_UNAVAILABLE " + path)
    guard(blob(proc.stdout) == want, "FIXED_GIT_BLOB_DRIFT " + path)
    return proc.stdout

def source_and_oracle(repo):
    original = git_bytes(repo, RC,
        "releases/P0D_S1_KIDS_RC01/src/server/MapBuilder.luau",
        BASE_MAP_BLOB).decode("utf8")
    conf = git_bytes(repo, RC,
        "releases/P0D_S1_KIDS_RC01/src/shared/Config.luau",
        BASE_CONFIG_BLOB).decode("utf8")
    raw_oracle = git_bytes(repo, ORACLE_COMMIT, ORACLE_PATH, ORACLE_BLOB)
    ns = {"__name__": "_p0d_readonly_upstream_oracle_"}
    exec(compile(raw_oracle, ORACLE_PATH, "exec"), ns)
    guard(isinstance(ns.get("FAKES"), str) and isinstance(ns.get("TEST"), str),
          "REFERENCE_ORACLE_MISSING")
    return original, conf, ns

def expected_patch(original):
    candidate = original
    for old, new in PATCH:
        guard(candidate.count(old) == 1, "SOURCE_PATCH_ANCHOR_NONUNIQUE_" + old)
        candidate = candidate.replace(old, new, 1)
    return candidate

def compare_candidate(original, candidate):
    guard(candidate == expected_patch(original),
          "CANDIDATE_MODIFIED_BEYOND_8_PRESENTATIONAL_LABELS")
    for marker in ('"Steal egg"', '"Deliver egg"', '"DELIVER HERE"'):
        guard(marker not in candidate, "ENGLISH_CHILD_LABEL_REMAINS " + marker)
    guard("Instance.new(\"RemoteEvent\")" not in candidate and
          "DataStore" not in candidate and "FireServer" not in candidate,
          "UNAUTHORIZED_MAP_AUTHORITY_ADDED")
    return True

def verify_manifest():
    data = json.loads(MANIFEST.read_text("utf8"))
    guard(set(data) == {"files", "format", "game_id", "packet_id",
                        "public_source_allowed", "work_id"},
          "PUBLIC_MANIFEST_KEYS")
    guard(data["format"] == "P0D_PUBLIC_SOURCE_V1"
          and data["game_id"] == "TRAP_RAIDERS"
          and data["work_id"] == "p0d-siege-v19"
          and data["packet_id"] == "P0D-S1-JP-MAP-SIGNS-20261112-01"
          and data["public_source_allowed"] is True,
          "PUBLIC_MANIFEST_IDENTITY")
    expected = {
        "candidate/src/server/MapBuilder.luau",
        "tools/test_jp_map.py",
        "README.md",
    }
    guard(isinstance(data["files"], list) and len(data["files"]) == 3,
          "PUBLIC_MANIFEST_RECORD_COUNT")
    seen = set()
    for record in data["files"]:
        guard(isinstance(record, dict) and
              set(record) == {"path", "sha256", "size"}, "PUBLIC_MANIFEST_RECORD_KEYS")
        path = record["path"]
        guard(isinstance(path, str) and path in expected and path not in seen,
              "PUBLIC_MANIFEST_ILLEGAL_OR_DUPLICATE_PATH")
        raw = (ROOT / path).read_bytes()
        guard(isinstance(record["sha256"], str) and
              re.fullmatch("[a-f0-9]{64}", record["sha256"]) and
              type(record["size"]) is int and
              record["size"] == len(raw) and
              hashlib.sha256(raw).hexdigest() == record["sha256"],
              "PUBLIC_MANIFEST_FILE_HASH_MISMATCH " + path)
        seen.add(path)
    guard(seen == expected, "PUBLIC_MANIFEST_MISSING_RECORD")
    print("P0D_JP_MAP_SOURCE_MANIFEST_PASS files=3/3")

def run_native(luau, source, config, oracle):
    with TemporaryDirectory(prefix="p0d_map_jp_native_") as temp:
        script = Path(temp) / "jp_map_source.luau"
        code = (oracle["FAKES"] +
                "local Config=(function()\n" + config + "\nend)()\n" +
                "local MapBuilder=(function()\n" + source + "\nend)()\n" +
                oracle["TEST"] + NATIVE_JP)
        script.write_text(code, encoding="utf8")
        result = subprocess.run([luau, str(script)], capture_output=True,
                                text=True, check=False, timeout=25)
        return result.returncode, result.stdout + result.stderr

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    parser.add_argument("--luau", required=True)
    args = parser.parse_args()
    verify_manifest()
    original, config, oracle = source_and_oracle(args.repo)
    candidate = CAND_PATH.read_text("utf8")
    compare_candidate(original, candidate)
    print("P0D_MAP_SOURCE_TEXT_ONLY_EXACT_8_REPLACEMENTS_PASS")
    code, out = run_native(args.luau, candidate, config, oracle)
    if code != 0 or "P0D_NATIVE_ACTUAL_OFFICIAL_MAPBUILDER_PASS" not in out or \
       "P0D_NATIVE_JP_MAP_SIGN_ACCEPTANCE_PASS assertions=20" not in out:
        raise RuntimeError("JP_MAP_NATIVE_REAL_SOURCE_FAILED " + out[-1400:])
    original_checks = re.search(
        r"P0D_NATIVE_ACTUAL_OFFICIAL_MAPBUILDER_PASS assertions=(\d+)", out)
    guard(original_checks is not None and int(original_checks.group(1)) >= 135,
          "ORIGINAL_PHYSICAL_GEOMETRY_TESTS_INSUFFICIENT")
    print("P0D_NATIVE_JP_MAP_ORIGINAL_GEOMETRY_PASS assertions=" +
          original_checks.group(1))
    print("P0D_NATIVE_JP_MAP_TEXT_PASS assertions=20")
    # For each deliberately broken candidate, the actual map runtime or our
    # independent assertion must fail with the expected descriptive check.
    for tag, old, new, expected in NEGATIVE:
        guard(candidate.count(old) >= 1, "NEGATIVE_NOT_ANCHORED_" + tag)
        changed = candidate.replace(old, new, 1)
        status, fail = run_native(args.luau, changed, config, oracle)
        guard(status != 0 and expected in fail,
              "NEGATIVE_MUTATION_ESCAPED_" + tag + " " + fail[-700:])
        print("P0D_JP_MAP_NEGATIVE_REJECTED " + tag)
    # Exact byte patch rule must also reject changes that might appear safe.
    dangerous = candidate.replace("p.CanCollide = collide ~= false",
                                   "p.CanCollide = true", 1)
    try:
        compare_candidate(original, dangerous)
    except RuntimeError:
        print("P0D_JP_MAP_NEGATIVE_REJECTED unlisted_geometry_mutation")
    else:
        raise RuntimeError("UNLISTED_GEOMETRY_PATCH_NOT_REJECTED")
    print("P0D_NATIVE_JP_MAP_NEGATIVE_CONTROLS=8/8")
    print("P0D_JP_MAP_SOURCE_PACK_READY_NOT_STUDIO_VERIFIED")
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except (RuntimeError, OSError, UnicodeError, ValueError,
            subprocess.TimeoutExpired) as exc:
        print("P0D_JP_MAP_NATIVE_BLOCKED " + str(exc), file=sys.stderr)
        sys.exit(1)
