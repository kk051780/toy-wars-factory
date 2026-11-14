#!/usr/bin/env python3
"""#372 FB-015 PRIVATE composition: #381 hit-cue slash + #374 minion art.

Never touches official branch or main. Parent assembled private67 remains
unchanged. Source-locked additional server cosmetic script is copied into a
separate private68 distribution and validated before atomic directory rename.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import fcntl
import os
from pathlib import Path
import shutil
import tempfile
from fb015_fs_guard import strict_inventory, reject_symlink_ancestors, transaction_parent_locks, atomic_json

ROOT = Path(__file__).resolve().parent
FEATURE = "ART_MINION_THREE_SILHOUETTES_V1"
SLASH = "ART_COMBAT_SLASH_READONLY_V1"
AUTHOR = ROOT / "features/art_minion/MinionArtSilhouette.server.luau"
DEST = "server/ArtMinionSilhouette.server.luau"
PIN = "4d0aac99d670ca4364a7368255d1edc63d28b3a0"
HIT_CUE_BLOB = "a2d07936bd9fe5bdf3630498c39d61d5a8560d99"
SLASH_CLIENT_BLOB = "17c6a9a3404e913b279b348e3b981ac61bfd1b24"
BASE = 67
MANIFEST = ".P0D_FB015_COMPOSITE_EXACT_MANIFEST.json"
TRUST_SUFFIX = ".fb015_external_receipt.json"

def receipt_path(out: Path) -> Path:
    return out.with_name(out.name + TRUST_SUFFIX)

def external_receipt(out: Path, dist: Path) -> dict:
    path=receipt_path(out)
    require(path.is_file() and not path.is_symlink(),
            "MISSING_TRUSTED_EXTERNAL_COMPOSITE_RECEIPT")
    record=json.loads(path.read_text("utf8"))
    require(record.get("id")=="P0D_FB015_COMPOSITE_EXTERNAL_RECEIPT_V1"
            and record.get("input")==str(dist)
            and record.get("output")==str(out)
            and isinstance(record.get("files"),dict),
            "INVALID_TRUSTED_EXTERNAL_COMPOSITE_RECEIPT")
    return record


def require(ok, reason):
    if not ok:
        raise RuntimeError(reason)

def blob(raw: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()

def files(dist: Path):
    src = dist / "src"
    return {p.relative_to(src).as_posix(): p.read_bytes()
            for p in sorted(src.rglob("*.luau"))}

def baseline(dist: Path):
    strict_inventory(dist)  # No external symlink targets may enter private68.
    source = files(dist)
    require(len(source) == BASE and DEST not in source, "REQUIRE_CLEAN_PRIVATE67")
    require(blob(source["server/MusouHorde.luau"]) == HIT_CUE_BLOB,
            "SOURCE_PIN_HORDE_SIGNAL_DRIFT")
    require(blob(source["client/ArtCombatSlash.client.luau"]) == SLASH_CLIENT_BLOB,
            "SOURCE_PIN_SLASH_CLIENT_DRIFT")
    require(source["server/Game.server.luau"].count(
        b"remote.OnServerEvent:Connect(") == 1, "NONUNIQUE_GAME_REMOTE")
    pins = {p: blob(v) for p, v in sorted(source.items())}
    locks = {}
    for key, name in (("source", "SOURCE_LOCK.json"),
                      ("feature", "RC_FEATURE_LOCK.json")):
        locks[key] = json.loads((dist / name).read_text("utf8"))
    require(locks["source"]["total_scripts"] == BASE and
            locks["source"]["blobs"] == pins, "SOURCE_LOCK_DRIFT")
    require(locks["feature"]["total_sources"] == BASE and
            locks["feature"]["source_gitblobs"] == pins, "FEATURE_LOCK_DRIFT")
    require(locks["feature"]["feature_flags"].get(SLASH) is True,
            "MISSING_SLASH_FEATURE")
    require(not locks["feature"]["feature_flags"].get(FEATURE),
            "DUPLICATE_MINION_FEATURE")
    proj = json.loads((dist / "default.project.json").read_text("utf8"))
    require(proj["tree"]["ServerScriptService"]["TrapRaidersS1"]["$path"]
            == "src/server", "SERVER_AUTO_MAPPING_DRIFT")
    require(proj["tree"]["StarterPlayer"]["StarterPlayerScripts"]
            ["ArtCombatSlash"]["$path"] ==
            "src/client/ArtCombatSlash.client.luau", "SLASH_ROJO_MAP_DRIFT")
    author = AUTHOR.read_bytes()
    require(blob(author) == PIN, "ART_MINION_SOURCE_DRIFT")
    for token in (b"KNIGHT_HELMET", b"WRAITH_HOOD", b"BRUTE_TUSK_",
                  b"ELITE_MASK", b"P0D_ART_MINION_V1",
                  b"mobsFolder.ChildAdded:Connect(",
                  b'P0D_ART_HIT_BUS_V1',
                  b'artHitBus.Event:Connect('):
        require(token in author, "ART_MINION_MISSING_ANCHOR_"+repr(token))
    for token in (b"FireServer(", b"TakeDamage(", b"UpdateAsync(",
                  b"OnServerEvent:Connect(", b"DataStoreService"):
        require(token not in author, "ART_MINION_AUTHORITIES_FORBIDDEN_"+repr(token))
    return source, pins, locks, author

def manifest_contents(stage: Path) -> dict[str, str]:
    return strict_inventory(stage, exclude=MANIFEST)

def generate_manifest(stage: Path, dist: Path, out: Path):
    data = {
        "id": "P0D_FB015_COMPOSITE_PRIVATE68_EXACT_TREE",
        "input": str(dist),
        "output": str(out),
        "files": manifest_contents(stage),
    }
    (stage / MANIFEST).write_text(
        json.dumps(data, ensure_ascii=False, sort_keys=True, indent=2)+"\n", "utf8")

def verify_private_output(out: Path, dist: Path):
    mf = out / MANIFEST
    require(mf.is_file(), "ROLLBACK_REFUSED_NOT_OUR_PRIVATE68")
    record = json.loads(mf.read_text("utf8"))
    require(record.get("id") == "P0D_FB015_COMPOSITE_PRIVATE68_EXACT_TREE",
            "ROLLBACK_REFUSED_WRONG_MANIFEST")
    require(record.get("output") == str(out) and record.get("input") == str(dist),
            "ROLLBACK_REFUSED_WRONG_INPUT_OUTPUT_IDENTITY")
    require(record.get("files") == manifest_contents(out),
            "ROLLBACK_REFUSED_ADDED_OR_MODIFIED_OR_MISSING_FILE")
    independent=external_receipt(out,dist)
    require(independent["files"] == strict_inventory(out),
            "EXTERNAL_COMPOSITE_INVENTORY_MISMATCH")
    require(independent["files"].get(MANIFEST) is not None,
            "EXTERNAL_RECEIPT_MUST_BIND_INTERNAL_MANIFEST")
    return record

def validate_partial_tombstone(tombstone: Path, record: dict) -> None:
    # An interrupted deletion may have removed some original files. The
    # remaining files must ALL match the recorded original bytes; never
    # delete a newly-added or modified user file on retry.
    expected=record["files"]
    observed=strict_inventory(tombstone)
    require(all(path in expected and sha == expected[path]
                for path,sha in observed.items()),
            "TOMBSTONE_EXTRA_OR_MODIFIED_FILE_ROLLBACK_REFUSED")


def _compose_locked(dist: Path, out: Path, enabled: bool):
    dist = dist.resolve()
    out = out.resolve()
    require(out != dist and out not in dist.parents and dist not in out.parents,
            "PRIVATE_OUTPUT_MUST_BE_SEPARATE")
    # An interrupted OFF is resumed only from our own pre-authorized tombstone.
    journal = out.with_name(out.name + ".fb015_delete_journal.json")
    tombstone = out.with_name(out.name + ".fb015_deleting")
    trusted=receipt_path(out)
    if not enabled:
        if tombstone.exists():
            require(not out.exists() and journal.is_file(),
                    "AMBIGUOUS_COMPOSITE_OFF_RETRY")
            record = json.loads(journal.read_text("utf8"))
            require(record.get("input") == str(dist)
                    and record.get("output") == str(out)
                    and record.get("id") == "P0D_FB015_COMPOSITE_PRIVATE68_EXACT_TREE",
                    "INVALID_COMPOSITE_DELETE_JOURNAL")
            independent=external_receipt(out,dist)
            validate_partial_tombstone(tombstone, independent)
            shutil.rmtree(tombstone)
            journal.unlink()
            trusted.unlink()
            print("ART_MINION_COMBO_INTERRUPTED_OFF_CLEANUP_RECOVERED")
            return True
        if not out.exists():
            if journal.is_file():
                record=json.loads(journal.read_text("utf8"))
                require(record.get("id")=="P0D_FB015_COMPOSITE_PRIVATE68_EXACT_TREE"
                        and record.get("input")==str(dist)
                        and record.get("output")==str(out),
                        "INVALID_COMPLETED_OFF_JOURNAL")
                require(external_receipt(out,dist).get("files"),
                        "MISSING_COMPOSITE_EXTERNAL_RECOVERY_RECEIPT")
                journal.unlink()
                trusted.unlink()
                print("ART_MINION_COMBO_COMPLETED_OFF_JOURNAL_RECOVERED")
                return True
            print("ART_MINION_COMBO_OFF_ZERO_WRITE")
            return False
        if journal.exists():
            # Crash after writing journal but before renaming the output.
            prior = json.loads(journal.read_text("utf8"))
            current = verify_private_output(out, dist)
            require(prior == current, "INVALID_PREPARED_COMPOSITE_DELETE_JOURNAL")
            journal.unlink()
        record = verify_private_output(out, dist)
        require((out / "src" / DEST).is_file(), "NO_PRIVATE_MINION_TO_ROLLBACK")
        feature = json.loads((out / "RC_FEATURE_LOCK.json").read_text("utf8"))
        require(feature["feature_flags"].get(FEATURE) is True,
                "COMPOSITE_ROLLBACK_REFUSED_MISSING_ID")
        require(blob((out / "src" / DEST).read_bytes()) == PIN,
                "COMPOSITE_ROLLBACK_REFUSED_DRIFT")
        # Only after verifying EVERY file may we authorize removal.
        atomic_json(journal,record)
        os.rename(out, tombstone)
        independent=external_receipt(out,dist)
        validate_partial_tombstone(tombstone,independent)
        shutil.rmtree(tombstone)
        journal.unlink()
        trusted.unlink()
        print("ART_MINION_COMBO_PRIVATE68_OFF_RETAINED_ORIGINAL67")
        return True
    require(not tombstone.exists() and not journal.exists() and not trusted.exists(),
            "PENDING_OFF_RECOVERY_MUST_FINISH_BEFORE_ENABLE")
    require(out != dist and not out.exists(), "COMPOSITE_ALREADY_PRESENT")
    source, pins, locks, author = baseline(dist)
    before_inventory=strict_inventory(dist)
    with tempfile.TemporaryDirectory(prefix=".fb015_combo_stage_", dir=out.parent) as tmp:
        staged = Path(tmp) / out.name
        # Never follow an input symlink inserted after preflight.
        shutil.copytree(dist, staged, symlinks=True)
        require(strict_inventory(staged)==before_inventory,
                "COMPOSITE_COPIED_BASE_TREE_DRIFT")
        target = staged / "src" / DEST
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(author)
        next_pins = dict(pins)
        next_pins[DEST] = PIN
        receipt = {
            "id": "FB015_MINION_COMBAT_TWO_FEATURES_PRIVATE68",
            "feature_ids": [SLASH, FEATURE],
            "parents": ["PR381", "PR374"],
            "input_source_count": BASE,
            "output_source_count": BASE + 1,
            "unchanged_private67_source_count": BASE,
            "non_authority": True,
            "art_minion_gitblob": PIN,
            "horde_visual_signal_gitblob": HIT_CUE_BLOB,
            "slash_client_gitblob": SLASH_CLIENT_BLOB,
            "official_rc_adoption": False,
            "owner_studio_fun": "ART_NO_GO",
            "rollback": "remove separate private68 output; original private67 distribution untouched"
        }
        slock = locks["source"]
        flock = locks["feature"]
        slock["total_scripts"] = BASE + 1
        slock["blobs"] = next_pins
        slock["art_minion_combo"] = receipt
        flock["total_sources"] = BASE + 1
        flock["source_gitblobs"] = next_pins
        flock["feature_flags"][FEATURE] = True
        flock["art_minion_combo"] = receipt
        (staged / "SOURCE_LOCK.json").write_text(
            json.dumps(slock, ensure_ascii=False, indent=2) + "\n", "utf8")
        (staged / "RC_FEATURE_LOCK.json").write_text(
            json.dumps(flock, ensure_ascii=False, indent=2) + "\n", "utf8")
        actual = files(staged)
        require(len(actual) == BASE + 1, "COMPOSITE_68_COUNT_DRIFT")
        require(all(actual[k] == v for k, v in source.items()),
                "COMPOSITE_MODIFIED_BASE_SCRIPT")
        require({p: blob(v) for p, v in sorted(actual.items())} == next_pins,
                "COMPOSITE_SOURCE_BLOB_DRIFT")
        generate_manifest(staged, dist, out)
        # Created OUTSIDE the candidate: editing the in-tree manifest can no
        # longer authorize deletion of altered user files.
        atomic_json(trusted,{
            "id":"P0D_FB015_COMPOSITE_EXTERNAL_RECEIPT_V1",
            "input":str(dist), "output":str(out),
            "files":strict_inventory(staged),
        })
        os.rename(staged, out)
    print("P0D_ART_COMBAT_MINION_PRIVATE68_SOURCE_EXACT_67_PRESERVED_PASS")
    return True

def compose(dist: Path, out: Path, enabled: bool):
    reject_symlink_ancestors(dist)
    reject_symlink_ancestors(out)
    # Linux CI file lock serializes OFF against an in-flight enable.
    dist = dist.resolve()
    out = out.resolve()
    require(out != dist and out not in dist.parents and dist not in out.parents,
            "PRIVATE_OUTPUT_MUST_BE_SEPARATE")
    # Source and output share the source parent lock with APPLY, even when
    # output is in another directory. This covers cooperating processes.
    with transaction_parent_locks(dist.parent, out.parent):
        return _compose_locked(dist, out, enabled)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dist", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--enabled", choices=["true", "false"], required=True)
    args = ap.parse_args()
    compose(args.dist, args.out, args.enabled == "true")

if __name__ == "__main__":
    main()
