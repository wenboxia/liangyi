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


class Orchestrator:
    def __init__(
        self,
        scenario: Scenario,
        *,
        profile: str = "primary",
        hitl: str = "off",
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
        self.hitl = hitl
        self.pool = WindowPool(profile)

        # 整条链最重要的一个输出：2D-fix 判的是「框架内改」还是「回 P1 重做」。
        # 之前它只活在两个地方——终端日志（在 /tmp，迟早被清）和 markdown 正文
        # 里的一句中文。run.json 的 status 一律写 completed，于是按 status 做
        # 汇总的脚本会把「回 P1」那条也算成正常完成，五条链的核心差异被抹平。
        self.verdict: str | None = None

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
        self.artifacts_dir = self.run_dir / "artifacts"
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)

        self.trace = Trace(
            self.run_dir,
            meta={
                "scenario_id": scenario.id,
                "scenario_name": scenario.name,
                "profile": profile,
                "hitl": hitl,
                "label": label,
                "windows": {
                    wid: self.pool._resolve(wid, profile).id for wid in WINDOWS
                },
            },
        )
        (self.run_dir / "scenario.yaml").write_text(
            yaml.safe_dump(
                {
                    "id": scenario.id, "name": scenario.name, "seed": scenario.seed,
                    "role_a": scenario.role_a, "stance_a": scenario.stance_a,
                    "role_b": scenario.role_b, "stance_b": scenario.stance_b,
                    "tension": scenario.tension,
                },
                allow_unicode=True, sort_keys=False,
            ),
            encoding="utf-8",
        )

    # ---- 产物读写 ----

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
            values["fix_round"] = "1"

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
        if self.hitl == "advised" and pos in interact.OPTIONS:
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
            )
            return self.read_artifact(step.output)

        raw = self._call_step(step)
        completion = self._last_completion

        if step.id == "P1.0":
            raw = self._adopt_generated_roles(raw, step)

        # 人工决策点
        if step.decision_point and enabled(self.hitl, step.decision_point):
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
            # 它只在 --hitl full 下才跑，而我们不打算跑 full —— 于是 full 的
            # 必要性无法验证，等于把一个没执行过的功能摆在那。
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
                    trigger_reason=f"HITL 档位 {self.hitl} 未启用此决策点",
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
            self.verdict = "back-to-p1" if back else "produced-v5"
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

    def pending(self) -> list[Step]:
        """还没跑的步骤。"""
        return [s for s in CHAIN if not self.has_artifact(s.output)]

    def run_baseline(self) -> str:
        """跑 v0 基线 —— 单 AI 一次性出方案。"""
        return self.execute(BASELINE)

    def run_chain(self, on_step=None) -> None:
        for step in self.pending():
            if on_step:
                on_step(step)
            self.execute(step)

    def finish(self, status: str = "completed") -> None:
        extra = {"windows": self.pool.summary()}
        # 续跑时链可能还没走到 2D-fix，这时别把已有的判定覆盖成 null
        if self.verdict is not None:
            extra["verdict"] = self.verdict
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
