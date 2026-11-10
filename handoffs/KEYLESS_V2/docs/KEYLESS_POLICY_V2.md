# P0-A/B/C/D 共通: 鍵の手渡し不要な GitHub 納品規約 v2

## 目的と定義

**個別ZIPごとのAES復号鍵をOWNERに貼らせない・Codexに探させない。** 
`KEYLESS` は人間によるパスワード/秘密鍵の受渡しが不要なことを指す。
暗号方式そのものを排除する意味ではない。PUBLIC GitHubで商用プライベートソースの平文公開は引き続き禁止。

## 受渡し方式（優先順）

1. **PRIVATE_REPO_DIRECT**: OWNERがGitHub PRIVATE repoを用意し、ChatGPT GitHub connectorとWindows Codexの双方にアクセスを付与。毎回そのリポジトリの`handoffs/<packet_id>/<zip>`と `manifest.json` を固定コミットで納品する。**ZIPパスワード・追加AESキー無し**。必ずrepo visibility=`private`を実際に確認してから書込。GitHubのアクセス認証自体は必要。承認・CAS・独立レビュー、main禁止を尊重。現 `kk051780/toy-wars-factory` は PUBLIC のため対象外。
2. **PUBLIC_REPO_RECIPIENT_V2**: PRIVATE repoがまだ無い場合のフォールバック。Windows Codexが**一度だけ自分自身で**受取用X25519 identityを作成し、**公開鍵だけ**Issue #217へ登録する。`owner-identity.local.json`という秘密ファイルはWindowsのユーザープロファイル内に保存し、OWNERもChatGPTも中身を受け渡さない。ChatGPT/他チャットは登録済の公開受取先にZIPをAES-256-GCMで封入してPUBLIC GitHub隔離branchへ送る。Windows Codexはローカルの受取identityで自動的に復号・SHA検査する。**パックごとの秘密鍵入力はゼロ**。受取identityの回復にはWindows上の安全なバックアップが必要。

**絶対に禁止**: PUBLIC GitHubへの平文 `*.luau`, `*.rbxlx`, 未暗号ZIP/キー/Windows owner identity、既存AESの秘密鍵集約ファイル、秘密鍵をURL・Issue・PR・CI・Automationに保存、ZIP SHA未確認の上書き、認証されていない公開鍵への切替。

## Windows初回セットアップ（公開鍵方式）

Windows CodexをOWNERが直接起動した際、公開GitHubから固定コミットの`tools/keyless_handoff_v2.py`を取得し、SHAを照合。PCローカルにPython `cryptography` が必要。

`py tools/keyless_handoff_v2.py enroll --public-out <Windows用のPUBLIC出力ファイル>`

既存のidentityがある場合は**再発行しない**。PC側は生成された公開 `recipient.json` だけGitHub Issue #217に記録（またはOWNERがこの会話に公開JSONを貼る）。ChatGPTが `recipient_key_id` と元のIssue投稿者・source SHAを確認し、公開受取先を固定GitHub commitに登録する。なりすましや勝手な変更を防ぐため、公開鍵を他人が上書きしたら停止してOWNERに確認する。秘密identityは**絶対に共有しない**。

## 送り手（ChatGPT全チャット）

- `#217`の最新・`#218`担当CLAIM・PC SHAを確認し、スコープ衝突を避ける。
- PRIVATE repoが実際に確認できればZIP+sha manifestを直接送る。公開の場合は、OWNERが登録した固定公開鍵を取得し、ローカル原本ZIPとSHA manifestを検証する。
- `python tools/keyless_handoff_v2.py seal --recipient recipient.json --zip YOUR.zip --packet-id YOUR_ID --out YOUR.keyless.json` で暗号化（相手の**公開**鍵だけ使用）。鍵を生成して人へ提示しない。
- GitHub `handoff/` 隔離branchに暗号JSON/公開安全READMEだけ書込み、固定commitから再GETして原本ハッシュ完全一致。Issue #218に `packet_id`, commit, 原ZIP SHA, meta, PC `NOT_TESTED`, Studio `NOT_TESTED` を記録。
- 元の個別AES-GCMパックはGitHubから削除しない（immutableな旧証拠）。移行には**元の平文ZIP**から新封入し直す。元ZIPが別チャットのPC/Libraryにしか無い場合は、その担当チャットが自己の原本を再封入する。**旧AES鍵を回収・集約・公開しない**。

## 受け手（OWNER Windows Codex）

- 自分のidentityは初回以外作り直さない。`restore --in-file PACKET.keyless.json --out private/packet.zip --expected-sha256 原ZIP_SHA --packet-id PACKET_ID`。`--identity`省略ならそのPCのローカル identity を使用。
- 出力は`O_EXCL`（既存ファイル拒否）。ZIPのSHA、CRC、全パス検査の後だけ保存。元PACKET記録とsource/Place SHAに一致することを確認。
- 一つの機能ずつ Luau/Studioで実機検査。Python PASSとGitHub readback PASSは**Studio PASSではない**。
- OWNERが開いたStudioのみ通常終了、PIDの消失・QA・SHAを #213 に記録。

## KEYLESS migrationの状態表示

`SOURCE_LOCAL_VERIFIED` → `PRIVATE_BUNDLE_READY`（手動渡し、公開禁止） → `OWNER_RECIPIENT_REGISTERED`（PUBLIC recipientのみ） → `RESEALED_TO_RECIPIENT` → `GITHUB_REMOTE_READBACK_PASS` → `PC_AUTO_RESTORED_SHA_PASS` → `STUDIO_QA_PASS`。

PRIVATE Repoが使える場合は `PRIVATE_REPO_VERIFIED` → `DIRECT_ZIP_SHA_UPLOAD` → `PRIVATE_REMOTE_READBACK_PASS` → `PC_GIT_DOWNLOAD_SHA_PASS` → `STUDIO_QA_PASS`。

登録がないのに `OWNER_RECIPIENT_REGISTERED` と記録したり、公開repoで未暗号ZIPを送ることは不可。GitHub Issueへのコメント投稿はWindows Codexの自動作業開始ではない。
