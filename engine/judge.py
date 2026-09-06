"""
两仪论工作流 · 盲评打分

消融实验的评分环节。设计上守两条方法论要求：

  1. **裁判不参与生产** —— 同厂商模型共享规范层与语料先验，会带相同偏好。
     MAD 论文实证过 judge 偏向同 backbone 的 debater（120:77 vs 52:136），
     所以裁判必须来自没参与生产的厂商，不是"没参与的模型"。

  2. **盲评** —— 裁判拿到的只有文档本身，不知道它是第几版、经过了什么流程。
     否则它会去评价"改得对不对"而不是"这方案成不成立"（这个失败模式在
     P2B 上已经实测踩过一次，见 VALIDATION.md 检验六）。

用方法论自己的 divergence 原则防自评偏差：两个裁判坐标不同，各打各的。
"""

from __future__ import annotations

import json
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path

from .config import MODELS
from .providers import call

PROMPT = Path(__file__).resolve().parent / "prompts" / "judge_score.md"

DIMENSIONS = ["完整性", "可行性", "风险覆盖", "目标用户清晰度", "自洽性"]


@dataclass
class Score:
    judge: str
    label: str                      # 被评文档的标识（盲评时裁判看不到）
    scores: dict[str, int] = field(default_factory=dict)
    reasons: dict[str, str] = field(default_factory=dict)
    overall: str = ""
    cost_usd: float = 0.0
    duration_ms: int = 0
    raw: str = ""

    @property
    def total(self) -> int:
        return sum(self.scores.values())

    @property
    def valid(self) -> bool:
        return len(self.scores) == len(DIMENSIONS)


def _extract_json(text: str) -> dict | None:
    """模型常把 JSON 包在代码块里，或前后带说明文字。"""
    for candidate in (
        text,
        re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.M),
    ):
        candidate = candidate.strip()
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass
    m = re.search(r"\{.*\}", text, re.S)
    if m:
        try:
            return json.loads(m.group(0))
        except json.JSONDecodeError:
            return None
    return None


def score_document(model_key: str, document: str, *, label: str = "") -> Score:
    """让一个裁判给一份文档打分。裁判看不到 label。"""
    model = MODELS[model_key]
    prompt = PROMPT.read_text(encoding="utf-8").replace("{document}", document)

    completion = call(model, [{"role": "user", "content": prompt}], max_tokens=16000)
    result = Score(
        judge=model_key, label=label, cost_usd=completion.cost_usd,
        duration_ms=completion.duration_ms, raw=completion.content,
    )

    data = _extract_json(completion.content)
    if not data:
        return result
    for dim in DIMENSIONS:
        entry = data.get(dim)
        if isinstance(entry, dict) and "分数" in entry:
            try:
                result.scores[dim] = int(entry["分数"])
            except (TypeError, ValueError):
                continue
            result.reasons[dim] = str(entry.get("理由", ""))
    result.overall = str(data.get("总评", ""))
    return result


def compare_judges(
    judges: list[str],
    documents: dict[str, str],
    *,
    repeats: int = 1,
    workers: int = 8,
) -> list[Score]:
    """
    每个裁判给每份文档打分，并发执行。

    评分任务之间完全独立——一份文档的分数不依赖另一份——所以可以并发。
    消融实验的规模是 5 场景 × 6 版本 × 2 裁判 × 3 次 = 180 次调用，串行跑
    要几小时，并发之后是几分钟。这个差别决定了"跑完看结果再调整实验设计"
    可不可行。

    repeats 是同一对（裁判, 文档）重复打分的次数。单次评分有噪声，
    实测过两个裁判对同一组文档给出方向相反的结论，所以正式实验必须多次采样
    看稳定性，不能跑一次就下判断。
    """
    tasks = [
        (j, label, text, r)
        for label, text in documents.items()
        for j in judges
        for r in range(repeats)
    ]
    results: list[Score] = []
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {
            pool.submit(score_document, j, text, label=label): (j, label, r)
            for j, label, text, r in tasks
        }
        for fut in as_completed(futures):
            j, label, r = futures[fut]
            try:
                results.append(fut.result())
            except Exception as exc:  # 单次失败不该拖垮整批
                results.append(Score(judge=j, label=label, raw=f"[失败] {exc}"))
    return results


def aggregate(results: list[Score]) -> dict[tuple[str, str], dict]:
    """按（裁判, 文档）聚合多次打分，给出均值与极差 —— 极差就是稳定性。"""
    buckets: dict[tuple[str, str], list[Score]] = {}
    for r in results:
        if r.valid:
            buckets.setdefault((r.judge, r.label), []).append(r)
    out = {}
    for key, rs in buckets.items():
        totals = [r.total for r in rs]
        out[key] = {
            "n": len(rs),
            "mean": sum(totals) / len(totals),
            "spread": max(totals) - min(totals),
            "per_dim": {
                d: sum(r.scores.get(d, 0) for r in rs) / len(rs) for d in DIMENSIONS
            },
            "cost": sum(r.cost_usd for r in rs),
        }
    return out


# ============================================================================
# 成对比较 —— 绝对打分的替代方案
# ============================================================================
# 实测发现绝对打分不可用：同一裁判对同一份文档打 5 次，极差 4-6 分，而两个
# 版本的真实差距只有 1 分。信号被自身噪声淹没，五个裁判因此给出从 -4 到 +4
# 的相反结论。
#
# 根因是 1-10 分没有锚点——"这算 8 分还是 6 分"全凭当次心证。成对比较不需要
# 锚点，只需要判断相对好坏，一致性显著更高。
#
# 位置偏差（模型倾向于选 A 或选 B）用交换顺序重跑来抵消。

PAIRWISE_PROMPT = Path(__file__).resolve().parent / "prompts" / "judge_pairwise.md"


@dataclass
class Verdict:
    judge: str
    left: str                        # 放在 A 位的文档标识
    right: str                       # 放在 B 位的文档标识
    winners: dict[str, str] = field(default_factory=dict)   # 维度 -> 胜方标识
    reasons: dict[str, str] = field(default_factory=dict)
    cost_usd: float = 0.0
    duration_ms: int = 0
    raw: str = ""

    @property
    def valid(self) -> bool:
        return len(self.winners) >= len(DIMENSIONS)


def compare_pair(
    model_key: str, doc_a: str, doc_b: str, *, label_a: str, label_b: str
) -> Verdict:
    """让一个裁判比较两份文档。裁判只看到 A / B，看不到真实标识。"""
    model = MODELS[model_key]
    prompt = (
        PAIRWISE_PROMPT.read_text(encoding="utf-8")
        .replace("{doc_a}", doc_a)
        .replace("{doc_b}", doc_b)
    )
    completion = call(model, [{"role": "user", "content": prompt}], max_tokens=16000)
    v = Verdict(
        judge=model_key, left=label_a, right=label_b,
        cost_usd=completion.cost_usd, duration_ms=completion.duration_ms,
        raw=completion.content,
    )
    data = _extract_json(completion.content)
    if not data:
        return v
    mapping = {"A": label_a, "B": label_b, "TIE": "TIE"}
    for dim in DIMENSIONS + ["总体"]:
        entry = data.get(dim)
        if isinstance(entry, dict) and "胜" in entry:
            v.winners[dim] = mapping.get(str(entry["胜"]).strip().upper(), "TIE")
            v.reasons[dim] = str(entry.get("理由", ""))
    return v


def run_pairwise(
    judges: list[str], doc_x: str, doc_y: str, *,
    label_x: str, label_y: str, repeats: int = 3, workers: int = 10,
) -> list[Verdict]:
    """
    跑成对比较。每轮都做**正反两次**（X 在 A 位一次、在 B 位一次），
    用来抵消模型的位置偏差 —— 有些模型系统性地偏好选 A。
    """
    tasks = []
    for _ in range(repeats):
        for j in judges:
            tasks.append((j, doc_x, doc_y, label_x, label_y))
            tasks.append((j, doc_y, doc_x, label_y, label_x))   # 交换位置

    out: list[Verdict] = []
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futs = [pool.submit(compare_pair, j, a, b, label_a=la, label_b=lb)
                for j, a, b, la, lb in tasks]
        for f in as_completed(futs):
            try:
                out.append(f.result())
            except Exception as exc:
                out.append(Verdict(judge="?", left="?", right="?", raw=f"[失败] {exc}"))
    return out


def win_rate(verdicts: list[Verdict], target: str) -> dict[str, dict]:
    """按裁判统计 target 的胜率。胜率接近 50% 意味着区分不出。"""
    by_judge: dict[str, list[Verdict]] = {}
    for v in verdicts:
        if v.valid:
            by_judge.setdefault(v.judge, []).append(v)
    out = {}
    for j, vs in by_judge.items():
        dims = {}
        for d in DIMENSIONS + ["总体"]:
            wins = sum(1 for v in vs if v.winners.get(d) == target)
            ties = sum(1 for v in vs if v.winners.get(d) == "TIE")
            dims[d] = {"win": wins, "tie": ties, "n": len(vs)}
        out[j] = {"dims": dims, "n": len(vs),
                  "cost": sum(v.cost_usd for v in vs)}
    return out
