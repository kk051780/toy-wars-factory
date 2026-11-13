# P0D H1 — 操作が分かりやすい28本統合試作版（未公開）

## 変更点
#255でSOURCE/native/Rojoの通った全28本の同じゲームを維持して、#251の既存オリジナル HUD修正版（GitBlob `313484a69eb10ce01bbdb4872afee215133b01d4`）**だけ**を追加で採用した、独立した私的Studio候補。

- RAIDER風走りボタン：卵運搬中/クールダウン中/風走り中は押せない表示。運搬中は「🥚 卵運搬中・風走り不可」。
- GUARDIAN罠ボタン：卵運搬中/クールダウン中は押せない表示。運搬中は「🥚 卵運搬中・罠は使えない」。
- 実サーバーGame、卵、勝敗、速度、罠、全職実装数（2職）、地形、幻獣2体、D18案内キャラは**変更なし**。元H1の28本を増やしていない。
- HUDはクライアントの表示であり、セキュリティの正式ルールは元のGame/WindRules/TrapRulesのみ。

## 再現可能な元ソース
- ベース #255 `1498c2d344ede2d9da6c2bfdd025ebc1a15ec48b` の28本Rojo全ゲーム
- #251 original UX only `4606a74dcebdf4d8a51de4e69b930a15ac788180`
- base server #252 25 source、壁修正 #253、D18 original Batch8 client 3つは同一SHAを維持
- 本候補は独立 `handoffs/P0D-H1-KIDS-UI-20261113-01/**` 及び専用workflowだけ。#255原本や正式 #220 RCを書き換えない。

ルートリポジトリから `python3 handoffs/P0D-H1-KIDS-UI-20261113-01/tools/assemble.py --assemble` を実行して、出来た `dist/TRAP_RAIDERS_H1_WOW_STUDIO_ONLY` の全ソースを使いRojoビルドする。私的Studio以外では海空/D18アートはソース上でOFF、公開用途ではない。

## QA基準
- 新HUD1/1GitBlob一致、Game等源ソース固定5/5、実Luau28/28構文、実RojoXML28/28一致
- UIボタンの条件消失など10種類の意図的な不正書換は全て拒否されること（PythonソースQA）。**これはRoblox UIが実機で押せないという証明ではない**
- オーナーの2client・実Androidタップ検査、卵運搬UI/罠/風走り、天空・海の往復、D18案内、H0との楽しさ比較：すべて **NOT_TESTED**（Studio実機証拠待ち）

採用候補ID `P0D-FUN-H1-001`、元H1/公式RC/公開不可のゲートは変えない。最終採用権限は #220。公開、merge、課金、追加費用、Windows Codex操作、P0A/B/C CAS、既存automations変更は禁止。
