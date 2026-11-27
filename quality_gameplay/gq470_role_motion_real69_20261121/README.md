# PR943 continuation — 通常攻撃の7職モーション接続（SOURCE PREP）

## 現在の候補と実害

正式RC `93a1147561a531610ac1609ebc68cc0ecf546623` では、成立した通常攻撃が `EGGRUMBLE_BasicCastSerial` を更新しても、既存ProceduralSkillsはA/B/C signatureだけを購読していました。実Source全文のNative再現では、技Aで3関節が動く一方、通常攻撃通知2回で関節書込みは0でした。既存のダメージ・ImpactFeedbackは動作するため、攻撃反応がすべて無いという主張ではありません。

本継続は、原#943の可読性改善を保持し、同じrendererへ通常攻撃を接続します。成立通知ごとに現在の職の既存A姿勢を使い、サーバーのダメージ、Remote、クールダウン、HP、Scoreには変更を加えません。

- BASICと技のsequenceを分離し、初期値・respawn時の既存値は再生しません。
- Player/Characterごとのobserver tokenを失効させ、終了した接続のcallbackが新しいbindingを変更することを防ぎます。
- 不正・重複・逆順のserialを拒否し、死亡・上限・技の優先で表示を捨てたserialも後から再生しません。
- 技A/B/Cの再生中はその姿勢を保ち、通常攻撃の連打で技Cを短縮しません。技は通常攻撃を置き換えられます。
- 元の7職、A/B/C曲線、0.26/0.48/0.82秒、16体、130stud、1本のPreSimulation、cleanupを保持します。

数値Player属性にはサーバー側のCharacter/match epochがありません。検証するのはローカルcallback失効・baseline・deduplicationであり、任意の旧ネットワーク値の出所を完全に識別する保証ではありません。

## 固定した入力・差分・復元

入力は正式push run `45106580546`、job `137469149262`、artifact `14787568439`、attempt 1。ZIPは **5,840,240 B / SHA256 `1187e0f2ff176a286855e911495da84006d5c99841f68891aeca9630915f275d`** です。source_lock.jsonに実親、raw receipt、project、Place、69 source hashesを固定しています。

| 段階 | Source bytes | SHA256 |
| --- | ---: | --- |
| F：正式H93 | 6,764 | `95e5dba544a759547ea41e8ecec1984317fc61b35281f4533b2323df1951491f` |
| R(F)：元#943 | 8,662 | `1856594a79d2e7ab7d4f6ac386c9379a45a8647a4168f65354246e888428bffb` |
| B(R(F))：今回の候補 | 11,568 | `2d4145fdbd05359e89cf52ca41117ec416c7b6e7ad3d95aedac5c857bc3e34fe` |

原ROLE_MOTION_REAL69.patchの4,016 Bをprefixとして完全保存し、独立したBASIC fragment 4,382 Bを後ろへ追加しました。R/Bの両順序が同じ最終Sourceとなり、各逆適用で元943または正式Sourceへ戻ることを実証しています。BASIC-onlyの代数的な適用可能性は、全20契約やARTの合格を意味しません。今回はR+Bを検証対象にします。

変更はProceduralSkills LocalScriptの1 routeだけです。他68源、project、class、非Source property、75 instancesは保持。実Rojo ON Placeは **833,462 B / `c5a3eb2177f6be0cc59b46c159dad3ef59388ae42c1c831ed2a7443d6da6d675`**、OFFは **828,658 B / `9cc9068b85893605c5090964fdc27175d9c48372803d65fe52914591fa7e5899`** で正式H93とbyte-exactです。

## 再現できる検証

`gate.py --base <official-extracted> --out <new-output> --archive <official.zip> --api-dir <actual-parent-api>` で実親を拘束して二段合成します。API directoryは実GETのrun.json / artifacts.json / jobs.json / ref.jsonです。API証拠を渡さないローカルSource検証も可能ですが、GitHub CIの成功証拠には昇格しません。

`gate.py --verify <output> --luau <f46-repl> --compiler <f46-compile> --luau-source <clean-f46-checkout> --rojo <7.7.1>` で以下を実行します。

- 原test_native_motion.py全4,211 Bを変更せず、21 role/slot ×101 samplesを検証。
- 実client全文を使う追加20ケース。7職BASIC、自身のAとの軌跡一致、独立counter、初期値、不正値の後の正常復帰、死亡、respawn、旧callback、同UID別Player、C優先、16体/130stud、両joint形式、teardownを確認。
- 独立指摘を受け、旧CharacterRemoving callback後に次のfresh serial 11も動くpredicateを追加。fixture/casesの作者はruntime_environment、製品への取込みとこの追記はroot。独立レビューとは区別します。
- 公式未修正版ではBASIC契約がREDとなり、A/B/C正制御はPASS。候補は20/20 PASS。
- ON69/OFF69の138コンパイル、Rojo Source/class/hash、非Source propertyとOFF Place一致、既存48 flag監査。元4負例と親metadata9負例も保持。

旧公式Place・CI/Native receiptsは `BASELINE_EVIDENCE` に保全し、候補の実行証拠は `candidate_evidence` に生成します。過去のGREENを候補の実行結果へ流用しません。CIは実PR headをcheckoutし、run/attempt/trigger SHAと検証対象headを分けて記録します。GitHub上の最終conclusionは固定PR headについて別途取得する必要があります。

## 権限・未検証

元PR943・同一FEATUREの限定継続です。実claim `P0D-GQ943-BASIC-MOTION-20261123-62AC651F` はregistry commit `970e7ccf86a0c56356a2a146ca2830a820370003`、#2187091657835。対象は元5 path＋source_lock.json＋test_native_cast_wiring.pyの7 path。新PRや共有UNION22変更、RC書込みはこのA_PREP grantに含みません。元943履歴とfresh正式RCを両親として保存し、最終treeはfresh RC＋7 pathだけとします。

ローカル検証はSOURCE_QAの証拠です。正式RC採用、同じ採用SHAのStudio Solo/2client、ART、Android15分、FUN、OWNER受入は別ゲートで未実施です。main/Publish/追加支出は対象外です。

---

## Historical original #943 README (retained verbatim; old input and metrics)

以下は元b2beの原文です。e809・旧artifact・旧容量は当時の履歴であり、今回の正式親や候補容量ではありません。

# GQ470 REAL69｜7職スキル動作 ART 改修（A候補のみ）

- Parent: #470 / #420 / #218 soft claim 7051834048
- Official source: `rc/p0d-s1-kids-rc01@e80973c354f14a0d0088577f3cc1a875454f0f8f`; real artifact #14610422120, Run #44695199140
- Unique selected route: `StarterPlayer/StarterPlayerScripts/EGGRUMBLE_ProceduralSkills` LocalScript
- Source OLD SHA256: `95e5dba544a759547ea41e8ecec1984317fc61b35281f4533b2323df1951491f`
- Source NEW SHA256: `1856594a79d2e7ab7d4f6ac386c9379a45a8647a4168f65354246e888428bffb`

## Actual player-visible change

One source-locked patch changes **existing** 7-role / A,B,C skill gestures only: 18% anticipation, 24% fast strike, 12% impact silhouette, 46% recovery for B/C; shorter A uses 18% windup, 18% attack, 26% impact hold and 38% recovery to keep peak visible at low FPS. It also adds B/C role-specific body/hand accents for WARRIOR/MAGE/NINJA/TRAPPER/BUILDER/BEAST/ZOMBIE (NINJA is the stable internal ID; display remains Assassin/暗殺者), disconnects per-player CharacterRemoving observers on exit, and clears residual procedural poses on leaving the 130-stud visible budget.

No Parts, particles, new loop, Roblox assets, duplicate client, RemoteEvents, gameplay attack timing, damage/HP, score, Store, skill authority or publication. Existing max 16 animated avatars and `DURATION={A=.26,B=.48,C=.82}` retained. Studio-only source remains intentionally Studio-only.

## Provenance and rollback

`ROLE_MOTION_REAL69.patch` applies with zero fuzz exclusively to original selected 6764-byte Luau; a changed base hash causes RED, never blind reapplication. `gate.py` fetches genuine 69 route/class/hash proofs, checks one changed route/68 byte-exact, creates `OFF69_SOURCE_EXACT`, and rejects 4 mutation negatives. CI runs original + candidate Native Luau 69/69, pinned Rojo ON/OFF and exact OFF Place. B receives **one selected source + route/SHA manifest**, not a PR-merge request.

Actual Native Luau dynamic test: **PASS 7 roles × 3 slots × 101 samples**, phase continuity, no stale endpoints and distinct B/C accents. The normalized A impact hold increased from 31.2ms to 67.6ms, a source-based readability precaution at 25fps—not an Android FPS measurement.\n\nLocal original REAL69 source verification: **PASS**. A candidate source 8662 bytes; original 6764 bytes. XML candidate Place formed from the real 798390B official Place for independent non-engine static sanity only: 802178B. These numbers do **not** establish Studio or Android performance.

## Official adoption conditions

This branch/PR is a proposal, not the formal RC. #910 P0 one playable match and #931 ART6 review have priority. Only #220 authorized writer may adopt the single verified source after #250 value decision, a fresh formal RC HEAD, exact source lock, nonforce expected-SHA CAS, same HEAD full CI and rollback. Do not merge this entire PR into RC/main. Check motion against server skills in actual Studio Solo + 2 clients, 8 fixed scenes old/new x PC/Android = 32 real images, Android 15m and OWNER acceptance. Until then `ART_NO_GO / MOBILE_NO_GO / FUN_NO_GO / OWNER_ACCEPTED=0`.