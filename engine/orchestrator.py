"""
两仪论工作流 · 编排器

确定性执行。按 steps.CHAIN 的顺序跑，不做任何临场决定——下一步是什么、
用哪个窗口、读哪些文件，全部在 steps.py 里写死了。

编排器只负责四件事：组装 prompt、调窗口、存产物、记 trace。
"""

from __future__ import annotations

import re
from dataclasses import dataclass, replace
from datetime import datetime
from pathlib import Path

import yaml

from .config import REPO_ROOT, WINDOWS, check_hard_rules, describe_profile
from .gate import GateResult, check_p0_fidelity, check_scope_creep, enabled
from .steps import BASELINE, CHAIN, Step
from .trace import Trace
from .window import WindowPool

PROMPT_DIR = Path(__file__).resolve().parent / "prompts"

# fix 类步骤用它分隔「决策日志」与「产品方案」。见 _split_and_store 的说明。
IDEA_SEPARATOR = "---IDEA-BELOW---"

# 必停点：位置本身就是边界判断，内容如何都要人来定。
# 条件触发点（P0-review / scope-creep）由 gate.py 的检测器决定停不停。
MUST_STOP = {"2C-rollback", "2D-fix"}


class HardRuleViolation(RuntimeError):
    """方法论硬规则未通过 —— 不允许开跑。"""


class BackToP1(RuntimeError):
    """人在 2D-fix 判定前提错了，要回 P1 重做。

    这是整条链唯一的「往回走」出口。四次变种实验全部卡在这个位置——
    它不是异常，是方法论设计里预留的一条合法路径。
    """


@dataclass
class Scenario:
    id: str
    name: str
    seed: str
    # 角色可以不写 —— 不写就由 P1.0 步骤自动生成。
    # 写死是为了让 Phase E 的实验可复现；自动生成是为了 Web 上的自由输入。
    role_a: str = ""
    stance_a: str = ""
    role_b: str = ""
    stance_b: str = ""
    tension: str = ""
    note: str = ""

    @property
    def has_roles(self) -> bool:
        return bool(self.role_a and self.stance_a and self.role_b and self.stance_b)

    def adopt_roles(self, data: dict) -> None:
        """采用 P1.0 生成的角色。"""
        for k in ("role_a", "stance_a", "role_b", "stance_b", "tension"):
            if data.get(k):
                setattr(self, k, str(data[k]).strip())

    @classmethod
    def load(cls, path: Path) -> "Scenario":
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        return cls(**data)

    def as_dict(self) -> dict:
        return {
            "seed": self.seed,
            "role_a": self.role_a,
            "stance_a": self.stance_a,
            "role_b": self.role_b,
            "stance_b": self.stance_b,
        }


# ---------------------------------------------------------------- 路由

# 出口，从六次手工实验里反推出来的三种真实决定
EXIT_BACK_P1 = "back-to-p1"       # 方向被推翻，整链重跑（Agent 评测 R2、ExamSniper X/Y R2）
EXIT_BACK_P2 = "back-to-p2"       # 「v5 还需验证」，只重压 P2 链条（人生决策 R2）
EXIT_DEADLOCK = "structural-deadlock"   # 重跑也撞同一堵墙（美团：「死循环是结构性的」）
EXIT_DONE = "done"

# 两道闸
MAX_ROUNDS = 2          # 既有终止条件；实测触发 3 次，项目史上从无第 3 轮
MAX_BUDGET_USD = 3.0    # 单链实测 $1.2，两轮约 $2.4。参照大厂「生产环境设预算」实践

# K 占比阈值 —— 判「方向可能错了但没被证死」。
#
# 【诚实说明】这条线是在 5 条链上定的：subscription-manager 的 K 占比 100%
# （5 条论据全指着核心前提打，但 H 级零条 → 0 kill shot → 产出 v5），
# 其余三条是 17% / 40% / 17%。60% 把它们干净分开。
# 但 n=5，属于小样本上定的阈值，**不是有理论依据的数**。
# 跑够 10 条再回看要不要调。
K_RATIO_THRESHOLD = 0.60

# 议题重叠阈值 —— 判「重跑无效」。
# 来源：longterm-and-reference.md 实测 Round 1 vs Round 2「60% 底层重叠」，
# 而美团那次的结论是「P2D-fix 死循环是结构性的」。
OVERLAP_THRESHOLD = 0.60

# 分级表的数据行 —— **靠内容认，不靠格式认**。
#
# 一行是数据行，当且仅当它同时含有一个「具体性」格（H/M）和一个「严重度」格（K/F）。
# 表头（| 论据 | 具体性 | 严重度 |）和分隔行（|---|---|）都不满足，自然被排除。
#
# 这条判据是被同一类 bug 咬了四次之后才定下来的。前三版都在赌模型的格式：
#   1. 靠「这行没有『论据摘要』四个字」排表头 → 模型写「论据」，表头被数成第 1 条论据
#   2. 靠第一格是阿拉伯数字认数据行 → 两条链用「一二三四五」编号，整张表数成 0 条
#   3. 靠标签列字面写着「Kill shot」数致命论据 → 模型写「K+M」「H+F」，数出 0 个
#   4. 靠第一格是**纯**数字 → 模型把序号和论据挤进同一格（「| 1. "忘了"这个前提错误 |」），
#      整张表又数成 0 条。这次代价最大：模型正确判出 2 个致命论据、写明回 P1，
#      **路由看到 0 行直接放行**，第二轮没启动 —— 循环本来要解决的
#      「系统产出了一个它无法执行的判定」，从解析的缝里漏了回来。
#
# p2d_fix.md 只约定了表要有哪几列，从没约定过序号怎么写、标签怎么措辞。
# **能依赖的只有模型填进那两个格子里的内容。**
_TABLE_ROW = re.compile(r"^\s*\|.*\|")
# 格子可能是「H（可核查的反例）」，也可能光写一个「H」。
# 契约写的是 H/M 和 K/F，但模型会自己发明档位（实测出现过 L「泛泛断言」）。
# 多认几种写法，判 kill shot 时只有 H / 高 算「具体性高」。
_SPEC = re.compile(r"^\**([HML]|高|中|低)\**\s*(?:[（(]|$)")
_SEV = re.compile(r"^\**([KF]|框架|框架级|可修)\**\s*(?:[（(]|$)")
_HIGH = {"H", "高"}
_FRAME = {"K", "框架", "框架级"}


def _grade_row(line: str) -> tuple[str, str] | None:
    """一行分级表 → (具体性, 严重度)。不是数据行就返回 None。"""
    if not _TABLE_ROW.match(line):
        return None
    cells = [c.strip() for c in line.strip().strip("|").split("|")]
    spec = next((m.group(1) for c in cells if (m := _SPEC.match(c))), "")
    sev = next((m.group(1) for c in cells if (m := _SEV.match(c))), "")
    return (spec, sev) if spec and sev else None


def parse_grading(text: str) -> tuple[int, int, int]:
    """
    从 2D-fix 的分级表里数出 (论据数, K 级数, kill shot 数)。

    kill shot = 框架级（K）+ 具体性高（H），由这两格**算**出来，
    不认标签那一列的字面 —— 见上面 _TABLE_ROW 那段。
    """
    seg = text[text.rfind("分级表"):] if "分级表" in text else text
    graded = [g for line in seg.splitlines() if (g := _grade_row(line))]
    K = sum(1 for spec, sev in graded if sev in _FRAME)
    ks = sum(1 for spec, sev in graded if sev in _FRAME and spec in _HIGH)
    return len(graded), K, ks


def grading_anomalies(text: str) -> list[str]:
    """
    分级表里**看着像数据行、却没能分级**的行。

    存在的理由：前四次踩的坑全都是「静默数少了」—— 表还在、内容也对，
    解析漏掉了，路由拿到一个偏小的数就照常放行，不报错。
    格式还会变，所以与其追格式，不如让漏掉这件事**出声**。
    """
    seg = text[text.rfind("分级表"):] if "分级表" in text else text
    out = []
    for line in seg.splitlines():
        if not _TABLE_ROW.match(line) or _grade_row(line):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 3 or all(set(c) <= set("-: ") for c in cells):
            continue                      # 分隔行
        if any(c in ("论据", "论据摘要", "具体性", "严重度", "标签", "#", "编号") for c in cells):
            continue                      # 表头
        out.append(line.strip()[:120])
    return out


def route(raw: str, round_no: int, overlap: float | None = None) -> tuple[str, str]:
    """
    2D-fix 之后走哪个出口。返回 (出口, 一句话理由)。

    **路由由代码按规则做，不由 AI 自由裁量。** 理由是实测出来的：同一份输入
    让检测器判四次得到 True/True/True/False，加 temperature=0 仍然 3/4。
    一个会翻的路由器会让 loop 不可复现，而可复现是消融实验的前提。

    AI 负责的是产出信号（分级表、议题重叠度），代码负责按规则路由 ——
    这也符合方法论自己的判据：边界决策可以「设计时由人做完、用规则消化掉」，
    前提是规则由人在系统外设计。这张路由表就是那条规则。
    """
    total, K, ks = parse_grading(raw)
    k_ratio = K / total if total else 0.0

    if ks >= 2:
        if round_no < MAX_ROUNDS:
            return EXIT_BACK_P1, f"{ks} 个 kill shot，方向被推翻"
        if overlap is not None and overlap >= OVERLAP_THRESHOLD:
            return EXIT_DEADLOCK, f"第 {round_no} 轮仍 {ks} 个 kill shot，议题重叠 {overlap:.0%}，重跑无效"
        return EXIT_DONE, f"第 {round_no} 轮，终止条件兜底强制产出 v5"

    if round_no == 1 and k_ratio >= K_RATIO_THRESHOLD:
        return EXIT_BACK_P2, f"K 占比 {k_ratio:.0%}（{K}/{total}）但 kill shot 仅 {ks} —— 方向可能错了但没被证死"

    return EXIT_DONE, f"{ks} 个 kill shot、K 占比 {k_ratio:.0%}，框架内消化"


# ---------------------------------------------------------------- 编排器

class Orchestrator:
    def __init__(
        self,
        scenario: Scenario,
        *,
        profile: str = "primary",
        mode: str = "auto",
        run_root: Path | None = None,
        label: str = "",
        resume_dir: Path | None = None,
    ):
        violations = check_hard_rules(profile)
        if violations:
            raise HardRuleViolation(
                "方法论硬规则未通过，拒绝开跑：\n  " + "\n  ".join(violations)
            )

        self.scenario = scenario
        self.profile = profile
        # 旧运行目录存的是老档位名（off/minimal/advised/full），续跑时映射过来
        from .gate import LEGACY_MODES
        self.mode = LEGACY_MODES.get(mode, mode)
        self.pool = WindowPool(profile)

        # 整条链最重要的一个输出：2D-fix 判的是「框架内改」还是「回 P1 重做」。
        # 之前它只活在两个地方——终端日志（在 /tmp，迟早被清）和 markdown 正文
        # 里的一句中文。run.json 的 status 一律写 completed，于是按 status 做
        # 汇总的脚本会把「回 P1」那条也算成正常完成，五条链的核心差异被抹平。
        self.verdict: str | None = None
        self.verdicts: list[str] = []       # 每轮一个
        self.exit_reason: str = ""
        self.exit_code: str = EXIT_DONE

        if resume_dir is not None:
            # 用户在命令行传的多半是相对路径，统一 resolve —— 否则后面
            # relative_to(REPO_ROOT) 会炸（resume 首次真实使用时踩到的）
            resume_dir = Path(resume_dir).resolve()
            self.run_dir = resume_dir
            if not (resume_dir / "artifacts").exists():
                raise FileNotFoundError(f"{resume_dir} 不像一个运行目录（缺 artifacts/）")
        else:
            stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            suffix = f"-{label}" if label else ""
            root = run_root or (REPO_ROOT / "runs")
            self.run_dir = root / f"{stamp}-{scenario.id}{suffix}"
        # 轮次。产物按轮分目录 —— 这是 loop 能成立的前提。
        #
        # 不分目录的话，第二轮跑 P1 时 idea-v1.md 已经存在，pending() 会把它
        # 当成「已完成」直接跳过：「第二轮重跑 P1」和「第一轮没跑完」，
        # 系统分不出来。分了目录之后每轮目录一开始是空的，
        # pending() / restore() 的逻辑一个字都不用改。
        self.round = 1
        (self.run_dir / "artifacts").mkdir(parents=True, exist_ok=True)
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)

        self.trace = Trace(
            self.run_dir,
            meta={
                "scenario_id": scenario.id,
                "scenario_name": scenario.name,
                "profile": profile,
                "mode": self.mode,
                "label": label,
                "windows": {
                    wid: self.pool._resolve(wid, profile).id for wid in WINDOWS
                },
            },
        )
        self._dump_scenario()

    # ---- 产物读写 ----

    @property
    def artifacts_dir(self) -> Path:
        """当前轮的产物目录。单轮运行也走 round-1/，不做特例。"""
        return self.run_dir / "artifacts" / f"round-{self.round}"

    def start_round(self, n: int) -> None:
        """进入第 n 轮：切目录、开全新窗口。"""
        self.round = n
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)
        # 第二轮所有窗口新开 —— 沿用历史三次 round-2 的做法（"所有窗口新开"）。
        # 理由不是底线规则要求（ZeroContextViolation 拦不住跨轮复用，它只在
        # inject_history() 里抛，而这里从不调那个方法），而是避免执笔窗口
        # 带着上一轮的记忆写新方案。
        self.pool = WindowPool(self.profile)

    def _dump_scenario(self) -> None:
        """
        把场景（含角色）写进运行目录。

        **P1.0 生成角色之后必须再调一次。** 原来只在 __init__ 里写一次，那时角色
        还是空的；P1.0 的 adopt_roles 只改内存对象，从不写回文件。于是任何
        auto-roles 的运行一续跑，Scenario.load 读回来的 role_a / stance_a 全是空串，
        专家 A/B 的提示词里角色和立场就是空的 —— voyageguard 那条正是 auto-roles，
        续跑过一次都没发现，因为它恰好没重跑 P1A/P1B。
        访客入口每一条都是 auto-roles，这个 bug 会直接把它卡死。
        """
        sc = self.scenario
        (self.run_dir / "scenario.yaml").write_text(
            yaml.safe_dump(
                {
                    "id": sc.id, "name": sc.name, "seed": sc.seed,
                    "role_a": sc.role_a, "stance_a": sc.stance_a,
                    "role_b": sc.role_b, "stance_b": sc.stance_b,
                    "tension": sc.tension,
                },
                allow_unicode=True, sort_keys=False,
            ),
            encoding="utf-8",
        )

    def _seed_back_to_p2(self) -> None:
        """
        出口 B（回 P2）：把 P0/P1 的产物原样带进新一轮，只让 P2 链条重跑。

        **不带的话 P0、P1A、P1B 会被白跑一遍。** pending() 是按「产物文件存不存在」
        判进度的，新一轮目录一开始是空的；只写 idea-v1.md 的话，那三步的产物不存在
        → 全部重跑，而消费它们的 P1.4 因为 idea-v1.md 已存在反而被跳过。
        结果是重新生成的两份专家方案根本不会被用上 —— 白花钱，还在 trace 里留下
        「像是重做了 P1」的误导记录。

        出口 B 的语义是「方向没被推翻、只是没压够」，所以 P0 精炼和 P1 双专家方案
        本来就该原样留着，重跑的只有 P2 那四轮批判。
        """
        prev_dir = self.run_dir / "artifacts" / f"round-{self.round - 1}"
        for name in ("P0-refined.md", "P1-roles.yaml",
                     "P1A-expert-a.md", "P1B-expert-b.md"):
            src = prev_dir / name
            if src.exists():
                self.write_artifact(name, src.read_text(encoding="utf-8"))
        # 上一轮的 v5 逐字成为本轮的 v1 —— 人生决策那次实测 diff 0 行差异
        self.write_artifact(
            "idea-v1.md", (prev_dir / "idea-v5.md").read_text(encoding="utf-8"))

    def read_artifact(self, name: str) -> str:
        return (self.artifacts_dir / name).read_text(encoding="utf-8")

    def write_artifact(self, name: str, content: str) -> None:
        (self.artifacts_dir / name).write_text(content, encoding="utf-8")

    def has_artifact(self, name: str) -> bool:
        return (self.artifacts_dir / name).exists()

    def _change_log(self) -> str:
        """
        合成给 P2C 的修改历史。

        P2C 的「知情」必须来自输入的材料，不来自参与过讨论——这两者的区别
        就是 P2C 能不能中立的区别。所以这里把前两轮的批判原文喂给它，
        让它自己看出「改动是为了响应什么」。
        """
        parts = []
        for label, fname in (
            ("第一轮 · 投资人批判", "P2A-critique.md"),
            ("第二轮 · 零上下文单盲反馈", "P2B-blind-review.md"),
        ):
            if self.has_artifact(fname):
                parts.append(f"### {label}\n\n{self.read_artifact(fname)}")
        return "\n\n---\n\n".join(parts) if parts else "（无）"

    # ---- 执行 ----

    def _build_prompt(self, step: Step) -> str:
        template = (PROMPT_DIR / step.prompt).read_text(encoding="utf-8")
        values: dict[str, str] = {}

        for var, source in step.artifacts.items():
            if source == "__change_log__":
                values[var] = self._change_log()
            else:
                values[var] = self.read_artifact(source)

        scenario_data = self.scenario.as_dict()
        for fname in step.scenario_fields:
            values[fname] = scenario_data[fname]

        if step.id == "2D-fix":
            values["fix_round"] = str(self.round)

        # 用 format_map 而不是 format —— 产物里可能带花括号，不能让它们被当成占位符
        class _Safe(dict):
            def __missing__(self, key):  # noqa: D105
                return "{" + key + "}"

        return template.format_map(_Safe(values))

    def _split_and_store(self, step: Step, raw: str) -> tuple[str, str]:
        """
        把 fix 类步骤的产出拆成「决策日志」和「产品方案」，分别落盘。

        为什么必须拆：docs 第七章要求 idea.md 与 decision-log **物理分离**——
        「如果保留决策痕迹，审查者会陷入『评价你的选择』而不是『评价产品本身』」。

        这不是理论洁癖，是实测踩到的。第一版实现把两部分写进同一个 idea-v2.md，
        文件以「# 批判响应日志」开头。结果 P2B 单盲读完的批准理由是
        「文档对 7 个批判点做了具体且逻辑自洽的回应」——它在评价修改过程，
        不是在评价产品。方法论预言的失败模式被一字不差地复现了。

        注意执笔窗口的历史里保留的是**完整产出**（含日志）——作者该记得自己
        的推理；被切掉的只是传给下游审查者的那份。
        """
        if IDEA_SEPARATOR not in raw:
            return raw, ""

        log_part, idea_part = raw.split(IDEA_SEPARATOR, 1)
        log_part, idea_part = log_part.strip(), idea_part.strip()

        entry = f"\n\n## {step.id}（→ {step.output}）\n\n{log_part}\n"
        path = self.run_dir / "decision-log.md"
        if not path.exists():
            path.write_text(
                f"# Decision Log · {self.scenario.name}\n\n"
                f"> 每个 fix 步骤的取舍理由。与 idea.md 物理分离——"
                f"审查者只该看到产品本身，不该看到修改痕迹。\n",
                encoding="utf-8",
            )
        with path.open("a", encoding="utf-8") as fh:
            fh.write(entry)

        return idea_part, log_part

    # ---- 人工决策点 ----

    def _run_gate(self, step: Step, content: str) -> GateResult:
        """条件触发点的检测。必停点不需要检测，直接停。"""
        pos = step.decision_point
        if pos == "P0-review":
            return check_p0_fidelity(self.scenario.seed, content)
        if pos == "scope-creep":
            critique_file = step.artifacts.get("critique")
            before_file = step.artifacts.get("idea")
            if not (critique_file and before_file):
                return GateResult(pos, False, "缺少对照材料，放行")
            return check_scope_creep(
                self.read_artifact(critique_file), self.read_artifact(before_file), content
            )
        return GateResult(pos or "?", False, "该位置无检测器")

    def _ask_human(self, step: Step, content: str, gate: GateResult):
        """把决定权交回给人。界面自带上下文——见 interact.py 的说明。"""
        from . import interact

        pos = step.decision_point

        # advised 档位：先跑顾问环，把两份旗舰模型的建议摆出来，再问人。
        # 顾问环失败（两份都空、抽取出错）不挡决策点 —— 人照常裸判。
        advice = None
        if self.mode == "hitl" and pos in interact.OPTIONS:
            from . import advisor
            try:
                advice = advisor.run_advisor_loop(self, pos, interact.OPTIONS[pos])
            except Exception as exc:
                interact.console.print(f"[yellow]顾问环出错，跳过：{exc}[/yellow]")

        if pos == "2C-rollback":
            return interact.ask_rollback(self, advice=advice)
        if pos == "2D-fix":
            grading = content.split(IDEA_SEPARATOR)[0] if IDEA_SEPARATOR in content else content
            return interact.ask_2d_fix(self, grading, advice=advice)
        if pos == "P0-review":
            return interact.ask_p0_review(self, gate.detail, content)
        if pos == "scope-creep":
            return interact.ask_scope_creep(
                self, gate.detail, step.artifacts.get("critique", "")
            )
        return None

    def _call_step(self, step: Step, extra: str = "") -> str:
        """跑一步。extra 是人给的补充指令，会附在 prompt 末尾。"""
        window = self.pool.get(step.window)
        prompt = self._build_prompt(step)
        if extra:
            prompt += (
                f"\n\n---\n\n【使用者的补充指令 —— 优先级高于上面的任何要求】\n{extra}\n"
            )
        completion = window.ask(
            prompt, max_tokens=step.max_tokens, remember=step.remember
        )
        self._last_completion = completion
        return completion.content

    def _adopt_generated_roles(self, raw: str, step: Step, attempt: int = 1) -> str:
        """
        解析 P1.0 生成的角色，校验张力是真的，然后采用。

        假对立是这一步最容易犯的错，而且**从产物上看不出来**——两份专家方案
        照样写得头头是道，只是不会真的打架，P1 的 divergence 是虚的。
        所以生成完必须校验：能不能构造出一个让两者答案相反的具体决策问题。

        判假就重生成一次，把上一次的失败原因作为约束喂回去。只重试一次——
        再多就该让人来看了。
        """
        from .gate import check_fake_tension

        body = re.sub(r"^```(?:yaml)?|```$", "", raw.strip(), flags=re.M).strip()
        try:
            data = yaml.safe_load(body) or {}
        except yaml.YAMLError:
            data = {}
        if not all(data.get(k) for k in ("role_a", "stance_a", "role_b", "stance_b")):
            raise RuntimeError(f"P1.0 产出无法解析成角色定义：\n{raw[:400]}")

        gate = check_fake_tension(
            data["role_a"], data["stance_a"], data["role_b"], data["stance_b"],
            str(data.get("tension", "")),
        )
        self.trace.record_decision(
            step_id=step.id, position="fake-tension",
            mode="auto-regenerate" if (gate.triggered and attempt == 1) else "auto-passed",
            triggered=gate.triggered, trigger_reason=gate.reason,
            rationale=gate.detail,
            round=self.round,
        )

        if gate.triggered and attempt == 1:
            extra = (
                f"上一次设计的角色被判定为**假对立**，必须重做。\n\n"
                f"判定理由：{gate.reason}\n{gate.detail}\n\n"
                f"这次务必找到一个真正的分岔口：两个角色在同一个具体决策上"
                f"给出相反答案，而且两个答案都站得住。"
            )
            return self._adopt_generated_roles(
                self._call_step(step, extra=extra), step, attempt + 1
            )

        self.scenario.adopt_roles(data)
        self._dump_scenario()   # 角色定了就写回去，续跑才读得到
        return yaml.safe_dump(data, allow_unicode=True, sort_keys=False)

    def execute(self, step: Step) -> str:
        window = self.pool.get(step.window)
        spec = WINDOWS[step.window]

        # P1.0：场景文件已写死角色就跳过 —— 那是为了让实验可复现
        if step.id == "P1.0" and self.scenario.has_roles:
            self.write_artifact(step.output, yaml.safe_dump(
                {k: getattr(self.scenario, k) for k in
                 ("role_a", "stance_a", "role_b", "stance_b", "tension")},
                allow_unicode=True, sort_keys=False))
            self.trace.record_decision(
                step_id=step.id, position="fake-tension", mode="skipped",
                triggered=False, trigger_reason="场景文件已指定角色，未自动生成",
                round=self.round,
            )
            return self.read_artifact(step.output)

        raw = self._call_step(step)
        completion = self._last_completion

        if step.id == "P1.0":
            raw = self._adopt_generated_roles(raw, step)

        # 人工决策点
        if step.decision_point and enabled(self.mode, step.decision_point):
            must = step.decision_point in MUST_STOP
            gate = GateResult(step.decision_point, True, "必停点") if must \
                else self._run_gate(step, raw)

            if gate.triggered:
                decision = self._ask_human(step, raw, gate)
                if decision and decision.choice == "back-to-p1":
                    self.trace.record_decision(
                        step_id=step.id, position=step.decision_point, mode="human",
                        triggered=True, trigger_reason=gate.reason,
                        decision="back-to-p1", rationale=decision.rationale,
                        think_ms=decision.think_ms,
                        advice=decision.advice,
                        human_text=f"{decision.instruction}\n{decision.rationale}",
                        round=self.round,
                    )
                    self.verdict = "back-to-p1"
                    raise BackToP1(decision.rationale or "人判定前提错误，回 P1")
                if decision and decision.choice != "accept":
                    raw = self._call_step(step, extra=decision.instruction)
                    completion = self._last_completion
                self.trace.record_decision(
                    step_id=step.id, position=step.decision_point, mode="human",
                    triggered=True, trigger_reason=gate.reason,
                    decision=decision.choice if decision else "accept",
                    rationale=decision.rationale if decision else "",
                    think_ms=decision.think_ms if decision else None,
                    advice=decision.advice if decision else None,
                    human_text=(f"{decision.instruction}\n{decision.rationale}"
                                if decision else ""),
                    round=self.round,
                )
            else:
                self.trace.record_decision(
                    step_id=step.id, position=step.decision_point, mode="auto-passed",
                    triggered=False, trigger_reason=gate.reason,
                )
        elif step.decision_point:
            # 影子模式：条件触发点的检测器照跑，只记录，绝不叫人。
            #
            # 起因是一个尴尬的事实：条件触发检测器至今一次都没真正执行过。七次
            # 运行全是 off 或 minimal，trace 里 21 条相关记录全是「档位未启用」。
            # 它原来只在 full 档跑，而 full 档已被砍掉 —— 检测器改成两档都跑，
            # 只记录不打断。
            #
            # 影子模式几乎免费地解决这个问题：_run_gate() 只读 artifact + 调
            # 检测器，不写任何东西；不调 _ask_human() 意味着 off 仍是零人工介入，
            # 消融对照组的有效性零损伤，链条内容和可复现性都不变。代价是每条链
            # 多三次 deepseek-v4-flash 调用。
            #
            # 换来的是：跑完就知道检测器到底会不会响。一次不响，full 就是死重。
            if step.decision_point in MUST_STOP:
                self.trace.record_decision(
                    step_id=step.id, position=step.decision_point, mode="auto-passed",
                    triggered=False,
                    trigger_reason=f"档位 {self.mode} 未启用此决策点",
                    round=self.round,
                )
            else:
                shadow = self._run_gate(step, raw)
                self.trace.record_decision(
                    step_id=step.id, position=step.decision_point, mode="shadow",
                    triggered=shadow.triggered,      # 「本来会不会叫人」，不是「叫了」
                    trigger_reason=shadow.reason,
                    detail=shadow.detail or None,
                )

        idea_part, _ = self._split_and_store(step, raw)

        # 2D-fix 判定回 P1 时不产出方案 —— 那一步的产物是判定本身，
        # 叫 idea-v5.md 会造成「有个 v5」的错觉。
        output_name = step.output
        if step.id == "2D-fix":
            back = detect_p1_return(raw)

            # 代码层硬终止：第 2 轮不论模型判什么，一律强制走框架内修改。
            #
            # p2d_fix.md 里本来就写着这条终止条件，但历史上两次都是靠模型
            # 自己遵守的 —— P2D-fix-judgment.md 里留着模型的原话
            # 「本应回 P1……但因终止条件强制走框架内修改」。规则该由代码保证。
            if back and self.round >= MAX_ROUNDS:
                self.trace.record_decision(
                    step_id=step.id, position="termination-guard", mode="forced",
                    triggered=True,
                    trigger_reason=f"第 {self.round} 轮，代码强制改判为框架内修改",
                    detail="模型判了回 P1，被终止条件兜底覆盖",
                    round=self.round,
                )
                back = False

            self.verdict = "back-to-p1" if back else "produced-v5"
            self.verdicts.append(self.verdict)
            if back:
                output_name = "P2D-fix-judgment.md"

        self.write_artifact(output_name, idea_part)
        step = replace(step, output=output_name) if output_name != step.output else step

        self.trace.record_step(
            step_id=step.id,
            phase=step.phase,
            window=window,
            role=spec.role,
            inputs=list(step.artifacts.values()) or list(step.scenario_fields),
            output_file=step.output,
            completion=completion,
            round=self.round,
        )

        return raw

    def restore(self) -> list[str]:
        """
        断点续跑：跳过已有产物的步骤，但把它们的对话补回窗口历史。

        补历史这一步不能省。执笔窗口在 2A-fix / 2B-fix / 2C-rollback / 2D-fix
        之间是连贯的同一个窗口——「修改必须由同一个执笔者做，否则 idea.md 会
        变成多个 AI 的拼贴」。如果续跑时让它从空白开始，这条纪律就断了。

        返回被跳过的步骤 id。
        """
        skipped: list[str] = []
        for step in CHAIN:
            if not self.has_artifact(step.output):
                break  # 链条是线性的，遇到第一个缺口就停
            if step.remember:
                window = self.pool.get(step.window)
                window.replay(self._build_prompt(step), self.read_artifact(step.output))
            skipped.append(step.id)
        return skipped

    # 一步可能写出不止一个产物名。2D-fix 判「回 P1」时写 P2D-fix-judgment.md，
    # 判「产出 v5」时写 idea-v5.md —— 两者都算这步跑完了。
    ALT_OUTPUTS = {"2D-fix": ("P2D-fix-judgment.md",)}

    def _step_done(self, step: Step) -> bool:
        names = (step.output, *self.ALT_OUTPUTS.get(step.id, ()))
        return any(self.has_artifact(n) for n in names)

    def pending(self) -> list[Step]:
        """
        还没跑的步骤。

        按产物存不存在判，不记进度文件 —— 但产物名不是一步一个：
        2D-fix 判「回 P1」时不产出 idea-v5.md，而是写一份判定书。
        只认 step.output 的话，续跑会把这一步当成没跑过重新跑一遍，
        **而重跑可能给出完全不同的判定**：2026-09-10 那次续跑，
        同一份 v4 的分级从「5 条 K 级、2 条致命」变成「0 条 K 级」，
        判定也从回 P1 翻成产出 v5。续跑本该接着走，不该重掷骰子。
        """
        return [s for s in CHAIN if not self._step_done(s)]

    def run_baseline(self) -> str:
        """跑 v0 基线 —— 单 AI 一次性出方案。"""
        return self.execute(BASELINE)

    def run_chain(self, on_step=None, on_round=None) -> None:
        """
        跑整条链，必要时按路由结果开新一轮。

        两道闸任一触顶就停下报告，不静默继续：
        · MAX_ROUNDS  —— 既有终止条件，实测触发 3 次，项目史上从无第 3 轮
        · MAX_BUDGET  —— 参照大厂「生产环境设预算是个好默认值」的实践
        """
        while True:
            for step in self.pending():
                if on_step:
                    on_step(step)
                self.execute(step)

            exit_code, why = self._decide_next_round()
            self.exit_reason = why
            if exit_code == EXIT_DONE or exit_code == EXIT_DEADLOCK:
                self.exit_code = exit_code
                return

            spent = sum(r.cost_usd for r in self.trace.steps)
            if spent >= MAX_BUDGET_USD:
                self.exit_code = "budget-capped"
                self.exit_reason = f"已花 ${spent:.2f}，触顶 ${MAX_BUDGET_USD}"
                return

            self.start_round(self.round + 1)
            if exit_code == EXIT_BACK_P2:
                self._seed_back_to_p2()
            if on_round:
                on_round(self.round, exit_code, why)

    def _decide_next_round(self) -> tuple[str, str]:
        """看 2D-fix 的产出决定下一轮走哪个出口。"""
        for name in ("P2D-fix-judgment.md", "idea-v5.md"):
            if self.has_artifact(name):
                break
        else:
            return EXIT_DONE, "链未跑到 2D-fix"

        log = (self.run_dir / "decision-log.md")
        raw = log.read_text(encoding="utf-8") if log.exists() else ""
        if self.has_artifact("P2D-fix-judgment.md"):
            raw += self.read_artifact("P2D-fix-judgment.md")

        # 分级表里有看着像数据行却没分上级的 —— 记一笔。
        # 这类漏行会让论据数偏小，路由拿着偏小的数照常放行，不报错。
        # 历史上栽过四次，每次都是「表还在、内容也对，就是没数着」。
        odd = grading_anomalies(raw)
        if odd:
            self.trace.record_decision(
                step_id="2D-fix", position="grading-parse", mode="anomaly",
                triggered=True,
                trigger_reason=f"分级表有 {len(odd)} 行没能分级，论据数可能偏小",
                detail="\n".join(odd), round=self.round,
            )

        return route(raw, self.round)

    def finish(self, status: str = "completed") -> None:
        extra = {"windows": self.pool.summary()}
        # 续跑时链可能还没走到 2D-fix，这时别把已有的判定覆盖成 null
        if self.verdict is not None:
            extra["verdict"] = self.verdict
        if self.verdicts:
            extra["verdicts"] = self.verdicts     # 每轮一个
        extra["rounds"] = self.round
        if self.exit_reason:
            extra["exit_code"] = self.exit_code
            extra["exit_reason"] = self.exit_reason
        self.trace.finish(status=status, extra=extra)

    # ---- 输出 ----

    def describe(self) -> str:
        return describe_profile(self.profile)


def detect_p1_return(text: str) -> bool:
    """
    2D-fix 是否判定了「回 P1 重做」。

    四次变种实验里，这个判定在四个不同场景全部触发——它是唯一让全自动流程
    卡死的位置，也是立场三精确化的证据来源。

    优先读 prompt 要求模型输出的判定标记。**不要靠正则去猜模型说了什么**：
    第一版就是这么写的，结果「本轮不回 P1」被匹配成了「回 P1」——正则看得见
    关键词，看不见否定词。与其猜，不如让模型明确说。

    标记缺失时才退回关键词匹配，且显式排除否定形式。
    """
    head = text[:2000]

    marker = re.search(r"【判定】\s*(回\s*P1|产出\s*v5)", head)
    if marker:
        return "P1" in marker.group(1)

    # 兜底：模型没给标记时的启发式判断
    if re.search(r"(不|无需|不必|毋须)\s*(回到?\s*P1|重做)", head):
        return False
    return bool(re.search(r"(回到?\s*P1|停止产出|无法提供修订版)", head))
