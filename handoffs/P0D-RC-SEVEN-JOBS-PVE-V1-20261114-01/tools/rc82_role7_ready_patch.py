#!/usr/bin/env python3
"""#297 original author RC82 role-selection safety patch (source-only, no RC writes)."""
from __future__ import annotations
import argparse
import hashlib
import io
import json
from collections import Counter
from pathlib import Path
import xml.etree.ElementTree as ET
import zipfile

BASE="d2f3ed1a47558fdaf07be0181c83c698bdb2ce34"
PLACE="P0D_RC82_ASSASSIN_7JOB_PRIVATE_MOBILE_STUDIO.rbxlx"
PLACE_SHA="79938054ff3d4c6859e195789be35520032bb8b9ff4bb3c7ff80515d0dcb22dd"
GP="server/Game.server.luau"
HP="client/HUD.client.luau"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def gitblob(s):
    b=s.encode()
    return hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()


def once(s,old,new,label):
    if s.count(old)!=1:
        raise ValueError("DRIFT_"+label+"_"+str(s.count(old)))
    return s.replace(old,new,1)


def patch_game(s):
    s=once(s,"and otherJob==job then occupied=true;break end",
       "and sevenJobSelected[other]==true and otherJob==job then occupied=true;break end","OCCUPIED")
    s=once(s,"    sevenJobLastChoose[player]=now\n    remote:FireClient(player,snapshotFor(player))",
       "    sevenJobLastChoose[player]=now\n    roundReady[player]=false\n    broadcast() -- update all peers after job change","READY_REVOKE")
    s=once(s,"    lastSeq[player]=data.seq\n    local alive,root=healthy(player)",
       "    if sevenJobSelected[player]~=true then return end -- reject before seq\n"
       "    lastSeq[player]=data.seq\n    local alive,root=healthy(player)","SKILL_BEFORE_PICK")
    s=once(s,'    if match.phase == "COUNTDOWN" and data.ready then return end\n'
       '    if not Rules.validSeq(data.seq, lastSeq[player] or 0) then return end',
       '    if match.phase == "COUNTDOWN" and data.ready then return end\n'
       '    if data.ready and (RunService:IsStudio() or privateHordeTrialAllowed())\n'
       '        and ServerStorage:GetAttribute("P0D_RC_ENABLE_SEVEN_JOBS_PVE")~=false\n'
       '        and sevenJobSelected[player]~=true then return end -- before seq\n'
       '    if not Rules.validSeq(data.seq, lastSeq[player] or 0) then return end',"READY_BEFORE_PICK")
    s=once(s,"            dropEgg(player)\n            player.Team = teamInstances[move.to]",
       '            dropEgg(player)\n            sevenJobs[player]="WARRIOR"\n'
       '            sevenJobSelected[player]=false\n            sevenJobLastChoose[player]=-math.huge\n'
       '            sevenJobLastUse[player]=-math.huge\n            roundReady[player]=false\n'
       '            player.Team = teamInstances[move.to]',"REBALANCE_CLEAR")
    return s


def patch_hud(s):
    s=once(s,"    if not readyButton.Visible then return end\n    seq += 1",
       "    if not readyButton.Visible or not readyButton.Active then return end\n    seq += 1","READY_CLICK")
    old=('    if type(s.phase) == "string" then\n'
         '        isReady = s.ready == true\n'
         '        readyButton.Visible = s.phase == "LOBBY" or s.phase == "COUNTDOWN"\n'
         '        readyButton.Text = if isReady then "✓ 出撃予約中\\n押すと取消" else "▶ 出撃する"\n'
         '    end\n')
    s=once(s,old,"", "STALE_READY_MUTATION")
    s=once(s,'    if id ~= nil then lastUpdateId = id end\n'
       '    relayLatest=s -- only after accepted SNAPSHOT ordering check',
       '    if id ~= nil then lastUpdateId = id end\n'
       '    isReady=s.ready==true\n'
       '    local mustPick=s.jobStudioPvE==true and s.jobSelected~=true\n'
       '    readyButton.Visible=s.phase=="LOBBY" or (s.phase=="COUNTDOWN" and isReady)\n'
       '    readyButton.Active=readyButton.Visible and not (mustPick and not isReady)\n'
       '    readyButton.AutoButtonColor=readyButton.Active\n'
       '    readyButton.Text=if mustPick and not isReady then "先に職業を選ぶ"\n'
       '        elseif isReady then "✓ 出撃予約中\\n押すと取消" else "▶ 出撃する"\n'
       '    relayLatest=s -- only after accepted SNAPSHOT ordering check',"ACCEPTED_READY_ONLY")
    s=once(s,'    jobMenu.Text="職業: "..jobName[picked].." J"',
       '    jobMenu.Text=if s.jobSelected==true then "職業: "..jobName[picked].." J"\n'
       '        else "職業を選ぶ J"',"UNSELECTED_LABEL")
    s=once(s,'    jobCast.Active=jobCast.Visible and jobCd==0 and not currentNetBound',
       '    jobCast.Active=jobCast.Visible and s.jobSelected==true and jobCd==0 and not currentNetBound',"SKILL_DISABLED")
    return s


def build(artifact):
    with zipfile.ZipFile(io.BytesIO(artifact)) as z:
        original=z.read(PLACE)
        if sha(original)!=PLACE_SHA:
            raise ValueError("OFFICIAL_PLACE_SHA_MISMATCH")
        lock=json.loads(z.read("SOURCE_LOCK.json"))
        fl=json.loads(z.read("RC_FEATURE_LOCK.json"))
    root=ET.fromstring(original)
    items=[]
    for item in root.iter("Item"):
        props=item.find("Properties")
        if props is None:continue
        name=props.find("./string[@name='Name']")
        script=props.find("./string[@name='Source']")
        if name is not None and script is not None and script.text is not None:
            items.append((name.text,script))
    if len(items)!=82:
        raise ValueError("SOURCE_COUNT_NOT_82")
    before={v:script.text for v,script in items if v in ("Game","TrapRaidersHUD")}
    if len(before)!=2:
        raise ValueError("MISSING_UNIQUE_GAME_HUD")
    original_counts=Counter(gitblob(s.text) for _,s in items)
    expected=Counter(lock["blobs"].values())
    if original_counts!=expected:
        raise ValueError("ORIGINAL_SOURCE_LOCK_INVALID")
    for name,path,fn in (("Game",GP,patch_game),("TrapRaidersHUD",HP,patch_hud)):
        script=next(s for n,s in items if n==name)
        if gitblob(script.text)!=lock["blobs"][path]:
            raise ValueError("SOURCE_PATH_MISMATCH_"+name)
        script.text=fn(script.text)
        lock["blobs"][path]=gitblob(script.text)
        fl["source_gitblobs"][path]=gitblob(script.text)
    after=Counter(gitblob(s.text) for _,s in items)
    if after!=Counter(lock["blobs"].values()):
        raise ValueError("OTHER_SOURCE_CHANGED")
    out=ET.tostring(root,encoding="utf-8")
    reread=ET.fromstring(out)
    blobs=Counter(gitblob(x.text) for x in reread.iter("string")
                  if x.attrib.get("name")=="Source" and x.text is not None)
    if blobs!=after:
        raise ValueError("SERIALIZATION_CHANGED_SOURCE")
    receipt={"schema":"P0D_RC82_ROLE7_PATCH_V1","source_rc":BASE,
             "official_place_sha256":PLACE_SHA,"private_place_sha256":sha(out),
             "private_place_bytes":len(out),"scripts":82,"unchanged_scripts":80,
             "modified":[GP,HP],"game_blob":lock["blobs"][GP],"hud_blob":lock["blobs"][HP],
             "native_luau":"NOT_RUN","studio":"NOT_RUN","android":"NOT_RUN",
             "product":"NO_GO","owner":False,"official_rc_write":False}
    return out,lock,fl,receipt,before


def main():
    p=argparse.ArgumentParser()
    p.add_argument("artifact_zip",type=Path)
    p.add_argument("output_zip",type=Path)
    args=p.parse_args()
    place,lock,feature,receipt,before=build(args.artifact_zip.read_bytes())
    args.output_zip.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(args.output_zip,"w",compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr("PRIVATE_ROLE7_READY_RC82.rbxlx",place)
        z.writestr("SOURCE_LOCK.json",json.dumps(lock,ensure_ascii=False,indent=2))
        z.writestr("RC_FEATURE_LOCK.json",json.dumps(feature,ensure_ascii=False,indent=2))
        z.writestr("RECEIPT.json",json.dumps(receipt,ensure_ascii=False,indent=2))
        z.writestr("READ_ME.txt","Source-only real RC82 patch. Original author #297; #220 integration required. No Studio or native Luau validation.\n")
    print(json.dumps(receipt,ensure_ascii=False,indent=2))


if __name__=="__main__":
    main()
