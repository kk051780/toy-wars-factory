#!/usr/bin/env python3
"""Source-exact, two-file overlay for #482 BotActors human PvP membership only.

This is not a separate Game, BotActor, combat server, or RC writer.
The caller must supply the immutable #482 original source files.
"""
import argparse
import hashlib
import json
from pathlib import Path

OWNER_HEAD = "fe67d31bc8d1b3e481cd22d2be9ea54a1eb031c9"
SOURCE_ROOT = "handoffs/P0D-PQG-SEVEN-HERO-PLAYABLE-20261116"
# Existing AI author #484, NOT a replacement AI implementation.
AI_AUTHOR_HEAD = "6b52eaf1f2725496277998fe0c5532b7a8fcaab5"
AI_BOT_BLOB = "832a26c9f713012b924234ce4cf8c1654a75654e"
HOST = "EGGRUMBLE_LobbyCastleModesPreview.server.luau"
BOT = "EGGRUMBLE_BotActors.luau"
OWNER_BLOBS = {
    HOST: "7162b209bf67b74a71553217f3f744e072a0365d",
    BOT: "fa38f24a26a619238e4c6a62b3ee582dc14cfe7a",
}

HOST_BEFORE = "sessions[mode]=session\n -- Clean up only this finished match;"
HOST_AFTER = (
    "sessions[mode]=session\n"
    "  -- Authoritative host-only membership fence for BotActors hero hits.\n"
    "  -- Never trust a stale castle ID or a client-side teleport as proof of participation.\n"
    "  session.isCurrentHuman=function(player:Player):boolean\n"
    "   return sessions[mode]==session and session.rules.phase==\"ACTIVE\"\n"
    "    and joined[player.UserId]==mode and player.Parent==Players\n"
    "    and session.rules.castles[tostring(player.UserId)]~=nil\n"
    "    and session.rules.castles[tostring(player.UserId)].isAI~=true\n"
    "  end\n"
    " -- Clean up only this finished match;"
)
BOT_BEFORE = (
    '  if pc and pc.alive and pc.id~=my.id and (session.mode~="TEAM" or pc.team~=my.team) then'
)
BOT_AFTER = (
    "  if pc and pc.alive and pc.id~=my.id\n"
    "   and session.isCurrentHuman~=nil and session.isCurrentHuman(player)\n"
    '   and (session.mode~="TEAM" or pc.team~=my.team) then'
)


def git_blob_sha(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def replace_exact(text: str, before: str, after: str, label: str) -> str:
    if text.count(before) != 1:
        raise ValueError(f"{label}: expected precisely one original insertion point; found {text.count(before)}")
    if after in text:
        raise ValueError(f"{label}: overlay already present")
    changed = text.replace(before, after, 1)
    if changed.replace(after, before, 1) != text:
        raise AssertionError(f"{label}: non-selective mutation")
    return changed


def compose(host: str, bot: str) -> tuple[str, str]:
    if not host.startswith("--!strict\n") or not bot.startswith("--!strict\n"):
        raise ValueError("Expected strict Luau source")
    patched_host = replace_exact(host, HOST_BEFORE, HOST_AFTER, HOST)
    patched_bot = replace_exact(bot, BOT_BEFORE, BOT_AFTER, BOT)
    if patched_bot.count("session.isCurrentHuman(player)") != 1:
        raise AssertionError("Expected exactly one BotActors PvP target fence")
    if patched_host.count("session.isCurrentHuman=function") != 1:
        raise AssertionError("Expected exactly one host callback")
    return patched_host, patched_bot


def run(source_dir: Path, out_dir: Path, ai_bot_file: Path | None = None) -> dict:
    texts = {}
    expected_blobs = dict(OWNER_BLOBS)
    if ai_bot_file is not None:
        expected_blobs[BOT] = AI_BOT_BLOB
    for name, expected in expected_blobs.items():
        raw = (ai_bot_file if name == BOT and ai_bot_file is not None else source_dir / name).read_bytes()
        observed = git_blob_sha(raw)
        if observed != expected:
            raise ValueError(f"{name}: pinned owner blob drift {observed}, expected {expected}")
        texts[name] = raw.decode("utf-8")
    if ai_bot_file is not None:
        # Never regress #484's real AI duel by selecting old #482 BotActors.
        if texts[BOT].count("for targetId,targetActor in pairs(bots)") != 1:
            raise ValueError("RED: current #484 bot-to-bot duel missing or ambiguous")
        if texts[BOT].count("targetHumanoid:TakeDamage(BOT_HERO_DAMAGE)") != 1:
            raise ValueError("RED: #484 bot-to-bot actual damage missing")
        if texts[BOT].count("tryHeroAttack(actor,me,session,lastHit,bots)") != 1:
            raise ValueError("RED: #484 new function signature not correctly wired")
    host, bot = compose(texts[HOST], texts[BOT])
    out_dir.mkdir(parents=True, exist_ok=True)
    result = {}
    for name, updated in ((HOST, host), (BOT, bot)):
        data = updated.encode("utf-8")
        (out_dir / name).write_bytes(data)
        result[name] = {
            "owner_blob": expected_blobs[name],
            "overlay_blob": git_blob_sha(data),
            "sha256": hashlib.sha256(data).hexdigest(),
            "bytes": len(data),
            "changed_lines": 8 if name == HOST else 3,
        }
    report = {
        "owner_head": OWNER_HEAD,
        "selected_ai_author_head": AI_AUTHOR_HEAD if ai_bot_file is not None else None,
        "ai_duel_preserved": ai_bot_file is not None,
        "official_rc_changed": False,
        "original_game_sources_changed": False,
        "new_runtime_authority": False,
        "real_roblox_engine_test": "NOT_RUN",
        "source_files": result,
    }
    (out_dir / "overlay_source_lock.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-dir", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--ai-bot-file", type=Path, default=None)
    args = parser.parse_args()
    print(json.dumps(run(args.source_dir, args.out_dir, args.ai_bot_file), ensure_ascii=False))
