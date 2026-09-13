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

from openai import (OpenAI, APIError, APIConnectionError, APITimeoutError,
                    InternalServerError, RateLimitError)

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


def _stream_call(client, kwargs: dict, reasoning_field: str):
    """
    流式发起一次调用，把 chunk 拼回成和非流式一样的三元组。

    为什么需要流式（2026-09-08 实测）：非流式的长请求会在**第 65 秒**被中间层
    当成空闲连接掐断，报 `Connection error`（不是 Timeout，所以调大超时没用），
    而且稳定复现三次。而 P2B 那一步 GLM-5.3 正常要跑 305–676 秒，**必然跨过
    那个坎**。流式因为一直有数据流动，不会被判定空闲 —— 实测活过 187 秒、
    7995 个 chunk。

    坑：reasoning_content 和 content 在不同字段里。推理模型可能整段都在
    reasoning 里、content 一个字都没有 —— 只读 content 会拿到空串，
    然后触发上层「空返回就加倍 max_tokens 重试」，白跑一轮。
    """
    parts, think, usage = [], [], None
    stream = client.chat.completions.create(**kwargs, stream=True)
    for chunk in stream:
        if getattr(chunk, "usage", None):
            usage = chunk.usage
        if not chunk.choices:
            continue
        d = chunk.choices[0].delta
        if getattr(d, "content", None):
            parts.append(d.content)
        for f in (reasoning_field, "reasoning", "reasoning_content"):
            v = getattr(d, f, None) or (getattr(d, "model_extra", None) or {}).get(f)
            if v:
                think.append(v)
                break
    return "".join(parts), "".join(think), usage


# 网络类失败（连接中断、5xx、限流）就地重试几次。实测连接失败率约 1/3，
# 给 5 次机会后单步失败概率降到千分之四以下。
NET_RETRIES = 5


def call(
    model: Model,
    messages: list[dict],
    *,
    max_tokens: int = 16000,
    temperature: float | None = None,
    capture_reasoning: bool = True,
    max_attempts: int = 3,
    timeout: float | None = None,
    stream: bool | None = None,
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

    def _once():
        """发一次请求，网络类失败就地重试，不消耗 attempt 预算。

        两种重试必须分开算：
        · **空返回**要把 max_tokens 加倍再来 —— 那是 attempt 在管的事
        · **网络抖动**只需要原样再发一次 —— 让它去消耗 attempt，就会顺带把
          max_tokens 翻上去，一次网络抖动能把 24000 翻成 96000，既贵又可能超模型上限

        实测环境下连接失败率约三分之一，所以这里给 NET_RETRIES 次机会。
        """
        net_err: Exception | None = None
        for net_try in range(NET_RETRIES + 1):
            try:
                use_stream = provider.stream if stream is None else stream
                if use_stream:
                    c, r, u = _stream_call(client, kwargs, provider.reasoning_field)
                    return c.strip(), r, u
                resp = client.chat.completions.create(**kwargs)
                msg = resp.choices[0].message
                return ((msg.content or "").strip(),
                        _extract_reasoning(msg, provider.reasoning_field), resp.usage)
            except (APIConnectionError, InternalServerError, RateLimitError) as exc:
                net_err = exc
                if net_try < NET_RETRIES:
                    time.sleep(min(2 ** net_try, 15))
        raise net_err  # type: ignore[misc]

    for attempt in range(1, max_attempts + 1):
        try:
            content, reasoning, usage = _once()
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

        # 可重试：限流、超时、连接中断、对面 5xx —— 都是「再试一次可能就好了」
        #
        # APIConnectionError 必须单列在前面。它是 APIError 的子类，本来会落进
        # 下面那条 break 分支 —— 于是网络一抖就直接放弃，日志还打「试了 3 次」，
        # 实际一次都没重试。2026-09-09 两条链先后死在 P1B 和 P1.4，就是这个。
        except (RateLimitError, APITimeoutError,
                APIConnectionError, InternalServerError) as exc:
            last_error = exc
            if attempt < max_attempts:
                time.sleep(2 ** attempt)  # 退避重试
                continue
        except APIError as exc:
            last_error = exc
            break  # 参数错、模型不存在这类 4xx 问题重试也没用

    raise RuntimeError(
        f"{model.id} 调用失败（试了 {attempt} 次）：{type(last_error).__name__}: {last_error}")


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
