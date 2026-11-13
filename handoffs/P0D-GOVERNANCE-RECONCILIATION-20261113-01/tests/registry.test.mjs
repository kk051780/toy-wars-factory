/* Run: node tests/registry.test.mjs. No external deps. */
import {readFileSync} from "node:fs";
import assert from "node:assert/strict";
import {validateRegistry} from "../tools/validate_registry.mjs";
const original=JSON.parse(readFileSync(new URL("../registry.json",import.meta.url),"utf8"));
assert.deepEqual(validateRegistry(original),[]);
const setters={
"duplicate":d=>d.items.push({...d.items[0]}),
"missing-source":d=>d.items[1].source_sha=null,
"phantom-rc":d=>d.items[3].official_rc_adopted=true,
"phantom-fun":d=>d.items[3].human_fun_accepted=true,
"missing-dependency":d=>d.items[2].dependencies.push("NOT_AN_ID"),
"missing-owner":d=>d.items[4].next_owner="",
"invalid-publication":d=>d.policy.publication="AUTHORIZED",
"too-many-RC-writers":d=>d.policy.max_parallel_official_rc_writers=2,
"invalid-gate":d=>d.policy.product_fun_gate="GO",
"unknown-authority":d=>d.items[5].systems.push("another_damage_owner"),
"unknown-successor":d=>d.items[0].superseded_by="BOGUS",
"too-many-selected":d=>{d.items[0].stage="SELECTED_FOR_PROTOTYPE";d.items[1].stage="SELECTED_FOR_PROTOTYPE";d.items[2].stage="SELECTED_FOR_PROTOTYPE"}
};
const expected={"duplicate":"E_DUPLICATE_ID","missing-source":"E_SOURCE_SHA","phantom-rc":"E_UNGROUNDED_RC","phantom-fun":"E_UNGROUNDED_FUN","missing-dependency":"E_MISSING_DEP","missing-owner":"E_ORPHAN","invalid-publication":"E_PUBLICATION","too-many-RC-writers":"E_RC_WRITERS","invalid-gate":"E_FUN_GATE","unknown-authority":"E_UNKNOWN_AUTHORITY","unknown-successor":"E_UNKNOWN_SUCCESSOR","too-many-selected":"E_SELECTED_WIP"};
for(const [name,mutate] of Object.entries(setters)){
 const doc=structuredClone(original);mutate(doc);
 assert.ok(validateRegistry(doc).some(e=>e.startsWith(expected[name])),name);
}
console.log("P0D_ADOPTION_REGISTRY_QA_PASS 13/13");
