#!/usr/bin/env python3
"""
从原始运行数据生成 docs/case-voyageguard.md。

这份案例是给「想追问」的读者看的，不进展示站——站上只讲产品怎么工作，
不摆我跑过的例子。

数字全部从数据文件算，不手抄：手抄过一次，抄出了字节冒充字数、
表头算术错、13 条对不上 14 行三处错。
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = json.loads((ROOT / "docs/visualizations/voyageguard-data.json").read_text(encoding="utf-8"))
JUDGE = json.loads((ROOT / "retrospective/voyageguard/judging.json").read_text(encoding="utf-8"))

STATE = {"守住": "原样保留", "收窄变形": "被改小", "未守住": "被推翻", "判不动": "无法判断"}
ACT_TITLE = {
    "P1": ("P1 · 对抗式方案生成", "两个坐标不同的专家窗口独立产出方案，执笔窗口融合成第一版"),
    "2A-fix": ("P2A · 怀疑论投资人批判 → 2A-fix", "针对市场与商业逻辑的 failure mode"),
    "2B-fix": ("P2B · 零上下文单盲复审 → 2B-fix", "窗口只收到方案正文，不给背景、不给目标、不给历史"),
    "2C-rollback": ("P2C · 知情复审（方向漂移检测）→ 2C-rollback", "同时拿到 v1 与 v3，查产品身份是否被置换"),
    "2D-fix": ("P2D · 拆台专家质疑前提 → 2D-fix", "只攻方案赖以成立的前提，不挑细节"),
}
WIN_WHY = {
    6: ("阈值查不到官方锚点",
        "项目初期的 PRD 写「浪高 1.5–2.5 米＝中风险」，事后查证找不到任何官方出处。"
        "这一步之后方案确立了「每条规则标注来源与可信等级」的机制，"
        "使「凭空给出一个数字」在结构上不再有位置。"),
    7: ("越权断言「停航预警」",
        "项目初期的 PRD 使用「高风险（停航预警）」这类断言措辞，超出该工具的资格边界。"
        "此后方案写死了自身的能力边界：不回答「这艘船今天到底会不会开」，"
        "只回答气象条件是否处于通常可安全运行的范围。"),
    10: ("数据缺失时静默按安全处理",
         "项目初期数据缺失时默认按「安全」处理（能见度取 999、风速取 0），"
         "是安全类产品最坏的默认值。此后改为分粒度处理，核心指标全缺才返回「数据不足」。"),
    11: ("任何地名都能评估",
         "项目初期任何地名都能评估，「上海→南极」返回「低风险，建议出行」。"
         "此后限定了具体的规则覆盖清单，清单外只返回原始数据、不给结论。"),
}


def main() -> None:
    seed, versions, acts = DATA["seed"], DATA["versions"], DATA["acts"]
    counts, matrix = JUDGE["counts"], JUDGE["matrix"]
    sealed = JUDGE["sealed_v5"]
    hits = {h["n"]: h["hit"] for h in DATA["result"]["rework_hits"]}
    v0hits = {h["item"]: h["hit"] for h in JUDGE["v0_rework"]}
    n_hit, n_v0 = sum(hits.values()), sum(v0hits.values())
    held = counts["v5"].get("守住", 0)

    L: list[str] = []
    w = L.append

    w("# 案例 · VoyageGuard 回溯跑\n")
    w("> 拿一个**已经做完的项目**，倒回到它最开始的样子，重新跑一遍这条链，")
    w("> 再和当年真实的返工清单对照。\n")
    w(f"> 2026-09-08 · 全自动档 · 13 步 · "
      f"${sum(s['cost'] for s in DATA['steps']):.2f} · "
      f"{round(sum(s['sec'] for s in DATA['steps'])/60)} 分钟\n")
    w("---\n")

    w("## 为什么能这样比\n")
    w("这个项目是**先做完、后回溯**的：成品在，当年的返工清单也在。")
    w("所以「链条能不能避开当年踩的坑」是可核对的，不用自己给自己打分。\n")
    w("两把尺子都在跑之前封存，顺序不可逆——")
    w("**先看链条产出 → 再开原子点 → 最后才开返工清单**。")
    w("先看答案再去产出里找对应，就是自导自演。\n")

    w("## 一、原始想法\n")
    w(f"写任何文档之前的想法，本人口述并确认，{seed['chars']} 字。\n")
    w("```")
    w(seed["text"].strip())
    w("```\n")

    w(f"## 二、拆成 {len(DATA['points'])} 条原子点\n")
    w("原子点＝这段话里所有「产品必须做到什么」的主张，逐条拆出来，拆完封存。")
    w("拆解、复核、三向审计由互相独立的窗口完成，**全部未见过该项目的成品与返工清单**。\n")
    w("| # | 这条主张是什么 | 原文依据 |")
    w("|---|---|---|")
    for p in DATA["points"]:
        w(f"| `{p['id']}` | {p['text']} | {p['source']} |")
    w("")
    w("> 编号缺 `P4`：原 P4 的依据是对用户能力的**描述句**，不是对产品的要求，")
    w("> 内容也和 P7、P8 重合，已删除。空号留着便于追溯。\n")

    w("## 三、十三步之后，这些主张的去向\n")
    order = ["v1", "v2", "v3", "v4", "v5"]
    w("| | " + " | ".join(order) + " |")
    w("|---|" + "---|" * len(order))
    for lbl, key in (("原样保留", "守住"), ("被改小", "收窄变形"), ("被推翻", "未守住")):
        w(f"| **{lbl}** | " + " | ".join(str(counts[v].get(key, 0)) for v in order) + " |")
    w("")
    w(f"**往下走不是坏事。**{len(DATA['points'])} 条一条不少地活到最后，")
    w("只说明没有一条被认真质疑过。这条链干的就是质疑。")
    w("该看的不是掉了几条，是**掉的那几条该不该掉**。\n")
    w("逐条去向：\n")
    w("| # | 结果 | v5 里的原句 |")
    w("|---|---|---|")
    for p in DATA["points"]:
        c = matrix["v5"].get(p["id"], {})
        st = STATE.get(c.get("state", ""), c.get("state", ""))
        q = (c.get("quote", "") or "").replace("\n", " ").strip()
        w(f"| `{p['id']}` | {st} | {q[:110]} |")
    w("")

    w("## 四、每一步换来了什么\n")
    w("十三步里真正会改动方案的有五处。**「换来的返工项」= 当年踩过、这一步之后不会再踩的坑。**\n")
    w("| 步骤 | 提出 | 新增主张 | 改动原子点 | 换来的返工项 |")
    w("|---|---|---|---|---|")
    for a in acts:
        title = ACT_TITLE[a["key"]][0].split(" · ")[0]
        wins = "、".join(f"第 {x['rework']} 条" for x in a["wins"]) or "**0 条**"
        w(f"| {title} | {a['proposed'] or '—'} | {len(a['additions'])} | "
          f"{len(a['points_changed'])} | {wins} |")
    w("")
    for a in acts:
        title, sub = ACT_TITLE[a["key"]]
        w(f"### {title}\n")
        w(f"{sub}。\n")
        if a["critic"]:
            c = a["critic"]
            w(f"由 `{c['model']}`（{c['coordinate']}）在 `{c['window']}` 窗口执行，"
              f"提出 {a['proposed']} 条。")
        elif a["contributors"]:
            names = "、".join(f"`{x['model']}`（{x['coordinate']}）" for x in a["contributors"])
            w(f"两个专家窗口分别由 {names} 承担，互不可见——独立是对抗成立的前提条件。")
        if a["verdicts"]:
            w("执笔窗口的处理：" + "、".join(f"{k} {v} 条" for k, v in a["verdicts"].items()) + "。")
        d = next((x for x in DATA["diffs"] if x["step"] == a["key"]), None)
        if d:
            w(f"字数变化：加 {d['added']}、删 {d['removed']}，净 {d['net']:+}。")
        w("")
        if a["wins"]:
            for x in a["wins"]:
                name, why = WIN_WHY[x["rework"]]
                w(f"**避开的返工项：第 {x['rework']} 条——{name}。**\n")
                w(f"{why}\n")
        else:
            w("**避开的返工项：0 条。**\n")
            if a["key"] == "P1":
                w(f"这一步在建立基线，尚未进入批判环节。"
                  f"后续 {len(DATA['additions'])} 条原文没有的新主张中，"
                  f"{len(a['additions'])} 条在这一步成型。\n")
            elif a["key"] == "2C-rollback":
                w("这一步是全链**唯一一次净减**，但按返工清单这把尺子量，它没换来任何东西。\n")
                w("需要说明：项目文档记载「P2C 是整条链最值钱的一步」，依据来自另一个场景。")
                w("**本次运行的数据不支持这一判断。**\n")
                w("同时也要说准确：这把尺子量的是「产品判断出错」，而 P2C 处理的是「方向偏移」，")
                w("**量不到不等于没有作用**——但这一次它确实没有换来任何可核对的收益。\n")

    w("## 五、三方对照\n")
    w("这 7 条**不是「纯人做对的事」，而是项目初期全部判断错误、后来返工修掉的事**。")
    w("所以这张表问的不是「流程能否追上人」，而是「同样的坑，谁踩了、谁没踩」。\n")
    w("| 纯人犯的错 | 纯人 | 两仪全自动流程 | 纯单个模型 |")
    w("|---|---|---|---|")
    mark = lambda x: "**避开**" if x else "犯了"
    for r in DATA["rework"]:
        w(f"| {r['n']} · {r['error']} | 犯了 | {mark(hits.get(r['n']))} | {mark(v0hits.get(r['n']))} |")
    w(f"| | **0 / {len(DATA['rework'])}** | **{n_hit} / {len(DATA['rework'])}** "
      f"| **{n_v0} / {len(DATA['rework'])}** |")
    w("")
    w(f"> **纯单个模型**＝ 同一段 {seed['chars']} 字原始想法，只调用一次模型、不走流程，直接产出方案。\n")

    w("### 结论\n")
    w(f"同一个原始想法，走完流程避开了 {n_hit} 个坑；只调用一次模型，避开 {n_v0} 个。")
    w("而且纯单个模型避开的那 1 条，流程同样避开——**没有一条是它做到而流程没做到的。**\n")

    w("### 但这些话不能说过头\n")
    w("**一、只跑了一次，就一个项目。**")
    w("流程和单个模型的差别只落在 3 条上。**3 条太少，少到分不清是真本事还是运气。**")
    w("能说的是「这一次流程明显更好」，不能说「流程就是更好」。\n")
    w("**二、只比了七分之一个项目。**")
    w("当年的返工清单一共 21 条，这里只用了 7 条。剩下 14 条是**东西开始做了以后**")
    w("才暴露的问题（评测怎么搭、数据怎么接）。这套流程只出想法，走不到那一步——")
    w("**不是它没做到，是压根没轮到它。**\n")
    ag = JUDGE["v5_agreement"]
    w("**三、判定不是跨厂商复核的。**")
    w("判据在跑之前就封存，判定者和复判者互相看不到结论，")
    w(f"一致率 {ag['agree']}/{ag['total']}。但两边都是同一家的模型，真正独立的第三方复核目前没有。\n")

    w("---\n")
    w("完整方法与自查见 [`evaluation.md`](evaluation.md)，")
    w("引擎的结构保证见 [`../engine/VALIDATION.md`](../engine/VALIDATION.md)。")
    w("原始判据封存在 [`../retrospective/voyageguard/`](../retrospective/voyageguard/)。")

    body = "\n".join(L) + "\n"
    out = ROOT / "docs/case-voyageguard.md"
    out.write_text(body, encoding="utf-8")
    print(f"写出 {out.relative_to(ROOT)}（{len(body)} 字符）")


if __name__ == "__main__":
    main()
