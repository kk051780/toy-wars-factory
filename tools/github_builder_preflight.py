#!/usr/bin/env python3
"""Read-only run/artifact admission; never reads Roblox keys, uploads or publishes.

The GitHub token is only used for private repository metadata GETs through
explicit exact GitHub REST API endpoints. Downloaded ZIP is supplied by host
and verified against the Actions artifact SHA256 digest.
"""
from __future__ import annotations
import argparse
import json
import os
import re
import sys
from pathlib import Path
from urllib.parse import urlsplit
import urllib.request
import urllib.error
from github_artifact_admission import Expected, AdmissionError, verify_metadata, verify_zip, REPO

BASE='https://api.github.com/repos/'+REPO

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl): return None

def github_json(path:str, *, token:str, opener=None):
    if type(token) is not str or len(token)<16 or len(token)>8192:
        raise AdmissionError('missing read-only workflow GitHub token')
    if re.fullmatch(r'/actions/runs/[1-9][0-9]{0,18}(?:/(?:jobs|artifacts)\?per_page=100)?',path) is None:
        raise AdmissionError('nonallowlisted GitHub REST resource path')
    opener=opener or urllib.request.build_opener(NoRedirect())
    req=urllib.request.Request(BASE+path,headers={'Authorization':'Bearer '+token,'Accept':'application/vnd.github+json','X-GitHub-Api-Version':'2022-11-28'},method='GET')
    try:
        with opener.open(req,timeout=12) as response:
            if response.geturl()!=BASE+path:raise AdmissionError('GitHub API redirect blocked')
            raw=response.read(500_001)
    except (urllib.error.HTTPError,urllib.error.URLError,OSError,TimeoutError):
        raise AdmissionError('GitHub metadata fetch failed, no secret details') from None
    if len(raw)>500_000:raise AdmissionError('GitHub JSON too large')
    try: data=json.loads(raw)
    except (ValueError,UnicodeError):raise AdmissionError('invalid GitHub metadata') from None
    if type(data) is not dict: raise AdmissionError('non-object GitHub metadata')
    return data

def download_artifact_zip(*, artifact_id:int, token:str, target:str|Path, opener=None) -> None:
    """2-hop read-only official artifact download; GitHub token never reaches CDN."""
    if type(artifact_id) is not int or artifact_id<=0 or artifact_id>2**63-1:
        raise AdmissionError('invalid artifact ID')
    if type(token) is not str or not 16<=len(token)<=8192:
        raise AdmissionError('missing read-only GitHub token')
    opener=opener or urllib.request.build_opener(NoRedirect())
    url=f'{BASE}/actions/artifacts/{artifact_id}/zip'
    request=urllib.request.Request(url,method='GET',headers={
        'Authorization':'Bearer '+token,'Accept':'application/vnd.github+json',
        'X-GitHub-Api-Version':'2022-11-28'})
    try:
        try:
            response=opener.open(request,timeout=12)
        except urllib.error.HTTPError as redirect:
            response=redirect
        code=response.code
        if code not in (301,302,303,307,308):
            raise AdmissionError('artifact REST did not return a signed download location')
        location=response.headers.get('Location','')
        response.close()
        parsed=urlsplit(location)
        host=(parsed.hostname or '').lower()
        # No token or auth header travels to the signed CDN URL.
        if (parsed.scheme!='https' or parsed.username or parsed.password or parsed.port is not None or
            not ((host.endswith('.blob.core.windows.net') and host!='.blob.core.windows.net') or
                 (host.endswith('.actions.githubusercontent.com') and host!='.actions.githubusercontent.com') or
                 host=='objects.githubusercontent.com') or not parsed.path or parsed.fragment):
            raise AdmissionError('artifact redirect host not on trusted GitHub CDN allowlist')
        req=urllib.request.Request(location,method='GET',headers={'Accept':'application/octet-stream'})
        with opener.open(req,timeout=20) as cdn:
            if cdn.geturl()!=location:
                raise AdmissionError('unexpected artifact CDN redirect')
            chunks=[]; total=0
            while True:
                c=cdn.read(64*1024)
                if not c: break
                total+=len(c)
                if total>12_000_000:
                    raise AdmissionError('downloaded artifact exceeds byte limit')
                chunks.append(c)
        if total<1:raise AdmissionError('artifact download empty')
        path=Path(target)
        if path.exists() or path.is_symlink() or path.suffix!='.zip' or not path.parent.is_dir():
            raise AdmissionError('artifact target must be a new regular ZIP path')
        with path.open('xb') as f:
            for c in chunks:f.write(c)
    except (urllib.error.HTTPError,urllib.error.URLError,OSError,TimeoutError) as exc:
        raise AdmissionError('GitHub Actions artifact download failed') from None


def main(argv=None,environ=None):
    p=argparse.ArgumentParser(description='A14 no-Roblox read-only GitHub build artifact admission')
    p.add_argument('--live-metadata',action='store_true')
    p.add_argument('--run-id',type=int)
    p.add_argument('--artifact-id',type=int)
    p.add_argument('--archive')
    p.add_argument('--download',action='store_true',help='Read-only GET exact artifact archive, no Roblox')
    ns=p.parse_args(argv)
    env=dict(os.environ if environ is None else environ)
    if not ns.live_metadata:
        print(json.dumps({'status':'READ_ONLY_DEFAULT','network_calls':0,'roblox_calls':0,'secret_calls':0}))
        return 0
    try:
        if env.get('GITHUB_ACTIONS')!='true' or env.get('GITHUB_REF')!='refs/heads/main' or env.get('GITHUB_REPOSITORY')!=REPO or env.get('GITHUB_EVENT_NAME')!='workflow_dispatch':
            raise AdmissionError('must run on protected reviewed main and manual dispatch')
        expected=Expected(source_sha=env.get('GITHUB_SHA',''),run_id=ns.run_id,artifact_id=ns.artifact_id)
        expected.check()
        if not ns.archive:raise AdmissionError('reviewed artifact ZIP path required')
        token=env.get('GH_TOKEN','')
        run=github_json(f'/actions/runs/{expected.run_id}',token=token)
        jobs=github_json(f'/actions/runs/{expected.run_id}/jobs?per_page=100',token=token) # handled separately
        arts=github_json(f'/actions/runs/{expected.run_id}/artifacts?per_page=100',token=token)
        metadata=verify_metadata(expected,run,jobs,arts)
        if ns.download:
            download_artifact_zip(artifact_id=expected.artifact_id,token=token,target=ns.archive)
        result=verify_zip(ns.archive,metadata)
        print(json.dumps(result,sort_keys=True))
        return 0
    except (AdmissionError,OSError,TypeError,ValueError):
        print(json.dumps({'status':'BLOCKED_BUILD_ARTIFACT','roblox_calls':0,'publications':0,'provider_authenticated':False}),file=sys.stderr)
        return 2

if __name__=='__main__':sys.exit(main())
