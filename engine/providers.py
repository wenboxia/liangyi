"""
两仪论工作流 · API 适配层

四家 provider（OpenRouter / DeepSeek / Moonshot / Zhipu）都是 OpenAI 兼容格式，
所以一个适配器就够。真正的差异只有三处，全部在 config.Provider 里声明：
base_url、环境变量名、推理字段名。

这里处理两个实测踩到的坑：

  1. 空输出 —— DeepSeek-V4-Pro / Kimi-K3 / GLM-5.3 全是推理模型，max_tokens 给小了
     会把预算全花在思考上，返回空 content。实测 GLM-5.3 思考了 2980 字符还没开始
     回答。所以必须检测并给出可读的报错，而不是让空字符串一路流到下游。

  2. 推理过程 —— OpenRouter 要显式传 reasoning 参数才返回，其余三家默认就给。
     字段名也不同（reasoning vs reasoning_content）。
"""

from __future__ import annotations

import time
from dataclasses import dataclass

from openai import OpenAI, APIError, APITimeoutError, RateLimitError

from .config import Model, PROVIDERS


class EmptyCompletionError(RuntimeError):
    """模型把 token 预算全花在思考上，没留下正式回答。"""


class MissingKeyError(RuntimeError):
    """provider 的 API key 没配。"""


@dataclass
class Completion:
    """一次模型调用的完整记录 —— 既是返回值，也是 trace 的原始素材。"""
    content: str
    reasoning: str | None
    model_id: str
    tokens_in: int
    tokens_out: int
    reasoning_tokens: int
    cost_usd: float
    duration_ms: int
    attempts: int = 1

    @property
    def has_reasoning(self) -> bool:
        return bool(self.reasoning and self.reasoning.strip())


_clients: dict[str, OpenAI] = {}


def _client(provider_name: str) -> OpenAI:
    """按 provider 缓存 client。"""
    if provider_name not in _clients:
        provider = PROVIDERS[provider_name]
        key = provider.api_key
        if not key:
            raise MissingKeyError(
                f"{provider.name} 的 API key 未配置。"
                f"请在项目根目录的 .env 里设置 {provider.env_key}=..."
                f"（模板见 .env.example）"
            )
        _clients[provider_name] = OpenAI(
            api_key=key,
            base_url=provider.base_url,
            timeout=provider.timeout,  # 按 provider 配，慢的模型单独放宽
            max_retries=0,  # 重试逻辑自己管，好记录 attempts
        )
    return _clients[provider_name]


def _extract_reasoning(message, provider_field: str) -> str | None:
    """从返回的 message 里取推理过程。字段名各家不同。"""
    for field in (provider_field, "reasoning", "reasoning_content"):
        value = getattr(message, field, None)
        if value:
            return value
    # 有些 provider 把它塞在 model_extra 里
    extra = getattr(message, "model_extra", None) or {}
    for field in (provider_field, "reasoning", "reasoning_content"):
        if extra.get(field):
            return extra[field]
    return None


def call(
    model: Model,
    messages: list[dict],
    *,
    max_tokens: int = 16000,
    temperature: float | None = None,
    capture_reasoning: bool = True,
    max_attempts: int = 3,
    timeout: float | None = None,
) -> Completion:
    """
    调用一次模型。

    max_tokens 默认给到 16000 —— 推理模型的思考过程也算在里面，给小了会返回空。
    这不是保守，是实测出来的下限。
    """
    provider = PROVIDERS[model.provider]
    client = _client(model.provider)

    kwargs: dict = {
        "model": model.id,
        "messages": messages,
        "max_tokens": max_tokens,
    }
    if temperature is not None:
        kwargs["temperature"] = temperature
    if capture_reasoning and provider.needs_reasoning_param:
        kwargs["extra_body"] = {"reasoning": {"enabled": True}}
    if timeout is not None:
        # 单次调用的超时，覆盖 provider 级默认值。给检测器这类「失败也无所谓、
        # 但绝不能拖住整条链」的调用用。
        kwargs["timeout"] = timeout

    last_error: Exception | None = None
    started = time.time()

    for attempt in range(1, max_attempts + 1):
        try:
            resp = client.chat.completions.create(**kwargs)
            message = resp.choices[0].message
            content = (message.content or "").strip()
            reasoning = _extract_reasoning(message, provider.reasoning_field)

            usage = resp.usage
            tokens_in = getattr(usage, "prompt_tokens", 0) or 0
            tokens_out = getattr(usage, "completion_tokens", 0) or 0
            details = getattr(usage, "completion_tokens_details", None)
            reasoning_tokens = getattr(details, "reasoning_tokens", 0) or 0 if details else 0

            if not content:
                # 坑一：预算被思考吃光。加倍重试，而不是把空字符串传给下游。
                if attempt < max_attempts:
                    kwargs["max_tokens"] = int(kwargs["max_tokens"] * 2)
                    continue
                raise EmptyCompletionError(
                    f"{model.id} 返回空内容：{reasoning_tokens} 个 token 全花在思考上，"
                    f"max_tokens={kwargs['max_tokens']} 仍然不够。"
                    f"这是推理模型的典型症状，把 max_tokens 调更大再试。"
                )

            return Completion(
                content=content,
                reasoning=reasoning,
                model_id=model.id,
                tokens_in=tokens_in,
                tokens_out=tokens_out,
                reasoning_tokens=reasoning_tokens,
                cost_usd=model.cost(tokens_in, tokens_out),
                duration_ms=int((time.time() - started) * 1000),
                attempts=attempt,
            )

        except (RateLimitError, APITimeoutError) as exc:
            last_error = exc
            if attempt < max_attempts:
                time.sleep(2 ** attempt)  # 退避重试
                continue
        except APIError as exc:
            last_error = exc
            break  # 参数错、模型不存在这类问题重试也没用

    raise RuntimeError(f"{model.id} 调用失败（试了 {max_attempts} 次）：{last_error}")


def preflight(profile: str = "primary") -> dict[str, str]:
    """
    开跑前检查所有 provider 的 key 是否可用。
    跑一条完整链要几分钟，不该跑到一半才发现某个 key 没配。
    """
    from .config import WINDOWS, resolve_model

    results: dict[str, str] = {}
    needed = {resolve_model(w, profile).provider for w in WINDOWS}
    for name in sorted(needed):
        provider = PROVIDERS[name]
        if not provider.api_key:
            results[name] = f"缺少 {provider.env_key}"
        else:
            results[name] = "就绪"
    return results
