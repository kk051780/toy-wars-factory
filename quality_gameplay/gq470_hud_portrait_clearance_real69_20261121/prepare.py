#!/usr/bin/env python3
"""One-source REAL69 portrait HUD ART candidate, not canonical RC.

Uses exact official action artifact #14610422120 (run #44695199140).
No alternate Game, Remote, Store, gameplay/HP mutation, or live Studio claims.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import shutil
from pathlib import Path

BASE = "e80973c354f14a0d0088577f3cc1a875454f0f8f"
RUN = 44695199140
MARK = "GQ470_FB015_HUD_PORTRAIT_CLEARANCE_REAL69_20261121"
TARGET = "ReplicatedStorage/EGGRUMBLE_HudPresentationPolicy"
PROJECT = "EGGRUMBLE_REAL69.project.json"
RECEIPT = "REAL69_LEGACY_INTAKE_RECEIPT.json"
ORIGINAL = (
    ("        local menuY = math.min(133, h * .18)",
     """        -- GQ470_FB015_HUD_PORTRAIT_CLEARANCE_REAL69_20261121
        -- On compact portrait screens the old y=h*.18 put MENU buttons
        -- over the HP status strip. Reserve 7px clearance beneath it.
        local menuY = clamp(h * .18, 64, 133)
        -- The 320px-wide layout can draw MENU buttons nearer the edge
        -- without stealing the central combat view.
        local itemInset = if w <= 360 then 45 else 65"""),
    ('            INVUL = at(x - 102, h - 71, 46, "無敵"),',
     '            INVUL = at(x - 122, h - 71, 46, "無敵"),'),
    ('            ITEM = at(x - 65, menuY, 42, "道具"),',
     '            ITEM = at(x - itemInset, menuY, 42, "道具"),'),
)

def require(yes: bool, msg: str) -> None:
    if not yes:
        raise ValueError("RED_GQ470_HUD_PORTRAIT_" + msg)

def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def patch_module(src: str) -> str:
    require(MARK not in src, "ALREADY_PATCHED_OR_SOURCE_DRIFT")
    require("function M.layout(w, h, hand)" in src
            and "function M.display(snapshot)" in src
            and "function M.menuItems(kind, owned)" in src
            and src.rstrip().endswith("return M"), "HUD_POLICY_IDENTITY")
    for old, new in ORIGINAL:
        require(src.count(old) == 1, "ANCHOR_DRIFT_" + old.strip()[:35])
        src = src.replace(old, new, 1)
    require(src.count(MARK) == 1, "MARKER_OR_PATCH_FAIL")
    return src

def selected_map(root: Path) -> dict[str, Path]:
    project = json.loads((root / PROJECT).read_text(encoding="utf-8"))
    routes: dict[str, Path] = {}
    def walk(node: dict, route: str) -> None:
        if "$path" in node:
            routes[route] = root / node["$path"]
        for key, value in node.items():
            if not key.startswith("$") and isinstance(value, dict):
                walk(value, (route + "/" + key) if route else key)
    walk(project["tree"], "")
    return routes

NATIVE_TEST = r'''
local function overlap(a,b)
 return math.abs(a.x-b.x)*2 < (a.size+b.size)
  and math.abs(a.y-b.y)*2 < (a.size+b.size)
end
local cases={
 {320,260},{320,400},{360,640},{375,667},{393,851},
 {480,320},{851,393},{1280,720},{1920,1080},
}
local checked=0
for _,v in ipairs(cases) do
 for _,hand in ipairs({"RIGHT","LEFT"}) do
  local d=M.layout(v[1],v[2],hand)
  local p=d.anchors
  assert(p.ATTACK and p.MOVE and p.MAP)
  if d.orientation=="PORTRAIT" then
   assert(not overlap(p.INVUL,p.MUSOU),"RED_INVUL_MUSOU_OVERLAP")
   assert(not overlap(p.ITEM,p.DODGE),"RED_ITEM_DODGE_OVERLAP")
   assert(not overlap(p.SKILL,p.JUMP),"RED_SKILL_JUMP_OVERLAP")
   assert(not overlap(p.INVUL,p.MOVE),"RED_INVUL_STICK_OVERLAP")
   local top=p.ITEM.y-p.ITEM.size/2
   local statusBottom=d.chrome.status.y+d.chrome.status.h
   assert(top>=statusBottom+6,"RED_ITEM_STATUS_OVERLAP")
   top=p.SKILL.y-p.SKILL.size/2
   assert(top>=statusBottom+6,"RED_SKILL_STATUS_OVERLAP")
   if v[1]==320 and v[2]==260 then
    assert(math.abs(p.ITEM.x-(hand=="LEFT" and 95 or 225))<=1,
      "RED_NARROW_COMBAT_VIEW_STEAL")
   end
  end
  checked+=1
 end
end
assert(checked==18,"RED_CASES_MISSING")
print("GQ470_HUD_PORTRAIT_REAL_LUAU_LAYOUT_18_CASES_PASS")
'''
def native_test_source(policy: str) -> str:
    require(policy.rstrip().endswith("return M"), "NATIVE_MODULE_TAIL")
    return policy.rstrip()[:-len("return M")] + NATIVE_TEST

def self_test() -> None:
    fake = ("function M.layout(w, h, hand)\n"
            "        local menuY = math.min(133, h * .18)\n"
            '            INVUL = at(x - 102, h - 71, 46, "無敵"),\n'
            '            ITEM = at(x - 65, menuY, 42, "道具"),\n'
            "end\nfunction M.display(snapshot) end\n"
            "function M.menuItems(kind, owned) end\nreturn M\n")
    good = patch_module(fake)
    require(good.count(MARK) == 1
            and "clamp(h * .18, 64, 133)" in good
            and "at(x - 122" in good
            and "x - itemInset" in good, "SELF_PASS")
    negatives = [good, fake.replace("x - 102", "x - 103"),
                 fake.replace("math.min(133, h * .18)", "math.min(133, h * .19)"),
                 fake.replace("return M", "return Missing"),
                 fake.replace("function M.display(snapshot)", "function X(snapshot)")]
    for num, mutant in enumerate(negatives):
        try:
            patch_module(mutant)
        except ValueError:
            continue
        raise AssertionError("RED_MUTATION_ACCEPTED_" + str(num))
    print("GQ470_HUD_PORTRAIT_PATCH_5_NEGATIVE_MUTANTS_PASS")

def apply(root: Path) -> None:
    routes = selected_map(root)
    receipt = json.loads((root / RECEIPT).read_text(encoding="utf-8"))
    require(len(routes) == 69 and TARGET in routes, "REAL69_ROUTE_MISSING")
    require(receipt.get("build_head") == BASE
            and len(receipt.get("source_hashes", {})) == 69,
            "IMMUTABLE_ORIGINAL_RECEIPT")
    before = {k: digest(v.read_bytes()) for k,v in routes.items()}
    require(before == receipt["source_hashes"], "ORIGINAL_HASH_LOCK")
    # The result must remain one changed ModuleScript, not a new runtime writer.
    rollback = root / "OFF69_HUD_PORTRAIT_ROLLBACK"
    require(not rollback.exists(), "ROLLBACK_COLLISION")
    shutil.copytree(root / "sources", rollback / "sources")
    shutil.copy2(root / PROJECT, rollback / PROJECT)
    target = routes[TARGET]
    raw = target.read_text(encoding="utf-8")
    require(raw.encode("utf-8") == target.read_bytes(), "UTF8_SOURCE")
    changed = patch_module(raw)
    require(changed != raw, "PATCH_NOOP")
    target.write_text(changed, encoding="utf-8", newline="")
    after = {k: digest(v.read_bytes()) for k,v in routes.items()}
    require({k for k in routes if before[k] != after[k]} == {TARGET},
            "NOT_EXACT_ONE_SELECTED_SOURCE")
    require(all(before[k] == after[k] for k in routes if k != TARGET),
            "OTHER_68_CHANGED")
    (root / "HUD_PORTRAIT_NATIVE_TEST.luau").write_text(
        native_test_source(changed), encoding="utf-8")
    receipt["source_hashes"][TARGET] = after[TARGET]
    receipt["build_head"] = "A_PREP_NOT_CANONICAL_FROM_" + BASE
    receipt["gq470_fb015_hud_portrait"] = {
        "feature_id": MARK, "formal_rc_base": BASE, "run_id": RUN,
        "selected_route": TARGET, "expected_class": "ModuleScript",
        "original_source_sha256": before[TARGET],
        "candidate_source_sha256": after[TARGET],
        "source_count": 69, "unchanged_selected_sources": 68,
        "visual_change": "portrait button separation and HUD status clearance",
        "gameplay_authority_changed": False, "new_runtime_scripts": 0,
        "rollback": "OFF69_HUD_PORTRAIT_ROLLBACK",
        "native_rojo": "NOT_TESTED", "studio_android_fun": "NOT_TESTED",
        "art_human": "NOT_TESTED", "real_png": 0, "owner_accepted": False,
        "formal_rc_adopted": False,
    }
    (root / RECEIPT).write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8")
    print("GQ470_HUD_PORTRAIT_ONE_SELECTED_SOURCE_68_EXACT_PREP_PASS")

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", type=Path)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
    else:
        require(args.base is not None, "NO_OFFICIAL_ARTIFACT")
        apply(args.base)

if __name__ == "__main__":
    main()
