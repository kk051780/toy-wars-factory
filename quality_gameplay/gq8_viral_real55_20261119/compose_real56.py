#!/usr/bin/env python3
"""GQ8 Real55 -> Real56: single preexisting V3 Host remains sole round/egg/castle owner.
Patches only factual *notification after* host-authorized state mutation.
No new ServerScript, RemoteEvent, trading, HP, damage or Store authority.
"""
from __future__ import annotations
import argparse, copy, hashlib, json, sys, re
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"gq8_successor_real48_shop_20261119"))
from compose_real48 import flatten, klass

HOST=("ServerScriptService","EGGRUMBLE_LobbyCastleModesPreview")
CLIENT=("StarterPlayer","StarterPlayerScripts","GQ8_ViralCapture")
FEATURE="GQ8_VIRAL_REAL56_20261119"

def exact(src, before, after, label):
    count=src.count(before)
    if count!=1: raise ValueError("RED_"+label+"_COUNT_"+str(count))
    return src.replace(before,after,1)

def regex_exact(src, pattern, replacement, label):
    amended,count=re.subn(pattern,replacement,src)
    if count!=1:raise ValueError("RED_"+label+"_COUNT_"+str(count))
    return amended

def patch_host(src):
    src=exact(src,"local function startSession(mode:string)",'''-- No extra gameplay owner: only this existing HOST emits factual capture hints.
local gq8ViralEpoch=0
local function gq8CaptureHint(player:Player,session:any,kind:string)
 if player.Parent~=Players then return end
 if session.rules.phase~="ACTIVE" and kind~="VICTORY" and kind~="COMEBACK" then return end
 local seq=player:GetAttribute("EGGRUMBLE_ViralSeq")
 if type(seq)~="number" or seq<0 or seq>100000000 then seq=0 end
 player:SetAttribute("EGGRUMBLE_ViralKind",kind)
 player:SetAttribute("EGGRUMBLE_ViralEpoch",session.gq8ViralEpoch)
 player:SetAttribute("EGGRUMBLE_ViralSeq",seq+1)
end

local function startSession(mode:string)''',"HOST_START")
    src=exact(src,'session.world.Name=mode.."_Arena";session.world.Parent=folder',
'''gq8ViralEpoch+=1
 session.gq8ViralEpoch=gq8ViralEpoch
 session.gq8ViralDanger={}
 session.gq8ViralResults=false
 session.world.Name=mode.."_Arena";session.world.Parent=folder''',"SESSION_EPOCH")
    src=regex_exact(src,
        r"if c\.alive and c\.heldEggs>0 then\n[ \t]+local ok=pcall\(function\(\) Rules\.depositEggs\(session\.rules,entry\.id,c\.heldEggs\) end\)\n[ \t]+if ok then session\.refresh\(\) end\n[ \t]+end",
        '''if c.alive and c.heldEggs>0 then
    local before=c.depositedEggs or 0
    local ok=pcall(function() Rules.depositEggs(session.rules,entry.id,c.heldEggs) end)
    if ok then
     if (c.depositedEggs or 0)>before then
      gq8CaptureHint(p,session,"EGG_DELIVER")
     end
     session.refresh()
    end
   end''',"EGG_DELIVER_EXACT_COMMIT")
    src=regex_exact(src,
        r"pcall\(function\(\) Rules\.takeEggs\(session\.rules,tostring\(p\.UserId\),1,entry\.id\) end\)\n[ \t]+session\.refresh\(\)",
'''local taker=session.rules.castles[tostring(p.UserId)]
   local before=taker and taker.heldEggs or 0
   local ok=pcall(function() Rules.takeEggs(session.rules,tostring(p.UserId),1,entry.id) end)
   if ok and taker and (taker.heldEggs or 0)>before then
    gq8CaptureHint(p,session,"EGG_STEAL")
   end
   session.refresh()''',"EGG_STEAL_EXACT_COMMIT")
    src=regex_exact(src,
        r"local c=session\.rules\.castles\[tostring\(player\.UserId\)\]\n[ \t]+if c and not c\.alive",
'''local c=session.rules.castles[tostring(player.UserId)]
     if c and c.alive and c.hp<=Rules.CASTLE_HP*.22
       and not session.gq8ViralDanger[player.UserId] then
      session.gq8ViralDanger[player.UserId]=true
      gq8CaptureHint(player,session,"CASTLE_DANGER")
     end
     if c and not c.alive''',"CASTLE_DANGER_ONLY_AUTHORIZED_STATE")
    src=regex_exact(src,
        r"if session\.rules\.winner~=nil then\n[ \t]+-- Short factual result shown exactly once",
'''if session.rules.winner~=nil then
    if not session.gq8ViralResults then
     session.gq8ViralResults=true
     for _,winnerPlayer in ipairs(queue) do
      if winnerPlayer.Parent==Players and joined[winnerPlayer.UserId]==mode then
       local id=tostring(winnerPlayer.UserId)
       local ownCastle=session.rules.castles[id]
       if ownCastle then
        local won=if mode=="TEAM" then session.rules.winner==ownCastle.team
         else session.rules.winner==id
        if won then
         local kind=if session.gq8ViralDanger[winnerPlayer.UserId] then "COMEBACK" else "VICTORY"
         gq8CaptureHint(winnerPlayer,session,kind)
        end
       end
      end
     end
    end
    -- Short factual result shown exactly once''',"TRUE_WINNER_ONLY")
    return src

def compose(parent55:Path, receipt55:Path, client:Path, out:Path):
    if out.exists():raise ValueError("RED_NO_OVERWRITE")
    original,old=flatten(parent55)
    assert len(old)==55 and HOST in old and CLIENT not in old,"RED_NOT_REAL55_PARENT"
    report=json.loads(receipt55.read_text(encoding="utf8"))
    assert report.get("selected_real55_count")==55 or report.get("selected_script_count")==55, "RED_RECEIPT_REAL55"
    expected={tuple(x["route"].split("/")):x for x in report["sources"]}
    assert set(old)==set(expected),"RED_PARENT_RECEIPT_ROUTES"
    for route,file in old.items():
        b=file.read_bytes();m=expected[route]
        assert hashlib.sha256(b).hexdigest()==m["sha256"] and len(b)==m["bytes"],"RED_PARENT_BYTES_"+"/".join(route)
    oldhost=old[HOST].read_text(encoding="utf8")
    host=patch_host(oldhost).encode("utf8")
    assert host!=old[HOST].read_bytes() and b"TakeDamage(" not in host[len(oldhost.encode("utf8")):],"RED_HOST_PATCH_NOT_PRESENT"
    child=client.read_bytes()
    assert b'EGGRUMBLE_ViralSeq' in child and b'FireServer(' not in child,"RED_BAD_CHILD"
    out.mkdir(parents=True)
    doc=copy.deepcopy(original)
    doc["name"]="GQ8_REAL56_VIRAL_TRUE_SERVER_EVENTS_CLIENT_CAPTURE_PRIVATE_ONLY"
    ledger=[]
    def put(route:tuple[str,...], b:bytes, suffix:str, owner:str):
        f=out.joinpath("sources",*route[:-1],route[-1]+suffix)
        f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(b)
        node=doc["tree"]
        for depth,name in enumerate(route[:-1]):
            if name not in node:node[name]={} if depth==0 else {"$className":"Folder"}
            node=node[name]
        node[route[-1]]={"$path":f.relative_to(out).as_posix()}
        ledger.append({"route":"/".join(route),"class":klass(f),"sha256":hashlib.sha256(b).hexdigest(),"bytes":len(b),"origin":owner})
    for route,file in sorted(old.items()):
        cls=klass(file)
        suffix=".server.luau" if cls=="Script" else ".client.luau" if cls=="LocalScript" else ".luau"
        b=host if route==HOST else file.read_bytes()
        put(route,b,suffix,"one_host_notification_patch" if route==HOST else "exact_parent55")
    put(CLIENT,child,".client.luau","optional_client_first_party_capture")
    project=out/"EGGRUMBLE_REAL56.project.json"
    project.write_text(json.dumps(doc,ensure_ascii=False,sort_keys=True,indent=2)+"\n",encoding="utf8")
    _,after=flatten(project)
    assert len(after)==56 and set(after)==set(old)|{CLIENT},"RED_REAL56_WIRING"
    for route,file in old.items():
        if route!=HOST: assert after[route].read_bytes()==file.read_bytes(),"RED_ORIGINAL_PRESERVATION_"+"/".join(route)
    assert klass(after[HOST])==klass(old[HOST]) and klass(after[CLIENT])=="LocalScript",("RED_CLASS",klass(after[HOST]),klass(old[HOST]),klass(after[CLIENT]))
    result={"feature_id":FEATURE,"parent":55,"candidate":56,"modified_old_source":["/".join(HOST)],
        "unchanged_original_source_count":54,"new_client_source":["/".join(CLIENT)],
        "new_remote_owners":0,"new_store_owners":0,"publish_enabled":False,"filming_default_off":True,
        "private_studio":"NOT_TESTED","android":"NOT_TESTED","fun":"NOT_TESTED",
        "rollback":"reselect exact immutable official Real55 original project",
        "sources":ledger}
    (out/"GQ8_VIRAL56_RECEIPT.json").write_text(json.dumps(result,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf8")
    print("GQ8_VIRAL56_ONE_HOST_ONLY_TRUE_EVENTS_54_PRESERVED_SOURCE_PASS")

# Current69 is a separate explicit entry. The original Real55 functions and
# legacy CLI below remain byte-for-byte intact.
CURRENT69_LOCK_SHA256 = "f356a3586f5b4db9b38b7c04e2ec39ebf6066b6dee0c85bded9bfc4229b8f962"
CURRENT69_HERE = Path(__file__).resolve().parent
CURRENT69_PROJECT = "EGGRUMBLE_REAL69.project.json"


def current69_require(condition, message):
    if not condition:
        raise ValueError("CURRENT69_" + message)


def current69_pin(value):
    data = value.read_bytes() if isinstance(value, Path) else value
    current69_require(isinstance(data, bytes), "PIN_REQUIRES_BYTES_OR_PATH")
    return {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def current69_json(data):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            current69_require(key not in result, "DUPLICATE_JSON_KEY_" + key)
            result[key] = value
        return result
    return json.loads(data.decode("utf-8", errors="strict"), object_pairs_hook=unique)


def current69_load_lock(path=None):
    path = Path(path) if path is not None else CURRENT69_HERE / "INPUT_LOCK.json"
    current69_require(path.is_file() and not path.is_symlink(), "LOCK_FILE_REQUIRED")
    raw = path.read_bytes()
    current69_require(hashlib.sha256(raw).hexdigest() == CURRENT69_LOCK_SHA256, "LOCK_BYTES_DRIFT")
    lock = current69_json(raw)
    current69_require(lock["schema"] == "GQ8_CAPTURE_CURRENT69_LOCK_V1", "LOCK_SCHEMA")
    current69_require(lock["source_count"] == 69 and lock["instance_count"] == 75, "LOCK_COUNTS")
    current69_require(len(lock["sources"]) == 69 and len(lock["source_delta_edits"]) == 12, "LOCK_INPUTS")
    return lock


def current69_validate_tree(root, lock, variant="original"):
    root = Path(root)
    current69_require(variant in ("original", "candidate"), "UNKNOWN_TREE_VARIANT")
    current69_require(root.is_dir() and not root.is_symlink(), "TREE_DIRECTORY_REQUIRED")
    project = root / CURRENT69_PROJECT
    current69_require(project.is_file() and not project.is_symlink(), "PROJECT_FILE_REQUIRED")
    raw = project.read_bytes()
    current69_require(current69_pin(raw) == {k: lock["input"]["project"][k] for k in ("bytes", "sha256")}, "PROJECT_PHYSICAL_BYTES_DRIFT")
    current69_json(raw)
    source_dir = root / "sources"
    current69_require(source_dir.is_dir() and not source_dir.is_symlink(), "SOURCE_DIRECTORY_REQUIRED")
    actual_files = set()
    for path in source_dir.rglob("*"):
        current69_require(not path.is_symlink(), "SOURCE_SYMLINK_REJECTED")
        if path.is_file():
            actual_files.add(path.relative_to(root).as_posix())
    expected_files = {item["path"] for item in lock["sources"]}
    current69_require(len(expected_files) == 69 and actual_files == expected_files, "SOURCE_PATH_MEMBERSHIP")
    _, items = flatten(project)
    expected_routes = {tuple(item["route"].split("/")) for item in lock["sources"]}
    current69_require(len(items) == 69 and set(items) == expected_routes, "SOURCE_ROUTE_MEMBERSHIP")
    for item in lock["sources"]:
        route = tuple(item["route"].split("/"))
        path = root / item["path"]
        current69_require(items[route] == path.resolve() and klass(path) == item["class"], "SOURCE_PATH_CLASS_" + item["route"])
        data = path.read_bytes()
        data.decode("utf-8", errors="strict")
        expected = lock["candidate"] if variant == "candidate" and route == CLIENT else item
        current69_require(current69_pin(data) == {k: expected[k] for k in ("bytes", "sha256")}, "SOURCE_BYTES_" + item["route"])
    return items


def current69_inverse(candidate, lock, v2_only=False):
    current69_require(current69_pin(candidate) == lock["candidate"], "INVERSE_CANDIDATE_BYTES")
    edits = lock["source_delta_edits"][-4:] if v2_only else lock["source_delta_edits"]
    restored = candidate
    for edit in reversed(edits):
        old, new = edit["before"].encode("utf-8"), edit["after"].encode("utf-8")
        current69_require(restored.count(new) == 1, "INVERSE_ANCHOR_NOT_UNIQUE")
        restored = restored.replace(new, old, 1)
    expected = lock["historical_v2"] if v2_only else lock["original_client"]
    current69_require(current69_pin(restored) == expected, "INVERSE_ORIGINAL_BYTES")
    return restored


def current69_verify_api(lock, ref_json, run_json, artifact_json):
    from datetime import datetime, timezone
    ref, run, artifact = [current69_json(Path(p).read_bytes()) if isinstance(p, (str, Path)) else p
                          for p in (ref_json, run_json, artifact_json)]
    current69_require(ref.get("ref") == "refs/heads/rc/p0d-s1-kids-rc01" and
                      ref.get("object", {}).get("sha") == lock["base_rc"], "LIVE_FORMAL_MOVED_REBIND_REQUIRED")
    for key, expected in lock["input"]["run"].items():
        current69_require(type(run.get(key)) is type(expected) and run.get(key) == expected, "OFFICIAL_RUN_" + key)
    for key in ("id", "name", "size_in_bytes", "digest"):
        expected = lock["input"]["artifact"][key]
        current69_require(type(artifact.get(key)) is type(expected) and artifact.get(key) == expected, "OFFICIAL_ARTIFACT_" + key)
    current69_require(artifact.get("expired") is False, "OFFICIAL_ARTIFACT_EXPIRED")
    current69_require(datetime.fromisoformat(artifact["expires_at"].replace("Z", "+00:00")) > datetime.now(timezone.utc), "OFFICIAL_ARTIFACT_EXPIRY")
    for key in ("id", "head_sha", "head_branch"):
        current69_require(artifact.get("workflow_run", {}).get(key) == lock["input"]["artifact"]["workflow_run"][key], "ARTIFACT_RUN_BINDING_" + key)
    return {"formal_head": lock["base_rc"], "run_id": run["id"], "artifact_id": artifact["id"],
            "offline_value_binding_only": True, "provider_authentication_proven": False}


def current69_extract_archive(archive, out, lock):
    import io, stat, zipfile
    from pathlib import PurePosixPath
    out = Path(out)
    current69_require(not out.exists() and not out.is_symlink(), "EXTRACT_OUTPUT_MUST_BE_NEW")
    raw = Path(archive).read_bytes()
    current69_require(current69_pin(raw) == {k: lock["archive"][k] for k in ("bytes", "sha256")}, "ARCHIVE_BYTES_DRIFT")
    members, seen = [], set()
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        infos = z.infolist()
        current69_require(len(infos) == lock["archive"]["members"], "ARCHIVE_MEMBER_COUNT")
        current69_require(sum(i.file_size for i in infos) == lock["archive"]["expanded_bytes"], "ARCHIVE_EXPANDED_BYTES")
        for info in infos:
            name = info.filename
            normalized = name[:-1] if info.is_dir() else name
            parts = PurePosixPath(normalized)
            current69_require(bool(normalized) and not parts.is_absolute() and ".." not in parts.parts and
                              "\\" not in name and ":" not in name and parts.as_posix() == normalized,
                              "ARCHIVE_UNSAFE_PATH")
            current69_require(normalized.casefold() not in seen, "ARCHIVE_DUPLICATE_PATH")
            seen.add(normalized.casefold())
            mode = stat.S_IFMT(info.external_attr >> 16)
            current69_require(mode in (0, stat.S_IFREG, stat.S_IFDIR) and not (info.flag_bits & 1), "ARCHIVE_LINK_OR_ENCRYPTED_MEMBER")
            members.append((normalized, info.is_dir(), b"" if info.is_dir() else z.read(info)))
        current69_require(z.testzip() is None, "ARCHIVE_CRC")
    out.mkdir(parents=True, exist_ok=False)
    for name, is_dir, data in members:
        path = out / name
        if is_dir:
            path.mkdir(parents=True, exist_ok=True)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("xb") as stream:
                current69_require(stream.write(data) == len(data), "ARCHIVE_SHORT_WRITE")
    return current69_validate_tree(out, lock, "original")


def current69_source_binding(lock, source_head):
    import os, subprocess
    repo = CURRENT69_HERE.parents[1]
    def git(*args):
        return subprocess.check_output(["git", "-C", str(repo), *args])
    current69_require(re.fullmatch(r"[0-9a-f]{40}", source_head) is not None, "SOURCE_HEAD_FORMAT")
    current69_require(git("rev-parse", "HEAD").decode().strip() == source_head, "ACTUAL_SOURCE_HEAD_MISMATCH")
    for ancestor in (lock["base_rc"], lock["original_source_head"]):
        subprocess.run(["git", "-C", str(repo), "merge-base", "--is-ancestor", ancestor, source_head], check=True)
    changes = git("diff", "--name-only", lock["base_rc"], source_head).decode().splitlines()
    current69_require(set(changes) == set(lock["source_scope_paths"]) and len(changes) == 11, "EXACT_ELEVEN_PATH_SCOPE")
    manifest = []
    for rel in lock["source_scope_paths"]:
        path = repo / rel
        current69_require(path.is_file() and not path.is_symlink(), "SOURCE_SCOPE_FILE_" + rel)
        raw = path.read_bytes()
        current69_require(raw == git("show", source_head + ":" + rel), "SOURCE_SCOPE_DIRTY_" + rel)
        manifest.append({"path": rel, **current69_pin(raw)})
    return {"source_head": source_head, "source_tree": git("rev-parse", source_head + "^{tree}").decode().strip(),
            "source_parents": git("show", "-s", "--format=%P", source_head).decode().split(),
            "source_context": "HOSTED_GITHUB_ACTIONS_ACTUAL_HEAD" if os.environ.get("GITHUB_ACTIONS") == "true" else "LOCAL_IMMUTABLE_CANDIDATE_NOT_REMOTE",
            "github_event": os.environ.get("GITHUB_EVENT_NAME"), "github_sha": os.environ.get("GITHUB_SHA"),
            "source_manifest": manifest}


def current69_compose(args):
    import shutil
    from datetime import datetime, timezone
    lock = current69_load_lock()
    api = current69_verify_api(lock, args.ref_json, args.run_json, args.artifact_json)
    binding = current69_source_binding(lock, args.source_head)
    current69_require(not args.out.exists() and not args.out.is_symlink(), "OUTPUT_MUST_BE_NEW")
    candidate = (CURRENT69_HERE / "GQ8_ViralCapture.client.luau").read_bytes()
    current69_require(current69_pin(candidate) == lock["candidate"], "SELECTED_CANDIDATE_BYTES")
    inverse = current69_inverse(candidate, lock)
    current69_inverse(candidate, lock, v2_only=True)
    args.out.mkdir(parents=True, exist_ok=False)
    parent = args.out / "input"
    before = current69_extract_archive(args.archive, parent, lock)
    shutil.copyfile(args.archive, args.out / "input_archive.zip")
    for key in ("place", "legacy_intake_receipt"):
        spec = lock["input"][key]
        current69_require(current69_pin(parent / spec["path"]) == {k: spec[k] for k in ("bytes", "sha256")}, "ORIGINAL_INPUT_" + key)
    current69_require(before[CLIENT].read_bytes() == inverse, "INVERSE_NOT_SELECTED_OFFICIAL_CLIENT")
    forward = inverse
    for edit in lock["source_delta_edits"]:
        old, new = edit["before"].encode("utf-8"), edit["after"].encode("utf-8")
        current69_require(forward.count(old) == 1, "FORWARD_ANCHOR_NOT_UNIQUE")
        forward = forward.replace(old, new, 1)
    current69_require(forward == candidate, "FORWARD_NOT_SELECTED_CANDIDATE")
    client_rel = next(item["path"] for item in lock["sources"] if item["route"] == "/".join(CLIENT))
    for label, body, variant in (("ON", candidate, "candidate"), ("OFF", inverse, "original")):
        target = args.out / label
        shutil.copytree(parent / "sources", target / "sources")
        (target / CURRENT69_PROJECT).write_bytes((parent / CURRENT69_PROJECT).read_bytes())
        (target / client_rel).write_bytes(body)
        current69_validate_tree(target, lock, variant)
    api_dir = args.out / "input_api"
    api_dir.mkdir()
    for name, path in (("formal-ref.json", args.ref_json), ("official-run.json", args.run_json), ("official-artifact.json", args.artifact_json)):
        (api_dir / name).write_bytes(path.read_bytes())
    receipt = {"schema": "GQ8_CAPTURE_CURRENT69_COMPOSITION_V1", **binding,
               "feature_id": lock["feature_id"], "claim_id": lock["scope_grant"]["claim_id"],
               "base_rc": lock["base_rc"], "official_input_head": lock["base_rc"],
               "created_at": datetime.now(timezone.utc).isoformat(), "input_api": api,
               "input_api_paths": ["input_api/formal-ref.json", "input_api/official-run.json", "input_api/official-artifact.json"],
               "input_archive": {"path": "input_archive.zip", **current69_pin(args.out / "input_archive.zip")},
               "input_lock": current69_pin(CURRENT69_HERE / "INPUT_LOCK.json"),
               "source_count": 69, "changed_sources": ["/".join(CLIENT)], "unchanged_sources": 68,
               "candidate": current69_pin(candidate), "inverse_original": current69_pin(inverse),
               "canonical_build": False, "formal_rc_adoption_proven": False, "provider_authentication_proven": False,
               "original_official_receipt": "input/REAL69_LEGACY_INTAKE_RECEIPT.json",
               "studio": "NOT_TESTED", "android": "NOT_TESTED", "art": "NO_GO", "fun": "NOT_TESTED",
               "limits": lock["limits"]}
    (args.out / "COMPOSITION_RECEIPT.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("CURRENT69_CAPTURE_EXACT_ONE_REPLACEMENT_68_PRESERVED_COMPOSITION_PASS_NOT_RC")


if __name__ == "__main__" and sys.argv[1:2] == ["current69"]:
    parser = argparse.ArgumentParser(description="Pinned current69 Capture lifecycle composition; not official adoption")
    for name in ("archive", "out", "ref-json", "run-json", "artifact-json"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--source-head", required=True)
    current69_compose(parser.parse_args(sys.argv[2:]))
    raise SystemExit(0)


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--parent55",type=Path,required=True)
    p.add_argument("--receipt55",type=Path,required=True)
    p.add_argument("--client",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    compose(a.parent55,a.receipt55,a.client,a.out)
