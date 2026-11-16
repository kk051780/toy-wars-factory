#!/usr/bin/env python3
"""P0D GQ8 — independent ACTUAL official RC .rbxlx artifact-to-feature proof.

Read-only. No duplicate author/game implementation. This checks what was built
rather than just the selector's claim. Source/identity gate, NOT Studio gameplay,
Android, ART acceptance or FUN. Fail closed for RC-HEAD drift and false feature
flags. Works on a downloaded official Actions artifact, not a local preview.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

PLACE = "EGGRUMBLE_V3_RC31_CANONICAL_STUDIO.rbxlx"
RECEIPT = "EGGRUMBLE_V3_OFFICIAL_RC31_RECEIPT.json"
N = 31

# A selected original source may own several features. This is a literal
# source-to-artifact contract, NOT a test of engine movement/visual quality.
RULES = {
 "characters": {
  "EGGRUMBLE_SevenRoleCombat": (
    'local ORDER={"WARRIOR","MAGE","NINJA","TRAPPER","BUILDER","BEAST","ZOMBIE"}',
    "local function execute(",
  )},
 "field": {
  "EGGRUMBLE_BotPathRouter": (
    "local ray=workspace:Raycast(at,diff.Unit*diff.Magnitude,p)",
  ),
  "EGGRUMBLE_LobbyCastleModesPreview": (
    "CastleAccessRamp",
    'local rowZ=if mode=="TEAM" then {338,506,610} else {338,448,676}',
  ),
 },
 "battle": {
  "EGGRUMBLE_SevenRoleCombat": (
    "GQ_DEAD_CASTER_FENCE:", "currentHumanMember(session,",
  )},
 "castle": {
  "EGGRUMBLE_LobbyCastleModesPreview": (
    "Rules.depositEggs(", "coreBoard.MaxDistance=65",
    "vaultBoard.MaxDistance=40",
  )},
 "neutral": {
  "EGGRUMBLE_SwarmCombat": (
    "candidate.victim.humanoid:TakeDamage(Melee.DAMAGE)",
    "session.neutralBudget:acquire(",
  )},
 "items": {
  "EGGRUMBLE_FieldItemPickups": (
    'interactionGuard.allow(player,part,"拾う",part.Name)',
    "local function restoreSpeed()",
  )},
 "lobby": {
  "EGGRUMBLE_LobbyCastleModesPreview": (
    'joinQueue("TEAM",p)', 'joinQueue("BATTLE_ROYALE",p)',
    "local function nearbyBoard(", "session.isCurrentHuman=function",
  )},
 "balance": {
  "EGGRUMBLE_CombatBalance": ("return Balance",),
  "EGGRUMBLE_MatchResultService": ("function ResultRetry.deliver(",),
  "EGGRUMBLE_ScoreBalance": (),
 },
}
ROLE_CLASSES = {
 "EGGRUMBLE_LobbyCastleModesPreview": "Script",
 "EGGRUMBLE_SevenRoleCombat": "ModuleScript",
 "EGGRUMBLE_SwarmCombat": "ModuleScript",
 "EGGRUMBLE_BotActors": "ModuleScript",
 "EGGRUMBLE_BotPathRouter": "ModuleScript",
 "EGGRUMBLE_FieldItemPickups": "ModuleScript",
 "EGGRUMBLE_CastleMatchRules": "ModuleScript",
 "EGGRUMBLE_MatchResultService": "ModuleScript",
 "EGGRUMBLE_CombatFeel": "LocalScript",
}
# These 16 are known to be source-selected in the current official V3 branch.
# A future new flag is not silently certified; report it as unassessed.
FEATURE_EVIDENCE = {
 "DEAD_CASTER_FENCE_530": ("EGGRUMBLE_SevenRoleCombat","GQ_DEAD_CASTER_FENCE:"),
 "HUMAN_MATCH_MEMBERSHIP_535": ("EGGRUMBLE_SevenRoleCombat","currentHumanMember(session,"),
 "HUMAN_BOT_MATCH_MEMBERSHIP_531": ("EGGRUMBLE_LobbyCastleModesPreview","session.isCurrentHuman=function"),
 "NEUTRAL_MELEE_533": ("EGGRUMBLE_SwarmCombat","candidate.victim.humanoid:TakeDamage(Melee.DAMAGE)"),
 "SHARED_NEUTRAL_BUDGET_528": ("EGGRUMBLE_SwarmCombat","session.neutralBudget:acquire("),
 "NEUTRAL_NEAREST_ELIGIBLE_FALLBACK_541": ("EGGRUMBLE_SwarmCombat","candidate.victim.humanoid:TakeDamage(Melee.DAMAGE)"),
 "CASTLE_EGG_DEPOSIT_REFRESH_537": ("EGGRUMBLE_LobbyCastleModesPreview","session.refresh()"),
 "ASSASSIN_RESPAWN_STEALTH_FENCE_540": ("EGGRUMBLE_LobbyCastleModesPreview","EGGRUMBLE_StealthUntil"),
 "LOBBY_NEARBY_BOARDS_539": ("EGGRUMBLE_LobbyCastleModesPreview","gui.MaxDistance=math.clamp(maxDistance,16,52)"),
 "ORIGINAL_ITEM_AUTHOR_489": ("EGGRUMBLE_FieldItemPickups",'interactionGuard.allow(player,part,"拾う",part.Name)'),
 "BOT_NEAREST_CURRENT_HUMAN_555": ("EGGRUMBLE_BotActors","nearestHumanoid:TakeDamage(BOT_HERO_DAMAGE)"),
 "BOT_ROUTE_FULLSTEP_536": ("EGGRUMBLE_BotPathRouter","local ray=workspace:Raycast(at,diff.Unit*diff.Magnitude,p)"),
 "CASTLE_EGG_BOARD_DISTANCE_547": ("EGGRUMBLE_LobbyCastleModesPreview","coreBoard.MaxDistance=65"),
 "CARRIER_STALE_AVATAR_DIED_FENCE_551": ("EGGRUMBLE_LobbyCastleModesPreview","player.Character~=character"),
 "RESULT_GUI_BOUNDED_RETRY_538": ("EGGRUMBLE_MatchResultService","function ResultRetry.deliver("),
 "FIELD_EGGS_CASTLE_FOUNDATION_CLEARANCE_523": (
   "EGGRUMBLE_LobbyCastleModesPreview",
   'local rowZ=if mode=="TEAM" then {338,506,610} else {338,448,676}'),

}

class RedGate(ValueError):
    pass

def require(condition:bool, reason:str):
    if not condition:
        raise RedGate("RED_GQ8_"+reason)

def source_scripts(place:bytes):
    root=ET.fromstring(place)
    found={}
    for node in root.iter("Item"):
        klass=node.attrib.get("class")
        if klass not in ("Script","LocalScript","ModuleScript"):
            continue
        props=node.find("Properties")
        require(props is not None,"SCRIPT_PROPERTIES")
        name=props.findtext("string[@name='Name']")
        content=props.findtext("ProtectedString[@name='Source']")
        if content is None:
            content=props.findtext("string[@name='Source']")
        require(bool(name) and content is not None,"SCRIPT_NAME_OR_SOURCE")
        require(name not in found,"DUPLICATE_SCRIPT_"+str(name))
        found[name]=(klass,content.replace("\r\n","\n"))
    require(len(found)==N,"SCRIPT_COUNT_31_"+str(len(found)))
    for name,klass in ROLE_CLASSES.items():
        require(name in found and found[name][0]==klass,"ROLE_CLASS_"+name)
    return found

def verify(place:bytes, receipt:dict, manifest:dict, active:dict, expected_head:str,
           allow_pr_premerge:bool=False):
    require(len(expected_head)==40 and all(c in "0123456789abcdef" for c in expected_head),
            "EXPECTED_COMMIT_SHA_INVALID")
    require(manifest["canonical_branch"]=="rc/p0d-s1-kids-rc01","CANONICAL_BRANCH")
    require(manifest["profile"]=="eggrumble_v3_31" and manifest["source_count"]==N,
            "ACTIVE_SOURCE_PROFILE_OR_COUNT")
    require(manifest["enabled"] is True,"V3_COMPANION_NOT_ENABLED")
    require(active["active_profile"]=="rich51","S1_LEGACY_CHANGED_WITHOUT_OWNER")
    require(active["source_profiles"]["eggrumble_v3_31"]["source_count"]==N,
            "S1_RC_PROFILE_NOT_REGISTERED")
    require(receipt.get("canonical_branch")=="rc/p0d-s1-kids-rc01",
            "ARTIFACT_NOT_CANONICAL")
    require(receipt.get("github_commit_sha")==expected_head,"ARTIFACT_STALE_WRONG_HEAD")
    official=receipt.get("official_rc_commit_verified") is True
    if not official:
        require(allow_pr_premerge and
                receipt.get("status")=="RC_PREMERGE_COMPANION_PROFILE_BUILD_PASS_NOT_STUDIO_PLAYTESTED",
                "NOT_OFFICIAL_PUSH")
    else:
        require(receipt.get("status")=="CANONICAL_RC_BRANCH_COMPANION_PROFILE_BUILD_PASS_NOT_STUDIO_PLAYTESTED",
                "OFFICIAL_PUSH_CLAIM_MISMATCH")
    require(receipt.get("release_profile")=="eggrumble_v3_31","ARTIFACT_NOT_V3")
    require(receipt.get("script_count")==N and receipt.get("script_source_and_class_exact")=="31/31",
            "ARTIFACT_SOURCE_RECEIPT_NOT_PASS")
    require(receipt.get("roblox_publish") is False,"UNAUTHORIZED_PUBLISH")
    require(receipt.get("s1_active_profile_unchanged") is True,"S1_MUTATION")
    require(receipt.get("source_author_heads")==manifest.get("source_heads"),
            "AUTHOR_SHA_MANIFEST_ARTIFACT_DRIFT")
    require(receipt.get("place_name")==PLACE,"ARTIFACT_PLACE_NAME")
    require(receipt.get("place_size_bytes")==len(place),"PLACE_BYTES_WRONG")
    placehash=hashlib.sha256(place).hexdigest()
    require(receipt.get("place_sha256")==placehash,"PLACE_SHA256_WRONG")
    scripts=source_scripts(place)
    by_domain={}
    for domain,targets in RULES.items():
        for name,needles in targets.items():
            require(name in scripts,"DOMAIN_"+domain+"_MISSING_"+name)
            for anchor in needles:
                require(anchor in scripts[name][1],"DOMAIN_"+domain+"_MISSING_"+name+"_"+anchor[:24])
        by_domain[domain]="SOURCE_ANCHOR_PRESENT_NOT_STUDIO_VERIFIED"
    flags=manifest.get("feature_flags",{})
    for flag,(script,anchor) in FEATURE_EVIDENCE.items():
        require(flags.get(flag) is True,"FEATURE_FLAG_DISABLED_OR_UNKNOWN_"+flag)
        require(anchor in scripts[script][1],"FEATURE_FALSE_ON_"+flag)
    return {
        "result":("OFFICIAL_SOURCE_ARTIFACT_8_DOMAIN_GATE_PASS_NOT_GAMEPLAY_ACCEPTANCE"
                  if official else "PR_PREMERGE_SOURCE_ARTIFACT_GATE_PASS_NOT_OFFICIAL_RC"),
        "official_rc_push_verified":official,
        "official_rc_head":expected_head,"studio_place_bytes":len(place),
        "studio_place_sha256":placehash,"script_count":len(scripts),
        "domains":by_domain,
        "verified_flag_count":len(FEATURE_EVIDENCE),
        "unassessed_new_flags":sorted(set(flags)-set(FEATURE_EVIDENCE)),
        "legacy_s1_default":"rich51",
        "real_studio_2client":"NOT_TESTED",
        "android_15min":"NOT_TESTED","owner_fun":"NOT_TESTED",
        "roblox_published":False,
    }

def main():
    cli=argparse.ArgumentParser()
    cli.add_argument("--artifact-dir",required=True,type=Path)
    cli.add_argument("--manifest",required=True,type=Path)
    cli.add_argument("--active",required=True,type=Path)
    cli.add_argument("--rc-head",required=True)
    cli.add_argument("--out",required=True,type=Path)
    cli.add_argument("--pr-premerge",action="store_true")
    a=cli.parse_args()
    data=a.artifact_dir.resolve(strict=True)
    place=(data/PLACE).read_bytes()
    receipt=json.loads((data/RECEIPT).read_text(encoding="utf-8"))
    manifest=json.loads(a.manifest.read_text(encoding="utf-8"))
    active=json.loads(a.active.read_text(encoding="utf-8"))
    result=verify(place,receipt,manifest,active,a.rc_head,allow_pr_premerge=a.pr_premerge)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,ensure_ascii=False,indent=2,sort_keys=True)+"\n",
                     encoding="utf-8")
    print("GQ8_OFFICIAL_PLACE_8_DOMAINS_SOURCE_ANCHOR_AND_16_FEATURE_FLAGS_PASS"
          if result["official_rc_push_verified"]
          else "GQ8_PR_PREMERGE_8_DOMAIN_SOURCE_ONLY_PASS_NOT_OFFICIAL_RC")
    print("GQ8_OFFICIAL_RC_SHA_PLACE_BYTES",result["official_rc_head"],
          result["studio_place_bytes"],result["studio_place_sha256"])

if __name__=="__main__":
    main()
