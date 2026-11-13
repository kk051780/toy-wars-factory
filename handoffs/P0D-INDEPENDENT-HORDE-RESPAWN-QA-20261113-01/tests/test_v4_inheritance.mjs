// Executable source QA for original #288 V2, latest V4, and the old earned-power H1.
// Catches stale state, floating NPC spawn, and one hit damaging mob+castle.
// Does NOT simulate actual Roblox Studio engine.
import {readFileSync} from "node:fs";
import assert from "node:assert/strict";
import {audit,inspectHorde,inspectGame,inspectPowerBuilder,pins} from "../tools/audit_v4_inheritance.mjs";

const files=process.argv.slice(2);
if(files.length!==7)throw Error(
  "USAGE node test_v4_inheritance.mjs <oldHorde> <newHorde> <powerHorde> <oldGame> <newGame> <powerGame> <oldAssembler>");
const [oldH,newH,powerH,oldG,newG,powerG,builder]=files.map(f=>readFileSync(f,"utf8"));
let done=0;
const yes=(p,label)=>{assert.ok(p,label);done++};
const old=audit(oldH,oldG);
const fixed=audit(newH,newG);
const power=audit(powerH,powerG,builder);
yes(old.horde.gitBlob===pins.v2HordeBlob,"old Horde pinned");
yes(fixed.horde.gitBlob===pins.v4HordeBlob,"v4 Horde pinned");
yes(power.horde.gitBlob===pins.v2HordeBlob,"power Horde old pinned");
yes(old.game.gitBlob===pins.v2GameBlob,"old Game pinned");
yes(fixed.game.gitBlob===pins.v4GameBlob,"v4 Game pinned");
yes(power.game.gitBlob===pins.powerGameBlob,"power Game pinned");
yes(power.builder.gitBlob===pins.powerAssemblerBlob,"power builder pinned");
yes(!old.safe,"old full v2 unsafe");
yes(fixed.safe,"v4 Horde+Game safe static");
yes(!power.safe,"power source inherited v2");
yes(!old.horde.footStable,"old fixed-Y floating actors");
yes(fixed.horde.footStable,"v4 uses source map floor");
yes(!power.horde.footStable,"power inherits float");
yes(!old.horde.eliteDeathAndRespawnSafe,"v2 stale elite tell");
yes(fixed.horde.eliteDeathAndRespawnSafe,"v4 elite state clean");
yes(!power.horde.eliteDeathAndRespawnSafe,"power stale elite tell");
yes(!old.game.singleAttackCastlePriority,"v2 mob+castle no guard");
yes(fixed.game.singleAttackCastlePriority,"v4 no mob+castle double hit");
yes(!power.game.singleAttackCastlePriority,"power lacks guard");
yes(power.game.pvePower&&power.game.pvpPower,"power feature real code preserved");
yes(power.builder.staleBase&&!power.builder.fixedParent,"power assembler old Sha");
yes(newH.includes('world:FindFirstChild("GrassArena")'),"v4 original arena");
yes(newH.includes('world:FindFirstChild("CenterRoad")'),"v4 original road");
yes(!inspectHorde(newH.replace('local feetY=groundTop(self.world,x,z)','local feetY=0')).safe,"mutant ground hardcoded");
yes(!inspectHorde(newH.replace('world:FindFirstChild("CenterRoad")','world:FindFirstChild("ImaginaryRoad")')).safe,"mutant road missing");
yes(!inspectGame(newG.replace('if mobHits>0 then return end','if mobHits<0 then return end')).safe,"mutant double damage guard removed");
yes(!inspectHorde(newH.replace('m.tellUntil=0\n                m.target=nil','m.target=nil')).safe,"mutant no elite revive tell reset");
yes(!inspectHorde(newH.replace('m.target=nil\n                m.flashUntil','m.flashUntil')).safe,"mutant no elite revive target reset");
yes(!inspectPowerBuilder(builder.replaceAll(pins.v2Full,pins.v4Full)).safe,"mutant fake parent metadata only");
const cloned=builder.replaceAll(pins.v2Full,pins.v4Full).replaceAll(pins.v2GameBlob,pins.v4GameBlob);
yes(inspectPowerBuilder(cloned).safe,"fixed parent metadata hypothetical only, requires actual fixed game and horde");
yes(!audit(powerH,powerG,cloned).safe,"fake metadata cannot hide old source");
console.log("P0D_V4_INHERITANCE_STATIC_QA_PASS",done,
  "pinned checks; v4 safe static, old 39 game BLOCKED");
