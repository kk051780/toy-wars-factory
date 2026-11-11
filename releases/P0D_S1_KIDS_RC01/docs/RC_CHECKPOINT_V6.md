# S1 V6 Guardian trap — recovery, version pin and acceptance

Scope: P0D-S1-KIDS-RC01, sole CHAT-INTEGRATOR RC01-B, latest previous unchanged official RC `5dc6c958ea5549b1e859d6d250e6179e731181fb`.

**Staged, not engine tested:** Guardian trap source in isolated `stage/p0d-s1-guardian-trap-rc01b-20261112`, original immutable code commit `e60c9668de9f5c758f5cf0429df944fc32b2bb16`. Use the new official commit in #220 when finalized, not this staging branch, for all future independent readback. Source `src/` Git tree `11f5828763122bd9facf78817a419fffe5516434` (21 Luau, includes original 20+new S1TrapRules) is the byte identity. Do not pretend official Windows Place matches it.

During V6 release write: original V5 official SHA = `5dc6c958ea5549b1e859d6d250e6179e731181fb`; perform `force=false expected_sha` RC branch CAS update, never reset/overwrite competing owner. Revalidate 6-key `BUILD_MANIFEST` every file SHA256/size, Rojo mappings and exactly one Game.server Script and 3 existing client LocalScripts; 17 ModuleScripts now, not 16. No second Remote, boss remains OFF, no paid/economy/XP changes. Preserve old V5 unchanged immutable commit.

Independent source and live engine milestones must remain separate. V5 approved Studio source receipt .rbxlx `f5c0b56...` is not V6 and must NOT be imported as V6 binary. After independent QA/real Rojo on new source, an OWNER-direct Windows PC final one-batch Codex QA must preserve latest PC Place and source HEAD, import full V6 into unpublished clone, two clients real hit/jump/egg/score/win/rematch/phone/trap clean exit, boss scope decision, human first play; report PASS/PARTIAL/FAIL. GitHub comment is not PC execution and does not authorize live Roblox public release.
