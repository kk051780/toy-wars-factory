#!/usr/bin/env python3
"""Historical P0D matrix and current requirements, not a release acceptance score."""
import argparse
import collections
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
WEIGHTS = {"IDEA": 20, "SOURCE": 40, "RC": 70, "STUDIO": 90, "FUN": 100}
LABELS = {"IDEA": "企画", "SOURCE": "独立ソース", "RC": "RCビルド", "STUDIO": "実機済", "FUN": "面白さ合格"}

def summarize(data):
    assert data["schema"] == "P0D_OWNER_PORTFOLIO_V1"
    assert data["progress_scoring"] == WEIGHTS
    rows = data["rows"]
    assert len(rows) >= 40
    assert len({r["id"] for r in rows}) == len(rows)
    for row in rows:
        assert row["stage"] in WEIGHTS, row["id"]
        assert row["release"] in ("S1", "S2+")
        assert row["name"] and row["group"] and row["note"]
        if row["stage"] in ("RC", "STUDIO", "FUN"):
            assert (row.get("rc_evidence") or "").startswith("https://github.com/"), row["id"]
        if row["stage"] in ("STUDIO", "FUN"):
            assert (row.get("studio_evidence") or "").startswith("https://"), row["id"]
        if row["stage"] == "FUN":
            assert row.get("fun_evidence"), row["id"]
    stages = collections.Counter(r["stage"] for r in rows)
    totals = {}
    for target in ("S1", "S2+"):
        group = [r for r in rows if r["release"] == target]
        reached = sum(WEIGHTS[r["stage"]] >= 70 for r in group)
        totals[target] = {"all": len(group), "rc": reached,
                          "rc_pct": round(100 * reached / len(group), 1),
                          "phase_pct": round(sum(WEIGHTS[r["stage"]] for r in group) / len(group), 1)}
    n = len(rows)
    rc = sum(WEIGHTS[r["stage"]] >= 70 for r in rows)
    return {
        "total": n, "rc": rc, "rc_pct": round(100 * rc / n, 1),
        "phase_pct": round(sum(WEIGHTS[r["stage"]] for r in rows) / n, 1),
        "stage_counts": {k: stages[k] for k in WEIGHTS},
        "targets": totals, "official_s1_last_reported": data["official_s1_previous_score"],
        "studio_rich51": "NOT_TESTED", "owner_fun": "NOT_TESTED",
        "historical_snapshot": {
            "as_of_jst": data["as_of_jst"],
            "verified_rc_head": data["verified_rc_head"],
            "scope": "既存の集計値はこの履歴snapshotに限る。現在のRC・Studio・FUNの合否を示さない。"
        },
        "current_release_requirements": data.get("current_release_requirements")
    }

def requirement_lines(layer):
    out = ["", "## 現在のリリース必須要件", ""]
    if layer is None:
        return out + ["現在の必須要件を示す追加層はありません。履歴stageから要件や合否を推定しません。"]
    out += [
        f"OWNER指定日: {layer['owner_effective_as_of_jst']}。必須指定と受入合格は別です。",
        layer["scope_note"],
        layer["display_names_note"],
        "",
        "|企画ID|対象／観測表示名|内部ID|発売要件|今回の受入評価|",
        "|---|---|---|---|---|",
    ]
    status = layer["acceptance_assessment"]["status"]
    assessment = "未評価" if status == "NOT_EVALUATED" else status
    for row in layer["requirements"]:
        name = row.get("observed_player_display_name") or row["name"]
        role_id = row.get("internal_role_id", "—")
        required = "必須" if row["release_must_pass"] is True else "必須指定なし"
        out.append(f"|{row['feature_id']}|{name}|{role_id}|{required}|{assessment}|")
    out.append("")
    for row in layer["requirements"]:
        if row.get("required_player_display_name"):
            out.append(f"表示名要件: {row['internal_role_id']} → {row['required_player_display_name']}。内部IDを維持。")
    out += ["", layer["acceptance_assessment"]["note"], "", "根拠:", ""]
    for source_id, source in layer["sources"].items():
        out.append(f"- [{source['label']}]({source['url']})（{source_id}）")
    return out

def report(data, summary):
    out = [
        "# P0D｜企画の履歴snapshotと現在のリリース必須要件",
        "",
        "企画の工程到達率と公式ゲーム完成率は別です。RCはGitHubでStudio用ファイルを生成した状態で、実機動作の確認ではありません。",
        "",
        f"## 履歴snapshot（as_of_jst: {data['as_of_jst']}）",
        "",
        f"**履歴の企画 {summary['total']} 件 / 当時RC段階 {summary['rc']} 件 / 当時RC段階率 {summary['rc_pct']}% / 当時工程平均 {summary['phase_pct']}%**",
        f"記録対象RC HEAD: `{data['verified_rc_head']}`。",
        f"記録上の公式S1前回監査 {summary['official_s1_last_reported']} / 100（この表では更新しない）。",
        "履歴の数値・未検証の記録から、現在のRC搭載・Studio2client・Android・人間FUNの合否は判断できません。",
        "",
        "工程%は企画20、独立ソース40、RCビルド70、実機試験90、面白さ評価合格100という便宜的指標で、工数見積ではありません。",
    ]
    out += requirement_lines(summary["current_release_requirements"])
    out += [
        "",
        f"## 履歴行（as_of_jst: {data['as_of_jst']}）",
        "",
        "|分類|当時の企画案|当時の状態|工程%|当時の記録|",
        "|---|---|---|---:|---|",
    ]
    for row in data["rows"]:
        source = (" [根拠](" + row["evidence"] + ")") if row.get("evidence") else ""
        note = row["note"].replace("|", "／")
        out.append("|" + "|".join([row["group"], row["name"], LABELS[row["stage"]],
                                  str(WEIGHTS[row["stage"]]), note + source]) + "|")
    out += ["", f"## 履歴snapshotの対象別集計（as_of_jst: {data['as_of_jst']}）", "",
            "|当時の区分|企画件数|当時RC段階|当時RC段階率|当時工程平均|",
            "|---|---:|---:|---:|---:|"]
    for target, v in summary["targets"].items():
        out.append(f"|{target}|{v['all']}|{v['rc']}|{v['rc_pct']}%|{v['phase_pct']}%|")
    out += ["", "履歴の行名・stage・release・証拠・集計値は保存しています。必須要件の追加で履歴のRC件数や受入評価は増えません。",
            "現在のRC採用や実機・FUN・OWNER受入は、それぞれ対象を固定した別の証拠で判定します。"]
    return "\n".join(out) + "\n"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path)
    ap.add_argument("--json", type=Path)
    args = ap.parse_args()
    data = json.loads((HERE / "FEATURE_CATALOG.json").read_text(encoding="utf-8"))
    stats = summarize(data)
    md = report(data, stats)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(md, encoding="utf-8")
    else:
        print(md)
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(stats, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("P0D_FEATURE_CATALOG_PASS", stats["total"], stats["rc"], stats["rc_pct"])

if __name__ == "__main__":
    main()
