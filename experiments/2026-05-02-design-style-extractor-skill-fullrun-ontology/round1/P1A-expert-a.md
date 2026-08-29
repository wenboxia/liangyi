方案：结构化风格抽取协议 Skill
1. Skill 形态
做万能提取器，但不是"让 AI 自由描述图片"的提取器——那是失败形态，因为输出每次都不一样，价值归 AI 不归 skill。

正确形态是：一个强约束的抽取协议。skill 本身不描述任何风格，它规定一套刚性 schema，强制读图 AI 必须按字段填空。同一组图 + 同一个 skill + 不同 AI / 不同次运行，产出的 style-spec 字段值差异要在可比对的范围内。Skill 的产物是 style-spec.md，下游 coding AI 直接消费这份结构化文件，而不是消费图片。

具体风格固化（纪念碑谷.skill.md、苹果.skill.md）不做。理由：维护爆炸、版本漂移、没有杠杆。万能抽取器跑一次就生成一份纪念碑谷 spec，等价于固化 skill，但可控、可改、可复用。

2. 输入侧
图片数量：5–9 张，强制下限 5。低于 5 张拒绝执行并报错。
图片类型必须覆盖：①主界面整图 ②次级界面整图 ③组件局部特写（按钮/输入框/卡片至少一类）④含状态变化的画面（hover / 选中 / 弹层）⑤边缘场景（空状态 / 错误态 / 过场）。缺类时 skill 强制提示补图。
约束：同一产品同一版本；拒绝混搭多个产品的截图；分辨率下限 1080px 长边；禁止带第三方 UI chrome（浏览器边框、手机壳）。
3. 提取深度（字段封闭清单）
覆盖：

Color tokens：primary / secondary / bg / surface / border / text-{1,2,3} / semantic-{success,warn,error}，每项 HEX + WCAG 对比度
Typography：family + fallback、size scale（≤7 级）、weight、line-height、letter-spacing
Spacing：base unit + scale 数组
Radius / Shadow / Elevation：枚举级别
Component atoms：button（5 状态）、input、card、modal、nav、list-item 的 token 组合
Iconography：stroke 宽度、端点、填充规则、栅格
Motion：easing 曲线、duration 档位、常见 pattern（fade/slide/scale）
Composition：栅格列数、对齐、密度档（compact/regular/loose）
Material：gradient / noise / glass / paper / flat 五选一 + 参数
Metaphor：从封闭枚举中选（geometric-illusion / cozy-pastoral / dark-puzzle / minimal-tech / …），自由文本字段不超过 1 行
不覆盖：品牌文案语气、插画与角色设计、音效、3D 资产、关卡/玩法。这些超出 UI 风格抽取边界，硬塞进来只会稀释 schema。

4. 输出模板
产出 style-spec.md，结构固定为：


---
source_images: [...]
extracted_at: ...
confidence: { color: 0.x, typo: 0.x, ... }
---
## tokens (machine-readable)
:root { --color-primary: #...; ... }
## components
button.primary { ... }
## motion
## composition
## metaphor
## unknown_fields  # 显式列出未能从图中确定的字段
机器可读的 CSS variables 块是硬要求，下游 coding AI 直接复制进 Tailwind config / theme 文件。每个字段都必须填，无法判定时填 unknown 并进 unknown_fields 区块——不允许沉默缺省。

5. 适用场景边界
用：模仿既有产品的 2D UI 视觉风格、给 vibe coding 项目锁定设计语言、跨多个页面保持一致性。

不用：3D 场景美术、游戏关卡、角色设计、插画生成、品牌 VI 重塑、动效为主的体验设计（motion 字段只能描述 UI 级动效，不覆盖叙事动画）。

也不用：参考图少于 5 张、参考图来自不同产品/不同艺术指导、用户其实只想要"好看"而没有具体参照物。

6. 与"直接喂图给多模态 AI"的对照
直接喂图路径的致命问题不是能力不够，是不可重复。同一组图，今天 GPT Image 2 生成的页面和明天生成的不一样，用户没法说清自己用的是什么。

本 skill 的不可替代价值：

可重复：spec 是文本，跑 100 次 coding 都用同一份 token，结果可比对。
可审计：用户能 diff 两份 spec、能手动改 --color-primary、能 review 哪些字段是 unknown。图片改不动。
可组合：CSS variables 直接进 Tailwind / theme，进设计系统，进 Storybook。图片不进任何系统。
可缓存：spec 一次抽取、N 次复用，token 成本摊薄。每次重新喂图的方案在大型项目里成本不收敛。
跨模型可移植：下游 coding AI 不需要多模态能力，弱视觉模型也能消费 spec。直接喂图把整条链路锁死在头部多模态模型上。
简言之：直接喂图是一次性即兴，本 skill 是把风格固化成可工程化的资产。两者不是同一类东西。