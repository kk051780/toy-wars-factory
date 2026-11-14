#!/usr/bin/env python3
"""#388 / #372 FB015: exact source private68 -> private69 visual motion candidate.

This is an independent, reversible A PREP candidate, never the official RC.
The latest pinned #387 68-source tree is copied, never modified.  All output files are
recorded by SHA256, new Luau by exact pinned Git blob.  OFF cannot delete any
unrelated or drifted files.  No main, RC branch, Roblox or remote operations.
"""
from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile

ROOT = Path(__file__).resolve().parent
AUTHOR = ROOT / "features/art_motion/NeutralMotion.client.luau"
DEST = "client/P0DNeutralMotion.client.luau"
FLAG = "FB015_MINION_MOTION_VISUAL_ONLY_V1"
BASE = 68
PIN = "866f21d327ffc3832748ecff4908b73c665d54e7"
MANIFEST = ".P0D_FB015_MOTION69_TREE.json"
MANIFEST_ID = "P0D_FB015_ART_MOTION_PRIVATE69_SOURCE_EXACT"
EXPECTED_PARENT_ID = "P0D_FB015_COMPOSITE_PRIVATE68_EXACT_TREE"
ORIGINAL_MINION = "4d0aac99d670ca4364a7368255d1edc63d28b3a0"
ORIGINAL_SLASH = "c8aa1c4ff740ca46b85fc78dbb99c2a2a82a6eba"
ORIGINAL_HORDE = "e48186a6d717a46c86ec395ffbe778d196ab182d"


def require(predicate: bool, reason: str) -> None:
    if not predicate:
        raise RuntimeError(reason)


def blob(raw: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()


def source_map(dist: Path) -> dict[str, bytes]:
    src = dist / "src"
    return {p.relative_to(src).as_posix(): p.read_bytes()
            for p in sorted(src.rglob("*.luau"))}


def manifest_files(stage: Path) -> dict[str, str]:
    output = {}
    for p in sorted(stage.rglob("*")):
        if p.is_symlink():
            raise RuntimeError("SYMLINK_FORBIDDEN_IN_ART_MOTION_TREE")
        if p.is_file() and p.relative_to(stage).as_posix() != MANIFEST:
            output[p.relative_to(stage).as_posix()] = hashlib.sha256(p.read_bytes()).hexdigest()
    return output


def preflight(parent: Path):
    require(parent.is_dir() and not parent.is_symlink(), "MISSING_PRIVATE68")
    parent_rec_path = parent / ".P0D_FB015_COMPOSITE_EXACT_MANIFEST.json"
    require(parent_rec_path.is_file(), "PARENT_PRIVATE68_MANIFEST_MISSING")
    parent_record = json.loads(parent_rec_path.read_text("utf8"))
    require(parent_record.get("id") == EXPECTED_PARENT_ID and
            parent_record.get("output") == str(parent), "WRONG_PRIVATE68_LINEAGE")
    exact = manifest_files(parent)
    exact.pop(parent_rec_path.name, None)
    # The parent manifest is intentionally excluded from its own SHA list.
    require(parent_record.get("files") == exact,
            "PRIVATE68_TREE_DRIFT_OR_UNRELATED_FILES")
    old = source_map(parent)
    require(len(old) == BASE and DEST not in old, "REQUIRE_REAL_PRIVATE68")
    pins = {key: blob(raw) for key, raw in sorted(old.items())}
    require(pins.get("server/ArtMinionSilhouette.server.luau") == ORIGINAL_MINION,
            "ORIGINAL_MINION_DRIFT")
    require(pins.get("client/ArtCombatSlash.client.luau") == ORIGINAL_SLASH,
            "ORIGINAL_SLASH_DRIFT")
    require(pins.get("server/MusouHorde.luau") == ORIGINAL_HORDE,
            "ORIGINAL_HORDE_DRIFT")
    require(old["server/Game.server.luau"].count(
        b"remote.OnServerEvent:Connect(") == 1, "SECOND_GAME_AUTHORITY")
    slock = json.loads((parent / "SOURCE_LOCK.json").read_text("utf8"))
    flock = json.loads((parent / "RC_FEATURE_LOCK.json").read_text("utf8"))
    require(slock.get("total_scripts") == BASE and slock.get("blobs") == pins,
            "SOURCE_LOCK68_DRIFT")
    require(flock.get("total_sources") == BASE and flock.get("source_gitblobs") == pins,
            "FEATURE_LOCK68_DRIFT")
    flags = flock.get("feature_flags", {})
    require(flags.get("ART_COMBAT_SLASH_READONLY_V1") is True and
            flags.get("ART_MINION_THREE_SILHOUETTES_V1") is True and
            not flags.get(FLAG), "MINION_COMBAT_PARENT_FLAGS_DRIFT")
    project = json.loads((parent / "default.project.json").read_text("utf8"))
    starters = project["tree"]["StarterPlayer"]["StarterPlayerScripts"]
    require(starters["ArtCombatSlash"]["$path"] ==
            "src/client/ArtCombatSlash.client.luau" and
            "P0DNeutralMotion" not in starters, "ROJO_MOTION_DUPLICATED")
    actual = AUTHOR.read_bytes()
    require(blob(actual) == PIN, "ART_MOTION_AUTHOR_BLOB_DRIFT")
    for term in (b"if not RunService:IsStudio() then return end",
                 b"P0D_ART_MINION_V1", b"MAX_MODELS = 16",
                 b"MAX_ACTIVE_COSMETIC_PARTS = 56", b"script.Destroying"):
        require(term in actual, "ART_MOTION_REQUIRED_ANCHOR_MISSING")
    for forbidden in (b"FireServer(", b"TakeDamage(", b"OnServerEvent",
                      b"DataStoreService", b"Instance.new(\"RemoteEvent\")",
                      b"Instance.new(\"ParticleEmitter\")",
                      b"Instance.new(\"Part\")"):
        require(forbidden not in actual, "MOTION_MUST_NOT_OWN_AUTHORITY")
    return old, pins, slock, flock, project, actual


def independent_expected_files(parent: Path) -> dict[str, str]:
    """Rebuild the complete 69-source byte identities from untouched parent68.

    We do NOT trust an editable manifest inside a candidate to authorize OFF.
    Only the deterministic parent tree, exact source blob and metadata changes
    made by this composer define files it is allowed to remove.
    """
    old, pins, slock, flock, project, author = preflight(parent)
    next_pins = dict(pins)
    next_pins[DEST] = PIN
    receipt = {
        "feature_id": FLAG, "parent": "#387 private68",
        "issue": "#388", "source_count": 69,
        "new_client_only_script": DEST,
        "studio": "NOT_TESTED", "android": "NOT_TESTED",
        "official_rc_adoption": False, "owner_acceptance": "ART_NO_GO",
        "rollback": "separate output only, parent68 byte-identical",
    }
    project["tree"]["StarterPlayer"]["StarterPlayerScripts"]["P0DNeutralMotion"] = {
        "$path": "src/" + DEST,
    }
    slock["total_scripts"] = 69
    slock["blobs"] = next_pins
    slock["motion69"] = receipt
    flock["total_sources"] = 69
    flock["source_gitblobs"] = next_pins
    flock["feature_flags"][FLAG] = True
    flock["motion69"] = receipt
    expected = manifest_files(parent)
    def sha(raw: bytes) -> str:
        return hashlib.sha256(raw).hexdigest()
    expected["src/" + DEST] = sha(author)
    expected["default.project.json"] = sha(
        (json.dumps(project, ensure_ascii=False, indent=2) + "\n").encode("utf8"))
    expected["SOURCE_LOCK.json"] = sha(
        (json.dumps(slock, ensure_ascii=False, indent=2) + "\n").encode("utf8"))
    expected["RC_FEATURE_LOCK.json"] = sha(
        (json.dumps(flock, ensure_ascii=False, indent=2) + "\n").encode("utf8"))
    return expected


def check_output(parent: Path, out: Path, identity: Path | None = None) -> None:
    require(out.is_dir() and not out.is_symlink(), "NO_MOTION69_OUTPUT")
    # During an interrupted OFF, the directory is moved to a tombstone, but
    # its signed manifest must still identify the original output path.
    expected_output = identity or out
    mf = out / MANIFEST
    require(mf.is_file(), "ROLLBACK_REFUSED_NOT_OUR_MOTION69")
    rec = json.loads(mf.read_text("utf8"))
    require(rec.get("id") == MANIFEST_ID and rec.get("input") == str(parent)
            and rec.get("output") == str(expected_output), "MOTION69_MANIFEST_ID_MISMATCH")
    actual = manifest_files(out)
    require(rec.get("files") == actual, "MOTION69_TREE_DRIFT_NO_REMOVAL")
    # Defense in depth: a rewritten self-manifest MUST NOT authorize deleting
    # unrelated files or altered baseline scripts.
    require(actual == independent_expected_files(parent),
            "MOTION69_INDEPENDENT_EXPECTED_TREE_DRIFT")
    src = out / "src" / DEST
    require(src.is_file() and blob(src.read_bytes()) == PIN,
            "MOTION69_SOURCE_PIN_MISMATCH")
    slock = json.loads((out / "SOURCE_LOCK.json").read_text("utf8"))
    flock = json.loads((out / "RC_FEATURE_LOCK.json").read_text("utf8"))
    require(slock.get("total_scripts") == 69 and flock.get("total_sources") == 69
            and flock.get("feature_flags", {}).get(FLAG) is True,
            "MOTION69_FEATURE_LOCK_MISMATCH")


def atomic_ticket(journal: Path, ticket: dict) -> None:
    """A crash during preparation cannot leave an unparseable active journal."""
    candidate = None
    try:
        with tempfile.NamedTemporaryFile(
                mode="w", encoding="utf8", prefix=".motion69_atomic_",
                suffix=".tmp", dir=journal.parent, delete=False) as tmp:
            candidate = Path(tmp.name)
            tmp.write(json.dumps(ticket, sort_keys=True) + "\n")
            tmp.flush()
            os.fsync(tmp.fileno())
        os.replace(candidate, journal)
    finally:
        if candidate is not None and candidate.exists():
            candidate.unlink()


def partial_tombstone_safe(parent: Path, tomb: Path, output: Path) -> None:
    """OFF retries only remove verified remaining OWN files after partial rmtree."""
    expected = independent_expected_files(parent)
    rec = {"id": MANIFEST_ID, "input": str(parent),
           "output": str(output), "files": expected}
    expected[MANIFEST] = hashlib.sha256(
        (json.dumps(rec, ensure_ascii=False, sort_keys=True, indent=2) + "\n")
        .encode("utf8")).hexdigest()
    observed = manifest_files(tomb)
    mf = tomb / MANIFEST
    if mf.is_file():
        observed[MANIFEST] = hashlib.sha256(mf.read_bytes()).hexdigest()
    require(all(name in expected and expected[name] == digest
                for name, digest in observed.items()),
            "MOTION69_PARTIAL_TOMBSTONE_UNRELATED_FILE_REFUSED")
    # Extra empty folders can also belong to someone else: refuse removal.
    valid_dirs = {"."}
    for name in expected:
        p = Path(name).parent
        while str(p) != ".":
            valid_dirs.add(p.as_posix())
            p = p.parent
    for directory in tomb.rglob("*"):
        if directory.is_dir():
            require(directory.relative_to(tomb).as_posix() in valid_dirs,
                    "MOTION69_UNEXPECTED_DIRECTORY_REFUSED")


def inner(parent: Path, out: Path, enabled: bool):
    parent = parent.resolve()
    out = out.resolve()
    require(parent != out and parent not in out.parents and out not in parent.parents,
            "MOTION69_INPUT_OUTPUT_OVERLAP")
    tomb = out.with_name(out.name + ".motion69_removing")
    journal = out.with_name(out.name + ".motion69_journal.json")
    if not enabled:
        ticket = {"input": str(parent), "output": str(out), "id": MANIFEST_ID}
        if tomb.exists():
            require(not out.exists() and journal.is_file(),
                    "MOTION69_RECOVERY_AMBIGUOUS")
            require(json.loads(journal.read_text("utf8")) == ticket,
                    "MOTION69_RECOVERY_TICKET_MISMATCH")
            # A crash may have deleted *some* original files. Validate every
            # remaining file against the independently rebuilt exact allowlist.
            # An added/edited user file is never deleted on recovery.
            partial_tombstone_safe(parent, tomb, out)
            shutil.rmtree(tomb)
            journal.unlink()
            print("P0D_ART_MOTION69_INTERRUPTED_OFF_RECOVERED")
            return True
        if journal.exists():
            require(json.loads(journal.read_text("utf8")) == ticket,
                    "MOTION69_RECOVERY_TICKET_MISMATCH")
            if out.exists():
                # Crash after writing journal and before the rename.
                check_output(parent, out)
                journal.unlink()
            else:
                # Crash after successful tomb deletion but before journal unlink.
                journal.unlink()
                print("P0D_ART_MOTION69_INTERRUPTED_OFF_FINISHED")
                return True
        if not out.exists():
            print("P0D_ART_MOTION69_OFF_ZERO_WRITE")
            return False
        check_output(parent, out)
        atomic_ticket(journal, ticket)
        os.rename(out, tomb)
        shutil.rmtree(tomb)
        journal.unlink()
        print("P0D_ART_MOTION69_OFF_RETAINED_PARENT68")
        return True

    require(not out.exists() and not tomb.exists() and not journal.exists(),
            "MOTION69_OUTPUT_ALREADY_PRESENT_OR_INTERRUPTED")
    require(parent.is_dir(), "MISSING_PRIVATE68")
    old, pins, slock, flock, project, actual = preflight(parent)
    with tempfile.TemporaryDirectory(prefix=".p0d_motion69_stage_", dir=out.parent) as tmp:
        stage = Path(tmp) / out.name
        shutil.copytree(parent, stage, symlinks=False)
        # Lock domain also holds parent68's own composer OFF. Re-validate the
        # immutable snapshot after the copy before making any output visible.
        require(manifest_files(stage) == manifest_files(parent),
                "MOTION69_PARENT_CHANGED_DURING_SNAPSHOT")
        target = stage / "src" / DEST
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(actual)
        project["tree"]["StarterPlayer"]["StarterPlayerScripts"]["P0DNeutralMotion"] = {
            "$path": "src/" + DEST,
        }
        (stage / "default.project.json").write_text(
            json.dumps(project, ensure_ascii=False, indent=2)+"\n", "utf8")
        next_pins = dict(pins)
        next_pins[DEST] = PIN
        receipt = {
            "feature_id": FLAG, "parent": "#387 private68",
            "issue": "#388", "source_count": 69,
            "new_client_only_script": DEST,
            "studio": "NOT_TESTED", "android": "NOT_TESTED",
            "official_rc_adoption": False, "owner_acceptance": "ART_NO_GO",
            "rollback": "separate output only, parent68 byte-identical",
        }
        slock["total_scripts"] = 69
        slock["blobs"] = next_pins
        slock["motion69"] = receipt
        flock["total_sources"] = 69
        flock["source_gitblobs"] = next_pins
        flock["feature_flags"][FLAG] = True
        flock["motion69"] = receipt
        (stage / "SOURCE_LOCK.json").write_text(
            json.dumps(slock, ensure_ascii=False, indent=2)+"\n", "utf8")
        (stage / "RC_FEATURE_LOCK.json").write_text(
            json.dumps(flock, ensure_ascii=False, indent=2)+"\n", "utf8")
        updated = source_map(stage)
        require(len(updated) == 69 and
                all(updated[name] == data for name, data in old.items()),
                "MOTION69_PARENT_SOURCE_CHANGED")
        require({key: blob(value) for key, value in sorted(updated.items())} ==
                next_pins, "MOTION69_NEW_SOURCE_LOCK_DRIFT")
        record = {"id": MANIFEST_ID, "input": str(parent),
                  "output": str(out), "files": manifest_files(stage)}
        (stage / MANIFEST).write_text(
            json.dumps(record, ensure_ascii=False, sort_keys=True, indent=2)+"\n", "utf8")
        os.rename(stage, out)
    try:
        check_output(parent, out)
    except Exception:
        # Do not report a completed candidate if parent provenance vanished.
        # Never delete an unverified candidate here; leave it quarantined.
        raise
    print("P0D_FB015_PRIVATE69_MOTION_SOURCE_EXACT_PARENT68_PRESERVED")
    return True


def compose(parent: Path, out: Path, enabled: bool):
    # Do not follow path-level or ancestor symbolic links, including paths
    # that are not yet present. A symlink under an ancestor is also forbidden.
    for path in (parent.absolute(), out.absolute()):
        require(not any(segment.is_symlink() for segment in (path, *path.parents)),
                "MOTION69_INPUT_OR_OUTPUT_SYMLINK_FORBIDDEN")
    parent = parent.resolve()
    out = out.resolve()
    require(out != parent and out not in parent.parents and parent not in out.parents,
            "MOTION69_INPUT_OUTPUT_OVERLAP")
    # The private68 builder locks the containing DIRECTORY via flock; take
    # that SAME lock so its OFF cannot remove parent68 during our compose/OFF.
    # Restrict to sibling output to guarantee a shared filesystem lock domain.
    require(parent.parent == out.parent, "MOTION69_PARENT_LOCK_DOMAIN_MISMATCH")
    fd = os.open(parent.parent, os.O_RDONLY | os.O_DIRECTORY)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        return inner(parent, out, enabled)
    finally:
        fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--dist", required=True, type=Path)
    p.add_argument("--out", required=True, type=Path)
    p.add_argument("--enabled", required=True, choices=["true", "false"])
    args = p.parse_args()
    compose(args.dist, args.out, args.enabled == "true")
