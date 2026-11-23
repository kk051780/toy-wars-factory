#!/usr/bin/env python3
"""Self-contained hostile-mutation tests. Actual source hashes are checked by CI."""
import copy
import hashlib
import json
import tempfile
from pathlib import Path

from verify_integrated_sources import ROUTES, EXPECTED, verify, N


def make_fixture(root: Path):
    rows = sorted(set(x for names in ROUTES.values() for x in names))
    assert len(rows) < N
    rows += ["ServerScriptService/GQ8_Fixture_%02d" % i for i in range(N - len(rows))]
    project = {"name": "synthetic_fixture_not_a_playable_place", "tree": {}}
    receipt = {"selected_real55_count": N, "actual_trade_settlement_enabled": False,
               "formal_rc_adopted": False, "sources": []}
    for route in rows:
        path = route.split("/")
        suffix = ".client.luau" if EXPECTED.get(route) == "LocalScript" else (
            ".luau" if EXPECTED.get(route) == "ModuleScript" else ".server.luau")
        name = "sources/" + "/".join(path) + suffix
        f = root / name
        f.parent.mkdir(parents=True, exist_ok=True)
        b = ("--!strict\n-- synthetic source " + route + "\n").encode()
        f.write_bytes(b)
        parent = project["tree"]
        for piece in path[:-1]:
            parent = parent.setdefault(piece, {})
        parent[path[-1]] = {"$path": name}
        receipt["sources"].append({"route": route, "bytes": len(b),
                                   "sha256": hashlib.sha256(b).hexdigest(),
                                   "class": EXPECTED.get(route, "Script")})
    proj = root / "real53.project.json"
    rec = root / "receipt.json"
    proj.write_text(json.dumps(project))
    rec.write_text(json.dumps(receipt))
    return proj, rec


def denied(proj, rec, code):
    try:
        verify(proj, rec)
        raise AssertionError("BAD_INPUT_ACCEPTED_" + code)
    except ValueError as exc:
        assert code in str(exc), (code, str(exc))


with tempfile.TemporaryDirectory() as temp:
    root = Path(temp)
    proj, rec = make_fixture(root)
    report = verify(proj, rec)
    assert report["source_count"] == 55
    assert report["evidenced_lanes_source_only"] == 9
    assert report["evidenced_lanes_actual_studio"] == 0
    assert report["author_private_artifact_claims_formal_rc"] is False

    original_receipt = rec.read_text()
    item = json.loads(original_receipt)
    item["sources"][1]["route"] = item["sources"][0]["route"]
    rec.write_text(json.dumps(item))
    denied(proj, rec, "RED_DUPLICATE_LEDGER_ROUTE")

    item = json.loads(original_receipt)
    item["actual_trade_settlement_enabled"] = True
    rec.write_text(json.dumps(item))
    denied(proj, rec, "RED_FALSE_COMMERCE_OR_RC_CLAIM")
    rec.write_text(original_receipt)

    route = "ServerScriptService/EGGRUMBLE_MusouFeverPolicy"
    file = root / ("sources/" + route + ".server.luau")
    old = file.read_bytes()
    file.write_bytes(old + b"-- source drift\n")
    denied(proj, rec, "RED_SOURCE_HASH")
    file.write_bytes(old)

    original_project = proj.read_text()
    project = json.loads(original_project)
    project["tree"]["ServerScriptService"]["GQ8_Fixture_RENAMED"] = project["tree"]["ServerScriptService"].pop("GQ8_Fixture_00")
    proj.write_text(json.dumps(project))
    denied(proj, rec, "RED_LEDGER_ROUTE_DRIFT")
    proj.write_text(original_project)

    item = json.loads(original_receipt)
    item["formal_rc_adopted"] = True
    rec.write_text(json.dumps(item))
    denied(proj, rec, "RED_FALSE_COMMERCE_OR_RC_CLAIM")

print("GQ8_REAL55_NINE_LANE_RECEIPT_5_HOSTILE_MUTATION_CASES_PASS")
