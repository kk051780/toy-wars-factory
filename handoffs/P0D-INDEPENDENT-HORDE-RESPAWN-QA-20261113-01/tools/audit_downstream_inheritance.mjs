// Independent downstream propagation gate for old #288 v2 elite stale telegraph.
 // This is static source QA, not real Studio execution or permission to edit owner branches.
import assert from "node:assert/strict";
import {readFileSync} from "node:fs";
import {pathToFileURL} from "node:url";
import {analyze,gitBlobSha} from "./audit_horde_respawn.mjs";

export const locks={
  oldHorde:"c1ef565f4e8b11a6e8ff7eac5ed55c8f268a4553",
  correctedV3Horde:"57c70e364b721d24e9e36eaeaf8be6dfd9fca592",
  oldFullGame:"55ad13b45907a5a3e9deae7196a7c202a0672c0c",
  correctedFullGame:"1117513a27f66f44e0a2dbaa0e387812d2bc0c73",
  earnedPowerHead:"cb2540dc4a3e5b819c0e3598d4af5e2b6dca76d3",
  originalPowerAssembleBlob:"04f89fa61f773ecd3342c969a9e354ed6703170e",
  oldGameBlob:"f8c45bcf109dc3229c0459e4fb9fa224ab6c38a4",
};
export function checkBaseline(inputHorde,assembleText) {
  const hordeBlob=gitBlobSha(inputHorde);
  const assembleBlob=gitBlobSha(assembleText);
  const code=analyze(inputHorde);
  const lockOld=assembleText.includes('"parent_game_sha":"'+locks.oldFullGame+'"')
    || assembleText.includes('"parent_game_sha": "'+locks.oldFullGame+'"')
;
  const oldGameGuard=assembleText.includes(locks.oldGameBlob);
  const oldHorde=hordeBlob===locks.oldHorde;
  const safe=code.safe && !oldHorde && !lockOld && !oldGameGuard;
  return {safe,sourceHordeBlob:hordeBlob,sourceAssemblyBlob:assembleBlob,
    oldHorde,oldAssemblerLock:lockOld,oldGameGuard,oldWarnState:!code.safe,
    correctV3Horde:hordeBlob===locks.correctedV3Horde,
    safeState:code.safe};
}
if(process.argv[1] && import.meta.url===pathToFileURL(process.argv[1]).href){
  if(process.argv.length<4)throw Error("USAGE node audit_downstream_inheritance.mjs path/to/MusouHorde.luau path/to/assemble.py [expect-unsafe|expect-safe]");
  const h=readFileSync(process.argv[2],"utf8");
  const a=readFileSync(process.argv[3],"utf8");
  const result=checkBaseline(h,a);
  const mode=process.argv[4]||"expect-safe";
  if(mode==="expect-unsafe"){
    assert.equal(result.oldHorde,true,"old exact Horde blob must reproduce");
    assert.equal(result.safe,false,"old power baseline must be blocked");
    assert.equal(result.oldAssemblerLock,true,"old source assembly lock must reproduce");
  }else if(mode==="expect-safe"){
    assert.equal(result.safe,true,"DO NOT ADOPT outdated or unverified Horde baseline");
  }else throw Error("UNKNOWN_MODE");
  console.log(JSON.stringify({mode,...result}));
}
