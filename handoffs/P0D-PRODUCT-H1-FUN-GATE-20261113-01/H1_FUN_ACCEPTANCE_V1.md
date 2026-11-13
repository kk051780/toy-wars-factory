# P0D企画室: H1「面白さ」採用判定パッケージ V1
Date: 2026-11-13 JST | game=EGG RAID RUMBLE / TRAP_RAIDERS | work_id=p0d-siege-v19
feature_slice=CHAT-P0D-PRODUCT-STUDIO-H1-FUN-EVALUATION-GATE-20261113-01
STAGE=DESIGN_AND_EVIDENCE_ONLY; NOT_GAME_SOURCE; NOT_SELECTED; NO_RC_CHANGE; NO_STUDIO_TEST

## 0. 制約と狙い
OWNERは2026-11-13、8safe私的試遊候補を「陳腐」と判定。公式S1進捗は#220の最後の監査75/100だが、製品FUNゲートNO_GO。
企画室の意思決定は「多機能の数」ではなく「最初90秒に卵奪取・爽快な戦闘・戦術ルート・生き物・収集欲が一つの試合として伝わるか」。#250 adoption_id=P0D-FUN-H1-001 を前進させ、別IDの新案量産ではない。

## 1. 2026-11-13 時点の競合観察（外部/一次を区別）
- 独立ランキング Blackbox Charts https://blackboxcharts.com/top : 2026-11-13の掲載時点で Steal An Egg / Blox Fruits / 99 Nights in the Forest / Break and Steal an Egg 等が上位。CCUは同時接続の一時点で、P0Dの需要・収益・面白さを証明しない。
- Roblox公式 FTUE https://create.roblox.com/docs/production/game-design/onboarding : 重要なのは「基本を教える」「楽しさに素早く到達する」「次を楽しみにさせる」。D1と導入ファネルで実測する。
- Roblox公式オンボーディング手法 https://create.roblox.com/docs/production/game-design/onboarding-techniques : 短い視覚案内/文脈型の操作説明。押し付けチュートリアルにしない。
- Roblox公式分析 https://create.roblox.com/docs/production/analytics : 公開後にD1/D7, session, payer conversion, revenueを計測。公開前は全てUNKNOWN。
- Roblox公式有料ランダムアイテム規則 https://create.roblox.com/docs/production/monetization/paid-random-items : Robuxを介したランダム報酬には確率表示とPlayer policy restrictionsが必要。初回は無料収集+任意コスメ、実課金ONせず。

OBSERVED: 市場に卵・育成・戦闘人気作が同居。INFERENCE/HYPOTHESIS: P0Dで「奪う→追う/逃げる→雑魚を掃討→育成の次目標」を結べば強い。
反証: H1で初見ユーザーが卵の目標を誤解/移動不能/攻撃が当たらない/スマホボタンが隠れる/再試行意思が無いなら不採用・修正。

## 2. 固定ソース別判定・重複不可
| Variant | fixed source | 実際に示されたもの | 限界・判定 |
|---|---|---|---|
| H0 8safe | 3120b9d3c0a5ec58c9f2613c5d186f3493b54f83 | 既存2役・卵/城/勝敗の基準作品、OWNER「陳腐」 | Freeze rollback。SRC/QA PASSはFUN PASSではない |
| A: evolution+Musou v5 | 5347cf28221badfe45bdcd1c3fc920af7ebb9e5f | #288の実40 Luau単一Game/Remote: 無双雑魚/赤警告・進化/XP/保存・モバイル配置修正・飛行VFX攻撃高さ修正。native/Rojo検査PASS | #250未選定/公式#220未統合; 実2client/Android FUN/real persistence NOT_TESTED |
| B: FIRST90 H1 + v5 | 4ebecee91b86f021d02d7e3eaffb3ecefa3e787c | #218 FIRST90 author 41 Luau単一Game/Remote: Aの機能をもとに最初90秒の server-authenticated objective cues と反例QA。native/Rojo PASS報告 | 独立候補。Aとは5秒召喚中の攻撃回数契約が異なる。AのGame/HUD丸ごと上書き禁止 |
| C: world H1 sky/sea | c73f305fb412927aee05b399a4f54a2a16d0579f | #248 8safeを土台とする空/海の物理ルート・移動クリーチャー候補 | #254で4つの城壁×通路干渉のsource-QA事実。現在のままMAP_WALKABILITY_BLOCKED |
| C' patch candidate | 2494fa855d77e1ef6dd2c5f8b8d21fbef90fc44a | #253の別branchで城壁からルートを退避したsource候補 | #248原作者による採用/正式統合、実Studio物理通過と卵保持/帰還は未検証 |

- C/C' はH0に対する別基盤のMap overlay。B+A+Cを単純にファイルごとマージしない。
- BとAは同じ源から分岐した別試作。single Game/Remote/Reward/XP/Saveの重複を作らない。
- original #220 sole RC SHA1263a03701211a652b99b91d2339575dc8104eff とは全て別。source proof != official release adoption。

## 3. 企画室からの明確な選択推奨（#250採用待ち）
推薦する評価用軸: **B（41 Luau FIRST90）を先にA/H0と比較**。目的説明+戦闘+卵奪取+進化の「1プレイ中のつながり」を最小追加開発で評価する。BにC'をまだ組み込まない。
同時に #248 作者に修正C'を検証してもらう。通路QA後、#220唯一の統合者が **Bの単一Game** に安全なルート/クリーチャーを**源契約確認の上で**入れる第二段階のH1を組み立てる。最初90秒改善の効果とフィールド改善の効果を分けて観測し、未確定の7職・648体/レア天候を初回S1の必須条件にしない。
**PRODUCT_RECOMMENDATION_ONLY**: 正式PRODUCT_SELECTやS1 RC採用の事実とはみなさない。#250/#220各責任者の判断が必要。

## 4. H0→H1実機プライベート評価（すべて未実施）
1. [ENGINE] 現行Game/Remote/score/carry/HP/round/XP/DataStore権威は各1つ。ソースlock+Luau native+Rojo+否定テスト。攻撃VFXだけで実敵HPが減らないケース、壁抜け、5秒GUARDとASSAULT回数差を負例に含む。
2. [PHYSICAL] Studio 2client各陣営、卵持ちで移動/帰還、中央/水/空が実際に通れる。#248の4城壁衝突は直すまで不合格。カメラ/救済/落下とmob障害物も検査。
3. [PHONE] 実Android横画面で851×393含む複数解像度。救助/覚醒/HP/卵警告の重なり無し、遅延/入力可視性/動作FPSを測る。計算上のHUD rectangle no-overlapだけでPASS不可。
4. [FIRST90] 0-15秒で赤青/卵/帰還方向が伝わる、15-30秒で初回攻撃と中立雑魚ヒットが見える、30-60秒で卵取得を試みられる、60-90秒で追跡・救助・戻り道の意思決定に触れることを期待する（達成は未測定）。未達時は秒数で具体的障害を記録。
5. [HUMAN] H0→A→B（順序を交替して順序効果を抑える）を初見5人程度に私的に遊んでもらい、口頭説明無しで目的を理解できるか、攻撃が気持ちいいか、もう1回遊びたいかを観察する。未成年は適切な同意と安全確保。試験小標本なので市場勝率に換算しない。
6. [FUN GATE] 仮のリリース判断線: 5人中4人以上が20秒以内に卵の目的を理解、3人以上が自主再戦希望、H1がH0より楽しさが明確に優位、重大クラッシュ/移動不能0。数字は**事前目安**であり達成済み実績ではない。いずれも未達ならREVISE、互角ならDEFER。
7. [LIVE] 本番公開後のフロー/first meaningful action、試合完走・再戦・D1/D7・売上と純収益の測定は公開承認後のみ。公開前UNKNOWN。

## 5. 試遊スコアカード（H0/A/B 個別、5段階×重み）
- egg goal 0-20点: 卵の目的と防衛・持帰りの一体感
- combat 0-25点: 雑魚を蹴散らす快感、強敵の予兆、逃走/救助
- movement/field 0-20点: ルート差・景観の意味、迷子なし
- growth 0-20点: 強さ/進化・次に集めたい魔獣の発見
- phone clarity 0-15点: UI視認性・誤操作/負荷
- TOTAL 0-100。採点者の個人差が大きいので順位と自由コメントを優先。scoreは実際に5人テスト後のみ埋める。空欄を0点と誤表現しない。

## 6. Next owner / Acceptance / Blocker
- NOW PRODUCT STUDIO (#219): この文書を固定SHA読戻しで成果登録し、#250へPRODUCT_RECOMMENDATIONを送る。CURRENT 企画受入5段階のうち G1-5可能/最後のG6実機は外部。
- NEXT #250: Bを評価用候補として明示SELECTするかH0比較を指示。B/Aの攻撃回数差（B 1成功/召喚、A最大2回の機会）を固定しAB比較で混同しない。
- NEXT #248/H1 world: #253 C'を元作者がレビュー後、城壁の4干渉と卵帰還・スマホルートの物理QAを解消する。後続コースとして分離。
- NEXT #220 sole RC: SELECTされた不変ソースだけで一体型H1を組み上げ、採用SOURCE_LOCK/回帰/単一権威/rollbackを記録。企画室がRCへ書込むことは禁止。
- NEXT OWNER (必要時): 本人Studioによる私的2client/Android評価または最終Codex QAを明示指示。IssueコメントはPC実行を開始しない。
- BLOCKER: C'公式非統合、B正式未選定、Studio/Android/実人間FUN未測定。
- HARD RULE: NO main direct write, merge, Roblox publish, paid item/extra spend, unauthorized Windows automation, P0-A/B/C CAS changes, original 5 automations changes.

GitHub references:
- https://github.com/kk051780/toy-wars-factory/issues/219
- https://github.com/kk051780/toy-wars-factory/issues/220
- https://github.com/kk051780/toy-wars-factory/issues/250
- https://github.com/kk051780/toy-wars-factory/issues/248
- https://github.com/kk051780/toy-wars-factory/issues/253
- https://github.com/kk051780/toy-wars-factory/issues/288
