# FB022 実ゲームRC82 城内戦・破城・籠城の実装受渡

OWNER 2026-11-15「つぎ」。前回FB021の7職武器/通常攻撃とFB020風走りを保持して城内戦を追加。

## 元と成果ファイル
親: FB021 private Place SHA256 9f4e32400dd6e098e526b59f9d4de38c069b938e1c8795a3b50483b69958278a
新: TRAP_RAIDERS_RC82_FB022_SIEGE_INTERIOR_PLAYTEST.rbxlx / 799478B / SHA256 b84486fe8c4f80e3a7806180b538c9ddab4429f658193ba4fd2d172ebe8b0ca3
配布ZIP: TRAP_RAIDERS_RC82_FB022_SIEGE_INTERIOR_PLAYTEST.zip / 224034B / SHA256 c62b1e7961ad73fb35727f9035a0f199deda69273692faf53e23be89a9c69d14
ZIPには実Studio Placeと再現パッチSOURCE_PATCH.py、RECEIPT.jsonを同梱。PRIVATEユーザー添付で提供、公開repoへPlace/元Game全文は転載しない。

## 実Luau/物理ワールドの差分
- 元82 source中、既存 Owner361CastleBattlefield 1本のみ実変更。他81本 source byte exact。元script gitblob 3599f7a86be2956d2ecf4f14267dfbb73f8f1074、改修後 9e30498bd55ecf46036c6806177e10b98594ccfb。
- 赤青2城の正面を実壁で閉じた上で幅17studの通行できる城門穴と衝突式portcullis。元城壁/庭と3経路/卵/コア/納入台を保持。
- 守備側は内側/外側の近接レバーで門の開閉・修復。敵側は屋外の破城ポイントを3回操作し物理破壊、修理完了まで開放。
- serverのPlayers.Team/ACTIVE phase/生存/実位置13stud/操作CDで全操作を検証。client任意位置やgate HPを信用しない。門閉鎖時CanCollide+CanQueryが有効、開放時は解除。人/Bot Humanoidが閉鎖位置にいる時は圧死防止のため閉鎖を拒否。
- 中庭にアクセスできる城内通路、各城2本の実衝突階段/上段城壁通路、卵保管屋根と側壁。元EGG/score/damage/win authorityは変更なし。
- 追加ランタイムはStudioだけ。round非ACTIVE時は門リセット、1回の操作とTween以外は常時heartbeatなし。

## テストと採用
実Place XML全82源再抽出/改造後再parse、1変更81byte exact、固定親SHA拒否、ZIP内容一致、全7職攻撃・風走り保持、二重Remoteなし等 **36/36 static PASS**。
native Luau compiler / Rojo / Studio(1人と2人) / Android / ART/FUN / OWNER受入 **NOT_RUN**。
正式RC取込0、main/publish/merge/pay0。実ゲーム作者 #366 と品質ライター #470 が源差分受領、#220 auth-writerが同HEAD Rojo/native/source-lock/非force CASで正式RCへ統合後に実機再試遊。元#297 Game/HUD sourceは今スライス無変更。
