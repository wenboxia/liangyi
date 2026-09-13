#!/usr/bin/env python3
"""
从原始运行数据抽出 VoyageGuard 案例的数据（voyageguard-data.json）。

页面是静态的、无框架的（todo.md 的技术约定），所以数据在构建时算好、
内联进 HTML，而不是运行时去读文件——直接双击打开的页面拿不到 fetch。

数据源全部是跑完就不再改的东西：
  trace.jsonl        每步谁在跑、多少字、多少秒、多少钱
  decision-log.md    每个 fix 步逐条的采纳/回退理由
  idea-v0..v5        版本正文，diff 现算
  judging.json       逐版四态矩阵（由判定流程产出，见 RESULT.md 第三节的方法）
"""
from __future__ import annotations

import difflib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RETRO = ROOT / "retrospective" / "voyageguard"
RUN = ROOT / "runs" / "20260908-192138-voyageguard-retro"
ART = RUN / "artifacts" / "round-1"
V0 = ROOT / "runs" / "20260909-081804-voyageguard-v0-baseline" / "artifacts" / "round-1" / "idea-v0.md"

VERSIONS = ["v0", "v1", "v2", "v3", "v4", "v5"]
TRANSITIONS = [("v1", "v2", "2A-fix"), ("v2", "v3", "2B-fix"),
               ("v3", "v4", "2C-rollback"), ("v4", "v5", "2D-fix")]


def vpath(v: str) -> Path:
    return V0 if v == "v0" else ART / f"idea-{v}.md"


def read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


# ---------------------------------------------------------------- seed 与原子点

def load_seed() -> dict:
    t = read(RETRO / "seed.md")
    # 只取正文：头部说明之后、「定稿时的两处明确」之前
    body = t.split("---", 2)[1] if t.count("---") >= 2 else t
    body = body.strip()
    return {"text": body, "chars": len(body), "dense": len(re.sub(r"\s", "", body))}


def load_points() -> list[dict]:
    t = read(RETRO / "atomic-points.md")
    seg = t[t.index("## 二、原子点"):t.index("## 三、判据边界")]
    out = []
    for row in re.findall(r"^\|\s*(P\w+)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*$", seg, re.M):
        out.append({"id": row[0], "text": row[1], "source": row[2]})
    return out


def load_blanks() -> list[dict]:
    t = read(RETRO / "atomic-points.md")
    seg = t[t.index("## 五、原文留白"):]
    out = []
    for m in re.finditer(r"^(\d+)\.\s*\*\*(.+?)\*\*\s*(.*?)(?=\n\n\d+\.\s*\*\*|\Z)",
                         seg, re.M | re.S):
        out.append({"n": int(m.group(1)), "title": m.group(2).strip(),
                    "text": re.sub(r"\s+", " ", m.group(3)).strip()})
    return out


# ---------------------------------------------------------------- 链条

def load_steps() -> list[dict]:
    rows = [json.loads(l) for l in read(RUN / "trace.jsonl").splitlines() if l.strip()]
    steps, decisions = [], []
    for r in rows:
        if r.get("kind") == "step":
            steps.append({
                "id": r["step_id"], "phase": r["phase"], "window": r["window"],
                "model": r["model"].split("/")[-1], "coordinate": r.get("coordinate", ""),
                "role": r.get("role", ""), "inputs": r.get("inputs", []),
                "out": r.get("output_file", ""), "chars": r.get("content_chars", 0),
                "sec": round(r.get("duration_ms", 0) / 1000),
                "cost": round(r.get("cost_usd", 0), 4),
                "think": r.get("reasoning_tokens", 0),
            })
        elif r.get("kind") == "decision":
            decisions.append({
                "step": r["step_id"], "position": r["position"], "mode": r["mode"],
                "triggered": bool(r.get("triggered")),
                "reason": r.get("trigger_reason") or "",
            })
    return steps, decisions


def load_decision_log() -> tuple[list[dict], list[dict]]:
    """每个 fix 步逐条的取舍。两种编号格式都要认。"""
    t = read(RUN / "decision-log.md")
    out, grading = [], []
    for chunk in re.split(r"\n## ", t)[1:]:
        head = chunk.split("\n", 1)[0].strip()
        m = re.match(r"(\S+?)（→ idea-(v\d)\.md）", head)
        if not m:
            continue
        step, ver = m.group(1), m.group(2)
        items = []
        # 格式甲：**N. 标题——判定**\n正文
        for mm in re.finditer(
                r"\*\*(\d+)\.\s*(.+?)——(\S+?)\*\*\s*\n(.*?)(?=\n\n\*\*\d+\.|\Z)",
                chunk, re.S):
            items.append({"n": int(mm.group(1)), "title": mm.group(2).strip(),
                          "verdict": mm.group(3).strip(),
                          "body": re.sub(r"\s+", " ", mm.group(4)).strip()})
        # 格式乙：N. **标题**——判定。正文
        if not items:
            for mm in re.finditer(
                    r"^(\d+)\.\s*\*\*(.+?)\*\*——(\S+?)。(.*?)(?=\n\d+\.\s*\*\*|\Z)",
                    chunk, re.M | re.S):
                items.append({"n": int(mm.group(1)), "title": mm.group(2).strip(),
                              "verdict": mm.group(3).strip(),
                              "body": re.sub(r"\s+", " ", mm.group(4)).strip()})
        note = ""
        nm = re.search(r"不采纳的部分：(.*?)$", chunk, re.S)
        if nm:
            note = re.sub(r"\s+", " ", nm.group(1)).strip()
        out.append({"step": step, "version": ver, "items": items, "not_adopted": note})

    if "分级表" in t:
        seg = t[t.rfind("分级表"):]
        for line in seg.splitlines():
            if not re.match(r"^\s*\|\s*(?:\d{1,3}|[一二三四五六七八九十]{1,3})\s*\|", line):
                continue
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) >= 5:
                grading.append({"n": cells[0], "arg": cells[1],
                                "specificity": cells[2], "severity": cells[3],
                                "label": cells[4]})
    return out, grading


def load_diffs() -> list[dict]:
    out = []
    for a, b, step in TRANSITIONS:
        ta, tb = read(vpath(a)), read(vpath(b))
        sm = difflib.SequenceMatcher(None, ta, tb, autojunk=False)
        added = removed = 0
        for tag, i1, i2, j1, j2 in sm.get_opcodes():
            if tag in ("insert", "replace"):
                added += j2 - j1
            if tag in ("delete", "replace"):
                removed += i2 - i1
        la = [l.strip() for l in ta.splitlines() if l.strip()]
        lb = [l.strip() for l in tb.splitlines() if l.strip()]
        d = difflib.SequenceMatcher(None, la, lb, autojunk=False)
        drop = [la[i] for tag, i1, i2, _, _ in d.get_opcodes()
                if tag in ("delete", "replace") for i in range(i1, i2)]
        gain = [lb[j] for tag, _, _, j1, j2 in d.get_opcodes()
                if tag in ("insert", "replace") for j in range(j1, j2)]
        out.append({
            "from": a, "to": b, "step": step,
            "added": added, "removed": removed,
            "net": len(tb) - len(ta),
            "dropped_headings": [l for l in drop if l.startswith("#")],
            "added_headings": [l for l in gain if l.startswith("#")],
        })
    return out


def load_versions() -> dict:
    out = {}
    for v in VERSIONS:
        t = read(vpath(v))
        out[v] = {"chars": len(t), "dense": len(re.sub(r"\s", "", t)),
                  "headings": [l.strip() for l in t.splitlines() if l.startswith("##")]}
    return out


# ---------------------------------------------------------------- 台账 / 返工 / 别的链

def load_additions() -> list[dict]:
    t = read(RETRO / "additions-ledger.md")
    out = []
    for m in re.finditer(
            r"^([AB]\d+)\s+(.+?)\n原句：(.+?)\n→\s*(.+?)(?=\n\n|\Z)", t, re.M | re.S):
        out.append({"id": m.group(1), "title": m.group(2).strip(),
                    "quote": re.sub(r"\s+", " ", m.group(3)).strip(),
                    "where": re.sub(r"\s+", " ", m.group(4)).strip(),
                    "kind": "留白" if m.group(1).startswith("A") else "真新增"})
    return out


def load_rework() -> list[dict]:
    t = read(RETRO / "SEALED-rework-list.md")
    out = []
    for m in re.finditer(r"^\|\s*(\d+)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*$", t, re.M):
        out.append({"n": int(m.group(1)), "error": m.group(2), "danger": m.group(3)})
    return out


def load_result_md() -> dict:
    """RESULT.md 里已经定稿的两样东西：7 条返工项的命中、第六节的诚实标注。"""
    t = read(RETRO / "RESULT.md")
    hits = []
    seg = t[t.index("## 四、"):t.index("## 五、")]
    for m in re.finditer(r"^\|\s*\*{0,2}(\d+)\*{0,2}\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*$",
                         seg, re.M):
        mark = m.group(3).replace("*", "").strip()
        hits.append({"n": int(m.group(1)), "hit": mark == "✓",
                     "handling": m.group(4).strip()})
    honesty = []
    seg6 = t[t.index("## 六、"):]
    for m in re.finditer(r"^\d+\.\s+(.+?)(?=\n\d+\.\s|\Z)", seg6, re.M | re.S):
        honesty.append(re.sub(r"\s+", " ", m.group(1)).strip())
    return {"rework_hits": hits, "honesty": honesty}


def load_all_runs() -> list[dict]:
    out = []
    for d in sorted((ROOT / "runs").iterdir()):
        rj = d / "run.json"
        if not rj.exists():
            continue
        j = json.loads(read(rj))
        rows = [json.loads(l) for l in read(d / "trace.jsonl").splitlines() if l.strip()] \
            if (d / "trace.jsonl").exists() else []
        st = [r for r in rows if r.get("kind") == "step"]
        if len(st) < 5:          # v0 基线只有一步，不进这张表
            continue
        if not j.get("finished_at"):
            continue             # 还在跑的，跑完再进表
        out.append({
            "name": d.name, "scenario": j.get("scenario_id", ""),
            "mode": j.get("mode") or j.get("hitl") or "",
            "status": j.get("status", ""), "verdict": j.get("verdict"),
            "rounds": j.get("rounds", 1),
            "steps": len(st),
            # 成本从 trace 逐步求和，不用 run.json 的 total_cost_usd ——
            # 续跑过的运行里 finish() 只按本次进程的记录重算，
            # 20260831 那条因此少记了 $0.80（写着 $0.59，实际 $1.39）。
            "cost": round(sum(r.get("cost_usd", 0) for r in st), 3),
            "minutes": round(sum(r.get("duration_ms", 0) for r in st) / 60000),
        })
    return out


def load_validation() -> list[dict]:
    t = read(ROOT / "engine" / "VALIDATION.md")
    out = []
    for m in re.finditer(r"^## (检验[一二三四五六七八九十]+)\s*·\s*(.+?)$", t, re.M):
        title = m.group(2).strip()
        mark = "pass" if "✅" in title else ("fail" if "❌" in title else "open")
        out.append({"no": m.group(1),
                    "title": re.sub(r"[✅❌]|→ 已修|（重要发现）|（重要）", "", title).strip(),
                    "mark": mark,
                    "fixed": "已修" in title})
    return out



# ---------------------------------------------------------------- 五个修改点

# 每个修改点避开了哪条返工项。
#
# 这张映射是**手写的**，不是自动匹配 —— 自动匹配在这里不可靠：返工清单用的是
# 「当年怎么错的」的措辞，台账用的是「方案里新增了什么」的措辞，两边没有共同字面。
# 逐条核对过 RESULT.md 第四节的「v5 的处理」列和 additions-ledger.md 里那条新增
# 首次出现的版本，对上了才写进来：
#   返工 6「阈值查不到官方锚点」 ← A1 三层可信等级体系，首次出现 v2（2A-fix）
#   返工 7「越权断言停航预警」   ← B1 产品自我限定回答范围，首次出现 v5（2D-fix）
#   返工 10「数据缺失静默按安全」← A2 数据缺失分粒度处理，首次出现 v3（2B-fix）
#   返工 11「任何地名都能评估」  ← A10 第一版规则覆盖清单，首次出现 v3（2B-fix）
WINS = {
    "v2": [{"rework": 6, "via": "A1"}],
    "v3": [{"rework": 10, "via": "A2"}, {"rework": 11, "via": "A10"}],
    "v5": [{"rework": 7, "via": "B1"}],
}

# 五个修改点：批判步和它对应的修改步合成一个，它们本来就是一问一答
ACTS = [
    ("P1",           "对抗式方案生成",        "v1", None,   "P1.4"),
    ("2A-fix",       "怀疑论投资人批判",      "v2", "P2A",  "2A-fix"),
    ("2B-fix",       "零上下文单盲复审",      "v3", "P2B",  "2B-fix"),
    ("2C-rollback",  "知情复审 · 方向漂移检测", "v4", "P2C",  "2C-rollback"),
    ("2D-fix",       "拆台专家质疑前提",      "v5", "P2D",  "2D-fix"),
]


def build_acts(steps: list[dict], dlog: list[dict], grading: list[dict],
               judging: dict) -> list[dict]:
    """把 13 步压成 5 个修改点，每个带上「它换来了什么」。"""
    by_id = {s["id"]: s for s in steps}
    log_by_step = {d["step"]: d for d in dlog}
    first = judging.get("first_seen", {})
    matrix = judging.get("matrix", {})
    order = ["v0", "v1", "v2", "v3", "v4", "v5"]

    out = []
    for key, title, ver, critic_id, fix_id in ACTS:
        prev = order[order.index(ver) - 1] if ver != "v1" else None
        changed = []
        if prev and matrix.get(prev) and matrix.get(ver):
            for pid, cur in matrix[ver].items():
                was = matrix[prev].get(pid, {}).get("state")
                if was and was != cur["state"]:
                    changed.append({"point": pid, "from": was, "to": cur["state"]})
        lg = log_by_step.get(fix_id, {})
        # 2D-fix 的 decision-log 只有【判定】和分级表，没有编号条目 ——
        # 它「提了几条」要从分级表数
        proposed = len(grading) if fix_id == "2D-fix" else len(lg.get("items", []))
        # 归一化：模型有时把理由写进判定里（「采纳，通过第3条的代理层日志自然解决…」），
        # 直接当 key 会让同一类判定散成好几种。按前缀归到五档。
        verdicts: dict[str, int] = {}
        for it in lg.get("items", []):
            v = it["verdict"]
            for prefix in ("部分采纳", "部分回退", "不采纳", "采纳", "回退", "保留"):
                if v.startswith(prefix):
                    v = prefix
                    break
            verdicts[v] = verdicts.get(v, 0) + 1
        out.append({
            "key": key, "title": title, "version": ver,
            "critic": by_id.get(critic_id) if critic_id else None,
            "fix": by_id.get(fix_id),
            "contributors": [by_id[i] for i in ("P1A", "P1B") if i in by_id] if key == "P1" else [],
            "proposed": proposed,
            "verdicts": verdicts,
            "not_adopted": lg.get("not_adopted", ""),
            "points_changed": changed,
            "additions": sorted([k for k, v in first.items() if v == ver]),
            "wins": WINS.get(ver, []),
        })
    return out


def main() -> None:
    steps, decisions = load_steps()
    dlog, grading = load_decision_log()
    judging = {}
    jf = RETRO / "judging.json"
    if jf.exists():
        judging = json.loads(read(jf))

    data = {
        "seed": load_seed(),
        "points": load_points(),
        "blanks": load_blanks(),
        "steps": steps,
        "detectors": decisions,
        "decision_log": dlog,
        "grading": grading,
        "versions": load_versions(),
        "diffs": load_diffs(),
        "additions": load_additions(),
        "rework": load_rework(),
        "runs": load_all_runs(),
        "validation": load_validation(),
        "acts": build_acts(steps, dlog, grading, judging),
        "result": load_result_md(),
        "judging": judging,
    }
    here = Path(__file__).parent
    (here / "voyageguard-data.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")

    # 2026-09-13 起只产出数据。原先在这里拼成的 liangyi.html / voyageguard-retro.html
    # 已退役至 archive/retired-2026-09/visualizations/；案例改由 build_case_doc.py 生成 markdown。
    print("写出 voyageguard-data.json")

    for k, v in data.items():
        n = len(v) if isinstance(v, (list, dict)) else 1
        print(f"  {k:<14} {n}")


if __name__ == "__main__":
    main()
