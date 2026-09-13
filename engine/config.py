"""
两仪论工作流 · 配置层

这份文件把方法论的「本体 vs 参考分离」纪律做进了代码结构：

  - 窗口（WINDOWS）按**角色**命名，不按模型命名 —— 这是本体，不随市场变化
  - 模型通过**槽位**（slot）映射进来 —— 这是参考，随时可换

换模型只需要改 PROFILES，不用碰任何其他代码。这不是为了写着好看：
2026-08 复核九家厂商时，四个月前写死的版本号已经全部过期。
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

REPO_ROOT = Path(__file__).resolve().parent.parent


# ============================================================================
# Provider · 四家 API 的接入差异
# ============================================================================
# 四家都是 OpenAI 兼容格式，差异只有三处：base_url、环境变量名、推理字段名。
# OpenRouter 只用于 Claude 和 GPT；DeepSeek / Kimi / GLM 走各自官方 API。

@dataclass(frozen=True)
class Provider:
    name: str
    base_url: str
    env_key: str
    reasoning_field: str  # 模型返回思考过程时用的字段名
    needs_reasoning_param: bool = False  # 是否要显式请求才返回推理过程
    # 请求超时。默认 600s 对大多数模型够用，但 GLM-5.3 在盲审这一步实测跑
    # 431s / 487s / 535s —— 第三条链已经贴着 600s 的边，第四条越过去直接超时。
    # 这不是间歇故障，是阈值本来就卡在实测分布的尾巴上。
    timeout: float = 600.0
    # 是否用流式请求。非流式的长请求会在第 65 秒被中间层当成空闲连接掐断
    # （报 Connection error 而非 Timeout，所以调大超时没用），而 GLM-5.3 在
    # 盲审那一步正常要跑 305-676 秒，必然跨过那个坎。流式一直有数据流动，
    # 不会被判空闲。只给需要的 provider 开 —— 流式会丢一部分 usage 字段。
    stream: bool = False

    @property
    def api_key(self) -> str | None:
        return os.getenv(self.env_key)


PROVIDERS: dict[str, Provider] = {
    "openrouter": Provider(
        name="openrouter",
        base_url="https://openrouter.ai/api/v1",
        env_key="OPENROUTER_API_KEY",
        reasoning_field="reasoning",
        needs_reasoning_param=True,
    ),
    "deepseek": Provider(
        name="deepseek",
        base_url="https://api.deepseek.com",
        env_key="DEEPSEEK_API_KEY",
        reasoning_field="reasoning_content",
    ),
    "moonshot": Provider(
        name="moonshot",
        base_url="https://api.moonshot.cn/v1",
        env_key="MOONSHOT_API_KEY",
        reasoning_field="reasoning_content",
    ),
    "zhipu": Provider(
        name="zhipu",
        base_url="https://open.bigmodel.cn/api/paas/v4",
        env_key="ZHIPU_API_KEY",
        reasoning_field="reasoning_content",
        timeout=1800.0,  # GLM-5.3 慢，见 Provider.timeout 上的说明
        stream=True,     # 见 Provider.stream：非流式长请求会被掐断
    ),
}


# ============================================================================
# Model · 模型定义与底模坐标
# ============================================================================
# 坐标依据见 references/ai-training-landscape.md（2026-08 快照）。
# 价格单位是每百万 token，2026-08-30 核对。

@dataclass(frozen=True)
class Model:
    id: str
    provider: str
    dim_a: str          # 冲突偏向：A1 规范优先 / A2 权限优先 / A3 任务优先
    dim_b: str          # 语料文化：B1 英文母语 / B2 中文母语 / B3 跨文化双核
    price_in: float     # USD per 1M input tokens
    price_out: float    # USD per 1M output tokens
    vendor: str

    @property
    def coordinate(self) -> str:
        return f"{self.dim_a}·{self.dim_b}"

    def cost(self, tokens_in: int, tokens_out: int) -> float:
        return tokens_in / 1e6 * self.price_in + tokens_out / 1e6 * self.price_out


MODELS: dict[str, Model] = {
    # ---- A2 权限优先（OpenAI）----
    "gpt-5.6-luna": Model(
        id="openai/gpt-5.6-luna", provider="openrouter",
        dim_a="A2", dim_b="B1", price_in=0.20, price_out=1.20, vendor="OpenAI",
    ),
    "gpt-5.6-terra": Model(  # 升级备选：luna 在长文档上吃力时换它
        id="openai/gpt-5.6-terra", provider="openrouter",
        dim_a="A2", dim_b="B1", price_in=2.00, price_out=12.00, vendor="OpenAI",
    ),
    # ---- A1 规范优先（Anthropic）----
    "claude-sonnet-5": Model(
        id="anthropic/claude-sonnet-5", provider="openrouter",
        dim_a="A1", dim_b="B1", price_in=2.00, price_out=10.00, vendor="Anthropic",
    ),
    "claude-haiku-4.5": Model(
        id="anthropic/claude-haiku-4.5", provider="openrouter",
        dim_a="A1", dim_b="B1", price_in=1.00, price_out=5.00, vendor="Anthropic",
    ),
    # ---- A3 任务优先 ----
    "deepseek-v4-pro": Model(
        id="deepseek-v4-pro", provider="deepseek",
        dim_a="A3", dim_b="B3", price_in=0.56, price_out=1.12, vendor="DeepSeek",
    ),
    "deepseek-v4-flash": Model(  # 调试档
        id="deepseek-v4-flash", provider="deepseek",
        dim_a="A3", dim_b="B3", price_in=0.07, price_out=0.28, vendor="DeepSeek",
    ),
    "kimi-k3": Model(
        id="kimi-k3", provider="moonshot",
        dim_a="A3", dim_b="B3", price_in=3.00, price_out=15.00, vendor="Moonshot",
    ),
    "kimi-k2.5": Model(  # 调试档
        id="kimi-k2.5", provider="moonshot",
        dim_a="A3", dim_b="B3", price_in=0.60, price_out=3.00, vendor="Moonshot",
    ),
    "glm-5.3": Model(
        id="glm-5.3", provider="zhipu",
        dim_a="A3", dim_b="B2", price_in=1.40, price_out=4.40, vendor="Zhipu",
    ),
    "glm-4-flash": Model(  # 调试档
        id="glm-4-flash", provider="zhipu",
        dim_a="A3", dim_b="B2", price_in=0.0, price_out=0.0, vendor="Zhipu",
    ),
}


# ============================================================================
# Profile · 槽位到模型的映射（这一层是「参考」，随时可换）
# ============================================================================
# 三个槽位对应方法论要求的三种底模角色：
#   anchor      —— 承担执笔与主要批判。需要「被明确指令时严格照做」的特性
#   divergent_a —— 与 anchor 跨维度。承担 P1 专家 B 与 P2D 拆台（拆台必须 A3）
#   divergent_b —— 第三家厂商。承担 P2B 单盲，取其「什么都不知道」最真实

PROFILES: dict[str, dict[str, str]] = {
    # 正式实验用 —— 与 docs/session-hygiene.md 的默认推荐组合一致
    # （Claude×4 + DeepSeek×2 + Kimi×1）。
    #
    # 2026-08-30 从 gpt-5.6-luna 换成 claude-sonnet-5。理由不只是能力：
    #   1. docs 里「为什么 P0 与执笔要用 A1」的全部论证都基于 A1 规范优先写的，
    #      用 A2 得额外解释「为什么 A2 也行」
    #   2. 六次实验全是 Claude 执笔，用 A2 会在「实验证据」与「产品实现」之间
    #      留一道断层
    #   3. 实测成本 5 场景 $5.17，绝对值完全在预算内（贵 3.5 倍但基数小）
    "primary": {
        "anchor": "claude-sonnet-5",
        "divergent_a": "deepseek-v4-pro",
        "divergent_b": "glm-5.3",
    },
    # 开发调试用 —— 只验证流程跑得通，不看质量
    "debug": {
        "anchor": "gpt-5.6-luna",
        "divergent_a": "deepseek-v4-flash",
        "divergent_b": "kimi-k2.5",
    },
    # A1 vs A2 对照组 —— 主线是 A1（规范优先），这里换成 A2（权限优先），
    # 测「换掉 anchor 的冲突偏向档位后，链条结论还稳不稳」。
    # 便宜档也是刻意的：这组要验证的是坐标差异，不是能力差异。
    "contrast_a2": {
        "anchor": "gpt-5.6-luna",
        "divergent_a": "deepseek-v4-pro",
        "divergent_b": "kimi-k3",
    },
    # 应急配置 —— OpenRouter 不可用时（403 / 额度问题）仍能跑通流程。
    # 三家全是 A3 任务优先，但 GLM 是 B2 中文母语、另两家是 B3 跨文化，
    # 所以维度 B 上仍然跨维度，硬规则（宽松版）成立。
    #
    # 代价要说清楚：anchor 位是 A3，而 docs 第六章论证 P0 精炼与执笔需要
    # 「被明确指令时不会主动扩展」的特性——A3 的奖励信号只看任务完成度，
    # 「把想法说得更好」会被它理解成任务的一部分。所以这个配置只用于验证
    # 流程能否跑通，不用于正式实验。
    "fallback_cn": {
        "anchor": "glm-5.3",
        "divergent_a": "deepseek-v4-pro",
        "divergent_b": "kimi-k3",
    },
    # 冒烟测试 —— 全 flash 档，只验证「链条能不能从头跑到尾」。
    # 不看产出质量，看的是编排、窗口隔离、产物传递、2D-fix 判定逻辑是否正常。
    # 实测教训：旗舰推理模型（GLM-5.3 / DeepSeek-V4-Pro / Kimi-K3）思考量极大，
    # 执笔一步要 5-10 分钟，验证流程时用它们纯属浪费。
    "smoke": {
        "anchor": "glm-4-flash",
        "divergent_a": "deepseek-v4-flash",
        "divergent_b": "kimi-k2.5",
    },

    # 在线体验入口用的档 —— 访客输入自己的想法，跑完整 13 步。
    #
    # 和 smoke / debug 的区别是**三个坐标各不相同**：smoke 和 debug 的两个批判位
    # 都是 A3·B3，同坐标。拿一个主打「跨维度对抗」的流程去演示，
    # 却用同坐标配置，说不过去 —— 硬规则能过，但演示本身就成了反例。
    #
    # 挑这三个的另一个理由是快和便宜：正式档一条链 31 分钟、$1.2，
    # 访客不会在网页上等那么久，而且每次点击花的是项目的钱。
    # glm-4-flash 免费，deepseek flash 是 pro 的八分之一价。
    "demo": {
        "anchor": "gpt-5.6-luna",          # A2·B1
        "divergent_a": "deepseek-v4-flash",  # A3·B3
        "divergent_b": "glm-4-flash",        # A3·B2
    },
}

# 评分裁判 · 两个都不参与生产，且坐标不同
#
# 2026-08-30 调整：单盲位从 kimi-k3 换成 glm-5.3（便宜 3.3 倍，且 B2 中文母语
# 做中文产品的单盲先验更贴）。这一换把 Kimi 从生产位释放出来，正好补上裁判二
# ——而 kimi-k2.5 做裁判比 glm-5.3 便宜 3.7 倍。一处调整省两笔。
#
# 为什么裁判必须没参与生产：同厂商模型共享规范层与语料先验，会带相同偏好。
# MAD 论文实证过 judge 偏向同 backbone 的 debater（120:77 vs 52:136）。
JUDGES = ["gpt-5.6-luna", "kimi-k2.5"]


# ============================================================================
# Window · 窗口定义（这一层是「本体」，不随模型变化）
# ============================================================================
# 一个窗口 = 一个独立的 messages 数组。同一个窗口在多个步骤出现 = 上下文延续；
# 不同窗口 = 上下文彻底隔离。session hygiene 在这里从人肉纪律变成代码结构。

@dataclass(frozen=True)
class WindowSpec:
    id: str
    slot: str
    role: str
    zero_context: bool = False  # 底线规则：单盲窗口永不接收历史上下文


WINDOWS: dict[str, WindowSpec] = {
    "expert-a": WindowSpec(
        id="expert-a", slot="anchor",
        role="P0 忠实精炼 + P1 专家 A 视角出方案",
    ),
    "scribe": WindowSpec(
        id="scribe", slot="anchor",
        role="idea.md 执笔者 —— 写初版并执行全部修改。"
             "divergence 体现在审查环节，绝不体现在修改环节，否则 idea 会变成多个 AI 的拼贴",
    ),
    "critic-investor": WindowSpec(
        id="critic-investor", slot="anchor",
        role="P2A 怀疑论投资人 —— 攻击逻辑与商业可行性。新开窗口才能真正冷眼",
    ),
    "critic-reviewer": WindowSpec(
        id="critic-reviewer", slot="anchor",
        role="P2C 知情复审 —— 对比 v1 与 v3 暴露方向漂移。"
             "「知情」来自输入的材料，不来自参与过讨论，这两者的区别就是能不能中立的区别",
    ),
    "expert-b": WindowSpec(
        id="expert-b", slot="divergent_a",
        role="P1 专家 B 视角出方案 —— 独立 session，绝不能看到专家 A 的方案",
    ),
    "critic-devil": WindowSpec(
        id="critic-devil", slot="divergent_a",
        role="P2D 拆台专家 —— 质疑整个方向的前提假设。"
             "必须由 A3 任务优先档扮演：有规范层的底模会在最关键那一刀上把攻击软化掉",
    ),
    "critic-blind": WindowSpec(
        id="critic-blind", slot="divergent_b",
        role="P2B 单盲复审 —— 零上下文陌生读者，暴露知识诅咒",
        zero_context=True,
    ),
}


# ============================================================================
# 硬规则校验
# ============================================================================

def resolve_model(window_id: str, profile: str = "primary") -> Model:
    """把窗口解析到具体模型。"""
    spec = WINDOWS[window_id]
    model_key = PROFILES[profile][spec.slot]
    return MODELS[model_key]


def check_hard_rules(profile: str = "primary") -> list[str]:
    """
    开跑前校验方法论硬规则。返回违规列表，空列表表示全部通过。

    这些不是代码风格检查，是方法论本体要求：
      1. 只用维度 A 可判定的模型（未公开档不进入任何窗口）
      2. P2 链条必须跨维度（至少一对底模在 A 或 B 上不重合）
      3. P2D 拆台必须由 A3 任务优先档扮演
      4. 单盲必须零上下文（由 window.py 在运行时强制）
    """
    violations: list[str] = []
    mapping = {w: resolve_model(w, profile) for w in WINDOWS}

    # 规则一：维度 A 必须可判定
    for wid, model in mapping.items():
        if model.dim_a not in ("A1", "A2", "A3"):
            violations.append(
                f"[规则一] 窗口 {wid} 用了维度 A 未公开的模型 {model.id}——"
                f"方法论要求选型依据可解释"
            )

    # 规则二：P2 链条跨维度
    p2_chain = ["critic-investor", "critic-blind", "critic-reviewer", "critic-devil"]
    coords = {mapping[w].coordinate for w in p2_chain}
    if len(coords) < 2:
        violations.append(
            f"[规则二] P2 链条全部落在同一坐标 {coords}——这是假覆盖："
            f"四条 failure mode 看似都覆盖，实际有一整块维度没被任何人碰到"
        )

    # 规则三：拆台必须 A3
    devil = mapping["critic-devil"]
    if devil.dim_a != "A3":
        violations.append(
            f"[规则三] P2D 拆台用了 {devil.dim_a} 档的 {devil.id}——"
            f"必须 A3 任务优先。有规范层的底模无法真实激活拆台 persona"
        )

    return violations


def describe_profile(profile: str = "primary") -> str:
    """打印当前配置，用于开跑前确认。"""
    lines = [f"配置档位：{profile}", ""]
    for wid, spec in WINDOWS.items():
        m = resolve_model(wid, profile)
        flag = " [零上下文]" if spec.zero_context else ""
        lines.append(f"  {wid:18} {m.id:28} {m.coordinate}{flag}")
    coords = {resolve_model(w, profile).coordinate for w in WINDOWS}
    lines.append("")
    lines.append(f"  坐标分布：{' + '.join(sorted(coords))}")
    return "\n".join(lines)
