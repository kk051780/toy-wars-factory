#!/usr/bin/env python3
"""Source-lock one existing EGGRUMBLE Combat and replace ONLY BEAST skill B.

No new Game/Remote/Store/score/Combat script. Only #220's authenticated non-force
CAS can source-select this in official RC after same-HEAD full31 Native/Rojo.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

ORIGINAL_482_BLOB = "66e666418b7c23d41f87faa5d61eb6e2770a463e"
INSERT_ANCHOR = "local function execute(session:any,p:Player,role:string,slot:string)\n"
OLD_BEAST_B = '''  elseif slot=="B" then
   local giant=makeEffect(session.world,rootAdvance(root,11),Vector3.new(12,15,12),def.color,1.6)
   giant.Name="BeastFeedGiant";char:SetAttribute("EGGRUMBLE_GiantFeedUntil",now+5);blast()
'''
NEW_BEAST_B = '''  elseif slot=="B" then
   -- Real one-companion beast; this existing Combat remains sole damage authority.
   if BeastEscort.begin(session,p,char,root,h,owner,function(petRoot:BasePart,pet:Model,at:Vector3)
    if session.rules.phase=="ACTIVE" and owner.alive and p.Character==char
     and h.Health>0 and p:GetAttribute("EGGRUMBLE_Role")=="BEAST"
     and (session.isCurrentHuman==nil or session.isCurrentHuman(p)==true)
     and (petRoot.Position-root.Position).Magnitude<=28 then
     neutralAndBotHit(session,p,petRoot,pet,at,3.5,6,def.color,spec.shape)
    end
   end) then
    char:SetAttribute("EGGRUMBLE_GiantFeedUntil",now+5)
   end
   blast()
'''

def git_blob(raw: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()

def compose(original: str, runtime: str) -> tuple[str, str]:
    if original.count(INSERT_ANCHOR) != 1 or original.count(OLD_BEAST_B) != 1:
        raise ValueError("RED_BEAST_COMBAT_ANCHOR_DRIFT")
    if original.count("local HeroCombat={}") != 1 or not original.rstrip().endswith("return HeroCombat"):
        raise ValueError("RED_COMBAT_AUTHORITY_DRIFT")
    if not runtime.startswith("--!strict\n") or runtime.count("return BeastEscort") != 1:
        raise ValueError("RED_BEAST_RUNTIME_DRIFT")
    if "Humanoid:TakeDamage" in runtime or 'Instance.new("RemoteEvent")' in runtime or "DataStoreService" in runtime:
        raise ValueError("RED_DUPLICATE_AUTHORITY")
    inner = runtime.replace("--!strict\n", "", 1)
    inline = "local BeastEscort=(function()\n" + inner + "end)()\n"
    selected = original.replace(INSERT_ANCHOR, inline + INSERT_ANCHOR, 1)
    selected = selected.replace(OLD_BEAST_B, NEW_BEAST_B, 1)
    if selected == original:
        raise ValueError("RED_NO_GAMEPLAY_DELTA")
    if rollback(selected, inline) != original:
        raise ValueError("RED_BEAST_OFF_NOT_BYTE_EXACT")
    return selected, inline

def rollback(selected: str, inline: str) -> str:
    if selected.count(inline) != 1 or selected.count(NEW_BEAST_B) != 1:
        raise ValueError("RED_BEAST_OFF_DRIFT")
    return selected.replace(NEW_BEAST_B, OLD_BEAST_B, 1).replace(
        inline + INSERT_ANCHOR, INSERT_ANCHOR, 1
    )

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--combat", type=Path, required=True)
    ap.add_argument("--runtime", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--receipt", type=Path, required=True)
    ap.add_argument("--expected-blob", default=ORIGINAL_482_BLOB)
    args = ap.parse_args()
    if not re.fullmatch(r"[0-9a-f]{40}", args.expected_blob):
        raise ValueError("RED_EXPECTED_COMBAT_BLOB_FORMAT")
    original_bytes = args.combat.read_bytes()
    original_blob = git_blob(original_bytes)
    if original_blob != args.expected_blob:
        raise ValueError(f"RED_COMBAT_SOURCE_LOCK expected={args.expected_blob} actual={original_blob}")
    selected, inline = compose(original_bytes.decode("utf-8"), args.runtime.read_text())
    if args.out.exists() or args.receipt.exists():
        raise ValueError("RED_REFUSE_OVERWRITE_CANDIDATE")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(selected, encoding="utf-8")
    args.receipt.write_text(json.dumps({
        "feature_id": "GQ_BEAST_ESCORT_REAL_UNIT_20261117",
        "source_input_blob": original_blob,
        "selected_combat_sha256": hashlib.sha256(selected.encode()).hexdigest(),
        "original_combat_sha256": hashlib.sha256(original_bytes).hexdigest(),
        "changed_runtime_script_count": 0,
        "one_existing_combat_authority": True,
        "exact_OFF_rollback": rollback(selected, inline) == original_bytes.decode(),
        "original_six_other_roles_preserved": True,
        "candidate_only": True,
        "official_rc": "NOT_ADOPTED",
        "studio_android_art_fun_owner": "NOT_TESTED",
        "next": "Re-compose from latest real selected31 Combat; Native31/Rojo31, immutable HEAD and #220 non-force CAS."
    }, indent=2) + "\n")
    print("GQ_BEAST_ESCORT_EXACT_SINGLE_COMBAT_SOURCE_AND_OFF_PASS")

if __name__ == "__main__":
    main()
