#!/usr/bin/env python3
"""GQ8 REAL65: keep *official* Real63 basic attack+dodge while adopting #840/#841.
This is a fail-closed merge of pinned author work, not another Combat owner.
"""
from __future__ import annotations
import argparse,hashlib,json,subprocess,tempfile
from pathlib import Path
from compose_real63 import (
    from_xml,flatten,put_project,receipt_verify,sha,HOST,COMBAT,INVUL,
    VIRAL,COUNTER,CLASS_SUFFIX
)
OFFICIAL63="ad602cebafc1a9d8caed078ab86c7a58b0fbbbef"
BASIC=("ServerScriptService","EGGRUMBLE_BasicMobilityPolicy")
HUD63=("StarterPlayer","StarterPlayerScripts","EGGRUMBLE_HudIntelRuntime")
def require(ok,label):
    if not ok: raise ValueError("RED_REAL65_"+label)
def safe_merge(ours:bytes,base:bytes,theirs:bytes)->bytes:
    # Git's three-way merge applies disjoint author edits; any conflict is fatal.
    with tempfile.TemporaryDirectory() as d:
        paths=[Path(d)/x for x in ("ours","base","theirs")]
        for path,body in zip(paths,(ours,base,theirs)):path.write_bytes(body)
        r=subprocess.run(["git","merge-file","-p",*(str(p) for p in paths)],
                         stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        require(r.returncode==0,"COMBAT_THREE_WAY_CONFLICT")
        require(b"<<<<<<<" not in r.stdout and b">>>>>>>" not in r.stdout,
                "COMBAT_CONFLICT_MARKER")
        return r.stdout

def run(a):
    # Existing verified composite has 64 sources from official62 + two authors.
    real64_doc,real64=flatten(a.real64)
    real64_receipt=json.loads(a.real64_receipt.read_text(encoding="utf8"))
    require(len(real64)==64,"AUTHOR64_COUNT")
    require(real64_receipt["selected_real_sources"]==64 and
            real64_receipt["official_base_head"]==
            "b15db4b9ad1f1f4c1f02fb0976eb3c2f6db8a6ff","AUTHOR64_PROVENANCE")
    receipt_verify(real64,real64_receipt["sources"],"AUTHOR64")
    original62=from_xml(a.real62_place)
    require(len(original62)==62,"REAL62_COUNT")
    # The true current canonical Real63, not an inferred or historical private place.
    official63=from_xml(a.real63_place)
    receipt=json.loads(a.real63_receipt.read_text(encoding="utf8"))
    print("GQ8_OFFICIAL63_RECEIPT_FIELDS",
          json.dumps({k:receipt.get(k) for k in
          ("official_rc_adopted","candidate_git_head","candidate_sources",
           "original_unchanged","native","rojo","official_parent_sha",
           "place_sha256")},sort_keys=True))
    require(receipt.get("official_rc_adopted") is True and
            receipt.get("candidate_git_head")==OFFICIAL63 and
            receipt.get("candidate_sources")==63 and
            receipt.get("original_unchanged")==60,"OFFICIAL63_RECEIPT")
    require(sha(a.real63_place.read_bytes())==receipt.get("place_sha256"),
            "OFFICIAL63_PLACE_HASH")
    receipt_verify(official63,receipt["on_sources"],"OFFICIAL63")
    require(len(official63)==63,"OFFICIAL63_COUNT")
    require(set(official63)-set(original62)=={BASIC} and
            not (set(original62)-set(official63)),"OFFICIAL63_ROUTE_DELTA")
    require(official63[BASIC][0]=="ModuleScript" and
            official63[HOST][0]=="Script","BASIC_OR_HOST_CLASS")
    changed={k for k in original62 if official63[k]!=original62[k]}
    require(changed=={COMBAT,HUD63},"OFFICIAL63_ONLY_COMBAT_HUD_MODIFIED")
    require(set(real64)-set(original62)==VIRAL|COUNTER,"AUTHOR64_ONLY_TWO_NEW_ROUTES")
    changed64={k for k in original62 if real64[k]!=original62[k]}
    require(changed64=={HOST,COMBAT,INVUL},"AUTHOR64_ONLY_THREE_OWNER_PATCHES")
    require(real64[HOST][0]=="Script" and
            real64[COMBAT][0]=="ModuleScript","SINGLE_OWNER_CLASSES")
    # Merge old Combat->Counter delta onto new formal63 Combat; never discard
    # owner-authored normal attack, dodge, Tool cleanup or touch UI.
    merged_combat=safe_merge(
        official63[COMBAT][1],original62[COMBAT][1],real64[COMBAT][1])
    original_basic=official63[COMBAT][1]
    basic_markers=[
        b'EGGRUMBLE_BASIC_ATTACK',b'EGGRUMBLE_DODGE_STEP',
        b'executeCoreAction(session,p,role,action,core)',
        b'EGGRUMBLE_BasicMobilityPolicy'
    ]
    for marker in basic_markers:
        require(merged_combat.count(marker)==original_basic.count(marker)
                and merged_combat.count(marker)>0,
                "BASIC_DODGE_LOST_"+marker.decode("utf8"))
    def damage_sites(b):
        return sum(line.split(b"--",1)[0].count(b":TakeDamage(")
                   for line in b.splitlines())
    require(damage_sites(merged_combat)==damage_sites(original_basic),
            "SECOND_DAMAGE_OWNER")
    require(merged_combat!=original_basic and
            merged_combat!=real64[COMBAT][1],"COUNTER_OR_DODGE_NOT_COMPOSED")
    chosen=dict(official63)
    chosen[HOST]=real64[HOST]
    chosen[COMBAT]=(official63[COMBAT][0],merged_combat)
    chosen[INVUL]=real64[INVUL]
    for k in VIRAL|COUNTER:
        require(k not in chosen,"NEW_ROUTE_ALREADY_OWNED")
        chosen[k]=real64[k]
    require(len(chosen)==65,"FINAL65_COUNT")
    unchanged={k for k in official63 if chosen[k]==official63[k]}
    require(len(unchanged)==60,"FORMAL63_ORIGINAL60_NOT_PRESERVED")
    for k in (BASIC,HUD63):
        require(chosen[k]==official63[k],"DODGE_POLICY_OR_TOUCH_HUD_LOST")
    require(sum(k[-1]=="EGGRUMBLE_SevenRoleCombat" for k in chosen)==1,
            "DUPLICATE_COMBAT_OWNER")
    require(sum(k[-1]=="EGGRUMBLE_LobbyCastleModesPreview" for k in chosen)==1,
            "DUPLICATE_HOST_OWNER")
    require(not a.out.exists(),"OUTPUT_EXISTS")
    a.out.mkdir(parents=True)
    on=put_project(real64_doc,chosen,a.out)
    (a.out/"EGGRUMBLE_REAL64.project.json").rename(a.out/"EGGRUMBLE_REAL65.project.json")
    # OFF63 is literally the verified official artifact; no reconstruction guess.
    (a.out/"OFF63_EXACT_OFFICIAL.rbxlx").write_bytes(a.real63_place.read_bytes())
    offdir=a.out/"off63";offdir.mkdir()
    off=put_project(real64_doc,official63,offdir)
    require(len(flatten(off)[1])==63,"OFF63_PROJECT_COUNT")
    report={
        "schema":"GQ8_REAL65_FORMAL63_PLUS_VIRAL_COUNTER_SOURCE_PROOF_V1",
        "official_parent_head":OFFICIAL63,"new_selected_source_count":65,
        "original_real63_source_count":63,"original_real63_byte_unchanged":60,
        "added_exact_routes":["/".join(k) for k in sorted(VIRAL|COUNTER)],
        "patched_existing_routes":["/".join(k) for k in (HOST,COMBAT,INVUL)],
        "preserves_real63_basic_attack":True,"preserves_real63_dodge":True,
        "preserves_real63_hud":True,"host_class":"Script",
        "owner_game":1,"owner_combat":1,"owner_swarm":1,
        "new_damage_sites":0,"new_store_writers":0,"new_remotes":0,
        "real_paid_trade":False,"roblox_publish":False,
        "native":"PENDING","rojo":"PENDING","formal_rc_adopted":False,
        "studio_2client":"NOT_TESTED","android_15min":"NOT_TESTED",
        "visual_art":"NO_GO","fun":"NO_GO",
        "rollback":"OFF63_EXACT_OFFICIAL.rbxlx literal byte-exact official REAL63 Place",
        "formal63_place_sha256":sha(a.real63_place.read_bytes()),
        "sources":[{"route":"/".join(k),"class":v[0],
                    "sha256":sha(v[1]),"bytes":len(v[1])}
                   for k,v in sorted(chosen.items())],
    }
    (a.out/"REAL65_INTAKE_RECEIPT.json").write_text(
        json.dumps(report,ensure_ascii=False,indent=2,sort_keys=True)+"\n",
        encoding="utf8")
    print("GQ8_REAL65_FORMAL63_BASIC_DODGE_PRESERVED_AND_COUNTER_VIRAL_COMPOSED")
if __name__=="__main__":
    p=argparse.ArgumentParser()
    for name in ("real64","real64_receipt","real62_place",
                 "real63_place","real63_receipt","out"):
        p.add_argument("--"+name.replace("_","-"),required=True,type=Path)
    run(p.parse_args())
