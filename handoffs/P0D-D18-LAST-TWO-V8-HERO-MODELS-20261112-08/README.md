# TRAP RAIDERS — D18 最後のv8看板2体 低ポリ3Dソース

`game_id=TRAP_RAIDERS` ・ `work_id=p0d-siege-v19`

**パケット：** `P0D-D18-LAST-TWO-V8-HERO-MODELS-20261112-08`

既存v8看板12体で、未制作だったオリジナル詳細3Dソースの残り2体を新たに制作した。これまでの10体の3Dソースと合わせ、**v8増補12体の全員に独立した3D生成ソース候補がある**状態となる（Studio実機/ゲーム導入は未実施）。全72看板のうちオリジナル3D試作ソースは12/72=16.67%。全648図鑑の個別文芸改稿78/648=12.04%は変更しない。

## 3Dモデル

- `TRCA-TR-063` **火輪跳ね台**／火輪の熔炉／罠／LEGENDARY。斜めに傾いた開放U字鉄輪・3本脚・小さな鍛冶槌・焼印。近景21パーツ、遠景16可視。
- `TRCA-WE-099` **遊園ホルン**／夢菓子の遊園／武器／LEGENDARY。二重の丸ホルン・頂部に小さな観覧車・三角キャンディの吹口・リボン・最後の乗車券。近景27パーツ、遠景16可視。

独自の原始Partのみ。外部ライセンス素材、アセットID、音声、サーバーRemote、武器・罠・跳躍効果、所有権・報酬・課金は含まない。

## 実ファイル

- `data/characters.json`: 2体の人手制作した形状、色、詳細LOD、4静的姿勢。
- `tools/generate_catalog.py` → `src/ShowcaseCatalog.luau`: 変更検査可能な決定的JSON→Luau生成。
- `src/ShowcaseFactory.luau`: `Build/SetPose/SetLod/GetStatus/Destroy`。表示用親のみ、Anchored、衝突・タッチ・照会OFF、最大12体。
- `src/DisabledDemo.client.luau`: `ENABLED=false`、自動稼働不可。
- `tests/test_showcase.py`: 原データ・API・安全境界・負例・ハッシュ・生成再現性。
- `tools/verify_pack.py`: PUBLIC_SOURCE_V1六キー厳格SHA256/sizeマニフェストの検査。
- `docs/INTEGRATION.md`: PC/Studioで将来受け取る場合の**任意**検証手順。

## ソース検査

```bash
python -m unittest discover -s tests -p 'test_*.py' -v
python tools/generate_catalog.py --check
python tools/verify_pack.py
```

`BUILD_MANIFEST.json` の `files` は本体全ソースとドキュメントのSHA256/UTF8バイト数。ZIPは暗号化せず、同じトップ階層を維持している。ゲーム本体、main、#220のリリース候補、Roblox公開・課金・PC操作には一切触れない。
