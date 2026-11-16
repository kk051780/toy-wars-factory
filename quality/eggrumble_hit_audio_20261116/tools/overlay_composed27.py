#!/usr/bin/env python3
"""Non-authoring sound-only overlay onto the original 27-source GQ composite.

No gameplay, AI, art, score, compass or original-author code is written.
"""
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path

CLIENT_NAME = "EGGRUMBLE_RealHitAudio"
CLIENTS_27 = {
    "EGGRUMBLE_CombatFeel", "EGGRUMBLE_ProceduralSkills",
    "EGGRUMBLE_ArtDistanceLOD", "EGGRUMBLE_GQ_ObjectiveCompass",
}
SERVERS_REQUIRED = {
    "EGGRUMBLE_LobbyCastleModesPreview", "EGGRUMBLE_SevenRoleCombat",
    "EGGRUMBLE_BotActors", "EGGRUMBLE_BotPathRouter",
    "EGGRUMBLE_CastleMatchRules", "EGGRUMBLE_SwarmCombat",
    "EGGRUMBLE_FieldItemPickups", "EGGRUMBLE_RaidItemIntake",
    "EGGRUMBLE_NeutralStoneGiant", "EGGRUMBLE_BossSessionFence",
    "EGGRUMBLE_MatchResultService", "EGGRUMBLE_ScoreBalance",
    "EGGRUMBLE_FlagshipFieldArt", "EGGRUMBLE_HeroSilhouetteArt",
}

def flatten(node, parent=()):
    out = {}
    for name, value in node.items():
        if name.startswith("$") or not isinstance(value, dict):
            continue
        label = parent + (name,)
        if "$path" in value:
            if set(value) != {"$path"} or label in out:
                raise ValueError(("unsafe project mapping", label))
            out[label] = value["$path"]
        else:
            sub = flatten(value, label)
            if out.keys() & sub.keys():
                raise ValueError("duplicate project path")
            out.update(sub)
    return out

def compose(base_project, base_receipt, script, out):
    project = Path(base_project).resolve(strict=True)
    receipt_file = Path(base_receipt).resolve(strict=True)
    script = Path(script).resolve(strict=True)
    out = Path(out).resolve()
    if out.parent != project.parent or out == project:
        raise ValueError("overlay must not rewrite 27-source source project")
    base = json.loads(project.read_text(encoding="utf-8"))
    receipt = json.loads(receipt_file.read_text(encoding="utf-8"))
    if receipt.get("status") != "SOURCE_ONLY_NOT_OFFICIAL_RC":
        raise ValueError("refuse non-preview authority")
    if receipt.get("total_sources") != 27 or receipt.get("original_26_sources_preserved") is not True:
        raise ValueError("source baseline must be original author+AI+ART+SCORE+compass 27")
    if receipt.get("overlay_name") != "EGGRUMBLE_GQ_ObjectiveCompass":
        raise ValueError("wrong 27th source")
    entries = flatten(base["tree"])
    names = [parts[-1] for parts in entries]
    if len(entries) != 27 or len(set(names)) != 27 or CLIENT_NAME in names:
        raise ValueError("duplicate or incomplete 27 source project")
    original_clients = base["tree"]["StarterPlayer"]["StarterPlayerScripts"]
    original_servers = base["tree"]["ServerScriptService"]
    if set(original_clients) - {"$className"} != CLIENTS_27:
        raise ValueError("mismatched original client source set")
    if not SERVERS_REQUIRED.issubset(set(original_servers) - {"$className"}):
        raise ValueError("castle/hero/field/AI/neutral/item/lobby/score/art missing")
    for key, relative in entries.items():
        src = (project.parent / relative).resolve(strict=True)
        if not src.is_file() or not src.name.endswith(".luau"):
            raise ValueError(("missing Luau", key))
    # Verify original 27th source is exactly the source hashed by its author.
    objective = next((project.parent / p).resolve(strict=True)
                     for key, p in entries.items()
                     if key[-1] == "EGGRUMBLE_GQ_ObjectiveCompass")
    if hashlib.sha256(objective.read_bytes()).hexdigest() != receipt.get("overlay_sha256"):
        raise ValueError("objective author source drift")
    if script.name != "EGGRUMBLE_RealHitAudio.client.luau":
        raise ValueError("unapproved sound overlay")
    body = script.read_text(encoding="utf-8")
    for necessary in ("RunService:IsStudio()", "EGGRUMBLE_ImpactSequence",
                      "EGGRUMBLE_SFXMuted", "MAX_VOICES=4"):
        if necessary not in body:
            raise ValueError(("invalid sound-only script", necessary))
    for forbidden in ("FireServer(", "TakeDamage(", "SetAttribute(", "DataStoreService",
                      "Instance.new(\"RemoteEvent\")"):
        if forbidden in body:
            raise ValueError(("sound script gameplay authority", forbidden))
    output = copy.deepcopy(base)
    output["name"] = "EGGRUMBLE_V3_AUTHOR_ART_SCORE_OBJECTIVE_AUDIO28_SOURCE_ONLY"
    output["tree"]["StarterPlayer"]["StarterPlayerScripts"][CLIENT_NAME] = {
        "$path": os.path.relpath(script, out.parent).replace(os.sep, "/")
    }
    actual = flatten(output["tree"])
    new_name = ("StarterPlayer", "StarterPlayerScripts", CLIENT_NAME)
    if len(actual) != 28 or set(actual) - set(entries) != {new_name}:
        raise ValueError("wrong 28-source overlay")
    if any(actual[key] != old for key, old in entries.items()):
        raise ValueError("original 27 paths modified")
    out.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    manifest = {
        "status": "SOURCE_ONLY_NOT_OFFICIAL_RC",
        "base_27_project_sha256": hashlib.sha256(project.read_bytes()).hexdigest(),
        "base_27_receipt_sha256": hashlib.sha256(receipt_file.read_bytes()).hexdigest(),
        "original_27_sources_preserved": True,
        "server_scripts": 23, "original_clients": 4,
        "audio_client_added": CLIENT_NAME, "script_count": 28,
        "audio_source_sha256": hashlib.sha256(script.read_bytes()).hexdigest(),
        "official_rc_integrated": False, "studio": "NOT_RUN",
        "android": "NOT_RUN", "fun": "NO_GO", "owner_accepted": False,
    }
    (out.parent / "GQ_OBJECTIVE_AUDIO_28_RECEIPT.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("GQ_REUSE_27_PLUS_AUDIO28_PASS")
    return manifest

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-project", required=True)
    ap.add_argument("--base-receipt", required=True)
    ap.add_argument("--audio-script", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    compose(a.base_project, a.base_receipt, a.audio_script, a.out)
