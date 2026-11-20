#!/usr/bin/env python3
"""Focused FB-015/014 REAL69 first-session art: short 3D cues, no overlay spam.

A candidate source patch ONLY. Native/Rojo checks do not prove Roblox Studio,
Android readability, first-three-minute FUN, or human ART acceptance.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil

BASE = "e80973c354f14a0d0088577f3cc1a875454f0f8f"
ROUTE = "StarterPlayer/StarterPlayerScripts/EGGRUMBLE_LegacyFirst90"
ORIGINAL_SHA256 = "cd346ca76f8c215219a7c31e0795b3e113a146eaab9c003cd5559eaf46919d5d"
FEATURE = "GQ470_FB015_FIRST90_MICROCUE_VISUAL_20261121"
PROJECT = "EGGRUMBLE_REAL69.project.json"
RECEIPT = "REAL69_LEGACY_INTAKE_RECEIPT.json"
PLACE = "EGGRUMBLE_REAL69_PRIVATE.rbxlx"
OFF = "OFF69_FIRST90_MICROCUE"
ORIGINAL_LOCAL = "quality_gameplay/gq8_rc85_first90_real69_20261120/EGGRUMBLE_LegacyFirst90.client.luau"

SIZE_OLD = "billboard.Size=UDim2.fromOffset(210,43)\nbillboard.StudsOffsetWorldSpace=Vector3.new(0,4.3,0)"
SIZE_NEW = "billboard.Size=UDim2.fromOffset(184,36)\nbillboard.StudsOffsetWorldSpace=Vector3.new(0,3.65,0)"
BG_OLD = "label.BackgroundTransparency=.26"
BG_NEW = "label.BackgroundTransparency=.42"
STATE_OLD = "local started=os.clock()\nlocal alive=true"
STATE_NEW = """-- GQ470_FB015_FIRST90_MICROCUE_VISUAL_20261121
-- Never leave an on-character hint above combat for ninety uninterrupted seconds.
-- A cue is visible briefly on semantic change; selection-only reminders are sparse.
local CUE_VISIBLE_SECONDS=4.5
local SELECTION_REMINDER_SECONDS=24
local started=os.clock()
local alive=true
local previousCue=""
local cueShownAt=started
local lastReminderAt=started
local lastBoundHead:BasePart?=nil"""
LOOP_OLD = """  local message=cue(now)
  local head=billboard.Adornee
  billboard.Enabled=message~="" and head~=nil and head.Parent~=nil
   and player.Character==currentCharacter
  if billboard.Enabled and label.Text~=message then
   label.Text=message
  end"""
LOOP_NEW = """  local message=cue(now)
  local needsSelection=message=="1/3  役職と対戦モードを選ぼう"
   or message=="1/3  好きな役職を選んで出撃！"
  if message~=previousCue then
   previousCue=message
   cueShownAt=now
   lastReminderAt=now
  elseif needsSelection and now-lastReminderAt>=SELECTION_REMINDER_SECONDS then
   cueShownAt=now
   lastReminderAt=now
  end
  local head=billboard.Adornee
  -- Late spawns and respawns must receive the current cue after the Head binds.
  -- Only a DIFFERENT adornee resets the window, so polling never prolongs it.
  if head~=lastBoundHead then
   lastBoundHead=head
   if head then cueShownAt=now end
  end
  -- Never show when eliminated, detached, or without an avatar head.
  billboard.Enabled=message~="" and now-cueShownAt<CUE_VISIBLE_SECONDS
   and head~=nil and head.Parent~=nil and player.Character==currentCharacter
  if billboard.Enabled and label.Text~=message then
   label.Text=message
  end"""

def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def guard(ok: bool, code: str) -> None:
    if not ok:
        raise ValueError("RED_GQ470_FIRST90_MICROCUE_" + code)

def transform(source: str) -> str:
    guard(FEATURE not in source, "DOUBLE_APPLY")
    guard(digest(source.encode("utf-8")) == ORIGINAL_SHA256, "ORIGINAL_SOURCE_HASH")
    for label, old in (("SIZE", SIZE_OLD), ("BG", BG_OLD),
                       ("STATE", STATE_OLD), ("LOOP", LOOP_OLD)):
        guard(source.count(old) == 1, label + "_ANCHOR")
    for label in (
        'if not RunService:IsStudio() then return end',
        'if player:GetAttribute("EGGRUMBLE_Eliminated")==true then',
        'player:GetAttribute("EGGRUMBLE_SelectedRole")',
        'player:GetAttribute("EGGRUMBLE_QueuedMode")',
        'mode~="BATTLE_ROYALE"',
        'billboard.AlwaysOnTop=false',
        'billboard.MaxDistance=32',
        'local DURATION=90',
        'if respawnConnection then respawnConnection:Disconnect() end',
        'characterConnection:Disconnect()',
        'billboard:Destroy()',
    ):
        guard(label in source, "LEGACY_CONTRACT_" + label[:18])
    out = (source.replace(SIZE_OLD, SIZE_NEW, 1)
                 .replace(BG_OLD, BG_NEW, 1)
                 .replace(STATE_OLD, STATE_NEW, 1)
                 .replace(LOOP_OLD, LOOP_NEW, 1))
    guard(out.count(FEATURE) == 1, "MARKER")
    guard(out.count("task.spawn(function()") == 1
          and out.count("task.wait(POLL)") == 1, "ONE_BOUNDED_POLL")
    guard(out.count('billboard.Enabled=') == 3, "UI_LIFECYCLE")  # initial, attach, poll
    for forbidden in ("FireServer(", "Instance.new(\"RemoteEvent\")",
                      "DataStoreService", "MarketplaceService", "RenderStepped:Connect("):
        guard(forbidden not in out, "AUTHORITY_OR_RENDER_LOOP")
    return out

def reverse(transformed: str) -> str:
    guard(transformed.count(FEATURE) == 1, "UNDO_MARKER")
    restored = (transformed.replace(LOOP_NEW, LOOP_OLD, 1)
                           .replace(STATE_NEW, STATE_OLD, 1)
                           .replace(BG_NEW, BG_OLD, 1)
                           .replace(SIZE_NEW, SIZE_OLD, 1))
    guard(digest(restored.encode("utf-8")) == ORIGINAL_SHA256, "UNDO_HASH")
    return restored

def selected(root: Path) -> dict[str, Path]:
    project = json.loads((root / PROJECT).read_text(encoding="utf-8"))
    output: dict[str, Path] = {}
    def walk(node: dict, route: str = "") -> None:
        if "$path" in node:
            path = (root / node["$path"]).resolve()
            guard(path.is_relative_to(root.resolve()) and path.is_file(), "PATH_TRAVERSAL")
            guard(route not in output, "DUPLICATE_ROUTE")
            output[route] = path
            return
        for key, value in node.items():
            if not key.startswith("$") and isinstance(value, dict):
                walk(value, (route + "/" if route else "") + key)
    walk(project["tree"])
    return output

def apply(root: Path) -> None:
    root = root.resolve()
    receipt_file = root / RECEIPT
    receipt = json.loads(receipt_file.read_text(encoding="utf-8"))
    sources = selected(root)
    guard(receipt.get("official_branch") == "rc/p0d-s1-kids-rc01"
          and receipt.get("build_head") == BASE and receipt.get("canonical_build") is True,
          "IMMUTABLE_BASE")
    guard(len(sources) == 69 and len(receipt.get("source_hashes", {})) == 69
          and set(sources) == set(receipt["source_hashes"])
          and receipt.get("source_classes", {}).get(ROUTE) == "LocalScript",
          "69_SELECTED_LOCK")
    original = {route: digest(path.read_bytes()) for route, path in sources.items()}
    guard(original == receipt["source_hashes"]
          and original[ROUTE] == ORIGINAL_SHA256, "SOURCE_BYTES")
    guard((root / PLACE).is_file() and not (root / OFF).exists(), "PLACE_OR_DOUBLE_APPLY")
    transformed = transform(sources[ROUTE].read_text(encoding="utf-8")).encode("utf-8")
    undo = root / OFF
    shutil.copytree(root / "sources", undo / "sources")
    for file in (PROJECT, RECEIPT, PLACE):
        shutil.copy2(root / file, undo / file)
    sources[ROUTE].write_bytes(transformed)
    updated = {route: digest(path.read_bytes()) for route, path in selected(root).items()}
    guard({route for route in updated if updated[route] != original[route]} == {ROUTE}
          and all(updated[route] == original[route] for route in original if route != ROUTE),
          "ONLY_ONE_ROUTE")
    guard(reverse(sources[ROUTE].read_text(encoding="utf-8")).encode("utf-8")
          == selected(undo)[ROUTE].read_bytes(), "EXACT_OFF69")
    receipt["source_hashes"][ROUTE] = updated[ROUTE]
    receipt["build_head"] = "PREP_FROM_" + BASE
    receipt["gq470_first90_microcue"] = {
        "feature_id": FEATURE, "base_rc": BASE, "selected_route": ROUTE,
        "source_before": ORIGINAL_SHA256, "source_after": updated[ROUTE],
        "others_68_byte_exact": True, "new_runtime_scripts": 0, "new_remotes": 0,
        "selected_count": 69, "visible_per_cue_seconds": 4.5,
        "selection_reminder_seconds": 24, "max_duration_seconds": 90,
        "draw_calls_per_frame": 0, "small_hint_size": [184,36],
        "visual_comparison_png": "NOT_TESTED", "studio": "NOT_TESTED",
        "android15": "NOT_TESTED", "kid_fun": "NOT_TESTED",
        "owner_accepted": False, "rollback": OFF,
    }
    receipt_file.write_text(json.dumps(receipt, ensure_ascii=False, indent=2,
                                       sort_keys=True) + "\n", encoding="utf-8")
    print("GQ470_REAL69_FIRST90_MICROCUE_ONE_LOCAL_SOURCE_OFF69_PASS", updated[ROUTE])

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", type=Path, required=True)
    apply(ap.parse_args().base)
