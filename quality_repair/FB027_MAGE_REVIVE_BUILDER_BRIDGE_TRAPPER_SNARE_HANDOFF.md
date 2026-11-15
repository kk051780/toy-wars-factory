# FB027｜実RC82：魔法使いの蘇生・建築士の橋・トラッパーの実罠

2026-11-15 OWNER「つぎ」。これまでのGame品質ゲートprivate累積スライスFB020〜026の**実ファイルを親**にした実Lua改修。単なる企画書ではなくユーザーへStudio用 `.rbxlx` とソース再生パッチを私的納品済。

## 受渡し・実体
- 親：`TRAP_RAIDERS_RC82_FB026_SEVEN_ROLE_SKILLS_PLAYTEST.rbxlx` SHA256 `df162246344f69a614763bf9eecfcad78340c3bee04a023c3c111e9810ccd318`。
- **新Place**：`TRAP_RAIDERS_RC82_FB027_TEAMPLAY_PLAYTEST.rbxlx` 865446B / SHA256 `5987a2e0d59ddc703975c10c3e017ed62faf25d9b0d62131da0430bb550aace6`。
- **OWNER配布ZIP**：`TRAP_RAIDERS_RC82_FB027_TEAMPLAY_PLAYTEST.zip` 242507B / SHA256 `58ce7dbccd3082e848125be676eb677beeccb3c82f78cb50af5feda3ce92d338`。
- ZIPに実Place・`SOURCE_PATCH.py`（実Game/HUD差分を元Placeへ再生）・固定SHA `RECEIPT.json`・操作案内。
- **全82個のLuau SourceをXMLから再抽出**。Game `5ed828ce4e3dc5d080165d17830d57b24aa19c9a`→`5f7f72b9f9d41c9d986c3e11bbb35eaab57a5994`、HUD `79c5c12f1f36e755926f6b9c7b4f7dd605d4d351`→`f38d3270c285666544e7e94afafceaa52eb8ef24`。他80 source byte-exact。
- 既存7職専用武器/Horde実HIT/風走り/城門破壊と城内区画/拾得8基・飛行/物理ロビー/魔獣AI/7職Q+X技能は全て原文維持。

## 実Luau Server動作の追加（Studio専用の私的候補）
1. **魔法使いX：既存範囲回復に蘇生を合体**。真正のHumanoid.Died時だけServerが15秒・一度きり・元ラウンドTEAM限定で死亡地点の小さなBeaconを記録。魔法使いが22stud以内でXするとServerが最も近い**同TEAMの最近死亡者**を選ぶ。まだ死亡中ならPlayer:LoadCharacter、既に自動respawn済みなら戦場へ即復帰。実Humanoid HP>=55%と2.5秒既存invulnを付与。自動respawnのため「一度死亡した人を強制的にDowned60秒固定」とは宣言しない。対象のいない時は旧Xの38HPチーム回復。
2. **建築士C：実際に歩ける27studの木橋**。自分と前方終点のServer Raycastによる安全床/高低差/ワールド範囲検査、team objective近接禁止、キャラクター埋込拒否。28秒で消え、1人1本。木床、左右欄干、歩いて乗り込む2スロープはCanCollide=true。従来Xの壁設置はそのまま。
3. **トラッパーC：22秒の敵用設置罠**。本物の床からServer設置、1人最大2個、13秒CD、敵に命中すると**既存TrapRules slow/元Game slowed管理**で減速しHumanoid:TakeDamage(6)を一回。Guardian既存罠を変更せず、同じGame `tickTraps` に`fb027` variantを追加。仲間への効果なし、卵納入口付近へ設置禁止。既存Xワープは保持。
4. 新しいRemote/Heartbeat/score/egg/HP authorityは作らず、既存唯一Game Remoteに`JOB_WORLD_SKILL`を追加。Job/Team/ACTIVE/ACK/生存/非卵運搬/非拘束/Server-seq/CD/復帰/退出/epoch cleanupを検査。HUDはX=既存固有補助、C=建築士橋/罠師罠。タッチは右下の小型ボタン（他職は非表示）。

## QAの証拠と残作業
- 原Parent実Place固定、全82源/80byte exact/2源の元SHAと修正SHA、パッチ再現、ZIP照合・CRC、Authority二重化無し、Job/phase/team/epoch、携帯ボタン、既存コンテンツ保持など**72/72 independent static tests PASS**（手元 `verify_fb027_teamplay.py`）。
- **Native Luau compiler/Rojo/Roblox Studio1・2client/Android/実蘇生・実橋横断・実罠発火/OWNER楽しさは NOT_RUN**。合格ではなく**PRIVATE_SOURCE_PATCH_STATIC_PASS**。正式RC採用0、OWNER受入0。
- 既存作者 #297 Game/HUD、#366 城/ #376 ロビーとのコンフリクトを避け最新公式同HEADへ**選択的差分**を統合する。正式RC書込みは #220 のauth/CAS + 同HEAD native/Rojoのみ。#470品質ゲートが実機で再調整完走。YELLOWは負債記録で非公開開発RCを進め、REDは停止。main直接/無断merge/公開/追加課金は禁止。

**次の判断はソース件数でなくStudioで「蘇生→橋→罠→卵強奪を同一試合で操作できるか」**。実機で不足ならFB027再OPENし修正。
