#!/usr/bin/env python3
"""Fail-closed event audit for staged GH-AW Markdown and generated Actions lock.

A check on YAML *event declarations*, not full YAML validity, model authentication,
actor attestation or execution authority. An unfamiliar YAML encoding is denied.
Intended as extra independent protection after `gh aw compile --strict`.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
from pathlib import Path

# Reviewed exact frontmatter SHA256; editorial body updates remain possible.
# This is source-policy integrity, NOT compiler or provider attestation.
APPROVED_FRONTMATTER_SHA256 = "2d82661d394cf9e9422becc924b8edcc4ca2628e8bc243b076b39dfd8798202c"

ROOT_ON = re.compile(r'''^(?:on|"on"|'on'):\s*(.*?)\s*$''')
EVENT = re.compile(r'^  ([a-zA-Z_][a-zA-Z_0-9-]*):(?:[ \t].*)?$')

class UnsafeTrigger(ValueError):
    pass

def get_frontmatter(markdown:str)->str:
    if type(markdown) is not str or not markdown.startswith('---\n'):
        raise UnsafeTrigger('MISSING_MARKDOWN_FRONTMATTER')
    pos=markdown.find('\n---\n',4)
    if pos<0:
        raise UnsafeTrigger('UNCLOSED_FRONTMATTER')
    return markdown[4:pos]+'\n'

def event_names(yaml: str)->set[str]:
    if type(yaml) is not str or len(yaml.encode('utf-8'))>2_000_000 or '\t' in yaml:
        raise UnsafeTrigger('UNTRUSTED_YAML')
    lines=yaml.splitlines()
    on=[]
    for i,line in enumerate(lines):
        match=ROOT_ON.fullmatch(line)
        if match:
            on.append((i,match.group(1)))
    if len(on)!=1:
        raise UnsafeTrigger('NO_UNIQUE_ON')
    i,inline=on[0]
    if inline:
        # Non-mapping event formats, YAML aliases/tags, flow mappings etc are
        # unsupported to avoid reading a schedule as a harmless comment.
        if inline!='workflow_dispatch':
            raise UnsafeTrigger('UNSUPPORTED_INLINE_ON')
        return {'workflow_dispatch'}
    events=[]
    for line in lines[i+1:]:
        if not line.strip() or line.lstrip().startswith('#'):
            continue
        if not line.startswith(' '):
            break
        item=EVENT.fullmatch(line)
        if item:
            events.append(item.group(1))
        elif line.startswith('  ') and not line.startswith('    '):
            raise UnsafeTrigger('UNPARSEABLE_EVENT_KEY')
        elif not events:
            raise UnsafeTrigger('NO_EVENT_BEFORE_NESTING')
        # Reject YAML merge keys or directives that can alias additional events.
        if '<<:' in line or ' !' in line or re.search(r'(^|\s)[&*][a-zA-Z_]',line):
            raise UnsafeTrigger('UNSUPPORTED_YAML_ANCHOR')
    if not events or len(events)!=len(set(events)):
        raise UnsafeTrigger('MISSING_OR_DUPLICATE_EVENT')
    return set(events)

def secure_network(markdown:str)->bool:
    """Conservative source-only guard; gh-aw --strict remains the real YAML validator.

    Explicit default ecosystem only, exactly once, no separate strict override.
    Reject different casing, aliases and flow maps rather than second-guess YAML.
    """
    if type(markdown) is not str:
        return False
    try:
        fm=get_frontmatter(markdown)
    except UnsafeTrigger:
        return False
    lines=fm.splitlines()
    if lines.count('network: defaults') != 1:
        return False
    if any(line.startswith(('network:', '"network":', "'network':", 'strict:'))
           for line in lines if line != 'network: defaults'):
        return False
    if any('<<:' in line or re.search(r'(^|\s)[&*][a-zA-Z_]',line)
           for line in lines):
        return False
    return True

def check(source_md:str,lock_yaml:str)->dict:
    try:
        frontmatter=get_frontmatter(source_md)
        src=event_names(frontmatter)
        if not secure_network(source_md):
            raise UnsafeTrigger('UNSAFE_OR_MISSING_STRICT_NETWORK')
        if hashlib.sha256(frontmatter.encode('utf-8')).hexdigest() != APPROVED_FRONTMATTER_SHA256:
            raise UnsafeTrigger('UNREVIEWED_FRONTMATTER_CHANGE')
        compiled=event_names(lock_yaml)
        if src != {'workflow_dispatch'} or compiled != {'workflow_dispatch'}:
            raise UnsafeTrigger('UNAPPROVED_TRIGGER_PRESENT')
        status='MANUAL_ONLY_EVENT_SHAPE_OBSERVED_NOT_ENGINE_APPROVAL'
        problems=[]
    except UnsafeTrigger as e:
        status='FAIL_CLOSED'
        problems=[str(e)]
        src=locals().get('src',set())
        compiled=locals().get('compiled',set())
    return {'schema':1,'status':status,
            'approved_frontmatter_sha256':APPROVED_FRONTMATTER_SHA256,
            'approved_frontmatter_matches':(type(source_md) is str and source_md.startswith('---\n') and hashlib.sha256((locals().get('frontmatter') or '').encode('utf-8')).hexdigest()==APPROVED_FRONTMATTER_SHA256),
            'source_events':sorted(src),
            'compiled_events':sorted(compiled),'problems':problems,
            'actual_gh_aw_compiled_here':False,'model_entitlement_proven':False,
            'model_spending_cap_proven':False,'independent_review_proven':False,
            'may_activate':False,'may_run_model':False,'may_write_repo':False,
            'may_merge':False,'may_spend':False,'may_publish':False,
            'may_release_any_lease':False}

def main(argv=None)->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',type=Path,required=True)
    p.add_argument('--compiled-lock',type=Path,required=True)
    a=p.parse_args(argv)
    try:
        source=a.source.read_text(encoding='utf-8')
        compiled=a.compiled_lock.read_text(encoding='utf-8')
        result=check(source,compiled)
    except (OSError,UnicodeError) as e:
        result={'schema':1,'status':'FAIL_CLOSED','problems':['FILE_UNAVAILABLE'],
                'may_activate':False,'may_run_model':False}
    print(json.dumps(result,sort_keys=True,indent=2))
    # The probe cannot approve activation, but a matching event shape is a
    # passing *unit diagnostic* for a further independent gate.
    return 0 if result['status'].startswith('MANUAL_ONLY_') else 2

if __name__=='__main__':
    raise SystemExit(main())
