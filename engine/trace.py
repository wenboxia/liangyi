"""
两仪论工作流 · 执行记录

每一步都留下完整痕迹：谁跑的、看到了什么、想了什么、产出了什么、花了多少钱。

「想了什么」是这里最值钱的一栏。手动跑方法论的时候，你只能看到模型的最终输出，
所以「这个批判 agent 是真在批判，还是在敷衍」这个判断一直只能靠读输出内容推断。
抓到推理过程之后，它变成可以直接检验的东西 —— 尤其是拆台那一步，可以拿 A1 和
A3 在同一个任务上的思考过程对照，看「有规范层的底模会在最关键那一刀上把攻击
软化掉」这个论断到底成不成立。

记录格式是 JSONL，一行一步，方便流式追加和事后按行读取。
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path

from .providers import Completion


def _now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


@dataclass
class StepRecord:
    step_id: str
    phase: str
    window: str
    model: str
    coordinate: str
    role: str
    inputs: list[str]
    output_file: str
    content_chars: int
    reasoning: str | None
    reasoning_tokens: int
    tokens_in: int
    tokens_out: int
    cost_usd: float
    duration_ms: int
    attempts: int
    round: int = 1          # 第几轮 —— loop 之后同一个 step_id 会出现多次
    timestamp: str = field(default_factory=_now)
    kind: str = "step"


@dataclass
class DecisionRecord:
    """人工决策点的记录 —— Phase C 用，这里先把结构定下来。"""
    step_id: str
    position: str          # 2C-rollback / 2D-fix / P0-review / scope-creep
    mode: str              # human | auto-passed | auto-skipped
    triggered: bool        # 条件触发的决策点是否真的被触发
    trigger_reason: str | None
    decision: str | None   # 人的决定
    rationale: str | None  # 人给的理由
    # 【这个字段不作为疲劳信号使用 —— 2026-09-07 判定】
    #
    # 原本是想拿它当「反滑坡规则」的外部观测量：人累了会说"你看着办"，而从
    # decision-log 上完全看不出来，记录里只会写"人已确认"。
    #
    # 两个原因让它不成立：
    #
    # 一、量的不是想的时间。计时从「选项显示」到「打出数字」结束，不含读顾问
    #    建议、写指令的时间。2026-09-06 那条链 2C 记了 6 秒，但那 6 秒只是打字。
    #
    # 二、更根本的是使用者自己指出的：跑实验期间他会中途做别的事，不同场次的
    #    注意力状态本来就不同。这个噪声比要测的信号大，测不出疲劳。
    #
    # 字段保留（记录成本为零，且原始耗时本身是事实），但**任何分析和对外叙述
    # 都不得把它当作疲劳或投入程度的证据**。
    think_ms: int | None = None
    # 检测器具体标出了什么。影子模式下这是唯一有价值的内容——
    # 只知道"响了"没用，得知道它指着哪一处说有问题。
    detail: str | None = None

    # ---- 顾问环（advised 档位）----
    # 记这些不是为了评判人，是为了让「人到底加了什么」变成可测量的东西。
    # 没有对照时「人做了决定」不可证伪；有了顾问，「10 次里偏离了 3 次、
    # 这 3 次抓到了 X」才是硬证据。
    advisor_a: str | None = None
    advisor_b: str | None = None
    advisor_a_choice: str | None = None
    advisor_b_choice: str | None = None
    concur: bool | None = None          # 人的选择是否和两位顾问都一致
    verbatim_paste: bool | None = None  # 人的理由是否就是某份建议的原文
    round: int = 1
    timestamp: str = field(default_factory=_now)
    kind: str = "decision"


def _norm(text: str) -> str:
    """比对用的归一化 —— 只留非空白字符。粘贴会带进不同的换行和缩进。"""
    return "".join(text.split())


def _advice_fields(advice, decision: str | None, human_text: str) -> dict:
    """
    把顾问环的结果摊平成记录字段。

    verbatim_paste 的判据：人写的东西归一化之后，和某份建议原文相同，或者是
    它的一大截（长度占比 ≥ 0.8 的包含关系）。2026-09-04 那次就是逐字粘贴，
    但记录里看不出来 —— 事后只能靠回忆还原发生了什么。这个字段不是用来
    judge 人的，是让那种情况**留下痕迹**。
    """
    if advice is None or not getattr(advice, "ok", False):
        return {}

    a, b = advice.a_text or "", advice.b_text or ""
    hn = _norm(human_text)
    verbatim = False
    if hn:
        for src in (a, b):
            sn = _norm(src)
            if not sn:
                continue
            if hn == sn:
                verbatim = True
                break
            longer, shorter = (sn, hn) if len(sn) >= len(hn) else (hn, sn)
            if shorter and shorter in longer and len(shorter) / len(longer) >= 0.8:
                verbatim = True
                break

    return {
        "advisor_a": a or None,
        "advisor_b": b or None,
        "advisor_a_choice": advice.a_choice or None,
        "advisor_b_choice": advice.b_choice or None,
        "concur": (advice.advisors_agree
                   and decision is not None
                   and _choice_key(decision) == advice.a_choice),
        "verbatim_paste": verbatim,
    }


def _choice_key(decision: str) -> str:
    """把 Decision.choice（accept / rollback-more / ...）映回选项编号。"""
    from .interact import OPTIONS
    for opts in OPTIONS.values():
        for key, name, _desc in opts:
            if name == decision:
                return key
    return "unknown"


class Trace:
    """一次运行的完整记录。"""

    def __init__(self, run_dir: Path, meta: dict):
        self.run_dir = run_dir
        self.run_dir.mkdir(parents=True, exist_ok=True)
        self.path = run_dir / "trace.jsonl"

        # 续跑时目录里已经有 run.json，必须保留它——否则上一轮的 status、
        # 总成本、finished_at 会被整个覆盖掉。
        #
        # 这个 bug 是真实踩过的：加完续跑功能后我在真实运行目录上测了一次
        # restore()，只是构造了 Orchestrator、一次 API 都没调，却把那次运行的
        # status 抹了。教训是「只读的测试」也可能有副作用——构造函数里的写操作
        # 不会因为你没调用业务方法就不发生。
        existing: dict = {}
        run_json = run_dir / "run.json"
        if run_json.exists():
            try:
                existing = json.loads(run_json.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                existing = {}

        self.meta = {**existing, **meta}
        if existing:
            self.meta["started_at"] = existing.get("started_at", _now())
            self.meta["resumed_at"] = _now()
            self.meta.pop("status", None)       # 要重新跑了，旧结论不再成立
            self.meta.pop("finished_at", None)
        else:
            self.meta["started_at"] = _now()

        self.records: list[StepRecord | DecisionRecord] = []
        self._write_meta()

    def _write_meta(self) -> None:
        (self.run_dir / "run.json").write_text(
            json.dumps(self.meta, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def _append(self, record) -> None:
        self.records.append(record)
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(asdict(record), ensure_ascii=False) + "\n")

    def record_step(
        self,
        *,
        step_id: str,
        phase: str,
        window,
        role: str,
        inputs: list[str],
        output_file: str,
        completion: Completion,
        round: int = 1,
    ) -> StepRecord:
        record = StepRecord(
            step_id=step_id,
            phase=phase,
            window=window.id,
            model=completion.model_id,
            coordinate=window.model.coordinate,
            role=role,
            inputs=inputs,
            output_file=output_file,
            content_chars=len(completion.content),
            reasoning=completion.reasoning,
            reasoning_tokens=completion.reasoning_tokens,
            tokens_in=completion.tokens_in,
            tokens_out=completion.tokens_out,
            cost_usd=completion.cost_usd,
            duration_ms=completion.duration_ms,
            attempts=completion.attempts,
            round=round,
        )
        self._append(record)
        return record

    def record_decision(
        self,
        *,
        step_id: str,
        position: str,
        mode: str,
        triggered: bool,
        trigger_reason: str | None = None,
        decision: str | None = None,
        rationale: str | None = None,
        think_ms: int | None = None,
        detail: str | None = None,
        advice=None,
        human_text: str = "",
        round: int = 1,
    ) -> DecisionRecord:
        record = DecisionRecord(
            step_id=step_id,
            position=position,
            mode=mode,
            triggered=triggered,
            trigger_reason=trigger_reason,
            decision=decision,
            rationale=rationale,
            think_ms=think_ms,
            detail=detail,
            round=round,
            **_advice_fields(advice, decision, human_text),
        )
        self._append(record)
        return record

    # ---- 汇总 ----

    @property
    def steps(self) -> list[StepRecord]:
        return [r for r in self.records if isinstance(r, StepRecord)]

    def _all_steps(self) -> list[dict]:
        """
        从 trace.jsonl 读全部步骤记录。

        不能用内存里的 self.records —— 续跑时 __init__ 会把它重置成空列表，
        于是 finish() 只统计本次会话跑的那几步。2026-09-06 那条链就是这么
        写出「步数 1、花费 $0.227」的，真实是 12 步、$1.185：中间续跑过两次，
        最后一次只跑了 2D-fix 一步。

        trace.jsonl 是逐条追加的，任何时候读它都是完整的。
        """
        if not self.path.exists():
            return []
        out = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            r = json.loads(line)
            if r.get("kind") == "step":
                out.append(r)
        return out

    @property
    def total_cost(self) -> float:
        return sum(r.cost_usd for r in self.steps)

    @property
    def total_tokens(self) -> tuple[int, int]:
        return (
            sum(r.tokens_in for r in self.steps),
            sum(r.tokens_out for r in self.steps),
        )

    def finish(self, status: str = "completed", extra: dict | None = None) -> None:
        # 统计一律从 trace.jsonl 全量算 —— 见 _all_steps 的说明
        allsteps = self._all_steps()
        self.meta.update(
            {
                "finished_at": _now(),
                "status": status,
                "steps": len(allsteps),
                "total_cost_usd": round(sum(r["cost_usd"] for r in allsteps), 6),
                "tokens_in": sum(r["tokens_in"] for r in allsteps),
                "tokens_out": sum(r["tokens_out"] for r in allsteps),
                "reasoning_captured": sum(1 for r in allsteps if r.get("reasoning")),
                **(extra or {}),
            }
        )
        self._write_meta()

    def cost_summary(self) -> str:
        allsteps = self._all_steps()          # 续跑时也要算上之前那几步
        by_model: dict[str, float] = {}
        for r in allsteps:
            by_model[r["model"]] = by_model.get(r["model"], 0.0) + r["cost_usd"]
        total = sum(r["cost_usd"] for r in allsteps)
        lines = [f"总花费 ${total:.4f}（{len(allsteps)} 步）"]
        for model, cost in sorted(by_model.items(), key=lambda kv: -kv[1]):
            lines.append(f"  {model:32} ${cost:.4f}")
        return "\n".join(lines)


def load_trace(run_dir: Path) -> tuple[dict, list[dict]]:
    """读回一次运行的记录 —— 可视化和事后分析用。"""
    meta = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
    records: list[dict] = []
    trace_path = run_dir / "trace.jsonl"
    if trace_path.exists():
        for line in trace_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                records.append(json.loads(line))
    return meta, records
