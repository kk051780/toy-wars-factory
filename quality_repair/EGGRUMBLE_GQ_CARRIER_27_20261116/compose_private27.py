#!/usr/bin/env python3
"""27-source isolated adapter: compose original #484 GQ26 + #502 egg-carrier fix.
Does not rewrite author assets, perform GitHub writes, or make a Studio claim.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

GAME = "handoffs/P0D-PQG-SEVEN-HERO-PLAYABLE-20261116"
BOT = "EGGRUMBLE_BotActors.luau"
NAV = "EGGRUMBLE_BotPathRouter.luau"
HOST = "EGGRUMBLE_LobbyCastleModesPreview.server.luau"
POLICY = "EGGRUMBLE_CarrierBotTargeting.luau"
REQUIRE_OLD = 'local Router=require(script.Parent:WaitForChild("EGGRUMBLE_BotPathRouter"))'
ORIGINAL_STEALTH = 'and os.clock()>=(player:GetAttribute("EGGRUMBLE_StealthUntil") or 0)'
CARRIER_STEALTH = 'and CarrierBotTargeting.canStrike(pc.heldEggs,player:GetAttribute("EGGRUMBLE_StealthUntil"),now)'
REQUIRE_NEW = 'local CarrierBotTargeting=require(script.Parent:WaitForChild("EGGRUMBLE_CarrierBotTargeting"))'


def once_replace(source: str, old: str, new: str, which: str) -> str:
    assert source.count(old) == 1, (which, "upstream drift or already applied", old)
    assert new not in source, (which, "duplicate patch")
    return source.replace(old, new, 1)


def patch_original_quality_bot(source: str) -> str:
    assert source.count("local function tryHeroAttack") == 1
    assert source.count("local now=os.clock()") >= 1
    assert 'session.rules.castles[tostring(player.UserId)]' in source
    assert 'and (session.mode~="TEAM" or pc.team~=my.team)' in source
    assert 'clearHeroStrike(actor,character,' in source
    assert 'h:TakeDamage(BOT_HERO_DAMAGE)' in source
    source = once_replace(source, REQUIRE_OLD, REQUIRE_OLD + "\n" + REQUIRE_NEW, "require")
    source = once_replace(source, ORIGINAL_STEALTH, CARRIER_STEALTH, "bot melee")
    return source


def main() -> None:
    parser = argparse.ArgumentParser()
    for name in ("author","quality","art","score","carrier","art_project","out"):
        parser.add_argument("--" + name.replace("_","-"), type=Path, required=True)
    a = parser.parse_args()
    a.out.parent.mkdir(parents=True, exist_ok=True)
    out = a.out.resolve()
    assert out.suffix == ".json" and out.parent.name == "artifacts"
    qdir = (a.quality / GAME).resolve(strict=True)
    carrier_file = (a.carrier / GAME / POLICY).resolve(strict=True)
    fixed = (out.parent / "_quality_502").resolve()
    (fixed / GAME).mkdir(parents=True, exist_ok=True)
    for f in (BOT, NAV, HOST):
        source = (qdir / f).read_text(encoding="utf-8")
        if f == BOT:
            source = patch_original_quality_bot(source)
        (fixed / GAME / f).write_text(source, encoding="utf-8")
    policy = carrier_file.read_text(encoding="utf-8")
    assert "function Targeting.canStrike" in policy
    assert "if carriedEggs > 0 then" in policy
    assert "return now >= stealthUntil" in policy

    composer = (a.quality / "quality_repair/EGGRUMBLE_V3_GQ_CURRENT26_20261116/compose.py").resolve(strict=True)
    subprocess.run([
        sys.executable, str(composer),
        "--author", str(a.author), "--quality", str(fixed),
        "--art", str(a.art), "--score", str(a.score),
        "--art-project", str(a.art_project), "--out", str(out),
    ], check=True)
    project = json.loads(out.read_text(encoding="utf-8"))
    server = project["tree"]["ServerScriptService"]
    clients = project["tree"]["StarterPlayer"]["StarterPlayerScripts"]
    assert len(server) - 1 == 23 and len(clients) - 1 == 3
    assert POLICY.removesuffix(".luau") not in server
    import os
    server[POLICY.removesuffix(".luau")] = {"$path":os.path.relpath(carrier_file,out.parent).replace(os.sep,"/")}
    project["name"] = "EGGRUMBLE_GQ_CARRIER_27_PRIVATE_SOURCE_NO_RC"
    out.write_text(json.dumps(project, ensure_ascii=False, indent=2)+"\n",encoding="utf-8")
    assert len(server) - 1 == 24 and len(clients) - 1 == 3

    receipt_file = out.parent / "SOURCE_RECEIPT.json"
    receipt = json.loads(receipt_file.read_text(encoding="utf-8"))
    assert receipt["script_count"] == 26 and receipt["server_count"] == 23
    receipt["script_count"] = 27
    receipt["server_count"] = 24
    receipt["source_sha256"][POLICY.removesuffix(".luau")] = hashlib.sha256(carrier_file.read_bytes()).hexdigest()
    receipt["quality_overrides"].extend(["EGGRUMBLE_CarrierBotTargeting", "EGGRUMBLE_BotActors.carrier_stealth_predicate_ONLY"])
    receipt["carrier_patch"] = {"original_quality_AI_preserved": True,
                                 "original_source_ref": "#502",
                                 "input_author_isolate": True,
                                 "no_duplicate_AI_or_egg_rule": True}
    receipt["official_rc_adopted"] = False
    receipt_file.write_text(json.dumps(receipt, ensure_ascii=False, indent=2)+"\n",encoding="utf-8")
    assert set(receipt["source_sha256"]) == (
        set(server) | set(clients)) - {"$className"}, "27-source receipt missing/extra"
    print("EGGRUMBLE_GQ_CARRIER_27_SOURCE_COMPOSITION_PASS",len(receipt["source_sha256"]))


if __name__ == "__main__":
    main()
