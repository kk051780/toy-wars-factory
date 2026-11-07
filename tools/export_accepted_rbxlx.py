#!/usr/bin/env python3
"""Create a source-pinned, UNVERIFIED CURRENT four-toy+victory XML from isolated QA branch.

No HTTP, Roblox credentials, Studio install, or game-source modifications. This
is a packaging step only. Independent security review and actual Roblox engine
validation remain mandatory before the XML can be deployed to a private place.
"""
from __future__ import annotations
import hashlib
import json
import re
from pathlib import Path
from xml.etree import ElementTree as ET

REPO = "kk051780/toy-wars-factory"
PINNED_QA_HEAD = "261686e05741b42806c8471243a8740aa7fe98b6"
EXPECTED = (
    ("ReplicatedStorage", "ToyWarsBalance", "ModuleScript", "src/ToyWarsBalance.lua", "ede62318d0c51bee1a8f6d086098169729d8bc16"),
    ("ServerScriptService", "ToyWarsServer", "Script", "src/ToyWarsServer.server.lua", "6ffb707142cebde26776945dff584fd322086653"),
    ("ServerScriptService", "ToyWarsSmokeTest", "Script", "src/ToyWarsSmokeTest.server.lua", "ccba431909c664909e2680785648d0402fedf3c3"),
    ("StarterPlayer/StarterPlayerScripts", "ToyWarsHUD", "LocalScript", "src/ToyWarsHUD.client.lua", "05d72aae6924cc5d93fe14595e9af2cdeb4f73fd"),
)
XML_NAME = "twf_4toy_junk_captain_NOT_ENGINE_VERIFIED.rbxlx"
RECEIPT_NAME = "twf_4toy_junk_captain_UNTRUSTED_receipt.json"

class ExportBlocked(ValueError):
    pass

def _blob(raw: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()

def _require(condition: bool, reason: str):
    if not condition:
        raise ExportBlocked(reason)

def read_pinned_sources(root: Path) -> dict[str, bytes]:
    """Pin exact combined-game blobs; reject stale/symlinked code."""
    root = Path(root)
    result = {}
    for _, _, _, relative, expected_blob in EXPECTED:
        p = root / relative
        _require(not p.is_symlink() and p.is_file(), "missing or symlinked pinned candidate source")
        raw = p.read_bytes()
        _require(0 < len(raw) <= 100_000 and _blob(raw) == expected_blob,
                 "source differs from exact candidate Git blob")
        try:
            raw.decode("utf-8", errors="strict")
        except UnicodeDecodeError as e:
            raise ExportBlocked("invalid source encoding") from e
        _require(not ({*raw} & set(range(0, 9))) and b"\x0b" not in raw and b"\x0c" not in raw,
                 "invalid XML control byte in source")
        result[relative] = raw
    return result

def build_place(root: Path) -> tuple[bytes, dict]:
    """Deterministically assemble the approved 10-instance Roblox XML place."""
    files = read_pinned_sources(root)
    doc = ET.Element("roblox", {"version": "4"})
    nodes: dict[str, ET.Element] = {}
    refs = 0
    def add(parent: ET.Element, parent_path: str, klass: str, name: str, source: bytes | None = None):
        nonlocal refs
        refs += 1
        el = ET.SubElement(parent, "Item", {"class": klass, "referent": f"RBX{refs:032X}"})
        props = ET.SubElement(el, "Properties")
        ET.SubElement(props, "string", {"name": "Name"}).text = name
        if source is not None:
            ET.SubElement(props, "ProtectedString", {"name": "Source"}).text = source.decode("utf-8")
        path = (parent_path + "/" if parent_path else "") + name
        nodes[path] = el
        return el
    add(doc, "", "Workspace", "Workspace")
    replicated = add(doc, "", "ReplicatedStorage", "ReplicatedStorage")
    add(replicated, "ReplicatedStorage", "ModuleScript", "ToyWarsBalance", files[EXPECTED[0][3]])
    add(replicated, "ReplicatedStorage", "RemoteEvent", "ToyWarsSelectUnit")
    server = add(doc, "", "ServerScriptService", "ServerScriptService")
    add(server, "ServerScriptService", "Script", "ToyWarsServer", files[EXPECTED[1][3]])
    add(server, "ServerScriptService", "Script", "ToyWarsSmokeTest", files[EXPECTED[2][3]])
    starter = add(doc, "", "StarterPlayer", "StarterPlayer")
    scripts = add(starter, "StarterPlayer", "StarterPlayerScripts", "StarterPlayerScripts")
    add(scripts, "StarterPlayer/StarterPlayerScripts", "LocalScript", "ToyWarsHUD", files[EXPECTED[3][3]])
    assert refs == 10
    xml = ET.tostring(doc, encoding="utf-8", xml_declaration=True, short_empty_elements=True)
    _require(xml.startswith(b"<?xml") and xml.endswith(b"</roblox>"), "invalid generated XML")
    _require(len(xml) <= 10_000_000, "XML file too large")
    sources = {relative: {"git_blob_sha1": _blob(files[relative]),
                          "sha256": hashlib.sha256(files[relative]).hexdigest(),
                          "bytes": len(files[relative])}
               for _, _, _, relative, _ in EXPECTED}
    receipt = {
        "schema": 1,
        "status": "UNVERIFIED_QA_BRANCH_SOURCE_PINNED_XML_ONLY",
        "repository": REPO,
        "unmerged_source_branch_head_sha": PINNED_QA_HEAD,
        "artifact_filename": XML_NAME,
        "rbxlx_sha256": hashlib.sha256(xml).hexdigest(),
        "rbxlx_bytes": len(xml),
        "sources": sources,
        "instance_count": 10,
        "contains_actual_place": True,
        "studio_open_verified": False,
        "roblox_engine_verified": False,
        "roblox_upload_attested": False,
        "public_publish_authorized": False,
        "git_action_run_authenticated": False,
        "source_merge_verified": False,
        "no_secrets_or_network_used": True,
    }
    return xml, receipt

def actions_export_allowed(environ: dict[str, str]) -> bool:
    """Never mistake an arbitrary shell env for an accepted GitHub event."""
    if environ.get('GITHUB_ACTIONS') != 'true' or environ.get('GITHUB_REPOSITORY') != REPO:
        return False
    event = environ.get('GITHUB_EVENT_NAME')
    ref = environ.get('GITHUB_REF', '')
    return (event == 'push' and
            ref == 'refs/heads/bootstrap/twf-junk-captain-boss-20261107')

def export(root: Path, target_dir: Path) -> dict:
    """Write a fresh source-pinned XML into the existing .qa/auto Actions artifact.

    Transactional, no overwrite of old results. Existing CI workflow collects
    .qa/auto only after successful tests. No workflow change is needed.
    """
    root = Path(root).resolve()
    target_dir = Path(target_dir)
    _require(target_dir == root / ".qa" / "auto",
             "output must be a dedicated .qa/auto directory")
    _require(not target_dir.is_symlink() and not (root / ".qa").is_symlink(),
             "symlinked artifact directory refused")
    binary, receipt = build_place(root)
    target_dir.mkdir(parents=True, exist_ok=True)
    xml_path = target_dir / XML_NAME
    json_path = target_dir / RECEIPT_NAME
    _require(not xml_path.exists() and not xml_path.is_symlink() and
             not json_path.exists() and not json_path.is_symlink(),
             "existing output cannot be overwritten")
    payload = (json.dumps(receipt, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")
    try:
        with xml_path.open("xb") as stream:
            stream.write(binary)
        with json_path.open("xb") as stream:
            stream.write(payload)
    except OSError:
        # Never unlink by name: a competing writer may have created this path
        # after preflight and our exclusive open cannot prove ownership.
        # Any leftover bytes in a failed CI artifact remain UNTRUSTED.
        raise ExportBlocked("failed to write XML candidate; no upload attempted") from None
    _require(xml_path.read_bytes() == binary and json_path.read_bytes() == payload,
             "export readback mismatch")
    return receipt

if __name__ == "__main__":
    import sys
    root = Path(__file__).resolve().parents[1]
    try:
        receipt = export(root, root / ".qa" / "auto")
    except (OSError, ExportBlocked) as exc:
        print("BLOCKED_XML_EXPORT: " + str(exc), file=sys.stderr)
        sys.exit(2)
    print(json.dumps({"status": receipt["status"], "rbxlx_sha256": receipt["rbxlx_sha256"],
                      "rbxlx_bytes": receipt["rbxlx_bytes"]}, sort_keys=True))
