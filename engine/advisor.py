"""
两仪论工作流 · 旗舰模型顾问环

2026-09-04 第一条 HITL 链暴露的问题：使用者看完改进后的界面，仍然判断不出
v1 和 v3 的本质区别。他把材料喂给 GPT-5.6 和 Claude Opus 5，两个都独立指出
「不能拿沉默推断闲置」，他把其中一份逐字粘了进去。

这件事有两个结论，方向相反：

**一、顾问是对的。** 方法论自己的 2026-08-27 修订写着「是否回退，AI 自主判断
的质量并不差」，实测记录里 AI 自判 2C 四次全对。两个旗舰模型的表现证实了这点。
决策成本从 45 分钟降下来，是真收益。

**二、但记录里分不出「认真读了同意」和「模型说了我就接受」。** 这是「反滑坡
规则」（注意力耗尽）和观察 17（判断依据缺失）之外的第三种滑坡形态：判断被外部
权威代劳。它比前两种隐蔽——前两种人心里知道自己没判断，这一种人会真心觉得
「这就是我的判断」。

所以顾问环给的是一个**参照系**：没有它，「人做了决定」不可证伪；有了它，
「人的决定相对两位顾问偏在哪」至少可以记录。

【2026-09-08 更正】这里原来写的是「把「人有没有价值」变成可验证命题的**唯一
办法**」。那句是过度主张，两个外部模型独立指出了同一点：受控分支对照（同一
中间状态分出「规则自动 / 顾问+AI 决策 / 顾问+人决策」三支）就是另一种办法，
而且比顾问环干净——它能把「人的判断」和「多跑一轮生成」分开，顾问环分不开。

更要紧的是：**与顾问不同不证明人有价值，与顾问一致也不证明人在走过场。**
这两个字段（concur / verbatim_paste）记的是位置，不是价值。任何拿它们直接
论证「人有没有用」的说法，都超出了它们能承载的东西。

Wenbo 的旗舰额度是网页订阅不是 API，所以这一环必须人工粘贴：引擎写材料包 →
他贴进 ChatGPT 和 Claude → 把两份回答贴回来。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .digest import DIGEST_MODEL, PROMPT_DIR, version_diff
from .gate import _ask_json

# 每个决策点要顾问回答的问题。措辞和 interact.py 里给人看的判据保持一致 ——
# 两边问的必须是同一个问题，否则顾问答的和人判的不是一回事。
QUESTIONS = {
    "2C-rollback": (
        "这份方案从最初的想法演化到现在，有没有偏离它最初要解决的问题？\n\n"
        "判据是「这偏离了我最初要解决的问题吗」，**不是「哪个设计更好」**。"
        "方案在批判下变得更严谨、更具体，那是改进不是漂移；但如果产品的身份、"
        "核心承诺、目标用户发生了转移，而这个转移不是有意为之的，那就该回退。"
    ),
    "2D-fix": (
        "这些拆台论据打中的是方案的**前提**，还是**框架内能消化**的实施问题？\n\n"
        "打中前提意味着方向本身错了，得推翻重来；框架内的问题可以通过加机制、"
        "调阈值、收窄措辞来消化，不需要推翻方向。"
    ),
}

# 材料包里要带哪些批判原文
CRITIQUE_OF = {
    "2C-rollback": ("P2C-review.md", "方向漂移诊断"),
    "2D-fix": ("P2D-devils-advocate.md", "拆台论据"),
}

_VERSIONS = ["idea-v1.md", "idea-v2.md", "idea-v3.md", "idea-v4.md"]


@dataclass
class Advice:
    a_text: str = ""
    b_text: str = ""
    a_choice: str = ""
    b_choice: str = ""
    brief_path: str = ""
    cost_usd: float = 0.0
    ok: bool = False

    @property
    def advisors_agree(self) -> bool:
        return bool(self.a_choice) and self.a_choice == self.b_choice


def build_brief(orch, position: str, options: list[tuple[str, str, str]]) -> str:
    """
    生成自包含材料包。

    「自包含」是硬要求：这份东西要被整份贴进网页，没有追问的机会，也不该需要
    人自己补充说明。缺一块，顾问就在信息不全的情况下作答。

    两个排版决定，都是看了第一版真实产出之后改的：

    **一、嵌入文档用分隔线围起来，不靠 markdown 标题分层。** 第一版直接把批判
    原文和方案全文拼进来，结果嵌入文档自带的 `## 一、`『## 五、』和材料包自己
    的章节编号撞在同一层级 —— 9000 字里出现两个「## 五、」，一个是方案的
    「主要风险与应对」，一个才是真正要回答的问题。

    **二、问题和选项在开头、结尾各出现一次。** 中间隔着几千字的材料，只在末尾
    问一次，读到那里时开头的任务描述已经很远了。
    """
    fence = "═" * 60
    ask = [QUESTIONS[position], "", "**请从这三个里选一个：**", ""]
    for key, _name, desc in options:
        ask.append(f"{key}. {desc}")
    ask_block = "\n".join(ask)

    def wrap(title: str, body: str) -> str:
        return (f"\n{fence}\n【{title}】以下到下一条分隔线为止，都是这份材料的原文\n"
                f"{fence}\n\n{body.strip()}\n\n{fence}\n【{title} 结束】\n{fence}\n")

    parts: list[str] = []
    parts.append("# 请你替我做一个判断\n\n")
    parts.append(
        "下面是一个产品想法在一条多 AI 协作流程里演化的完整记录。\n"
        "请你站在**提出这个想法的人**的位置上判断。\n\n"
        "先看要判断什么，再看材料：\n\n"
    )
    parts.append(ask_block)
    parts.append("\n\n---\n\n# 材料\n")

    parts.append("\n## 一、我最初的想法\n")
    parts.append(wrap("最初的想法", orch.scenario.seed))

    parts.append("\n## 二、方案怎么走到现在\n\n")
    present = [v for v in _VERSIONS if orch.has_artifact(v)]
    short = lambda f: f.replace("idea-", "").replace(".md", "")
    for a, b in zip(present, present[1:]):
        d = version_diff(orch.read_artifact(a), orch.read_artifact(b))
        parts.append(f"- **{short(a)} → {short(b)}**："
                     f"{d.change if d.ok else '（摘要生成失败，见下方全文）'}\n")

    fname, label = CRITIQUE_OF[position]
    parts.append(f"\n## 三、{label}\n")
    parts.append(wrap(label, orch.read_artifact(fname)))

    if present:
        cur = present[-1]
        parts.append(f"\n## 四、方案现在的样子（{short(cur)}）\n")
        parts.append(wrap(f"{short(cur)} 全文", orch.read_artifact(cur)))

    parts.append("\n---\n\n# 现在请回答\n\n")
    parts.append(ask_block)
    parts.append(
        "\n\n**请先明确说你选几，再说理由。**如果选 2 或 3，请具体说明要回退或"
        "保留哪些地方，不要只说原则。\n"
    )
    return "".join(parts)


def extract_choice(advice_text: str,
                   options: list[tuple[str, str, str]]) -> tuple[str, float]:
    """
    从建议正文里抽出它实际主张选哪个。

    用 gpt-5.6-luna 而不是推理模型 —— 这是结构化抽取任务，CLAUDE.md 的选型
    纪律对这类任务写得很死：绝不能用推理模型（deepseek-v4-flash 处理同类任务
    曾经思考 16001 token 还不出内容）。
    """
    opts = "\n".join(f"{k}. {d}" for k, _n, d in options)
    prompt = (PROMPT_DIR / "digest_advisor_choice.md").read_text(encoding="utf-8") \
        .replace("{options}", opts).replace("{advice}", advice_text)
    data, cost = _ask_json(prompt, DIGEST_MODEL, max_tokens=2000)
    if not data:
        return "unknown", cost
    return str(data.get("选项", "unknown")).strip() or "unknown", cost


def run_advisor_loop(orch, position: str,
                     options: list[tuple[str, str, str]]) -> Advice:
    """
    写材料包 → 提示粘贴 → 收两份建议 → 各自抽取主张。

    收不到建议（两份都空）时返回 ok=False，调用方应当照常让人裸判 ——
    顾问环失败不该挡住决策点。
    """
    from .interact import _read_multiline, console
    from rich.panel import Panel

    brief = build_brief(orch, position, options)
    name = f"advisor-brief-{position}.md"
    orch.write_artifact(name, brief)
    path = orch.artifacts_dir / name      # 产物按轮分目录；原来少了 round-N/ 一层，打印的路径并不存在

    console.print(Panel(
        f"材料包已生成：[bold]{path}[/bold]\n\n"
        f"把这份文件**整份**贴进 ChatGPT 和 Claude，各自拿一份回答回来。\n"
        f"它是自包含的，不需要你再补充说明。",
        title="[bold]顾问环[/bold]", border_style="magenta", expand=False,
    ))

    a = _read_multiline("粘贴 顾问 A（ChatGPT）的回答：")
    b = _read_multiline("粘贴 顾问 B（Claude）的回答：")

    if not (a or b):
        console.print("[yellow]两份建议都是空的，跳过顾问环，按你自己的判断来。[/yellow]")
        return Advice(brief_path=str(path))

    cost = 0.0
    ac, c1 = extract_choice(a, options) if a else ("unknown", 0.0)
    bc, c2 = extract_choice(b, options) if b else ("unknown", 0.0)
    cost += c1 + c2

    return Advice(a_text=a, b_text=b, a_choice=ac, b_choice=bc,
                  brief_path=str(path), cost_usd=cost, ok=True)
