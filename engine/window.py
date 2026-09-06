"""
两仪论工作流 · 窗口抽象

一个窗口 = 一个独立的 messages 数组 + 一个绑定的模型。

这是整个引擎最重要的一个概念。方法论里的 session hygiene 原本是人肉纪律——
「每个角色一个独立窗口」「单盲必须零上下文」靠使用者自己守。手动跑的时候，
最常见也最致命的错误就是图省事用同一个窗口跑完整个流程，于是单盲不单盲、
综合不中立、批判不独立，方法论当场失效。

做成代码之后，这条纪律变成了结构保证：

  - 不同窗口 = 不同的 Window 实例 = 物理隔离的 messages 数组
  - 零上下文窗口 = 每次调用都从空数组开始，**代码层面不可能累积历史**

最后这条是底线规则（违反即 P2B 当场失效），所以这里不只是「默认不传历史」，
而是主动拒绝任何注入历史的尝试并抛异常。这是可审计的：面试时可以直接指着
`ZeroContextViolation` 说，单盲窗口就算我想给它喂上下文也喂不进去。
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .config import Model, WindowSpec
from .providers import Completion, call


class ZeroContextViolation(RuntimeError):
    """试图给零上下文窗口注入历史 —— 违反 P2B 底线规则。"""


@dataclass
class Window:
    spec: WindowSpec
    model: Model
    _messages: list[dict] = field(default_factory=list, repr=False)
    _calls: int = 0

    @property
    def id(self) -> str:
        return self.spec.id

    @property
    def is_zero_context(self) -> bool:
        return self.spec.zero_context

    @property
    def turn_count(self) -> int:
        return self._calls

    def ask(
        self,
        prompt: str,
        *,
        system: str | None = None,
        max_tokens: int = 16000,
        remember: bool = True,
    ) -> Completion:
        """
        向这个窗口提问。

        remember=True 时把这一轮对话存进窗口历史，下次调用带着它 —— 这是
        「续窗口」的语义（执笔者在各个 fix 步骤之间保持连贯，靠的就是它）。
        remember=False 时不留痕迹，用于一次性的旁路提问。

        零上下文窗口忽略 remember，永远从空开始。
        """
        if self.is_zero_context:
            messages: list[dict] = []
            if system:
                messages.append({"role": "system", "content": system})
            messages.append({"role": "user", "content": prompt})
            completion = call(self.model, messages, max_tokens=max_tokens)
            self._calls += 1
            return completion

        messages = list(self._messages)
        if system and not messages:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        completion = call(self.model, messages, max_tokens=max_tokens)
        self._calls += 1

        if remember:
            self._messages = messages + [
                {"role": "assistant", "content": completion.content}
            ]
        return completion

    def replay(self, prompt: str, answer: str) -> None:
        """
        把一轮已经发生过的对话补回窗口历史，不产生 API 调用。

        断点续跑时用：前面的步骤已经有产物了，不需要重跑，但执笔窗口必须
        知道自己之前写过什么，否则续写会失去连贯性——「修改必须由同一个
        执笔者做」这条纪律，在续跑场景下靠这个方法维持。

        零上下文窗口不需要也不允许 replay：它每次都从空开始，本来就没有
        历史可言。
        """
        if self.is_zero_context:
            return
        self._messages = self._messages + [
            {"role": "user", "content": prompt},
            {"role": "assistant", "content": answer},
        ]

    def inject_history(self, messages: list[dict]) -> None:
        """
        预置对话历史。用于从中断处恢复运行。

        零上下文窗口拒绝这个操作 —— 这是底线规则的强制点。
        """
        if self.is_zero_context:
            raise ZeroContextViolation(
                f"窗口 {self.id} 是零上下文窗口（P2B 单盲），不接受历史注入。\n"
                f"单盲的价值就是暴露「文档脱离作者上下文还站不站得住」。"
                f"一旦给它背景信息，它会脑补，P2B 的核心机制当场失效——"
                f"这条规则没有例外。"
            )
        self._messages = list(messages)

    def history(self) -> list[dict]:
        return list(self._messages)

    def reset(self) -> None:
        """清空窗口 —— 等价于关掉重开一个新窗口。"""
        self._messages = []
        self._calls = 0


class WindowPool:
    """
    一次运行里所有窗口的集合。

    窗口按需创建、创建后保持 —— 这样「同一个窗口在多个步骤出现」自然就是
    上下文延续，「不同窗口」自然就是彻底隔离，不需要调用方额外做什么。
    """

    def __init__(self, profile: str = "primary"):
        from .config import WINDOWS, resolve_model

        self.profile = profile
        self._specs = WINDOWS
        self._resolve = resolve_model
        self._windows: dict[str, Window] = {}

    def get(self, window_id: str) -> Window:
        if window_id not in self._windows:
            spec = self._specs[window_id]
            model = self._resolve(window_id, self.profile)
            self._windows[window_id] = Window(spec=spec, model=model)
        return self._windows[window_id]

    def active(self) -> dict[str, Window]:
        return dict(self._windows)

    def summary(self) -> list[dict]:
        """每个窗口用了什么模型、调用了几次 —— 进 trace 用。"""
        return [
            {
                "window": w.id,
                "model": w.model.id,
                "coordinate": w.model.coordinate,
                "zero_context": w.is_zero_context,
                "turns": w.turn_count,
            }
            for w in self._windows.values()
        ]
