"""
两仪论工作流 · 决策点摘要

人在决策点要做的判断，和他能做的判断，必须对得上。

实测教训（2026-08-31）：第一版界面把整篇 P2C 诊断摊开，等于要求使用者做
**领域专家的设计评审**——"这个权限模型拆得对不对""自动回滚该放哪一档"。
使用者的反馈是"我没有这个能力和资格去判断"。

但方法论要他判断的根本不是这个。docs 对 2C-rollback 的定义是「回退的标准是
这偏离了产品最初要解决的问题」——翻译过来就一句话：**你当初说要 X，现在变成
了 Y，这个变化你认不认**。

这个判断不需要懂领域，只需要他是那个提出想法的人。而"哪种设计更严谨"是系统
自己能判的，根本不该拿来问人。这正是立场三：**人做的是系统内部无法自判的决策**
——系统不知道你想要什么，但系统知道什么设计更周全。

所以这个模块只干一件事：把决策点需要的判断，压缩到人真正答得了的那个层面。
完整材料仍然随时可查，但不再是**必须读完才能决定**的东西。

摘要用 gpt-5.6-luna 而不是检测器那个 deepseek-v4-flash。理由是任务形态不同：
检测是判断题（输出短、值得深想），摘要是「读长文档 + 输出结构化」——推理模型
在这上面会陷进去。实测 deepseek-v4-flash 处理同一份 P2C 诊断，一次只花
$0.0004 就完成，另一次思考了 16001 个 token 还没吐出内容。

这不是模型不好，是**任务形态和模型特性不匹配**。luna 官方定位就是
"fast, cost-efficient"，思考少、结构化输出稳，正适合这种活。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .gate import _ask_json

# 摘要任务用思考少的模型 —— 见模块开头的说明
DIGEST_MODEL = "gpt-5.6-luna"

PROMPT_DIR = Path(__file__).resolve().parent / "prompts"


@dataclass
class IntentShift:
    promise_then: str = ""
    promise_now: str = ""
    rows: list[dict] = field(default_factory=list)
    summary: str = ""
    cost_usd: float = 0.0
    ok: bool = False


@dataclass
class DevilDigest:
    points: list[dict] = field(default_factory=list)
    overall: str = ""
    cost_usd: float = 0.0
    ok: bool = False

    @property
    def hits_premise(self) -> int:
        return sum(1 for p in self.points if "前提" in str(p.get("打中的是", "")))


@dataclass
class VersionDiff:
    change: str = ""
    touched_product: bool = True
    cost_usd: float = 0.0
    ok: bool = False


def intent_shift(seed: str, review: str) -> IntentShift:
    """从原始想法和漂移诊断里抽出「当初 vs 现在」。"""
    prompt = (PROMPT_DIR / "digest_intent.md").read_text(encoding="utf-8") \
        .replace("{seed}", seed).replace("{review}", review)
    data, cost = _ask_json(prompt, DIGEST_MODEL, max_tokens=8000)
    if not data:
        return IntentShift(cost_usd=cost)

    core = data.get("核心承诺", {}) or {}
    return IntentShift(
        promise_then=str(core.get("当初", "")).strip(),
        promise_now=str(core.get("现在", "")).strip(),
        rows=[r for r in (data.get("对照") or []) if isinstance(r, dict)],
        summary=str(data.get("一句话", "")).strip(),
        cost_usd=cost,
        ok=bool(core.get("当初") and core.get("现在")),
    )


def devil_digest(devil: str) -> DevilDigest:
    """把拆台论据压成一句一条，标出打中的是前提还是细节。"""
    prompt = (PROMPT_DIR / "digest_devil.md").read_text(encoding="utf-8") \
        .replace("{devil}", devil)
    data, cost = _ask_json(prompt, DIGEST_MODEL, max_tokens=8000)
    if not data:
        return DevilDigest(cost_usd=cost)

    points = [p for p in (data.get("论据") or []) if isinstance(p, dict)]
    return DevilDigest(
        points=points,
        overall=str(data.get("整体", "")).strip(),
        cost_usd=cost,
        ok=bool(points),
    )


# 同一条链里 2C 和 2D 都要看版本演化，算过的不重算。
# key 是两版正文的长度对，够用了 —— 一次运行内不会有两对不同内容而长度全等。
_diff_cache: dict[tuple[int, int], VersionDiff] = {}


def version_diff(prev: str, curr: str) -> VersionDiff:
    """
    一句话说清这一版把什么改成了什么。

    为什么只给一句话、而且明令不许评价：2C-rollback 要人判断的是「哪些漂移
    偏离了我最初要解决的问题」。摘要一旦带上「更严谨」「改进了」这类词，判断
    就从「这还是我要的吗」滑到「哪个设计更好」——后者需要领域专家，而 Wenbo
    对着那种界面的原话是"我没有这个能力和资格去判断"。

    句式统一成「把 X 改成了 Y」，是因为要判的就是这个变化本身。
    """
    key = (len(prev), len(curr))
    if key in _diff_cache:
        return _diff_cache[key]

    prompt = (PROMPT_DIR / "digest_version.md").read_text(encoding="utf-8") \
        .replace("{prev}", prev).replace("{curr}", curr)
    data, cost = _ask_json(prompt, DIGEST_MODEL, max_tokens=4000)
    if not data:
        return VersionDiff(cost_usd=cost)

    change = str(data.get("变化", "")).strip()
    result = VersionDiff(
        change=change,
        touched_product=bool(data.get("动没动产品", True)),
        cost_usd=cost,
        ok=bool(change),
    )
    _diff_cache[key] = result
    return result
