#!/usr/bin/env python3
"""GQ470 FB015: two bounded 3D KO slashes replace a generic Neon KO sphere.

A-only SOURCE PREP on selected REAL69, not a new combat/score authority.
Real Studio and Android art gates remain untested.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
from pathlib import Path

BASE = "273e763c42ee0f405ef854b75c3cf071b078e896"
PUBLISHED_KO_SHA = "b5ae780bf885813155f0ae8a99ff15577a8cb8ed75f5126b6a265ff7d022c703"
OWNER_LIVE_CAP_SHA = "63e6658dd635588f71ffdb21a130b8b837f7862abfbe9d4eeb2f66e26638a8b8"
ROUTE = "ServerScriptService/EGGRUMBLE_ImpactFeedback"
OLD_SHA = "d916a97af0efb3a8ec39aaa656a4e901aad520f20a8f3c7305700480936a306a"
FEATURE = "GQ470_FB015_CONFIRMED_KO_SLASH_REAL69_20261120"
PROJECT = "EGGRUMBLE_REAL69.project.json"
RECEIPT = "REAL69_LEGACY_INTAKE_RECEIPT.json"
OFF = "OFF69_KO_SLASH"

OLD = """function Feedback.ko(world:Instance,target:Model,role:string):boolean
 -- One short radial burst per confirmed Humanoid.Died, not client-predicted KOs.
 if not world.Parent or not target.PrimaryPart or not budget(true) then return false end
 local at=target.PrimaryPart.Position
 local ring=Instance.new("Part")
 ring.Name="EGGRUMBLE_KO_BURST"
 ring.Shape=Enum.PartType.Ball
 ring.Size=Vector3.new(1,1,1)
 ring.Material=Enum.Material.Neon
 ring.Anchored=true;ring.CanCollide=false;ring.CanTouch=false
 ring.CanQuery=false;ring.CastShadow=false
 ring.Color=colors[role] or colors.WARRIOR
 ring.Transparency=.37;ring.Position=at
 ring.Parent=world
 local tween=game:GetService("TweenService"):Create(
  ring,TweenInfo.new(.24,Enum.EasingStyle.Quad,Enum.EasingDirection.Out),
  {Size=Vector3.new(6,3.2,6),Transparency=1})
 tween:Play()
 Debris:AddItem(ring,.32)
 return true
end
"""

NEW = """function Feedback.ko(world:Instance,target:Model,role:string):boolean
 -- GQ470_FB015_CONFIRMED_KO_SLASH_REAL69_20261120
 -- Real server-confirmed KO only. Two solid asymmetrical 3D slash fins
 -- replace one expanding Neon sphere; no light, particles, Remote or audio.
 -- Original six-KOs-per-second budget applies to the whole two-fin burst.
 -- Art orientation follows horizontal victim facing; no camera-facing HUD.
 if not world.Parent or not target.PrimaryPart or not budget(true) then return false end
 local pivot=target.PrimaryPart.CFrame
 local at=pivot.Position
 local flatLook=Vector3.new(pivot.LookVector.X,0,pivot.LookVector.Z)
 if flatLook.Magnitude<.001 then flatLook=Vector3.new(0,0,-1) end
 local burstFrame=CFrame.lookAt(at,at+flatLook.Unit)
 local accent=colors[role] or colors.WARRIOR
 for side=-1,1,2 do
  local fin=Instance.new("WedgePart")
  fin.Name="EGGRUMBLE_KO_BURST"
  fin.Size=Vector3.new(.34,1.65,.44)
  fin.Material=Enum.Material.SmoothPlastic
  fin.Anchored=true;fin.CanCollide=false;fin.CanTouch=false
  fin.CanQuery=false;fin.CastShadow=false
  fin.Color=if side==1 then accent else Color3.fromRGB(245,245,235)
  fin.Transparency=.12
  fin.CFrame=burstFrame*CFrame.new(side*.38,1.0,0)
   *CFrame.Angles(0,math.rad(side*28),math.rad(side*37))
  fin.Parent=world
  local endAt=fin.CFrame*CFrame.new(side*.74,.7,0)
  local tween=TweenService:Create(
   fin,TweenInfo.new(.23,Enum.EasingStyle.Quad,Enum.EasingDirection.Out),
   {Size=Vector3.new(.8,3.5,.28),CFrame=endAt,Transparency=1})
  tween:Play()
  Debris:AddItem(fin,.30)
 end
 return true
end
"""

def sha(blob: bytes) -> str:
    return hashlib.sha256(blob).hexdigest()

def must(value: bool, reason: str) -> None:
    if not value:
        raise ValueError("RED_KO_SLASH_" + reason)

def selected(root: Path) -> dict[str, Path]:
    project = json.loads((root / PROJECT).read_text(encoding="utf-8"))
    paths: dict[str, Path] = {}
    def walk(node: dict, prefix: str = ""):
        for key, child in node.items():
            if key == "$path":
                path = (root / child).resolve()
                must(path.is_relative_to(root.resolve()) and path.is_file(), "BAD_PATH")
                must(prefix not in paths, "DUPLICATE_ROUTE")
                paths[prefix] = path
            elif not key.startswith("$") and isinstance(child, dict):
                walk(child, f"{prefix}/{key}" if prefix else key)
    walk(project["tree"])
    return paths

def transform(source: str) -> str:
    must(source.count(OLD) == 1, "ORIGINAL_KO_ANCHOR")
    must(FEATURE not in source, "DOUBLE_PATCH")
    must('local Debris=game:GetService("Debris")' in source, "SERVICE_ANCHOR")
    for lock in ("local MAX_KO_BURSTS_PER_SEC=6\n", "local MAX_FEEDBACK_PER_SEC=18",
                 "function Feedback.hit(", "function Feedback.attacker(",
                 "function Feedback.clear(", "if not budget(false)", "or not budget(true)"):
        must(lock in source, "ORIGINAL_CONTRACT")
    must("RemoteEvent" not in NEW and "TakeDamage" not in NEW and "DataStore" not in NEW, "NO_NEW_AUTHORITY")
    out = source.replace('local Debris=game:GetService("Debris")',
                         'local Debris=game:GetService("Debris")\nlocal TweenService=game:GetService("TweenService")', 1)
    out = out.replace(OLD, NEW, 1)
    must(out.count(FEATURE) == 1 and out.count('Instance.new("WedgePart")') == 1, "TWO_FIN_SCULPT")
    must('local MAX_KO_BURSTS_PER_SEC=6\n' in out, "RATE_LIMIT")
    must(source[source.index("function Feedback.attacker("):] ==
         out[out.index("function Feedback.attacker("):], "TAIL_BYTE_EXACT")
    return out

def self_test():
    fixture = ('local Debris=game:GetService("Debris")\n'
               'local MAX_KO_BURSTS_PER_SEC=6\nlocal MAX_FEEDBACK_PER_SEC=18\n'
               'function Feedback.hit() if not budget(false) then return false end end\n'
               + OLD +
               'function Feedback.attacker() end\nfunction Feedback.clear() end\n')
    patched = transform(fixture)
    must('WedgePart' in patched and 'Enum.Material.Neon' not in patched and
         "TweenService:Create" in patched and 'for side=-1,1,2 do' in patched and
         "local burstFrame=CFrame.lookAt(at,at+flatLook.Unit)" in patched and
         "flatLook.Magnitude<.001" in patched, "SCULPT_PRESENT")
    for mutant in (patched, fixture.replace(OLD, ""), fixture.replace("MAX_KO_BURSTS_PER_SEC=6", "MAX_KO_BURSTS_PER_SEC=60"),
                   fixture.replace('local Debris=game:GetService("Debris")', ""),
                   fixture.replace("function Feedback.attacker(", "function Attacker("),
                   fixture.replace("or not budget(true)", "or budget(true)")):
        try:
            transform(mutant)
        except ValueError:
            continue
        raise AssertionError("NEGATIVE_MUTATION_ACCEPTED")
    print("GQ470_KO_SLASH_6_NEGATIVES_PASS")

def apply_owner_live_cap(published: bytes) -> bytes:
    """Reuse the exact source provided in #928 comment 7130786017."""
    must(sha(published) == PUBLISHED_KO_SHA, "EXACT_PUBLISHED_KO_SOURCE")
    changes = (
        (
            b"local MAX_KO_BURSTS_PER_SEC=6\n",
            b"local MAX_KO_BURSTS_PER_SEC=6\nlocal MAX_LIVE_KO_BURSTS=6\n",
        ),
        (
            b"local koCount=0\n",
            b"local koCount=0\n"
            b"-- A burst owns both fins until neither is parented. Bounded by the live cap,\n"
            b"-- never by the number of KOs in a long match. No per-frame or timer loop.\n"
            b"local liveKOBursts:{{BasePart}}={}\n",
        ),
        (
            b" if not world.Parent or not target.PrimaryPart or not budget(true) then return false end\n local pivot=",
            b" if not world.Parent or not target.PrimaryPart then return false end\n"
            b" -- A fixed-second rate limiter alone permits two overlapping bursts of six\n"
            b" -- around a second boundary. Reclaim only fully removed pairs (Debris or\n"
            b" -- arena teardown); a single remaining fin still occupies the burst slot.\n"
            b" for i=#liveKOBursts,1,-1 do\n"
            b"  local live=false\n"
            b"  for _,fin in ipairs(liveKOBursts[i]) do\n"
            b"   if fin.Parent then live=true;break end\n"
            b"  end\n"
            b"  if not live then table.remove(liveKOBursts,i) end\n"
            b" end\n"
            b" if #liveKOBursts>=MAX_LIVE_KO_BURSTS or not budget(true) then return false end\n local pivot=",
        ),
        (
            b" for side=-1,1,2 do\n",
            b" local burst:{BasePart}={}\n table.insert(liveKOBursts,burst)\n for side=-1,1,2 do\n",
        ),
        (b"  fin.Parent=world\n", b"  table.insert(burst,fin)\n  fin.Parent=world\n"),
    )
    fixed = published
    for previous, replacement in changes:
        must(fixed.count(previous) == 1, "OWNER_LIVE_CAP_ANCHOR")
        fixed = fixed.replace(previous, replacement, 1)
    must(sha(fixed) == OWNER_LIVE_CAP_SHA, "COMPLETE_ORIGINAL_OWNER_LIVE_CAP")
    inverse = fixed
    for previous, replacement in reversed(changes):
        must(inverse.count(replacement) == 1, "OWNER_LIVE_CAP_INVERSE_ANCHOR")
        inverse = inverse.replace(replacement, previous, 1)
    must(inverse == published, "OWNER_LIVE_CAP_INVERSE")
    return fixed


def apply(root: Path, head: str, candidate_head: str):
    must(re.fullmatch(r"[a-f0-9]{40}", candidate_head) is not None, "ACTUAL_CANDIDATE_CHECKOUT")
    official = json.loads((root / "UNION22_FINAL_ADMISSION.json").read_text())
    must(official.get("receipt_provenance") == "OFFICIAL" and official.get("official_build_head") == BASE
         and official.get("formal_rc_adoption_proven") is True, "EXACT_OFFICIAL_SOURCE_CHAIN")
    paths = selected(root)
    receipt = json.loads((root / RECEIPT).read_text(encoding="utf-8"))
    must(head == BASE and receipt.get("build_head") == BASE, "STALE_OFFICIAL")
    must(receipt.get("official_branch") == "rc/p0d-s1-kids-rc01", "NOT_SINGLE_RC")
    must(receipt.get("selected_source_count") == len(paths) == 69, "NOT_REAL69")
    must(set(paths) == set(receipt["source_hashes"]), "SOURCE_ROUTE_SET")
    must(receipt["source_classes"].get(ROUTE) == "ModuleScript", "WRONG_CLASS")
    must(receipt["source_hashes"].get(ROUTE) == OLD_SHA, "STALE_SOURCE_HASH")
    for route, path in paths.items():
        must(sha(path.read_bytes()) == receipt["source_hashes"][route], "INPUT_SOURCE_" + route)
    original = paths[ROUTE].read_bytes()
    changed = apply_owner_live_cap(transform(original.decode("utf-8")).encode("utf-8"))
    backup = root / OFF
    must(not backup.exists(), "DUPLICATE_OFF")
    backup.mkdir()
    shutil.copytree(root / "sources", backup / "sources")
    for name in (PROJECT, RECEIPT, "EGGRUMBLE_REAL69_PRIVATE.rbxlx"):
        shutil.copyfile(root / name, backup / name)
    paths[ROUTE].write_bytes(changed)
    before = selected(backup)
    must({route for route, path in paths.items()
          if path.read_bytes() != before[route].read_bytes()} == {ROUTE}, "OTHER68_CHANGED")
    must((root / PROJECT).read_bytes() == (backup / PROJECT).read_bytes(), "PROJECT_CHANGED")
    receipt.update({
        "build_head": candidate_head,
        "official_build_head": None,
        "receipt_provenance": "A_PRIVATE_SOURCE_PREP_ONLY",
        "canonical_build": False,
        "formal_rc_adoption_proven": False,
        "execution_context": {"kind": "A_PRIVATE_SOURCE_PREP_ONLY", "build_head": candidate_head,
                              "exact_official_parent": head},
    })
    receipt["source_hashes"][ROUTE] = sha(changed)
    receipt["gq470_ko_slashed_confirmed"] = {
        "feature_id": FEATURE,
        "target": ROUTE,
        "before_sha256": sha(original),
        "after_sha256": sha(changed),
        "other_sources_unchanged": 68,
        "ko_per_second_limit": 6,
        "max_parented_ko_pairs": 6,
        "max_parented_ko_fin_parts": 12,
        "official_parent_head": head,
        "official_parent_receipt_sha256": sha((backup / RECEIPT).read_bytes()),
        "original_author_live_cap": "https://github.com/kk051780/toy-wars-factory/pull/928#issuecomment-7130786017",
        "new_parts_per_confirmed_ko": 2,
        "previous_parts_per_confirmed_ko": 1,
        "yaw_follows_victim": True,
        "zero_flat_look_guard": True,
        "new_remotes": 0,
        "new_gameplay_authority": False,
        "rollback": OFF,
        "source_only": True,
        "android_15min": "NOT_TESTED",
        "pc_android_beauty": "NOT_TESTED",
        "first3min_fun": "NOT_TESTED",
        "owner_accepted": False,
    }
    (root / RECEIPT).write_text(json.dumps(receipt, ensure_ascii=False,
                                            sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print("GQ470_KO_SLASH_REAL69_SOURCE_PATCH_PASS", sha(changed))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", type=Path)
    parser.add_argument("--head", default=BASE)
    parser.add_argument("--candidate-head")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
    else:
        must(args.base is not None and args.candidate_head is not None, "MISSING_ARTIFACT_OR_CANDIDATE_HEAD")
        apply(args.base, args.head, args.candidate_head)
