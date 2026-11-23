#!/usr/bin/env python3
"""Adversarial tests for the true nine-domain source intake auditor."""
from __future__ import annotations
import hashlib
import json
import tempfile
from pathlib import Path
from audit import audit, DOMAINS, SINGLETONS

def fixture(root: Path, n: int):
    names = set(SINGLETONS)
    for names_in_domain in DOMAINS.values():
        names.update(names_in_domain)
    names.add("GQ805_ShopKioskClient")
    if n >= 55:
        names.update(("GQ8_LobbySocialPlaza", "GQ8_TradePolicy"))
    while len(names) < n:
        names.add("GQ8_TestStableBody_" + str(len(names)))
    assert len(names) == n
    tree = {"$className": "DataModel", "ServerScriptService": {}}
    rows = []
    for name in sorted(names):
        ending = ".client.luau" if name == "GQ805_ShopKioskClient" else ".luau"
        kind = "LocalScript" if ending == ".client.luau" else "ModuleScript"
        rel = "sources/ServerScriptService/" + name + ending
        f = root / rel
        f.parent.mkdir(parents=True, exist_ok=True)
        body = "return {}\n"
        if name == "EGGRUMBLE_SwarmCombat":
            body = ("dummy:TakeDamage(InvulRuntime.filterDamage(victim, 1, 'PVP'))\n" * (12 if n >= 65 else 13))
        if name == "EGGRUMBLE_SevenRoleCombat" and n >= 65:
            body = ('local originalAttackDamage=InvulRuntime.filterDamage(enemyHum,damage*duel*mark*musou,"PLAYER",p.UserId)\n'
                    'enemyHum:TakeDamage(originalAttackDamage)\n'
                    'local realDamage=InvulRuntime.filterDamage(atHum,amount,"PLAYER",enemyPlayer.UserId)\n'
                    'atHum:TakeDamage(realDamage)\n')
        if name == "GQ805_ShopKioskClient":
            body = "local robuxEnabled=false\n"
        if name == "GQ8_TradePolicy":
            body = "local requiresExistingStoreAtomicJournal=true\n"
        f.write_text(body)
        tree["ServerScriptService"][name] = {"$path": rel}
        rows.append({"route": "ServerScriptService/" + name, "class": kind,
                     "bytes": len(f.read_bytes()),
                     "sha256": hashlib.sha256(f.read_bytes()).hexdigest()})
    project = root / "game.project.json"
    receipt = root / "source_receipt.json"
    project.write_text(json.dumps({"tree": tree}))
    key = "new_selected_source_count" if n >= 65 else ("selected_real55_count" if n == 55 else "selected_script_count")
    receipt.write_text(json.dumps({key: n, "sources": rows}))
    return project, receipt

def must_fail(fn, code):
    try:
        fn()
    except ValueError as ex:
        assert code in str(ex), (code, str(ex))
    else:
        raise AssertionError("missed negative mutation: " + code)

def main():
    with tempfile.TemporaryDirectory() as tmp:
        p, r = fixture(Path(tmp), 53)
        x = audit(p, r, 53)
        assert x["source_coverage_count"] == 9
        assert x["prehit_wired_damage_calls"] == 13
        original = json.loads(r.read_text())
        edited = json.loads(r.read_text())
        edited["sources"][0]["sha256"] = "0" * 64
        r.write_text(json.dumps(edited))
        must_fail(lambda: audit(p, r, 53), "RED_SOURCE_CLASS_OR_HASH")
        r.write_text(json.dumps(original))
        # Modify actual live source, not the receipt.
        raw = p.parent / "sources/ServerScriptService/EGGRUMBLE_SwarmCombat.luau"
        old = raw.read_text()
        raw.write_text(old.replace("InvulRuntime.filterDamage(", "unverified(", 1))
        must_fail(lambda: audit(p, r, 53), "RED_SOURCE_CLASS_OR_HASH")
        raw.write_text(old)
        kiosk = p.parent / "sources/ServerScriptService/GQ805_ShopKioskClient.client.luau"
        old = kiosk.read_text()
        kiosk.write_text("return {}\n")
        must_fail(lambda: audit(p, r, 53), "RED_SOURCE_CLASS_OR_HASH")
        kiosk.write_text(old)
    with tempfile.TemporaryDirectory() as tmp:
        p,r=fixture(Path(tmp),55)
        x=audit(p,r,55)
        assert x["source_count"]==55 and x["source_coverage_count"]==9
        broken=json.loads(r.read_text())
        broken["selected_real55_count"]=54
        r.write_text(json.dumps(broken))
        must_fail(lambda: audit(p,r,55), "RED_RECEIPT_SOURCE_COUNT")
    with tempfile.TemporaryDirectory() as tmp:
        p,r=fixture(Path(tmp),65)
        x=audit(p,r,65)
        assert x["source_count"]==65 and x["direct_damage_calls"]==14
        assert x["prehit_wired_damage_calls"]==12
        combat=p.parent/"sources/ServerScriptService/EGGRUMBLE_SevenRoleCombat.luau"
        combat.write_text(combat.read_text().replace('local realDamage=InvulRuntime.filterDamage(atHum,amount,"PLAYER",enemyPlayer.UserId)', 'local realDamage=amount'))
        changed=json.loads(r.read_text())
        for row in changed["sources"]:
            if row["route"].endswith("/EGGRUMBLE_SevenRoleCombat"):
                row["bytes"]=len(combat.read_bytes())
                row["sha256"]=hashlib.sha256(combat.read_bytes()).hexdigest()
        r.write_text(json.dumps(changed))
        must_fail(lambda:audit(p,r,65),"RED_REAL65_MISSING_PRECOMPUTED_INVUL_GUARD")
    print("GQ8_9DOMAIN_53_55_65_IDENTITY_AND_COUNTER_NEGATIVE_MUTATIONS_PASS")

if __name__=="__main__":
    main()
