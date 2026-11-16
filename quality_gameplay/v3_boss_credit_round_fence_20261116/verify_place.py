"""Check real Rojo rbxlx against 23 exact source files, fail-closed."""
import hashlib
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
project = HERE / "EGGRUMBLE_BOSS_CREDIT_STUDIO.project.json"
place = Path(sys.argv[1]).resolve(strict=True)
manifest_path = Path(sys.argv[2])
tree = json.loads(project.read_text(encoding="utf-8"))["tree"]
scripts = {}
for context, branch in (
    ("ServerScriptService", tree["ServerScriptService"]),
    ("StarterPlayerScripts", tree["StarterPlayer"]["StarterPlayerScripts"]),
):
    for name, info in branch.items():
        if name == "$className":
            continue
        source_path = (HERE / info["$path"]).resolve(strict=True)
        if not source_path.is_relative_to(ROOT):
            raise AssertionError(f"source outside repository: {name}")
        class_name = (
            "Script" if source_path.name.endswith(".server.luau")
            else "LocalScript" if source_path.name.endswith(".client.luau")
            else "ModuleScript"
        )
        if name in scripts:
            raise AssertionError(f"duplicate source mapping: {name}")
        scripts[name] = {
            "class": class_name,
            "source_path": str(source_path.relative_to(ROOT)).replace("\\", "/"),
            "source": source_path.read_text(encoding="utf-8").replace("\r\n", "\n"),
            "sha256": hashlib.sha256(source_path.read_bytes()).hexdigest(),
            "container": context,
        }
assert len(scripts) == 23, len(scripts)
actual = {}
for item in ET.parse(place).iter("Item"):
    cls = item.attrib.get("class")
    if cls not in {"Script", "ModuleScript", "LocalScript"}:
        continue
    properties = item.find("Properties")
    if properties is None:
        continue
    name = properties.find("string[@name='Name']")
    if name is None or not name.text:
        continue
    source = properties.find("ProtectedString[@name='Source']")
    if source is None:
        source = properties.find("string[@name='Source']")
    if name.text in actual:
        raise AssertionError(f"duplicate actual script name: {name.text}")
    actual[name.text] = {"class": cls, "source": (source.text or "").replace("\r\n", "\n") if source is not None else None}
assert set(scripts) == set(actual), {"missing": sorted(set(scripts)-set(actual)), "unexpected": sorted(set(actual)-set(scripts))}
for name, expected in scripts.items():
    observed = actual[name]
    assert observed["class"] == expected["class"], (name, expected["class"], observed["class"])
    assert observed["source"] == expected["source"], (name, "source mismatch")
receipt = {
    "status": "SOURCE_EXACT_PRIVATE_ONLY",
    "script_count": len(scripts),
    "original_author_count": 21,
    "new_independent_sources": 2,
    "place_bytes": place.stat().st_size,
    "place_sha256": hashlib.sha256(place.read_bytes()).hexdigest(),
    "scripts": {name: {"class": s["class"], "path": s["source_path"], "sha256": s["sha256"]} for name, s in sorted(scripts.items())},
    "studio_play": "NOT_TESTED",
    "android": "NOT_TESTED",
    "official_rc_integration": False,
}
manifest_path.parent.mkdir(parents=True, exist_ok=True)
manifest_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print("PRIVATE_SOURCE_EXACT_23_OF_23_PASS", receipt["place_bytes"], receipt["place_sha256"])
