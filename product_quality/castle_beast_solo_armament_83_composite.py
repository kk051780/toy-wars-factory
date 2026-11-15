#!/usr/bin/env python3
"""#470 FB020-A: source-exact combine castle gate + real Beast + SoloTeamBots + 7 weapons.

Actual native 82-script castle candidate is the only parent, then import the
existing #471 SevenJobArmamentM1 ModuleScript and Game-authority patch. NOT a
new Game/Remote/Store authority, and never writes official RC/main.
"""
from __future__ import annotations
import argparse,copy,hashlib,json,sys
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
from xml.etree import ElementTree as ET
from role7_respawn_guard import extract,verify,blob

sys.path.insert(0,str(Path(__file__).parent/"role7_armament_m1"))
from build_arsenal import patch_game

PARENT_PLACE="P0D_CASTLE_WALKIN_SIEGE_GATE_BEAST_SOLO_PRIVATE_RC82.rbxlx"
PARENT_SHA="c0c74efab8b63716a7b4cef1f8884b4270309c659478e194e1ecf3b8421111a4"
PARENT_MAP="52e677d208412483b744c7ac464eb0ffbc9e6ecd"
PARENT_GAME="d704792acbc8f7cf0568ed612b97c53a3cd7a22b"
PARENT_BOTS="a77176fdcfe3351b5dc9ed4aa23fcf48a28edd53"
MOD_BLOB="7468f143ef801ebc7bdeab75f13bb5b16f66b103"
RC="d2f3ed1a47558fdaf07be0181c83c698bdb2ce34"
OUTPUT_PLACE="P0D_CASTLE_BEAST_SOLO_SEVEN_WEAPONS_PRIVATE_RC83.rbxlx"
GAME="server/Game.server.luau"
MODULE="server/SevenJobArmamentM1.luau"

EXPECTED_PLACE_SHA="c342010e40208df4411831acb01c9e429c4fe7d100fdd953b1d342882cfc92c3"
EXPECTED_BYTES=803551
EXPECTED_GAME_BLOB="8a15f03ea45e4cf6512b09430e3f5dca6d0e1893"

def sha(data):return hashlib.sha256(data).hexdigest()

def original_egg_game(s):
    first='for _, team in ipairs({"RED", "BLUE"}) do\n    map.teams[team].eggPrompt.Triggered:Connect'
    last='\n-- P0D_SAVED_PVE_MASTERY_V1:'
    i=s.index(first);return s[i:s.index(last,i)]

def add_module(root,module_source):
    # The existing original author's SevenJobsRules ModuleScript owns its
    # correct ReplicatedStorage/ServerScriptService class and folder structure.
    # Clone only that script's shell: source, name and referent are unique.
    target=None
    owner=None
    for parent in root.iter():
        for item in parent.findall("Item"):
            prop=item.find("Properties")
            if prop is None:continue
            name=prop.findtext("string[@name='Name']")
            if name=="SevenJobsRules":
                if target is not None:raise ValueError("DUPLICATE_SEVEN_JOBS_SHELL")
                target=item;owner=parent
            if name=="SevenJobArmamentM1":
                raise ValueError("ARMAMENT_MODULE_ALREADY_PRESENT")
    if target is None or owner is None or target.get("class")!="ModuleScript":
        raise ValueError("ORIGINAL_SEVEN_JOB_MODULE_MISSING")
    item=copy.deepcopy(target)
    used={int(i.attrib['referent']) for i in root.iter("Item")
          if i.attrib.get("referent","").isdigit()}
    newref=max(used)+1
    while newref in used:newref+=1
    item.set("referent",str(newref))
    p=item.find("Properties")
    p.find("string[@name='Name']").text="SevenJobArmamentM1"
    p.find("string[@name='Source']").text=module_source
    owner.append(item)

def build(parent,out,extract_dir=None):
    with ZipFile(parent) as z:
        names=z.namelist()
        if len(names)!=len(set(names)) or any(n.startswith("/") or ".." in Path(n).parts for n in names):
            raise ValueError("UNSAFE_SOURCE_ARCHIVE")
        raw=z.read(PARENT_PLACE)
        lock=json.loads(z.read("SOURCE_LOCK.json"))
        feature=json.loads(z.read("RC_FEATURE_LOCK.json"))
        receipt=json.loads(z.read("RECEIPT.json"))
    if sha(raw)!=PARENT_SHA or receipt.get("official_rc_head")!=RC or receipt.get("official_rc_write") is not False:
        raise ValueError("PARENT_RC_OR_SOURCE_NOT_PINNED")
    if lock["blobs"].get("server/MapBuilder.luau")!=PARENT_MAP or lock["blobs"].get(GAME)!=PARENT_GAME or lock["blobs"].get("server/SoloTeamBots.luau")!=PARENT_BOTS:
        raise ValueError("REAL_CASTLE_BEAST_SOLO_PARENT_SOURCE_CHANGED")
    original=verify(raw,lock,feature)
    if len(original)!=82:raise ValueError("REQUIRE_ORIGINAL_82")
    module=(Path(__file__).parent/"role7_armament_m1"/"SevenJobArmamentM1.luau").read_text(encoding="utf-8")
    if blob(module)!=MOD_BLOB:raise ValueError("ORIGINAL_ARMAMENT_MODULE_DRIFT")
    old_game=original["Game"].text
    new_game=patch_game(old_game)
    if original_egg_game(old_game)!=original_egg_game(new_game):
        raise ValueError("ORIGINAL_EGG_SCORES_OR_WINNER_CHANGED")
    for proof in (
        "summonSevenBeast", "privateSoloBotsTrialAllowed()",
        "pcall(SoloTeamBots.start,map,getTeamName(player),botAuthority)",
        "SoloTeamBots.tryHumanHit(team,root.Position,look",
        "horde:tick(now,eligibleSoloPlayers(),healthy)",
        "sevenJobPickAckSeq[player]~=selectedAck",
        "player.Character~=castCharacter",
        "P0D_SAFE_LOBBY","personalEggDeposits[player]=(personalEggDeposits[player] or 0)+1",
        'else "EGG_CAPTURE")',
        'SevenJobs.ArmamentM1.equip(player.Character,job)',
        'SevenJobs.ArmamentM1.strike(job,stage,root.Position,look,'
    ):
        if proof not in new_game:raise ValueError("ORIGINAL_GAMEPLAY_LOST:"+proof)
    for keyword in ("local function resetRound()","local function tickRound()",
                    "local function applyAttack(","local botAuthority="):
        if new_game.count(keyword)!=1:raise ValueError("SECOND_GAME_AUTHORITY:"+keyword)
    root,nodes=extract(raw)
    nodes["Game"].text=new_game
    add_module(root,module)
    final=ET.tostring(root,encoding="utf-8")
    tree,after=extract(final)
    if len(after)!=83 or set(after)-set(original)!={"SevenJobArmamentM1"}:
        raise ValueError("SOURCE_COUNT_OR_NEW_MODULE_DRIFT")
    for name in original:
        if name!="Game" and original[name].text!=after[name].text:
            raise ValueError("ORIGINAL_81_SCRIPT_CHANGED:"+name)
    if after["SevenJobArmamentM1"].text!=module:
        raise ValueError("SEVEN_JOB_WEAPON_MODULE_CHANGED")
    if EXPECTED_PLACE_SHA and (sha(final)!=EXPECTED_PLACE_SHA or len(final)!=EXPECTED_BYTES or blob(new_game)!=EXPECTED_GAME_BLOB):
        raise ValueError("COMPOSITE_PRIVATE83_SHA_BYTES_OR_GAME_DRIFT")
    lock["blobs"][GAME]=feature["source_gitblobs"][GAME]=blob(new_game)
    lock["blobs"][MODULE]=feature["source_gitblobs"][MODULE]=MOD_BLOB
    lock["total_scripts"]=83
    feature["total_sources"]=83
    # The legacy role7_respawn_guard.verify intentionally enforces EXACTLY 82.
    # This one-time real new ModuleScript requires a strict *83*-source lock.
    from collections import Counter
    if lock.get("total_scripts")!=83 or feature.get("total_sources")!=83:
        raise ValueError("NEW_83_SCRIPT_COUNT_LOCK_DRIFT")
    if lock.get("blobs")!=feature.get("source_gitblobs") or len(lock["blobs"])!=83:
        raise ValueError("NEW_83_DUAL_SOURCE_LOCK_DRIFT")
    if Counter(blob(n.text) for n in after.values())!=Counter(lock["blobs"].values()):
        raise ValueError("NEW_83_GAME_SOURCE_BLOB_DRIFT")
    if len({name for name in after})!=83 or after["SevenJobArmamentM1"].text!=module:
        raise ValueError("NEW_83_MODULE_IDENTITY_DRIFT")
    report={"schema":"P0D_FB020_CASTLE_BEAST_SOLO_ALL_SEVEN_WEAPONS_REAL83",
        "official_rc_head":RC,"official_rc_write":False,
        "source_parent_sha256":PARENT_SHA,"place_sha256":sha(final),
        "place_bytes":len(final),"game_blob":blob(new_game),
        "weapon_module_blob":MOD_BLOB,"source_count":83,
        "existing_81_sources_byte_exact":True,
        "egg_score_winner_byte_exact":True,
        "source_lock_path_and_class_exact":True,
        "real_siege_gate_preserved":True,"real_beast_follow_attack_preserved":True,
        "private_solo_egg_ai_preserved":True,
        "seven_welded_weapons":True,"seven_distinct_server_m1":True,
        "native":"NOT_RUN","rojo":"NOT_RUN","studio":"NOT_RUN","android":"NOT_RUN",
        "owner":False,"product":"NO_GO"}
    with ZipFile(out,"w",ZIP_DEFLATED) as z:
        z.writestr(OUTPUT_PLACE,final)
        z.writestr("SOURCE_LOCK.json",json.dumps(lock,indent=2,ensure_ascii=False)+"\n")
        z.writestr("RC_FEATURE_LOCK.json",json.dumps(feature,indent=2,ensure_ascii=False)+"\n")
        z.writestr("RECEIPT.json",json.dumps(report,indent=2,ensure_ascii=False)+"\n")
    if extract_dir:
        extract_dir.mkdir(parents=True,exist_ok=True)
        for name,node in after.items():
            (extract_dir/(name+".luau")).write_text(node.text,encoding="utf-8")
    return report

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--parent",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--extract",type=Path)
    args=p.parse_args()
    print(json.dumps(build(args.parent,args.out,args.extract),ensure_ascii=False,indent=2))
