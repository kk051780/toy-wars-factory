// Exact cross-branch deterministic regression test; feed files from pinned Git show refs.
// NOTE: checks SOURCE only, not actual Roblox Studio or native Luau.
import assert from "node:assert/strict";
import {readFileSync} from "node:fs";
import {checkBaseline,locks} from "../tools/audit_downstream_inheritance.mjs";
import {gitBlobSha,analyze} from "../tools/audit_horde_respawn.mjs";

if(process.argv.length!==6)throw Error("USAGE node test_downstream_inheritance.mjs <v2-horde> <fixed-v3-horde> <power-commit-horde> <power-assemble.py>");
const [oldFile,newFile,powerFile,powerBuilderFile]=process.argv.slice(2);
const read=(p)=>readFileSync(p,"utf8");
const old=read(oldFile), updated=read(newFile), power=read(powerFile), builder=read(powerBuilderFile);
let n=0;
const ok=(v,label)=>{assert.ok(v,label);n+=1};
ok(gitBlobSha(old)===locks.oldHorde,"original V2 exact immutable Git blob");
ok(gitBlobSha(updated)===locks.correctedV3Horde,"fixed V3 exact immutable Git blob");
ok(gitBlobSha(power)===locks.oldHorde,"earned power still inherits V2 Horde");
ok(gitBlobSha(builder)===locks.originalPowerAssembleBlob,"earned power exact assembly program");
ok(analyze(old).requiresFix===true,"original V2 pending attack hazardous");
ok(analyze(updated).safe===true,"original V3 both lifetime resets");
ok(analyze(power).requiresFix===true,"earned power reintroduces V2 risk");
ok(checkBaseline(power,builder).safe===false,"H1 power baseline BLOCKED");
ok(checkBaseline(power,builder).oldHorde===true,"same exact old module");
ok(checkBaseline(power,builder).oldAssemblerLock===true,"power locked old H1 SHA");
ok(checkBaseline(power,builder).oldGameGuard===true,"power builder asserts old Game blob");
ok(builder.includes("shutil.copytree(OLD,DIST)"),"inherits all upstream modules");
ok(!builder.includes('"server/MusouHorde.luau":'),"no Horde override repairing bug");
ok(builder.includes('assert len(old)==38'),"still one old 38-module base");
const cloned=builder
  .replaceAll(locks.oldFullGame,locks.correctedFullGame)
  .replaceAll(locks.oldGameBlob,"REBASE_TO_V3_NEW_GAME_BLOB_REQUIRED");
ok(checkBaseline(updated,cloned).safe===true,"only after explicit V3 source+assembler update can gate pass");
ok(checkBaseline(old,cloned).safe===false,"new assembly declaration alone does not fix source");
ok(checkBaseline(updated,builder).safe===false,"new Horde alone does not supersede old pinned assembly");
const commented=old.replace("m.deadUntil=now+8","m.deadUntil=now+8\n -- m.tellUntil=0; m.target=nil");
ok(analyze(commented).safe===false,"comment-only bogus fix rejected");
console.log("P0D_DOWNSTREAM_HORDE_INHERITANCE_STATIC_PASS",n,"checks; current power H1 correctly BLOCKED until source rebase+new build");
