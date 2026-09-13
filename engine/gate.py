"""
两仪论工作流 · 条件触发式人工决策点

方法论说"人的核心价值是做出系统内部无法自判的决策"，但没说每一步都得叫人。
四次变种实验的结论是：能委托的是**系统内部的局部判断**（这条批判成不成立），
不能委托的是**站在系统外的边界判断**（方向对不对、该不该停）。

所以决策点分两类：

**必停** —— 位置本身就是边界判断，无论内容如何都要人来定
  · 2C-rollback：方向漂移了要不要回退。投资 skill 那次证明，不停就交付错东西
  · 2D-fix：框架内修改还是回 P1。四个场景全部卡在这里

**条件触发** —— 位置属于局部判断，但特定情况下会溢出成边界问题
  · P0 精炼审：精炼版偏离原意时。这一步做错，后面全错，且没人会发现
  · 范围扩大化：AI 把批判的攻击范围扩大化处理时。critic 只说"双语同口径没
    先例"，Claude-2 就把整个英文版砍了——这是决策模拟器那次的真实教训

条件触发的价值在于：它让人的介入密度降下来，但不降在该介入的地方。
`cross-scenario-observations-v1.md` §4.2 说边界决策可以事先规则化消化，
前提是"规则本身必须由站在系统外的人设计"——这些触发条件就是那种规则。

检测用便宜快的模型。它不产出内容、只做判断，不受"裁判不能参与生产"那条约束
——那条防的是评分偏见，这里没有评分。

**为什么不是 deepseek-v4-flash（2026-09-05 换掉）**：它是推理模型，而 scope-creep
的任务形态是「读三份长文档 → 输出结构化 JSON」，正是 CLAUDE.md 的选型纪律点名
禁止用推理模型的形态。原来那条"只做判断所以没关系"的理由回应的是裁判独立性，
不是任务形态，两件事被混为一谈了。

代价是实测出来的：五条链的 2B-fix 检测，三条几分钱跑完，两条空转到超时——而且
卡死的两条输入**比成功的还小**（12980/13878 vs 15129/15931），不是长度问题。
叠加 providers.call 的"返回空就把 max_tokens 加倍重试"，三次重试越跑越慢。

换成 gpt-5.6-luna：digest.py 用它跑同样形态一直稳定，CLAUDE.md 记着它"思考少、
结构化输出稳"。它同时是裁判，但检测器只在 --hitl full 下才可能影响链条内容
（影子模式下影响不了任何东西）—— 真要跑 full 且用 luna 当裁判时，必须换掉它。
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

from .config import MODELS
from .providers import call

PROMPT_DIR = Path(__file__).resolve().parent / "prompts"

DETECTOR_MODEL = "gpt-5.6-luna"   # 见模块开头：换掉推理模型的原因


@dataclass
class GateResult:
    position: str
    triggered: bool
    reason: str = ""
    detail: str = ""
    cost_usd: float = 0.0
    checked: bool = True     # False 表示这个门根本没启用

    @classmethod
    def skipped(cls, position: str) -> "GateResult":
        return cls(position=position, triggered=False, checked=False,
                   reason="该档位未启用此决策点")


def _ask_json(prompt: str, model_key: str | None = None,
              max_tokens: int = 4000) -> tuple[dict | None, float]:
    # 检测失败一律放行。检测器是建议性的 —— 它的作用是「要不要叫人」，
    # 判不出来时正确的行为是不叫人，而不是把整条链拖死或炸掉。
    # 超时给 180 秒、只试一次：这类调用正常几秒就回，慢下来基本就是空转了。
    try:
        completion = call(MODELS[model_key or DETECTOR_MODEL],
                          [{"role": "user", "content": prompt}],
                          max_tokens=max_tokens, max_attempts=1, timeout=180.0)
    except Exception:
        return None, 0.0
    text = completion.content.strip()
    for candidate in (text, re.sub(r"^```(?:json)?|```$", "", text, flags=re.M).strip()):
        try:
            return json.loads(candidate), completion.cost_usd
        except json.JSONDecodeError:
            continue
    m = re.search(r"\{.*\}", text, re.S)
    if m:
        try:
            return json.loads(m.group(0)), completion.cost_usd
        except json.JSONDecodeError:
            pass
    return None, completion.cost_usd


def _majority(make: "callable", votes: int = 3) -> GateResult:
    """
    同一个检测跑 votes 次取多数。

    实测：merchant-appeal 的 2B-fix，同样输入连跑四次得到 True/True/True/False；
    加上 temperature=0 仍然 3/4。LLM 在 temp 0 下也不是确定性的，单次检测在
    阈值附近就是抛硬币。

    值得注意的是**内容是稳的、二元判定才抖** —— 三次 True 指的都是同一处
    （"把冻结申诉权限整个删掉，而批判只要求补足认定流程"）。所以多数投票不是
    在掩盖分歧，是在把一个稳定的观察从不稳定的阈值判断里捞出来。

    这条教训项目里已经踩过一次：longterm-and-reference.md 记着「两个坐标不同
    的裁判如果都在噪声里取样，分歧就不再是信息，只是随机。测量工具要先被验证，
    然后才谈用它测什么」。当时是裁判，这次是检测器，同一个道理。

    票数记进 reason，让噪声可见 —— 2:1 和 3:0 是不同强度的信号，抹平了就看不出。
    """
    results = [make() for _ in range(votes)]
    yes = [r for r in results if r.triggered]
    cost = sum(r.cost_usd for r in results)
    win = yes if len(yes) * 2 > votes else [r for r in results if not r.triggered]
    best = max(win, key=lambda r: len(r.detail or "")) if win else results[0]

    return GateResult(
        position=best.position,
        triggered=len(yes) * 2 > votes,
        reason=f"[{len(yes)}/{votes} 票] {best.reason}",
        detail=best.detail,
        cost_usd=cost,
    )


def check_p0_fidelity(seed: str, refined: str) -> GateResult:
    """
    P0 精炼是否偏离原意。

    先用长度做零成本初筛 —— 忠实精炼的产出应该和输入长度接近。膨胀超过 80%
    基本可以肯定加了东西，缩水超过 40% 基本可以肯定丢了东西。初筛不过再问模型。

    窗口取 0.6–1.8 的依据：五次真实运行的长度比是 0.94 / 0.99 / 0.99 / 0.98 /
    1.03，全部贴着 1.0。窗口比实测分布宽得多，落在外面属于真异常。

    （这段初筛此前是死代码 —— ratio 算出来没用、if 分支是 pass、无论如何都调
    模型。docstring 描述的行为和代码不符，宣称的"零成本"一分钱没省。2026-09-05 修。）
    """
    ratio = len(refined) / max(len(seed), 1)
    if not 0.6 <= ratio <= 1.8:
        kind = "膨胀" if ratio > 1.8 else "缩水"
        return GateResult(
            position="P0-review",
            triggered=True,
            reason=f"长度比 {ratio:.2f} 落在 0.6–1.8 之外（{kind}）",
            detail=f"忠实精炼的产出应该和原始想法长度接近（实测都在 1.0 附近）。"
                   f"差到 {ratio:.2f}，基本可以肯定{kind}的那部分不是原文的意思。",
        )

    prompt = (PROMPT_DIR / "gate_p0_fidelity.md").read_text(encoding="utf-8") \
        .replace("{seed}", seed).replace("{refined}", refined)
    return _majority(lambda: _p0_once(prompt))


def _p0_once(prompt: str) -> GateResult:
    data, cost = _ask_json(prompt)
    if not data:
        return GateResult("P0-review", False, "检测器输出无法解析，放行", cost_usd=cost)

    issues = data.get("问题", []) or []
    triggered = bool(data.get("偏离", False)) and bool(issues)
    return GateResult(
        position="P0-review",
        triggered=triggered,
        reason=data.get("结论", ""),
        detail="\n".join(f"· {i}" for i in issues),
        cost_usd=cost,
    )


def check_scope_creep(critique: str, before: str, after: str) -> GateResult:
    """
    执笔者是否把批判的攻击范围扩大化。

    这条检测的原型是决策模拟器 round-2 的真实事故：critic 只说"双语同口径在
    心理类无成功先例"，Claude-2 就把整个英文版砍掉了；critic 只说"海外华语是
    7 个碎片市场"，它就收窄到北美华人。两次都是人拦下来的。

    判据不是"改动大不大"，是"**被删掉的东西，批判有没有攻击过**"。
    """
    prompt = (PROMPT_DIR / "gate_scope_creep.md").read_text(encoding="utf-8") \
        .replace("{critique}", critique).replace("{before}", before).replace("{after}", after)
    return _majority(lambda: _scope_once(prompt))


def _scope_once(prompt: str) -> GateResult:
    data, cost = _ask_json(prompt)
    if not data:
        return GateResult("scope-creep", False, "检测器输出无法解析，放行", cost_usd=cost)

    removals = data.get("超范围删减", []) or []
    triggered = bool(data.get("存在扩大化", False)) and bool(removals)
    lines = []
    for r in removals:
        if isinstance(r, dict):
            lines.append(f"· 被删：{r.get('被删内容','?')}\n    批判其实只说：{r.get('批判原本说的','?')}")
        else:
            lines.append(f"· {r}")
    return GateResult(
        position="scope-creep",
        triggered=triggered,
        reason=data.get("结论", ""),
        detail="\n".join(lines),
        cost_usd=cost,
    )


# ============================================================================
# 档位
# ============================================================================
# off      全自动。消融实验主线用 —— 全 AI 跑可复现，剔除了"是方法论好还是
#          使用者厉害"这个混淆变量
# minimal  只开两个必停点。日常使用的推荐档
# full     加上两个条件触发点。高风险 idea 用

# 两档，不是四档。
#
# 原来有 off / minimal / advised / full 四档，砍成两档的理由：
#
# · minimal（停两次但无顾问）—— 它原本是「有人但无顾问」这个对照臂，
#   随评测层转向（不再试图证明 HITL 的必要性）已经不需要。
#
# · full（多两个条件触发检测器）—— **删的是档位，不是检测器**。
#   P0 精炼审和范围扩大化检测保留，改成两档都跑影子模式：只记录
#   「这里本来会触发」，不打断任何人。
#   理由：这两个检测器判的是「AI 改得对不对」——系统内部的局部判断，
#   规则就够了。做成会打断人的档位，反而在演示「用规则就够了」，
#   和 HITL 的论点相反。但它们抓到过真东西（2026-09-06 那条链的
#   2B-fix 触发过），所以留着 —— 价值在数据里，不在打断里。
PRESETS: dict[str, set[str]] = {
    "auto": set(),                              # 全自动，一次都不停
    "hitl": {"2C-rollback", "2D-fix"},          # 两个必停点 + 顾问环
}

# 旧运行目录里的 run.json 存的还是老档位名，续跑时要映射过来
LEGACY_MODES = {"off": "auto", "minimal": "hitl", "advised": "hitl", "full": "hitl"}


def enabled(hitl: str, position: str) -> bool:
    return position in PRESETS.get(hitl, set())


# ============================================================================
# 假对立检测 —— P1.0 生成的角色是否构成真张力
# ============================================================================
# docs 第七章步骤 1.0 的三条原则里，最难守的是「不要选『主流派 vs 激进派』
# 这种假对立」。模型很容易产出程度差异（稳健 vs 激进）而不是立场分歧，
# 而且产出看起来很像样 —— 两份方案都写得头头是道，只是不会真的打架。
#
# 这种失败特别隐蔽：P1 的 divergence 是虚的，但从产物上看不出来，
# 一路影响到后面所有步骤，最后消融数据也解释不了为什么这个场景效果差。
#
# 判据不是"两个角色听起来是否不同"，是「**能不能构造出一个具体决策问题，
# 让两者给出相反答案**」——给不出反例就是假对立。

def check_fake_tension(role_a: str, stance_a: str, role_b: str,
                       stance_b: str, tension: str = "") -> GateResult:
    prompt = (PROMPT_DIR / "gate_fake_tension.md").read_text(encoding="utf-8") \
        .replace("{role_a}", role_a).replace("{stance_a}", stance_a) \
        .replace("{role_b}", role_b).replace("{stance_b}", stance_b) \
        .replace("{tension}", tension or "（未给出）")
    data, cost = _ask_json(prompt)
    if not data:
        return GateResult("fake-tension", False, "检测器输出无法解析，放行", cost_usd=cost)

    real = bool(data.get("真对立", False))
    if real:
        detail = (f"决定性问题：{data.get('决定性问题','')}\n"
                  f"  A 的答案：{data.get('A的答案','')}\n"
                  f"  B 的答案：{data.get('B的答案','')}")
    else:
        detail = (f"问题：{data.get('问题','')}\n"
                  f"  建议：{data.get('建议','')}")

    # triggered = 需要人介入 / 需要重生成，所以「假对立」才触发
    return GateResult(
        position="fake-tension",
        triggered=not real,
        reason=data.get("结论", ""),
        detail=detail,
        cost_usd=cost,
    )
