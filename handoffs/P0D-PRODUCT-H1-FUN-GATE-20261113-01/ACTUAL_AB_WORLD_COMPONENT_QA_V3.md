# P0D-FUN-H1-001: A40 V6 / B42 実体ソースのWORLD・CREATURE・GAME配線監査
Date: 2026-11-13 JST | owner existing PRODUCT_STUDIO lane #219 | Stage SOURCE_ONLY_VERIFIED_NOT_STUDIO.

## 実際に読んだファイル
- B42 FIRST90 WAYPOINT, 42 Luau, immutable source SHA `837853e66278e38bb79f6399c3e8bfc9a2403be6`, actual RBXLX sha256 `2b218936d5559680f21498fb190d79dfbd0b26b8671e4f71fe62d66efec008be`, original source CI https://github.com/kk051780/toy-wars-factory/actions/runs/43390044132.
- A40 MUSOU V6, 40 Luau, immutable source SHA `4b09de3eb70abb2e79268ce41bdecc4b614d39df`, actual RBXLX sha256 `0db97a001acbe47d938d0b45e01272b2d12ac959e45d065d9f989669f7c37ef7`, original source CI https://github.com/kk051780/toy-wars-factory/actions/runs/43390992103.
- Both raw XML Places parsed by independent Python stdlib source auditor, actual source string/record verified, **14/14 executed local Python unit/negative-mutant checks PASS** (SHA, XML module counts, world class/Studio guard, 6 paths, monster preview, fake floating-castle collision and path-wall mutation rejection). This is NOT native Luau, Roblox Studio, physics, FPS or OWNER FUN evidence. Local audit script SHA256 `5a2de66675a3221c86d9527c75f56b3c171fba1893d437fccf29086c07b7537d`; test SHA256 `dfaaceed74f02b4f41a55868846906a8347ad3cd723212faeb26ce8a1e3b5591`; result JSON SHA256 `2231b04d91319c53fd28bb07ff737945675cf8637e2a70d15ddba2ce349fc89e`. Local files delivered to user in the source chat only (not GitHub scripts).

## 実際の新事実（前の台帳の大ざっぱな理解を訂正）
1. **両方とも `ServerScriptService/TrapRaidersS1/H1FunWorld` が Script として入っている**。`Game` の別ServerScriptとして、Studioのみの `RunService:IsStudio()` guard後、`workspace:WaitForChild("TRAP_RAIDERS_S1",30)` の現在のGame製MapBuilderへ `H1_FUN_WORLD` を追加するコードが実配線。単なる「別branchの企画案だけ」「42には世界が入っていない」は誤り。GameとH1FunWorldの2 Scriptは**2つの対戦権威ではない**（後者はMap装飾/2体プレビュー）。Engineで実生成できたかはNOT_TESTED。
2. 両者の `H1FunWorld` のバイト列SHA256は **`a02291dbbc62...` で同一**（正式SHA256は添付ソース監査JSON参照）。`SKY_RAMP_RED` `SKY_WALKWAY` `SKY_RAMP_BLUE` と、`SEA_ENTRY_RED` `SEA_LOW_CAUSEWAY` `SEA_ENTRY_BLUE` の**6つの固体通路パーツ**を持つ。Sky x最大62(+width6)=68、sea x最大72(+width5)=77で、MapBuilder既存の城側壁が始まる|x|=83から少なくとも6 studsの保守的X余裕。これは**ソース上の座標検査**でありStudioの物理可通性/卵運搬成功ではない。
3. #248別ソース `c73f305f...` の4つの城壁衝突は **このA40/B42にそのまま当てはめてはいけない**。ここのSkyはz=18、Seaはz=-22/中心x±72、旧#248問題ルートのz=43/-45/x±99と異なる。一方、#248の修正版 `2494fa...` を二重にマウントすれば `H1_FUN_WORLD`重複・Route重複の危険がある。正式#220は必ず現物の `H1FunWorld` を確認して単一scene writerとする。
4. **巨大な浮遊城はまだ遊べない**。`FLOATING_SKY_ISLAND` はY=62、`CanCollide=false` の遠景装飾。遊べるSky高架はY=16で浮遊城への接続・空中城での卵盗み・城攻撃は未実装。つまり「空中ルートの原型が動くソース」≠「天空城が戦術拠点として機能」。
5. **幻獣もまだ戦闘・本当の図鑑育成に連結されていない**。`SPACE`のクジラ/ `CELESTIAL`のペガサスは `VisualPreviewOnly=true`, `NoRewardNoD18Ownership=true`; 発見時 `player:SetAttribute("H1_Found_"..id,true)` はセッション中のみ。別途サーバーの`MusouHorde`中立兵9体は戦闘ソースなので混同しない。
6. **本物の海戦はまだない**。青い水面 `COSMETIC_SEA` は非衝突装飾、SEAルートは実コリジョン付き歩道。潜水/船/海の敵との卵争奪は現ソースに実装済みとは主張しない。

## 企画室の採用判断（余計なアイデア増産なし）
- B42 FIRST90 は #250 で**非公開私的試遊**向けに選定済。A40 V6は敵外観比較用。同一Sourceの `H1FunWorld` が両方にあるので、世界比較としてのA/Bではなく**第一90秒案内と中立敵V5/V6の違い**を人間が見て評価する。
- #220 sole RCは、B42/A40の現物を受ける前に `H1FunWorld` が既に入っていることを理解し、**同じworldを2回採用しない**。現物でYESなのは「Studioでは生成し得るスクリプト」まで。実Roblox Studio2client/Android/本人FUNは未検証のまま。
- 次の創作/実装単位は新キャラ100体ではなく、**浮遊城へ実際に到達でき卵の奪取/護衛に使える1本の戦術ルート**。#222/#248既存WORLD作者にH1_SOURCE実験として検討を渡す。既存の单一卵/得点/HP/保存/Remote権威は不変更、無償入口・安全復帰・両軍公平/スマホ・2clientを先行仕様化。
- Source QAなら道が城壁を避けることは確認できるが、真正な道順の通行・浮遊城侵入・卵持ち帰還は**PC Studio実プレイ/物理でのみ検証可能**。この報告で正式RC採用や実機FUN合格を宣言しない。
- NEXT_OWNER=OWNER safe private Studio B42/A40 2-client + phone; #220 sole decision; #248/#222 world source owner for future playable floating castle; #219 follows until adoption.
- STATUS=SOURCE_QA_ONLY; LAST_SOLE_S1=75/100; PRODUCT_FUN_GATE=NO_GO; no main/RC/merge/publish/paid/PC/CAS/5 automation changes.

## 参考
#218 / #219 / #220 / #250 / #248 / #253 / #288 / 監査の元ゲーム2本のSHA。