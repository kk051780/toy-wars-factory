#!/usr/bin/env python3
"""P0D FB003+FB008 confirmed individual match results on genuine 82-source place.
Only one Game, one HUD, one ResultNextStep patched. No second damage/score/Remote.
The existing Horde:hit returns server-confirmed per-swing defeated HP-zero KOs.
"""
from __future__ import annotations
import argparse,hashlib,json,os,shutil,tempfile
from pathlib import Path
from apply_fb003_prompt_fix import read,blob

GAME="server/Game.server.luau"
HUD="client/HUD.client.luau"
RESULT="client/ResultNextStep.client.luau"
FEATURE="P0D_FB003_FB008_PERSONAL_RESULTS_V1"
BASE_FEATURE="FB008_ORIGINAL17_SIXPACK_REAL82_V1"
PINS={
    GAME:"9aa40d9fb5c137c7a60a1efc535b47bb4857aa32",
    HUD:"f416c047bf5e05e7e434fc07235743b2fb509d98",
    RESULT:"03898fa5d84096f2209e4afacef6e50a96682196",
}
NEW_PINS={
    GAME:"a8248896acea4ede4b191bd22485d77a9da18e12",
    HUD:"14594676e6c7f798d46bde6614ff715972bd6e19",
    RESULT:"fc39e152b30c2e391c2661dbb3246415d97aa2c6",
}

def one(s,old,new):
    assert s.count(old)==1,("ORIGINAL_ANCHOR_DRIFT",old[:70],s.count(old))
    return s.replace(old,new,1)

def patch(data):
    assert all(blob(data[k])==v for k,v in PINS.items()),"REAL82_ORIGINAL_SOURCE_DRIFT"
    g=data[GAME].decode("utf8")
    h=data[HUD].decode("utf8")
    r=data[RESULT].decode("utf8")
    g=one(g,'local mobLastKOs: {[Player]: number} = {}\n',
      'local mobLastKOs: {[Player]: number} = {}\n'
      '-- Confirmed HP-zero KOs and successful home-pad egg deposits only, per match.\n'
      'local personalNeutralKOs: {[Player]: number} = {}\n'
      'local personalEggDeposits: {[Player]: number} = {}\n')
    g=one(g,'        musouLastKOs = mobLastKOs[player] or 0,\n',
      '        musouLastKOs = mobLastKOs[player] or 0,\n'
      '        personalNeutralKOs = personalNeutralKOs[player] or 0,\n'
      '        personalEggDeposits = personalEggDeposits[player] or 0,\n')
    g=one(g,'                local hits=horde:hit(currentRoot.Position,currentRoot.CFrame.LookVector,',
      '                local hits,kos=horde:hit(currentRoot.Position,currentRoot.CFrame.LookVector,')
    g=one(g,'                    mobLastKOs[player]=0\n',
      '                    mobLastKOs[player]=kos\n'
      '                    if kos>0 then personalNeutralKOs[player]=(personalNeutralKOs[player] or 0)+kos end\n')
    g=one(g,'        mobLastKOs[p] = 0\n',
      '        mobLastKOs[p] = 0\n'
      '        personalNeutralKOs[p] = 0\n'
      '        personalEggDeposits[p] = 0\n')
    g=one(g,'    match.scores.RED=h2ScoreState.scores.RED\n'
      '    match.scores.BLUE=h2ScoreState.scores.BLUE\n'
      '    recordServerProgress(player,"DEPOSIT")\n',
      '    match.scores.RED=h2ScoreState.scores.RED\n'
      '    match.scores.BLUE=h2ScoreState.scores.BLUE\n'
      '    personalEggDeposits[player]=(personalEggDeposits[player] or 0)+1\n'
      '    recordServerProgress(player,"DEPOSIT")\n')
    g=one(g,'        match.scores[team] += 1\n'
      '        recordServerProgress(player,"DEPOSIT")\n',
      '        match.scores[team] += 1\n'
      '        personalEggDeposits[player]=(personalEggDeposits[player] or 0)+1\n'
      '        recordServerProgress(player,"DEPOSIT")\n')
    g=one(g,'            mobLastKOs[player]=defeated\n',
      '            mobLastKOs[player]=defeated\n'
      '            if defeated>0 then personalNeutralKOs[player]=(personalNeutralKOs[player] or 0)+defeated end\n')
    g=one(g,'        mobLastKOs[player]=kos\n        First90Guide.mark(',
      '        mobLastKOs[player]=kos\n'
      '        if kos>0 then personalNeutralKOs[player]=(personalNeutralKOs[player] or 0)+kos end\n'
      '        First90Guide.mark(')
    g=one(g,'    mobLastKOs[player] = 0\n',
      '    mobLastKOs[player] = 0\n'
      '    personalNeutralKOs[player] = 0\n'
      '    personalEggDeposits[player] = 0\n')
    g=one(g,'    mobLastKOs[player] = nil\n',
      '    mobLastKOs[player] = nil\n'
      '    personalNeutralKOs[player] = nil\n'
      '    personalEggDeposits[player] = nil\n')
    h=one(h,'    -- RESULTS ends at the lobby. A new round still needs enough players.\n'
      '    return outcome .. "　" .. reason .. "｜次の準備まで " .. tostring(seconds) .. " 秒"\n',
      '    local kills=if type(s.personalNeutralKOs)=="number"\n'
      '        and s.personalNeutralKOs>=0 and s.personalNeutralKOs<=100000\n'
      '        and s.personalNeutralKOs%1==0 then s.personalNeutralKOs else nil\n'
      '    local eggs=if type(s.personalEggDeposits)=="number"\n'
      '        and s.personalEggDeposits>=0 and s.personalEggDeposits<=10000\n'
      '        and s.personalEggDeposits%1==0 then s.personalEggDeposits else nil\n'
      '    local personal=if eggs~=nil and kills~=nil\n'
      '        then "｜🥚"..tostring(eggs).." ⚔"..tostring(kills) else ""\n'
      '    -- Existing single mobile status text only; no new persistent HUD or popup.\n'
      '    return outcome .. personal .. "｜次の準備まで " .. tostring(seconds) .. " 秒"\n')
    r=one(r,'local function summarize(msg: any): string\n',
      'local function personalInt(value: any, limit: number): number?\n'
      '    if type(value)~="number" or value~=value or value<0 or value>limit\n'
      '        or value%1~=0 then return nil end\n'
      '    return value\n'
      'end\n\nlocal function summarize(msg: any): string\n')
    r=one(r,'    -- The original snapshot has team score, NOT individual egg deposits.\n'
      "    -- Never label this as a player's own egg or the match's neutral KOs.\n",
      '    -- Server result fields are per-player, not team score or transient last hit.\n')
    r=one(r,'    local dojo = dojoView(msg)\n',
      '    local eggs=personalInt(msg.personalEggDeposits,10000)\n'
      '    local kills=personalInt(msg.personalNeutralKOs,100000)\n'
      '    local personalText=if eggs~=nil and kills~=nil then "自分 🥚"..tostring(eggs)\n'
      '        .."・中立撃破 "..tostring(kills) else "個人成績: 未確認"\n'
      '    local dojo = dojoView(msg)\n')
    r=one(r,'        local advice = Advisor.build({won=won, eggsScored=score or 0},\n',
      '        local advice = Advisor.build({won=won, eggsScored=eggs or 0},\n')
    r=one(r,'    local summary = resultText.."  |  "..scoreText.."\\n"..adviceText..bonusText..\n'
      '        "\\n7秒で消えます・戦績はサーバー情報のみ"\n',
      '    local summary = resultText.."  |  "..scoreText.."\\n"..personalText..\n'
      '        "\\n"..adviceText..bonusText\n')
    changed={GAME:g.encode("utf8"),HUD:h.encode("utf8"),RESULT:r.encode("utf8")}
    assert {k:blob(v) for k,v in changed.items()}==NEW_PINS, "AUTHOR_PATCH_OUTPUT_CHANGED"
    assert g.count('horde:hit(')==3
    assert g.count('remote.OnServerEvent:Connect(')==1
    assert g.count('personalNeutralKOs[player]=(personalNeutralKOs[player] or 0)+')==3
    assert g.count('personalEggDeposits[player]=(personalEggDeposits[player] or 0)+1')==2
    assert g.count('H2Score.deposit(')==1
    assert g.count('match.scores[team] += 1')==1
    return changed

def apply(base:Path,out:Path,enabled:bool):
    assert not out.exists(),"OUTPUT_EXISTS"
    if not enabled:
        print("P0D_PERSONAL_RESULT_OFF_ZERO_WRITE");return False
    base=base.resolve();out=out.absolute()
    assert base.is_dir() and out.parent.is_dir()
    assert not out.is_relative_to(base) and not base.is_relative_to(out)
    before=read(base)
    assert len(before)==82 and set(PINS)<=set(before)
    sl=json.loads((base/"SOURCE_LOCK.json").read_text("utf8"))
    fl=json.loads((base/"RC_FEATURE_LOCK.json").read_text("utf8"))
    oldpins={k:blob(v) for k,v in sorted(before.items())}
    assert sl["total_scripts"]==fl["total_sources"]==82
    assert sl["blobs"]==fl["source_gitblobs"]==oldpins
    assert fl["feature_flags"].get(BASE_FEATURE) is True,"MISSING_FB008_PARENT"
    assert FEATURE not in fl["feature_flags"]
    fixed=patch(before)
    after={**before,**fixed}
    assert len(after)==82 and {k for k in before if before[k]!=after[k]}==set(PINS)
    newpins={k:blob(v) for k,v in sorted(after.items())}
    receipt={
      "feature_id":FEATURE,"parent":BASE_FEATURE,
      "original_author_source":"#364 personal result audit + preexisting MatchResultLedger draft",
      "three_modified_sources":list(PINS),"remaining79_byte_exact":True,
      "kills_only_from_server_horde_hp_zero":True,"normal_job_scout_kos":True,
      "classic_h2_success_deposits_only":True,"h2_team_points_not_egg_count":True,
      "per_player_per_round_reset":True,"no_persistent_hud_added":True,
      "owner_studio":"NOT_TESTED","android":"NOT_TESTED",
      "product_quality":"NO_GO","owner_accepted":False,
      "old_blobs":{k:oldpins[k] for k in PINS},"new_blobs":NEW_PINS,
      "rollback":"omit this overlay; original FB003+FB008 remains 82-source exact"
    }
    sl["blobs"]=newpins;fl["source_gitblobs"]=newpins
    sl["personal_results_v1"]=fl["personal_results_v1"]=receipt
    fl["feature_flags"][FEATURE]=True
    temp=Path(tempfile.mkdtemp(prefix=".p0d_personal_result_",dir=str(out.parent)))
    stage=temp/"candidate"
    try:
      shutil.copytree(base,stage,symlinks=False)
      for k,v in fixed.items(): (stage/"src"/k).write_bytes(v)
      for n,o in (("SOURCE_LOCK.json",sl),("RC_FEATURE_LOCK.json",fl)):
        (stage/n).write_text(json.dumps(o,ensure_ascii=False,indent=2)+"\n","utf8")
      assert read(stage)==after and read(base)==before,"PARENT_CHANGED"
      os.replace(stage,out)
    finally:
      shutil.rmtree(temp,ignore_errors=True)
    print("P0D_PERSONAL_RESULTS_RC82_SOURCE_EXACT_PASS",newpins[GAME],newpins[HUD],newpins[RESULT])
    return True

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--base",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--enabled",choices=("true","false"),required=True)
    a=p.parse_args()
    apply(a.base,a.out,a.enabled=="true")
