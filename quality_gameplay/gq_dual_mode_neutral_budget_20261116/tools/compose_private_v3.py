#!/usr/bin/env python3
"""Source-exact 21-off / 22-on ORIGINAL EGGRUMBLE private Rojo staging.

No writes to author files, official RC, or main. Every author source is blob SHA pinned.
"""
import argparse
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
REPO = HERE.parents[1]
AUTHOR_DIR = REPO / "handoffs/P0D-PQG-SEVEN-HERO-PLAYABLE-20261116"
LOCK = json.loads((HERE / "source_lock.json").read_text(encoding="utf-8"))
POLICY = HERE / "EGGRUMBLE_DualModeNeutralBudget.luau"
HOST = "EGGRUMBLE_LobbyCastleModesPreview.server.luau"
SWARM = "EGGRUMBLE_SwarmCombat.luau"
MODULE = "EGGRUMBLE_DualModeNeutralBudget.luau"


def git_blob(text: bytes) -> str:
    return hashlib.sha1(f"blob {len(text)}\0".encode() + text).hexdigest()


def swap_once(src: str, before: str, after: str, label: str) -> str:
    if src.count(before) != 1:
        raise AssertionError(f"{label}: expected exactly one source anchor, got {src.count(before)}")
    return src.replace(before, after, 1)


def patch_host(source: str) -> str:
    source = swap_once(
        source,
        'local BossSessionFence=require(script.Parent:WaitForChild("EGGRUMBLE_BossSessionFence"))',
        'local BossSessionFence=require(script.Parent:WaitForChild("EGGRUMBLE_BossSessionFence"))\n'
        '-- GQ528 PRIVATE ON only: one shared allocation across both active match sessions.\n'
        'local GQDualBudget=require(script.Parent:WaitForChild("EGGRUMBLE_DualModeNeutralBudget"))\n'
        'local gqDualBudget=GQDualBudget.new(128,96,32)',
        "host-share-one-budget",
    )
    source = swap_once(
        source,
        '  lifeConnections={},walkBaseline={},\n }\n',
        '   lifeConnections={},walkBaseline={},\n  }\n'
        '  session.neutralBudget=gqDualBudget\n'
        '  session.neutralBudgetEpoch=gqDualBudget:begin(mode)\n',
        "host-begin-epoch",
    )
    source = swap_once(
        source,
        '  if abandoned then session.rules.phase="ABANDONED" end\n',
        '   if abandoned then session.rules.phase="ABANDONED" end\n'
        '   -- Idempotent even if the horde folder was destroyed first.\n'
        '   if session.neutralBudgetEpoch then\n'
        '    gqDualBudget:retire(mode,session.neutralBudgetEpoch)\n'
        '    session.neutralBudgetEpoch=nil\n'
        '   end\n',
        "host-close-one-session",
    )
    return source


def patch_swarm(source: str) -> str:
    source = swap_once(
        source,
        ' local all=Instance.new("Folder");all.Name="NeutralHorde";all.Parent=session.world\n',
        '  local all=Instance.new("Folder");all.Name="NeutralHorde";all.Parent=session.world\n'
        '  if session.neutralBudget and session.neutralBudgetEpoch then\n'
        '   -- Manual folder destruction must not leak tickets before closeRound.\n'
        '   all.Destroying:Connect(function()\n'
        '    if session.neutralBudgetEpoch then\n'
        '     session.neutralBudget:retire(session.mode,session.neutralBudgetEpoch)\n'
        '    end\n'
        '   end)\n'
        '  end\n',
        "swarm-folder-destroy-fence",
    )
    source = swap_once(
        source,
        '  local m=soldier(all,at)\n  local h=m:FindFirstChildOfClass("Humanoid") :: Humanoid\n  live[m]=h\n',
        '  -- PRIVATE GQ528 ON: reserve one global live-model ticket BEFORE creating an NPC.\n'
        '  local ticket:string?=nil\n'
        '  if session.neutralBudget then\n'
        '   local permit,_reason=session.neutralBudget:acquire(session.mode,session.neutralBudgetEpoch)\n'
        '   if not permit then return end\n'
        '   ticket=permit\n'
        '  end\n'
        '  local constructed,model=pcall(soldier,all,at)\n'
        '  if not constructed then\n'
        '   if ticket then session.neutralBudget:release(ticket) end\n'
        '   warn("[GQ528] neutral spawn rejected",model)\n'
        '   return\n'
        '  end\n'
        '  local m=model :: Model\n'
        '  local h=m:FindFirstChildOfClass("Humanoid") :: Humanoid\n'
        '  if not h then\n'
        '   if ticket then session.neutralBudget:release(ticket) end\n'
        '   m:Destroy()\n'
        '   return\n'
        '  end\n'
        '  if ticket then\n'
        '   m.Destroying:Connect(function() session.neutralBudget:release(ticket) end)\n'
        '  end\n'
        '  live[m]=h\n',
        "swarm-atomic-spawn-and-ticket",
    )
    source = swap_once(
        source,
        '  h.Died:Connect(function()\n   live[m]=nil\n',
        '   h.Died:Connect(function()\n'
        '    if ticket then session.neutralBudget:release(ticket) end\n'
        '    live[m]=nil\n',
        "swarm-death-unique-release",
    )
    return source


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--mode", choices=["ON", "OFF"], default="ON")
    args = parser.parse_args()
    assert LOCK["author_head"] == "fe67d31bc8d1b3e481cd22d2be9ea54a1eb031c9"
    base_project = AUTHOR_DIR / "EGGRUMBLE_V3_STUDIO.project.json"
    assert git_blob(base_project.read_bytes()) == LOCK["author_project_sha"]
    project = json.loads(base_project.read_text(encoding="utf-8"))
    assert len(LOCK["original_sources"]) == 21
    assert HOST in LOCK["original_sources"] and SWARM in LOCK["original_sources"]
    assert "ServerScriptService" in project["tree"]
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    dest = out / "src"
    dest.mkdir(exist_ok=True)
    receipt = {
        "mode": args.mode,
        "original_author_head": LOCK["author_head"],
        "original_count": len(LOCK["original_sources"]),
        "scripts": {},
        "original_preserved": 0,
        "overlaid_original_sources": [],
        "private_only": True,
    }
    for name, pinned in LOCK["original_sources"].items():
        raw = (AUTHOR_DIR / name).read_bytes()
        assert git_blob(raw) == pinned, f"original blob changed: {name}"
        value = raw.decode("utf-8")
        if args.mode == "ON" and name == HOST:
            value = patch_host(value)
            receipt["overlaid_original_sources"].append(name)
        if args.mode == "ON" and name == SWARM:
            value = patch_swarm(value)
            receipt["overlaid_original_sources"].append(name)
        if value.encode() == raw:
            receipt["original_preserved"] += 1
        (dest / name).write_text(value, encoding="utf-8")
        receipt["scripts"][name] = {
            "original_git_blob": pinned,
            "staged_git_blob": git_blob(value.encode("utf-8")),
            "source_sha256": hashlib.sha256(value.encode("utf-8")).hexdigest(),
        }
    def rewrite_paths(obj):
        if isinstance(obj, dict):
            for key, value in obj.items():
                if key == "$path":
                    assert value in LOCK["original_sources"]
                    obj[key] = "src/" + value
                else:
                    rewrite_paths(value)
        elif isinstance(obj, list):
            for value in obj:
                rewrite_paths(value)
    rewrite_paths(project["tree"])
    if args.mode == "ON":
        shutil.copyfile(POLICY, dest / MODULE)
        project["tree"]["ServerScriptService"]["EGGRUMBLE_DualModeNeutralBudget"] = {"$path": "src/" + MODULE}
        receipt["scripts"][MODULE] = {
            "source_sha256": hashlib.sha256(POLICY.read_bytes()).hexdigest(),
            "staged_git_blob": git_blob(POLICY.read_bytes()),
        }
        assert receipt["original_preserved"] == 19
        assert sorted(receipt["overlaid_original_sources"]) == sorted([HOST, SWARM])
    else:
        assert receipt["original_preserved"] == 21
        assert receipt["overlaid_original_sources"] == []
    receipt["mapped_script_count"] = len(receipt["scripts"])
    assert receipt["mapped_script_count"] == (22 if args.mode == "ON" else 21)
    (out / "private_v3.project.json").write_text(json.dumps(project, indent=2, ensure_ascii=False) + "\n")
    (out / "source_lock_receipt.json").write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n")
    print(f"GQ528_PRIVATE_{args.mode}_{receipt['mapped_script_count']}_SOURCE_STAGE_PASS",
          receipt["original_preserved"], "original byte-identical")
    print(out)


if __name__ == "__main__":
    main()
