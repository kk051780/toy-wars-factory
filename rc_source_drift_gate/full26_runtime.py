"""Scope: read-only Studio-only guard inspection across 26 *selected owner* scripts.

Not another composer, source lineage verification, gameplay engine, test bot,
or official RC writer. The real #484 26-source composer owns source bytes.
This inspects author/ART/SCORE/quality originals selected by that composer,
with generated host guard attested in its unchanged prefix only.
"""
from __future__ import annotations
import hashlib
from runtime_activation import guard_lines

GAME = "handoffs/P0D-PQG-SEVEN-HERO-PLAYABLE-20261116/"
ART = "handoffs/EGGRUMBLE-ART-SILHOUETTE-FIELD-20261116/"
ART_SCRIPT_FILES = {
    "EGGRUMBLE_HeroSilhouetteArt": "EGGRUMBLE_HeroSilhouetteArt.server.luau",
    "EGGRUMBLE_FlagshipFieldArt": "EGGRUMBLE_FlagshipFieldArt.server.luau",
    "EGGRUMBLE_EncounterReadabilityArt": "EGGRUMBLE_EncounterReadabilityArt.server.luau",
    "EGGRUMBLE_ArtDistanceLOD": "EGGRUMBLE_ArtDistanceLOD.client.luau",
}
# Trace only: a runtime guard in one optional ART script should not be
# misreported as 8 missing authoritative gameplay sources.
SCRIPT_DOMAIN_HINTS = {
    "EGGRUMBLE_CastleMatchRules": ("castle_egg","balance"),
    "EGGRUMBLE_BotPathRouter": ("field","castle_egg","item","neutral"),
    "EGGRUMBLE_SwarmCombat": ("neutral","battle","balance"),
    "EGGRUMBLE_InteractionGuard": ("castle_egg","item","battle"),
    "EGGRUMBLE_CombatBalance": ("balance","battle","character"),
    "EGGRUMBLE_SkillFX": ("character","battle"),
    "EGGRUMBLE_ImpactFeedback": ("battle","character"),
    "EGGRUMBLE_WeaponSilhouettes": ("character","battle"),
    "EGGRUMBLE_DivineMantle": ("character","battle"),
    "EGGRUMBLE_FieldItemPickups": ("field","item","balance"),
    "EGGRUMBLE_RaidItemIntake": ("item","castle_egg","balance"),
    "EGGRUMBLE_NeutralStoneGiant": ("neutral","battle","field"),
    "EGGRUMBLE_BossSessionFence": ("neutral","battle"),
    "EGGRUMBLE_AttackGeometry": ("battle","field"),
    "EGGRUMBLE_ProceduralSkills": ("character","battle"),
    "EGGRUMBLE_CombatFeel": ("battle","character"),
    "EGGRUMBLE_ScoreBalance": ("balance","castle_egg","neutral"),
    "EGGRUMBLE_HeroSilhouetteArt": ("character","battle"),
    "EGGRUMBLE_FlagshipFieldArt": ("field","castle_egg","lobby"),
    "EGGRUMBLE_EncounterReadabilityArt": ("battle","neutral","item","castle_egg"),
    "EGGRUMBLE_ArtDistanceLOD": ("character","field","battle","castle_egg","neutral","item","lobby"),
}
ALL_DOMAINS = ("character","field","battle","castle_egg","neutral","item","lobby","balance")


def select_all26_runtime_sources(prs, author_project, composer_text,
                                 project_nodes, choose_five, read_pinned):
    """Read selected immutable 21+4+1 files without writing any real source."""
    src, origins = choose_five(prs, author_project, composer_text, read_pinned)
    mapped = project_nodes(author_project)
    if len(mapped) != 21:
        raise ValueError("author_is_not_21_sources")
    for name, node in mapped.items():
        if name in src:
            continue
        owner = "quality" if name == "EGGRUMBLE_BotPathRouter" else "author"
        sha = prs[owner]["head"]["sha"]
        body = read_pinned(node["path"], sha)
        if not isinstance(body, str) or not body.strip():
            raise ValueError("missing_selected_game_source:" + name)
        src[name] = body
        origins[name] = {"selected_owner":owner,"selected_commit":sha,
                         "evidence_region":"COMPOSER_SELECTED_OWNER_FILE",
                         "path":node["path"]}
    for name,filename in ART_SCRIPT_FILES.items():
        if name in src:
            raise ValueError("duplicate_game_art_source:" + name)
        sha = prs["art"]["head"]["sha"]
        path=ART+filename
        body=read_pinned(path,sha)
        if not isinstance(body,str) or not body.strip():
            raise ValueError("missing_selected_art_source:" + name)
        src[name]=body
        origins[name]={"selected_owner":"art","selected_commit":sha,
                       "evidence_region":"COMPOSER_SELECTED_ART_FILE","path":path}
    name="EGGRUMBLE_ScoreBalance"
    if name in src:
        raise ValueError("duplicate_score_source")
    sha=prs["score"]["head"]["sha"]
    path=GAME+name+".luau"
    body=read_pinned(path,sha)
    if not isinstance(body,str) or not body.strip():
        raise ValueError("missing_selected_score_source")
    src[name]=body
    origins[name]={"selected_owner":"score","selected_commit":sha,
                   "evidence_region":"COMPOSER_SELECTED_SCORE_FILE","path":path}
    if len(src)!=26 or len(origins)!=26:
        raise ValueError("effective_selected_script_count_not_26")
    return src, origins


def inspect_full26_runtime(sources, origins):
    """Surface actionable per-domain game vs visual activation risk only."""
    if len(sources)!=26 or len(origins)!=26 or set(sources)!=set(origins):
        raise ValueError("incomplete_current26_source_selection")
    # The base host means all real gameplay modes are disabled nonStudio.
    from runtime_activation import REQUIRED_RUNTIME_SOURCES
    guarded=[]
    per_domain={x:{"game_guard_count":0,"art_guard_count":0} for x in ALL_DOMAINS}
    for name,body in sorted(sources.items()):
        origin=origins[name]
        is_art=origin["selected_owner"]=="art"
        domains=tuple(REQUIRED_RUNTIME_SOURCES.get(name, SCRIPT_DOMAIN_HINTS.get(name, ())))
        if not domains:
            # A new unknown script cannot inherit a false production PASS.
            raise ValueError("unclassified_runtime_source:"+name)
        for item in guard_lines(body):
            event={
                "name":name,
                "owner":origin["selected_owner"],
                "source_commit":origin["selected_commit"],
                "selected_path":origin["path"],
                "line":item["line"],
                "guard_kind":item["kind"],
                "source_sha256":hashlib.sha256(body.encode("utf-8")).hexdigest(),
                "affected_domains":domains,
                "evidence_region":origin["evidence_region"],
            }
            guarded.append(event)
            for domain in domains:
                bucket="art_guard_count" if is_art else "game_guard_count"
                per_domain[domain][bucket]+=1
    host = [e for e in guarded if e["name"]=="EGGRUMBLE_LobbyCastleModesPreview"
            and e["guard_kind"]=="STUDIO_ONLY_EARLY_RETURN"]
    return {
        "schema":"P0D_GQ_SELECTED_26_RUNTIME_GUARDS_V1",
        "selected_script_count":len(sources),
        "generated_host_byte_identity":"NOT_ATTESTED_BY_THIS_GATE_USE_491",
        "source_selector":"CURRENT26_482_QUALITY484_ART485_SCORE487",
        "static_source_read":"PASS",
        "gameplay_server_activation": (
            "BLOCKED_PREVIEW_HOST" if host else
            "NOT_VERIFIED_REQUIRES_REAL_NONSTUDIO_2CLIENT"),
        "art_nonstudio_visual_activation": (
            "STUDIO_ONLY_VISUALS_DETECTED"
            if any(x["owner"]=="art" for x in guarded)
            else "NOT_VERIFIED_REQUIRES_ANDROID_VISUAL_QA"),
        "guard_count":len(guarded),
        "game_guard_count":sum(x["owner"]!="art" for x in guarded),
        "art_guard_count":sum(x["owner"]=="art" for x in guarded),
        "per_domain":per_domain,
        "guards":guarded,
        "product_go":False,
        "owner_next":"#482+existing production host author: single authority adapter; #485 ART nonStudio acceptance; #220 sole CAS",
    }
