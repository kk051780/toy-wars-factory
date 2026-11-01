"""Protected, no-CLI Roblox Cloud v2 task-create POST transport candidate.

NOT an authorization gate: a trusted host must separately verify private target,
source/version, scoped key, GitHub source and globally reserved task intent.
No default credentials, environment discovery, retries, or unattended entrypoint.
All output authority/engine flags are False, even after an HTTP 200 response.
Requires explicitly injected opener + local one-process fence; not cross-host CAS.
"""
from __future__ import annotations
from dataclasses import dataclass
import hashlib
import json
import re
import ssl
import threading
import urllib.request

HOST = 'https://apis.roblox.com'
SMOKE_SHA256 = 'fc343ede29c2466b0962689b183b5320d81122a807d65ad7f82e942a9268759d'
SCRIPT_TIMEOUT = '30s'
MAX_SCRIPT_BYTES = 8192
MAX_ACK_BYTES = 32768
TIMEOUT_SECONDS = 8
ID = re.compile(r'[1-9][0-9]{0,18}\Z')
UUID = re.compile(r'[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}\Z')

class TaskHold(ValueError):
    """Only non-secret constant error messages."""

def need(ok: bool, reason: str) -> None:
    if not ok:
        raise TaskHold(reason)

@dataclass(frozen=True)
class Target:
    universe_id: str
    place_id: str
    saved_version_id: str

    def create_path(self) -> str:
        vals=(self.universe_id,self.place_id,self.saved_version_id)
        need(all(type(v) is str and ID.fullmatch(v) is not None for v in vals),
             'INVALID_EXPLICIT_PRIVATE_VERSION_TARGET')
        return (f'universes/{self.universe_id}/places/{self.place_id}/'
                f'versions/{self.saved_version_id}/luau-execution-session-tasks')

@dataclass(frozen=True)
class FixedRequest:
    method: str
    url: str
    body: bytes
    script_sha256: str
    body_sha256: str


def prepare(target: Target, smoke_script: bytes) -> FixedRequest:
    need(type(target) is Target, 'INVALID_TARGET')
    path=target.create_path()
    need(type(smoke_script) is bytes and 0<len(smoke_script)<=MAX_SCRIPT_BYTES and
         hashlib.sha256(smoke_script).hexdigest()==SMOKE_SHA256,
         'UNREVIEWED_SCRIPT_BYTES')
    try:
        script=smoke_script.decode('utf-8',errors='strict')
    except UnicodeError:
        raise TaskHold('UNREVIEWED_SCRIPT_BYTES') from None
    payload=json.dumps({'script':script,'timeout':SCRIPT_TIMEOUT},
                       ensure_ascii=False,separators=(',',':'),allow_nan=False).encode('utf-8')
    return FixedRequest('POST',f'{HOST}/cloud/v2/{path}',payload,
                        SMOKE_SHA256,hashlib.sha256(payload).hexdigest())

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def hardened_opener():
    return urllib.request.build_opener(
        urllib.request.ProxyHandler({}),NoRedirect(),
        urllib.request.HTTPSHandler(context=ssl.create_default_context()))


def strict_ack(raw: bytes, target: Target, original_script: str):
    need(type(raw) is bytes and len(raw)<=MAX_ACK_BYTES,'INVALID_ACK_SIZE')
    def duplicate_reject(rows):
        obj={}
        for k,v in rows:
            need(k not in obj,'DUPLICATE_ACK_JSON_KEY')
            obj[k]=v
        return obj
    def nonfinite(_): raise TaskHold('NONFINITE_ACK_JSON')
    try:
        d=json.loads(raw.decode('utf-8',errors='strict'),object_pairs_hook=duplicate_reject,
                     parse_constant=nonfinite)
    except TaskHold: raise
    except (UnicodeError,ValueError,RecursionError):
        raise TaskHold('MALFORMED_ACK') from None
    need(type(d) is dict,'MALFORMED_ACK')
    required=('path','script','timeout','state')
    need(all(k in d for k in required) and
         type(d['path']) is str and type(d['script']) is str and
         type(d['timeout']) is str and type(d['state']) is str,'MISSING_TYPED_ACK_FIELD')
    prefix=(f'universes/{target.universe_id}/places/{target.place_id}/'
            f'versions/{target.saved_version_id}/luau-execution-sessions/')
    pattern=rf'{re.escape(prefix)}{UUID.pattern[:-2]}/tasks/{UUID.pattern[:-2]}\Z'
    need(re.fullmatch(pattern,d['path']) is not None,'ACK_TARGET_VERSION_MISMATCH')
    need(d['script']==original_script and d['timeout']==SCRIPT_TIMEOUT,
         'ACK_SCRIPT_TIMEOUT_MISMATCH')
    need(d['state'] in ('QUEUED','PROCESSING','COMPLETE') and
         d.get('error') is None,'ACK_FAILED_OR_UNKNOWN_STATE')
    return d['path'],d['state']


class LocalIntentFence:
    """TEST/ONE-PROCESS interlock; never a cross-process or external CAS proof.

    This local fence does not authorize API traffic or prove that a GitHub / Roblox
    identity was authenticated. Production requires a separate durable, genuine
    compare-and-swap reservation from the reviewed PR #158 integration.
    """
    def __init__(self):
        self._lock=threading.Lock()
        self._consumed=set()

    def consume_once(self, key: str) -> None:
        need(type(key) is str and len(key)==64, 'INVALID_INTENT_FINGERPRINT')
        with self._lock:
            need(key not in self._consumed, 'DUPLICATE_INTENT_DENIED')
            self._consumed.add(key)  # durable for this process lifetime, even on lost ACK

class OneShotPoster:
    """One consumed attempt per object, even for timeout/unknown POST outcome.

    Creating this class or LocalIntentFence is not permission to POST.
    Missing transport/fence FAILS CLOSED. A new process can bypass local fencing.
    Future reviewed host must
    externally validate secrets, current task intent CAS and private-version
    attestation. Neither booleans nor an injected opener prove these controls.
    """
    def __init__(self, request: FixedRequest, target: Target, script: bytes, *, api_key: str, opener=None, intent_fence=None):
        need(type(request) is FixedRequest and type(target) is Target,
             'INVALID_FIXED_REQUEST')
        need(type(api_key) is str and 16<=len(api_key)<=8192 and
             not any(c in api_key for c in '\r\n\x00'), 'INVALID_SCOPED_KEY')
        expected=prepare(target,script)
        need(request==expected,'MODIFIED_FIXED_REQUEST')
        self._r=request
        self._t=target
        self._script=script.decode('utf-8')
        self._key=api_key
        # An omitted opener must never implicitly open a real network connection.
        need(opener is not None, 'UNTRUSTED_HOST_TRANSPORT_NOT_INSTALLED')
        need(type(intent_fence) is LocalIntentFence, 'LOCAL_FENCE_REQUIRED')
        self._opener=opener
        need(callable(getattr(self._opener,'open',None)), 'INVALID_TRANSPORT')
        self._fence=intent_fence
        self._fingerprint=hashlib.sha256((self._r.url+'\n'+self._r.body_sha256).encode('ascii')).hexdigest()
        self._attempted=False

    def submit_once(self) -> dict:
        need(not self._attempted,'DUPLICATE_POST_DENIED')
        self._fence.consume_once(self._fingerprint) # before any I/O; within this process only
        self._attempted=True  # before any I/O; no retry on lost ACK
        req=urllib.request.Request(self._r.url,method='POST',data=self._r.body,
               headers={'x-api-key':self._key,'Content-Type':'application/json',
                        'Accept':'application/json'})
        try:
            with self._opener.open(req,timeout=TIMEOUT_SECONDS) as res:
                need(res.geturl()==self._r.url,'REDIRECT_DENIED')
                need(type(res.status) is int and res.status==200,'UNEXPECTED_POST_STATUS')
                ct=res.headers.get('Content-Type','')
                need(type(ct) is str and
                     ct.lower().split(';',1)[0].strip()=='application/json',
                     'UNEXPECTED_ACK_CONTENT_TYPE')
                raw=res.read(MAX_ACK_BYTES+1)
        except TaskHold: raise
        except Exception:
            raise TaskHold('POST_OUTCOME_UNKNOWN_NO_RETRY') from None
        path,state=strict_ack(raw,self._t,self._script)
        return {'status':'UNTRUSTED_CLOUD_CREATE_ACK',
                'task_path_claim':path,'task_state_claim':state,
                'request_body_sha256':self._r.body_sha256,
                'script_sha256':self._r.script_sha256,
                'ack_raw_sha256':hashlib.sha256(raw).hexdigest(),
                'post_attempts':1,'automatic_retries':0,'may_retry_post':False,
                'api_key_returned':False,'raw_ack_returned':False,
                'provider_authenticated':False,'private_target_authenticated':False,
                'saved_version_authenticated':False,'intent_reserved_authenticated':False,
                'engine_verified':False,'may_publish':False,'may_merge':False}
