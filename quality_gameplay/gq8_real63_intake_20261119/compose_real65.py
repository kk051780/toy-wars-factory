#!/usr/bin/env python3
"""GQ8 REAL65: keep *official* Real63 basic attack+dodge while adopting #840/#841.
This is a fail-closed merge of pinned author work, not another Combat owner.
"""
from __future__ import annotations
import argparse,copy,hashlib,json,subprocess,tempfile
from pathlib import Path
from compose_real63 import (
    from_xml,flatten,put_project,receipt_verify,sha,HOST,COMBAT,INVUL,
    VIRAL,COUNTER,CLASS_SUFFIX
)
OFFICIAL63="d52f2060dda81f0af6d1b143eee25fb416141602"
BASIC=("ServerScriptService","EGGRUMBLE_BasicMobilityPolicy")
HUD63=("StarterPlayer","StarterPlayerScripts","EGGRUMBLE_HudIntelRuntime")
VIEW63=("ReplicatedStorage","EGGRUMBLE_HudPresentationPolicy")
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

def fix_viral_capture_callback_scope(author_host:bytes)->bytes:
    """Fix author #840's Luau lexical forward-scope bug without a second Host.

    The egg deposit/steal callbacks are declared inside createWorldCastle BEFORE
    'local function gq8CaptureHint'; Luau binds those earlier references to the
    absent GLOBAL, so successful egg actions error before session.refresh().
    Reposition the exact author block ahead of the existing function. No other
    source edits, Remote, combat authority, or gameplay policy changes.
    """
    start=b"-- No extra gameplay owner: only this existing HOST emits factual capture hints.\n"
    stop=b"\nlocal function startSession(mode:string)"
    before=b"local function createWorldCastle(session:any,entry:any,index:number)"
    require(author_host.count(start)==1 and author_host.count(stop)==1
            and author_host.count(before)==1,"VIRAL_SCOPE_ANCHORS")
    first=author_host.index(start)
    last=author_host.index(stop,first)
    block=author_host[first:last]
    require(block.count(b"local function gq8CaptureHint(")==1
            and block.count(b"local gq8ViralEpoch=0")==1
            and author_host.count(b"gq8CaptureHint(p,session,")==2,
            "VIRAL_SCOPE_AUTHOR_SHAPE")
    require(author_host.index(b"gq8CaptureHint(p,session,")<first,
            "VIRAL_SCOPE_BUG_NOT_PRESENT_STOP_REPATCH")
    without=author_host[:first]+author_host[last:]
    pos=without.index(before)
    fixed=without[:pos]+block+b"\n"+without[pos:]
    require(fixed.count(b"local function gq8CaptureHint(")==1
            and fixed.index(b"local function gq8CaptureHint(")<
                fixed.index(b"gq8CaptureHint(p,session,")
            and fixed.count(b"gq8CaptureHint(p,session,")==2,
            "VIRAL_SCOPE_FORWARD_BINDING_NOT_FIXED")
    return fixed

def add_fb014_firstplay(host:bytes)->bytes:
    """One local first-play path sign; preserve the single Host and 65 routes."""
    anchor=b"-- GQ646_LOBBY_SAFE_SPAWN_END\n"
    marker=b"GQ8_FB014_FIRSTPLAY_GUIDE_BEGIN"
    require(host.count(anchor)==1,"FB014_SAFE_SPAWN_ANCHOR_DRIFT")
    require(host.count(marker)==0,"FB014_ALREADY_PRESENT")
    guide="-- GQ8_FB014_FIRSTPLAY_GUIDE_BEGIN: lobby-only, no HUD/Remote/queue owner.\nlocal fb014Anchor=Instance.new(\"Part\")\nfb014Anchor.Name=\"GQ8_FB014_FIRSTPLAY_ANCHOR\"\nfb014Anchor.Anchored=true\nfb014Anchor.CanCollide=false\nfb014Anchor.CanTouch=false\nfb014Anchor.CanQuery=false\nfb014Anchor.Transparency=1\nfb014Anchor.Size=Vector3.new(2,2,1)\nfb014Anchor.Position=root+Vector3.new(0,4,-15)\nfb014Anchor.Parent=folder\nlocal fb014Gui=Instance.new(\"BillboardGui\")\nfb014Gui.Name=\"GQ8_FB014_FIRSTPLAY_SIGN\"\nfb014Gui.Size=UDim2.fromOffset(288,92)\nfb014Gui.StudsOffsetWorldSpace=Vector3.new(0,1.8,0)\nfb014Gui.AlwaysOnTop=false\nfb014Gui.MaxDistance=44\nfb014Gui.Parent=fb014Anchor\nlocal fb014Text=Instance.new(\"TextLabel\")\nfb014Text.Name=\"Instructions\"\nfb014Text.Size=UDim2.fromScale(1,1)\nfb014Text.BackgroundColor3=Color3.fromRGB(30,37,51)\nfb014Text.BackgroundTransparency=.18\nfb014Text.BorderSizePixel=0\nfb014Text.Font=Enum.Font.GothamBold\nfb014Text.TextColor3=Color3.fromRGB(245,248,235)\nfb014Text.TextSize=17\nfb014Text.TextWrapped=true\nfb014Text.Text=\"はじめての出撃\\n① 奥の職業台で役職選択\\n② 戻ってTEAM／BRゲートで出撃\"\nfb014Text.Parent=fb014Gui\n-- GQ8_FB014_FIRSTPLAY_GUIDE_END\n"
    updated=host.replace(anchor,anchor+guide.encode("utf8"),1)
    require(updated.count(b"GQ8_FB014_FIRSTPLAY_SIGN")==1 and
            updated.count(b'fb014Gui.MaxDistance=44')==1 and
            updated.count(b'fb014Anchor.CanCollide=false')==1 and
            updated.count(b'fb014Text.Text="')==1 and
            updated.count(anchor)==1,"FB014_SELECTED_SOURCE_MUTATION")
    return updated

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
            receipt.get("original_unchanged")==59,"OFFICIAL63_RECEIPT")
    require(sha(a.real63_place.read_bytes())==receipt.get("place_sha256"),
            "OFFICIAL63_PLACE_HASH")
    receipt_verify(official63,receipt["on_sources"],"OFFICIAL63")
    require(len(official63)==63,"OFFICIAL63_COUNT")
    require(set(official63)-set(original62)=={BASIC} and
            not (set(original62)-set(official63)),"OFFICIAL63_ROUTE_DELTA")
    require(official63[BASIC][0]=="ModuleScript" and
            official63[HOST][0]=="Script","BASIC_OR_HOST_CLASS")
    changed={k for k in original62 if official63[k]!=original62[k]}
    require(changed=={COMBAT,HUD63,VIEW63},"OFFICIAL63_COMBAT_HUD_PRESENTATION_EXACT")
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
    # Original #848 inter-round session-identity correction must survive the counter merge.
    basic_markers.append(b"matchEpoch=tostring(session),mode=session.mode")
    require(b"matchEpoch=tostring(session.world)" not in merged_combat,
            "STALE_ROUND_EPOCH_REINTRODUCED")
    for marker in basic_markers:
        require(merged_combat.count(marker)==original_basic.count(marker)
                and merged_combat.count(marker)>0,
                "BASIC_DODGE_LOST_"+marker.decode("utf8"))
    def damage_sites(b):
        return sum(line.split(b"--",1)[0].count(b":TakeDamage(")
                   for line in b.splitlines())
    print("GQ8_COMBAT_DAMAGE_SITES",json.dumps({
        "formal62":damage_sites(original62[COMBAT][1]),
        "formal63":damage_sites(original_basic),
        "counter_author64":damage_sites(real64[COMBAT][1]),
        "merged65":damage_sites(merged_combat)},sort_keys=True))
    # #841 adds exactly one authorized counter-reflect damage application in
    # the SAME original Combat owner. Compare to its pinned original author,
    # not the older three-site baseline; reject any accidental duplicate.
    require(damage_sites(original62[COMBAT][1])==damage_sites(original_basic)
            and damage_sites(real64[COMBAT][1])==damage_sites(original_basic)+1
            and damage_sites(merged_combat)==damage_sites(real64[COMBAT][1]),
            "COUNTER_REFLECT_DAMAGE_SITE_DRIFT")
    require(merged_combat!=original_basic and
            merged_combat!=real64[COMBAT][1],"COUNTER_OR_DODGE_NOT_COMPOSED")
    chosen=dict(official63)
    fixed_host=fix_viral_capture_callback_scope(real64[HOST][1])
    chosen[HOST]=(real64[HOST][0],add_fb014_firstplay(fixed_host))
    chosen[COMBAT]=(official63[COMBAT][0],merged_combat)
    chosen[INVUL]=real64[INVUL]
    for k in VIRAL|COUNTER:
        require(k not in chosen,"NEW_ROUTE_ALREADY_OWNED")
        chosen[k]=real64[k]
    # GQ8 unique startup fix: both showroom Scripts must wait for the *Host-owned*
    # safe spawn. Studio starts independent ServerScripts in unspecified order.
    SHOP=("ServerScriptService","GQ805_LobbyGuildShop")
    PLAZA=("ServerScriptService","GQ8_LobbySocialPlaza")
    def patch_spawn(route,old,new):
        cls,body=chosen[route]
        require(cls=="Script" and body.count(old)==1,
                "LOBBY_BOOTSTRAP_EXPECTED_ORIGINAL_"+route[-1])
        chosen[route]=(cls,body.replace(old,new,1))
    patch_spawn(SHOP,
        b'local spawn=workspace:FindFirstChildWhichIsA("SpawnLocation",true)\n'
        b'local origin=spawn and spawn.Position or Vector3.new(0,4,0)',
        b'local canonical=workspace:WaitForChild("EGGRUMBLE_LOBBY_CASTLE_MODES_PREVIEW",60)\n'
        b'if not canonical then warn("[GQ805 SHOP] canonical lobby missing: skip") return end\n'
        b'local spawn=canonical:WaitForChild("GQ646_LOBBY_NEUTRAL_SPAWN",30)\n'
        b'if not spawn or not spawn:IsA("SpawnLocation") then warn("[GQ805 SHOP] canonical spawn missing: skip") return end\n'
        b'local origin=spawn.Position')
    patch_spawn(PLAZA,
        b'local spawn = workspace:FindFirstChildWhichIsA("SpawnLocation", true)\n'
        b'if not spawn then warn("[GQ8 SOCIAL] no safe SpawnLocation: skip") return end',
        b'local canonical = workspace:WaitForChild("EGGRUMBLE_LOBBY_CASTLE_MODES_PREVIEW",60)\n'
        b'if not canonical then warn("[GQ8 SOCIAL] canonical lobby missing: skip") return end\n'
        b'local spawn = canonical:WaitForChild("GQ646_LOBBY_NEUTRAL_SPAWN",30)\n'
        b'if not spawn or not spawn:IsA("SpawnLocation") then warn("[GQ8 SOCIAL] canonical spawn missing: skip") return end')
    # Evidence: the selected physical Place must contain exactly these guards,
    # not merely a source-only flag or a fallback to arbitrary map spawns.
    for route in (SHOP,PLAZA):
        source=chosen[route][1]
        require(source.count(b'canonical:WaitForChild("GQ646_LOBBY_NEUTRAL_SPAWN",30)')==1
                and b'FindFirstChildWhichIsA("SpawnLocation"' not in source,
                "LOBBY_STARTUP_RACE_FENCE_NOT_IN_SELECTED_SOURCE")
    require(chosen[HOST][1].count(b"GQ8_FB014_FIRSTPLAY_GUIDE_BEGIN")==1, "FB014_NOT_IN_FINAL_HOST")
    require(len(chosen)==65,"FINAL65_COUNT")
    unchanged={k for k in official63 if chosen[k]==official63[k]}
    require(len(unchanged)==58,"FORMAL63_ORIGINAL58_NOT_PRESERVED")
    for k in (BASIC,HUD63,VIEW63):
        require(chosen[k]==official63[k],"DODGE_POLICY_OR_TOUCH_HUD_LOST")
    require(sum(k[-1]=="EGGRUMBLE_SevenRoleCombat" for k in chosen)==1,
            "DUPLICATE_COMBAT_OWNER")
    require(sum(k[-1]=="EGGRUMBLE_LobbyCastleModesPreview" for k in chosen)==1,
            "DUPLICATE_HOST_OWNER")
    require(not a.out.exists(),"OUTPUT_EXISTS")
    a.out.mkdir(parents=True)
    on=put_project(real64_doc,chosen,a.out)
    (a.out/"EGGRUMBLE_REAL64.project.json").rename(a.out/"EGGRUMBLE_REAL65.project.json")
    # The original multi-lane helper builds a REAL64-named project by design.
    # This selected REAL65 Place must identify itself correctly in Studio.
    # Change only the project metadata, never any original game script bytes.
    selected_project=a.out/"EGGRUMBLE_REAL65.project.json"
    spec=json.loads(selected_project.read_text(encoding="utf8"))
    require(spec.get("name")=="GQ8_REAL64_COMBINED_PRIVATE_NOT_PUBLISHED",
            "STUDIO_PROJECT_EXPECTED_PARENT_NAME")
    spec["name"]="EGGRUMBLE_REAL65_PRIVATE_STUDIO"
    selected_project.write_text(json.dumps(spec,ensure_ascii=False,indent=2,sort_keys=True)+"\n",
                                encoding="utf8")
    require(flatten(selected_project)[1]==chosen and
            json.loads(selected_project.read_text(encoding="utf8"))["name"]==
            "EGGRUMBLE_REAL65_PRIVATE_STUDIO",
            "STUDIO_PROJECT_METADATA_ONLY")
    # OFF63 is literally the verified official artifact; no reconstruction guess.
    (a.out/"OFF63_EXACT_OFFICIAL.rbxlx").write_bytes(a.real63_place.read_bytes())
    offdir=a.out/"off63";offdir.mkdir()
    # Source template from author64 still contains VIRAL+COUNTER $path entries.
    # Remove *only* those two routes from OFF63 to make its rollback a true
    # 63-source profile, not a missing-file or phantom-source projection.
    offdoc=copy.deepcopy(real64_doc)
    for route in VIRAL|COUNTER:
        node=offdoc["tree"]
        for segment in route[:-1]:node=node[segment]
        require(route[-1] in node,"OFF63_AUTHOR_ROUTE_MISSING")
        del node[route[-1]]
    off=put_project(offdoc,official63,offdir)
    require(len(flatten(off)[1])==63,"OFF63_PROJECT_COUNT")
    report={
        "schema":"GQ8_REAL65_FORMAL63_PLUS_VIRAL_COUNTER_SOURCE_PROOF_V1",
        "official_parent_head":OFFICIAL63,"new_selected_source_count":65,
        "original_real63_source_count":63,"original_real63_byte_unchanged":58,
        "official63_parent_original62_unchanged":59,
        "added_exact_routes":["/".join(k) for k in sorted(VIRAL|COUNTER)],
        "patched_existing_routes":["/".join(k) for k in (HOST,COMBAT,INVUL,SHOP,PLAZA)],
        "lobby_spawn_order_race_fenced":True,
        "preserves_real63_basic_attack":True,"preserves_real63_dodge":True,
        "preserves_real63_hud":True,"preserves_real63_presentation":True,
        "preserves_real63_round_epoch":True,"host_class":"Script",
        "viral_egg_callback_forward_scope_fixed":True,
        "viral_author64_host_sha256":sha(real64[HOST][1]),
        "viral_fixed_host_sha256":sha(fixed_host),
        "owner_game":1,"owner_combat":1,"owner_swarm":1,
        "new_damage_sites":1,"counter_reflect_damage_owner":"EXISTING_SINGLE_COMBAT",
        "new_store_writers":0,"new_remotes":0,
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
