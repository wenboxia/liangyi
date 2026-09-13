"""
两仪论工作流 · 保证验证

方法论有几条规则是「违反即当场失效」的底线，手动跑的时候只能靠使用者自觉。
这份文件验证它们在代码里是**结构性成立**的，不是靠调用方守规矩。

    python -m engine.test_guarantees

不需要 API key，不产生任何调用费用 —— 验证的是结构，不是模型行为。
"""

from __future__ import annotations

import sys

from .config import PROFILES, check_hard_rules
from .window import WindowPool, ZeroContextViolation

PASS, FAIL = "\033[32m✓\033[0m", "\033[31m✗\033[0m"
_results: list[bool] = []


def check(condition: bool, label: str, detail: str = "") -> None:
    _results.append(condition)
    print(f"  {PASS if condition else FAIL} {label}")
    if detail:
        print(f"      {detail}")


def test_zero_context_isolation() -> None:
    """
    底线规则：单盲必须零上下文。

    P2B 的价值是模拟真实传播中的陌生读者。一旦给它背景信息，它会脑补，
    「暴露知识诅咒」这个核心机制当场失效。docs 里写着「这条规则没有例外」——
    所以这里不是「默认不传历史」，是主动拒绝任何注入历史的尝试。
    """
    print("\n单盲零上下文（底线规则）")
    pool = WindowPool("debug")
    blind = pool.get("critic-blind")

    check(blind.is_zero_context, "critic-blind 标记为零上下文窗口")

    try:
        blind.inject_history([{"role": "user", "content": "这个产品的背景是……"}])
        check(False, "注入历史应当被拒绝", "但它成功了 —— 底线规则失守")
    except ZeroContextViolation:
        check(True, "注入历史被拒绝，抛出 ZeroContextViolation")

    check(len(blind.history()) == 0, "拒绝之后窗口仍然是空的")


def test_window_isolation() -> None:
    """
    session hygiene 原则一二：每个角色一个独立窗口，同数字 = 同窗口。

    手动跑最致命的错误是用一个窗口跑完全程，于是所有角色污染在一起。
    这里验证隔离是物理的 —— 不同窗口就是不同的 messages 数组。
    """
    print("\n窗口隔离")
    pool = WindowPool("debug")
    scribe = pool.get("scribe")
    investor = pool.get("critic-investor")

    scribe.inject_history([{"role": "user", "content": "执笔者看过的东西"}])
    check(
        len(investor.history()) == 0,
        "执笔者有历史后，投资人窗口仍为空",
        f"执笔者 {len(scribe.history())} 条 / 投资人 {len(investor.history())} 条",
    )
    check(scribe is not investor, "不同角色是不同实例")
    check(pool.get("scribe") is scribe, "同名窗口取回同一实例 —— 续窗口语义成立")

    expert_a = pool.get("expert-a")
    check(
        expert_a.model.id == investor.model.id and expert_a is not investor,
        "同一个底模可以承担多个互相隔离的窗口",
        f"两者都用 {expert_a.model.id}，但上下文彻底分开",
    )


def test_hard_rules_block_bad_config() -> None:
    """
    硬规则不是文档里的建议，是开跑前的准入检查。

    最危险的违规是「假覆盖」：P2 链条全部落在同一坐标时，四条 failure mode
    看起来都被覆盖了，实际上有一整块维度没被任何人碰到。
    """
    print("\n硬规则准入检查")

    check(len(check_hard_rules("primary")) == 0, "primary 配置通过全部硬规则")
    check(len(check_hard_rules("contrast_a2")) == 0, "A2 对照组配置也通过")

    PROFILES["_test_all_same"] = {
        "anchor": "gpt-5.6-luna",
        "divergent_a": "gpt-5.6-luna",
        "divergent_b": "gpt-5.6-luna",
    }
    try:
        violations = check_hard_rules("_test_all_same")
        check(len(violations) >= 2, f"全同坐标配置被拦下，报出 {len(violations)} 条违规")
        joined = " ".join(violations)
        check("假覆盖" in joined, "识别出「假覆盖」问题（规则二）")
        check("A3" in joined, "识别出拆台档位不合规（规则三）")
    finally:
        PROFILES.pop("_test_all_same", None)


def test_chain_activates_four_axes() -> None:
    """
    P2 四步应当各激活一根 divergence 轴，且底模坐标真的跨维度。

    这不是风格偏好 —— 同坐标的底模共享规范约束和语料先验。
    """
    print("\nP2 链条的坐标分布")
    pool = WindowPool("primary")
    chain = ["critic-investor", "critic-blind", "critic-reviewer", "critic-devil"]
    coords = {pool.get(w).model.coordinate for w in chain}

    check(len(coords) >= 2, f"P2 链条跨维度：{' + '.join(sorted(coords))}")

    devil = pool.get("critic-devil")
    check(
        devil.model.dim_a == "A3",
        f"拆台由 A3 任务优先档扮演（{devil.model.id}）",
        "有规范层的底模会在最关键那一刀上把攻击软化掉",
    )

    blind = pool.get("critic-blind")
    producers = {pool.get(w).model.vendor for w in ["scribe", "expert-b"]}
    check(
        blind.model.vendor not in ("Anthropic", "OpenAI") or blind.model.vendor not in producers,
        f"单盲用第三方厂商（{blind.model.vendor}）",
        "同厂商模型的补脑能力最强，最不适合做单盲",
    )


def test_decision_points() -> None:
    """
    人工决策点的档位与触发规则。

    方法论把决策分两类：能委托的是系统内部的局部判断，不能委托的是站在系统外的
    边界判断。所以必停点不是"重要的步骤"，是"位置本身就是边界判断"的步骤。
    """
    from .gate import PRESETS, enabled
    from .orchestrator import MUST_STOP

    print("\n人工决策点")

    check(PRESETS["auto"] == set(), "auto 档全自动 —— 一次都不停，跑批用")
    check(
        PRESETS["hitl"] == MUST_STOP,
        f"hitl 档只开必停点：{sorted(MUST_STOP)}",
        "2C-rollback（不停就交付错东西）/ 2D-fix（不停就卡死）",
    )
    check(
        not enabled("auto", "2D-fix") and enabled("hitl", "2D-fix"),
        "同一决策点在两档下正确开关",
    )
    check(
        not any("scope-creep" in v for v in PRESETS.values()),
        "条件触发检测器不再绑定任何档位 —— 改成两档都跑影子模式",
        "full 档已砍：删的是档位，不是检测器",
    )

    from .steps import CHAIN
    declared = {s.decision_point for s in CHAIN if s.decision_point}
    check(
        MUST_STOP < declared,
        "链条声明的决策点是必停点的超集 —— 多出来的走影子模式",
        f"链条声明：{sorted(declared)}；必停：{sorted(MUST_STOP)}",
    )


def test_verdict_recorded() -> None:
    """
    2D-fix 的判定必须进结构化记录。

    这条测试是被一个真实 bug 逼出来的：meeting-notes 那条链判定「回 P1」，
    终端打了「判定回 P1」、产物也改名成 P2D-fix-judgment.md，但 run.json 的
    status 照写 completed，判定本身一个字都没进结构化记录——只活在 /tmp 里
    迟早被清掉的终端日志，和 markdown 正文的一句中文里。

    后果不是「少个字段」：整条链最重要的输出就是这个判定，按 status 做汇总的
    脚本会把「回 P1」算成正常完成，五条链的核心差异被整个抹平。
    """
    import json, tempfile
    from pathlib import Path as _P
    from .orchestrator import detect_p1_return
    from .trace import Trace

    print("\n2D-fix 判定的记录")

    check(
        detect_p1_return("【判定】回P1") and not detect_p1_return("【判定】产出v5"),
        "判定标记能被正确识别",
    )
    check(
        not detect_p1_return("【判定】不回 P1，框架内改"),
        "否定式表述不会被误判成回 P1",
    )

    # finish() 要把判定写进 run.json，且续跑时不能把已有判定覆盖成 null
    d = _P(tempfile.mkdtemp())
    tr = Trace(d, {"scenario_id": "x"})
    tr.finish(status="completed", extra={"verdict": "back-to-p1"})
    check(
        json.loads((d / "run.json").read_text())["verdict"] == "back-to-p1",
        "判定写得进 run.json",
    )

    tr2 = Trace(d, {"scenario_id": "x"})          # 模拟续跑
    tr2.finish(status="completed", extra={})       # 这次还没走到 2D-fix
    check(
        json.loads((d / "run.json").read_text()).get("verdict") == "back-to-p1",
        "续跑时不会把已有判定抹掉",
    )


def test_multiline_and_advisor() -> None:
    """
    多行输入不被切碎，以及顾问环的记录能分出「粘贴」和「想过之后同意」。

    2026-09-04 的事故：界面用 console.input() 只读一行，使用者粘进二十多行判断，
    终端把每个换行当成一次提交 —— 第一行成了全部指令，第二行的 ``` 成了「理由」。
    45 分钟的思考在 trace 里只留下一个反引号。

    终止条件不能用「单个空行」：人写的判断带段落间隔，本身就有空行，那样会从
    中间截断。所以这条测试专门验带空行的输入能被完整收下。
    """
    import json, tempfile
    from dataclasses import dataclass
    from pathlib import Path as _P
    from . import interact
    from .gate import PRESETS
    from .trace import Trace

    print("\n多行输入与顾问环记录")

    # --- 多行读取：带空行、带反引号，都要完整收下 ---
    pasted = ["第一行", "```", "> 2", "```", "", "空行之后还有内容", "最后一行"]
    feed = iter(pasted)

    def _fake_input(*a, **k):
        try:
            return next(feed)
        except StopIteration:
            raise EOFError    # 模拟 Ctrl-D —— 真实使用里粘完就是这么结束的

    orig = interact.console.input
    interact.console.input = _fake_input
    try:
        got = interact._read_multiline("测试")
    finally:
        interact.console.input = orig

    check("空行之后的内容" in got or "空行之后还有内容" in got,
          "单个空行不会截断多行输入", f"收到 {len(got.splitlines())} 行")
    check("```" in got, "反引号块不会被当成控制字符吃掉")

    # --- 顾问环记录：粘贴 vs 自己写，必须分得出 ---
    @dataclass
    class _Adv:
        a_text: str; b_text: str; a_choice: str; b_choice: str
        ok: bool = True
        @property
        def advisors_agree(self): return self.a_choice == self.b_choice

    advice = _Adv(a_text="我选 2，理由是不能拿沉默推断闲置。",
                  b_text="我选 2，我自己说哪些要退回去。通知会被错过。",
                  a_choice="2", b_choice="2")

    def _record(human_text: str, choice: str) -> dict:
        d = _P(tempfile.mkdtemp())
        tr = Trace(d, {"scenario_id": "t"})
        tr.record_decision(step_id="2C-rollback", position="2C-rollback",
                           mode="human", triggered=True, decision=choice,
                           rationale=human_text, advice=advice, human_text=human_text)
        return json.loads((d / "trace.jsonl").read_text().strip())

    pasted_rec = _record(advice.b_text, "rollback-more")
    own_rec = _record("我同意方向，但提醒功能我想保留，只是别拿它推断。", "rollback-more")

    check(pasted_rec["verbatim_paste"] is True,
          "逐字粘贴顾问输出会被记下来",
          "9-04 那次就是这样，但当时记录里看不出来")
    check(own_rec["verbatim_paste"] is False and own_rec["concur"] is True,
          "「自己写的、结论也一致」不会被误判成粘贴",
          "两种情况 concur 都是 True，靠 verbatim_paste 区分")

    # --- advised 档位和 minimal 停在同样的位置 ---
    from .orchestrator import MUST_STOP as _MS
    check(PRESETS["hitl"] == _MS, "hitl 档停在两个必停点上")


def test_loop_routing() -> None:
    """
    路由与轮次隔离。

    这条测试锁住三件事，每一件都是 loop 能不能成立的前提：

    一、**路由表要在真实数据上分得开。** 五条已跑完的链摆在那，
       subscription-manager 该走回 P2（K 占比 100% 但 0 kill shot ——
       方向可能错了但没被证死），meeting-notes 该走回 P1（2 个 kill shot），
       其余三条正常产出。分不开就说明阈值是拍脑袋定的。

    二、**第 2 轮必须被代码拦住。** p2d_fix.md 里本来就写着这条终止条件，
       但历史上两次都是靠模型自己遵守的 —— 判定书里留着模型的原话
       「本应回 P1……但因终止条件强制走框架内修改」。规则该由代码保证。

    三、**轮次目录必须隔离。** 不隔离的话第二轮跑 P1 时 idea-v1.md 已存在，
       pending() 会当成「已完成」跳过 —— 「第二轮重跑」和「第一轮没跑完」
       系统分不出来。
    """
    import tempfile
    from pathlib import Path as _P
    from .orchestrator import (Orchestrator, Scenario, route, parse_grading,
                               EXIT_BACK_P1, EXIT_BACK_P2, EXIT_DONE, MAX_ROUNDS)

    print("\nloop 路由与轮次")

    # ---- 一、路由表在真实数据上分得开 ----
    import glob, os
    got = {}
    for d in sorted(glob.glob("runs/*-auto")):
        name = os.path.basename(d).split("-", 2)[2].rsplit("-", 1)[0]
        log = open(f"{d}/decision-log.md", encoding="utf-8").read()
        j = f"{d}/artifacts/P2D-fix-judgment.md"
        if os.path.exists(j):
            log += open(j, encoding="utf-8").read()
        got[name] = route(log, 1)[0]

    if got:
        check(got.get("meeting-notes") == EXIT_BACK_P1,
              "meeting-notes（2 个 kill shot）走回 P1", f"实际 {got.get('meeting-notes')}")
        check(got.get("subscription-manager") == EXIT_BACK_P2,
              "subscription-manager（K 占比 100%、0 kill shot）走回 P2",
              f"实际 {got.get('subscription-manager')}")
        check(all(got.get(n) == EXIT_DONE
                  for n in ("dev-diagnose", "merchant-appeal", "what-to-wear")),
              "其余三条正常产出 v5")

    # ---- 二、第 2 轮被代码拦住 ----
    killshots = "分级表\n| 1 | a | H | K | Kill shot |\n| 2 | b | H | K | Kill shot |"
    check(route(killshots, 1)[0] == EXIT_BACK_P1, "第 1 轮 2 个 kill shot → 回 P1")
    check(route(killshots, MAX_ROUNDS)[0] != EXIT_BACK_P1,
          f"第 {MAX_ROUNDS} 轮同样的输入不再回 P1 —— 终止条件由代码保证",
          "历史上这条只靠模型自觉遵守")

    # ---- 三之前：出口 B 只重跑 P2 链条 ----
    #
    # pending() 按「产物存不存在」判进度，新一轮目录是空的。出口 B 如果只写
    # idea-v1.md，P0/P1A/P1B 的产物不存在 → 全部白跑，而消费它们的 P1.4
    # 反而因为 idea-v1.md 已存在被跳过 —— 重新生成的专家方案根本用不上。
    sc0 = Scenario.load(_P("scenarios/dev-diagnose.yaml"))
    o2 = Orchestrator(sc0, run_root=_P(tempfile.mkdtemp()), mode="auto")
    for n, body in (("P0-refined.md", "精炼稿"), ("P1-roles.yaml", "roles: x"),
                    ("P1A-expert-a.md", "A 案"), ("P1B-expert-b.md", "B 案"),
                    ("idea-v1.md", "第一轮 v1"), ("idea-v5.md", "第一轮 v5")):
        o2.write_artifact(n, body)
    o2.start_round(2)
    o2._seed_back_to_p2()
    todo = [x.id for x in o2.pending()]
    check(not ({"P0", "P1A", "P1B", "P1.4"} & set(todo)),
          "出口 B：P0 / P1A / P1B / P1.4 不重跑", f"待跑 {todo}")
    check(todo and todo[0] == "P2A", "出口 B：从 P2A 开始", f"实际从 {todo[:1]} 开始")
    check(o2.read_artifact("idea-v1.md") == "第一轮 v5",
          "出口 B：上一轮的 v5 成为本轮的 v1")
    check(o2.read_artifact("P1A-expert-a.md") == "A 案",
          "出口 B：P1 双专家方案原样带进新一轮")

    # ---- 三、轮次目录隔离 ----
    sc = Scenario.load(_P("scenarios/dev-diagnose.yaml"))
    orch = Orchestrator(sc, run_root=_P(tempfile.mkdtemp()), mode="auto")
    orch.write_artifact("idea-v1.md", "第一轮")
    orch.start_round(2)
    check(not orch.has_artifact("idea-v1.md"),
          "第二轮看不到第一轮的产物 —— 否则 pending() 会跳过重跑的步骤")
    orch.write_artifact("idea-v1.md", "第二轮")
    orch.start_round(1)
    check(orch.read_artifact("idea-v1.md") == "第一轮",
          "第二轮的产物不覆盖第一轮的")


def test_grading_row_count() -> None:
    """
    分级表只数数据行，不数表头。

    起因是一个静默的真 bug：原来的实现靠「行里没有『论据摘要』四个字」来排掉
    表头，可 p2d_fix.md 只约定了表的列，没约定表头逐字怎么写。模型写成
    「| # | 论据 |」（少了「摘要」二字）时，**表头就被当成第 1 条论据数进去**。
    VoyageGuard 那次 5 条论据被数成 6 条，写进了结果文档。

    后果不止是数字难看：K 占比 = K/total，分母灌水会系统性压低占比，
    让出口 B（回 P2）比它该有的更难触发 —— 一个偏向「不循环」的静默偏差。

    序号用中文数字的表也必须认：merchant-appeal 和 what-to-wear 两条链
    写的是「一二三四五」。
    """
    from .orchestrator import parse_grading

    print("\n分级表行数")

    body = ("| 1 | a | H（具体） | K（框架） | Kill shot |\n"
            "| 2 | b | M（一般） | F（框架内） | Fixable |\n"
            "| 3 | c | H（具体） | F（框架内） | Fixable |\n")
    for header in ("| # | 论据摘要 | 具体性 | 严重度 | 标签 |",
                   "| # | 论据 | 具体性 | 严重度 | 标签 |",
                   "| 编号 | 论点 | 具体性 | 严重度 | 标签 |"):
        table = f"分级表\n\n{header}\n|---|---|---|---|---|\n{body}"
        check(parse_grading(table) == (3, 1, 1),
              f"表头写成「{header.split('|')[2].strip()}」时仍然只数出 3 条")

    # kill shot 必须从「具体性 + 严重度」两格算出来，不认标签那一列的字面。
    # p2d_fix.md 只约定标签列要有，没约定逐字怎么写 —— 2026-09-10 那次 meeting-notes
    # 模型写的是「K+M」「H+F」而不是「Kill shot」「Fixable」，还多加了一列「说明」。
    # 靠字面匹配的话，真出现 K+H 时会数出 0 个 kill shot，回 P1 那条出口永远不触发。
    for label, extra in (("Kill shot", ""), ("K+H", ""), ("致命", ""),
                         ("K+H", " 说明 |"), ("", "")):
        t = (f"分级表\n\n| # | 论据 | 具体性 | 严重度 | 标签 |{extra}\n|---|---|---|---|---|\n"
             f"| 1 | a | H（可核查的反例） | K（打中核心前提） | {label} |\n"
             f"| 2 | b | M（属合理推断） | F（框架内可消化） | {label} |\n")
        check(parse_grading(t) == (2, 1, 1),
              f"标签写成「{label or '空'}」时仍然算得出 1 个 kill shot",
              f"实际 {parse_grading(t)}")

    # 序号和论据挤在同一格 —— 2026-09-10 的 subscription-manager 就是这样，
    # 结果整张表数成 0 行，模型判了回 P1 而路由放行成 done，第二轮没启动。
    merged = ("分级表\n\n| 论据 | 具体性 | 严重度 | 标签 |\n|---|---|---|---|\n"
              "| 1. 归因前提错误 | H（可核实的普遍现象） | K（攻击根因诊断） | **Kill shot** |\n"
              "| 2. 手动录入必然失效 | M（构造性场景） | K（指向覆盖能力） | Fixable |\n")
    check(parse_grading(merged) == (2, 2, 1),
          "序号和论据挤在同一格时仍然数得出来", f"实际 {parse_grading(merged)}")

    # 模型自己发明的档位（实测出现过 L）不能让整行被丢掉
    invented = ("分级表\n\n| # | 论据 | 具体性 | 严重度 |\n|---|---|---|---|\n"
                "| 1 | a | L（泛泛断言） | K（指向差异化） |\n"
                "| 2 | b | H（具体可核实） | K（指向根基） |\n")
    check(parse_grading(invented) == (2, 2, 1),
          "模型发明的档位 L 不会让整行被丢掉", f"实际 {parse_grading(invented)}")

    # 真漏了行的时候要出声，不能静默数少
    from .orchestrator import grading_anomalies
    broken = ("分级表\n\n| # | 论据 | 具体性 | 严重度 |\n|---|---|---|---|\n"
              "| 1 | a | H（具体） | K（框架） |\n"
              "| 2 | b | 说不好 | 也说不好 |\n")
    check(len(grading_anomalies(broken)) == 1,
          "分不了级的行会被单独报出来，不静默吞掉",
          f"实际报出 {len(grading_anomalies(broken))} 行")
    check(not grading_anomalies(merged) and not grading_anomalies(invented),
          "正常的表不产生误报")

    cn = ("分级表\n\n| 编号 | 论据 | 具体性 | 严重度 | 标签 |\n|---|---|---|---|---|\n"
          "| 一 | a | M（推理） | K（指向目标市场） | Fixable |\n"
          "| 二 | b | H（点名产品） | F（机制层可补） | Fixable |\n")
    check(parse_grading(cn) == (2, 1, 0),
          "序号用中文数字的表也数得出来")

    # 真实历史数据：7 条带分级表的链，条数必须和人工数的一致
    import glob, os, re
    row = re.compile(r"^\s*\|\s*(?:\d{1,3}|[一二三四五六七八九十]{1,3})\s*\|")
    checked = 0
    for d in sorted(glob.glob("runs/*/")):
        raw = ""
        for f in (f"{d}decision-log.md", f"{d}artifacts/P2D-fix-judgment.md"):
            if os.path.exists(f):
                raw += open(f, encoding="utf-8").read()
        if "分级表" not in raw:
            continue
        seg = raw[raw.rfind("分级表"):]
        manual = len([l for l in seg.splitlines() if row.match(l)])
        check(parse_grading(raw)[0] == manual,
              f"{os.path.basename(d.rstrip('/'))[:34]} 数出 {manual} 条")
        checked += 1
    check(checked >= 7, f"覆盖了 {checked} 条历史链的真实分级表")


def test_loop_turns_on_real_judgments() -> None:
    """
    循环装置能不能真的转 —— 用**真实跑出来的判定书**驱动，不发 API 调用。

    为什么要离线验：这条链上唯一能推翻方向的判断点极不稳定。同一个场景
    (subscription-manager)、同一份 v4，三次运行给出三种分级：
      2026-09-02  5 条 K 级、0 条致命  → 产出 v5
      2026-09-10  5 条 K 级、2 条致命  → 回 P1
      同日续跑    0 条 K 级           → 产出 v5
    所以「重跑几次直到撞上某个出口」验不了循环 —— 撞上了也只说明这次骰子这么掷。
    **循环装置对不对，和模型判得稳不稳，是两件事，必须分开验。**

    这里验的是前一件：给定一份真实的判定书，编排器会不会真的开出第二轮、
    第二轮从哪一步开始、第一轮的产物有没有被覆盖、终止条件拦不拦得住第三轮。
    """
    import tempfile
    from pathlib import Path as _P
    from .orchestrator import (Orchestrator, Scenario, parse_grading,
                               EXIT_BACK_P1, EXIT_BACK_P2, MAX_ROUNDS)
    from .steps import CHAIN

    print("\n循环装置（离线 · 真实判定书驱动）")

    REAL = {
        "back-to-p1": "runs/20260910-105702-subscription-manager-loopB/artifacts/round-1/P2D-fix-judgment.md",
        "back-to-p2": "runs/20260902-085850-subscription-manager-auto/decision-log.md",
    }
    for k, f in REAL.items():
        if not _P(f).exists():
            print(f"  [跳过] 找不到 {f}")
            return

    def fresh(judgment: str, as_judgment: bool):
        """铺好一轮完整产物，2D-fix 的产出用真实判定书。"""
        sc = Scenario.load(_P("scenarios/subscription-manager.yaml"))
        o = Orchestrator(sc, run_root=_P(tempfile.mkdtemp()), mode="auto")
        for st in CHAIN:
            if st.id == "2D-fix":
                continue
            o.write_artifact(st.output, f"round-1 的 {st.output}")
        o.write_artifact("P2D-fix-judgment.md" if as_judgment else "idea-v5.md", judgment)
        (o.run_dir / "decision-log.md").write_text(judgment, encoding="utf-8")
        return o

    # ---- 出口 A：真的开出第二轮，整链重跑 ----
    j1 = _P(REAL["back-to-p1"]).read_text(encoding="utf-8")
    check(parse_grading(j1)[2] >= 2, f"这份真实判定书确实有 {parse_grading(j1)[2]} 条致命论据")
    o = fresh(j1, as_judgment=True)
    check(o.pending() == [], "第一轮铺满后没有待跑步骤 —— 判定书也算 2D-fix 跑过了")
    code, why = o._decide_next_round()
    check(code == EXIT_BACK_P1, "真实判定书 → 出口 A（回 P1）", why)

    pool_before = o.pool
    o.start_round(2)
    check((o.run_dir / "artifacts" / "round-2").is_dir(), "第二轮目录真的建出来了")
    check([s.id for s in o.pending()] == [s.id for s in CHAIN],
          "第二轮从 P0 开始整链重跑")
    check(o.pool is not pool_before, "第二轮所有窗口新开，不带上一轮的记忆")
    check((o.run_dir / "artifacts" / "round-1" / "idea-v1.md").exists(),
          "第一轮的产物原样还在，没被第二轮覆盖")

    # ---- 第三轮必须被终止条件拦住 ----
    o.write_artifact("P2D-fix-judgment.md", j1)
    code3, why3 = o._decide_next_round()
    check(code3 != EXIT_BACK_P1,
          f"第 {MAX_ROUNDS} 轮同样判回 P1，被终止条件拦下", why3)

    # ---- 出口 B：只重压 P2 链条 ----
    j2 = _P(REAL["back-to-p2"]).read_text(encoding="utf-8")
    t, K, ks = parse_grading(j2)
    check(ks == 0 and K / t >= 0.6,
          f"这份真实判定书是「大部分打前提（{K}/{t}）但零致命」的形状")
    o2 = fresh(j2, as_judgment=False)
    code2, why2 = o2._decide_next_round()
    check(code2 == EXIT_BACK_P2, "真实判定书 → 出口 B（回 P2）", why2)

    o2.start_round(2)
    o2._seed_back_to_p2()
    todo = [s.id for s in o2.pending()]
    check(todo and todo[0] == "P2A", f"第二轮从 P2A 开始，不重跑 P0/P1", f"实际 {todo}")
    check(o2.read_artifact("idea-v1.md") == "round-1 的 idea-v5.md".replace("idea-v5", "idea-v5")
          or o2.read_artifact("idea-v1.md") == j2,
          "上一轮的 v5 逐字成为第二轮的 v1")


def main() -> int:
    print("两仪论工作流 · 结构保证验证")
    print("=" * 52)
    test_zero_context_isolation()
    test_window_isolation()
    test_hard_rules_block_bad_config()
    test_chain_activates_four_axes()
    test_decision_points()
    test_verdict_recorded()
    test_multiline_and_advisor()
    test_loop_routing()
    test_grading_row_count()
    test_loop_turns_on_real_judgments()

    passed, total = sum(_results), len(_results)
    print("\n" + "=" * 52)
    print(f"{passed}/{total} 通过" if passed == total else f"\033[31m{passed}/{total} 通过\033[0m")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
