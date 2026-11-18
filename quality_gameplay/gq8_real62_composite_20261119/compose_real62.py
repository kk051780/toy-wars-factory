#!/usr/bin/env python3
"""Current official Real59 (HUD/Fog) + original #838 journal/UI/escrow 3 => Real62."""
import argparse,json,sys
from pathlib import Path
from xml.etree import ElementTree as ET
ROOT=Path(__file__).resolve().parents[2]
HUD=ROOT/"handoffs/EGGRUMBLE-HUD-INTEL-20261119"
TRADE=ROOT/"quality_gameplay/gq8_trade_ux_journal_20261119"
sys.path.insert(0,str(HUD))
from compose_real40 import contents,project_for,digest
MORE={
 "ServerScriptService/GQ8_TradeJournalContract":("ModuleScript","GQ8_TradeJournalContract.luau"),
 "StarterPlayer/StarterPlayerScripts/GQ8_TradeReview":("LocalScript","GQ8_TradeReview.client.luau"),
 "ServerScriptService/GQ8_TradeEscrowReducer":("ModuleScript","GQ8_TradeEscrowReducer.luau"),
}
HEAD="38d11f0bf311491ba76fe03f818948e5d4b06889"
def compose(place,receipt,out):
    data=json.loads(receipt.read_text(encoding="utf8"))
    assert data.get("candidate_head")==HEAD and data.get("official_head")==HEAD
    assert data.get("official_rc_adopted") is True
    assert data.get("candidate_real59_source_count")==59
    assert data.get("selected59_place_sha256")==digest(place)
    original,classes=contents(ET.parse(place).getroot())
    assert len(original)==59
    assert ("ServerScriptService","EGGRUMBLE_LobbyCastleModesPreview") in original
    assert ("StarterPlayer","StarterPlayerScripts","EGGRUMBLE_HudIntelRuntime") in original
    assert ("ServerScriptService","EGGRUMBLE_MapIntelBridge") in original
    assert ("ServerScriptService","GQ8_LobbySocialPlaza") in original
    assert not out.exists()
    out.mkdir()
    off=out/"off59";off.mkdir()
    offproj,offindex=project_for(original,classes,off,"REAL62_OFF59")
    allscripts=dict(original)
    for route,(cl,filename) in MORE.items():
        key=tuple(route.split("/"))
        assert key not in allscripts
        allscripts[key]=(cl,(TRADE/filename).read_text(encoding="utf8"))
        classes[key]=cl
        for i in range(1,len(key)):
            sub=key[:i];classes.setdefault(sub,"Folder" if len(sub)>1 else sub[0])
    assert len(allscripts)==62 and len({r[-1] for r in allscripts})==62
    assert all(allscripts[k]==v for k,v in original.items())
    on=out/"on62";on.mkdir()
    onproj,onindex=project_for(allscripts,classes,on,"REAL62_HUD_TRADE")
    assert {r["route"] for r in onindex}-{r["route"] for r in offindex}==set(MORE)
    report={"baseline_official_head":HEAD,"baseline_count":59,"combined_count":62,"original59_exact":True,"new_routes":list(MORE),"on_sources":onindex,"off_sources":offindex,"official_rc_adopted":False,"paid_trading":False,"actual_inventory_transfer":False,"studio":"NOT_TESTED","android":"NOT_TESTED","fun":"NOT_TESTED","rollback":"OFF59 exact original"}
    (out/"B_REAL62_RECEIPT.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
    print("REAL62_ORIGINAL59_EXACT_PLUS3_TRADE_PASS")
if __name__=="__main__":
    a=argparse.ArgumentParser()
    a.add_argument("--place",type=Path,required=True)
    a.add_argument("--receipt",type=Path,required=True)
    a.add_argument("--out",type=Path,required=True)
    p=a.parse_args();compose(p.place,p.receipt,p.out)
