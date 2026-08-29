# 全自动变种 · 真实人生决策模拟器 · 完整 P0-P3 跑通(场景四)

## 时间
2026-04-26

## 跑这个的目的

**这次不是对照实验、是真用方法论跑一个产品**——前三次跑（美团 / Agent 评测 / ExamSniper）都是在某条规则上做对照验证（终止条件 / Kill shot 分级），这一次只走主线、用全自动变种 + Kill shot 分级新规则跑一个完整产品 idea，产出可以直接用于工程实施的 4 份文档（PRD / Tech Spec / CLAUDE.md / Dev Guide）。

P4 是否跑由 Wenbo 决定——不在这次默认范围。

## 场景

**真实人生决策模拟器**——C 端 AI 工具。用户填一份"create yourself"问卷（性格 + 基本信息）+ 提一个当前要做的决策（小到吃什么、大到换工作 / 分手 / 生育），产品输出：

1. 对当前这次决策的建议
2. 不同选项对用户未来人生路径的影响（A 选项短期 / 中期 / 长期、B 选项短期 / 中期 / 长期、…），以"人生画像"形式呈现

**核心机制设计灵感**：
- create yourself 部分参考 [yourself-skill](https://github.com/notdog1998/yourself-skill)
- 预测 / 决策建议部分参考中西方占卜方法（紫微 / 易经 / 塔罗），参考 [taibu](https://github.com/hhszzzz/taibu) 和 [chatgpt-tarot-divination](https://github.com/dreamhunter2333/chatgpt-tarot-divination)——不是单纯 AI 推理 + 给建议，而是让 AI 学会这套占卜技巧来"算"

**产品定位张力**：科学决策（认知偏差 / 概率 / Bayesian 更新）vs 占卜命理（象征 / 原型 / 内在投射）—— 这两条路线的对撞是 P1 专家 A/B 的核心张力源。

**P0 输入排除项**（剥到 P3 再加回）：
- 实现路径（Claude Code agent teams 多角色开发）
- 上线路径（Hugging Face Space → Apple App Store）
- 这些是工程展开层、不进 P0-P2 的 idea 探讨

## 参数替换

| 参数项 | 替换内容 |
|---|---|
| **P1.1 专家 A 定位** | **决策科学派**——立场:人生决策本质是不确定性下的选择问题,产品价值 = 帮用户用结构化方式拆解决策、识别认知偏差、用概率思维对路径做模拟。倾向 Kahneman & Tversky 行为决策学、Annie Duke "Thinking in Bets"、Decision Trees / Pre-mortem / Bayesian 更新;延伸方向是"基于性格画像 + 决策上下文,给出贝叶斯式的多路径概率分布"。现实流派对照:沃顿 / 哥伦比亚商学院决策科学、《思考,快与慢》、《超预测》派 |
| **P1.2 专家 B 定位** | **东西方占卜命理整合派**——立场:人生决策不是概率问题、是用户当下处境与内在自我的镜像反射;产品价值 = 用占卜的象征语言、原型、仪式感,让用户被"映照"从而获得决策清晰度。倾向塔罗大阿尔卡纳的人生原型 + 紫微斗数的命盘格局 + 易经卦象推演 + Jungian archetypes;延伸方向是"用户付费要的不是统计真相、是被看见的体感"。现实流派对照:荣格 + 现代塔罗实践者、紫微斗数命理师、Co-Star、占卜垂类 App 派 |
| **P2A 批判视角** | **C 端 AI 应用 VC + 资深 C 端 PM 复合视角**(Lightspeed / a16z 投 Character.ai / Replika 那条线)。关切维度:PMF 验证(C 端"决策辅助"是真需求还是伪需求、用户决策时第一反应是不是 AI)、留存逻辑(决策完成后用户为什么还回来、单次决策不形成复购)、付费意愿(C 端 AI 心理 / 占卜类产品付费天花板)、AI 伦理 / 监管风险("AI 算命"在中国大陆 / iOS App Store 双轨监管下的合规边界、心理 / 命运类 AI 应用最近的下架案例)、护城河(为什么不是再一个套壳 GPT、占卜 prompt 工程能否构成壁垒)、单位经济(模拟多路径推理的 token 成本能否撑 C 端定价) |
| **P2B 单盲对象** | **28-35 岁城市白领、面临人生级真实节点决策**——例:要不要离职 / 要不要分手或结婚 / 要不要生孩子 / 要不要回老家 / 要不要做出重大职业转型。这群人是真正付费做塔罗 / 心理咨询 / 命理咨询的核心用户、对"AI 算命"有警惕又有好奇、有一定可支配收入但同时被信息过载困住、不会脑补"作者意图"、对 prompt 表达不清的地方会立刻迷失。Qwen-1 严格按硬性 prompt 纪律走(不脑补、只报告第一眼困惑、不提优化建议、不判断卡点严重度) |
| **P3.1.1 用户反馈视角** | 同 P2B 单盲对象同一群体、不同实例(用 Qwen-2 模拟)。读 PRD 后回答:作为 28-35 岁城市白领面临人生级决策、能不能理解这产品要解决我什么问题、会不会愿意用、哪里是"我根本不会这么想"的(比如有没有产品话术让我感到被冒犯 / 觉得太玄学不可信 / 觉得太机械没共鸣) |
| **P3 PRD 评估指标** | 分两层——<br>**内测期**(Hugging Face Space 自用阶段):单次交互完成率(用户填完问卷 + 提决策 + 看完输出)、"被映照感"(用户主观打分:这个 AI 模拟出的人生画像是不是说到我心里)、决策路径合理性(模拟出的多路径有没有逻辑支撑)、占卜与决策科学融合的"违和感"是否过高<br>**上线期**(App Store):D7 / D30 留存、决策完成转化率(用户从填问卷到看完路径模拟的完成漏斗)、付费转化率(免费基础版 + 付费深度版的转化)、社交分享率(C 端社交传播)、**决策回访率**(用户在做完决策一段时间后回来反馈"实际走出的路径和模拟的像不像"——这是本 idea 独有的可验证回路、其他 C 端决策 / 命理产品没有这条) |

## 自动化替代清单(同变种 5.1 节)

| 原人工决策点 | 位置 | 自动化替代 |
|---|---|---|
| 审 P0 精炼 | P0 末尾 | 跳过 |
| 综合两份专家方案 + 写执笔指令 | P1.3 | Claude-2 读两份方案自行综合 |
| 批判取舍(响应 / 忽略) | 2A-fix / 2B-fix / 2D-fix | Claude-2 自行判断,默认"能改则改" |
| 是否回退 | 2C-rollback | Claude-2 自行判断,默认"P2C 指出漂移就回退" |
| P2D 触发条件 | P2D 入口 | 强制触发 |
| 框架内 vs 框架级判定 | 2D-fix | Kill shot 分级 + 终止条件(详见 prompts/P2D-fix.md) |
| idea.md 锁定 | P2/P3 边界 | 2D-fix 跑完自动锁 |
| P3.1.1 用户视角校验 | P3.1.1 | 保留——但用 AI 模拟用户(Qwen-2)、不需要真人 |

保留的硬规则:
- AI 窗口独立(Claude-1 ~ Claude-4、DeepSeek-1/2、Qwen-1/2)
- 底模坐标跨维度(Claude A1·B1 + DeepSeek A4·B3 + Qwen A3·B3,严格版满足)
- P2B 单盲零上下文 + 硬性 prompt 纪律(底线规则)
- P2D 拆台由 A3/A4 模型扮演(DeepSeek-2)、不许软化、3-5 条根本论据

## 工程展开层约束(P3 时回灌)

以下内容是 idea seed 自带、但属于工程展开层、P0-P2 的 idea 探讨阶段不引入、到 P3.2 Tech Spec / P3.4 Dev Guide 时显式回灌进 prompt:

- **MVP 上线路径**:先在 Hugging Face Space 上线、Wenbo 自用验证 → 最终目标 Apple App Store
- **开发模式**:全程使用 Claude Code agent teams 模式、分配多角色(前端 + 后端 + 测试 + PM 等)、Wenbo 只参与决策、不写代码
- **核心实现参考**:
  - Create yourself 流程参考 [yourself-skill](https://github.com/notdog1998/yourself-skill)
  - 占卜算法实现参考 [taibu](https://github.com/hhszzzz/taibu) 和 [chatgpt-tarot-divination](https://github.com/dreamhunter2333/chatgpt-tarot-divination)

## 实际执行路径(全部已完成)

**Round 1**:已跑完——P0 → P2D-fix,产出 idea-v1 ~ v5。Wenbo 在 4 段位置人工介入(重设目标尺度 / 提商业模型 / P2C-rollback 决策权拉回 / P2D-fix 战略调整含不进大陆 + 塔罗回归)
**Round 2**:已跑完——不是"回 P1",是 Wenbo 判断"v5 还需验证、回 P2 重压一轮"。用全新 Claude-3'/Claude-4'/Qwen-1'/DeepSeek-2' 窗口跑完整二次 P2 链条(Claude-2 续保执笔连贯),产出 r2-idea-v1 ~ v5,8 处比 round-1 更 solid
**P3 四份文档**:已产出——PRD(含 PRD-2/3/4 三轮迭代) / Tech-Spec / CLAUDE.md / dev-guide,在 docs/

**注**:本场景实质是"变种骨架 + 人保留 fix 决策权"的**混合形态**,不是纯变种(见 `../../docs/longterm-and-reference.md` 长期观察第 9 条)。`docs/user-validation.md` 目前为空——P3.1.1 用户视角校验的产出没有归档。

## 档案清单

```
2026-04-26-life-decision-simulator-fullrun/
├── README.md                           (本文件)
├── seed-idea.md                        (P0 原始输入,剥掉技术细节后的 idea seed)
├── prompts/
│   └── P2D-fix.md                      (Kill shot 分级 prompt 副本)
├── round-1/
│   ├── P0-refined.md
│   ├── P1A-expert-a.md                 (决策科学派方案)
│   ├── P1B-expert-b.md                 (占卜命理整合派方案)
│   ├── idea-v1.md                      (Claude-2 P1.4 综合产出)
│   ├── P2A-critique.md                 (Claude-3 投资人批判)
│   ├── idea-v2.md                      (Claude-2 2A-fix 后)
│   ├── P2B-blind-review.md             (Qwen-1 单盲)
│   ├── idea-v3.md                      (Claude-2 2B-fix 后)
│   ├── P2C-review.md                   (Claude-4 知情复审)
│   ├── idea-v4.md                      (Claude-2 2C-rollback 后)
│   ├── P2D-devils-advocate.md          (DeepSeek-2 拆台)
│   ├── P2D-fix-judgment.md             (Claude-2 Kill shot 分级判定)
│   └── idea-v5.md                      (锁定版,若 0 或 1 个 kill shot;否则进 round-2)
├── round-2/                            (仅当 round-1 触发回 P1 才存在)
│   └── ... (路径 1:新 P0 输入只带 seed-idea.md)
└── docs/                               (idea 锁定后产出)
    ├── PRD.md                          (P3.1)
    ├── user-validation.md              (P3.1.1 Qwen-2 模拟用户反馈)
    ├── tech-spec.md                    (P3.2,加回 agent teams + HF / App Store 约束)
    ├── CLAUDE.md                       (P3.3)
    └── dev-guide.md                    (P3.4)
```

## 和前三次实验的区别

| 维度 | 前三次(美团 / Agent 评测 / ExamSniper) | 本次(决策模拟器) |
|---|---|---|
| 目的 | 验证某条规则(终止条件 / Kill shot 分级) | 真用方法论跑出可工程化的产品 |
| 跑法 | X / Y 双实验对照 | 只走主线、Kill shot 分级新规则 |
| 事后小调用 | 跑(D1 / D2 喂老 / 新规则) | 不跑 |
| 4 件比较 | 跑 | 不跑 |
| 跑到哪一步 | P0 → idea-v5(P2 末尾锁定) | P0 → P3 四份工程文档全部 |
| Round 限制 | 终止条件兜底 Round 2 | 同前 |
| P3.1.1 | 不在前三次范围 | 用 Qwen-2 模拟 |
