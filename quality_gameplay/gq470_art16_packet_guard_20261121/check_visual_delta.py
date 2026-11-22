#!/usr/bin/env python3
"""Source-only change-line attack surface fence for GQ470 ART16.

Not a game semantics / Roblox Studio / FPS / beauty proof. Checks *added* text
inside previously verified ART16 selected Luaus for newly introduced API
surfaces inappropriate in original cosmetic-only modifications. Existing
original code is not falsely flagged merely because it contains these strings.
"""
from __future__ import annotations
import argparse
import difflib
import json
from pathlib import Path
import re

from verify_packet import locate, normalized_selected, verify

PATTERNS = {
    "data_store": re.compile(r"\bDataStoreService\b"),
    "marketplace_purchase": re.compile(r"\bMarketplaceService\b"),
    "external_http": re.compile(r"\bHttpService\b"),
    "asset_insertion": re.compile(r"\bInsertService\b"),
    "game_teleport": re.compile(r"\bTeleportService\b"),
    "new_network_authority": re.compile(
        r"Instance\s*\.\s*new\s*\(\s*['\"]Remote(?:Event|Function)['\"]"),
    "client_server_fire": re.compile(r":\s*FireServer\s*\("),
    "dynamic_exec": re.compile(r"\b(?:loadstring|getfenv|setfenv)\s*\("),
    "player_kick": re.compile(r":\s*Kick\s*\("),
    "server_damage": re.compile(r":\s*TakeDamage\s*\("),
}
# Source mention counts are risk *indicators*, never rendered part count or FPS.
VISUAL_RISK_PATTERNS = {
    "new_basepart_constructors": re.compile(r"Instance\s*\.\s*new\s*\(\s*['\"](?:Part|WedgePart|MeshPart|UnionOperation)['\"]"),
    "new_neon_material_mentions": re.compile(r"\bEnum\s*\.\s*Material\s*\.\s*Neon\b"),
    "new_billboardgui_mentions": re.compile(r"['\"]BillboardGui['\"]"),
    "new_always_on_top_true": re.compile(r"\bAlwaysOnTop\s*=\s*true\b"),
    "new_frame_hook_mentions": re.compile(r"\b(?:RenderStepped|Heartbeat|Stepped)\b"),
    "new_particle_emitter_mentions": re.compile(r"['\"]ParticleEmitter['\"]"),
    "new_tween_service_mentions": re.compile(r"\bTweenService\b"),
}
MODES = ("insert","replace")

def added_lines(before: str, after: str) -> list[str]:
    a=before.splitlines()
    b=after.splitlines()
    d=difflib.SequenceMatcher(None,a,b,autojunk=False)
    lines=[]
    for tag,a0,a1,b0,b1 in d.get_opcodes():
        if tag in MODES:
            lines.extend(b[b0:b1])
    return lines

def check(before: str, after: str) -> tuple[list[str], list[str]]:
    new=added_lines(before,after)
    offenders=[]
    for line in new:
        without_inline_comment=line.split("--",1)[0]
        for name,rx in PATTERNS.items():
            if rx.search(without_inline_comment):
                offenders.append(name)
    return new,offenders

def selftest() -> list[str]:
    original='local p=game:GetService("MarketplaceService")\nlocal ready=true'
    # An original blocked string remains allowed if unmodified.
    new,off=check(original,original+"\nlocal cosmetic=Instance.new('WedgePart')")
    assert len(new)==1 and off==[]
    tests=[
        ("data_store",'local r=game:GetService("DataStoreService")'),
        ("marketplace_purchase",'local r=game:GetService("MarketplaceService")'),
        ("external_http",'local r=game:GetService("HttpService")'),
        ("asset_insertion",'local r=game:GetService("InsertService")'),
        ("game_teleport",'local r=game:GetService("TeleportService")'),
        ("new_network_authority",'local e=Instance.new("RemoteEvent")'),
        ("client_server_fire",'Remote:FireServer(user_input)'),
        ("dynamic_exec",'local f=loadstring("x")'),
        ("player_kick",'player:Kick("bad")'),
        ("server_damage",'human:TakeDamage(50)'),
    ]
    names=[]
    for expected,text in tests:
        _,bad=check(original,original+"\n"+text)
        if expected not in bad:
            raise AssertionError("RED_ART16_VISUAL_DELTA_MUTANT_NOT_REJECTED_"+expected)
        names.append(expected)
    # A commented-out prohibited API must not be an executed new operation.
    _,notbad=check(original,original+'\n-- game:GetService("DataStoreService")')
    assert notbad==[]
    print("ART16_VISUAL_DELTA_10_AUTHORITY_SERVICE_NEGATIVES_PASS")
    return names

def audit(formal: Path, artifact: Path) -> dict:
    candidate,packet=locate(artifact)
    # Independent package hash/class proof must PASS before any semantic scan.
    verified=verify(formal,candidate,packet)
    a,_=normalized_selected(formal)
    b,_=normalized_selected(candidate)
    changed=sorted(route for route in a if a[route]!=b[route])
    assert len(changed)==16
    stats=[]
    seen=0
    findings=[]
    visual_risk_counts={key:0 for key in VISUAL_RISK_PATTERNS}
    for route in changed:
        added,off=check(a[route].decode("utf-8"), b[route].decode("utf-8"))
        seen+=len(added)
        route_risks={key:sum(bool(pattern.search(line.split("--",1)[0])) for line in added)
                     for key,pattern in VISUAL_RISK_PATTERNS.items()}
        for key,value in route_risks.items():
            visual_risk_counts[key]+=value
        stats.append({"route":route,"added_or_replaced_source_lines":len(added),
                      "visual_source_risk_indicators":route_risks})
        findings.extend({"route":route,"reason":name} for name in off)
    if findings:
        raise ValueError("RED_GQ470_ART16_NEW_FORBIDDEN_API_IN_VISUAL_DELTA:"+json.dumps(findings))
    return {
        "schema":"GQ470_ART16_NEW_SERVICE_REMOTE_AUTHORITY_FENCE_V1",
        "formal_head":verified["canonical_formal_head"],
        "a_candidate_sha":verified["candidate_a_head"],
        "a_candidate_real_place_sha":verified["candidate_private_place_sha256"],
        "actual_checked_changed_source_routes":len(changed),
        "actual_original_exact_unchanged_sources":verified["preserved_exact_sources"],
        "source_delta_insert_or_replace_lines":seen,
        "source_visual_risk_indicators_not_draw_calls":visual_risk_counts,
        "source_visual_risk_limitation":"Added source mentions only; not instantiated Part count, 3D quality, duration, Android frame time or visual score",
        "new_forbidden_api_surfaces":len(findings),
        "source_scope_result":"PASS_STATIC_API_SURFACE_ONLY",
        "limitations":"Not semantic authority or run-time call graph; look at game/Studio separately",
        "art_gate":"ART_NO_GO",
        "formal_rc_adopted":False,"studio":"NOT_TESTED","android":"NOT_TESTED",
        "mutants_rejected":selftest(),
        "route_details":stats
    }

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--formal",type=Path)
    p.add_argument("--artifact",type=Path)
    p.add_argument("--out",type=Path)
    p.add_argument("--self-test",action="store_true")
    a=p.parse_args()
    if a.self_test:
        selftest()
    else:
        if not all((a.formal,a.artifact,a.out)):p.error("--formal --artifact --out required")
        result=audit(a.formal,a.artifact)
        a.out.parent.mkdir(parents=True,exist_ok=True)
        a.out.write_text(json.dumps(result,ensure_ascii=False,sort_keys=True,indent=2)+"\n",encoding="utf-8")
        print("ART16_16_REAL_CHANGED_SCRIPTS_NO_NEW_BANNED_SERVICE_OR_REMOTE_API",
              result["source_delta_insert_or_replace_lines"])
