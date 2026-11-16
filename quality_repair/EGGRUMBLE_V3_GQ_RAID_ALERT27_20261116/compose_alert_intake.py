#!/usr/bin/env python3
"""Source-selective RAID ALERTS intake on TOP of the ORIGINAL #484 26-script composer.

Does not modify author #482, quality #484, ART #485, SCORE #487 source.
Writes only a new private preview manifest + one derived Game host for the
single existing V3 Studio-only script. This is not the authenticated #220 RC.
"""
import argparse
import copy
import hashlib
import json
import os
import re
from pathlib import Path

GAME = Path("handoffs/P0D-PQG-SEVEN-HERO-PLAYABLE-20261116")
MODULE_NAME = "EGGRUMBLE_RaidAlerts"
HOST_NAME = "EGGRUMBLE_LobbyCastleModesPreview"

def unique_replace(source: str, old: str, new: str, label: str) -> str:
    assert source.count(old) == 1, (label, "source drift or duplicate patch", source.count(old))
    assert new not in source, (label, "already adopted elsewhere")
    return source.replace(old, new)

def apply_alerts(host: str) -> str:
    """Exactly the #495 source-owned diff; keep ART/SCORE and #484 ramp intact."""
    host = unique_replace(
        host,
        'local RoundReplay=require(script.Parent:WaitForChild("EGGRUMBLE_RoundReplay"))',
        'local RoundReplay=require(script.Parent:WaitForChild("EGGRUMBLE_RoundReplay"))\n'
        'local RaidAlerts=require(script.Parent:WaitForChild("EGGRUMBLE_RaidAlerts"))',
        "require",
    )
    host = unique_replace(
        host,
        '  if c.alive and c.heldEggs>0 then pcall(function() Rules.depositEggs(session.rules,entry.id,c.heldEggs) end) end',
        '  if c.alive and c.heldEggs>0 then\n'
        '   local deposited=pcall(function() Rules.depositEggs(session.rules,entry.id,c.heldEggs) end)\n'
        '   -- Players must see a completed deposit immediately, without waiting for a bot tick.\n'
        '   if deposited then session.refresh() end\n'
        '  end',
        "deposit",
    )
    host = unique_replace(
        host,
        " session.refresh=function()",
        ' session.refresh=function()\n'
        '  -- Optional cosmetic lane: a failed alert must never stop egg/castle/AI gameplay.\n'
        '  if session.raidAlertsDisabled~=true then\n'
        '   local alertOk,alertErr=pcall(RaidAlerts.process,session)\n'
        '   if not alertOk then\n'
        '    session.raidAlertsDisabled=true\n'
        '    warn("[EGGRUMBLE GQ] YELLOW_RAID_ALERTS_OPTIONAL:",alertErr)\n'
        '   end\n'
        '  end',
        "one-game-refresh",
    )
    host = unique_replace(
        host,
        " Rules.start(session.rules)",
        ' Rules.start(session.rules)\n'
        ' -- Seed the original castle-HP snapshot before any player or bot deals siege damage.\n'
        ' -- This also paints the initial scoreboard exactly once in the existing refresh path.\n'
        ' session.refresh()',
        "initial-state",
    )
    assert host.count('local RaidAlerts=require(') == 1
    assert host.count('pcall(RaidAlerts.process,session)') == 1
    return host

def script_map(project: Path, source_manifest: dict) -> dict:
    result = {}
    def walk(node, parts=()):
        for key, value in node.items():
            if key.startswith("$") or not isinstance(value, dict):
                continue
            trail = parts + (key,)
            if "$path" in value:
                assert set(value) == {"$path"}, trail
                file = (project.parent / value["$path"]).resolve(strict=True)
                assert trail not in result
                result[trail] = file
            else:
                walk(value, trail)
    walk(source_manifest["tree"])
    return result

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline-project", type=Path, required=True)
    parser.add_argument("--author-project", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    baseline = args.baseline_project.resolve(strict=True)
    author = args.author_project.resolve(strict=True)
    out = args.out.resolve()
    assert out.parent.is_dir() and out != baseline and out != author
    own = Path(__file__).resolve().parents[2] / GAME
    own_game = (own / "EGGRUMBLE_LobbyCastleModesPreview.server.luau").resolve(strict=True)
    own_alerts = (own / "EGGRUMBLE_RaidAlerts.luau").resolve(strict=True)
    raw = json.loads(baseline.read_text(encoding="utf-8"))
    author_raw = json.loads(author.read_text(encoding="utf-8"))
    before = script_map(baseline, raw)
    expected = len(before)
    assert expected == 26, ("#484 original composite must be exactly 26", expected)
    game_key = ("ServerScriptService", HOST_NAME)
    assert game_key in before
    original = script_map(author, author_raw)
    assert len(original) == 21, ("#482 original author must supply 21 exact scripts", len(original))
    assert original[game_key].read_text(encoding="utf-8") != before[game_key].read_text(encoding="utf-8"), "expected #484 castle-ramp-only patch"
    # Strong original-author diff provenance: our adapter exactly reproduces the
    # author-side #495 host, without unrelated rewrites.
    source_host = original[game_key].read_text(encoding="utf-8")
    assert apply_alerts(source_host) == own_game.read_text(encoding="utf-8"), (
        "raid hook drift from owned #495 host; reconcile manually")
    baseline_host = before[game_key].read_text(encoding="utf-8")
    assert baseline_host.count("CastleAccessRamp") == 1, "original #484 quality ramp missing"
    assert "EGGRUMBLE_RaidAlerts" not in baseline_host, "quality already owns raid alerts; collision"
    after_host = apply_alerts(baseline_host)
    assert "CastleAccessRamp" in after_host
    patched_host = out.parent / "EGGRUMBLE_LobbyCastleModesPreview_ALERT27.server.luau"
    patched_host.write_text(after_host, encoding="utf-8")
    new_manifest = copy.deepcopy(raw)
    server = new_manifest["tree"]["ServerScriptService"]
    assert MODULE_NAME not in server
    assert len(server) - 1 == 23 and len(new_manifest["tree"]["StarterPlayer"]["StarterPlayerScripts"]) - 1 == 3
    server[HOST_NAME] = {"$path": os.path.relpath(patched_host, out.parent).replace(os.sep, "/")}
    server[MODULE_NAME] = {"$path": os.path.relpath(own_alerts, out.parent).replace(os.sep, "/")}
    new_manifest["name"] = "EGGRUMBLE_V3_GQ_AUTHOR_ART_SCORE_ALERT27_PRIVATE_NO_PUBLISH"
    out.write_text(json.dumps(new_manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    after = script_map(out, new_manifest)
    assert len(after) == 27
    assert set(after) - set(before) == {("ServerScriptService", MODULE_NAME)}
    assert set(after) - {game_key, ("ServerScriptService", MODULE_NAME)} == set(before) - {game_key}
    # 25 untouched author/ART/SCORE/AI files. Original composer never modified.
    assert all(after[k] == before[k] for k in before if k != game_key)
    host_requirements = re.findall(r'script\.Parent:WaitForChild\("([^"]+)"\)', after_host)
    assert all(name in server for name in host_requirements), ("unmapped dependency", host_requirements)
    assert "EGGRUMBLE_RaidItemIntake" in after_host
    assert "EGGRUMBLE_NeutralStoneGiant" in after_host
    assert "EGGRUMBLE_BossSessionFence" in after_host
    assert "CastleAccessRamp" in after_host
    assert sum(path.name.endswith(".server.luau") for path in after.values()) == 4, "expected game host + 3 ART servers"
    assert ("ServerScriptService", "EGGRUMBLE_ScoreBalance") in after
    all_hashes = {"/".join(key): hashlib.sha256(file.read_bytes()).hexdigest()
                  for key, file in sorted(after.items())}
    receipt = {
        "status": "SOURCE_ONLY_PRIVATE_ART_SCORE_ALERT_INTAKE_NOT_OFFICIAL_RC",
        "author_project": str(author), "quality_26_project": str(baseline),
        "script_count": 27, "game_hosts": 1, "server_modules": 20,
        "server_art_scripts": 3, "client_scripts": 3,
        "unchanged_quality_26_sources": 25,
        "one_host_overlay": HOST_NAME,
        "added_original_alert_module": str(own_alerts),
        "source_sha256": all_hashes,
        "studio": "NOT_TESTED", "android": "NOT_TESTED",
        "owner_accepted": False, "official_rc_integrated": False,
        "published": False
    }
    (out.parent / "RAID_ALERT27_SOURCE_RECEIPT.json").write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("RAID_ALERT27_ORIGINAL_26_PLUS_ONE_SOURCE_SELECTIVE_PASS",
          len(after), "unchanged26", receipt["unchanged_quality_26_sources"])

if __name__ == "__main__":
    main()
