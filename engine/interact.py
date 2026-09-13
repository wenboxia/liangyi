"""
两仪论工作流 · 人工决策点的交互界面

被叫住的时候，人需要看到什么才能做判断？这份文件的全部设计都围绕这个问题。

方法论说人做的是"系统内部无法自判的决策"。那么界面就不能只问"同意吗"——
那等于把人变成橡皮图章，正是「反滑坡规则」要防的那种滑坡。

实测教训（2026-08-31）：第一版只展示了 P2C 的诊断和当前版本开头，使用者的
反馈是"前九步的内容我也看不到，我怎么去判断"。这不是续跑造成的——从头跑
前九步也是刷屏过去的。**决策点必须自带上下文，不能指望人记得刚才发生了什么。**

所以每次中断给四样东西：
  1. 你最初想做的是什么（原始 seed）
  2. 方案怎么走到现在的（版本演化 + 每一版因何而改）
  3. 这一步的判断材料（诊断 / 拆台论据，完整不截断）
  4. 可以选的路，以及随时调阅任何一份完整文档
"""

from __future__ import annotations

import time
from dataclasses import dataclass

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

RULE = "═" * 74


def _pos(step_id: str) -> str:
    """步数动态算 —— 链条会增删步骤（P1.0 就是后加的），写死必然过期。"""
    from .steps import CHAIN
    ids = [s.id for s in CHAIN]
    return f"({ids.index(step_id) + 1}/{len(CHAIN)} 步)" if step_id in ids else ""



# 决策点的选项。提到模块级是因为顾问材料包要用同一份 —— 两边给的选项一旦
# 不一致，顾问答的和人判的就不是同一个问题，对照数据全废。
OPTIONS: dict[str, list[tuple[str, str, str]]] = {
    "2C-rollback": [
        ("1", "accept", "接受诊断，让执笔者自己判断哪些回退、哪些保留"),
        ("2", "rollback-more", "我指定要回退的地方"),
        ("3", "keep-more", "这些漂移其实是改进，我指定要保留的"),
    ],
    "2D-fix": [
        ("1", "accept", "按执笔者的判定走"),
        ("2", "revise", "框架内修改，但按我的指令改"),
        ("3", "back-to-p1", "前提确实错了，回 P1 重做"),
    ],
}


@dataclass
class Decision:
    choice: str
    instruction: str = ""
    rationale: str = ""
    think_ms: int = 0   # 从界面呈现到做出选择花了多久 —— 疲劳信号
    advice: object | None = None   # Advice；没跑顾问环时是 None


# ---------------------------------------------------------------- 上下文展示

_VERSION_STORY = [
    ("idea-v1.md", "P1 两位专家方案融合而成"),
    ("idea-v2.md", "响应 P2A 投资人批判后"),
    ("idea-v3.md", "响应 P2B 零上下文单盲反馈后"),
    ("idea-v4.md", "响应 P2C 方向漂移诊断后"),
    ("idea-v5.md", "响应 P2D 拆台后"),
]


def _title_of(text: str) -> str:
    """
    取产品名。

    只要破折号前那一截 —— 「订阅哨 —— 一个不问你银行密码，也能帮你把订阅
    问题看清楚的工具」里，有身份漂移信号的是「订阅哨」，后面那半句是宣传语。
    整条塞进表格会换行三次，把字数曲线挤得读不出来。
    """
    title = "（无标题）"
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("# ") and "idea" not in s.lower():
            title = s[2:].strip()
            break
    else:
        for line in text.splitlines():
            if line.strip():
                title = line.strip()
                break

    for sep in ("——", "—", " - ", "|"):
        if sep in title:
            title = title.split(sep)[0].strip()
            break
    return title[:22] + "…" if len(title) > 22 else title


def _show_origin(orch) -> None:
    console.print(Panel(
        orch.scenario.seed.strip(),
        title="[bold]① 你最初想做的[/bold]", border_style="green", expand=False,
    ))


def _show_evolution(orch) -> None:
    """
    方案怎么走到现在。

    表里是字数曲线和每版标题 —— 前者一眼看出「越改越胖」，后者一眼看出产品
    身份漂没漂（投资 skill 那次就是从「投资助手」漂成了「防呆引擎」）。

    表下面是每一步的实质变化。加这块是因为 2C-rollback 的选项 2/3 要人「指定
    哪些漂移要回退」，而原来那一列「因何而改」是写死的字符串（"响应 P2B 零
    上下文单盲反馈后"），只说了这版是被谁逼出来的，没说它到底改了什么 ——
    拿这个没法指定回退哪些。
    """
    from .digest import version_diff

    table = Table(show_header=True, header_style="bold", box=None, padding=(0, 2))
    for col in ("版本", "字数", "变化", "标题"):
        table.add_column(col, justify="right" if col in ("字数", "变化") else "left")

    versions: list[tuple[str, str]] = []   # (版本短名, 正文)
    prev = None
    for fname, _why in _VERSION_STORY:
        if not orch.has_artifact(fname):
            continue
        text = orch.read_artifact(fname)
        n = len(text)
        delta = "—" if prev is None else f"{(n - prev) / prev * 100:+.0f}%"
        short = fname.replace("idea-", "").replace(".md", "")
        table.add_row(short, f"{n:,}", delta, _title_of(text))
        versions.append((short, text))
        prev = n

    console.print(Panel(table, title="[bold]② 方案怎么走到现在的[/bold]",
                        border_style="cyan", expand=False))

    if len(versions) < 2:
        return

    lines = []
    for (a, ta), (b, tb) in zip(versions, versions[1:]):
        d = version_diff(ta, tb)
        if not d.ok:
            lines.append(f"[dim]{a} → {b}[/dim]   [dim]（摘要生成失败，输入 {b} 看原文）[/dim]")
        elif d.touched_product:
            lines.append(f"[bold cyan]{a} → {b}[/bold cyan]   {d.change}")
        else:
            lines.append(f"[dim]{a} → {b}   {d.change}[/dim]")

    console.print(Panel("\n".join(lines), border_style="cyan", expand=False,
                        title="[bold]每一步实际改了什么[/bold]"))


def _show_body(text: str, title: str, style: str) -> None:
    console.print(Panel(text.strip(), title=f"[bold]{title}[/bold]",
                        border_style=style, expand=False))



def _show_intent(orch) -> None:
    """
    意图对照 —— 这是整个界面最重要的一块。

    人要判断的不是"哪个设计更好"（那需要领域专家），是"这还是我想要的吗"
    （那只需要他是提出想法的人）。所以把判断收敛到这两行。
    """
    from .digest import intent_shift

    shift = intent_shift(orch.scenario.seed,
                         orch.read_artifact("P2C-review.md"))
    if not shift.ok:
        console.print("[dim]（意图摘要生成失败，请直接看下方完整诊断）[/dim]")
        return

    body = [
        f"[bold green]你当初要的[/bold green]   {shift.promise_then}",
        f"[bold yellow]现在变成了[/bold yellow]   {shift.promise_now}",
    ]
    if shift.rows:
        body.append("")
        for r in shift.rows:
            body.append(
                f"[dim]{str(r.get('维度','')):8}[/dim] "
                f"{r.get('当初','')}  [dim]→[/dim]  {r.get('现在','')}"
            )
    if shift.summary:
        body += ["", f"[bold]⇒ {shift.summary}[/bold]"]

    console.print(Panel("\n".join(body), border_style="yellow",
                        title="[bold]这还是你想要的东西吗[/bold]", expand=False))


def _show_devil_digest(orch) -> None:
    """拆台摘要 —— 每条一句话，标出打中的是前提还是实施细节。"""
    from .digest import devil_digest

    dg = devil_digest(orch.read_artifact("P2D-devils-advocate.md"))
    if not dg.ok:
        console.print("[dim]（拆台摘要生成失败，请直接看下方完整论据）[/dim]")
        return

    lines = []
    for pt in dg.points:
        hit = str(pt.get("打中的是", ""))
        tag = "[red]打前提[/red]" if "前提" in hit else "[dim]打细节[/dim]"
        lines.append(f"{pt.get('序号','·')}. {tag}  {pt.get('一句话','')}")
    if dg.overall:
        lines += ["", f"[bold]⇒ {dg.overall}[/bold]"]
    lines.append(f"\n[dim]打中前提的 {dg.hits_premise}/{len(dg.points)} 条 —— "
                 f"这是判断「框架内消化」还是「回 P1」的主要依据[/dim]")

    console.print(Panel("\n".join(lines), border_style="red",
                        title="[bold]拆台论据，一条一句话[/bold]", expand=False))


# ---------------------------------------------------------------- 调阅与提问

def _viewable(orch) -> dict[str, tuple[str, str]]:
    """可以随时调阅的完整文档。键是用户输入的短名。"""
    catalog = {
        "seed": ("原始想法", None),
        "v1": ("idea-v1.md", "idea-v1.md"),
        "v2": ("idea-v2.md", "idea-v2.md"),
        "v3": ("idea-v3.md", "idea-v3.md"),
        "v4": ("idea-v4.md", "idea-v4.md"),
        "p1a": ("P1 专家A 方案", "P1A-expert-a.md"),
        "p1b": ("P1 专家B 方案", "P1B-expert-b.md"),
        "p2a": ("P2A 投资人批判", "P2A-critique.md"),
        "p2b": ("P2B 零上下文单盲", "P2B-blind-review.md"),
        "p2c": ("P2C 方向漂移诊断", "P2C-review.md"),
        "p2d": ("P2D 拆台", "P2D-devils-advocate.md"),
        "log": ("决策日志", None),
    }
    return {k: v for k, v in catalog.items()
            if v[1] is None or orch.has_artifact(v[1])}


def _view(orch, key: str) -> None:
    cat = _viewable(orch)
    label, fname = cat[key]
    if key == "seed":
        body = orch.scenario.seed
    elif key == "log":
        p = orch.run_dir / "decision-log.md"
        body = p.read_text(encoding="utf-8") if p.exists() else "（还没有决策日志）"
    else:
        body = orch.read_artifact(fname)
    console.print(Panel(body.strip(), title=f"[bold]{label}[/bold]",
                        border_style="dim"))


def _drain_stdin() -> None:
    """
    丢掉缓冲区里没被读走的输入。

    2026-09-06 的真实事故：使用者在上一栏结束时多打了一个 `.`，那个字符留在
    stdin 里没人消费。到下一个提示「粘贴顾问 A 的回答」时它被立刻读走 —— 而
    `.` 正是终止符，于是 A 栏瞬间结束、内容为空，使用者粘的东西顺位落进了 B 栏。

    这和 09-04 那次是同一类问题：一次输入的残留污染下一个提示。修多行读取只
    解决了单次读取内部，跨提示的残留要在每个提示开始前清掉。

    只在真终端上做。管道输入（测试、脚本）不能清，那会把喂进来的数据吃掉。
    """
    try:
        import sys
        import termios
        if sys.stdin.isatty():
            termios.tcflush(sys.stdin, termios.TCIFLUSH)
    except Exception:
        pass      # 非 Unix 或没有 tty —— 清不了就算了，不该为此中断决策


def _read_multiline(hint: str) -> str:
    """
    读多行输入。

    2026-09-04 的真实事故：这里原来是 `console.input()`，只读一行。使用者粘进
    二十多行判断，终端把每个换行都当成一次提交——第一行成了全部指令，第二行
    ``` 成了「理由」，剩下十几行涌进后续提示。45 分钟的思考在 trace 里只留下
    一个反引号。

    终止方式不能用「空行结束」：人真正写出来的判断带段落间隔，本身就有空行，
    那样会把输入从中间截断。所以用 Ctrl-D（EOF，粘贴场景的标准做法）、单独一行
    的 `.`（怕 Ctrl-D 的退路）、或连续两个空行。
    """
    _drain_stdin()
    console.print(f"[dim]{hint}[/dim]")
    console.print("[dim]（多行。粘完按 Ctrl-D 结束；也可以单独一行打 . 或连按两次回车）[/dim]")

    lines: list[str] = []
    blanks = 0
    while True:
        try:
            line = console.input("")
        except EOFError:          # Ctrl-D —— TTY 上是单次 EOF，后面还能继续读
            break
        if line.strip() == ".":
            break
        if line.strip():
            blanks = 0
        else:
            blanks += 1
            if blanks >= 2:
                break
        lines.append(line)

    text = "\n".join(lines).strip()

    # 回显收下了多少 —— 万一双空行把粘贴内容从中间截断了，这一行能当场看出来。
    # 不回显的话，截断和「本来就写这么多」在屏幕上长得一模一样。
    if text:
        console.print(f"[dim]  ✓ 收下 {len(text.splitlines())} 行 / {len(text)} 字[/dim]")
    return text


def _ask(orch, options: list[tuple[str, str, str]]) -> Decision:
    cat = _viewable(orch)
    console.print(f"\n[bold]④ 你的决定[/bold]")
    for key, name, desc in options:
        console.print(f"  [bold cyan]{key}[/bold cyan]  {desc}")
    console.print(f"  [dim]或输入以下任一项查看完整原文（看完会回到这里）：[/dim]")
    console.print(f"  [dim]  {' / '.join(cat)}[/dim]")

    _drain_stdin()
    started = time.time()
    valid = {o[0] for o in options}
    while True:
        raw = console.input("\n> ").strip().lower()
        if raw in cat:
            _view(orch, raw)
            continue
        if raw in valid:
            break
        console.print(f"[yellow]请输入 {'/'.join(sorted(valid))}，或文档名查看原文[/yellow]")

    think_ms = int((time.time() - started) * 1000)   # 选定的那一刻计时结束
    choice = next(o[1] for o in options if o[0] == raw)
    instruction = ""
    if raw != "1":
        instruction = _read_multiline("写给执笔者的指令：")
    rationale = _read_multiline("你这么定的理由（进 decision-log，可留空）：")
    return Decision(choice=choice, instruction=instruction,
                    rationale=rationale, think_ms=think_ms)


def _show_advice(advice) -> None:
    """
    展示两份顾问建议。

    刻意**先展示、后问选择**，而且不给「和顾问一致就一键采纳」这种快捷方式 ——
    那正好是 2026-09-04 那次踩的坑：粘贴比思考省力，于是记录里只剩下粘贴。

    也刻意不逼人找分歧。「他们说得都对、我都赞同、所以选 2」是合法的综合判断。
    要防的不是「同意顾问」，是「同意得看不出想没想过」——所以真正的手段不在
    这个界面上，而在 trace 里那两个字段（concur / verbatim_paste）。
    """
    if advice is None or not getattr(advice, "ok", False):
        return

    for tag, text, choice, who in (
        ("A", advice.a_text, advice.a_choice, "ChatGPT"),
        ("B", advice.b_text, advice.b_choice, "Claude"),
    ):
        if not text:
            continue
        console.print(Panel(
            text.strip(),
            title=f"[bold]顾问 {tag}（{who}）· 主张选 {choice}[/bold]",
            border_style="magenta", expand=False,
        ))

    if advice.advisors_agree:
        console.print(
            f"[dim]两位顾问一致主张选 {advice.a_choice}。"
            f"一致不等于正确 —— 它们可能共享同一个盲区。[/dim]"
        )
    else:
        console.print(
            f"[bold yellow]两位顾问不一致[/bold yellow]"
            f"（A 主张 {advice.a_choice}，B 主张 {advice.b_choice}）"
            f"[dim] —— 分歧处通常最有信息量。[/dim]"
        )


# ---------------------------------------------------------------- 决策点入口

def ask_rollback(orch, advice=None) -> Decision:
    """
    2C-rollback · 必停点。

    不停的代价有实测：投资 skill 那次 P2C 抓到产品身份从「投资助手」漂成
    「防呆引擎」，没回退的话交付的会是一份通过审查的合规文档。
    """
    console.print(f"\n{RULE}")
    console.print(f"[bold yellow]人工决策点 · 2C-rollback[/bold yellow]"
                  f"   [dim]{_pos('2C-rollback')}[/dim]")
    console.print(RULE)

    _show_intent(orch)
    _show_evolution(orch)

    console.print(
        "[dim]判据是「这偏离了我最初要解决的问题吗」，不是「哪个设计更好」——"
        "后者系统自己能判，前者只有你知道。\n"
        "想看完整诊断输入 p2c，想看方案原文输入 v1 / v3。[/dim]"
    )
    _show_advice(advice)
    d = _ask(orch, OPTIONS["2C-rollback"])
    d.advice = advice
    return d


def ask_2d_fix(orch, grading: str = "", advice=None) -> Decision:
    """
    2D-fix · 必停点。整条链唯一让全自动流程停下来的位置。

    旗舰模型实测会用实质判断覆盖形式规则（标了 K+H 却判 Fixable），
    所以这里的规则化判定不能替代人。
    """
    console.print(f"\n{RULE}")
    console.print(f"[bold red]人工决策点 · 2D-fix[/bold red]   [dim]{_pos('2D-fix')}[/dim]")
    console.print(RULE)

    _show_origin(orch)
    _show_evolution(orch)      # 选项 3 是「整条链重来」，得先知道这条链走了多远
    _show_devil_digest(orch)
    if grading.strip():
        _show_body(grading[:1500], "执笔者的分级判定", "dim")

    console.print(
        "\n[dim]要判的是：这些拆台打中了前提，还是框架内能消化？\n"
        "四个变种场景全部卡在这个位置。想看完整论据输入 p2d。[/dim]"
    )
    _show_advice(advice)
    d = _ask(orch, OPTIONS["2D-fix"])
    d.advice = advice
    return d


def ask_p0_review(orch, gate_detail: str, refined: str) -> Decision:
    """P0 精炼审 · 条件触发。检测到精炼版偏离原意时才叫人。"""
    console.print(f"\n{RULE}")
    console.print(f"[bold yellow]人工决策点 · P0 精炼审[/bold yellow]   [dim]{_pos('P0')}[/dim]")
    console.print(RULE)
    _show_origin(orch)
    _show_body(refined, "② 精炼版", "cyan")
    _show_body(gate_detail, "③ 检测到的偏离", "yellow")
    console.print("\n[dim]P0 做错了后面全错，而且没人会发现——"
                  "因为后面所有步骤都以它为准。[/dim]")
    return _ask(orch, [
        ("1", "accept", "偏离可接受，继续"),
        ("2", "revise", "重新精炼（下一步写要求）"),
    ])


def ask_scope_creep(orch, gate_detail: str, critique_file: str) -> Decision:
    """
    范围扩大化 · 条件触发。

    原型是决策模拟器那次：critic 只说「双语同口径没先例」，执笔者把整个英文版
    砍了。两次都是人拦下来的，而**归档产物里看不出这件事发生过**。
    """
    console.print(f"\n{RULE}")
    console.print("[bold yellow]人工决策点 · 修改超出了批判范围[/bold yellow]")
    console.print(RULE)
    _show_origin(orch)
    _show_evolution(orch)
    _show_body(gate_detail, "③ 检测到的超范围删减", "yellow")
    console.print("\n[dim]批判攻击的是某个属性，不一定是这个东西本身。"
                  "问一句：有没有改法能保留它、同时消除批判指出的问题？[/dim]")
    return _ask(orch, [
        ("1", "accept", "删得对，批判确实指向这个东西本身"),
        ("2", "keep-more", "删过头了，我指定要保留什么"),
    ])
