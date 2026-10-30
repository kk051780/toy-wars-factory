"""Read-only admission gate: native GitHub run/job/artifact metadata plus raw downloaded ZIP.

Never equate caller-supplied/mock response to authenticated GitHub. The optional
API reader is restricted to the repository's public GitHub REST host and cannot
call Roblox. Provider-authentication/approvals and upload are out of scope.
"""
from __future__ import annotations
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import Any
import hashlib
import json
import re
import zipfile

REPO = 'kk051780/toy-wars-factory'
WORKFLOW = '.github/workflows/toy-wars-rojo-build-only.yml'
ARTIFACT = 'twf-rojo-build-only-rbxl'
BINARY = 'toy-wars-private-test.rbxl'
RECEIPT = 'build-receipt.json'
MAX_ZIP = 12_000_000
MAX_RBXL = 10_000_000
SHA = re.compile(r'[0-9a-f]{40}\Z')
DIGEST = re.compile(r'[0-9a-f]{64}\Z')
MAGIC = b'<roblox!\x89\xff\r\n\x1a\n'

class AdmissionError(ValueError):
    pass

def _require(ok: bool, reason: str) -> None:
    if not ok: raise AdmissionError(reason)

def _positive(n: Any) -> bool:
    return type(n) is int and 1 <= n <= 2**63 - 1

@dataclass(frozen=True)
class Expected:
    source_sha: str
    run_id: int
    artifact_id: int

    def check(self) -> None:
        _require(type(self.source_sha) is str and SHA.fullmatch(self.source_sha) is not None,
                 'pinned main commit SHA required')
        _require(_positive(self.run_id) and _positive(self.artifact_id),
                 'integer GitHub run / artifact identifiers required')

def verify_metadata(expected: Expected, run: Any, jobs: Any, artifacts: Any) -> dict:
    """Check 3 independently acquired REST resources (caller MUST authenticate GET)."""
    expected.check()
    _require(type(run) is dict and run.get('id') == expected.run_id and
             type(run.get('head_sha')) is str and run['head_sha'] == expected.source_sha and
             run.get('head_branch') == 'main' and run.get('event') == 'workflow_dispatch' and
             run.get('status') == 'completed' and run.get('conclusion') == 'success' and
             _positive(run.get('run_attempt')) and
             run.get('repository', {}).get('full_name') == REPO and
             type(run.get('path')) is str and run['path'] == WORKFLOW + '@refs/heads/main',
             'GitHub builder run ID/ref/workflow/source/status mismatch')
    _require(type(jobs) is dict and type(jobs.get('jobs')) is list and
             type(jobs.get('total_count')) is int and jobs['total_count'] == len(jobs['jobs']) and
             1 <= len(jobs['jobs']) <= 12, 'partial or invalid GitHub job list')
    seen=set(); matched=0
    for job in jobs['jobs']:
        _require(type(job) is dict and _positive(job.get('id')) and job['id'] not in seen and
                 job.get('run_id') == expected.run_id and job.get('head_sha') == expected.source_sha and
                 job.get('run_attempt') == run.get('run_attempt') and job.get('status') == 'completed' and
                 job.get('conclusion') == 'success', 'job failed/mismatched run/attempt/commit')
        seen.add(job['id'])
        if job.get('name') == 'rojo-build-only': matched+=1
    _require(matched == 1, 'must have exactly one successful Rojo builder job')
    _require(type(artifacts) is dict and type(artifacts.get('artifacts')) is list and
             type(artifacts.get('total_count')) is int and
             artifacts['total_count'] == len(artifacts['artifacts']) and
             1 <= len(artifacts['artifacts']) <= 100,
             'partial GitHub artifact metadata not admissible')
    selected=[a for a in artifacts['artifacts'] if type(a) is dict and a.get('id') == expected.artifact_id]
    _require(len(selected) == 1, 'artifact ID not unique or missing from run')
    artifact=selected[0]
    digest=artifact.get('digest')
    link=artifact.get('workflow_run')
    _require(artifact.get('name') == ARTIFACT and artifact.get('expired') is False and
             type(artifact.get('size_in_bytes')) is int and artifact['size_in_bytes']>0 and
             artifact['size_in_bytes']<=MAX_ZIP and type(digest) is str and
             digest.startswith('sha256:') and DIGEST.fullmatch(digest[7:]) is not None and
             type(link) is dict and link.get('id') == expected.run_id and
             link.get('head_sha') == expected.source_sha and link.get('head_branch') == 'main',
             'artifact metadata missing authentic run/source/digest binding')
    return {'repository':REPO,'build_run_id':expected.run_id,
            'artifact_id':expected.artifact_id,'archive_sha256':digest[7:],
            'archive_bytes':artifact['size_in_bytes'],'source_sha':expected.source_sha,
            'metadata_consistent_untrusted':True,'provider_authenticated':False,
            'secret_access_authorized':False,'roblox_saved_authorized':False}

def verify_zip(archive_path: str | Path, metadata: dict) -> dict:
    """Bounded ZIP, authenticated archive digest and source->RBXL receipt cross-check.

    No extraction to disk. Prevent symlink/zip bomb/duplicate traversal and unknown files.
    """
    _require(type(metadata) is dict and metadata.get('repository') == REPO and
             type(metadata.get('source_sha')) is str and SHA.fullmatch(metadata['source_sha']) is not None and
             type(metadata.get('archive_sha256')) is str and DIGEST.fullmatch(metadata['archive_sha256']) is not None and
             type(metadata.get('archive_bytes')) is int and 1 <= metadata['archive_bytes'] <= MAX_ZIP,
             'invalid supplied archive metadata')
    p=Path(archive_path)
    _require(p.suffix == '.zip' and not p.is_symlink() and p.is_file() and
             p.stat().st_size == metadata['archive_bytes'], 'missing or altered GitHub ZIP')
    with p.open('rb') as f: data=f.read(MAX_ZIP+1)
    _require(len(data) == metadata['archive_bytes'] and hashlib.sha256(data).hexdigest() == metadata['archive_sha256'],
             'downloaded GitHub ZIP digest differs from actual Actions metadata')
    try:
        with zipfile.ZipFile(BytesIO(data)) as z:
            members=z.infolist()
            _require(len(members)==2 and {x.filename for x in members}=={BINARY,RECEIPT},
                     'ZIP must contain exactly one binary and one build receipt')
            for m in members:
                mode=m.external_attr >> 16
                _require(m.filename in {BINARY,RECEIPT} and not m.is_dir() and
                         (mode & 0o170000) not in {0o120000,0o040000} and
                         m.compress_type in {zipfile.ZIP_DEFLATED,zipfile.ZIP_STORED} and
                         m.flag_bits & 1 == 0 and
                         m.file_size <= (MAX_RBXL if m.filename==BINARY else 4096),
                         'unsafe compressed artifact member')
            with z.open(BINARY) as stream:
                binary=stream.read(MAX_RBXL+1)
            with z.open(RECEIPT) as stream:
                raw=stream.read(4097)
    except (OSError,ValueError,zipfile.BadZipFile,RuntimeError,EOFError) as exc:
        raise AdmissionError('invalid GitHub builder ZIP format') from None
    _require(40 <= len(binary) <= MAX_RBXL and binary.startswith(MAGIC) and len(raw)<=4096,
             'invalid actual RBXL or receipt payload')
    try: receipt=json.loads(raw)
    except (ValueError,UnicodeError): raise AdmissionError('invalid JSON builder receipt') from None
    _require(type(receipt) is dict and set(receipt)=={'repository','source_main_sha','rbxl_sha256','rbxl_bytes','build_only','engine_verified'},
             'invalid builder receipt keys')
    _require(receipt['repository']==REPO and receipt['source_main_sha']==metadata['source_sha'] and
             receipt['rbxl_bytes']==len(binary) and type(receipt['rbxl_bytes']) is int and
             receipt['rbxl_sha256']==hashlib.sha256(binary).hexdigest() and
             receipt['build_only'] is True and receipt['engine_verified'] is False,
             'builder manifest != source/artifact bytes')
    return {'status':'BUILD_ADMISSION_DATA_CONSISTENT_NOT_PROVIDER_ATTESTED',
            'repository':REPO,'source_main_sha':metadata['source_sha'],
            'build_run_id':metadata.get('build_run_id'), 'artifact_id':metadata.get('artifact_id'),
            'archive_sha256':metadata['archive_sha256'],
            'rbxl_sha256':receipt['rbxl_sha256'],'rbxl_bytes':len(binary),
            'rbxl_origin_authenticated':False,'roblox_saved_authorized':False,
            'roblox_engine_verified':False,'public_publish_authorized':False}
