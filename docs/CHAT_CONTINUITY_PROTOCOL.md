# TOY WARS FACTORY — チャット間継続規約

唯一の正本は private GitHub repository kk051780/toy-wars-factory の main ブランチ。

新しいチャットでは、GitHub連携で status/CHAT_HANDOFF.md と status/LATEST_STATE.json を読み、PROJECT_STATE.json、AGENTS.md、quality_policy.jsonも照合する。その後、最新Actions、main、PR、Issuesを直接確認し、未完了の続きから開発する。

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
