#!/usr/bin/env python3
"""P0D product-studio bridge: 6 separately captured H0/H1 Studio probe logs -> ONE *advisory* decision.

Read-only, run offline. NEVER emits personal details/username/chat logs; uses original #245
sanitizing parser unchanged and pinned by its exact Git blob.
Six user-supplied text files alone can be spoofed and are NEVER engine/human/phone PASS.
A manual OWNER review, human score, screenshots, 2-client and phone check remain mandatory.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

HERE=Path(__file__).resolve()
ROOT=HERE.parent
VENDOR=ROOT/"vendor/review_studio_probe_logs_PINNED_UNCHANGED.py"
VENDOR_GIT_BLOB="d2e4580e1ea417225d7e75a6ea83b559a4f677ac"
SOURCE_DECIDER=ROOT/"decide_next_ab.py"
REQUIRED_SIX=("h0_server","h0_red","h0_blue","h1_server","h1_red","h1_blue")

def gitblob(data:bytes)->str:
    return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()

def load_original_parser():
    if gitblob(VENDOR.read_bytes())!=VENDOR_GIT_BLOB:
        raise ValueError("ORIGINAL_PASSIVE_PROBE_PARSER_BLOB_MISMATCH")
    spec=importlib.util.spec_from_file_location("p0d_original_passive_parser",VENDOR)
    if not spec or not spec.loader:
        raise ValueError("PASSIVE_PROBE_PARSER_UNAVAILABLE")
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def load_decider():
    spec=importlib.util.spec_from_file_location("p0d_owner_manually_reviewed_decider",SOURCE_DECIDER)
    if not spec or not spec.loader:
        raise ValueError("MARKET_ARBITER_UNAVAILABLE")
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def hold(code:str,message:str,probes:dict|None=None)->dict:
    return {
        "report_type":"P0D_H0_H1_PASSIVE_PROBE_PRODUCT_BRIDGE_V1",
        "product_decision":code,
        "next_experiment":None,
        "reason":message,
        "h0_h1_probe_observations_only":probes,
        "source_content_personal_information_retained":False,
        "real_roblox_engine_two_client_certified":False,
        "real_phone_certified":False,
        "manual_owner_fun_certified":False,
        "official_rc_adopted":False,
        "publish_authorized":False,
        "paid_features_authorized":False
    }

def check_log_inputs(paths:dict)->bool:
    if not isinstance(paths,dict) or set(paths)!=set(REQUIRED_SIX):
        return False
    files=[Path(paths[k]).resolve() for k in REQUIRED_SIX]
    return len(set(files))==6 and all(p.is_file() and p.stat().st_size<=15*1024*1024 for p in files)

def judge_manual_and_probe(manual:dict,paths:dict)->dict:
    if not isinstance(manual,dict):
        return hold("HOLD_MISSING_OWNER_SCORECARD","Manual H0/H1 owner checklist missing.")
    if not check_log_inputs(paths):
        return hold("HOLD_NEED_SIX_DISTINCT_LOGS","Need separately saved H0/H1 x SERVER/RED/BLUE UTF-8 logs; size <=15MB/file.")
    p=load_original_parser()
    assessments={}
    for version in ("h0","h1"):
        try:
            # Exact original #245 passive observer parser, not our invented imitation.
            proof=p.process(Path(paths[version+"_server"]),Path(paths[version+"_red"]),
                            Path(paths[version+"_blue"]))
        except (ValueError,OSError,UnicodeError) as exc:
            return hold("HOLD_PROBE_LOG_INVALID",f"{version.upper()} read-only Studio logs failed whitelist parser: {type(exc).__name__}")
        assert proof["status"]=="OBSERVED_ONLY_NOT_STUDIO_PASS"
        assert proof["manual_case_pass_count"]==0
        assert proof["physical_two_client_certified"] is False
        assert proof["real_mobile_certified"] is False
        assert proof["human_ux_certified"] is False
        assessments[version]={
           "type":proof["format"],
           "status":proof["status"],
           "log_sha256":proof["log_sha256"],
           "record_counts":proof["record_counts"],
           "client_phases_observed":proof["client_phases_observed"],
           "event_counts":proof["event_counts"],
           "warning_kinds":sorted(set(w["kind"] for w in proof["passive_warnings"])),
           "manual_cases_accepted":0
        }
    six_hashes=[digest for version in assessments.values()
                for digest in version["log_sha256"].values()]
    if len(set(six_hashes))!=6:
        return hold("HOLD_REUSED_SESSION_LOGS",
                    "H0 and H1 use identical log bytes; record independent trials.",assessments)
    for version,proof in assessments.items():
        if proof["warning_kinds"]:
            return hold("HOLD_REVIEW_STUDIO_WARNINGS",
                f"{version.upper()} passive probe reported warning(s); review engine/UI before game fun acceptance.",
                assessments)
        phases=proof["client_phases_observed"]
        for team in ("RED","BLUE"):
            if phases[team]["ACTIVE"] is not True:
                return hold("HOLD_INCOMPLETE_ACTIVE_MATCH",
                    f"{version.upper()} {team} did not provide an ACTIVE phase observation.",
                    assessments)
    decider=load_decider()
    # Never alter human booleans or fun ratings. Presence of probe text CANNOT set
    # "studio_2client", mobile_checked, owner_confirmation, pickup, score or route proof.
    ans=decider.evaluate(manual)
    # Contradictory manual declaration is safely rejected, not silently fixed.
    if not isinstance(manual.get("h0"),dict) or not isinstance(manual.get("h1"),dict) or \
        manual["h0"].get("server_red_blue_logs") is not True or \
        manual["h1"].get("server_red_blue_logs") is not True:
        return hold("HOLD_OWNER_MUST_ACK_LOG_REVIEW",
                    "Original logs are present, but OWNER has not checked each saved output.",
                    assessments)
    return {
        "report_type":"P0D_H0_H1_PASSIVE_PROBE_PRODUCT_BRIDGE_V1",
        **ans,
        "h0_h1_probe_observations_only":assessments,
        "source_content_personal_information_retained":False,
        "real_roblox_engine_two_client_certified":False,
        "real_phone_certified":False,
        "manual_owner_fun_certified":False,
        "publish_authorized":False,
        "paid_features_authorized":False,
        "official_rc_adopted":False,
        "source_caveat":"User-provided logs can be spoofed; only full OWNER local Studio human review can validate game/phone/fun."
    }

def main()->int:
    ap=argparse.ArgumentParser(description="Read six H0/H1 passive logs and owner-only manually scored checklist.")
    ap.add_argument("--owner-json",type=Path,required=True)
    for ver in ("h0","h1"):
        for who in ("server","red","blue"):
            ap.add_argument(f"--{ver}-{who}-log",type=Path,required=True)
    ap.add_argument("--output",type=Path,required=True)
    args=ap.parse_args()
    try:
        manual=json.loads(args.owner_json.read_text(encoding="utf-8"))
        paths={k:getattr(args,k+"_log") for k in REQUIRED_SIX}
        result=judge_manual_and_probe(manual,paths)
        if args.output.exists():
            raise ValueError("REFUSE_OVERWRITE_EXISTING_OWNER_EVIDENCE_REPORT")
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        print("P0D_PRODUCT_STUDIO_H0_H1_OBSERVATION_ADVISORY_"+result["product_decision"])
        print("NEVER_AUTO_CERTIFY_STUDIO_MOBILE_HUMAN_OR_PUBLISH")
        return 0
    except (ValueError,OSError,UnicodeError,json.JSONDecodeError) as exc:
        print("P0D_PRODUCT_STUDIO_EVIDENCE_BRIDGE_BLOCKED "+str(exc),file=sys.stderr)
        return 2

if __name__=="__main__":
    sys.exit(main())
