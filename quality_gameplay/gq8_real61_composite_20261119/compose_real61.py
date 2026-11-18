from pathlib import Path
from xml.etree import ElementTree as ET
import argparse,sys,json
ROOT=Path(__file__).resolve().parents[2]
HUD=ROOT/"handoffs/EGGRUMBLE-HUD-INTEL-20261119"
TRADE=ROOT/"quality_gameplay/gq8_trade_ux_journal_20261119"
sys.path.insert(0,str(HUD))
from compose_real40 import contents,project_for,ADDITIONS,digest
MORE={"ServerScriptService/GQ8_TradeJournalContract":("ModuleScript","GQ8_TradeJournalContract.luau"),"StarterPlayer/StarterPlayerScripts/GQ8_TradeReview":("LocalScript","GQ8_TradeReview.client.luau")}
def compose(place,receipt,out):
    info=json.loads(receipt.read_text())
    assert info.get("selected_official_branch_sha")=="a6020867fac80fa3b2ca47478625873fc6f3678e"
    assert info.get("official_rc_adopted") is True and info.get("source_profile")=="eggrumble_v3_real55"
    assert info.get("private_place_sha256")==digest(place)
    original,classes=contents(ET.parse(place).getroot())
    assert len(original)==55
    assert ("ServerScriptService","GQ8_LobbySocialPlaza") in original
    assert ("ServerScriptService","EGGRUMBLE_LobbyCastleModesPreview") in original
    assert ("ReplicatedStorage","GQ8Trade","GQ8_TradePolicy") in original
    assert not out.exists()
    out.mkdir()
    off=out/"off55";off.mkdir()
    offproject,offindex=project_for(original,classes,off,"REAL61_OFF55")
    combined=dict(original)
    for path,(cl,name) in list(ADDITIONS.items())+list(MORE.items()):
        route=tuple(path.split("/"))
        assert route not in combined
        combined[route]=(cl,((HUD if path in ADDITIONS else TRADE)/name).read_text())
        classes[route]=cl
        for j in range(1,len(route)):
            sub=route[:j];classes.setdefault(sub,"Folder" if j>1 else sub[0])
    assert len(combined)==61 and len({k[-1] for k in combined})==61
    assert all(combined[k]==v for k,v in original.items())
    on=out/"on61";on.mkdir()
    onproject,onindex=project_for(combined,classes,on,"REAL61_HUD_TRADE")
    assert {x["route"] for x in onindex}-{x["route"] for x in offindex}==set(ADDITIONS)|set(MORE)
    report={"original_count":55,"combined_count":61,"original55_byte_exact":True,"added":list(ADDITIONS)+list(MORE),"original_sources":offindex,"selected_sources":onindex,"official_rc_adopted":False,"trade_settlement":False,"paid_features":False,"studio":"NOT_TESTED","android":"NOT_TESTED","fun":"NOT_TESTED","rollback":"OFF55"}
    (out/"B_REAL61_RECEIPT.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
    print("REAL61_ORIGINAL55_PRESERVED_PLUS6_PASS")
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--place",type=Path,required=True)
    p.add_argument("--receipt",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args();compose(a.place,a.receipt,a.out)
