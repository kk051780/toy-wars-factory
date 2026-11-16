"""Generate isolated 22-source Rojo candidate; never update canonical RC or author files."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil

ROOT=Path(__file__).resolve().parents[3]
ORIGIN=ROOT/"handoffs/P0D-PQG-SEVEN-HERO-PLAYABLE-20261116"
LANE=Path(__file__).resolve().parents[1]
AUTHOR_GIT_BLOB="66e666418b7c23d41f87faa5d61eb6e2770a463e"

def blob_sha(data:bytes)->str:
    return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()

def mapped_paths(node):
    if isinstance(node,dict):
        if "$path" in node:
            yield node["$path"]
        else:
            for key,value in node.items():
                if not key.startswith("$"):
                    yield from mapped_paths(value)

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--out",type=Path,required=True)
    args=parser.parse_args()
    author=(ORIGIN/"EGGRUMBLE_SevenRoleCombat.luau").read_bytes()
    assert blob_sha(author)==AUTHOR_GIT_BLOB,"author source drift"
    target=args.out.resolve()
    target.mkdir(parents=True,exist_ok=False)
    src_proj=json.loads((ORIGIN/"EGGRUMBLE_V3_STUDIO.project.json").read_text())
    paths=list(mapped_paths(src_proj["tree"]))
    assert len(paths)==21 and len(set(paths))==21, "expected pinned 21 scripts"
    assert paths.count("EGGRUMBLE_SevenRoleCombat.luau")==1
    hashes={}
    for path in paths:
        source=(ORIGIN/path).resolve(strict=True)
        assert source.is_relative_to(ORIGIN.resolve()),"path traversal"
        data=(LANE/"EGGRUMBLE_SevenRoleCombat.patched.luau").read_bytes() if path=="EGGRUMBLE_SevenRoleCombat.luau" else source.read_bytes()
        dst=target/path
        dst.parent.mkdir(parents=True,exist_ok=True)
        dst.write_bytes(data)
        hashes[path]=hashlib.sha256(data).hexdigest()
    policy="EGGRUMBLE_StatusTickFence.luau"
    (target/policy).write_bytes((LANE/policy).read_bytes())
    hashes[policy]=hashlib.sha256((target/policy).read_bytes()).hexdigest()
    server=src_proj["tree"]["ServerScriptService"]
    assert "EGGRUMBLE_StatusTickFence" not in server
    server["EGGRUMBLE_StatusTickFence"]={"$path":policy}
    assert len(list(mapped_paths(src_proj["tree"])))==22
    (target/"project.json").write_text(json.dumps(src_proj,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    receipt={
        "baseline_author_sha":"fe67d31bc8d1b3e481cd22d2be9ea54a1eb031c9",
        "baseline_combat_git_blob_sha":AUTHOR_GIT_BLOB,
        "scope":"GQ_V3_BURN_PREDATOR_TARGET_LIFETIME_FENCE",
        "original_unchanged":20,
        "modified_original_source":1,
        "added_pure_policy":1,
        "private_source_count":22,
        "source_sha256":hashes,
        "official_rc_integrated":False,
        "studio":"NOT_TESTED",
        "android":"NOT_TESTED",
        "owner_accepted":False,
        "public_publish":False
    }
    (target/"SOURCE_RECEIPT.json").write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("GQ_STATUS_22_SOURCE_COMPOSED_EXACT",len(hashes))

if __name__=="__main__":
    main()
