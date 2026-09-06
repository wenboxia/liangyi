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

    check(PRESETS["off"] == set(), "off 档全自动 —— 消融实验主线用，保可复现")
    check(
        PRESETS["minimal"] == MUST_STOP,
        f"minimal 档只开必停点：{sorted(MUST_STOP)}",
        "2C-rollback（不停就交付错东西）/ 2D-fix（不停就卡死）",
    )
    check(
        MUST_STOP < PRESETS["full"],
        f"full 档在必停点之上再加条件触发：{sorted(PRESETS['full'] - MUST_STOP)}",
    )

    check(
        not enabled("off", "2D-fix") and enabled("minimal", "2D-fix"),
        "同一决策点在不同档位下正确开关",
    )
    check(
        not enabled("minimal", "scope-creep") and enabled("full", "scope-creep"),
        "条件触发点只在 full 档启用",
    )

    from .steps import CHAIN
    declared = {s.decision_point for s in CHAIN if s.decision_point}
    check(
        declared == PRESETS["full"],
        "链条里声明的决策点与 full 档完全对应",
        f"链条声明：{sorted(declared)}",
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
    check(PRESETS["advised"] == PRESETS["minimal"],
          "advised 与 minimal 停点相同 —— 否则测不出顾问带来的差异")


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

    passed, total = sum(_results), len(_results)
    print("\n" + "=" * 52)
    print(f"{passed}/{total} 通过" if passed == total else f"\033[31m{passed}/{total} 通过\033[0m")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
