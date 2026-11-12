# P0D S1 最新V6：途中参加・退出・人数不足・連続再戦の独立結合QA

game_id=TRAP_RAIDERS、work_id=p0d-siege-v19、release_id=P0D-S1-KIDS-RC01
packet_id=P0D-S1-V6-ROSTER-ROUND-CYCLES-NATIVE-20261112-01
issue: https://github.com/kk051780/toy-wars-factory/issues/233

## 対象と原理
公式固定コミット `1263a03701211a652b99b91d2339575dc8104eff` にある正規のサーバーGame・本物のMapBuilder・実Rules/LobbyTeamRecovery/Config/S1TrapRules、計6ソースを正規native Luauで実行。元の受入済み実マップ統合QA `84d061d81ffd28418f6e28e9e85bb684dd0daaf7` の固定バイトを読み込んで、試験コードのみ拡張する。**公式ゲーム本体のソースには一切変更なし。**

現行2人の正規試合・マップ・卵・罠・攻撃・勝敗・再戦が既に動いた後、次を追加で確認する。

- 試合途中に3人目と4人目が入っても2対2へ均等に配属される
- 途中参加REDが実際のBLUE卵を奪い、退出したら卵が帰り、仲間が残るRED陣営はその時点では負けにならない
- BLUEの4人目が退出しても、BLUE2人のうち元の1人が残る試合は続行する
- BLUE最後の人が抜けると、元の試合終了条件が適切に適用される
- 結果終了→ソロ待機→2人揃いカウントダウン→再びソロで中止→次の2人目加入→新たなラウンドが始まる
- 前ラウンドの攻撃seq=5は新ラウンドでも拒否され、seq=6だけ攻撃が成立する

意図的に「全員BLUE配属」「退出時の卵回収なし」「仲間が残っているのに負け」「カウントダウン中止忘れ」「ラウンド開始で通信seqを0に戻す」という5つの危険なGame.server変異を**元ソースの一時コピー上のみ**施し、それぞれ想定した本物のLuauアサーションで検知できるかも検査。

## 使い方
```sh
python3 handoffs/P0D-S1-V6-ROSTER-ROUND-CYCLES-NATIVE-20261112-01/tools/roster_cycle_native.py --selftest
python3 -m unittest discover -s handoffs/P0D-S1-V6-ROSTER-ROUND-CYCLES-NATIVE-20261112-01/tests -v
python3 handoffs/P0D-S1-V6-ROSTER-ROUND-CYCLES-NATIVE-20261112-01/tools/roster_cycle_native.py --repo . --luau /path/to/native/luau
```

CIは固定された公式native Luau（`f46d879e28302a430029304f7f6a162aed66f103`）をビルドする。元6 LuauのGit blob完全一致・元QAのSHA・本packの全バイトSHA256マニフェストを照合する。

これはRobloxサービスを試験用ダブルに置換した**実ゲームロジックのオフラインnative Luau**であり、Studio実機／リアル2クライアント／子ども試遊／スマホ物理・ネットワーク遅延／公開の証明ではない。全体S1進捗率は#220唯一の統合担当が決定する。自パックの成功を公式リリース達成と呼ばない。

保護: main/公式RC/merge/Roblox本番公開/支出/OWNER Codex/P0-A/B/C本人認証CAS/5件の自動化を変更しない。
