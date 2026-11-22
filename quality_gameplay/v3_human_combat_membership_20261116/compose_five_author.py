#!/usr/bin/env python3
"""SOURCE-EXACT private composition: #482 + #510/#516/#524/#529 Combat + #531 Host/Bot + #535 gate.

No source owner, official RC, main, Studio, publish or paid resources are changed.
Run only in throwaway CI workspace after git-fetch of all fixed author commits.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET

from compose import AUTHOR_HEAD, AUTHOR_BLOB, COMBAT_NAME, git_blob, patch, undo

ROOT = Path("handoffs/P0D-PQG-SEVEN-HERO-PLAYABLE-20261116")
PROJECT = "EGGRUMBLE_V3_STUDIO.project.json"
AUTHORS = {
    "gq_mage": "0338bd13f9d3d199972bd4cd30e467443083dffa",
    "gq_dot": "8f0275692c54874f823d66748d470fb849607df5",
    "gq_warp": "f90875e14446ba86b1c668ba43efa37fbc74be20",
    "gq_stealth": "99ae00fbec2b5057c54e938d741ea99b0caad924",
    "gq_bot_member": "e78bff41e70564d0b26578e3c3a85f4698e6110e",
    "gq_ai_duel": "6b52eaf1f2725496277998fe0c5532b7a8fcaab5",
}
SELECT = {
    "_gq_mage/quality_gameplay/v3_mage_heal_los_20261116/build_candidate.py":
        ("gq_mage", "quality_gameplay/v3_mage_heal_los_20261116/build_candidate.py"),
    "_gq_dot/quality_gameplay/v3_status_tick_fence_20261116/tools/compose_with_mage_author.py":
        ("gq_dot", "quality_gameplay/v3_status_tick_fence_20261116/tools/compose_with_mage_author.py"),
    "_gq_dot/quality_gameplay/v3_status_tick_fence_20261116/EGGRUMBLE_SevenRoleCombat.patched.luau":
        ("gq_dot", "quality_gameplay/v3_status_tick_fence_20261116/EGGRUMBLE_SevenRoleCombat.patched.luau"),
    "_gq_dot/quality_gameplay/v3_status_tick_fence_20261116/EGGRUMBLE_StatusTickFence.luau":
        ("gq_dot", "quality_gameplay/v3_status_tick_fence_20261116/EGGRUMBLE_StatusTickFence.luau"),
    "_gq_warp/quality_gameplay/v3_safe_warp_landing_20261116/patch_safe_warp.py":
        ("gq_warp", "quality_gameplay/v3_safe_warp_landing_20261116/patch_safe_warp.py"),
    "quality_gameplay/v3_human_stealth_pvp_20261116/build_candidate.py":
        ("gq_stealth", "quality_gameplay/v3_human_stealth_pvp_20261116/build_candidate.py"),
    "quality_gameplay/v3_human_stealth_pvp_20261116/compose_four_author.py":
        ("gq_stealth", "quality_gameplay/v3_human_stealth_pvp_20261116/compose_four_author.py"),
}
STATUS_NAME = "EGGRUMBLE_StatusTickFence"
HOST_NAME = "EGGRUMBLE_LobbyCastleModesPreview.server.luau"
BOT_NAME = "EGGRUMBLE_BotActors.luau"
ROUTER_NAME = "EGGRUMBLE_BotPathRouter.luau"
PINNED_AI_HOST_SOURCE_BLOB = "c1ff23cd2883401d44d6fc47311bebcfd53eb1c6"
PINNED_AI_BOT_SOURCE_BLOB = "832a26c9f713012b924234ce4cf8c1654a75654e"
PINNED_AI_ROUTER_SOURCE_BLOB = "d9841bb874659129cae6c930bce302ff6936ac4a"

def git_show(sha: str, path: str) -> bytes:
    return subprocess.check_output(["git", "show", f"{sha}:{path}"])

def materialize(path: Path, data: bytes):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)

def script_paths(project: dict) -> dict:
    mapping = {}
    def walk(node: dict):
        for name, child in node.items():
            if name.startswith("$") or not isinstance(child, dict):
                continue
            if "$path" in child:
                rel = child["$path"]
                if "/" in rel or "\\" in rel or not rel.endswith(".luau"):
                    raise RuntimeError("RED unexpected original project script path")
                if name in mapping:
                    raise RuntimeError("RED duplicate original script name")
                mapping[name] = rel
            else:
                walk(child)
    walk(project["tree"])
    return mapping

def build(out: Path) -> dict:
    project_bytes = git_show(AUTHOR_HEAD, str(ROOT / PROJECT))
    project = json.loads(project_bytes)
    original_files=script_paths(project)
    if len(original_files)!=21 or COMBAT_NAME not in original_files.values():
        raise RuntimeError("RED not original 21 source project")
    for rel in original_files.values():
        raw=git_show(AUTHOR_HEAD,str(ROOT / rel))
        materialize(ROOT / rel,raw)
        if rel == COMBAT_NAME and git_blob(raw)!=AUTHOR_BLOB:
            raise RuntimeError("RED original Combat SHA drift")
    materialize(ROOT / PROJECT,project_bytes)
    for pref in ("_gq_mage","_gq_dot","_gq_warp"):
        materialize(Path(pref) / ROOT / COMBAT_NAME,(ROOT / COMBAT_NAME).read_bytes())
    for dest,(owner,src) in SELECT.items():
        materialize(Path(dest),git_show(AUTHORS[owner],src))
    # Reuse the current #531 author overlay verbatim, selecting its #484 AI-duel
    # BotActors, not an older #482 BotActors. No second Host/AI authority.
    member_tool = Path("_gq_bot_member/compose.py")
    materialize(member_tool,git_show(AUTHORS["gq_bot_member"],
        "quality_gameplay/v3_bot_human_match_membership_20261116/compose.py"))
    ai_bot_file=Path("_gq_bot_member/EGGRUMBLE_BotActors.luau")
    materialize(ai_bot_file,git_show(AUTHORS["gq_ai_duel"],str(ROOT / BOT_NAME)))
    if git_blob(ai_bot_file.read_bytes())!=PINNED_AI_BOT_SOURCE_BLOB:
        raise RuntimeError("RED #484 bot duel original source changed")
    router_source=git_show(AUTHORS["gq_ai_duel"],str(ROOT / ROUTER_NAME))
    if git_blob(router_source)!=PINNED_AI_ROUTER_SOURCE_BLOB:
        raise RuntimeError("RED #484 real bot path router source changed")
    # Source-select the genuine current #484 navigation author, not the
    # incompatible prior #482 route. Do not invent a second navigator.
    materialize(out/ROUTER_NAME,router_source)
    spec_member=importlib.util.spec_from_file_location("gq_real_531",member_tool.resolve())
    if not spec_member or not spec_member.loader:
        raise RuntimeError("RED missing existing #531 composer")
    member_module=importlib.util.module_from_spec(spec_member)
    spec_member.loader.exec_module(member_module)
    if member_module.AI_AUTHOR_HEAD!=AUTHORS["gq_ai_duel"] or member_module.AI_BOT_BLOB!=PINNED_AI_BOT_SOURCE_BLOB:
        raise RuntimeError("RED original #531/484 author lock mismatch")
    member_report=member_module.run(ROOT,out,ai_bot_file=ai_bot_file)
    if not member_report["ai_duel_preserved"]:
        raise RuntimeError("RED #531 did not source-select #484 bot AI")
    # The original #484 Host contains traversable castle access ramps and the
    # authoritative AI staging environment. Build #531's one callback against
    # THAT exact parent Host instead of reverting the gameplay world to #482.
    ai_host_bytes=git_show(AUTHORS["gq_ai_duel"],str(ROOT / HOST_NAME))
    if git_blob(ai_host_bytes)!=PINNED_AI_HOST_SOURCE_BLOB:
        raise RuntimeError("RED current #484 Host original source drift")
    ai_host=ai_host_bytes.decode("utf-8")
    if ai_host.count('"CastleAccessRamp"')!=1 or ai_host.count("BotActors.start(session,Rules)")!=1:
        raise RuntimeError("RED #484 castle traversal or AI start contract drift")
    final_host=member_module.replace_exact(ai_host,member_module.HOST_BEFORE,
        member_module.HOST_AFTER,HOST_NAME)
    if final_host.replace(member_module.HOST_AFTER,member_module.HOST_BEFORE,1)!=ai_host:
        raise RuntimeError("RED #531 callback rollback lost #484 Host")
    if final_host.count("session.isCurrentHuman=function")!=1:
        raise RuntimeError("RED #531 host callback missing or duplicated")
    materialize(out / HOST_NAME,final_host.encode("utf-8"))
    member_report["selected_host_author_head"]=AUTHORS["gq_ai_duel"]
    member_report["source_files"][HOST_NAME]={
        "owner_blob": PINNED_AI_HOST_SOURCE_BLOB,
        "overlay_blob": git_blob(final_host.encode("utf-8")),
        "sha256": hashlib.sha256(final_host.encode("utf-8")).hexdigest(),
        "bytes":len(final_host.encode("utf-8")),
        "changed_lines":8,
    }
    (out / "overlay_source_lock.json").write_text(
        json.dumps(member_report,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    # This is the ACTUAL #529 multi-author composer. We do not duplicate its patch logic.
    four_path=Path("quality_gameplay/v3_human_stealth_pvp_20261116/compose_four_author.py")
    spec=importlib.util.spec_from_file_location("gq_real_529",four_path.resolve())
    if not spec or not spec.loader:
        raise RuntimeError("RED #529 composer not importable")
    four_module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(four_module)
    four, heads=four_module.build_union()
    # Our own unique delta is applied LAST; its OFF restores exact existing four-author Combat.
    five=patch(four)
    if undo(five)!=four:
        raise RuntimeError("RED regression to existing #529 multi-author source")
    out.mkdir(parents=True,exist_ok=True)
    if git_blob((out / HOST_NAME).read_bytes())!=member_report["source_files"][HOST_NAME]["overlay_blob"]:
        raise RuntimeError("RED #531 callback changed or #484 Host drift")
    if git_blob((out / BOT_NAME).read_bytes())!=member_report["source_files"][BOT_NAME]["overlay_blob"]:
        raise RuntimeError("RED #531 latest BotActors drift")
    bot=(out / BOT_NAME).read_text()
    router=(out / ROUTER_NAME).read_text()
    if "PathfindingService:CreatePath" not in router or "path:ComputeAsync" not in router:
        raise RuntimeError("RED #484 navigator losing real pathfinder")
    if "local ok=pcall(function()\n   path=PathfindingService:CreatePath" not in router:
        raise RuntimeError("RED #484 CreatePath fault recovery lost")
    if bot.count("targetHumanoid:TakeDamage(BOT_HERO_DAMAGE)")!=1 or bot.count("for targetId,targetActor in pairs(bots)")!=1:
        raise RuntimeError("RED latest #484 real bot-to-bot duel disappeared")
    if bot.count("session.isCurrentHuman(player)")!=1:
        raise RuntimeError("RED missing one bot-to-human session member fence")
    if five.count("currentHumanMember(session,")!=4 or five.count("humanCombatTargetable(")!=3:
        raise RuntimeError("RED human stealth or current-member gates lost")
    if five.count("StatusTickFence.canTick(")!=1:
        raise RuntimeError("RED #516 DOT fence lost")
    if five.count("safeMove(session,char,root,")!=2:
        raise RuntimeError("RED #524 warp fence lost")
    if five.count("botHum.Health=math.min(botHum.MaxHealth,botHum.Health+25)")!=1:
        raise RuntimeError("RED #510 MAGE teammate heal lost")
    (out / COMBAT_NAME).write_bytes(five.encode("utf-8"))
    (out / (STATUS_NAME+".luau")).write_bytes(
        Path("_gq_dot/quality_gameplay/v3_status_tick_fence_20261116/EGGRUMBLE_StatusTickFence.luau").read_bytes())
    output_project=json.loads((out / PROJECT).read_text())
    server=output_project["tree"]["ServerScriptService"]
    if STATUS_NAME in server:
        raise RuntimeError("RED duplicate status module")
    server[STATUS_NAME]={"$path":STATUS_NAME+".luau"}
    output_project["name"]="EGGRUMBLE_GQ_5_AUTHOR_COMBAT_AND_BOT_MEMBER_PRIVATE22_NOT_RC"
    (out / PROJECT).write_text(json.dumps(output_project,ensure_ascii=False,indent=2)+"\n")
    result={
        "state":"PRIVATE22_NOT_FORMAL_RC",
        "owner_original_sha":AUTHOR_HEAD,
        "author_head_locks":AUTHORS,
        "four_combat_529_sha256":hashlib.sha256(four.encode()).hexdigest(),
        "five_combat_535_sha256":hashlib.sha256(five.encode()).hexdigest(),
        "sources_expected":22,
        "original_script_sources_unmodified":17,
        "updated_existing_host_bot_combat_router":4,
        "added_existing_status_module":1,
        "original_host_bot_owner":AUTHORS["gq_bot_member"],
        "bot_ai_author_sha":AUTHORS["gq_ai_duel"],
        "original_484_host_castle_ramp_preserved":True,
        "original_484_host_author_blob":PINNED_AI_HOST_SOURCE_BLOB,
        "single_host_callback_531":True,
        "bot_ai_duel_real_damage_preserved":True,
        "bot_ai_pathfinder_source_preserved":True,
        "bot_ai_router_blob":PINNED_AI_ROUTER_SOURCE_BLOB,
        "bot_ai_router_last_stud_ray_defect_from_gq536":"YELLOW_EXISTING_AUTHOR_536_PENDING",
        "bot_human_current_match_predicate_preserved":True,
        "no_duplicate_game_or_combat":True,
        "rollback_535": "undo Combat patch restores #529 composed Combat exactly",
        "official_rc_adopted":False,
        "source_sha256":{p:hashlib.sha256((out/p).read_bytes()).hexdigest()
                         for p in script_paths(output_project).values()},
    }
    (out / "GQ_FIVE_AUTHOR_PRIVATE22_RECEIPT.json").write_text(
        json.dumps(result,indent=2,ensure_ascii=False)+"\n")
    print("GQ_535_FOUR_COMBAT_529_PLUS_531_HOST_BOT_SOURCE_COMPOSE_PASS",len(five))
    return result

def verify(out:Path,place:Path):
    project=json.loads((out/PROJECT).read_text())
    source=script_paths(project)
    if len(source)!=22:
        raise RuntimeError("RED source count not 22")
    expected={}
    for name,rel in source.items():
        kind = "LocalScript" if rel.endswith(".client.luau") else "Script" if rel.endswith(".server.luau") else "ModuleScript"
        expected[name]=(kind,(out/rel).read_text().replace("\r\n","\n"))
    real={}
    for item in ET.fromstring(place.read_bytes()).iter("Item"):
        kind=item.attrib.get("class")
        if kind not in {"Script","ModuleScript","LocalScript"}: continue
        prop=item.find("Properties")
        if prop is None:continue
        name=prop.findtext("string[@name='Name']")
        data=prop.findtext("ProtectedString[@name='Source']")
        if data is None:data=prop.findtext("string[@name='Source']")
        if name in real or data is None:
            raise RuntimeError(f"RED duplicate/empty script source {name}")
        real[name]=(kind,data.replace("\r\n","\n"))
    if expected!=real:
        raise RuntimeError("RED actual Rojo Place Script Source/Class mismatches original22")
    receiptfile=out/"GQ_FIVE_AUTHOR_PRIVATE22_RECEIPT.json"
    receipt=json.loads(receiptfile.read_text())
    receipt["rojo_source_class_exact_22"]=True
    receipt["private_place_bytes"]=place.stat().st_size
    receipt["private_place_sha256"]=hashlib.sha256(place.read_bytes()).hexdigest()
    receiptfile.write_text(json.dumps(receipt,indent=2,ensure_ascii=False)+"\n")
    print("GQ_FIVE_AUTHOR_PRIVATE22_ACTUAL_PLACE_SOURCE_CLASS_EXACT_PASS",place.stat().st_size)

if __name__=="__main__":
    cli=argparse.ArgumentParser()
    cli.add_argument("mode",choices=["build","verify"])
    cli.add_argument("--out",type=Path,required=True)
    cli.add_argument("--place",type=Path)
    options=cli.parse_args()
    if options.mode=="build":build(options.out)
    else:
        if not options.place:cli.error("--place required")
        verify(options.out,options.place)
