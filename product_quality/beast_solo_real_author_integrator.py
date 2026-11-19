#!/usr/bin/env python3
"""#470: original #297 REAL Beast Tamer companion + #471 real private SoloTeamBots.

Three-way selection of actual 82-script Places; never mutates official RC/main.
The exact Game/HUD/SevenJobs original-author and private-Solo AI source is retained.
"""
from __future__ import annotations
import argparse,io,hashlib,json,subprocess,tempfile
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile,ZIP_DEFLATED
from p0d_role7_spectator_solo_batch import locked,blob,sha

RC="d2f3ed1a47558fdaf07be0181c83c698bdb2ce34"
PINS={
 "base":("P0D_ROLE7_ACK_WIND_BUILDER_COMBO_RESPAWN_SPECTATOR_RC82.rbxlx","bbb9c919cb11cfc5147a75a9d8f8e770eb5a7d540acfffeb650010f5710e0d1c"),
 "beast":("P0D_RC82_BEAST_TAMER_REAL_COMPANION_PRIVATE.rbxlx","b64db322c3cafe817fc4c6a9a8d7b4fb51f1cec93f681d6d4f5502c945bf163d"),
 "solo":("P0D_FB005_AI_RAID_RESULT_PRIVATE_RC82.rbxlx","130170d565a9b11851f4742a2a8dd7f6e3e926464aeb12d192cec4715bfb266a"),
}
OUTPUT="P0D_RC82_BEAST_COMPANION_SOLO_AI_CUMULATIVE_PRIVATE.rbxlx"
EXPECTED_PLACE="eb9ccd5bb516328ce61da3b0c82c5dcccdb6cc6ad0e60076d4c9f15db19de1eb"
EXPECTED_BYTES=787836
EXPECTED_GAME="d704792acbc8f7cf0568ed612b97c53a3cd7a22b"
GAME="server/Game.server.luau"
BOTS="server/SoloTeamBots.luau"
LATCH_OLD='studioSoloRoundStarted = StudioSolo.isSoloRound(RunService:IsStudio() or privateHordeTrialAllowed(),\n        #Players:GetPlayers(), teamCount("RED"), teamCount("BLUE"))'
LATCH_NEW=LATCH_OLD.replace('#Players:GetPlayers()','#eligibleSoloPlayers()')
FAIL_OLD='if studioSoloRoundStarted and match.phase=="ACTIVE"\n                    and #Players:GetPlayers()==1 then\n                    stopRound("DRAW","SOLO_BOTS_TICK_FAILURE")'
FAIL_NEW=FAIL_OLD.replace('#Players:GetPlayers()','#eligibleSoloPlayers()')

def load(path,tag):
    with ZipFile(path) as z:
        names=z.namelist()
        if len(names)!=len(set(names)) or any(n.startswith("/") or ".." in Path(n).parts for n in names):
            raise ValueError("UNSAFE_SOURCE_ZIP_"+tag)
        place=z.read(PINS[tag][0])
        lock=json.loads(z.read("SOURCE_LOCK.json"))
        feature=json.loads(z.read("RC_FEATURE_LOCK.json"))
    if sha(place)!=PINS[tag][1]:
        raise ValueError("WRONG_PINNED_PLACE_"+tag)
    root,scripts=locked(place,lock,feature)
    return place,lock,feature,root,scripts

def egg_block(source):
    start='for _, team in ipairs({"RED", "BLUE"}) do\n    map.teams[team].eggPrompt.Triggered:Connect'
    stop='\n-- P0D_SAVED_PVE_MASTERY_V1:'
    i=source.index(start)
    return source[i:source.index(stop,i)]

def merge_game(beast,base,solo):
    with tempfile.TemporaryDirectory() as tmp:
        a,b,c=(Path(tmp)/name for name in ("beast.luau","base.luau","solo.luau"))
        for file,content in ((a,beast),(b,base),(c,solo)):
            file.write_text(content,encoding="utf-8")
        proc=subprocess.run(["git","merge-file","-p",str(a),str(b),str(c)],capture_output=True)
        if proc.returncode!=0 or b"<<<<<<<" in proc.stdout:
            raise ValueError("AUTHOR_AND_QUALITY_GAME_MERGE_CONFLICT")
        game=proc.stdout.decode("utf-8")
    for label,old,new in (("SOLO_ROUND",LATCH_OLD,LATCH_NEW),("BOT_TICK_FAILURE",FAIL_OLD,FAIL_NEW)):
        if game.count(old)!=1 or new in game:
            raise ValueError("REAL_GAME_ANCHOR_DRIFT_"+label)
        game=game.replace(old,new,1)
    return game

def build(basefile,beastfile,solofile,target,extract=None):
    _,base_lock,base_feat,_,base=load(basefile,"base")
    original,author_lock,author_feat,root,author=load(beastfile,"beast")
    _,solo_lock,solo_feat,_,solo=load(solofile,"solo")
    get=lambda s:{n:node.text for n,(node,kind,path) in s.items()}
    old=get(base);a=get(author);b=get(solo)
    if {n for n in old if old[n]!=a[n]}!={"Game","TrapRaidersHUD","SevenJobsRules"}:
        raise ValueError("AUTHOR_SOURCE_SCOPE_DRIFT")
    if {n for n in old if old[n]!=b[n]}!={"Game","SoloTeamBots"}:
        raise ValueError("QUALITY_SOURCE_SCOPE_DRIFT")
    game=merge_game(a["Game"],old["Game"],b["Game"])
    for contract in (
        "summonSevenBeast","privateSoloBotsTrialAllowed()",
        "pcall(SoloTeamBots.start,map,getTeamName(player),botAuthority)",
        "pcall(SoloTeamBots.tick,now)",
        "SoloTeamBots.tryHumanHit(team,root.Position,look",
        "P0D_SAFE_LOBBY","sevenJobPickAckSeq[player]~=selectedAck",
        "player.Character~=castCharacter","horde:tick(now,eligibleSoloPlayers(),healthy)",
        "personalEggDeposits[player]=(personalEggDeposits[player] or 0)+1",
        'else "EGG_CAPTURE")',LATCH_NEW,FAIL_NEW):
        if contract not in game: raise ValueError("MISSING_ACTUAL_GAME_CONTRACT:"+contract)
    if egg_block(game)!=egg_block(old["Game"]):
        raise ValueError("ORIGINAL_EGG_SCORE_WINNER_CHANGED")
    for k in ('local function applyAttack(','local function resetRound()',
              'local function tickRound()','local botAuthority='):
        if game.count(k)!=1:raise ValueError("DUPLICATE_GAME_AUTHORITY:"+k)
    if "P0D_LateJoinSpectator" not in b["SoloTeamBots"] or "callbacks.deposit(bot,bot.team,bot.carry)" not in b["SoloTeamBots"]:
        raise ValueError("BOT_EGG_AI_SOURCE_MISSING")
    author["Game"][0].text=game
    author["SoloTeamBots"][0].text=b["SoloTeamBots"]
    place=ET.tostring(root,encoding="utf-8")
    if sha(place)!=EXPECTED_PLACE or len(place)!=EXPECTED_BYTES or blob(game)!=EXPECTED_GAME:
        raise ValueError("REAL_PLACE_SHA_BLOB_OR_BYTE_REPRODUCIBILITY_FAILURE")
    author_lock["blobs"][GAME]=author_feat["source_gitblobs"][GAME]=blob(game)
    author_lock["blobs"][BOTS]=author_feat["source_gitblobs"][BOTS]=blob(b["SoloTeamBots"])
    _,result=locked(place,author_lock,author_feat)
    if any(result[n][0].text!=a[n] for n in a if n not in ("Game","SoloTeamBots")):
        raise ValueError("OTHER_80_ORIGINAL_AUTHOR_SOURCE_CHANGED")
    receipt={
        "schema":"P0D_470_ORIGINAL_BEAST_PLUS_SOLO_AI_INTEGRATION_V1",
        "official_rc_head":RC,"official_rc_write":False,
        "parent_place_sha256":{k:v[1] for k,v in PINS.items()},
        "place_sha256":sha(place),"place_bytes":len(place),
        "game_gitblob":blob(game),"solo_bots_gitblob":blob(b["SoloTeamBots"]),
        "scripts":82,"original_author_scripts_unchanged":80,
        "original_beast_3d_follow_attack_source":True,
        "private_solo_ai_egg_result_source":True,"private_only":True,"default_off":True,
        "egg_score_winner_source_byte_exact":True,
        "source_lock_exact":True,"native":"NOT_RUN","rojo":"NOT_RUN",
        "studio":"NOT_RUN","android":"NOT_RUN","owner":False,"product":"NO_GO"}
    with ZipFile(target,"w",ZIP_DEFLATED) as z:
        z.writestr(OUTPUT,place)
        z.writestr("SOURCE_LOCK.json",json.dumps(author_lock,ensure_ascii=False,indent=2)+"\n")
        z.writestr("RC_FEATURE_LOCK.json",json.dumps(author_feat,ensure_ascii=False,indent=2)+"\n")
        z.writestr("RECEIPT.json",json.dumps(receipt,ensure_ascii=False,indent=2)+"\n")
        z.writestr("source/server/Game.server.luau",game)
        z.writestr("source/server/SoloTeamBots.luau",b["SoloTeamBots"])
    if extract:
        extract.mkdir(parents=True,exist_ok=True)
        for name,(node,kind,path) in result.items():
            (extract/(name+".luau")).write_text(node.text,encoding="utf-8")
    return receipt

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--base",type=Path,required=True)
    p.add_argument("--beast",type=Path,required=True)
    p.add_argument("--solo",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--extract",type=Path)
    args=p.parse_args()
    print(json.dumps(build(args.base,args.beast,args.solo,args.out,args.extract),ensure_ascii=False,indent=2))
