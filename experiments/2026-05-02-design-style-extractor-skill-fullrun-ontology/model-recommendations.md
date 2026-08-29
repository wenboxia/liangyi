# Model Recommendations · design-style-extractor

> 本清单基于 2026-05-02 跨厂商 5 个模型咨询综合(Claude Opus 4.7 / ChatGPT / Gemini 3 Pro / DeepSeek / Qwen 3.6-plus)+ 作者最终判断。判定标准沿用 design-style-extractor v5:**审美中立、主见不过强、避免模型自身的隐式审美偏好把风格带偏**。

## 抽取侧(运行 design-style-extractor 时的多模态模型)

### 首选 · Claude Opus 4.7(Anthropic)

- **理由**:5 模型咨询中 4 个推 Claude 系列;Opus 4.7 是最新版、视觉能力是真升级(CharXiv 跳 13 个点、分辨率提到 2576px);Anthropic 训练范式最匹配"克制 + 不主动加戏 + 指令遵循优于自主发挥"
- **潜在弱点**:4.7 这一代 design taste 较强、可能在描述时套用成熟设计词汇——需要 prompt 内强约束"先逐图做无术语视觉清单、再做体感总结"

### 次选 · Claude Sonnet 4.6(Anthropic)

- **理由**:成本约 1/5、训练范式同 Opus、SWE-bench 仅低 1.2 点;高频跑性价比合适
- **潜在弱点**:复杂多图细节上比 Opus 4.7 弱一档

### 备选 · Gemini 3.1 Pro(Google)

- **理由**:原生多模态、长上下文便宜、视觉细节精度高
- **潜在弱点**:在 ambiguous 输入上"自信走错"是结构性风险——可能把星露谷归类为"复古游戏 UI"并补全图里没有的元素

### 不建议

- **GPT-5.5 / GPT-5.x(OpenAI)**——训练取向是 agentic autonomy、与"克制"要求结构性冲突
- **任何开源 VLM**(Qwen-VL / GLM-V / Llama Vision / Pixtral 等)——描述精度 / 风格中立性未在本任务上验证
- **任何"美学化"专精图像模型**——会把所有风格往"漂亮"方向拉、正是本 skill 要避开的失败模式

## 下游侧(消费产出 style.skill.md 时的编码模型)

### 首选 · Claude Sonnet 4.6(Anthropic)

- **理由**:高频跑性价比最好、SWE-bench 持续领先、训练范式偏"按 token 落地、不主动加戏"
- **潜在弱点**:在 ambiguous token 上仍会基于自身审美补全——需要 skill.md 显式声明"未指定项保持视觉一致性、不引入新元素"

### 次选 · Claude Opus 4.7(Anthropic)

- **理由**:复杂前端项目(多文件、动效、复杂状态)需要更强代码能力时
- **潜在弱点**:成本约 5x、design taste 比 Sonnet 强一档、ambiguous 时更倾向自主补全

### 备选 · DeepSeek V3.1(DeepSeek)

- **理由**:极端"无审美包袱"——RLHF 偏向"逻辑正确"而非"用户体验好"、像无情的编译器一样还原 token
- **潜在弱点**:对体感层(人类可读隐喻)的理解较弱、缺乏明确 token 时无法做合理映射;DeepSeek 自己也未推荐自家做下游主力

### 不建议

- **GPT 系列(GPT-5.5 / GPT-4.1 / 4o)**——"主动加戏"是结构性问题、不是 prompt 能完全压住的
- **Gemini Pro 系列**——ambiguous 自信化在下游侧后果是"看着挺好但不是 skill 描述的那个东西"
- **所有创造型 / "帮你优化"型模型**——会把 skill 当灵感而非规约

## 关键 caveats(5 个咨询模型一致强调)

1. **prompt engineering 比模型选型权重更大**——再好的模型选型也压不过糟糕的 prompt 设计
2. **"审美中立"没有公开 benchmark**——本清单的所有判断都基于训练取向间接倒推、没有客观数据
3. **必须做"反主流 A/B 测试"**——上线前用以下三类参考图做对比:
   - 极简反骨:Hacker News / Craigslist 截图——测抽取是否脑补阴影圆角、下游是否擅自加 CSS
   - 强风格游戏:Monument Valley / Stardew Valley / Persona 5 截图——测是否被"现代化解释"
   - 不规范设计稿:Figma 中拼凑的非标设计——测 token 是否 hallucinate
4. **顶配模型都被训练成"会做出好设计"**——你的需求"忠实记录"和它们的训练目标有结构性张力、模型选型不是最大权重

## 来源声明 + 维护建议

- 本清单基于 2026-05-02 的跨厂商 5 模型咨询综合
- 咨询的模型:Claude Opus 4.7、ChatGPT、Gemini 3 Pro、DeepSeek、Qwen 3.6-plus
- 详细原始回答见 `给多个模型的AI模型选型咨询.txt`
- **建议每 6 个月或在主要厂商发布新旗舰模型后重新跑一次咨询综合**——本清单的"半衰期"由模型市场演化决定
