# TOY WARS FACTORY — チャット間継続規約

コード・権限・品質・公開判断の唯一の正本は GitHub repository kk051780/toy-wars-factory の現在の main ブランチ。2026-11-08に公開を確認したが毎回GitHubから権限を再確認する。生成 status は正本ではない。

新しいチャットでは、まず現在main HEAD、PROJECT_STATE.json、AGENTS.md、config/quality_policy.json、PR・Actions・Issues・twf-repair-coordinator をGitHubから直接取得する。mainの status/CHAT_HANDOFF.md と status/LATEST_STATE.json は歴史的な生成資料であり最新の正本とは扱わない。

補助的なread-modelが必要な場合だけ、twf-handoff-snapshots の status/CHAT_HANDOFF.md と status/LATEST_STATE.json を**同一不変commit SHA**から読む。schema=2、canonical_repo=kk051780/toy-wars-factory、release_decision=HOLD_ENGINE_UNVERIFIED、40桁hexのsource_revisionを検査し、GitHub compareで現在mainに対する祖先性とsource_revision以降の変更が status/ のみであることを独立確認する。twf-handoff-snapshots-g0002以降も世代連続性・全祖先の2つの100644通常ファイル・512個以下の直列履歴・孤立rootのprior-snapshot-tip連鎖を検証する。欠落・不一致・不確証時はUNTRUSTED_STALEとして破棄し、main/PR/CIから直接再構成する。スナップショットは承認・権限・実機検証・公開許可の根拠ではない。

同じChatGPTプロジェクト内の新しいチャットで「TOY WARS再開」の一言を送れば、AIは上記の状態取得から始める。古いチャットの記憶や添付よりGitHubの現物を優先する。

tools/build_handoff.py はコードサイズとキャラクターと進捗を入力に、引き継ぎを自動生成する。更新がない場合は架空の進捗コミットを追加しない。ゲーム開発と自律開発システム改善の二重ループを管理し、テストと実測証拠を残す。

ただし、まったく新しいチャットがユーザーの発言なしに自動開始され、GitHubを自動で読み込むことまでは製品仕様として保証できない。定期タスクおよびGitHub Actionsはチャットと独立して作動する。作業にはAIランナーと認証が別途必要。

公開、課金、権限拡大、品質基準緩和は所有者承認。スマホだけで操作できる方式を優先し、PC上の手動デバッグは求めない。

## 再開地点と未マージPRの記録

PROJECT_STATE.json の resume_checkpoint は、確認済み作業、参照コミット、
証拠ファイル、承認範囲、未確認事項、直後の作業を保存する。
review_queue は未マージPRの帰属と検証範囲を保存する。
tools/build_handoff.py は両方を JSON と人が読む引き継ぎに転記する。

これらは記録時点の状態であり、最新PR一覧やActionsへの直接照合を省略する根拠にはしない。
新しいチャットでは、mainに未反映の修正提案もPR一覧から確認する。
PRを作っただけの変更をmainの実装済み機能として数えず、Gemini失敗と別の
チャット内修正を区別する。再開を求められたことだけで、消費済みの単発推論、
定期AI実行、自動マージ、Roblox公開の承認を復活させない。

引き継ぎの回帰検証は実際の一時Git履歴で行う。
状態ファイルだけのコミットでは基準ソースを変えず、historyの新しい証拠では
基準ソースを更新し、同じ入力から同じ引き継ぎが再生成されることを確認する。

GitHub Actionsのcheckoutは `fetch-depth: 0` を指定する。
浅い履歴ではsnapshotだけの境界コミットも全ファイル追加に見えるため、
build_handoff.pyは浅い履歴を検出したら生成前に停止する。
この検証は、履歴が完全なテスト用リポジトリだけでなく、本物のdepth=1の
ローカルcloneとunshallow後の回復を含む。生成物だけが増え続ける誤判定を防ぐ。
