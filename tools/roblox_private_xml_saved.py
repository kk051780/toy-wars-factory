"""Fail-closed TEST-ONLY Roblox .rbxlx Saved-version bridge.

No Roblox network calls occur without an independently approved protected host,
nonpublic test IDs and a separately provisioned API key. Neither the supplied
metadata nor this module attests GitHub/Roblox provenance or engine success.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable
import hashlib
import json
import re
import urllib.request
import urllib.error
from xml.etree import ElementTree as ET

REPOSITORY = 'kk051780/toy-wars-factory'
MAIN_BASE = 'e5deff4d5681bca4823a3da0f848e01bc089ae6e'
API_ROOT = 'https://apis.roblox.com'
MAX_XML_BYTES = 10_000_000
ID = re.compile(r'[1-9][0-9]{0,18}\Z')
SHA = re.compile(r'[0-9a-f]{40}\Z')
DIGEST = re.compile(r'[0-9a-f]{64}\Z')
# Four accepted current-main Luau source byte digests independently verified
# against the real GitHub Actions installer artifact, Issue #117 2026-10-31.
SOURCE_PINS = {
    ('ReplicatedStorage','ToyWarsBalance'): ('ModuleScript','1fd6b9238e623efe523b675eb1e5e71d690991faa44f82cf485904eca4b26c87'),
    ('ServerScriptService','ToyWarsServer'): ('Script','698d99e0d991143d944dc264538177bc0b4f354ebcff0cc5a2662990af817baa'),
    ('ServerScriptService','ToyWarsSmokeTest'): ('Script','4da6ddb7630e29c5b51f3dd049d6743949df9cea5071471a8a7d34838391f8f7'),
    ('StarterPlayer','StarterPlayerScripts','ToyWarsHUD'): ('LocalScript','9767f820cfe935b3d25a32b8d6b97baeaa680fa7ceabdd2d1b4f7c3ebd483d19'),
}
EXPECTED_TOPOLOGY = {
    ('Workspace',):'Workspace',
    ('ReplicatedStorage',):'ReplicatedStorage',
    ('ReplicatedStorage','ToyWarsBalance'):'ModuleScript',
    ('ReplicatedStorage','ToyWarsSelectUnit'):'RemoteEvent',
    ('ServerScriptService',):'ServerScriptService',
    ('ServerScriptService','ToyWarsServer'):'Script',
    ('ServerScriptService','ToyWarsSmokeTest'):'Script',
    ('StarterPlayer',):'StarterPlayer',
    ('StarterPlayer','StarterPlayerScripts'):'StarterPlayerScripts',
    ('StarterPlayer','StarterPlayerScripts','ToyWarsHUD'):'LocalScript',
}

class XmlStageError(ValueError):
    pass

def demand(ok:bool,reason:str)->None:
    if not ok:raise XmlStageError(reason)

@dataclass(frozen=True)
class XmlStageConfig:
    test_universe_id: str
    test_place_id: str
    production_universe_id: str
    production_place_id: str
    source_main_sha: str
    rbxlx_sha256: str
    rbxlx_bytes: int
    reviewed_workflow_sha: str

    def check(self)->None:
        ids=(self.test_universe_id,self.test_place_id,self.production_universe_id,self.production_place_id)
        demand(all(type(x) is str and ID.fullmatch(x) for x in ids),'invalid universe/place identifier')
        demand(self.test_universe_id != self.production_universe_id and
               self.test_place_id != self.production_place_id,
               'private test cannot reuse a production universe/place')
        demand(type(self.source_main_sha) is str and SHA.fullmatch(self.source_main_sha) and
               self.source_main_sha == MAIN_BASE,
               'current-main source pin was not independently refreshed')
        demand(type(self.reviewed_workflow_sha) is str and SHA.fullmatch(self.reviewed_workflow_sha),
               'invalid reviewed main workflow SHA')
        demand(type(self.rbxlx_sha256) is str and DIGEST.fullmatch(self.rbxlx_sha256) and
               type(self.rbxlx_bytes) is int and 40 <= self.rbxlx_bytes <= MAX_XML_BYTES,
               'invalid bounded XML artifact pin')

@dataclass(frozen=True)
class XmlSavedRequest:
    method: str
    url: str
    content_type: str
    body: bytes

def _name(item:ET.Element)->str:
    props=[p for p in item if p.tag == 'Properties']
    demand(len(props)==1,'missing or duplicate item Properties')
    names=[p for p in props[0] if p.attrib.get('name')=='Name']
    demand(len(names)==1 and names[0].tag=='string' and type(names[0].text) is str and names[0].text,
           'missing or duplicate instance Name')
    return names[0].text

def check_rbxlx_bytes(data:bytes,cfg:XmlStageConfig)->dict[str,Any]:
    """Structure + original four source hashes; NOT Studio open or Roblox attestation."""
    cfg.check()
    demand(type(data) is bytes and len(data)==cfg.rbxlx_bytes and
           hashlib.sha256(data).hexdigest()==cfg.rbxlx_sha256,
           'XML file bytes/digest differ from review pin')
    demand(data.lstrip().startswith(b'<?xml') or data.lstrip().startswith(b'<roblox'),
           'missing Roblox XML document')
    upper=data.upper()
    demand(b'<!DOCTYPE' not in upper and b'<!ENTITY' not in upper,
           'XML entities and DTD are forbidden')
    # Outside-root comments and PIs are not retained even by TreeBuilder.
    # Inspect original bytes to stop previously ignored processing markup.
    visible=data.lstrip()
    if re.match(br'^<\?xml[ \t\r\n]',visible):
        end=visible.find(b'?>', 0, 256)
        demand(end>=0, 'invalid bounded XML declaration')
        visible=visible[end+2:]
    demand(b'<!--' not in visible and b'<?' not in visible,
           'unreviewed XML processing markup')
    try:root=ET.fromstring(data,parser=ET.XMLParser(target=ET.TreeBuilder(insert_comments=True,insert_pis=True)))
    except (ET.ParseError,ValueError,UnicodeError):raise XmlStageError('invalid Roblox XML syntax') from None
    demand(root.tag=='roblox' and root.attrib=={'version':'4'},'invalid Roblox XML place root')
    demand(root.text is None or not root.text.strip(), 'unreviewed root structural text')
    demand(all(child.tail is None or not child.tail.strip() for child in root), 'unreviewed root child tail')
    # Count Item nodes iteratively before entering the depth-recursive walker.
    # A hostile but well-formed XML tree must not trigger uncaught RecursionError.
    demand(sum(1 for item in root.iter('Item')) == len(EXPECTED_TOPOLOGY),
           'XML instance count not exactly approved')
    topology={}
    scripts={}
    referents=set()
    def walk(item:ET.Element,parent:tuple[str,...]):
        cls=item.attrib.get('class')
        demand(type(cls) is str and cls,'missing Roblox class')
        demand(item.text is None or not item.text.strip(), 'unreviewed Item structural text')
        demand(all(child.tail is None or not child.tail.strip() for child in item), 'unreviewed Item child tail')
        name=_name(item)
        path=parent+(name,)
        demand(path not in topology,'duplicate Roblox instance path')
        referent=item.attrib.get('referent')
        demand(set(item.attrib)=={'class','referent'} and
               type(referent) is str and
               re.fullmatch(r'RBX[0-9A-F]{1,32}',referent) is not None and
               referent not in referents,'invalid, duplicate or unreviewed Roblox instance referent')
        referents.add(referent)
        topology[path]=cls
        demand(all(child.tag in {'Properties','Item'} for child in item),
               'unexpected element inside Roblox Item')
        props=next(p for p in item if p.tag=='Properties')
        demand(not props.attrib,'unexpected Properties attributes')
        demand(props.text is None or not props.text.strip(), 'unreviewed Properties structural text')
        permitted={'Name':'string'}
        if path in SOURCE_PINS:permitted['Source']='ProtectedString'
        observed=set()
        for prop in props:
            demand(len(prop)==0 and (prop.tail is None or not prop.tail.strip()),
                   'unreviewed XML property markup or tail')
            label=prop.attrib.get('name')
            demand(set(prop.attrib)=={'name'} and label in permitted and
                   prop.tag==permitted[label] and label not in observed,
                   'unreviewed or duplicate XML instance property')
            observed.add(label)
        demand(observed==set(permitted),'missing expected XML instance property')
        for child in item:
            if child.tag=='Item': walk(child,path)
        if path in SOURCE_PINS:
            typ,digest=SOURCE_PINS[path]
            demand(cls==typ,'script class differs from current-main pin')
            props=next(p for p in item if p.tag=='Properties')
            sources=[s for s in props if s.attrib.get('name')=='Source']
            demand(len(sources)==1 and sources[0].tag in {'ProtectedString','string'} and
                   type(sources[0].text) is str,'script source missing')
            value=sources[0].text.encode('utf-8')
            demand(hashlib.sha256(value).hexdigest()==digest,'script source does not match accepted main')
            scripts['/'.join(path)]=digest
    demand(all(item.tag == 'Item' for item in root),
           'unexpected top-level Roblox XML element')
    for item in root:
        if item.tag=='Item':walk(item,())
    demand(topology==EXPECTED_TOPOLOGY,'XML instance topology not exactly approved')
    demand(len(scripts)==4,'four current-main script pins required')
    return {'status':'XML_STAGED_BYTES_CONSISTENT_UNTRUSTED','format':'RBXLX_XML',
            'content_type':'application/xml','rbxlx_sha256':cfg.rbxlx_sha256,
            'rbxlx_bytes':len(data),'source_main_sha':cfg.source_main_sha,
            'source_sha256':scripts,'instance_count':len(topology),
            'github_authenticated':False,'studio_open_verified':False,
            'roblox_upload_attested':False,'roblox_engine_verified':False,
            'public_publish_authorized':False}

def check_rbxlx_file(path:str|Path,cfg:XmlStageConfig)->bytes:
    cfg.check()
    p=Path(path)
    demand(p.suffix=='.rbxlx' and not p.is_symlink() and p.is_file(),
           'regular unsymlinked XML place file required')
    try:
        demand(p.stat().st_size==cfg.rbxlx_bytes,'XML file exact bytes mismatch')
        with p.open('rb') as stream:data=stream.read(MAX_XML_BYTES+1)
    except OSError:raise XmlStageError('XML place file unavailable') from None
    check_rbxlx_bytes(data,cfg)
    return data

def saved_xml_request(cfg:XmlStageConfig,data:bytes)->XmlSavedRequest:
    check_rbxlx_bytes(data,cfg)
    return XmlSavedRequest('POST',
        f'{API_ROOT}/universes/v1/{cfg.test_universe_id}/places/{cfg.test_place_id}/versions?versionType=Saved',
        'application/xml',data)

def saved_version(result:Any)->str:
    demand(type(result) is dict and set(result)=={'versionNumber'},
           'Roblox Saved response must contain one native versionNumber')
    value=result['versionNumber']
    demand(type(value) is int and 1<=value<=10**19-1,'invalid Saved versionNumber')
    return str(value)

def stage_once(cfg:XmlStageConfig,data:bytes,transport:Callable[[XmlSavedRequest],Any])->dict:
    request=saved_xml_request(cfg,data)
    result=transport(request)
    version=saved_version(result)
    return {'status':'XML_SAVED_RESPONSE_UNTRUSTED','source_main_sha':cfg.source_main_sha,
            'rbxlx_sha256':cfg.rbxlx_sha256,'version':version,
            'test_universe_id':cfg.test_universe_id,'test_place_id':cfg.test_place_id,
            'version_type':'Saved','upload_attempts':1,'publish_calls':0,
            'roblox_upload_attested':False,'engine_verified':False,
            'independent_provider_reconciliation_required':True}

def check_host_environment(cfg:XmlStageConfig, env:Any)->None:
    cfg.check()
    demand(type(env) is dict and all(type(k) is str and type(v) is str for k,v in env.items()),
           'untrusted environment metadata')
    expected={'GITHUB_ACTIONS':'true','GITHUB_REPOSITORY':REPOSITORY,'GITHUB_REF':'refs/heads/main',
              'GITHUB_SHA':cfg.reviewed_workflow_sha,'GITHUB_EVENT_NAME':'workflow_dispatch',
              'TWF_ACCEPTED_GAME_SOURCE_SHA':cfg.source_main_sha,
              'TWF_REVIEWED_MAIN_SHA':cfg.reviewed_workflow_sha,
              'TWF_PRIVATE_STAGE_APPROVED':'true','TWF_PROTECTED_ENVIRONMENT':'roblox-private-test',
              'TWF_TEST_UNIVERSE_ID':cfg.test_universe_id,'TWF_TEST_PLACE_ID':cfg.test_place_id,
              'TWF_PROD_UNIVERSE_ID':cfg.production_universe_id,'TWF_PROD_PLACE_ID':cfg.production_place_id}
    demand(all(env.get(k)==v for k,v in expected.items()),
           'not a reviewed test-only GitHub Actions context')
    # Strings can be spoofed. Host must independently authorize the workflow,
    # target, secret and source artifact before permitting any live POST.

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):return None

class LiveSavedXmlTransport:
    """One nonretrying POST; only use after protected independent provider checks."""
    def __init__(self,cfg:XmlStageConfig,*,api_key:str,environment:dict[str,str]):
        check_host_environment(cfg,environment)
        demand(type(api_key) is str and 16<=len(api_key)<=8192,'test-only API key unavailable')
        self._cfg=cfg;self._api_key=api_key;self._used=False
        self._opener=urllib.request.build_opener(NoRedirect())
    def __call__(self,request:XmlSavedRequest)->dict:
        expected=saved_xml_request(self._cfg,request.body)
        demand(not self._used and request==expected,'duplicate or unapproved XML Saved POST')
        self._used=True  # no retry if network/ACK fails
        req=urllib.request.Request(expected.url,data=expected.body,method='POST',
                headers={'x-api-key':self._api_key,'Content-Type':'application/xml','Accept':'application/json'})
        try:
            with self._opener.open(req,timeout=25) as response:
                demand(response.geturl()==expected.url,'Roblox response changed endpoint')
                body=response.read(16385)
        except (urllib.error.HTTPError,urllib.error.URLError,OSError,TimeoutError):
            raise XmlStageError('Saved upload outcome UNKNOWN; no automatic retry') from None
        demand(len(body)<=16384,'oversized Roblox response')
        try:value=json.loads(body)
        except (ValueError,UnicodeError):raise XmlStageError('malformed Saved response') from None
        demand(type(value) is dict,'non-object Saved response')
        return value
