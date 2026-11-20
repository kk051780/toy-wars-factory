#!/usr/bin/env python3
"""Source-selective, rollbackable EGGRUMBLE V3 TEAM/BR ITEM ownership fence.

Does NOT write to the owner branch, main or official RC. Inputs MUST be exact
author-vetted Git blobs. This emits only candidate scripts for #482/#489 review.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

FEATURE = "GQ_V3_ITEM_MODE_OWNERSHIP_20261116"
ORIGINAL_HOST_BLOB = "7162b209bf67b74a71553217f3f744e072a0365d"
ORIGINAL_ITEM_BLOB = "107046cb0bf81fed9e3cba1699ada31571e44a22"
HOST_NAME = "EGGRUMBLE_LobbyCastleModesPreview.server.luau"
ITEM_NAME = "EGGRUMBLE_FieldItemPickups.luau"
MARKER = "-- GQ_V3_ITEM_MODE_OWNERSHIP_20261116"

ITEM_ANCHOR = "local function canUse(player:Player,session:any):boolean\n"
HOST_ANCHOR = " sessions[mode]=session\n"

ITEM_INSERT = """ -- GQ_V3_ITEM_MODE_OWNERSHIP_20261116: a stale castle roster is not a live queue.
 -- Authorization is a server-only closure from the original TEAM/BR host.
 if session and (session.mode=="TEAM" or session.mode=="BATTLE_ROYALE") then
  local authorize=session.canCollectWorldItem
  if type(authorize)~="function" then return false end
  local ok,allowed=pcall(authorize,player)
  if not ok or allowed~=true then return false end
 end
"""

HOST_INSERT = """  -- GQ_V3_ITEM_MODE_OWNERSHIP_20261116: no second match/ITEM authority.
  session.canCollectWorldItem=function(actor:Player):boolean
   return actor.Parent~=nil
    and sessions[mode]==session
    and joined[actor.UserId]==mode
    and session.rules~=nil
    and session.rules.phase=="ACTIVE"
  end
"""

def git_blob_sha(raw: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()

def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()

def guarded_insert(source: str, anchor: str, addition: str, label: str) -> str:
    if MARKER in source:
        raise ValueError(f"{label}: candidate already applied; reject duplicate")
    if source.count(anchor) != 1:
        raise ValueError(f"{label}: anchor missing/duplicated; stop on author drift")
    return source.replace(anchor, anchor + addition, 1)

def patch_sources(host: str, item: str) -> tuple[str, str]:
    if "session.canCollectWorldItem" in host or "session.canCollectWorldItem" in item:
        raise ValueError("a different item-ownership hook already exists; author review")
    if "local function canUse(player:Player,session:any):boolean" not in item:
        raise ValueError("not the source-author FieldItemPickups")
    if "sessions[mode]=session" not in host or "joined[p.UserId]" not in host:
        raise ValueError("not the source-author two-mode Lobby host")
    return (
        guarded_insert(host, HOST_ANCHOR, HOST_INSERT, "lobby"),
        guarded_insert(item, ITEM_ANCHOR, ITEM_INSERT, "item"),
    )

def generate(host_path: Path, item_path: Path, output: Path,
             host_blob: str = ORIGINAL_HOST_BLOB,
             item_blob: str = ORIGINAL_ITEM_BLOB) -> dict:
    host_bytes, item_bytes = host_path.read_bytes(), item_path.read_bytes()
    real_host, real_item = git_blob_sha(host_bytes), git_blob_sha(item_bytes)
    if real_host != host_blob or real_item != item_blob:
        raise ValueError(
            f"SOURCE_LOCK mismatch: host {real_host} != {host_blob}; "
            f"item {real_item} != {item_blob}; no artifacts written"
        )
    # Check before creating output: fail closed on mismatched source/author.
    patched_host, patched_item = patch_sources(
        host_bytes.decode("utf-8"), item_bytes.decode("utf-8")
    )
    if output.exists() and any(output.iterdir()):
        raise ValueError("refuse to overwrite an existing non-empty candidate directory")
    output.mkdir(parents=True, exist_ok=True)
    files = [(HOST_NAME, patched_host), (ITEM_NAME, patched_item)]
    for name, contents in files:
        (output / name).write_text(contents, encoding="utf-8", newline="")
    manifest = {
        "feature_id": FEATURE,
        "state": "PRIVATE_SOURCE_CANDIDATE_NOT_OFFICIAL_RC",
        "owner_original": "#482 Game / #489 ITEM (and #517 HEAL overlay on author ACK)",
        "source_lock": {"host_git_blob": real_host, "item_git_blob": real_item},
        "candidate_sha256": {
            name: sha256(contents.encode("utf-8")) for name, contents in files
        },
        "source_changes": 2,
        "new_authorities": 0,
        "rollback": "discard these two emitted overlay files; restore exact input Git blobs",
        "studio_android_owner": "NOT_TESTED",
    }
    (output / "candidate_manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return manifest

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", type=Path, required=True)
    parser.add_argument("--item", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--host-blob", default=ORIGINAL_HOST_BLOB)
    parser.add_argument("--item-blob", default=ORIGINAL_ITEM_BLOB)
    args = parser.parse_args()
    print(json.dumps(generate(args.host, args.item, args.out,
                              args.host_blob, args.item_blob), indent=2))

if __name__ == "__main__":
    main()
