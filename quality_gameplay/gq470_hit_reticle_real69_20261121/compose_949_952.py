#!/usr/bin/env python3
"""A-only same-selected-Luau source composer: pin ORIGINAL #949 then apply #952.

Conflicts resolved at SOURCE, never two uncoordinated official RC writes.
Source blob, CI run and original SHA of #949 are fixed, not guessed. Combined
native/Rojo and art-source gate are separate GitHub CI; no Studio claims.
"""
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path
import patch_hit_reticle as m

AUTHOR_PR = 949
AUTHOR_HEAD = 'd94e8852b0da3d3c65d671f8ea263ab042b11c8d'
AUTHOR_CI_RUN = 44834993878
AUTHOR_CI_ARTIFACT = 14677759742
AUTHOR_FEATURE = 'GQ470_FB015_CONFIRMED_HIT_MATTE_STREAK_REAL69_20261121'
AUTHOR_SHA = '860a8d60e7e577b7e5f01ca08b901290ec0a040beec63a46c66993ab71187dd3'
AUTHOR_BYTES = 27640
COMPOSITE_SHA = 'b37194cb97357cf7290fc6eb3f94396720265b15915ad588d2bd05b9b870e833'
COMPOSITE_BYTES = 28097

def check(ok,code):
 if not ok: raise AssertionError('RED_GQ470_HIT_COMPOSITE_'+code)

def validate_upstream(author:Path)->str:
 report=json.loads((author/'GQ470_HIT_STREAK_SOURCE_QA.json').read_text())
 check(report.get('formal_head')==m.FORMAL_SHA and
       report.get('original_sha256')==m.OLD_SHA and
       report.get('candidate_sha256')==AUTHOR_SHA,'AUTHOR_PROVENANCE')
 check(report.get('route')==m.ROUTE and report.get('class')=='LocalScript' and
       report.get('selected_source_count')==69 and report.get('source_byte_exact')==68 and
       report.get('added_ui_frames')==2 and report.get('added_world_parts')==0 and
       report.get('new_remotes')==0,'AUTHOR_SOURCE_SCOPE')
 p=author/m.RELATIVE_SOURCE
 check(p.exists(),'AUTHOR_ACTUAL_SOURCE_MISSING')
 b=p.read_bytes()
 check(m.digest(b)==AUTHOR_SHA and len(b)==AUTHOR_BYTES,'AUTHOR_RAW_SOURCE_SHA')
 text=b.decode('utf8')
 check(text.count(AUTHOR_FEATURE)==1,'AUTHOR_FEATURE_MARKER')
 check('EGGRUMBLE_Eliminated' in text and 'ConfirmedMatteStreak_' in text,'AUTHOR_REAL_LUAU')
 return text

def compose(base:Path,author:Path,out:Path)->dict:
 check(base.is_dir() and author.is_dir(),'REAL_INPUTS')
 original=m.source_routes(base)[m.ROUTE].read_bytes()
 check(m.digest(original)==m.OLD_SHA,'ORIGINAL_REAL69_SOURCE_SHA')
 upstream=validate_upstream(author)
 full=m.changed_text(upstream)
 m.validate_source(upstream,full)
 check(m.sample_mutations(upstream,full)==12,'12_NEGATIVE_MUTATIONS')
 bytes_=full.encode('utf8')
 check(m.digest(bytes_)==COMPOSITE_SHA and len(bytes_)==COMPOSITE_BYTES,'PIN_COMBINED_SOURCE_SHA')
 # Reuse #952's proven 69/69 original OFF + 1 source changed A prep for safety;
 # the only further modification is a source-select to the composed source.
 result=m.run(base,out)
 original_off=m.source_routes(out/m.OFF_NAME)
 selected=m.source_routes(out)
 check(selected[m.ROUTE].read_bytes()!=bytes_,'BOTH_DIFFER_FROM_952_ONLY')
 selected[m.ROUTE].write_bytes(bytes_)
 check({k for k in selected if selected[k].read_bytes()!=original_off[k].read_bytes()}=={m.ROUTE},'ONE_TOTAL_SOURCE_DELTA')
 report={
   'schema':'GQ470_FB015_COMBATFEEL_949_952_ONE_SOURCE_COMPOSITE_V1',
   'canonical_branch':'rc/p0d-s1-kids-rc01','official_base_sha':m.FORMAL_SHA,
   'source_count':69,'changed_routes':[m.ROUTE],'other_68_exact':True,
   'script_class':'LocalScript','original_sha256':m.OLD_SHA,
   'author_949_head':AUTHOR_HEAD,'author_949_ci_run':AUTHOR_CI_RUN,
   'author_949_ci_artifact':AUTHOR_CI_ARTIFACT,'author_949_sha256':AUTHOR_SHA,
   'author_949_source_bytes':AUTHOR_BYTES,'author_949_feature':AUTHOR_FEATURE,
   'reticle_952_feature':m.MARKER,'candidate_sha256':COMPOSITE_SHA,
   'original_bytes':len(original),'candidate_bytes':len(bytes_),
   'added_gui_frames':2,'added_world_parts':0,'added_network_or_game_authority':False,
   '12_reticle_source_mutants_rejected':12,'formal_rc_integrated':False,
   'studio_2client':'NOT_TESTED','android15':'NOT_TESTED','screenshots':'0/32',
   'art':'ART_NO_GO','fun':'FUN_NO_GO','product':'PRODUCT_NO_GO','owner_accepted':False,
   'value_priority':'AFTER_910_PLAYABLE_AND_931_ART6_ONLY_IF_250_ADOPT',
   'official_writer':'B220_CAS_ONLY','no_whole_pr_merge':True,
 }
 receipt_path=out/m.RECEIPT
 receipt=json.loads(receipt_path.read_text())
 receipt['source_hashes'][m.ROUTE]=COMPOSITE_SHA
 receipt['gq470_hit_reticle_candidate']={**result,'candidate_source_sha256':COMPOSITE_SHA,'composed_949':True,'original_source_sha256':m.OLD_SHA}
 receipt['gq470_confirmed_hit_shared_composite_candidate']=report
 receipt_path.write_text(json.dumps(receipt,indent=2,ensure_ascii=False,sort_keys=True)+'\n')
 handoff=out/'B220_RETICLE_ONE_SOURCE_NOT_FORMAL'
 f=handoff/'selected_sources'/m.RELATIVE_SOURCE.split('sources/',1)[1]
 f.write_bytes(bytes_)
 (handoff/'SOURCE_SELECT_MANIFEST.json').write_text(json.dumps(report,indent=2,ensure_ascii=False,sort_keys=True)+'\n')
 (out/'GQ470_HIT_949_952_COMPOSITE_QA.json').write_text(json.dumps(report,indent=2,ensure_ascii=False,sort_keys=True)+'\n')
 check(f.read_bytes()==selected[m.ROUTE].read_bytes(),'B_PACKET_EXACT')
 print('GQ470_HIT_949_952_COMPOSITE_LOCAL_PASS',COMPOSITE_SHA,COMPOSITE_BYTES)
 return report

def main():
 parser=argparse.ArgumentParser()
 parser.add_argument('--base',required=True,type=Path)
 parser.add_argument('--author949',required=True,type=Path)
 parser.add_argument('--out',required=True,type=Path)
 args=parser.parse_args();compose(args.base.resolve(),args.author949.resolve(),args.out.resolve())

if __name__=='__main__': main()
