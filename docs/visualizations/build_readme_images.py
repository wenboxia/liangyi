#!/usr/bin/env python3
"""
README 用图：横幅、架构总览、回溯对照两张图（中英各一份）。

数字一律从仓库数据读，不手抄：
  - 7 处返工三方对照：voyageguard-data.json 的 result.rework_hits（两仪）
    与 retrospective/voyageguard/judging.json 的 v0_rework（单模型基线）
  - 14 条原子点逐版四态：judging.json 的 counts
  - 模型与坐标：engine/config.py 的 PROFILES / MODELS / WINDOWS

渲染：先写 HTML，再用系统 Chrome headless 截图（@2x）。不引任何依赖。
    python3 docs/visualizations/build_readme_images.py
输出：docs/images/*.png
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from engine.config import MODELS, PROFILES, WINDOWS  # noqa: E402

OUT = ROOT / "docs/images"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

DATA = json.loads((ROOT / "docs/visualizations/voyageguard-data.json").read_text(encoding="utf-8"))
JUDGE = json.loads((ROOT / "retrospective/voyageguard/judging.json").read_text(encoding="utf-8"))

assert len(WINDOWS) == 7, "角色数变了，横幅与架构图要跟着改"


def model(profile: str, slot: str) -> tuple[str, str]:
    m = MODELS[PROFILES[profile][slot]]
    return PROFILES[profile][slot], m.coordinate


BASE_CSS = """
*{box-sizing:border-box;margin:0;padding:0}
html,body{background:#FAF9F5;color:#141413}
body{font-family:-apple-system,"PingFang SC","Helvetica Neue",Arial,sans-serif;-webkit-font-smoothing:antialiased;overflow:hidden}
.serif{font-family:Georgia,"Songti SC","Noto Serif SC",serif}
.muted{color:#87867F}
.mono{font-family:"SF Mono",Menlo,monospace}
"""


def render(name: str, html: str, w: int, h: int) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / f"{name}.html"
        src.write_text(f"<!doctype html><meta charset=utf-8><style>{BASE_CSS}body{{width:{w}px;height:{h}px}}</style>{html}",
                       encoding="utf-8")
        subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                        "--force-device-scale-factor=2", f"--window-size={w},{h}",
                        f"--screenshot={OUT / (name + '.png')}", src.as_uri()],
                       check=True, capture_output=True)
    print("wrote", OUT / f"{name}.png")


# ---------------------------------------------------------------- 横幅

TAIJI = """<svg viewBox="0 0 100 100" width="{s}" height="{s}"><circle cx="50" cy="50" r="48" fill="#FAF9F5" stroke="#141413" stroke-width="3"/>
<path d="M50 2 A48 48 0 0 1 50 98 A24 24 0 0 1 50 50 A24 24 0 0 0 50 2Z" fill="#141413"/>
<circle cx="50" cy="26" r="7" fill="#141413"/><circle cx="50" cy="74" r="7" fill="#FAF9F5"/></svg>"""


def banner() -> None:
    tiles = [("13", "步确定性编排"), ("4", "轮独立批判"), ("7", "个角色 Agent · 3 家厂商"), ("2", "个 HITL 必停点")]
    t = "".join(f'<div class="tile"><b>{n}</b><span>{escape(s)}</span></div>' for n, s in tiles)
    html = f"""<style>
.wrap{{height:100%;padding:56px 72px;display:flex;align-items:center;gap:64px;border-bottom:1px solid rgba(20,20,19,.1)}}
.l{{flex:1;display:flex;gap:36px;align-items:center}}
h1{{font-size:64px;font-weight:700;letter-spacing:-.01em;line-height:1.1}}
h2{{font-size:34px;font-weight:600;margin-top:12px}}
.en{{font-size:20px;margin-top:10px}}
.tag{{font-size:21px;margin-top:22px;color:#5E5D59}}
.tiles{{display:grid;grid-template-columns:1fr 1fr;gap:14px;width:520px}}
.tile{{background:#F0EEE6;border-radius:12px;padding:18px 20px;display:flex;flex-direction:column;gap:4px}}
.tile b{{font-size:40px;line-height:1;color:#D97757}}
.tile span{{font-size:18px;color:#3D3D3A}}
</style>
<div class="wrap"><div class="l">{TAIJI.format(s=150)}<div>
<h1>两仪 Liangyi</h1>
<h2>跨厂商多 Agent 产品想法优化工作流</h2>
<div class="en muted">Cross-vendor multi-agent workflow for refining product ideas</div>
<div class="tag serif">一个想法进去 → 对抗生成 → 四轮独立批判 → 拆台分级 → 交付或推翻</div>
</div></div><div class="tiles">{t}</div></div>"""
    render("banner", html, 1600, 380)


# ---------------------------------------------------------------- 架构总览

ARCH = {
    "zh": {
        "c1": "① 对抗式方案生成 · P0–P1", "c2": "② 四轮独立批判 · P2", "c3": "③ 分级判定与路由",
        "seed": "原始想法",
        "p0": ("P0 忠实精炼", "不扩写，只重述"),
        "p10": ("P1.0 生成两个对立角色", "假对立检测：构造不出相反答案就重生成"),
        "p1a": ("P1A 专家 A", "独立出方案"), "p1b": ("P1B 专家 B", "看不到 A"),
        "p14": ("P1.4 执笔融合", "→ v1"),
        "crit": [("P2A 投资人批判", "新窗口，攻逻辑与商业", "2A-fix → v2", ""),
                 ("P2B 单盲复审", "零上下文，只收方案正文", "2B-fix → v3", ""),
                 ("P2C 知情复审", "对照 v1 / v3 查方向漂移", "2C-rollback → v4", "HITL ①"),
                 ("P2D 前提拆台", "只攻前提假设", "2D-fix → v5 · 论据分级", "HITL ②")],
        "note2": "每轮批判开新窗口；所有修改由同一个执笔窗口完成",
        "router": "致命论据 = 打前提（K 级）× 具体性高（H 级）",
        "exits": [("回 P1 · 整链重跑", "致命论据 ≥ 2，第 1 轮"),
                  ("回 P2 · 重跑批判", "打前提的论据占比 ≥ 60%，第 1 轮；上轮 v5 作新 v1"),
                  ("结束 · 产出 v5", "其余情况；第 2 轮兜底强制产出")],
        "cap": "路由规则写在 route()，多轮驱动写在 run_chain()（两轮封顶、开第 2 轮前花费 ≥ $3 则停）。出口判定与开新一轮的零件已用真实判定书离线驱动，run_chain() 本身与预算闸未经测试。命令行与网页入口只跑一轮：执笔者的【判定】决定交付 v5 还是停在判定书",
        "legend_h": "7 个角色 Agent 按职责固定分属三个槽位；各槽位按底模坐标（冲突偏向 A × 语料文化 B）跨厂商选模型",
        "slots": [("anchor", "专家 A · 执笔 · 投资人 · 知情复审"),
                  ("divergent_a", "专家 B · 拆台（必须 A3 任务优先）"),
                  ("divergent_b", "单盲复审（零上下文）")],
        "prod": "正式档", "demo": "演示档",
        "rules": "开跑前 3 条硬规则，违反即拒跑：维度 A 必须可判定 · P2 四个批判窗口至少两个不同坐标 · 拆台必须 A3",
        "hitl": "HITL 必停点：auto 档由执笔按规则自判通过；hitl 档停下由人判——2C 判「这还是我想要的吗」，2D 判「拆台打中的是前提，还是框架内能消化」",
    },
    "en": {
        "c1": "① Adversarial drafting · P0–P1", "c2": "② Four independent critiques · P2", "c3": "③ Grade and route",
        "seed": "Raw idea",
        "p0": ("P0 faithful restatement", "restate, don't expand"),
        "p10": ("P1.0 two opposing roles", "fake-opposition check: regenerate if no conflicting answer"),
        "p1a": ("P1A Expert A", "drafts alone"), "p1b": ("P1B Expert B", "cannot see A"),
        "p14": ("P1.4 scribe merges", "→ v1"),
        "crit": [("P2A investor critique", "fresh window: logic & business", "2A-fix → v2", ""),
                 ("P2B blind review", "zero context, sees only the text", "2B-fix → v3", ""),
                 ("P2C informed review", "v1 vs v3: direction drift", "2C-rollback → v4", "HITL ①"),
                 ("P2D premise teardown", "attacks assumptions only", "2D-fix → v5 · grading", "HITL ②")],
        "note2": "Every critique opens a new window; every revision is made by the same scribe window",
        "router": "Kill shot = hits a premise (K) × highly specific (H)",
        "exits": [("Back to P1 · full rerun", "≥ 2 kill shots, round 1"),
                  ("Back to P2 · rerun critiques", "≥ 60% premise-level arguments, round 1; old v5 becomes v1"),
                  ("Done · ship v5", "otherwise; round 2 is forced to ship")],
        "cap": "Routing rule in route(); multi-round driver in run_chain() (2-round cap, no round 2 once spend ≥ $3). The exit decision and round-switching parts were driven offline with real judgments; run_chain() itself and the budget check are untested. The CLI and web entry run one round: the scribe's verdict ships v5 or stops at a judgment file",
        "legend_h": "7 role agents fixed to three slots by role; each slot's model is chosen across vendors by base-model coordinate (conflict bias A × corpus culture B)",
        "slots": [("anchor", "Expert A · scribe · investor · informed reviewer"),
                  ("divergent_a", "Expert B · teardown (must be A3 task-first)"),
                  ("divergent_b", "Blind reviewer (zero context)")],
        "prod": "primary", "demo": "demo",
        "rules": "3 hard rules checked before a run, else it refuses: dimension A must be known · the 4 P2 critics span ≥ 2 distinct coordinates · teardown must be A3",
        "hitl": "HITL stops: in auto the scribe decides by rule; in hitl it pauses for a person — at 2C \"is this still what I wanted?\", at 2D \"do the attacks hit the premise, or can the framework absorb them?\"",
    },
}
SLOT_CLS = {"anchor": "a", "divergent_a": "b", "divergent_b": "c"}


def architecture(lang: str) -> None:
    T = ARCH[lang]

    def node(title: str, sub: str, cls: str, extra: str = "") -> str:
        return f'<div class="n {cls}"><b>{escape(title)}</b><small>{escape(sub)}</small>{extra}</div>'

    col1 = (f'<div class="seed">{escape(T["seed"])}</div><i>↓</i>'
            + node(*T["p0"], "a") + "<i>↓</i>" + node(*T["p10"], "a") + "<i>↓</i>"
            + f'<div class="pair">{node(*T["p1a"], "a")}{node(*T["p1b"], "b")}</div><i>↓</i>'
            + node(*T["p14"], "a"))
    crit_cls = ["a", "c", "a", "b"]
    rows = []
    for (ct, cs, fx, h), cc in zip(T["crit"], crit_cls):
        hit = f'<span class="h">★ {h}</span>' if h else ""
        rows.append(f'<div class="row">{node(ct, cs, cc)}<i>→</i><div class="n a fix{" hx" if h else ""}"><b>{escape(fx)}</b>{hit}</div></div>')
    col2 = "".join(rows) + f'<p class="note muted">{escape(T["note2"])}</p>'
    ex_cls = ["x1", "x2", "x3"]
    col3 = (f'<div class="router">{escape(T["router"])}</div>'
            + "".join(f'<div class="ex {c}"><b>{escape(t)}</b><small>{escape(s)}</small></div>' for (t, s), c in zip(T["exits"], ex_cls))
            + f'<p class="note muted">{escape(T["cap"])}</p>')
    leg = []
    for slot, roles in T["slots"]:
        pm, pc = model("primary", slot)
        dm, dc = model("demo", slot)
        leg.append(f'<div class="lg {SLOT_CLS[slot]}"><div class="sw"></div><div><b class="mono">{slot}</b>'
                   f'<div>{escape(roles)}</div><small class="muted">{T["prod"]} {pm} · {pc}　{T["demo"]} {dm} · {dc}</small></div></div>')
    html = f"""<style>
.wrap{{padding:36px 40px}}
.cols{{display:grid;grid-template-columns:1fr 1.45fr 1fr;gap:28px}}
.col{{background:#fff;border:1px solid rgba(20,20,19,.1);border-radius:16px;padding:22px 22px 18px;display:flex;flex-direction:column;align-items:stretch}}
h3{{font-size:19px;font-weight:700;margin-bottom:14px}}
i{{font-style:normal;color:#B0AEA5;text-align:center;font-size:18px;line-height:22px}}
.n{{border-radius:10px;padding:9px 12px;border:1.5px solid;display:flex;flex-direction:column;gap:2px;position:relative}}
.n b{{font-size:16px}} .n small{{font-size:13px;color:#5E5D59;line-height:1.35}}
.a{{background:#F0EEE6;border-color:#B0AEA5}} .b{{background:#E4ECF2;border-color:#8FA3B3}} .c{{background:#E8F0E6;border-color:#8FB08F}}
.seed{{align-self:center;border-radius:999px;padding:7px 18px;background:#141413;color:#FAF9F5;font-size:15px}}
.pair{{display:grid;grid-template-columns:1fr 1fr;gap:10px}}
.row{{display:grid;grid-template-columns:1.25fr 22px 1fr;align-items:center;margin-bottom:12px}}
.row i{{line-height:1}}
.fix{{justify-content:center;min-height:62px}}
.hx{{background:#FBEFE9;border-color:#D97757;border-width:2px}}
.h{{font-size:13px;font-weight:700;color:#C6613F}}
.note{{font-size:13px;margin-top:auto;padding-top:10px;line-height:1.4}}
.router{{background:#FFF4D6;border:1.5px solid #C9A227;border-radius:10px;padding:12px;font-size:15px;font-weight:600;margin-bottom:14px;line-height:1.4}}
.ex{{border-radius:10px;padding:10px 12px;margin-bottom:10px;border:1.5px solid;display:flex;flex-direction:column;gap:3px}}
.ex b{{font-size:16px}} .ex small{{font-size:13px;color:#3D3D3A}}
.x1{{background:#F8DADA;border-color:#B04141}} .x2{{background:#DCEEF3;border-color:#3E7A8C}} .x3{{background:#141413;border-color:#141413;color:#FAF9F5}} .x3 small{{color:#D8D6CE}}
.leg{{margin-top:22px;background:#fff;border:1px solid rgba(20,20,19,.1);border-radius:16px;padding:18px 22px}}
.leg h4{{font-size:15px;font-weight:600;margin-bottom:12px}}
.lgs{{display:grid;grid-template-columns:repeat(3,1fr);gap:18px}}
.lg{{display:flex;gap:10px;align-items:flex-start;background:none;border:none;font-size:14px;line-height:1.45}}
.lg .sw{{width:18px;height:18px;border-radius:5px;border:1.5px solid;flex:none;margin-top:2px}}
.lg.a .sw{{background:#F0EEE6;border-color:#B0AEA5}} .lg.b .sw{{background:#E4ECF2;border-color:#8FA3B3}} .lg.c .sw{{background:#E8F0E6;border-color:#8FB08F}}
.lg small{{font-size:12.5px}}
.foot{{margin-top:14px;display:flex;flex-direction:column;gap:6px;font-size:13.5px;color:#3D3D3A}}
.foot span b{{color:#C6613F}}
</style>
<div class="wrap"><div class="cols">
<div class="col"><h3>{escape(T["c1"])}</h3>{col1}</div>
<div class="col"><h3>{escape(T["c2"])}</h3>{col2}</div>
<div class="col"><h3>{escape(T["c3"])}</h3>{col3}</div>
</div>
<div class="leg"><h4>{escape(T["legend_h"])}</h4><div class="lgs">{"".join(leg)}</div>
<div class="foot"><span>{escape(T["rules"])}</span><span><b>★</b> {escape(T["hitl"])}</span></div></div>
</div>"""
    render("architecture" if lang == "zh" else "architecture.en", html, 1600, 740 if lang == "zh" else 800)


# ---------------------------------------------------------------- 回溯对照：7 处返工

REWORK_LABEL = {
    "zh": {5: "跨海客滚船风速红线比真实标准宽松，且无出处", 6: "浪高「中风险」区间查不到官方锚点",
           7: "「停航预警」这类超出工具资格的断言措辞", 9: "以为评测把工具全 mock 掉就够了",
           10: "数据缺失时静默按「安全」处理", 11: "以为任何地名都能评估",
           12: "PRD 阈值：方向错、无来源、措辞夸大"},
    "en": {5: "Ferry wind red line looser than the real standard, unsourced", 6: "\"Medium risk\" wave band with no official anchor",
           7: "Assertions like \"sailing suspended\" beyond the tool's remit", 9: "Assuming evals could mock every tool",
           10: "Treating missing data as \"safe\" silently", 11: "Assuming any place name can be assessed",
           12: "PRD thresholds: wrong direction, unsourced, overstated"},
}
REWORK_TXT = {
    "zh": {"title": "VoyageGuard 返工清单里源自原始 PRD 的 7 条，谁提前避开了", "sub": "同一段原始想法：项目初期的 PRD、只调用一次模型、走完两仪 13 步（返工清单共 21 条，其余 14 条开工后才暴露，链条看不到）",
           "cols": ["项目初期 PRD", "单模型一次调用", "两仪全自动 13 步"], "yes": "避开", "no": "踩了",
           "src": "数据：docs/case-voyageguard.md。第一列按定义全踩：这 7 条就是当年 PRD 实际犯下、后来返工的错。两仪一列经初判与独立复判（均为 Claude，复判把 5/7 改为 4/7），单模型一列只判一次；一个项目、一次运行，未做跨厂商复核。"},
    "en": {"title": "The 7 VoyageGuard rework items from the original PRD — who avoided them in advance", "sub": "Same raw idea: the original PRD, one single-model call, and Liangyi's 13 steps (21 rework items in total; the other 14 surfaced during build and are out of the chain's sight)",
           "cols": ["Original PRD", "Single model, one call", "Liangyi, 13 steps (auto)"], "yes": "avoided", "no": "not avoided",
           "src": "Source: docs/case-voyageguard.md. Column 1 is 0/7 by definition: these 7 are the PRD's own mistakes, reworked later. The Liangyi column was judged and independently re-judged (both Claude; re-judging cut 5/7 to 4/7); the single-model column was judged once. One project, one run, no cross-vendor review."},
}


def rework(lang: str) -> None:
    T, L = REWORK_TXT[lang], REWORK_LABEL[lang]
    ly = {r["n"]: r["hit"] for r in DATA["result"]["rework_hits"]}
    v0 = {r["item"]: r["hit"] for r in JUDGE["v0_rework"]}
    items = [r["n"] for r in DATA["rework"]]
    assert set(items) == set(ly) == set(v0) and len(items) == 7
    cols = [{n: False for n in items}, v0, ly]           # 纯人：7 条都是当年真实犯下的错
    tot = [sum(c.values()) for c in cols]
    head = "".join(f'<th><span class="big">{t} / 7</span><span class="ch">{escape(c)}</span></th>' for t, c in zip(tot, T["cols"]))
    body = ""
    yes = '<td><span class="y">● ' + T["yes"] + "</span></td>"
    no = '<td><span class="no">○ ' + T["no"] + "</span></td>"
    for n in items:
        cells = "".join(yes if c[n] else no for c in cols)
        body += f'<tr><th class="it"><span class="num">#{n}</span>{escape(L[n])}</th>{cells}</tr>'
    html = f"""<style>
.wrap{{padding:34px 40px}}
h3{{font-size:25px;font-weight:700}} .sub{{font-size:16px;margin:6px 0 20px}}
table{{width:100%;border-collapse:separate;border-spacing:0;background:#fff;border:1px solid rgba(20,20,19,.1);border-radius:14px;overflow:hidden}}
th,td{{padding:11px 16px;text-align:center;border-bottom:1px solid rgba(20,20,19,.07);font-size:15px}}
thead th{{background:#F0EEE6;vertical-align:bottom;padding:16px}}
thead th:first-child{{width:46%}}
.big{{display:block;font-size:30px;font-weight:700;line-height:1.1}}
thead th:last-child .big{{color:#C6613F}}
.ch{{display:block;font-size:14px;color:#5E5D59;margin-top:4px;font-weight:500}}
.it{{text-align:left;font-weight:400}} .num{{display:inline-block;width:40px;color:#87867F;font-family:"SF Mono",Menlo,monospace;font-size:13px}}
.y{{color:#C6613F;font-weight:700}} .no{{color:#9C9A92}}
tbody tr:last-child th,tbody tr:last-child td{{border-bottom:none}}
td:last-child{{background:#FDF6F2}}
.src{{font-size:13px;margin-top:12px}}
</style><div class="wrap"><h3>{escape(T["title"])}</h3><p class="sub muted">{escape(T["sub"])}</p>
<table><thead><tr><th></th>{head}</tr></thead><tbody>{body}</tbody></table><p class="src muted">{escape(T["src"])}</p></div>"""
    render("retro-rework" if lang == "zh" else "retro-rework.en", html, 1400, 590)


# ---------------------------------------------------------------- 回溯对照：14 条原子点

ATOM_TXT = {
    "zh": {"title": "原始想法拆成 14 条原子点，每一版还剩多少", "sub": "流程会改动原始想法的主张：拆台后 8 条守住、4 条收窄或变形、2 条未守住",
           "rows": {"v0": "v0 · 单模型一次调用（基线）", "v1": "v1 · 两位专家融合后", "v2": "v2 · 投资人批判后",
                    "v3": "v3 · 单盲复审后", "v4": "v4 · 漂移回退后", "v5": "v5 · 前提拆台后"},
           "keys": {"守住": "守住", "收窄变形": "收窄或变形", "未守住": "未守住（被推翻）"},
           "src": "数据：retrospective/voyageguard/judging.json 逐版矩阵（v5 与封存判定 13/14 一致，差 P12 一条）。"},
    "en": {"title": "The raw idea split into 14 atomic points — how many survive each version", "sub": "The chain does change the idea's claims: after teardown 8 upheld, 4 narrowed or altered, 2 overturned",
           "rows": {"v0": "v0 · single model, one call (baseline)", "v1": "v1 · after merging two experts", "v2": "v2 · after investor critique",
                    "v3": "v3 · after blind review", "v4": "v4 · after drift rollback", "v5": "v5 · after premise teardown"},
           "keys": {"守住": "upheld", "收窄变形": "narrowed or altered", "未守住": "overturned"},
           "src": "Source: retrospective/voyageguard/judging.json (v5 matches the sealed verdict on 13/14 points; P12 differs)."},
}
ATOM_COLOR = {"守住": "#2a78d6", "收窄变形": "#eda100", "未守住": "#e34948"}   # 已过 dataviz 调色校验（light）


def atoms(lang: str) -> None:
    T = ATOM_TXT[lang]
    counts = JUDGE["counts"]
    total = len(JUDGE["matrix"]["v5"])
    assert total == 14
    legend = "".join(f'<span><i style="background:{ATOM_COLOR[k]}"></i>{escape(v)}</span>' for k, v in T["keys"].items())
    rows = ""
    for v in ["v0", "v1", "v2", "v3", "v4", "v5"]:
        c = counts[v]
        assert sum(c.values()) == total
        segs = "".join(
            f'<div class="seg" style="flex:{c[k]};background:{ATOM_COLOR[k]}"><span>{c[k]}</span></div>'
            for k in ATOM_COLOR if c.get(k))
        rows += f'<div class="r{" base" if v == "v0" else ""}"><div class="lab">{escape(T["rows"][v])}</div><div class="bar">{segs}</div></div>'
    html = f"""<style>
.wrap{{padding:34px 40px}}
h3{{font-size:25px;font-weight:700}} .sub{{font-size:16px;margin:6px 0 16px}}
.lgd{{display:flex;gap:22px;font-size:14.5px;margin-bottom:16px;color:#3D3D3A}} .lgd i{{display:inline-block;width:13px;height:13px;border-radius:3px;margin-right:7px;vertical-align:-1px}}
.box{{background:#fff;border:1px solid rgba(20,20,19,.1);border-radius:14px;padding:18px 22px}}
.r{{display:grid;grid-template-columns:300px 1fr;align-items:center;gap:16px;padding:7px 0}}
.r.base{{border-bottom:1px dashed rgba(20,20,19,.15);padding-bottom:13px;margin-bottom:6px}}
.lab{{font-size:15px;color:#3D3D3A}}
.bar{{display:flex;gap:2px;height:30px}}
.seg{{display:flex;align-items:center;justify-content:center;border-radius:4px;min-width:30px}}
.seg span{{font-size:14px;font-weight:700;color:#fff}}
.seg[style*="eda100"] span{{color:#141413}}
.src{{font-size:13px;margin-top:12px}}
</style><div class="wrap"><h3>{escape(T["title"])}</h3><p class="sub muted">{escape(T["sub"])}</p>
<div class="lgd">{legend}</div><div class="box">{rows}</div><p class="src muted">{escape(T["src"])}</p></div>"""
    render("atomic-survival" if lang == "zh" else "atomic-survival.en", html, 1400, 525)


if __name__ == "__main__":
    banner()
    for lang in ("zh", "en"):
        architecture(lang)
        rework(lang)
        atoms(lang)
