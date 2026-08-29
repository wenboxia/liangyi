# 2026-05-23 · 个人投资 Skill · 本体完整跑

## 场景介绍

为 Wenbo 生成一个专属的个人投资 Skill——一个可交给任意 AI(不限 Claude)的文件,让接手的 AI 立即了解 Wenbo 的投资目标、现有组合、价值观、可用资金途径、主攻市场,从而提供贴合他的投资决策支持。

Wenbo 是中国国籍、在瑞典读研二、专业为 AI/计算机/自动化方向。瑞典居留卡 2027-01-12 到期后回中国内地工作。投资板块希望集中在他了解的领域(计算机、通信、AI、机器人等)。资金不固定——Skill 把"当前本金/投多少"作为每次输入,投资习惯与价值观作为固化层。Skill 需具备 web search 能力以结合时事热点。

核心设计张力:Wenbo 的约束里有一部分带硬到期日(居留卡 2027-01-12、Nordea 卡 2028-12、税务 ID 2029-09-22、Revolut/Wise 可用性随居留状态变化)。一个静态 Skill 会在已知未来日期悄悄过时——这是整个流程最该被压测的点。

## 节奏感选择

**大问题(P3 按 deliverable 形态退化)**:

- P0-P2 全跑本体完整版(含所有人工决策点)
- P2D 拆台触发,事后证明值得(直接促成 Projects 架构转向)
- idea 阶段产出 v1 → v5.1(锁定),共 6 个版本(含 v5.1 结构性镜子 + 偏好显性化 + life_stage 钩子的增量)
- **P3 退化为"转译 + 单盲校验"**(2026-05-30 Wenbo 在锁定同时修正):本 idea 的 deliverable 本身是一份 .md 文件,4 工程文档会把 idea 内容重复 4 遍。改为 Claude-2 续把 idea-v5.1 转译为最终 SKILL.md + 可选 P3.1.1 单盲校验
- P4(把 SKILL.md 安装到 Claude Code / 作为 CLAUDE.md 落地)在本流程外

## 与变种和前三次实验的区别

前三次实验(美团 / Agent 评测 / ExamSniper)是变种(无人工决策版)。本次跑本体——P0 审、P1.3 综合、每个 fix 步骤的取舍、是否回退、P2D 触发、框架内/级判定、idea 锁定全部由 Wenbo 做。`decision-log.md` 是本体核心,每个人工决策点都有详细记录。

## 参数适配

| 参数 | 选定 | 状态 |
|---|---|---|
| 流程规模 | 大问题、P0-P3 全跑、P2D 大概率触发 | 已定 |
| P1 专家 A(Claude-1) | 长期投资策略专家——投资实质立场 | 已定 |
| P1 专家 B(DeepSeek-1) | AI 知识工程与跨境执行专家——载体抗腐烂/可移植立场 | 已定 |
| P1 张力维度 | 投资实质的质量 vs 载体的健壮性与可移植性 | 已定 |
| P2A 批判视角(Claude-3) | 务实有效性怀疑者(质疑 Skill 真能否让 Wenbo 投得更好、建议是否平庸或有害、可执行性) | 拟定,P2A 前确认 |
| P2B 单盲对象(Qwen-1) | 默认 Qwen 零上下文 | 拟定,P2B 前确认 |
| P2C(Claude-4) | 标准知情复审、方向漂移暴露 | 默认 |
| P2D 拆台(DeepSeek-2) | A3/A4 路径拆框架——"做这个 Skill 这件事本身对吗" | 默认 |
| P3.1.1 用户视角 | 模拟"收到这个 Skill 的陌生 AI"实际试用 PRD(主);备选叠加"未来回国工作的 Wenbo"视角 | 拟定,P3 前确认 |
| P3 PRD 评估指标 | 可移植性、抗腐烂性(带日期事实+刷新纪律)、决策支持质量、对真实约束的覆盖度、固化层/输入层边界清晰度、web search 集成清晰度 | 拟定,P3 前确认 |

投资风格画像(idea 内容,非流程参数):平衡型(核心稳健 + 卫星激进);目标退休/财务自由(超长跑、复利优先);决策风格核心被动配置 + 卫星主动选股。

## 窗口分配

| 窗口 | 底模 | 角色 | 步骤 |
|---|---|---|---|
| Claude-1 | Claude(A1·B1) | P0 精炼 / P1.1 专家 A | P0、P1.1 |
| DeepSeek-1 | DeepSeek(A3/A4·B3) | P1.2 专家 B | P1.2 |
| Claude-2 | Claude | idea.md 执笔者 | P1.4、所有 fix、P3 全部 |
| Claude-3 | Claude | 务实有效性怀疑者批判 | P2A |
| Qwen-1 | Qwen(A3·B3) | 单盲(零上下文) | P2B |
| Claude-4 | Claude | 知情复审 | P2C |
| DeepSeek-2 | DeepSeek | 拆台(A3/A4 路径) | P2D |
| Qwen-2 / DeepSeek-3 | (新开) | 用户视角校验 | P3.1.1(待定) |

跨维度硬规则满足:Claude A1·B1 × 4 + DeepSeek/Qwen A3·B3 × 3,严格版双维度 divergent。

## 人工决策点 · 完成状态

| # | 位置 | 决策内容 | 状态 |
|---|---|---|---|
| 0 | 流程启动前 | 流程规模 + P1 专家角色对 | 完成(大问题 / 组合 α) |
| 1 | P0 末尾 | P0 精炼是否忠实于原意 | 待 |
| 2 | P1.3 | 综合两份方案 + 写执笔指令给 Claude-2 | 待 |
| 3 | 2A-fix | 哪些批判响应、哪些忽略 + 修改指令 | 待 |
| 4 | 2B-fix | 哪些卡点响应、哪些忽略 + 修改指令 | 待 |
| 5 | 2C-rollback | 是否回退、回退到哪 | 待 |
| 6 | P2D 入口 | 是否触发 P2D | 待 |
| 7 | 2D-fix | 框架内 vs 框架级(修方案 or 回 P1) | 待 |
| 8 | P2/P3 边界 | idea.md 锁定 | 待 |

## 执行路径 · 完成状态

```
[完成] P0 (Claude-1 新开) → round-1/P0-refined.md
[完成] P1.1 (Claude-1 续) → round-1/P1A-expert-a.md
[完成] P1.2 (DeepSeek-1 新开、独立) → round-1/P1B-expert-b.md
[完成] P1.3 (Wenbo 综合) → decision-log 决策点 2
[完成] P1.4 (Claude-2 新开) → round-1/idea-v1.md
[完成] P2A (Claude-3 新开) → round-1/P2A-critique.md
[完成] P2A-fix (Claude-2 续) → round-1/idea-v2.md
[完成] P2B (Qwen-1 新开 单盲) → round-1/P2B-blind-review.md
[完成] P2B-fix (Claude-2 续) → round-1/idea-v3.md
[完成] P2C (Claude-4 新开) → round-1/P2C-review.md
[完成] P2C-rollback (Claude-2 续) → round-1/idea-v4.md
[完成] P2D 触发判断 → decision-log 决策点 6(触发)
[完成] P2D (DeepSeek-2 新开) → round-1/P2D-devils-advocate.md
[完成] P2D-fix (Claude-2 续) → round-1/idea-v5.md
[完成] v5 → v5.1(锁定前补结构性镜子 + 偏好显性化 + life_stage 钩子)→ round-1/idea-v5.1.md
[完成] idea 锁定 v5.1 → decision-log 决策点 8
[完成] P3.1 转译 (Claude-2 续) → round-1/SKILL.md(42KB,含 Claude Code Skill frontmatter)
[完成] P3.1.1 单盲校验 (DeepSeek + Opus 4.8 双校验) → skill-validation.md
[完成] 校验后处置(决策点 9 · defer 9 个 gap 到运行时自我演化) → decision-log
[完成] 场景级 meta-observations → scenario-observations.md
[完成] 收尾归档
```

**最终交付**:[`round-1/SKILL.md`](./round-1/SKILL.md)。
**整套本体跑完成日期**:2026-05-30。
