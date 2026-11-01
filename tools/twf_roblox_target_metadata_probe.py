"""Read-only, bounded Roblox Cloud v2 universe/place metadata preflight.

A successful response here verifies only caller-supplied IDs against the returned
resource paths. It NEVER establishes ownership, nonpublic status, Saved version,
credentials provenance, or permission for upload, execute, publish or merge.
Protected draft; not installed in unattended workflows or run without separate
trust-root review. Exactly two GETs maximum; no retry, proxy inheritance, POST.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import re
import ssl
import urllib.request

HOST = 'https://apis.roblox.com'
ID = re.compile(r'[1-9][0-9]{0,18}\Z')
MAX_BODY_BYTES = 65536
TIMEOUT_SECONDS = 8


class TargetHold(ValueError):
    """Bounded error token, never includes input, API key or response content."""


def ensure(ok, reason):
    if not ok:
        raise TargetHold(reason)


@dataclass(frozen=True)
class Target:
    test_universe_id: str
    test_place_id: str
    production_universe_id: str | None = None
    production_place_id: str | None = None

    def paths(self):
        ids = (self.test_universe_id, self.test_place_id)
        ensure(all(type(x) is str and ID.fullmatch(x) for x in ids), 'INVALID_TEST_TARGET')
        prod = (self.production_universe_id, self.production_place_id)
        if prod != (None, None):
            ensure(all(type(x) is str and ID.fullmatch(x) for x in prod),
                   'INVALID_PRODUCTION_REFERENCE')
            ensure(self.test_universe_id != self.production_universe_id and
                   self.test_place_id != self.production_place_id,
                   'PRODUCTION_TARGET_COLLISION')
        return (f'universes/{self.test_universe_id}',
                f'universes/{self.test_universe_id}/places/{self.test_place_id}')


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        return None


def no_proxy_opener():
    return urllib.request.build_opener(
        urllib.request.ProxyHandler({}),
        NoRedirect(),
        urllib.request.HTTPSHandler(context=ssl.create_default_context()),
    )


def _decode_exact_json(raw):
    ensure(type(raw) is bytes and len(raw) <= MAX_BODY_BYTES,
           'UNSAFE_METADATA_RESPONSE')
    def pairs(rows):
        obj = {}
        for key, value in rows:
            ensure(key not in obj, 'DUPLICATE_JSON_FIELD')
            obj[key] = value
        return obj
    def nonfinite(_):
        raise TargetHold('NONFINITE_JSON_VALUE')
    try:
        obj = json.loads(raw.decode('utf-8', errors='strict'),
                         object_pairs_hook=pairs, parse_constant=nonfinite)
    except TargetHold:
        raise
    except (ValueError, UnicodeError, RecursionError):
        raise TargetHold('UNSAFE_METADATA_RESPONSE') from None
    ensure(type(obj) is dict, 'METADATA_NOT_OBJECT')
    return obj


def _get_once(opener, path, api_key):
    url = f'{HOST}/cloud/v2/{path}'
    req = urllib.request.Request(url, method='GET', headers={
        'x-api-key': api_key, 'Accept': 'application/json'})
    try:
        with opener.open(req, timeout=TIMEOUT_SECONDS) as response:
            ensure(response.geturl() == url, 'UNEXPECTED_REDIRECT')
            ensure(type(response.status) is int and response.status == 200,
                   'UNEXPECTED_STATUS')
            ct = response.headers.get('Content-Type', '')
            ensure(type(ct) is str and
                   ct.lower().split(';', 1)[0].strip() == 'application/json',
                   'UNEXPECTED_CONTENT_TYPE')
            raw = response.read(MAX_BODY_BYTES + 1)
    except TargetHold:
        raise
    except Exception:
        raise TargetHold('GET_FAILED_NO_RETRY') from None
    payload = _decode_exact_json(raw)
    ensure(payload.get('path') == path and type(payload.get('path')) is str,
           'RESOURCE_IDENTITY_MISMATCH')
    return hashlib.sha256(raw).hexdigest()


def inspect_existing_target(target: Target, api_key: str, *, opener=None):
    """At most two GETs; caller-injected transport invalidates origin proof.

    This is NOT a provider-authenticated target attestation. No real target
    data, key, private status or response body is returned or persisted.
    """
    ensure(type(target) is Target, 'TARGET_OBJECT_INVALID')
    universe_path, place_path = target.paths()
    ensure(type(api_key) is str and 16 <= len(api_key) <= 8192 and
           not any(c in api_key for c in '\r\n\x00'), 'BAD_SCOPED_API_KEY')
    actual_opener = no_proxy_opener() if opener is None else opener
    ensure(hasattr(actual_opener, 'open') and callable(actual_opener.open),
           'TRANSPORT_INVALID')
    universe_hash = _get_once(actual_opener, universe_path, api_key)
    place_hash = _get_once(actual_opener, place_path, api_key)
    return {
        'status': 'UNTRUSTED_TARGET_METADATA_PATHS_MATCH',
        'universe_path': universe_path,
        'place_path': place_path,
        'universe_raw_sha256': universe_hash,
        'place_raw_sha256': place_hash,
        'http_get_count': 2,
        'http_post_count': 0,
        'automatic_retries': 0,
        'environment_proxy_inherited': False,
        'api_key_returned': False,
        'raw_body_returned': False,
        'provider_authenticated': False,
        'owner_authenticated': False,
        'nonpublic_status_verified': False,
        'saved_version_verified': False,
        'roblox_engine_verified': False,
        'may_upload': False,
        'may_execute': False,
        'may_publish': False,
        'may_merge': False,
    }
