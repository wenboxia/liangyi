"""
两仪论工作流 · 步骤定义

整条链是**声明式**的：每一步声明自己在哪个窗口跑、读哪些产物、用哪个 prompt、
写出什么文件。编排器照着执行，不做任何临场决定。

这是刻意的设计选择。流程的阶段结构是固定且事先已知的，这种情况下 workflow
比 agent loop 更合适——它可复现、可调试、成本可控。而可复现正是消融实验能
成立的前提：要说「v3 比 v2 好是因为 P2B 这一步」，就必须保证除了 P2B 之外
别的都没变。塞一个 agent 做编排，每次跑的路径都可能不同，实验结论就不作数了。

（另外，方法论红线三写着「不做多 Agent 自动协商」。总调度 agent 会一路滑到那里。）
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Step:
    id: str
    phase: str
    window: str
    prompt: str
    output: str
    # 从已产出的文件里读，键是 prompt 模板里的变量名
    artifacts: dict[str, str] = field(default_factory=dict)
    # 从场景配置里读
    scenario_fields: tuple[str, ...] = ()
    # 是否把这轮对话记进窗口历史（执笔者需要，一次性批判不需要）
    remember: bool = False
    # 人工决策点标记 —— Phase C 用
    decision_point: str | None = None
    max_tokens: int = 16000
    note: str = ""


# ============================================================================
# 主链条 · P0 → idea-v5
# ============================================================================

CHAIN: list[Step] = [
    Step(
        id="P0",
        phase="P0",
        window="expert-a",
        prompt="p0_refine.md",
        scenario_fields=("seed",),
        output="P0-refined.md",
        remember=True,
        decision_point="P0-review",
        max_tokens=8000,
        note="忠实精炼。不改逻辑、不扩展、不质疑——让想法可被对抗，而不是对抗它",
    ),
    Step(
        id="P1.0",
        phase="P1",
        window="expert-a",   # 续 P0 窗口：它刚读过这个想法，最懂它难在哪
        prompt="p1_roles.md",
        artifacts={"refined_idea": "P0-refined.md"},
        output="P1-roles.yaml",
        remember=False,      # 设计角色不该污染它随后扮演专家 A 的视角
        max_tokens=8000,
        note="按 docs 步骤 1.0 的三条原则设计两个专家角色。"
             "场景文件里已写死角色时跳过这一步——那是为了让实验可复现",
    ),
    Step(
        id="P1A",
        phase="P1",
        window="expert-a",  # 续 P0 窗口：它已经理解了原始想法
        prompt="p1a_expert.md",
        artifacts={"refined_idea": "P0-refined.md"},
        scenario_fields=("role_a", "stance_a"),
        output="P1A-expert-a.md",
        remember=True,
        note="专家 A 视角出方案",
    ),
    Step(
        id="P1B",
        phase="P1",
        window="expert-b",  # 独立 session，绝不能看到专家 A 的方案
        prompt="p1b_expert.md",
        artifacts={"refined_idea": "P0-refined.md"},
        scenario_fields=("role_b", "stance_b"),
        output="P1B-expert-b.md",
        note="专家 B 视角独立出方案。独立是两仪论对抗的基础条件",
    ),
    Step(
        id="P1.4",
        phase="P1",
        window="scribe",  # 新开：不能让扮演过专家 A 的窗口来写融合方案
        prompt="p1_synthesize.md",
        artifacts={
            "refined_idea": "P0-refined.md",
            "proposal_a": "P1A-expert-a.md",
            "proposal_b": "P1B-expert-b.md",
        },
        scenario_fields=("role_a", "role_b"),
        output="idea-v1.md",
        remember=True,
        max_tokens=24000,
        note="综合成单一立场的 idea.md，不保留双声音痕迹",
    ),
    Step(
        id="P2A",
        phase="P2",
        window="critic-investor",
        prompt="p2a_critique.md",
        artifacts={"idea": "idea-v1.md"},
        output="P2A-critique.md",
        note="投资人批判 —— target 市场/逻辑 failure mode，激活 persona 轴",
    ),
    Step(
        id="2A-fix",
        phase="P2",
        window="scribe",
        prompt="fix_generic.md",
        artifacts={"idea": "idea-v1.md", "critique": "P2A-critique.md"},
        output="idea-v2.md",
        remember=True,
        decision_point="scope-creep",
        max_tokens=24000,
        note="修改一律由执笔者执行 —— divergence 在审查环节，不在修改环节",
    ),
    Step(
        id="P2B",
        phase="P2",
        window="critic-blind",  # 零上下文，底线规则
        prompt="p2b_blind.md",
        artifacts={"idea": "idea-v2.md"},
        output="P2B-blind-review.md",
        max_tokens=8000,
        note="单盲复审 —— target 知识诅咒 failure mode，激活 context 轴",
    ),
    Step(
        id="2B-fix",
        phase="P2",
        window="scribe",
        prompt="fix_generic.md",
        artifacts={"idea": "idea-v2.md", "critique": "P2B-blind-review.md"},
        output="idea-v3.md",
        remember=True,
        decision_point="scope-creep",
        max_tokens=24000,
    ),
    Step(
        id="P2C",
        phase="P2",
        window="critic-reviewer",
        prompt="p2c_review.md",
        artifacts={
            "idea_v1": "idea-v1.md",
            "idea_v3": "idea-v3.md",
            "change_log": "__change_log__",  # 由编排器合成
        },
        output="P2C-review.md",
        max_tokens=12000,
        note="知情复审 —— target 整体自洽 failure mode，激活 scope 轴。"
             "它同时是 linear 打散整合的兜底机制",
    ),
    Step(
        id="2C-rollback",
        phase="P2",
        window="scribe",
        prompt="p2c_rollback.md",
        artifacts={"idea": "idea-v3.md", "review": "P2C-review.md"},
        output="idea-v4.md",
        remember=True,
        decision_point="2C-rollback",  # 必停 —— 本体跑证明不停就交付错东西
        max_tokens=24000,
    ),
    Step(
        id="P2D",
        phase="P2",
        window="critic-devil",  # 必须 A3 任务优先档
        prompt="p2d_devil.md",
        artifacts={"idea": "idea-v4.md"},
        output="P2D-devils-advocate.md",
        max_tokens=12000,
        note="拆台 —— target 框架 failure mode，激活 AI identity 轴",
    ),
    Step(
        id="2D-fix",
        phase="P2",
        window="scribe",
        prompt="p2d_fix.md",
        artifacts={"idea": "idea-v4.md", "critique": "P2D-devils-advocate.md"},
        output="idea-v5.md",
        remember=True,
        decision_point="2D-fix",  # 必停 —— 四个场景全部卡在这里
        max_tokens=24000,
        note="框架内修改 vs 回 P1。这是唯一让全自动流程卡死的位置",
    ),
]


# ============================================================================
# 基线 · v0（单 AI 一次性出方案，消融实验的对照底座）
# ============================================================================

BASELINE = Step(
    id="v0",
    phase="baseline",
    window="scribe",
    prompt="v0_baseline.md",
    scenario_fields=("seed",),
    output="idea-v0.md",
    max_tokens=24000,
    note="同一个 seed，单 AI 一次性出方案。消融实验的基线",
)


IDEA_VERSIONS = [
    "idea-v1.md", "idea-v2.md", "idea-v3.md", "idea-v4.md", "idea-v5.md",
]


def step_by_id(step_id: str) -> Step:
    for s in CHAIN:
        if s.id == step_id:
            return s
    raise KeyError(f"未知步骤：{step_id}")
