#!/usr/bin/env python3
"""Negative mutation gates for source retention, route collisions, and status truth."""
import copy
import hashlib
import json
import tempfile
from pathlib import Path

from compose_real61 import (
    BASE_COUNT, REQUIRED, SUFFIX, checked_manifest, compose, git_blob, klass, sha
)

BASE_SHA = "a6020867fac80fa3b2ca47478625873fc6f3678e"
SCRIPT_ROWS = [
    ("ReplicatedStorage/EGGRUMBLE_HudPresentationPolicy", "ModuleScript", 829),
    ("ServerScriptService/EGGRUMBLE_MapVisibilityPolicy", "ModuleScript", 829),
    ("ServerScriptService/EGGRUMBLE_MapIntelBridge", "Script", 829),
    ("StarterPlayer/StarterPlayerScripts/EGGRUMBLE_HudIntelRuntime", "LocalScript", 829),
    ("ServerScriptService/GQ8_TradeJournalContract", "ModuleScript", 838),
    ("StarterPlayer/StarterPlayerScripts/GQ8_TradeReview", "LocalScript", 838),
]


def prepared(root: Path):
    src = root / "parent55"
    src.mkdir()
    tree = {"$className": "DataModel"}
    receipt_rows = []
    routes = sorted(REQUIRED)
    while len(routes) < BASE_COUNT:
        routes.append(("ServerScriptService", f"GQ8_TestOriginal{len(routes):02d}"))
    for route in routes:
        leaf = src.joinpath("sources", *route[:-1], route[-1] + ".luau")
        leaf.parent.mkdir(parents=True, exist_ok=True)
        body = ("-- ORIGINAL " + "/".join(route) + "\nreturn {}\n").encode()
        leaf.write_bytes(body)
        node = tree
        for depth, part in enumerate(route[:-1]):
            node = node.setdefault(part, {} if depth == 0 else {"$className": "Folder"})
        node[route[-1]] = {"$path": leaf.relative_to(src).as_posix()}
        receipt_rows.append({"route": "/".join(route), "sha256": sha(body),
                             "bytes": len(body), "class": "ModuleScript"})
    project = src / "EGGRUMBLE_REAL55.project.json"
    project.write_text(json.dumps({"name": "FakeParent55", "tree": tree}))
    receipt = root / "B_REAL55_RECEIPT.json"
    receipt.write_text(json.dumps({
        "source_profile": "eggrumble_v3_real55",
        "selected_official_branch_sha": BASE_SHA,
        "selected_real55_count": 55, "official_rc_adopted": True,
        "sources": receipt_rows
    }))
    inputs = {}
    new = []
    for i, (route, cls, pr) in enumerate(SCRIPT_ROWS):
        body = f"-- NEW {route}\nreturn {{}}\n".encode()
        f = root / (f"candidate{i:02d}" + SUFFIX[cls])
        f.write_bytes(body)
        inputs[tuple(route.split("/"))] = f
        new.append({"pr": pr, "head": "f" * 40, "route": route,
                    "path": "exact/author.luau", "blob": git_blob(body),
                    "class": cls})
    manifest = {
        "schema": "GQ8_REAL61_HUD_TRADE_CROSS_LANE_SOURCE_CANDIDATE_V1",
        "baseline_official_head": BASE_SHA,
        "source_profile": "eggrumble_v3_real61_candidate",
        "parent_source_count": 55, "source_count": 61,
        "adoption_status": "CANDIDATE_NOT_FORMALLY_ADOPTED",
        "new_sources": new,
        "pending_intersection": [{"pr": 840}, {"pr": 841}],
        "acceptance": {"shop_trade_live": False, "purchases": False,
                       "roblox_published": False}
    }
    mf = root / "manifest.json"
    mf.write_text(json.dumps(manifest))
    return project, receipt, manifest, mf, inputs


def must_fail(fn, marker):
    try:
        fn()
    except (ValueError, KeyError) as e:
        assert marker in str(e), (marker, str(e))
        return
    raise AssertionError("RED_MUTANT_WAS_NOT_BLOCKED_" + marker)


with tempfile.TemporaryDirectory(prefix="gq8-real61-gate-") as t:
    root = Path(t)
    p, r, m, mf, inputs = prepared(root)
    checked_manifest(mf)
    out = root / "good61"
    result = compose(p, r, m, inputs, out)
    assert len(result["scripts"]) == 61
    assert result["official_rc_adopted"] is False
    assert result["original55_bytes_and_class_preserved"] is True
    assert result["pending_unmerged_prs"] == [840, 841]
    print("PASS_01_TRUE_REAL61_SOURCE_SELECTION_55_UNCHANGED")

    bad = copy.deepcopy(m)
    bad["new_sources"][0]["route"] = bad["new_sources"][1]["route"]
    mf.write_text(json.dumps(bad))
    must_fail(lambda: checked_manifest(mf), "RED_DUPLICATE_ADDITION")
    print("PASS_02_DUPLICATE_ROUTE_REJECTED")

    bad = copy.deepcopy(m)
    bad["pending_intersection"] = [{"pr": 840}]
    mf.write_text(json.dumps(bad))
    must_fail(lambda: checked_manifest(mf), "RED_HIDDEN_PENDING_AUTHOR_WORK")
    print("PASS_03_PENDING_OWNER_NOT_HIDDEN")

    bad = copy.deepcopy(m)
    bad["acceptance"]["shop_trade_live"] = True
    mf.write_text(json.dumps(bad))
    must_fail(lambda: checked_manifest(mf), "RED_UNSAFE_PUBLICATION_CLAIM")
    print("PASS_04_FAKE_LIVE_TRADE_REJECTED")

    key = tuple(SCRIPT_ROWS[0][0].split("/"))
    inputs[key].write_bytes(b"-- corrupted candidate")
    must_fail(lambda: compose(p, r, m, inputs, root / "bad_blob"),
              "RED_AUTHOR_GIT_BLOB_OR_CLASS_DRIFT")
    print("PASS_05_SOURCE_BLOB_MUTATION_REJECTED")
    inputs[key].write_bytes(f"-- NEW {SCRIPT_ROWS[0][0]}\nreturn {{}}\n".encode())

    rc = json.loads(r.read_text())
    rc["sources"][0]["sha256"] = "0" * 64
    r.write_text(json.dumps(rc))
    must_fail(lambda: compose(p, r, m, inputs, root / "bad_receipt"),
              "RED_ORIGINAL55_SOURCE_CLASS_OR_HASH_DRIFT")
    print("PASS_06_OFFICIAL_PARENT_MUTATION_REJECTED")

    rc["sources"][0]["sha256"] = sha(
        p.parent.joinpath("sources", *tuple(rc["sources"][0]["route"].split("/"))[:-1],
                          rc["sources"][0]["route"].split("/")[-1] + ".luau").read_bytes())
    r.write_text(json.dumps(rc))
    key = ("ServerScriptService", "GQ8_TradeJournalContract")
    inputs[key].write_text("return DataStoreService.UpdateAsync('paid')\n")
    # Temporarily change only the signed blob lock to exercise secondary authority protection.
    bad = copy.deepcopy(m)
    bad["new_sources"][4]["blob"] = git_blob(inputs[key].read_bytes())
    must_fail(lambda: compose(p, r, bad, inputs, root / "bad_trade"),
              "RED_TRADE_PREVIEW_GRANT_OR_PAYMENT")
    print("PASS_07_UNAUTHORIZED_TRADE_WRITE_REJECTED")

print("GQ8_REAL61_CROSS_CANDIDATE_7_NEGATIVE_AND_PRESERVATION_GATES_PASS")
