#!/usr/bin/env python3
"""Independent fail-closed art budget + server authority guard for the real 69 source.

Does not claim visual/runtime/FPS. Compares actual authentic original with patched Luau.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
from pathlib import Path

ROLES = ("WARRIOR", "MAGE", "NINJA", "TRAPPER", "BUILDER", "BEAST", "ZOMBIE")
OLD_HASH = "b2c279371a8fd986b929883290aae58ed9acdafb7cd48f878eae3785e4acccab"
NEW_HASH = "817a865e7812f7190efec5f870dc3883370cc562c0452176b3ce75637b0b1406"

def require(condition: bool, key: str) -> None:
    if not condition:
        raise ValueError("RED_ART_BUDGET_" + key)

def block(source: str, start: str, end: str) -> str:
    require(source.count(start) == 1 and source.count(end) == 1, "BLOCK_ANCHOR")
    return source.split(start, 1)[1].split(end, 1)[0]

def check(original: str, candidate: str, *, exact_hash: bool = True) -> dict:
    if exact_hash:
        require(hashlib.sha256(original.encode()).hexdigest() == OLD_HASH, "ORIGINAL_SHA_DRIFT")
        require(hashlib.sha256(candidate.encode()).hexdigest() == NEW_HASH, "CANDIDATE_SHA_DRIFT")
    roles_old = block(original, "local DESIGN={", "\nlocal function validSnapshot")
    roles_new = block(candidate, "local DESIGN={", "\nlocal function validSnapshot")
    require(roles_old == roles_new, "ROLE_COLORS_OR_SILHOUETTES_CHANGED")
    require(all(roles_new.count(role + "={") == 1 for role in ROLES), "SEVEN_ROLE_CONTRACT")
    require('name="暗殺者・紅影連斬"' in roles_new, "ASSASSIN_DISPLAY")
    for a, b, label in (
        ("local function validSnapshot(s)", "local function clean(character)", "SNAPSHOT_AUTHORITY"),
        ("local function clean(character)", "local function phaseText(p)", "CLEANUP"),
        ("function M.stop(character)", "function M.start(character,snapshot)", "STOP_API"),
    ):
        require(block(original, a, b) == block(candidate, a, b), label)
    for token in ('Instance.new(', 'game:GetService("RunService")',
                  'GetAttribute("Mode")', 'SetAttribute("Mode"', 'M.start(character,snapshot)',
                  'validSnapshot(snapshot)', 'localViewDist(head)'):
        if token == 'localViewDist(head)':
            # Two additional dist calls: first-frame burst and update, no new render loop.
            require(candidate.count(token) == original.count(token) + 1, "DISTANCE_BUDGET")
        else:
            require(candidate.count(token) == original.count(token), "UNCHANGED_OWNER_" + token)
    for token in ("RemoteEvent", "FireServer", "InvokeServer", "DataStore",
                  "RunService.RenderStepped", "RunService.Heartbeat", "task.spawn",
                  "BindToRenderStep", "CollectionService", "TakeDamage"):
        require(candidate.count(token) == original.count(token), "NO_AUTHORITY_OR_FRAME_LOOP_" + token)
    expected = (
        'gui.Size=UDim2.fromOffset(150,34)',
        'gui.MaxDistance=100',
        'gui.AlwaysOnTop=false',
        'label.TextScaled=false',
        'label.TextSize=16',
        'label.TextTruncate=Enum.TextTruncate.AtEnd',
        'particles.LightEmission=.28',
        'particles.Rate=7',
        'particles.Speed=NumberRange.new(.65,1.6)',
        'particles.Lifetime=NumberRange.new(.25,.48)',
        'local rate=if snapshot.phase=="KAKUHEN" then 12 else 7',
        'particles.Rate=if dist<=55 then rate elseif dist<=95 then 3 else 0',
        'gui.Enabled=dist<=95',
        'h.Enabled=dist<=115',
        'folder:SetAttribute("ClientCosmeticOnly",true)',
    )
    require(all(candidate.count(token) == 1 for token in expected), "VISUAL_BUDGET_CONTRACT")
    require("gui.Size=UDim2.fromOffset(195,54)" in original, "BASE_GUI_SIZE")
    require("gui.MaxDistance=160" in original, "BASE_VIEW_DISTANCE")
    require("particles.Rate=12" in original, "BASE_PARTICLE_RATE")
    require("particles.LightEmission=.7" in original, "BASE_LIGHT_EMISSION")
    require(candidate.count("particles:Emit(") == original.count("particles:Emit("), "BURST_EMITTER_OWNERS")
    require(candidate.count("ClientCosmeticOnly") == original.count("ClientCosmeticOnly"), "CLIENT_COSMETIC_ONLY")
    return dict(seven_roles=list(ROLES), one_selected_existing_module=True,
        source_count_other68_untouched="VERIFIED_BY_SEPARATE_EXACT_SOURCE_LOCK",
        nominal_label_area_before=195*54, nominal_label_area_after=150*34,
        area_reduction_pct=round((1-150*34/(195*54))*100,1),
        particle_regular_near_rate_before=12, particle_regular_near_rate_after=7,
        max_distance_studs_before=160,max_distance_studs_after=100,
        new_world_parts=0,new_event_or_render_loops=0,
        studio_performance="NOT_TESTED", human_art="NOT_TESTED", owner_accepted=False)

def verify_negatives(original: str, candidate: str) -> int:
    bad = {
      "seven_roles": candidate.replace('name="暗殺者・紅影連斬"', 'name="忍者・紅影連斬"', 1),
      "dangerous_label": candidate.replace('gui.Size=UDim2.fromOffset(150,34)', 'gui.Size=UDim2.fromOffset(250,80)', 1),
      "neon_overdraw": candidate.replace('particles.LightEmission=.28', 'particles.LightEmission=1', 1),
      "unbounded_rate": candidate.replace('particles.Rate=7', 'particles.Rate=20', 1),
      "unbounded_distance": candidate.replace('gui.MaxDistance=100', 'gui.MaxDistance=300', 1),
      "fake_authority": candidate + '\nlocal poison=Instance.new("RemoteEvent")\n',
      "per_frame_loop": candidate + '\nRunService.RenderStepped:Connect(function() end)\n',
      "save_side_effect": candidate + '\nlocal data=game:GetService("DataStoreService")\n',
      "cleanup_removed": candidate.replace("local old=character:FindFirstChild(FOLDER)", "local old=nil", 1),
      "snapshot_weakened": candidate.replace("and s.remaining>0", "and true", 1),
      "no_cosmetic_flag": candidate.replace('folder:SetAttribute("ClientCosmeticOnly",true)', '', 1),
    }
    for name, input_ in bad.items():
        require(input_ != candidate, "TEST_MUTATION_IDENTITY_" + name)
        try:
            check(original, input_, exact_hash=False)
        except ValueError:
            continue
        raise AssertionError("NEGATIVE_NOT_CAUGHT_" + name)
    return len(bad)

def main() -> None:
    cli=argparse.ArgumentParser()
    cli.add_argument("--original", type=Path, required=True)
    cli.add_argument("--candidate", type=Path, required=True)
    cli.add_argument("--out", type=Path, required=True)
    args=cli.parse_args()
    original=args.original.read_bytes().decode("utf-8")
    candidate=args.candidate.read_bytes().decode("utf-8")
    report=check(original,candidate)
    report["negative_mutants_rejected"]=verify_negatives(original,candidate)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps(report,ensure_ascii=False))

if __name__=="__main__":
    main()
