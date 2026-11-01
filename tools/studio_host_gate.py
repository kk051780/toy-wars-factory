"""A14 hosted Roblox Studio local-place structural probe. No network or secrets.

This runner can record *real* Studio edit-mode loading only on a trusted Windows host.
It cannot infer engine Play, client gameplay or mobile functionality from an XML file.
"""
from __future__ import annotations
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import sys
import tempfile
from typing import Any

TWF_REPO = 'kk051780/toy-wars-factory'
EXACT_ARTIFACT_ZIP = '2f662dad3e0fd81d71aaa52f34fcf1be56406cf6aecc5637b30f6de8bdac3b7b'
EXACT_PLACE_SHA256 = '1c9bdc3dc478fe72e51870e478aa15392c47875618b86262aa7dd605e4026b33'
EXACT_PLACE_BYTES = 54753
EXACT_MAIN_SHA = 'e5deff4d5681bca4823a3da0f848e01bc089ae6e'
PASS_MARKER = 'TWF_STUDIO_LOCAL_PLACE_STRUCTURE_OK_V1'
ARTIFACT_ID = 13015999142
BUILDER_RUN_ID = 41137070161
PLACE_NAME = 'twf_source_pinned_NOT_ENGINE_VERIFIED.rbxlx'
PROBE_SCRIPT_SHA256 = '75676b530b76f6182fc5b98196759f4e0f9512562eea6b1e1510554ad6dbd549'
SIGNATURE_SENTINEL = 'TWF_STUDIO_SIGNER_VERIFIED'

class StudioProbeBlocked(RuntimeError):
    pass

def require(ok: bool, reason: str) -> None:
    if not ok:
        raise StudioProbeBlocked(reason)

def sha256_bytes(blob: bytes) -> str:
    return hashlib.sha256(blob).hexdigest()

def validate_file(data: bytes) -> dict[str,Any]:
    """Only original protected source-pinned XML, not arbitrary unreviewed code."""
    require(type(data) is bytes and len(data) == EXACT_PLACE_BYTES and
            sha256_bytes(data) == EXACT_PLACE_SHA256,
            'XML bytes do not match independently retrieved exact immutable artifact')
    require(b'<roblox version="4">' in data[:180] and b'<?xml' in data[:80],
            'place is not expected local Roblox XML format')
    return {'file_bytes':len(data),'file_sha256':EXACT_PLACE_SHA256,
            'current_main_source_sha':EXACT_MAIN_SHA,'engine_verified':False}

def parse_studio_output(stdout: str, file_output: str, stderr: str, *, exit_code: int) -> dict[str,Any]:
    """Sentinel must be in the Studio-designated output, not random stdout."""
    require(type(exit_code) is int and exit_code == 0,'Studio process exit unsuccessful')
    require(all(type(s) is str and len(s) <= 1_000_000 for s in [stdout,file_output,stderr]),
            'Studio log invalid or over limit')
    line_matches = [s.strip() for s in file_output.splitlines() if s.strip()==PASS_MARKER]
    require(len(line_matches)==1,'unique Studio output marker not found')
    combined = '\n'.join((stdout,file_output,stderr)).lower()
    for forbidden in ('traceback', 'script execution failed', 'error while loading place', 'failed to load place', 'failure to open place'):
        require(forbidden not in combined,'Studio log contains an error string')
    return {'status':'STUDIO_EDIT_MODEL_STRUCTURE_VERIFIED_ONLY',
            'studio_process_success':True,'studio_output_marker':PASS_MARKER,
            'play_mode_verified':False,'server_scripts_executed':False,
            'client_verified':False,'two_client_verified':False,'mobile_verified':False,
            'public_publish_authorized':False}

def verify_windows_studio_signature(studio: Path, *, runner=None, system=None) -> bool:
    """A non-mock call checks official Windows Authenticode before any Studio execution.

    A human-readable filename or an environment variable is never sufficient proof.
    Testing may inject a fake signature-check subprocess but the CLI does not expose it.
    """
    system = platform.system() if system is None else system
    require(system == 'Windows', 'Studio signature check only available on Windows')
    require(studio.name.lower() == 'robloxstudiobeta.exe' and studio.is_file() and not studio.is_symlink(),
            'missing official named Roblox Studio executable')
    encoded = base64.b64encode(str(studio.resolve()).encode('utf-8')).decode('ascii')
    script = ("$p=[System.Text.Encoding]::UTF8.GetString([Convert]::FromBase64String('"+encoded+"'));"
              "$s=Get-AuthenticodeSignature -LiteralPath $p;"
              "if ($s.Status -ne 'Valid' -or $null -eq $s.SignerCertificate -or "
              "$s.SignerCertificate.Subject -notmatch '(^|,\\s*)O=Roblox Corporation(\\s*,|$)') { exit 8 };"
              "Write-Output '"+SIGNATURE_SENTINEL+"'")
    runner = runner or subprocess.run
    try:
        outcome = runner(['powershell.exe', '-NoProfile', '-NonInteractive', '-Command', script],
                         capture_output=True, text=True, timeout=12, check=False, shell=False)
    except (OSError, subprocess.TimeoutExpired):
        raise StudioProbeBlocked('Roblox Studio Authenticode validation unavailable') from None
    require(outcome.returncode == 0 and outcome.stdout.strip() == SIGNATURE_SENTINEL,
            'Roblox Studio is not verifiably signed')
    return True


def validate_probe_script(script: Path) -> None:
    require(script.is_file() and not script.is_symlink() and script.name == 'twf_local_place_probe.luau',
            'trusted Luau script missing')
    data = script.read_bytes()
    require(0 < len(data) < 20000 and sha256_bytes(data) == PROBE_SCRIPT_SHA256,
            'Luau probe script changed from reviewed bytes')


def build_args(studio: Path, place: Path, script: Path, output: Path) -> list[str]:
    for p in (studio,place,script):
        require(p.is_file() and not p.is_symlink(),'Studio/script/place file absent or symlink')
    require(studio.name.lower()=='robloxstudiobeta.exe','not official Studio executable filename')
    require(place.suffix.lower()=='.rbxlx' and place.name==PLACE_NAME,'not expected XML place name')
    validate_probe_script(script)
    require(output.parent.is_dir() and not output.exists(),'output file must be newly allocated')
    return [str(studio.resolve()),'--task','RunScript','--localPlaceFile',str(place.resolve()),
            '--runScriptFile',str(script.resolve()),'--outputFile',str(output),
            '--quitAfterExecution']

def run_once(*, studio: Path, place: Path, script: Path,
             runner=None, system=None, timeout: int=140, signature_checker=None) -> dict[str,Any]:
    """One attempt only. Missing Windows Studio means fail closed, not pretend success."""
    system = platform.system() if system is None else system
    require(system=='Windows','real Studio probe requires trusted Windows host')
    require(type(timeout) is int and 30<=timeout<=180,'timeout outside bounded range')
    # Capture the reviewed bytes once, then supply Studio with private copies.
    # Original paths may be replaced during the Authenticode subprocess.
    require(place.name==PLACE_NAME and place.is_file() and not place.is_symlink(),
            'trusted XML place path required')
    require(script.name=='twf_local_place_probe.luau' and script.is_file() and not script.is_symlink(),
            'trusted Luau probe path required')
    place_bytes=place.read_bytes()
    artifact=validate_file(place_bytes)
    probe_bytes=script.read_bytes()
    require(0 < len(probe_bytes) < 20000 and sha256_bytes(probe_bytes)==PROBE_SCRIPT_SHA256,
            'Luau probe script changed from reviewed bytes')
    with tempfile.TemporaryDirectory(prefix='twf-studio-proof-') as d:
        private_place=Path(d)/PLACE_NAME
        private_script=Path(d)/'twf_local_place_probe.luau'
        # Exclusive create: never follow a pre-existing name or symlink.
        with private_place.open('xb') as f: f.write(place_bytes)
        with private_script.open('xb') as f: f.write(probe_bytes)
        log_file=Path(d)/'studio-output.log'
        cmd=build_args(studio,private_place,private_script,log_file)
        verified = (signature_checker(studio) if signature_checker is not None else
                    verify_windows_studio_signature(studio, system=system))
        require(verified is True, 'untrusted Studio executable signer')
        # Re-pin private contents *after* signature checking, before spawning.
        validate_file(private_place.read_bytes())
        validate_probe_script(private_script)
        runner=runner or subprocess.run
        try:
            p=runner(cmd, capture_output=True, text=True, timeout=timeout, check=False, shell=False)
        except (subprocess.TimeoutExpired, OSError) as exc:
            raise StudioProbeBlocked('Studio process failed or timed out; no retry') from None
        file_output=log_file.read_text(encoding='utf-8') if log_file.exists() else ''
        result=parse_studio_output(p.stdout,file_output,p.stderr,exit_code=p.returncode)
    return {**artifact, **result,'proof_origin':'UNATTESTED_LOCAL_HOST',
            'artifact_id':ARTIFACT_ID,'builder_run_id':BUILDER_RUN_ID,
            'network_calls_by_runner':0,'roblox_saved_version':None}

def main(argv=None) -> int:
    ap=argparse.ArgumentParser(description='A14 strict Studio local XML read-only smoke proof')
    ap.add_argument('--run', action='store_true',help='Requires trusted Windows Studio installation and source proof')
    ap.add_argument('--studio')
    ap.add_argument('--place')
    ap.add_argument('--script')
    ns=ap.parse_args(argv)
    if not ns.run:
        print(json.dumps({'status':'DISABLED_PLAN_ONLY','studio_runs':0,'roblox_network_calls':0,
                          'artifact_id':ARTIFACT_ID,'source_main_sha':EXACT_MAIN_SHA},sort_keys=True))
        return 0
    try:
        require(all([ns.studio,ns.place,ns.script]),'all explicit trusted local files required')
        answer=run_once(studio=Path(ns.studio),place=Path(ns.place),script=Path(ns.script))
        print(json.dumps(answer,sort_keys=True))
        return 0
    except (StudioProbeBlocked,ValueError,FileNotFoundError):
        print(json.dumps({'status':'BLOCKED_REAL_STUDIO_EXECUTION_NOT_VERIFIED',
                          'studio_runs_attested':False,'engine_verified':False}),file=sys.stderr)
        return 2
if __name__=='__main__':sys.exit(main())
