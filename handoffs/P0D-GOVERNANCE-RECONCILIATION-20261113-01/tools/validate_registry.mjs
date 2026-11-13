/* P0D read-only adoption registry linter. No network or game writes. */
export function validateRegistry(o) {
 const e=[], has=x=>typeof x==="string"&&x.trim().length>0, sha=x=>typeof x==="string"&&/^[0-9a-f]{40}$/.test(x);
 if(o.schema!=="P0D_CHANGE_CONTROL_V1")e.push("E_SCHEMA");
 if(!sha(o.official_rc?.frozen_reference_sha))e.push("E_OFFICIAL_SHA");
 if(o.policy?.publication!=="NOT_AUTHORIZED")e.push("E_PUBLICATION");
 if(o.policy?.product_fun_gate!=="FUN_NO_GO")e.push("E_FUN_GATE");
 if(o.policy?.max_parallel_official_rc_writers!==1)e.push("E_RC_WRITERS");
 if(o.policy?.max_selected_experiments>2)e.push("E_WIP");
 const ids=new Set((o.items||[]).map(x=>x.id));
 if(ids.size!==(o.items||[]).length)e.push("E_DUPLICATE_ID");
 const allowed=new Set(["IDEA_CARD","SELECTED_FOR_PROTOTYPE","SOURCE_DELIVERED_UNVERIFIED","SOURCE_VERIFIED","INDEPENDENT_QA","SOLE_RC_GAMEPLAY_INTEGRATED","HUMAN_FUN_ACCEPTED","DEFERRED","SUPERSEDED"]);
 for(const x of o.items||[]){
  if(!has(x.id)||!has(x.title)||!allowed.has(x.stage))e.push("E_ITEM_INVALID:"+x.id);
  if(!has(x.next_owner)||!has(x.next_acceptance))e.push("E_ORPHAN:"+x.id);
  if(x.stage!=="IDEA_CARD"&&!sha(x.source_sha))e.push("E_SOURCE_SHA:"+x.id);
  if(x.official_rc_adopted&&!(["SOLE_RC_GAMEPLAY_INTEGRATED","HUMAN_FUN_ACCEPTED"].includes(x.stage)&&sha(x.official_rc_sha)&&has(x.rc_evidence_url)))e.push("E_UNGROUNDED_RC:"+x.id);
  if(x.human_fun_accepted&&!(x.official_rc_adopted&&x.stage==="HUMAN_FUN_ACCEPTED"&&has(x.human_evidence_url)))e.push("E_UNGROUNDED_FUN:"+x.id);
  for(const dep of x.dependencies||[])if(!ids.has(dep))e.push("E_MISSING_DEP:"+x.id+":"+dep);
  for(const s of x.systems||[])if(!(o.authority_contract||[]).some(y=>y.system===s))e.push("E_UNKNOWN_AUTHORITY:"+x.id+":"+s);
  if(!has(x.bundle_role))e.push("E_BUNDLE_ROLE:"+x.id);
 }
 for(const x of o.items||[])if(x.superseded_by&&!ids.has(x.superseded_by))e.push("E_UNKNOWN_SUCCESSOR:"+x.id);
 if((o.items||[]).filter(x=>x.stage==="SELECTED_FOR_PROTOTYPE").length>2)e.push("E_SELECTED_WIP");
 if((o.blockers||[]).some(x=>!has(x.evidence)||!has(x.next)))e.push("E_BLOCKER_UNOWNED");
 return e;
}
if(process.argv[1]?.endsWith("validate_registry.mjs")){
 const {readFileSync}=await import("node:fs");
 const doc=JSON.parse(readFileSync(new URL("../registry.json",import.meta.url),"utf8"));
 const errors=validateRegistry(doc);
 if(errors.length){console.error("P0D_REGISTRY_FAIL",errors.join(" | "));process.exitCode=1}
 else console.log("P0D_REGISTRY_READONLY_PASS items="+doc.items.length+" blockers="+doc.blockers.length);
}
