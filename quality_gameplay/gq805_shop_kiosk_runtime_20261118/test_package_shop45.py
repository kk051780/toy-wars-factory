from pathlib import Path
import json
import tempfile
import sys
from package_shop45 import package, git_blob, UPSTREAM_CATALOG_BLOB, UPSTREAM_VIEW_BLOB

def test(catalog:Path,view:Path):
    assert git_blob(catalog.read_bytes())==UPSTREAM_CATALOG_BLOB
    assert git_blob(view.read_bytes())==UPSTREAM_VIEW_BLOB
    with tempfile.TemporaryDirectory(prefix="gq805-shop45-") as t:
        p=Path(t)
        upstream=p/"upstream";upstream.mkdir()
        routes=[
            ("ServerScriptService","EGGRUMBLE_LobbyCastleModesPreview"),
            ("ServerScriptService","EGGRUMBLE_SwarmCombat"),
            ("ServerScriptService","EGGRUMBLE_CastleMatchRules"),
        ]+[("ServerScriptService","GQ805_SYNTHETIC_UPSTREAM_"+str(i)) for i in range(38)]
        tree={"ServerScriptService":{}}
        ledger=[]
        for route in routes:
            data=("-- synthetic test only "+route[-1]+"\nreturn {}\n").encode()
            f=upstream/(route[-1]+".luau");f.write_bytes(data)
            tree["ServerScriptService"][route[-1]]={"$path":f.name}
            import hashlib
            ledger.append({"route":"/".join(route),"git_blob":git_blob(data),
                "sha256":hashlib.sha256(data).hexdigest(),"class":"ModuleScript","bytes":len(data)})
        doc=upstream/"fake41.project.json"
        doc.write_text(json.dumps({"name":"fake41","tree":tree}))
        head="9"*40
        receipt=upstream/"receipt.json"
        receipt.write_text(json.dumps({"candidate_sha":head,"source_count":41,"sources":ledger}))
        kiosk=Path(__file__).parent
        report=package(doc,receipt,catalog,view,kiosk,p/"good",head)
        assert report["source_count"]==45
        project=json.loads((p/"good"/"EGGRUMBLE_REAL45_KIOSK.project.json").read_text())
        assert project["tree"]["ReplicatedStorage"]["GQ805Shop"]["$className"]=="Folder"
        assert report["unchanged_original_count"]==41
        assert report["original41_readback_pass"] is True
        assert (p/"good"/"sources"/"ReplicatedStorage"/"GQ805Shop"/"EGGRUMBLE_LobbyShopView.luau").read_bytes()==view.read_bytes()
        assert (p/"good"/"sources"/"StarterPlayer"/"StarterPlayerScripts"/"GQ805_ShopKioskClient.client.luau").exists()
        def must_fail(out:Path,meaning:str,readcatalog:Path=catalog):
            try: package(doc,receipt,readcatalog,view,kiosk,out,head)
            except ValueError as exc:
                assert meaning in str(exc),(meaning,str(exc))
            else: raise AssertionError("unexpectedly accepted "+meaning)
        upstream.joinpath("EGGRUMBLE_SwarmCombat.luau").write_text("-- mutated")
        must_fail(p/"bad-parent","RED_REAL41_SOURCE_CLASS_OR_SHA_DRIFT")
        upstream.joinpath("EGGRUMBLE_SwarmCombat.luau").write_bytes(("-- synthetic test only EGGRUMBLE_SwarmCombat\nreturn {}\n").encode())
        altered=p/"bad_catalog.luau";altered.write_text("return {}")
        must_fail(p/"bad-catalog","RED_CATALOG_808_AUTHOR_DRIFT",altered)
        must_fail(p/"good","RED_DO_NOT_REUSE_PORTABLE_FOLDER")
    print("GQ805_PRIVATE45_COMPOSER_41_EXACT_OFF41_AND_3_NEGATIVES_PASS")

if __name__=="__main__":
    if len(sys.argv)!=3: raise SystemExit("usage: test_package_shop45.py catalog view")
    test(Path(sys.argv[1]),Path(sys.argv[2]))
