#!/usr/bin/env python3
"""Non-owning GQ overlay: append a single optional LocalScript to the *existing*
author+quality+ART+SCORE 26-source composite. No game source is rewritten.
"""
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path

GAME_HOST = "EGGRUMBLE_LobbyCastleModesPreview"
CLIENT_NAME = "EGGRUMBLE_GQ_ObjectiveCompass"
ITEM_NAME = "EGGRUMBLE_FieldItemPickups"
ITEM_PATH = ("ServerScriptService", ITEM_NAME)
CLIENT_SET = {
    "EGGRUMBLE_CombatFeel", "EGGRUMBLE_ProceduralSkills",
    "EGGRUMBLE_ArtDistanceLOD",
}
ART_SET = {
    "EGGRUMBLE_HeroSilhouetteArt", "EGGRUMBLE_FlagshipFieldArt",
    "EGGRUMBLE_EncounterReadabilityArt",
}
SERVER_REQUIRED = {
    GAME_HOST, "EGGRUMBLE_BotActors", "EGGRUMBLE_BotPathRouter",
    "EGGRUMBLE_CastleMatchRules", "EGGRUMBLE_SevenRoleCombat",
    "EGGRUMBLE_NeutralStoneGiant", "EGGRUMBLE_BossSessionFence",
    "EGGRUMBLE_RaidItemIntake", ITEM_NAME,
    "EGGRUMBLE_InteractionGuard",
    "EGGRUMBLE_MatchResultService", "EGGRUMBLE_ScoreBalance",
    *ART_SET,
}


def flatten(tree, prefix=()):
    result = {}
    for key, child in tree.items():
        if key.startswith("$") or not isinstance(child, dict):
            continue
        path = prefix + (key,)
        if "$path" in child:
            if set(child) != {"$path"} or path in result:
                raise ValueError(("invalid map", path))
            result[path] = child["$path"]
        else:
            result.update(flatten(child, path))
    return result


def compose(base_project, base_receipt, new_script, out, item_source=None, item_sha256=None):
    base_project = Path(base_project).resolve(strict=True)
    base_receipt = Path(base_receipt).resolve(strict=True)
    new_script = Path(new_script).resolve(strict=True)
    out = Path(out).resolve()
    if out.parent != base_project.parent:
        raise ValueError("Use same artifacts folder to preserve all 26 relative paths")
    if base_project == out:
        raise ValueError("Cannot overwrite the original 26-source project")
    receipt = json.loads(base_receipt.read_text(encoding="utf-8"))
    if receipt.get("status") != "SOURCE_ONLY_NOT_OFFICIAL_RC":
        raise ValueError("Not a safe source-only 26-source receipt")
    if receipt.get("script_count") != 26 or len(receipt.get("source_sha256", {})) != 26:
        raise ValueError("Base composite not the 26-source author/ART/SCORE baseline")
    data = json.loads(base_project.read_text(encoding="utf-8"))
    prior = flatten(data["tree"])
    if any(p[-1] == CLIENT_NAME for p in prior):
        raise ValueError("Objective compass already installed")
    if len(prior) != 26 or len({p[-1] for p in prior}) != 26:
        raise ValueError("Source names duplicate or incomplete")
    server = data["tree"]["ServerScriptService"]
    clients = data["tree"]["StarterPlayer"]["StarterPlayerScripts"]
    if server["$className"] != "ServerScriptService" or clients["$className"] != "StarterPlayerScripts":
        raise ValueError("Wrong service mapping")
    if len(server) != 24 or len(clients) != 4:
        raise ValueError("Expected 23 original server and 3 original client sources")
    if not SERVER_REQUIRED.issubset(set(server) - {"$className"}):
        raise ValueError("Original combat, field, castle, boss, item, score or ART missing")
    if set(clients) - {"$className"} != CLIENT_SET:
        raise ValueError("Original playable skills / art client no longer match")
    if GAME_HOST not in server or server[GAME_HOST]["$path"].endswith(".client.luau"):
        raise ValueError("Wrong game host")
    for path, relative in prior.items():
        source = (base_project.parent / relative).resolve(strict=True)
        expected_sha = receipt["source_sha256"].get(path[-1])
        if not expected_sha or hashlib.sha256(source.read_bytes()).hexdigest() != expected_sha:
            raise ValueError(("Underlying author's source changed", path))
    if not new_script.name.endswith(".client.luau"):
        raise ValueError("Overlay must be client-only")
    script_bytes = new_script.read_bytes()
    script_text = script_bytes.decode("utf-8")
    if ("RunService:IsStudio()" not in script_text
            or "EGGRUMBLE_GQ_ObjectiveCompass" not in script_text
            or "FireServer(" in script_text or "Instance.new(\"RemoteEvent\")" in script_text):
        raise ValueError("Unsafe/incorrect client overlay")
    # Source-select the existing ITEM owner's actual file, not a reimplemented item authority.
    # The underlying 26-source author+ART+SCORE receipt is checked *before* this override.
    item_source_bytes = None
    old_item_sha = receipt["source_sha256"][ITEM_NAME]
    if item_source is not None:
        item_source = Path(item_source).resolve(strict=True)
        if (item_source.name != ITEM_NAME + ".luau" or not item_sha256
                or len(item_sha256) != 64):
            raise ValueError("Pinned original ITEM owner SHA256 and name required")
        item_source_bytes = item_source.read_bytes()
        if hashlib.sha256(item_source_bytes).hexdigest() != item_sha256.lower():
            raise ValueError("Item original-owner SHA256 mismatch")
        item_text = item_source_bytes.decode("utf-8")
        if not all(token in item_text for token in (
                "function Items.start(", "carryingEnemyEggs(",
                'interactionGuard.allow(player,part,"拾う",part.Name)',
                "cancelBuffIfCarrier(", "RESPAWN_SECONDS=35")):
            raise ValueError("ITEM candidate violates existing owner fairness/LOS contract")
        if item_sha256 == old_item_sha:
            raise ValueError("Original ITEM author source was not updated")
    elif item_sha256 is not None:
        raise ValueError("SHA256 supplied without authored ITEM source")
    overlay = copy.deepcopy(data)
    if item_source is not None:
        overlay["tree"]["ServerScriptService"][ITEM_NAME] = {
            "$path": os.path.relpath(item_source, out.parent).replace(os.sep, "/")
        }
    overlay["name"] = "EGGRUMBLE_V3_AUTHOR_ART_SCORE_GQ_OBJECTIVE27_PRIVATE"
    overlay["tree"]["StarterPlayer"]["StarterPlayerScripts"][CLIENT_NAME] = {
        "$path": os.path.relpath(new_script, out.parent).replace(os.sep, "/")
    }
    after = flatten(overlay["tree"])
    add = ("StarterPlayer", "StarterPlayerScripts", CLIENT_NAME)
    if len(after) != 27 or set(after) - set(prior) != {add}:
        raise ValueError("Not exactly one new client script")
    for key, old in prior.items():
        if key == ITEM_PATH and item_source is not None:
            if after[key] == old:
                raise ValueError("Original ITEM owner patch not applied")
        elif after[key] != old:
            raise ValueError(("Original mapping rewritten", key))
    out.write_text(json.dumps(overlay, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    new_receipt = {
        "status": "SOURCE_ONLY_NOT_OFFICIAL_RC", "base_26_receipt_sha256":
            hashlib.sha256(base_receipt.read_bytes()).hexdigest(),
        "base_26_project_sha256": hashlib.sha256(base_project.read_bytes()).hexdigest(),
        "original_26_sources_preserved": item_source is None,
        "original_25_source_paths_preserved": item_source is not None,
        "item_source_selectively_replaced": item_source is not None,
        "item_original_sha256": old_item_sha,
        "item_author_sha256": item_sha256 if item_source is not None else old_item_sha,
        "total_sources": 27,
        "server_scripts": 23, "original_client_scripts": 3,
        "new_client_scripts": 1, "overlay_name": CLIENT_NAME,
        "overlay_sha256": hashlib.sha256(script_bytes).hexdigest(),
        "official_rc_integrated": False, "studio": "NOT_TESTED",
        "android": "NOT_TESTED", "art_fun_owner": "NO_GO"
    }
    rpath = out.parent / "GQ_OBJECTIVE_27_RECEIPT.json"
    rpath.write_text(json.dumps(new_receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("GQ_OBJECTIVE_REUSE_26_PLUS_ONE_PASS", len(after))
    return new_receipt


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--base-project", required=True)
    p.add_argument("--base-receipt", required=True)
    p.add_argument("--new-script", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--item-source", default=None)
    p.add_argument("--item-sha256", default=None)
    args = p.parse_args()
    compose(args.base_project, args.base_receipt, args.new_script, args.out,
            item_source=args.item_source, item_sha256=args.item_sha256)


if __name__ == "__main__":
    main()
