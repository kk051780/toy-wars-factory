#!/usr/bin/env python3
"""Source-exact private Studio candidate. Never writes original scripts or official RC."""
import argparse
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
AUTHOR = REPO / "handoffs/P0D-PQG-SEVEN-HERO-PLAYABLE-20261116"
PROJECT = AUTHOR / "EGGRUMBLE_V3_STUDIO.project.json"
HOST = AUTHOR / "EGGRUMBLE_LobbyCastleModesPreview.server.luau"
HOST_BLOB = "7162b209bf67b74a71553217f3f744e072a0365d"
REQUIRE_ANCHOR = 'local RoundReplay=require(script.Parent:WaitForChild("EGGRUMBLE_RoundReplay"))'
START_ANCHOR = " BotActors.start(session,Rules)"
ADD_REQUIRE = 'local CarrierTell=require(script.Parent:WaitForChild("EGGRUMBLE_CarrierWorldTell"))'
ADD_START = " CarrierTell.start(session)"

def git_blob_sha(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()

def compose(out: Path) -> dict:
    original = HOST.read_bytes()
    assert git_blob_sha(original) == HOST_BLOB, "RED: original author Game changed; rebase and re-review"
    text = original.decode("utf-8")
    assert text.count(REQUIRE_ANCHOR) == 1 and text.count(START_ANCHOR) == 1, "RED: hook no longer unique"
    assert ADD_REQUIRE not in text and ADD_START not in text, "RED: already integrated"
    text = text.replace(REQUIRE_ANCHOR, REQUIRE_ANCHOR + "\n" + ADD_REQUIRE, 1)
    text = text.replace(START_ANCHOR, START_ANCHOR + "\n" + ADD_START, 1)
    out.mkdir(parents=True, exist_ok=True)
    host = out / "EGGRUMBLE_LobbyCastleModesPreview.server.luau"
    host.write_text(text, encoding="utf-8")
    project = json.loads(PROJECT.read_text(encoding="utf-8"))
    server = project["tree"]["ServerScriptService"]
    sources = {}
    for label, node in server.items():
        if not isinstance(node, dict) or "$path" not in node:
            continue
        source = AUTHOR / node["$path"]
        if label == "EGGRUMBLE_LobbyCastleModesPreview":
            source = host
        assert source.is_file(), f"RED: missing {source}"
        sources[label] = hashlib.sha256(source.read_bytes()).hexdigest()
        node["$path"] = __import__("os").path.relpath(source,out).replace("\\","/")
    for label,node in project["tree"]["StarterPlayer"]["StarterPlayerScripts"].items():
        source = AUTHOR / node["$path"]
        assert source.is_file(), f"RED: missing {source}"
        sources[label] = hashlib.sha256(source.read_bytes()).hexdigest()
        node["$path"] = __import__("os").path.relpath(source,out).replace("\\","/")
    for label,file in [
        ("EGGRUMBLE_CarrierWorldTell","EGGRUMBLE_CarrierWorldTell.luau"),
        ("EGGRUMBLE_CarrierTellPolicy","EGGRUMBLE_CarrierTellPolicy.luau"),
    ]:
        source = HERE / file
        assert source.is_file()
        sources[label] = hashlib.sha256(source.read_bytes()).hexdigest()
        server[label] = {"$path":__import__("os").path.relpath(source,out).replace("\\","/")}
    project["name"] = "EGGRUMBLE_V3_CARRIER_WORLD_TELL_PRIVATE_NO_RC"
    project_path = out / "EGGRUMBLE_CARRIER_TELL_PRIVATE.project.json"
    project_path.write_text(json.dumps(project,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    receipt = {
        "owner_original_blob": HOST_BLOB,
        "author_source_count": len(sources)-2,
        "private_source_count": len(sources),
        "official_rc_integrated": False,
        "studio_android_tested": False,
        "source_sha256": sources,
    }
    (out / "receipt.json").write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    assert len(sources) == 23, f"RED: expected 21 original sources + 2 optional, got {len(sources)}"
    return receipt

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--out",type=Path,required=True)
    args = parser.parse_args()
    rec = compose(args.out.resolve())
    print(f"PRIVATE_SOURCE_COMPOSE_OK {rec['private_source_count']}/23 (not Studio/RC GO)")
