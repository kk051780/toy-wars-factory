#!/usr/bin/env python3
"""Replay downloaded REAL70 A-only artifact; never confer RC or ART acceptance."""
import argparse
import hashlib
import json
import shutil
from pathlib import Path
from tempfile import TemporaryDirectory
from xml.etree import ElementTree as ET

BASE = "e80973c354f14a0d0088577f3cc1a875454f0f8f"
ROUTE = "StarterPlayer/StarterPlayerScripts/EGGRUMBLE_CastleApproachMatte"
FEATURE = "GQ470_FB015_CASTLE_APPROACH_MATTE_20261121"
PACKET = "B220_CASTLE_APPROACH_ONE_NEW_CLIENT_SOURCE_NOT_FORMAL"
PLACE = "GQ470_CASTLE_APPROACH_ON70_NOT_FORMAL.rbxlx"
SOURCE = "on70/sources/" + ROUTE + ".client.luau"
B_SOURCE = "on70/" + PACKET + "/selected_sources/" + ROUTE + ".client.luau"
MANIFEST = "on70/" + PACKET + "/SOURCE_SELECT_MANIFEST.json"
RECEIPT = "on70/GQ470_CASTLE_APPROACH_SOURCE_RECEIPT.json"
ART = "ART_CHECK_REPORT.json"
EXPECTED = {PLACE, SOURCE, B_SOURCE, MANIFEST, RECEIPT, ART}


def require(value, label):
    if not value:
        raise ValueError("RED_GQ470_POSTUPLOAD_" + label)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def verify(root, source_path):
    root = root.resolve()
    present = {p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file()}
    require(present == EXPECTED, "EXACT_SIX_ARTIFACT_PATHS")
    require(not any(p.is_symlink() for p in root.rglob("*")), "NO_SYMLINKS")
    raw = (root / SOURCE).read_bytes()
    require(raw == source_path.read_bytes(), "REPO_SOURCE_MUST_MATCH")
    require((root / B_SOURCE).read_bytes() == raw, "B_PACKET_SOURCE_MUST_MATCH")
    place = (root / PLACE).read_bytes()
    man = read_json(root / MANIFEST)
    rec = read_json(root / RECEIPT)
    art = read_json(root / ART)
    require(man.get("schema") == "GQ470_CASTLE_APPROACH_B220_SOURCE_SELECT_V1"
            and man.get("feature_id") == FEATURE
            and man.get("formal_base_sha") == BASE
            and man.get("formal_branch") == "rc/p0d-s1-kids-rc01"
            and man.get("source_profile") == "PRIVATE_COMPANION_REAL69_TO_70_A_ONLY"
            and man.get("new_script_route") == ROUTE
            and man.get("new_script_class") == "LocalScript"
            and man.get("new_source_path") == "selected_sources/" + ROUTE + ".client.luau"
            and man.get("new_source_sha256") == digest(raw)
            and man.get("new_source_bytes") == len(raw)
            and man.get("candidate_place_sha256") == digest(place)
            and man.get("candidate_place_bytes") == len(place)
            and man.get("original_selected_sources_preserved") == 69
            and man.get("candidate_selected_sources") == 70
            and man.get("source_only") is True
            and man.get("formal_integrated") is False
            and man.get("owner_accepted") is False
            and man.get("art_status") == "ART_NO_GO"
            and man.get("studio_android_fun") == "NOT_TESTED"
            and man.get("b_admission") == "DEFER_P0_910_FIRST_PENDING_CLAIM_AND_250"
            and man.get("needs_b220_authenticated_fresh_head_nonforce_cas") is True,
            "MANIFEST_UNVERIFIED")
    require(rec.get("base_head") == BASE
            and rec.get("feature_id") == FEATURE
            and rec.get("added_selected_script") == ROUTE
            and rec.get("added_script_class") == "LocalScript"
            and rec.get("added_script_sha256") == digest(raw)
            and rec.get("stage") == "A_SOURCE_CANDIDATE_NOT_FORMAL"
            and rec.get("original_sources_preserved") == 69
            and rec.get("candidate_source_count") == 70
            and rec.get("formal_integrated") is False
            and rec.get("owner_accepted") is False
            and rec.get("art_gate") == "ART_NO_GO",
            "RECEIPT_UNVERIFIED")
    images = art.get("comparison_images", [])
    require(art.get("feature_id") == FEATURE
            and art.get("base_head") == BASE
            and art.get("candidate_place_sha256") == digest(place)
            and art.get("candidate_place_bytes") == len(place)
            and art.get("comparison_image_count") == 0
            and len(images) == 32
            and all(i.get("exists") is False and i.get("human_score") is None for i in images)
            and art.get("art_gate") == "ART_NO_GO"
            and art.get("product_gate") == "PRODUCT_NO_GO"
            and art.get("formal_rc_integrated") is False
            and art.get("owner_accepted") is False
            and art.get("studio_solo") == "NOT_TESTED"
            and art.get("studio_2client") == "NOT_TESTED",
            "ART_UNVERIFIED")
    items = []
    selected = []
    for element in ET.fromstring(place).iter("Item"):
        property_source = element.find('./Properties/ProtectedString[@name="Source"]')
        if property_source is None:
            property_source = element.find('./Properties/string[@name="Source"]')
        if property_source is None:
            continue
        items.append(element)
        name = element.find('./Properties/string[@name="Name"]')
        if name is not None and name.text == "EGGRUMBLE_CastleApproachMatte":
            selected.append((element, property_source))
    require(len(items) == 70 and len(selected) == 1, "ROJO_ACTUAL_70_SCRIPTS")
    item, property_source = selected[0]
    require(item.get("class") == "LocalScript"
            and property_source.text is not None
            and property_source.text.strip() == raw.decode("utf-8").strip(),
            "ROJO_SELECTED_SOURCE_AND_CLASS")
    return {"schema": "GQ470_POSTUPLOAD_REPLAY_V1", "candidate_place_sha256": digest(place),
            "private_place_bytes": len(place), "source_sha256": digest(raw),
            "native_rojo_verified_in_parent_job": True,
            "replayed_real_script_count": len(items),
            "formal_rc_integrated": False, "art_gate": "ART_NO_GO"}


def negatives(root, source_path):
    mutations = [
        (MANIFEST, lambda a: json.dumps({**json.loads(a), "formal_integrated": True}).encode()),
        (MANIFEST, lambda a: json.dumps({**json.loads(a), "new_source_sha256": "forged"}).encode()),
        (RECEIPT, lambda a: json.dumps({**json.loads(a), "original_sources_preserved": 68}).encode()),
        (SOURCE, lambda a: a + b"\n-- forged"),
        (B_SOURCE, lambda a: a + b"\n-- forged"),
        (PLACE, lambda a: a.replace(b"MAX_CASTLES", b"MAX_FORGED_CASTLES", 1)),
        (ART, lambda a: json.dumps({**json.loads(a), "art_gate": "ART_GO"}).encode()),
        (MANIFEST, lambda a: json.dumps({**json.loads(a), "b_admission": "READY_FOR_AUTO_MERGE"}).encode()),
    ]
    for rel, mutate in mutations:
        with TemporaryDirectory() as temp:
            clone = Path(temp) / "artifact"
            shutil.copytree(root, clone)
            target = clone / rel
            original = target.read_bytes()
            changed = mutate(original)
            require(changed != original, "NEGATIVE_FIXTURE_NO_CHANGE")
            target.write_bytes(changed)
            try:
                verify(clone, source_path)
            except (ValueError, ET.ParseError):
                continue
            raise ValueError("RED_GQ470_POSTUPLOAD_MUTANT_ACCEPTED_" + rel)
    return len(mutations)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--artifact", type=Path, required=True)
    ap.add_argument("--source", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    opt = ap.parse_args()
    data = verify(opt.artifact, opt.source)
    data["rejected_mutants"] = negatives(opt.artifact, opt.source)
    require(not opt.out.exists(), "OVERWRITE_REPORT")
    opt.out.write_text(json.dumps(data, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print("GQ470_INDEPENDENT_POSTUPLOAD_70_SOURCE_CLASS_8_MUTANTS_PASS")
    print(json.dumps(data, sort_keys=True))
