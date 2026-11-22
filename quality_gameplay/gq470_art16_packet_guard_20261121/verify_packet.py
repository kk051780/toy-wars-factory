#!/usr/bin/env python3
"""Independent *post-upload* ART16 B220 source packet verifier.

Consumes actual GitHub Actions extracted #970 artifact and frozen official
REAL69 full-source artifact, not a hand-crafted test fixture. Only static
source integrity. This is not a Roblox Engine, art, owner or RC acceptance.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import tempfile

FORMAL_HEAD = "e80973c354f14a0d0088577f3cc1a875454f0f8f"
ART16_A_HEAD = "180f5067bfe71c59b8c0c59b90aa69f1cd00cb7f"
BASE_SHA = "fc63171149a86f6b39779ba6ebe7e18fcb7099fbde98ad2ec33a7cb92b3a9934"
COMPOSITE_SHA = "41a4bad1ce3fe8aa7f04c92cecfe4c710fbe92e702151887066279c2f3fda703"
PROJECT = "EGGRUMBLE_REAL69.project.json"
RECEIPT = "REAL69_LEGACY_INTAKE_RECEIPT.json"
PLACE = "EGGRUMBLE_REAL69_PRIVATE.rbxlx"
PACKET = "B220_ART16_SELECTED_BYTES_ONLY_NOT_FORMAL"
MANIFEST = "SOURCE_SELECT_MANIFEST.json"
PARENTS = {
    966: ("e7c425b3af566defaff71bd540734a117cf2bf2b", 44844649777, 15),
    967: ("89719973047c13dde5ba64732231814a4db32f42", 44845621663, 1),
}

def demand(ok: bool, why: str) -> None:
    if not ok:
        raise ValueError("RED_GQ470_ART16_PACKET_" + why)

def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def js(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))

def project_selected(root: Path) -> dict[str, tuple[Path, str]]:
    project = js(root / PROJECT)
    output: dict[str, tuple[Path, str]] = {}
    base = root.resolve()
    def visit(x: dict, route: str = "") -> None:
        demand(isinstance(x, dict), "PROJECT_NODE")
        if "$path" in x:
            path = x["$path"]
            demand(isinstance(path, str), "PROJECT_SOURCE_PATH_TYPE")
            dest=(root/path).resolve()
            demand(dest.is_relative_to(base) and dest.is_file() and
                   route not in output and route != "", "PROJECT_PATH_COLLISION_TRAVERSAL")
            clazz=("LocalScript" if path.endswith(".client.luau") else
                    "Script" if path.endswith(".server.luau") else
                    "ModuleScript")
            output[route]=(dest,clazz)
            return
        for key,sub in x.items():
            if not key.startswith("$"):
                visit(sub, route+"/"+key if route else key)
    visit(project["tree"])
    demand(len(output)==69, "SCRIPTS69")
    return output

def normalized_selected(root: Path) -> tuple[dict[str,bytes],dict[str,str]]:
    z=project_selected(root)
    return ({route:path.read_bytes() for route,(path,clazz) in z.items()},
            {route:clazz for route,(path,clazz) in z.items()})

def locate(artifact: Path) -> tuple[Path,Path]:
    places=[p for p in artifact.rglob(MANIFEST) if p.parent.name==PACKET]
    demand(len(places)==1, "ONE_REAL_B220_PACKET_ONLY")
    folder=places[0].parent
    roots=[p.parent for p in artifact.rglob(PROJECT)
           if (p.parent/RECEIPT).is_file() and (p.parent/PLACE).is_file()
           and (p.parent/PACKET).resolve()==folder.resolve()]
    demand(len(roots)==1, "ONE_TRUE_COMPOSITE_ROOT")
    return roots[0],folder

def verify(formal: Path, candidate: Path, packet: Path) -> dict:
    formal, candidate, packet = formal.resolve(),candidate.resolve(),packet.resolve()
    orig_receipt=js(formal/RECEIPT)
    c_receipt=js(candidate/RECEIPT)
    a, original_class=normalized_selected(formal)
    b, candidate_class=normalized_selected(candidate)
    demand(orig_receipt.get("canonical_build") is True and
           orig_receipt.get("build_head")==FORMAL_HEAD and
           orig_receipt.get("official_branch")=="rc/p0d-s1-kids-rc01" and
           orig_receipt.get("selected_source_count")==69 and
           orig_receipt.get("source_hashes")=={r:sha(raw) for r,raw in a.items()} and
           orig_receipt.get("source_classes")==original_class,
           "AUTHENTIC_REAL69_BASELINE")
    base_place=(formal/PLACE).read_bytes()
    demand(len(base_place)==798390 and sha(base_place)==BASE_SHA,
           "ORIGINAL_REAL_PLACE")
    candidate_place=(candidate/PLACE).read_bytes()
    note=c_receipt.get("gq470_art16_source_bridge",{})
    demand(len(candidate_place)==822211 and sha(candidate_place)==COMPOSITE_SHA and
           c_receipt.get("private_place_sha256")==COMPOSITE_SHA and
           c_receipt.get("private_place_bytes")==822211,
           "ACTUAL_COMPOSITE_PLACE")
    demand(c_receipt.get("canonical_build") is False and
           c_receipt.get("build_head")=="ART16_A_SOURCE_BRIDGE_NOT_FORMAL" and
           c_receipt.get("source_hashes")=={r:sha(raw) for r,raw in b.items()} and
           c_receipt.get("source_classes")==candidate_class and
           candidate_class==original_class and
           (candidate/PROJECT).read_bytes()==(formal/PROJECT).read_bytes() and
           set(a)==set(b),
           "ALL_69_EXISTING_SCRIPTS_AND_PROJECT")
    demand(note.get("selected_changed")==16 and
           note.get("untouched_original")==53 and
           note.get("native_69_on_off")=="PASS_SOURCE_ONLY" and
           note.get("rojo_69_on_off")=="PASS_SOURCE_ONLY" and
           note.get("formal_base_sha")==FORMAL_HEAD and
           note.get("officially_integrated") is False and
           note.get("owner_accepted") is False and
           note.get("art_gate")=="ART_NO_GO",
           "PREP_ONLY_RECEIPT_OR_FALSE_ART_PASS")
    changes={r for r in a if a[r]!=b[r]}
    demand(len(changes)==16 and len(set(a)-changes)==53,
           "TRUE_SOURCE_DELTAS_16_53")
    manifest=js(packet/MANIFEST)
    demand(manifest.get("schema")=="GQ470_ART16_966_967_B220_SOURCE_ONLY_V1" and
           manifest.get("formal_head")==FORMAL_HEAD and
           manifest.get("source_profile")=="REAL69_PRIVATE_COMPANION" and
           manifest.get("original_script_count")==69 and
           manifest.get("selected_changed")==16 and
           manifest.get("other53_exact") is True and
           manifest.get("requires_unique_writer_220_fresh_expected_sha_nonforce") is True and
           manifest.get("source_authorized_for_formal") is False and
           manifest.get("formal_rc_adopted") is False and
           manifest.get("art_gate")=="ART_NO_GO" and
           manifest.get("owner_accepted") is False and
           manifest.get("real_png")=="0/32" and
           manifest.get("studio")=="NOT_TESTED" and
           manifest.get("android")=="NOT_TESTED",
           "B_MANIFEST_FALSE_FORMAL_OR_ART_GO")
    parents=manifest.get("parent_heads",[])
    demand(isinstance(parents,list) and len(parents)==2 and
           {p.get("pr") for p in parents}==set(PARENTS) and
           all(p["head"]==PARENTS[p["pr"]][0] and
               p["run"]==PARENTS[p["pr"]][1] and
               p["changed"]==PARENTS[p["pr"]][2] for p in parents),
           "REAL_ORIGINAL_PARENT_AUTHOR_SHA_RUN")
    rows=manifest.get("source_only",[])
    demand(isinstance(rows,list) and len(rows)==16 and
           {row.get("selected_route") for row in rows}==changes,
           "16_SELECTED_WITHOUT_OVERLAP")
    found: set[str]=set()
    count={966:0,967:0}
    for row in rows:
        route=row["selected_route"]
        rel=row.get("selected_path")
        demand(isinstance(rel,str) and
               rel=="selected_sources/"+route+".luau",
               "SOURCE_FILE_PATH_TEMPLATE_OR_TRAVERSAL")
        file=(packet/rel).resolve()
        demand(file.is_relative_to(packet) and file.is_file(),
               "PACKET_FILE_PATH_OR_MISSING")
        raw=file.read_bytes()
        owner=row.get("source_parent")
        demand(owner in PARENTS,"SOURCE_OWNER_NOT_PINNED")
        count[owner]+=1
        demand(row.get("selected_class")==original_class[route] and
               row.get("original_sha256")==sha(a[route]) and
               row.get("new_sha256")==sha(b[route]) and
               row.get("bytes")==len(b[route]) and raw==b[route],
               "SOURCE_BYTES_SHA_AND_CLASS_IN_REAL_CANDIDATE")
        found.add(rel)
    actual={p.relative_to(packet).as_posix()
            for p in packet.rglob("*.luau")}
    demand(actual==found and count=={966:15,967:1},
           "EXTRA_OR_MISSING_PACKET_FILE_OR_PARENT_SPLIT")
    return {
        "schema":"GQ470_ART16_REAL_GITHUB_ARTIFACT_POST_UPLOAD_RECEIPT_V1",
        "pr":970,"candidate_a_head":ART16_A_HEAD,
        "candidate_actions_run":44850475985,
        "canonical_formal_head":FORMAL_HEAD,
        "original_selected_count":69,
        "changed_selected_sources":16,"preserved_exact_sources":53,
        "real_packet_source_files_verified":16,
        "original_private_place_bytes":798390,
        "candidate_private_place_bytes":822211,
        "candidate_private_place_sha256":COMPOSITE_SHA,
        "parent_pr_changed_sources":count,
        "no_runtime_game_authority_added":True,
        "formal_rc_adopted":False,
        "source_gate":"PASS_SOURCE_ONLY",
        "studio":"NOT_TESTED","android":"NOT_TESTED",
        "old_new_screenshots":"0/32",
        "art_gate":"ART_NO_GO","product_gate":"PRODUCT_NO_GO",
        "owner_accepted":False,
    }

def negatives(formal: Path,candidate: Path,packet: Path) -> list[str]:
    base=js(packet/MANIFEST)
    row=base["source_only"][0]
    cases=[
        ("false_formal_adopted",lambda a:a.update(formal_rc_adopted=True)),
        ("false_art_go",lambda a:a.update(art_gate="ART_GO")),
        ("wrong_original_sha",lambda a:a["source_only"][0].update(original_sha256="0"*64)),
        ("source_path_traversal",lambda a:a["source_only"][0].update(selected_path="../../escape.luau")),
        ("overlap_duplicate_route",lambda a:a["source_only"][1].update(selected_route=row["selected_route"])),
        ("source_parent_spoof",lambda a:a["source_only"][0].update(source_parent=1234)),
        ("pin_parent_head",lambda a:a["parent_heads"][0].update(head="0"*40)),
        ("source_count_spoof",lambda a:a.update(selected_changed=17)),
    ]
    checked=[]
    for name,change in cases:
        with tempfile.TemporaryDirectory(prefix="art16-packet-neg-") as d:
            child=Path(d)/PACKET
            shutil.copytree(packet,child)
            data=js(child/MANIFEST)
            change(data)
            (child/MANIFEST).write_text(json.dumps(data)+"\n",encoding="utf-8")
            try:
                verify(formal,candidate,child)
            except (ValueError,KeyError):
                checked.append(name)
            else:
                raise AssertionError("RED_GQ470_ART16_ADVERSARIAL_MUTANT_ACCEPTED_"+name)
    with tempfile.TemporaryDirectory(prefix="art16-packet-byte-neg-") as d:
        child=Path(d)/PACKET
        shutil.copytree(packet,child)
        file=child/row["selected_path"]
        file.write_bytes(file.read_bytes()+b"\n--TAMPER")
        try:
            verify(formal,candidate,child)
        except (ValueError,KeyError):
            checked.append("actual_selected_Luau_byte_tamper")
        else:
            raise AssertionError("RED_GQ470_SELECTED_LUAU_CORRUPTION_ACCEPTED")
    with tempfile.TemporaryDirectory(prefix="art16-packet-extra-neg-") as d:
        child=Path(d)/PACKET
        shutil.copytree(packet,child)
        extra=child/"selected_sources/ExtraUnclaimed.client.luau"
        extra.write_text("-- bogus extra")
        try:
            verify(formal,candidate,child)
        except (ValueError,KeyError):
            checked.append("extra_unclaimed_source")
        else:
            raise AssertionError("RED_GQ470_EXTRA_UNCLAIMED_SCRIPT_ACCEPTED")
    demand(len(checked)==10,"MUTANT10")
    return checked

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--formal",type=Path,required=True)
    parser.add_argument("--artifact",type=Path,required=True)
    parser.add_argument("--out",type=Path,required=True)
    parser.add_argument("--negatives",action="store_true")
    a=parser.parse_args()
    candidate,packet=locate(a.artifact)
    report=verify(a.formal,candidate,packet)
    if a.negatives:
        report["negative_packet_mutations_rejected"]=negatives(a.formal,candidate,packet)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(report,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("GQ470_REAL_ART16_UPLOADED_PACKET_16_EXACT_53_PRESERVED_10_MUTATIONS",len(report.get("negative_packet_mutations_rejected",[])))
