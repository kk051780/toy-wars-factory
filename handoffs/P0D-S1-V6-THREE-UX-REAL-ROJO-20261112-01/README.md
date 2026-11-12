# TRAP RAIDERS S1 V6｜日本語案内・Guardian説明・スマホ罠ボタンの３点統合レビュー

game_id=TRAP_RAIDERS、work_id=p0d-siege-v19、release_id=P0D-S1-KIDS-RC01
packet=P0D-S1-V6-THREE-UX-REAL-ROJO-20261112-01
担当Issue：https://github.com/kk051780/toy-wars-factory/issues/231

## 目的と実装内容

本当にゲームとして起動できる **21本のLuau一式** を、公式S1固定コミット `1263a03701211a652b99b91d2339575dc8104eff` と実際の検証済みUXソースだけで組み立てる。2点統合ソースの固定コミット `438831cbef68a22c5257a4738ceb27c8182cb09f` が元。さらに独立受入済みのHUD `10940c76d708f99be908c587094c00757b22e7f6` を追加。

唯一の変更は正規の3件：
- MapBuilder：卵／城／納品先の日本語案内、入力 `78f849af28e15d7e990dd2690f2cafff0854d001`
- FirstMinuteModel：Guardian罠設置・20秒待機の最初60秒説明、入力 `e29d37737890671d458072bebe729127878700f6`
- HUD：罠ボタンを左下の移動スティック付近から、右の攻撃ボタンの上へ、入力 `10940c76d708f99be908c587094c00757b22e7f6`

残りの**18件は公式RCのソースblobと完全一致**。サーバーの勝敗・移動・攻撃・罠の権限、ボス有効化のOFF判定、報酬・課金は触らない。元ゲーム・main・公式RCに直接書き込まず、独立した `preview/` プロジェクト内に21件のLuauと正規Rojo定義を複製している。

`SELECTION_LOCK.json` は22件のプロジェクト及びソースをGit blob SHAとbyte数で固定。`tools/check_three_ux_rojo.py` は元のGit履歴、3採用元、実際にRojoが作るrbxlx内の21 Script/ModuleScript/LocalScriptのソースbyteを全部照合し、9件の危険な改ざんを拒否する。公式Rojo 7.7.1のZIP SHA256も固定。GitHub Actionsはさらに21件の本物Luauコンパイルを確認する。

## 証拠の限界と引き渡し

GitHub Actionsの添付 `TRAP_RAIDERS_S1_V6_THREE_UX_REVIEW.rbxlx` は**完成候補のレビュー用ファイル**で、Robloxへの公開ファイルでも、Roblox Studio実機でのテスト合格でもない。2クライアント、移動しながら罠を設置、卵運搬、試合終了と再戦、スマホのジャンプ・画面セーフエリア・実際の子どもの理解度・FPSはOWNERの最終一括検証が必須。

唯一の統合担当 #220 が現在の公式RCに採用してよいか判断する。追加のコレクションや幻想世界S2+は今回の初回S1リリースのブロッカーにはしない。自分のパック5/5完了と、公式ゲーム全体75/100の監査値は混同しない。

禁止: main/公式RC直接変更、勝手なmerge、ゲーム公開、課金・支出、OWNER承認なしCodex起動、P0A/B/C保護/CAS/5自動化変更。
