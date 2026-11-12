# P0D S1 eight-safe｜実サーバー → HUD＋子供ガイド 結合回帰テスト

**位置付け：正式RCの変更ではない独立テスト。** 固定ソース `7b4f95a3f424741bbe8ff1c555c5f5a2ed64d4bd` を読み込む。これは21本の本物のLuauソースがある未公開8変更版Rojo製品であり、Game`e684ca79b8f5ed279bcdf033f4118bf77d552abb`・Coach`d8dda6b1781375612c123f8c83b6f23fe45d09f1`・HUD`50823390853989ccdda78e28c16ea4757bbe0715`は全て固定Git blob。

## 過去のQAとの違い

- 7変更版#238：本物のGame.server/Map/Rules/Lobby/Trapが発行したSNAPSHOTを、本物のGuardian Coachに渡した（164 assertion）。
- 8変更版#240：本物のHUDをネイティブLuauで動かし、テスト用に作ったSNAPSHOTを渡した（43 assertion）。
- **今回：本物のGame.serverが発行したBLUEプレイヤー向けSNAPSHOTを実際に捕獲し、同じLuau VMで本物のHUDとCoachの両方へ渡す**。LOBBY→GUARDIAN選択→COUNTDOWN→ACTIVE→卵奪取→RED得点→RESULTS→再戦ACTIVEと、同じ試合中の遅い旧パケット/試合を跨いだ旧パケットもテストする。危険なHUD古いupdateId受入・Guardian罠ボタン非表示・server更新番号停止の変異を、テスト専用コードだけに加えて各エラーを検知する。

**注意：** Roblox外部サービス、Instance、RemoteEventの外側だけをモックする。Roblox Studioの実2clientネットワーク/本当のスマートフォンのタッチ/UI表示/物理演算を再現したという意味ではない。脚本で実パケットを意図的に到着順変更するネイティブ回帰検証である。これ以外に実機QA30ケースは全てNOT_TESTED。

## 技術と所有権

テストは過去実績ある#238の完全サーバー＋Coachの元テストを固定Git Blobごと取り込み、#240の元HUD Client UIの外部Roblox環境モックだけを借りる。本物のGame/HUD/Coachのソース本文は一切変更しない。37ファイルのBUILD_MANIFESTを全再検証し、7安全版との差分がHUDのみであることを証明する。Genuine native Luau interpreterは上流固定commit `f46d879e28302a430029304f7f6a162aed66f103` を使用する。

完全なコマンド：`python3 run_eight_real_hud_coach.py --selftest`、`--repo . --source-only`、`--repo . --luau /path/to/luau`。CI workflowで自動検証し、実行ログと40文字の固定commitのみを#220専任統合担当に引き継ぐ。

**制限：** official `rc/p0d-s1-kids-rc01`・main・ゲーム本体・他人のbranchには一切writeしない。Codex/Windows/Studioを実行せず、ロブロックスに公開せず、課金しない。OWNERの公開指示も必要。単体QA完了率をS1全体の完成率75/100と混同しない。
