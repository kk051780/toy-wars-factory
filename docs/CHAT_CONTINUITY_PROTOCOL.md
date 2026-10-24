# TOY WARS FACTORY — チャット間継続規約

唯一の正本は private GitHub repository kk051780/toy-wars-factory の main ブランチ。

新しいチャットでは、GitHub連携で status/CHAT_HANDOFF.md と status/LATEST_STATE.json を読み、PROJECT_STATE.json、AGENTS.md、quality_policy.jsonも照合する。その後、最新Actions、main、PR、Issuesを直接確認し、未完了の続きから開発する。

同じChatGPTプロジェクト内の新しいチャットで「TOY WARS再開」の一言を送れば、AIは上記の状態取得から始める。古いチャットの記憶や添付よりGitHubの現物を優先する。

tools/build_handoff.py はコードサイズとキャラクターと進捗を入力に、引き継ぎを自動生成する。更新がない場合は架空の進捗コミットを追加しない。ゲーム開発と自律開発システム改善の二重ループを管理し、テストと実測証拠を残す。

ただし、まったく新しいチャットがユーザーの発言なしに自動開始され、GitHubを自動で読み込むことまでは製品仕様として保証できない。定期タスクおよびGitHub Actionsはチャットと独立して作動する。作業にはAIランナーと認証が別途必要。

公開、課金、権限拡大、品質基準緩和は所有者承認。スマホだけで操作できる方式を優先し、PC上の手動デバッグは求めない。
