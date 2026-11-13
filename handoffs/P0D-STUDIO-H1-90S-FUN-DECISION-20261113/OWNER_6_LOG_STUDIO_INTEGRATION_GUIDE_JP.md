# P0D企画室｜H0/H1 6ログを改善1件へつなぐ
調査日 2026-11-13 JST｜採用ID P0D-FUN-H1-001｜ソース・試遊準備のみ

## 何を改良したか
最初の90秒のH0 vs H1比較に、既存の読み取り専用Studio観測器から出るSERVER/RED/BLUE Outputを連携。欠落したゲーム起動、赤青の混在、使い回したログ、警告をHOLDとして拒否し、OWNERの人間評価が埋まった場合に限り、既に作った改善候補から1件だけ提案する。自動RC採用・公開・課金・PC操作は一切しない。

## 確定した原本
- H0 QA-only 23-Luau Place: SHA256 f0d45aae5469cdb862e3642b65fdc5c4c7da8ada924b3a0d48291cabca89344b（#245）
- H1 QA-only 30-Luau Place: SHA256 f290c6fccfa8796220fa4f13000a53ed8f8ec7c7a269951280938aff3240ee7e（#259）
- 元の検査プログラム #245 review_studio_probe_logs.py GitBlob d2e4580e1ea417225d7e75a6ea83b559a4f677ac をvendor内へ一文字も変えずに再利用。既存の48? ではなく正確に34項目の手動検査は元のまま NOT_TESTED。
- 企画室の前回の decide_next_ab.py をそのまま使用、機能案を新しく増やさない。

## OWNER Windows Studio 最短操作
1. H0とH1を別のローカルPlaceとして開き、Roblox Studioの Test → Server & Clients → 2 → Playで試す（公式 https://create.roblox.com/docs/studio/testing-modes）。公開・本番上書きは禁止。
2. それぞれ SERVER / RED / BLUE のOutputを別々に保存して、H0_SERVER.txt、H0_RED.txt、H0_BLUE.txt、H1_SERVER.txt、H1_RED.txt、H1_BLUE.txt の6テキストファイルにする。観測器 P0D_STUDIO_PROBE_V1 の行を確認。
3. 実際の卵を取る→運ぶ→得点、海/空の移動、風/罠、ドラゴン案内、勝敗/再戦を確認。Androidなどスマホ実機チェックはエミュレータで代用したと申告しない。最初90秒の楽しさ0〜5点、初アクション秒数と再戦意思を記録。
4. 本パックの OWNER_STUDIO_H0_H1_BLANK_NOT_TESTED.json のローカルコピーに、実施した結果だけ入力。未実施は偽のowner_confirmationを立てない。
5. PythonをインストールしたPCで次の1行を実行（本パックを含むrepoのルートから、ファイル名は適宜調整）。

```powershell
py handoffs/P0D-STUDIO-H1-90S-FUN-DECISION-20261113/bridge_studio_evidence.py --owner-json OWNER_FILLED.json --h0-server-log H0_SERVER.txt --h0-red-log H0_RED.txt --h0-blue-log H0_BLUE.txt --h1-server-log H1_SERVER.txt --h1-red-log H1_RED.txt --h1-blue-log H1_BLUE.txt --output H0_H1_ADVISORY_NEW.json
```

## 判定の意味
- HOLD：未試遊、ログの欠落/混在/使い回し、ACTIVE相不足、観測器の警告、スマホ評価・人間評価不足。
- STOP_FIX：卵奪取、持帰りや地形など元ゲーム実装の不具合。新キャラ/演出より先に修正。
- REVISE_ONE_AB_ONLY：スマホUIなら#260、目標が迷子ならD18コンパス、通れるが長いなら#262、取得が地味なら#266の、**一件だけ**比較。
- RECOMMEND_SOLE_RC_REVIEW：人間が入力した試遊評価のルール上は候補。Studioの真実・子どもの面白さ・公開合格を自動証明しない。#220のみ正式RC採用。

## 安全・プライバシー
6ログはただのユーザー提出テキストなので加工を防止できない。人間によるStudio/スマホ実画面の検証が必須。元ログの個人名・ユーザーID・チャットは公開GitHubへ貼らない。出力は原本パーサの許可済みイベント種別・件数・SHAのみ。Pythonテストは人工データであり、実プレー証拠ではない。
通常のRoblox公式StudioTestService APIも将来の自動2client検証に利用できるが、ここでは実行していない：https://create.roblox.com/docs/reference/engine/classes/StudioTestService

## 進捗区分
企画室の商品判断・安全なログ接続コードが完了しただけ。OWNER実機試遊0件、H1新規採用0件、P0D正式ゲーム進捗#220最終値75%、フィールド#222最終値50%。既存main/RC/課金/公開/PC/Codex/Automationsに変更なし。
