# 2026-05-02 · 设计风格提取 Skill · 本体完整跑

## 场景介绍

做一个 `.skill.md` 文件、用于 AI coding 时从参考图提取目标设计风格、指导前端实现。

原始动机：vibe coding 中"我想要纪念碑谷的感觉"→ AI 实际产出 → 风格走样、是普遍 pain。文字描述设计风格本身有信息论上限——颜色、间距、纹理、光影、隐喻这些视觉信号文字化必然失真。用参考图固化风格是设计行业 mood board 几十年的共识——把它接到 AI coding 工作流是合理方向。

## 节奏感选择

**中等偏轻**：

- P0-P2 走本体完整版（含所有人工决策点、P2D 触发由 Wenbo 判）
- P3 退化为：Claude-2 把锁定 idea 转译成 skill.md + 可选 P3.1.1 单盲校验
- P3 **不跑**传统四份工程文档（PRD / Tech Spec / CLAUDE.md / Dev Guide）
- P4 在本流程外（Wenbo 用 skill 跑实战实验做体外验证）

## 与变种和前三次实验的区别

前三次实验都是变种（无人工决策版）。本次跑本体——每个 fix 步骤的取舍判断都在 Wenbo 手里。`decision-log.md` 是本体核心、每个人工决策点都有详细记录。

## 参数适配

| 参数 | 选定 |
|---|---|
| P1 专家 A 定位（Claude-1） | Claude Skill 工程师 / Skill marketplace 实战者——**结构化指令立场** |
| P1 专家 B 定位（DeepSeek-1） | UI/UX 设计哲学研究者——**语境保留立场** |
| P2A 投资人视角（Claude-3） | Anthropic Claude Skills 团队 PM |
| P2B 单盲对象（Qwen-1） | 默认 Qwen 零上下文 |
| P3.1.1 用户视角（Qwen-2 或 DeepSeek-3） | 想用 AI coding 做 indie 产品的 vibe coder |

P1 张力维度："结构化指令 vs 语境保留"——决定 skill 是穷尽量化的指令集还是指向 + 留白的容器。

## 窗口分配

| 窗口 | 底模 | 角色 | 步骤 |
|---|---|---|---|
| Claude-1 | Claude（A1·B1） | P0 精炼 / P1.1 专家 A | P0、P1.1 |
| DeepSeek-1 | DeepSeek（A3/A4·B3） | P1.2 专家 B | P1.2 |
| Claude-2 | Claude | idea.md 执笔者 | P1.4、所有 fix、P3 全部 |
| Claude-3 | Claude | Anthropic Skills PM 批判 | P2A |
| Qwen-1 | Qwen（A3·B3） | 单盲（零上下文） | P2B |
| Claude-4 | Claude | 知情复审 | P2C |
| DeepSeek-2 | DeepSeek | 拆台（A3/A4 路径） | P2D |
| Qwen-2 / DeepSeek-3 | （新开） | vibe coder 视角校验 | P3.1.1（待定） |

跨维度硬规则满足：Claude A1·B1 × 4 + DeepSeek/Qwen A3·B3 × 3、严格版双维 divergent。

## 人工决策点 · 完成状态

| # | 位置 | 决策内容 | 状态 |
|---|---|---|---|
| 1 | P0 末尾 | P0 精炼是否忠实于原意 | 完成（接受） |
| 2 | P1.3 | 综合两份方案 + 写执笔指令给 Claude-2 | 完成（"取长补短" light-touch 综合） |
| 3 | 2A-fix | 哪些批判响应、哪些忽略 + 修改指令 | 完成（响应 1/2/5/7、自由裁量 3/4/6 → idea-v2） |
| 4 | 2B-fix | 同上 | 完成（全盘接受 8 处卡点 → idea-v3） |
| 5 | 2C-rollback | 是否回退、回退到哪 | 完成（漂移 A 显性调整、B/D 部分回退、C 双重保留 → idea-v4） |
| 6 | P2D 入口 | 是否触发 P2D | 完成（虽然三步均有重大修改、依然触发） |
| 7 | 2D-fix | 框架内 vs 框架级 | 完成（4 条 K/H 全部框架内、不回 P1 → idea-v5） |
| 8 | P2/P3 边界 | idea.md 锁定 | 完成（锁定 v5、进入 P3.1） |
| 9 | P3.1 v1 接收 | 整体转译是否接收 | 完成（接收、在此基础上调整） |
| 10 | P3.1 v1 调整 | 双侧模型清单处理 | 完成（model-recommendations.md 已落地为独立文件） |
| 11 | P3.1 v1 调整 | motion 三重防御是否加码 | 完成（加码到四重、motion-scan.sh + skill v2 第 6 步已落地） |
| 12 | P3.1.1 触发 | 是否跑 vibe coder 视角校验 | 完成（2026-08-27 决定**不跑**、实验 freeze——见 decision-log 决策点 12） |

## 执行路径 · 完成状态

```
[完成] P0 (Claude-1) → P0-refined.md
[完成] P1.1 (Claude-1 续) → P1A-expert-a.md
[完成] P1.2 (DeepSeek-1 新开、独立) → P1B-expert-b.md
[完成] P1.3 (Wenbo 综合) → 写在 decision-log
[完成] P1.4 (Claude-2 新开) → idea-v1.md
[完成] P2A (Claude-3 新开) → P2A-critique.md
[完成] P2A-fix (Claude-2 续) → idea-v2.md
[完成] P2B (Qwen-1 新开 单盲) → P2B-blind-review.md
[完成] P2B-fix (Claude-2 续) → idea-v3.md
[完成] P2C (Claude-4 新开) → P2C-review.md
[完成] P2C-rollback (Claude-2 续) → idea-v4.md
[完成] P2D 触发判断 → 触发
[完成] P2D (DeepSeek-2 新开) → P2D-devils-advocate.md
[完成] P2D-fix (Claude-2 续) → idea-v5.md
[完成] idea.md 锁定（决策点 8）→ 锁定 v5
[完成] P3.1 v1 (Claude-2 续) → design-style-extractor.skill.md
[完成] 模型清单子流程：5 模型综合 + 接受 Claude 初稿
[完成] P3.1 v2 (Claude-2 续) → design-style-extractor.skill.v2.md + model-recommendations.md + motion-scan.sh
[完成] 决策点 12（2026-08-27）→ 不跑 P3.1.1
[完成] 实验 freeze（2026-08-27）→ 保留全部产出不动、skill v2 不再迭代
```

## 当前状态：已 freeze（2026-08-27）

本实验走到 P3.1 v2 产出为止。决策点 12 判定不跑 P3.1.1，实验完结、不再迭代。

**freeze 理由**（详见 decision-log 决策点 12）：本 skill 不作为面试项目经历使用；P3.1.1 的方法论价值已由 2026-05-23 投资 skill 那次验证过，同一机制再证一次不增加说服力。

**最终产出**（根目录）：`design-style-extractor.skill.v2.md`（主交付物）+ `model-recommendations.md` + `motion-scan.sh`。过程归档在 `round1/`（P0-P2D 全产出 + idea v1-v5 + 完整对话归档 + 5 模型咨询原文）。

**本实验对方法论的贡献**（已记录在 `../../docs/longterm-and-reference.md`，未进本体）：
- P3 退化模式首现——deliverable 本身就是一份 .md 文件时，P3 的四份工程文档框架冗余。此模式在 2026-05-23 投资 skill 场景第二次复现
- P2D 在 P2A/B/C 都有重大修改的情况下仍有非平凡补抓价值——本体"触发条件 = 三步都顺利通过"可能定得过严
- P2D H4（双轨矛盾）补抓到了 P2C linear 链条上漏掉的整体矛盾
