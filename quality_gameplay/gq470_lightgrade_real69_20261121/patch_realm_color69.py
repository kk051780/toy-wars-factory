#!/usr/bin/env python3
"""Source-exact, reversible one-client visual patch on official REAL69.

Requires authentic official 2026-11-20 REAL69 artifact #14610422120.
Does NOT alter formal RC, download secrets, or claim Studio/mobile PASS.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re
import zipfile

BASE_HEAD = "e80973c354f14a0d0088577f3cc1a875454f0f8f"
TARGET = "StarterPlayer/StarterPlayerScripts/EGGRUMBLE_RealmBattleControls"
TARGET_FILE = "sources/" + TARGET + ".client.luau"
BEFORE_SHA = "8a7473f348bfe834fc8c6f5018822608903845c89796ce4976eea04fe9a95e6f"
AFTER_SHA = "b33030c9e8f170221b5dc21b467055672e04fc3a457d87f1b6978e7da6f59a5b"
MARK = "GQ470_FB015_REALM_CLIENT_GRADE_REAL69_20261121"

RUN_SERVICE = 'local RunService=game:GetService("RunService")\n'
RUN_SERVICE_NEW = RUN_SERVICE + 'local Lighting=game:GetService("Lighting")\n'
KIND = 'local currentKind="NONE"\n'
KIND_NEW = KIND + '''-- GQ470_FB015_REALM_CLIENT_GRADE_REAL69_20261121: client visual only.
-- Existing RenderStepped cadence drives palette changes. No extra loops,
-- physics, damage, remote, camera occlusion, or new GUI surface.
local gradeName="EGGRUMBLE_RealmClientColorGrade"
local ownedGrade=nil
local currentGradeMood="NONE"
local function updateRealmGrade(mood)
 if mood==currentGradeMood then return end
 if mood=="NONE" then
  currentGradeMood=mood
  if ownedGrade then ownedGrade.Enabled=false end
  return
 end
 -- One lazy effect in sea/fighter only, never modify another lane's effect.
 if not ownedGrade then
  if Lighting:FindFirstChild(gradeName) then return end
  local effect=Instance.new("ColorCorrectionEffect")
  effect.Name=gradeName
  effect.Enabled=false
  effect.Parent=Lighting
  ownedGrade=effect
 end
 currentGradeMood=mood
 local effect=ownedGrade
 effect.Enabled=true
 if mood=="SUBSEA" then
  effect.Contrast=.065;effect.Saturation=-.08;effect.Brightness=-.025
  effect.TintColor=Color3.fromRGB(205,230,245)
 elseif mood=="THUNDER" then
  effect.Contrast=.09;effect.Saturation=-.07;effect.Brightness=-.02
  effect.TintColor=Color3.fromRGB(216,224,239)
 elseif mood=="WIND" then
  effect.Contrast=.065;effect.Saturation=-.025;effect.Brightness=0
  effect.TintColor=Color3.fromRGB(232,241,246)
 else
  effect.Enabled=false
 end
end
script.Destroying:Connect(function()
 if ownedGrade then ownedGrade:Destroy() end
end)
'''
DIVER = ' local isDiver=currentKind=="SUBSEA"\n'
DIVER_NEW = DIVER + ' local gradeTarget=isDiver and "SUBSEA" or "NONE"\n'
WEATHER = '  local weather=core and core:GetAttribute("RealmWeather") or "CLEAR"\n'
WEATHER_NEW = WEATHER + '''   if weather=="THUNDER" then gradeTarget="THUNDER"
   elseif weather=="WIND" then gradeTarget="WIND" end
'''
AFTER_FLIGHT = ' end\n heading.Text=currentKind=="FIGHTER"'
AFTER_FLIGHT_NEW = ' end\n updateRealmGrade(gradeTarget)\n heading.Text=currentKind=="FIGHTER"'
REPLACEMENTS = (
    (RUN_SERVICE, RUN_SERVICE_NEW, "SERVICE"),
    (KIND, KIND_NEW, "GRADE"),
    (DIVER, DIVER_NEW, "DIVER"),
    (WEATHER, WEATHER_NEW, "WEATHER"),
    (AFTER_FLIGHT, AFTER_FLIGHT_NEW, "APPLY"),
)


def sha(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def check(ok: bool, label: str) -> None:
    if not ok:
        raise ValueError("RED_REALM_GRADE_" + label)


def patch(before: str) -> str:
    check(MARK not in before, "DOUBLE_APPLY")
    check(before.startswith("--!nonstrict"), "ORIGINAL_CLIENT")
    check(before.count("RunService.RenderStepped:Connect") == 1, "ORIGINAL_CONTROL_LOOP")
    check("EGGRUMBLE_RealmBattleIntent_V1" in before, "ORIGINAL_REMOTE")
    check('currentKind=="SUBSEA"' in before, "ORIGINAL_SUBSEA")
    check('core:GetAttribute("RealmWeather")' in before, "ORIGINAL_WEATHER")
    output = before
    for old, new, label in REPLACEMENTS:
        check(output.count(old) == 1, "ANCHOR_" + label)
        output = output.replace(old, new, 1)
    check(output.count(MARK) == 1, "MISSING_MARK")
    check(output.count("RunService.RenderStepped:Connect") == 1, "EXTRA_CONTROL_LOOP")
    check(output.count('Instance.new("ColorCorrectionEffect")') == 1,
          "EFFECT_BUDGET")
    check('Instance.new("Part")' not in output, "PART_BUDGET")
    check('remote:FireServer("FLIGHT"' in output, "PRESERVE_FLIGHT")
    check(unpatch(output) == before, "NOT_REVERSIBLE")
    return output


def unpatch(after: str) -> str:
    output = after
    for old, new, label in reversed(REPLACEMENTS):
        check(output.count(new) == 1, "OFF_ANCHOR_" + label)
        output = output.replace(new, old, 1)
    return output


def selected_paths(project: dict) -> dict[str, str]:
    output = {}
    def walk(node: dict, route: str = "") -> None:
        if "$path" in node:
            check(route not in output, "DUPLICATE_ROUTE")
            output[route] = node["$path"]
            return
        for key, child in node.items():
            if not key.startswith("$") and isinstance(child, dict):
                walk(child, route + "/" + key if route else key)
    walk(project["tree"])
    return output


def build(artifact: pathlib.Path, destination: pathlib.Path) -> dict:
    check(not destination.exists(), "OUT_ALREADY_EXISTS")
    with zipfile.ZipFile(artifact) as archive:
        names = archive.namelist()
        check(all(not n.startswith("/") and ".." not in pathlib.PurePosixPath(n).parts
                  for n in names), "ZIP_PATH")
        project_bytes = archive.read("EGGRUMBLE_REAL69.project.json")
        receipt_bytes = archive.read("REAL69_LEGACY_INTAKE_RECEIPT.json")
        project = json.loads(project_bytes)
        receipt = json.loads(receipt_bytes)
        routes = selected_paths(project)
        check(receipt["build_head"] == BASE_HEAD, "OFFICIAL_HEAD")
        check(receipt["selected_source_count"] == 69 == len(routes), "REAL69")
        check(set(receipt["source_hashes"]) == set(routes), "RECEIPT_ROUTES")
        check(TARGET in routes and routes[TARGET] == TARGET_FILE, "TARGET_ROUTE")
        check(receipt["source_hashes"][TARGET] == BEFORE_SHA, "BEFORE_PIN")
        for route, name in routes.items():
            check(name in names, "MISSING_" + route)
            check(sha(archive.read(name)) == receipt["source_hashes"][route],
                  "SOURCE_MISMATCH_" + route)
        original = archive.read(TARGET_FILE)
        check(sha(original) == BEFORE_SHA, "ORIGINAL_SHA")
        before_text = original.decode("utf-8")
        after = patch(before_text).encode("utf-8")
        check(sha(after) == AFTER_SHA, "EXPECTED_RESULT_SHA_LOCK")
        check(unpatch(after.decode("utf-8")).encode("utf-8") == original,
              "BYTE_EXACT_OFF")
        destination.mkdir(parents=True)
        for route, name in routes.items():
            out = destination / name
            check(out.resolve().is_relative_to(destination.resolve()), "PATH_ESCAPE")
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_bytes(after if route == TARGET else archive.read(name))
        (destination / "EGGRUMBLE_REAL69.project.json").write_bytes(project_bytes)
        (destination / "ORIGINAL_REAL69_RECEIPT.json").write_bytes(receipt_bytes)
        (destination / "OFF69_REALM_GRADE_ORIGINAL.client.luau").write_bytes(original)
        report = {
            "formal_base_sha": BASE_HEAD, "selected_source_count": 69,
            "changed_selected_routes": [TARGET],
            "unaltered_selected_routes": 68,
            "original_source_sha256": BEFORE_SHA,
            "candidate_source_sha256": sha(after),
            "rollback_source_byte_exact": True,
            "original_source_bytes": len(original),
            "candidate_source_bytes": len(after),
            "source_delta_bytes": len(after) - len(original),
            "new_part_count": 0,
            "new_renderstep_connections": 0,
            "new_color_correction_effects_max": 1,
            "engine": "NOT_TESTED", "android": "NOT_TESTED",
            "art": "NO_GO", "official_rc_changed": False,
        }
        (destination / "REALM_GRADE_PREP_REPORT.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8")
        return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact", type=pathlib.Path, required=True)
    parser.add_argument("--out", type=pathlib.Path, required=True)
    args = parser.parse_args()
    print(json.dumps(build(args.artifact, args.out), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
