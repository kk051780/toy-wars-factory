#!/usr/bin/env python3
"""Read-only original-GitHub HTTPS input collector for stale manual-GO preflight.

No scheduler, no dispatch, no approvals and no provider attestation emitted in
returned JSON. The caller must independently prove that an actual trusted host
executed this exact source with an original GitHub-issued credential. Injectable
GET fixtures prove only test behavior, not provider identity.
"""
from __future__ import annotations

import base64
from hashlib import sha1
import json
import re
from urllib import request, error

from tools import system_manual_go_priority_preflight as pre

REPO = pre.REPO
REPO_ID = 1431683395
ROOT = f'https://api.github.com/repos/{REPO}'
CONTROL = pre.CONTROL_BRANCH
COORD_PATH = 'ops/REPAIR_COORDINATOR.json'
REQUEST_PATH = 'ops/WORK_REQUESTS.json'
API_VERSION = '2022-11-28'
_MAX_JSON = 2_000_000
_MAX_FILE = 1_000_000
_SHA = re.compile(r'[0-9a-f]{40}\Z')


class ReadError(ValueError):
    """Fixed, non-sensitive error codes only."""


def check(pred, code):
    if not pred:
        raise ReadError(code)


def unique(pairs):
    obj = {}
    for k, v in pairs:
        check(k not in obj, 'DUPLICATE_JSON_FIELD')
        obj[k] = v
    return obj


def nonfinite(_):
    raise ReadError('NONFINITE_JSON')


def parse_json(raw):
    check(type(raw) is bytes and len(raw) <= _MAX_JSON, 'INVALID_GITHUB_JSON')
    try:
        result = json.loads(raw, object_pairs_hook=unique, parse_constant=nonfinite)
    except ReadError:
        raise
    except Exception:
        raise ReadError('INVALID_GITHUB_JSON') from None
    check(type(result) is dict, 'INVALID_GITHUB_JSON')
    return result


def gitsha(blob):
    return sha1(b'blob ' + str(len(blob)).encode('ascii') + b'\x00' + blob).hexdigest()


class NoRedirect(request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


class GitHubGet:
    """An HTTPS GET-only client to four literal endpoint families; no redirects."""
    def __init__(self, token, *, opener=None):
        check(type(token) is str and 0 < len(token) <= 4096, 'TOKEN_NOT_AVAILABLE')
        self.token = token
        self._open = opener or request.build_opener(NoRedirect()).open

    @staticmethod
    def allowed_url(url):
        if type(url) is not str:
            return False
        refs = {f'{ROOT}/git/ref/heads/main', f'{ROOT}/git/ref/heads/{CONTROL}', ROOT}
        if url in refs:
            return True
        return any(url.startswith(f'{ROOT}/contents/{path}?ref=') and
                   _SHA.fullmatch(url.split('?ref=', 1)[-1]) is not None
                   for path in (COORD_PATH, REQUEST_PATH))

    def __call__(self, url):
        check(self.allowed_url(url), 'URL_NOT_ALLOWLISTED')
        req = request.Request(url, method='GET', headers={
            'Authorization': 'Bearer ' + self.token,
            'Accept': 'application/vnd.github+json',
            'X-GitHub-Api-Version': API_VERSION,
            'User-Agent': 'twf-manual-go-priority-guard'})
        try:
            with self._open(req, timeout=12) as resp:
                check(resp.getcode() == 200, 'GITHUB_NON_200')
                raw = resp.read(_MAX_JSON + 1)
                check(len(raw) <= _MAX_JSON, 'GITHUB_RESPONSE_TOO_LARGE')
                return parse_json(raw)
        except ReadError:
            raise
        except Exception:
            raise ReadError('GITHUB_GET_FAILED') from None


def get_ref(reader, branch):
    x = reader(f'{ROOT}/git/ref/heads/{branch}')
    check(type(x) is dict and x.get('ref') == f'refs/heads/{branch}' and
          type(x.get('object')) is dict and
          type(x['object'].get('sha')) is str and
          _SHA.fullmatch(x['object']['sha']) and
          x['object'].get('type') == 'commit', 'INVALID_GIT_REF')
    return x['object']['sha']


def get_file(reader, branch_sha, path):
    x = reader(f'{ROOT}/contents/{path}?ref={branch_sha}')
    check(type(x) is dict and x.get('type') == 'file' and
          x.get('path') == path and x.get('encoding') == 'base64' and
          type(x.get('size')) is int and 0 <= x['size'] <= _MAX_FILE and
          type(x.get('content')) is str and
          type(x.get('sha')) is str and _SHA.fullmatch(x['sha']), 'INVALID_GIT_FILE')
    try:
        content = base64.b64decode(x['content'].replace('\r', '').replace('\n', ''), validate=True)
    except Exception:
        raise ReadError('INVALID_GIT_FILE') from None
    check(len(content) == x['size'] and len(content) <= _MAX_FILE and
          gitsha(content) == x['sha'], 'GIT_FILE_HASH_MISMATCH')
    return parse_json(content)


def collect_preflight(reader):
    """Injectable GET callback. Original GitHub provenance must be verified outside."""
    check(callable(reader), 'READER_NOT_AVAILABLE')
    metadata = reader(ROOT)
    check(type(metadata) is dict and metadata.get('id') == REPO_ID and
          metadata.get('full_name') == REPO and
          metadata.get('private') is True, 'REPOSITORY_ID_MISMATCH')
    main = get_ref(reader, 'main')
    coord = get_ref(reader, CONTROL)
    state = get_file(reader, coord, COORD_PATH)
    requests = get_file(reader, coord, REQUEST_PATH)
    # Reject ref changes across the bounded read. A stable ref is not an atomic
    # snapshot nor cryptographic evidence of the callback's true source.
    check(get_ref(reader, 'main') == main and get_ref(reader, CONTROL) == coord,
          'GIT_REF_DRIFT')
    result = pre.preflight(repository=REPO, current_main_sha=main,
        coordinator_ref=coord, work_requests_ref=coord,
        coordinator=state, work_requests=requests)
    result['reader_input_class'] = 'CALLBACK_INPUT_NOT_PROVIDER_ATTESTED'
    result['git_ref_consistent_two_pass'] = True
    result['host_callback_get_count'] = 7
    return result


def main():
    import os
    import sys
    try:
        summary = collect_preflight(GitHubGet(os.environ.get('GITHUB_TOKEN', '')))
        print(json.dumps(summary, sort_keys=True, ensure_ascii=False))
        return 0 if summary['status'] == 'SNAPSHOT_CONSISTENT_FURTHER_HOST_CHECKS_REQUIRED' else 2
    except ReadError as exc:
        print(json.dumps({'schema': 1, 'status': 'BLOCK_SOURCE_GET',
            'reason': str(exc), 'may_dispatch': False, 'may_write': False}))
        return 2
    except Exception:
        print(json.dumps({'schema': 1, 'status': 'BLOCK_SOURCE_GET',
            'reason': 'UNEXPECTED_ERROR', 'may_dispatch': False, 'may_write': False}))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
