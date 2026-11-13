# EGG RAID RUMBLE — 卵→育成→分岐進化→神話形態

OWNER requested 2026-11-13: 「レベルの作り込みはそれだね。あとは進化という要素も欲しい」

- Issue: [#287](https://github.com/kk051780/toy-wars-factory/issues/287)
- Owner lane: `P0D-EVOLUTION-BRANCHING-PURE-POLICY-20261113-01`.
- Player-facing game brand **EGG RAID RUMBLE**; original internal `TRAP_RAIDERS`, `p0d-siege-v19` remain unchanged.
- This source is a new independent **policy + visual Studio gallery**, NOT real match integration. It does not create another `Game.server` or edit/merge #220 release controller.
- Current dependencies: [#275](https://github.com/kk051780/toy-wars-factory/issues/275) original IDs `starter_scout`, `forest_scout`, `star_scout`; [#281](https://github.com/kk051780/toy-wars-factory/issues/281) real Lv1-50/masteryLv1-10 XP; [#285](https://github.com/kk051780/toy-wars-factory/issues/285) optional permanent combat strength and 8-second once-round awakening; [#280](https://github.com/kk051780/toy-wars-factory/issues/280) first real original scout Game candidate; [#282](https://github.com/kk051780/toy-wars-factory/issues/282) and [#286](https://github.com/kk051780/toy-wars-factory/issues/286) original persistence/XP; [#284](https://github.com/kk051780/toy-wars-factory/issues/284) read-only growth HUD.

## Why evolution is not simply higher stats

Four-stage PERMANENT growth with a **meaningful choice in stage 2**, distinct from #285's **temporary 8-second awakening**. No legendary gets an extra hidden stacking PvP multiplier above #285. A Stage 3 veteran has remarkable body/summoning/elemental effects and large PvE advantage through level/mastery; PvP still has counterplay and capped combat modifiers. Ownership remains exactly the same `itemId` through all forms; changing form never loses the hatch reward, previous collection discovery, or paid skin (not sold here).

| Form | Requirements (both gates) | Evolved fragments (FREE) | Proposed unlock |
| --- | --- | ---: | --- |
| 0: 幼体 | Egg ownership | 0 | Base ability is ready immediately |
| 1: 成長体 | Player Lv10 and item mastery Lv3 | 2 | Updated visible movement, novice tactical improvement |
| 2: 分岐進化 | Player Lv25 and mastery Lv6 | 5 | Choose attack/area pressure OR guardian/support route |
| 3: 神話形態 | Player Lv40 and mastery Lv10 | 10 | Immense dragon/VFX and ultimate ability DESIGN target |
| Final Lv50+ | Lv50 after mythic | No separate mandatory evolution | Optional legendary aura and mastery title |

Gates are **proposed initial tuning**, not observed retention or expected player completion times. The 3 upgrade costs sum to 17 FREE fragments, earn 1 from each legitimate objective-participating 60–360s match, 2 when 2+ server-confirmed objective actions; capped 2/round. Stage2+ branch can be changed for 3 earned fragments in the lobby; do not make a mistaken branch an irreversible loss. Round server + owned/XP verification is mandatory, client cannot directly award materials. No Robux/material boost, pay-to-win evolution, paid random forms, or mandatory purchase.

## Evolution signatures across all six collection categories

| Kind | Assault branch: aggressive play | Guard branch: support/counter |
| --- | --- | --- |
| BEAST | `SKY_HUNTER`: aerial spotting + mob pressure (carrier flight forbidden) | `EGG_GUARDIAN`: castle/local egg defense, reveal intruders |
| SPELL | `STORM_ARC`: dramatic PvE mob chain magic | `ICE_BRIDGE`: clear ally route over water |
| MOUNT | `SKY_DASH_NO_EGG`: air shortcut without an egg | `SEA_ESCORT`: escort boat, visible counter along coast |
| ITEM | `ENEMY_SCANNER`: active route insight | `ALLIED_SHIELD`: short defensive cover |
| ZOMBIE | `MOB_DISTRACTION`: enemies chase summoned decoy | `GATE_BLOCK`: limited castle blocking squad |
| TRAP | `PRESSURE_SNARE`: warning net/slow | `CASTLE_ALARM`: visible egg-perimeter signal |

**Truthful content count:** This *policy* currently whitelists three actual original #275 BEAST item IDs plus five hypothetical other-category demo IDs. A demo item in the registry is **NOT OWNED and NOT currently playable in the H1 game**. The catalog is designed to be driven from the real D18 canonical source later; items must have verified original 3D, mobile-ready skill, server authority, original cooldown, and actual 2-client engine QA before counting them playable. New monsters are never manufactured by altering existing paid/rare egg odds.

## Implementation contract

- `src/EvolutionRules.luau`: pure SERVER-only profile & evolution state. `newProfile(userId)`, `creditRound(profile,roundId,serverObjectiveCount,duration,serverConfirmed)`, `nextEvolution(profile,itemId,ownedItems,accountLevel,masteryLevel)`, `evolve(profile,itemId,ownedItems,accountLevel,masteryLevel,phase,requestId,choice,serverConfirmed)`, `switchBranch(...)`, `form(...)`.
- `profile.forms[itemId] = {stage,branch}` and `profile.fragments`. One immutable receipt per `JobId:matchEpoch:userId` fragment settlement, one server-generated `requestId` per evolution action or branch respec. Replaying an exact evolution request returns saved receipt without charging again. Mismatched item/choice on same receipt is conflict. 4,096 receipt cap fails closed pending rolling storage/migration (do not silently delete and make receipts redeemable again). **These source arrays are not persisted here.**
- **CRITICAL**: Original #281 xp/mastery/owned from #275/280 must be read from the same trusted player profile as evolution, never supplied by client. #282/#286 owner must eventually perform same atomic `UpdateAsync` profile mutation including fragments, forms, earnings receipts, existing owned/equipped/mastery/settled round IDs to avoid inter-server duplicate/lost update. Return state to client only by one Game's existing Remote through its sole integrator, not a new live event.
- `form().abilityDesignId` and Stage3 `formToken=MYTHIC` are **design signatures only**. They are NOT real combat code or a working legendary dragon. `additionalPvpStatMultiplier=0`, `modelId=NOT_INTEGRATED`, `actualCombatImplemented=false`; #285 remains the combat power budget owner.
- Existing actual H1 supports two roles and two modes, not seven finished roles. Do not claim all species/classes are live.

## Private 3D vision sample (real source, not completed gameplay)

`demo/EvolutionGallery.server.luau` builds 5 original toy-like dragon appearances with Roblox Parts/Wedges/highlight: (0) tiny mint hatchling, (1) adult wings, (2a) crimson sky assault, (2b) blue water guardian, (3) giant glowing golden mythic. `demo/EvolutionGalleryCamera.client.luau` uses simple touch buttons to inspect each silhouette in the stand-alone `default.project.json` Rojo private Studio. Both scripts exit immediately outside `RunService:IsStudio()`. All materials are original and built from Roblox primitives (no third-party/unlicensed 3D import). No real summon AI/combat/ability/damage/egg ownership/purchase/storage in this gallery.

Repro with owner's existing trusted Rojo installation:

```sh
cd handoffs/P0D-EVOLUTION-BRANCHING-20261113-01
rojo build default.project.json -o EGG_RUMBLE_EVOLUTION_GALLERY_PRIVATE.rbxlx
```

Review human silhouette appeal, HUD mobile camera clipping, minion-only overpower vs PvP effective fairness, attack/guardian route clarity and natural animations. Avatar model quality and mythic particle/FPS are **not validated by this source**, even if original Place compiles.

## Native QA

```sh
python3 -m unittest discover -s tests -p test_project_static.py -v
python3 tests/run_native_evolution.py --luau /path/to/real/luau --compiler /path/to/real/luau-compile
```

GitHub Actions uses exact pinned native luau-lang source version `f46d879e28302a430029304f7f6a162aed66f103`. Runtime checks exercise full form/cost/branch/ownership/receipt replay/AFK/match cap/paid flag, compiled original source. Static tests check Studio-only and project wiring. **Never claim native PASS until an exact-HASH completed-success job with log is confirmed.**

Next real game integration requires #220 sole integrator to select and join #281/#285/#275 and #286 profile in ONE original Game; choose ONE original H1/H2 Game server + one Remote. Then actual dedicated BEAST Stage1 moving/summon + explicit attacker-vs-guardian action, enemy seeing and defending against it, persistent reconnect and 2-client+Android QA. Other five categories extend after success.

Official only S1 release estimate as last audited: 75/100; real owner original early-session FUN gate NO_GO. This isolated feature's source/QA completion must not inflate it. No main writes/merges, live Roblox publish, purchase/pricing changes, paid combat/egg luck, PC Codex, P0-A/B/C CAS or five automations modifications.

## V2：分岐進化が「実際に異なる働き」をするStudio専用PvEラボ

追加日：2026-11-13 JST。前述の原創ドラゴン外見展示とは独立した battle.project.json を追加。既存の EvolutionRules.luau をサーバー側から呼び、魔獣 forest_scout の攻撃分岐と守備分岐が実際に異なる結果を生むソースを用意した。**正式ゲームH1/H2には未統合。**

- battle/EvolutionCombat.server.luau：原創3D進化ドラゴン、城HP120、敵中立NPC（最大14体・HP60・城へ進軍）、紅蓮進化は周囲17studs（神話25）内のNPC HumanoidへサーバーでTakeDamage、蒼潮進化は城への攻撃を8秒・3回（神話5回）までサーバー側で遮断、技再使用12秒。
- battle/EvolutionCombat.client.luau：スマホ横画面でも押せる進化4択と技発動ボタン、残クールダウン、城HPと中立NPC数。実アカウントデータは変更しないことを画面に表示。
- **進化の段階・素材は訓練用の仮想実績**：進化形態を素早く試すため、専用Studioサーバーが仮想Lv40・熟練Lv10と架空の正規11試合を内部生成し、正規のEvolutionRules.evolveを呼ぶ。実ゲームでの育成・アイテム取得・進化達成を証明するものではない。何もDataStoreへ保存しない。
- サーバーはフォーム4択ホワイトリスト、選択1秒制限、12秒間の技再発動拒否、サーバー正本フォーム検証、NPC射程、城シールド残りヒット数を確認する。プレイヤーへのダメージや、PvPのレベル差はこのラボでは評価できない。
- PvEは既存の#285正式戦闘計算器ではない独立の検証用。元H1/H2のGame/Remote、#286持続XP、#220公式RCを変更しない。無断本番公開なし。

Rojo（OWNER PCに導入済みの場合）の再現コマンド：

    cd handoffs/P0D-EVOLUTION-BRANCHING-20261113-01
    rojo build default.project.json -o EVO_VISUAL_PRIVATE.rbxlx
    rojo build battle.project.json -o EVO_BATTLE_PRIVATE.rbxlx

**OWNER実機確認が必要な事項：** 2clientの同一NPC撃破・同じ城HP変化、守護のヒット遮断、技連打12秒拒否、他人から見える魔獣、スマホ誤タップ/視認性、14体NPC＋神話演出のFPS、スタック/長時間試遊。現在この実機試験は未実施。別レーンの#220のみ正式ゲームへの選定・統合が可能であり、#250製品採用手順も変わらない。

## V3：進化図鑑の履歴を消さない「FormDex」

新規 `src/EvolutionFormDex.luau` は、**元の `EvolutionRules` の真の所有品・進化形態・サーバー保存済みの進化記録（evoReceipts）を読むだけ**の独立モジュール。プロフィール・レベル・進化素材・図鑑の権利を変更することは一切ない。原本の `EvolutionRules.luau` は変更せず、`Dex.new(EvolutionRules).snapshot(evolutionProfile,ownedItems)` で読み取り専用の画面向けデータを作る。

1品の魔獣につき幼体 S0、成長体 S1、攻撃型 S2、守護型 S2、攻撃神話 S3、守護神話 S3 の **最大6形態**を図鑑で追う。成長後に進化先を切り替えても、一度進化した「別の枝」の履歴は既存の正規 `evoReceipts` に残るため再構築できる。現在装備できる形態はサーバー正規の `forms[itemId]` から求め、**発見済み履歴と現在の装備形態を混同しない**。図鑑から直接過去の枝へ無料で切り替える権利は付けず、正規の `switchBranch` の素材支払いを使う。

本モジュールの出力は `schema=EGG_RUMBLE_FORM_DEX_V1`, `items[]`, `discoveredForms[]`, `activeFormId`, `discoveredCount`, `missingForms`。現時点の #275 実在アイテムIDと未公開デモ用IDを区別する `isCurrentPlayableId` も保持する。偽の進化受領記録（段階矛盾、異なるアイテム・枝・FormID、将来形態の偽造）は復元時に fail-closed で拒否する。

**永続化について**：本モジュールは DataStore を呼ばない。図鑑履歴の根拠となる `evoReceipts` が本番でセーブ/再取得できることはまだ未実装。#286 と競合する第二のデータ保存処理を追加しない。唯一の #220 統合担当が選定後、Owned/Equipped/XP/Mastery/Forms/Fragments/EvoReceipts を *同一* `UpdateAsync` 保存トランザクションへ追加する必要がある。Receipt の容量上限を超えた場合に履歴を削除すると過去の発見が消えるため、履歴の独立した不変要約を同トランザクションで保存する設計は将来の契約課題。

再現可能な純Luau実行試験：`python3 tests/run_native_formdex.py --luau /path/to/luau --compiler /path/to/luau-compile`。正規進化→枝切替→神話両枝取得の完全な発見履歴、未所持、二重進化ID再試行、偽記録拒否、サーバープロフィール不変を実際にオリジナルLuauソースで検証する。Github Actionsの成功時だけ「実行テストPASS」と報告する。

**進化図鑑UI・正式H1/H2の表示・本物の再ログイン保存**はこの段階では未実装。進化図鑑のデータ投影を作ったという事実と、本物のゲームで図鑑を完成させた事実は区別する。
