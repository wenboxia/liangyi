# 未镜 The Other Path · 项目协议(CLAUDE.md)

> 这是未镜代码仓根目录的 CLAUDE.md。每个 spawn 出的 Claude Code teammate 在 session 启动时自动加载本文件——它是 agent teams 工作时永远在场的全局指挥棒。
>
> **本文是指挥棒,不是地图。** 地图在 `Tech-Spec.md`。本文只列纪律 + 指向。

---

## 0. 一句话项目定义

**未镜 / The Other Path** 是一个陪用户慢慢理一遍重大人生决策(要不要离职 / 分手 / 回老家)的 web 产品——**慢推演 + 反思式开场镜子 + 多路径人生预测**,服务真正纠结的少数人。

**我们做的事**:陪用户把"已经在心里反复转的那个想法"理一遍,让他自己听清自己。
**我们不做的事**:替用户做决定、预言未来、给"答案"。

---

## 1. 不可妥协立场(Red lines · 任何时候)

这 4 条是 idea 锁定的硬约束,工程实现里任何对它们的"软化"= 立即停手 escalate 给 lead → Wenbo。

1. **不预言** — 主语永远是用户。AI 不解读塔罗、不告诉用户"这意味着什么"、不给确定性陈述。任何 prompt 改动让 AI 输出预言式语句(如 "这张牌意味着 X" "你将会 Y")就是越界。
   *为什么:占卜钩子高转化、但与本产品的诚实立场不可调和。一旦让步,产品哲学崩。*

2. **Barnum 护栏** — 原型只命名路径不分类用户。AI 不输出"你是 Explorer 型"等用户标签;原型只用来给"想象路径"取名。
   *为什么:Barnum 效应让用户误以为系统懂他、产生不该有的依赖。我们要让用户更清醒、不是更被命中。*

3. **双层一致性** — 结构层与原型层冲突时,**重写原型层、不动结构层**。
   *为什么:结构(决策科学)是骨,原型(故事)是皮。皮迁就骨,不能反过来。*

4. **长期颗粒度梯度** — 长期段(>2 年)只给"故事核 + 方差形状",**不给具体事件**(不写"你会在 30 岁遇到 X")。
   *为什么:长期具体事件 = 假预言。给方差形状才是诚实的想象材料。*

进一步细则见 `Tech-Spec.md §14.6.1`(idea 锁定硬约束)与 `r2-idea-v5.md §6 / §7`。

---

## 2. 架构与模块拆分(简版)

11 个 M-* 模块,**模块间只通过 API 契约交互、不共享内存状态**。

| 代号 | 一句话职责 |
|---|---|
| M-User | 注册 / 登录 / 问卷 / 画像 / ToS 同意 / 18+ |
| M-Inference | 六步推演流水线 + 镜子模块 + 多路径生成 + 双层一致性审查 |
| M-AI | 主备模型路由 + prompt 模板 + 输出过滤 + token 预算 |
| M-Stream | 思考流卡片时序 + 快速捕捉 + 衔接 |
| M-FollowUp | 90 天 push + 2 题决策回访 + 匿名故事勾选 |
| M-Feedback | 表单 + 一键 emoji + 自动 alert |
| M-i18n | Accept-Language + localStorage + 跨设备同步 |
| M-Visual | 颜色 token + 字体 + 镜子语言 + 动效 |
| M-Error | voice 纪律 + fallback + 本地缓存 |
| M-Pay | 三档 + 决策包 + 24h 免重支付 + 退款 |
| M-Legal | GDPR / CCPA / 数据导出删除 / 18+ 校验 |

**详细架构图 + 模块边界 + 接口契约见 `Tech-Spec.md §1` 与 `§9`,任何跨模块改动前必读。**

---

## 3. 代码约定

### 3.1 目录结构(模块隔离硬约束)

每个模块的代码在独立 directory,不交叉写文件:

```
/api/user/         M-User
/api/inference/    M-Inference
/api/ai/           M-AI
/api/stream/       M-Stream
/api/followup/     M-FollowUp
/api/feedback/     M-Feedback
/api/payment/      M-Pay
/api/legal/        M-Legal
/web/              M-Visual + M-i18n(前端)
/db/migrations/    [共享 — 必须 lead 协调]
/i18n/             [共享 — 必须 lead 协调]
/core/             [共享 core: error_messages / output_filter / etc]
```

### 3.2 命名

- Python 模块名 / 文件名:`snake_case`,与 M-* 对应(如 `api/inference/pipeline.py`)
- Python 类名:`PascalCase`(`InferenceRunner`)
- API 路径:`/api/{module}/{verb}`(如 `/api/inference/start`)
- DB 表名:`snake_case` 复数(`inference_runs`,见 `Tech-Spec.md §3`)
- i18n key:`{module}.{component}.{element}`(如 `inference.step4.prompt`)

### 3.3 git / commit / 分支

- 每个 teammate 一个分支:`feature/T-Backend-Core-...` / `feature/T-Frontend-...`
- **lead 负责 merge,teammate 不直接 push 到 main**
- commit 信息一行说清"改了什么 + 哪个 PRD/Tech-Spec 章节"
- 详见 `Tech-Spec.md §14.5`。

### 3.4 共享文件清单(改动必须 lead 协调)

引自 `Tech-Spec.md §14.5`:

- `db/migrations/` — schema 改动
- `i18n/` — 翻译资源
- `core/error_messages.py` — 错误文案表(对应 `Tech-Spec.md §7.5`)
- `core/output_filter.py` — 禁用词清单(对应 `Tech-Spec.md §4.5`)

teammate 想改这 4 类文件之一 → 先 SendMessage 通知 lead。

---

## 4. AI 调用层的硬约束(关键)

任何对以下的修改 → **立即停手 escalate**:

| 红线 | 为什么 / 出处 |
|---|---|
| 镜子层 system prompt 的"主语永远是用户" | 让步 = 直接违反"不预言"。见 `Tech-Spec.md §4.2 §15.1` |
| 输出过滤禁用词清单(中英) | 不许为"输出更顺"放松。清单出处:`Tech-Spec.md §4.5.1`,中英完整列表 + PRD-4 §3.3.3 |
| 双层一致性审查 4 步流程 | 不许因"性能优化"绕过。见 `Tech-Spec.md §4.6` |
| 长期段(>2 年)的"只给方差不给事件" | 见 `Tech-Spec.md §15.4` |
| Step 4(可能性档位)必填 | AI 不得"友好地"替用户填。见 `Tech-Spec.md §15.3` |
| Step 6(Pre-mortem)必填 | AI 不得替用户写。见 `r2-idea-v5.md §6` |
| 单次完整推演 token 成本 ≤ ¥0.5 | 单位经济硬上限。见 `Tech-Spec.md §4.7 / §15.6` |
| 模型 fallback 链 | 不允许 teammate 自己换主模型。见 `Tech-Spec.md §4.4` |

**任何让 AI 表现得"更懂用户、更温暖、更主动"的 prompt 改动**——先想一遍是否触及上述任何一条。如果触及,这个改动大概率错了。

---

## 5. 测试与质量门槛

- 单元测试必须 pass(见 `Tech-Spec.md §12.1`)
- **关键 prompt 输出过滤回归测试必须 pass**(见 `Tech-Spec.md §12.4 / §4.5`)——这是 voice 纪律的工程护栏,优先级与单测同级
- 错误注入测试覆盖 `Tech-Spec.md §13.1` 全部场景
- 任何对核心 prompt 模板 / 禁用词清单 / 一致性审查规则的改动 → 走专门 review,**不能 teammate 自己 commit**,需要 lead 看过 + 跑过过滤回归测试
- 错误文案必须用 `Tech-Spec.md §7.5` 的硬编码表,**不允许后端把原始错误码 / API 名 / 模型名 / token 数 / queue 位置返回到前端**
  *为什么:任何技术细节进 user-facing voice = 破坏"陪你慢慢理"的产品语调。*

---

## 6. agent teams 协作规范

### 6.1 角色分工

直接引 `Tech-Spec.md §14.2` 的 4 个 teammate 角色表:T-Backend-Core / T-Backend-Aux / T-Frontend / T-Devops-Legal。临时 slot:T-Test / T-Prompt(详见 §14.2)。

### 6.2 任务认领

- 用 task list 自动认领(参考 Claude Code 官方 agent teams 文档)
- 不需要 lead 显式分配每条任务——lead 只在冲突 / 阻塞时介入
- task list 来源:`Tech-Spec.md §14.3`(Phase 1-4,~12 天到 MVP)

### 6.3 跨 teammate 沟通

- 直接用 SendMessage **互通**,不需要全部走 lead
- 仅 §6.4 列出的事件需要 escalate 到 lead
- 接口契约冲突:先在 teammate 之间讨论一次,无法收敛 → escalate

### 6.4 何时 escalate 到 lead → Wenbo(必须)

直接引 `Tech-Spec.md §14.6.4` 表格:

| 场景 | 例子 |
|---|---|
| 产品方向调整 | 用户反馈想要 A、PRD 要 B,改不改? |
| Idea 锁定后的硬约束改动 | "Step 4 让 AI 替写一点更好用" |
| 外部 API 选型超预算 | 想换 Claude Sonnet 4.6 做镜子层 |
| PRD-4 锁定纪律的修订 | "禁用词太严了想去掉'命中'" |
| 一键反馈集中负面信号 | Step 5 的 ☹️ 占了 40% |

### 6.5 lead 可以自决的事

引自 `Tech-Spec.md §14.6.5`:接口字段命名 / HTTP status code / 模块内实现选择(Pydantic vs dataclass) / 测试 edge case 补充 / DB 索引性能优化 / 不改契约的 refactor。

### 6.6 冲突解决

1. teammate 之间先 SendMessage 沟通一次
2. 无法收敛 → escalate lead,lead 看是否触及 §14.6
3. 触及 §14.6.4 → lead escalate Wenbo
4. 触及 §14.6.1-3 → lead 直接拒绝 + 引用对应章节

---

## 7. 不要做的事(综合 red lines)

下列任何一条触及就停手:

1. 不许引入 PRD-4 之外的新功能(连讨论都先 escalate)
2. 不许改 idea 锁定后的硬约束(`Tech-Spec.md §14.6.1`)
3. 不许改 PRD-4 锁定方向(`Tech-Spec.md §14.6.2`,含方案 B 镜子语言 / C 方案国际化 / 付费结构 / 决策回访极简 / 双反馈入口)
4. 不许跳过单测、不许跳过 prompt 输出过滤回归测试
5. 不许把 Step 4 / Step 6 的"用户填入"改成"AI 替用户填",哪怕是为了"用户体验更好"
6. 不许在任何 user-facing 文本(marketing / ToS / 错误提示 / Onboarding / i18n key 文案)里出现禁用词:
   - 中文:意味着 / 预示 / 注定 / 命中 / 命运 / 应该 / 一定 / 必然 / 你将 / 注定要 / ……(完整清单见 `Tech-Spec.md §4.5.1` zh_blacklist)
   - 英文:means / signifies / destined / predicts / shall / fate / must / will surely / ……(完整清单见 §4.5.1 en_blacklist)
7. 不许在错误提示里暴露技术细节(API 名 / 模型名 / token 数 / queue 位置 / stack trace)——错误时刻文案必须用 `Tech-Spec.md §7.5` 表格
8. 不许把 dev-guide / Tech-Spec / PRD-4 当作"可以随便补的杂项"——这些是新 spawn teammate 的防漂移护栏,改它们等于改纪律
9. 不许做 v6+ 的功能(暗色模式 / native iOS App / 紫微星盘 / AI 解牌 / 真人陪伴 / 朋友圈分享卡 / SEO 优化等)。完整 v6+ 清单见 `PRD-4.md §10` 与 `Tech-Spec.md §16.1`
10. 不许在文案 voice 里出现"被迫 / 被动 / 系统建议 / 我们认为"等替用户做主语的措辞——voice 用法表见 PRD-4 §5
11. 不许在镜子层 / 推演层 / 思考流任何位置写"AI 解读塔罗"的逻辑——塔罗永远是给用户投射用,不是给 AI 解读用(`Tech-Spec.md §15.1 / §15.9`)

---

## 8. 文档导航

按必读顺序:

| 文档 | 角色 | 何时读 |
|---|---|---|
| `r2-idea-v5.md` | idea 真源(只读、锁定) | spawn 时必读 §1-§11 |
| `PRD-4.md` | 产品需求(锁定) | spawn 时必读全部 |
| `Tech-Spec.md` | 技术方案地图(本文件指向的目的地) | spawn 时必读 §1 §3 §9 + 自己模块对应章节 |
| `Tech-Spec.md §15` | 关键设计决策的"为什么"(防漂移最后护栏) | fix bug / 重构 / 觉得"这条规则没必要"时必读 |
| `Tech-Spec.md §14.6` | 不能动清单 | 触及就停手问 lead |
| `dev-guide.md`(后续 lead 起草) | 工程踩坑记录 + 决策更新 | 出 bug / 重构前查阅 |

锁定的 idea 和 PRD-4 是**只读**——不允许 teammate / lead 单方面修改。任何修订需要 Wenbo 显式批准 + 走 P2 critique 流程。

---

## 9. Wenbo 在哪里(operational note)

- Wenbo = lead session 的发起者 + **唯一人类决策者**
- Wenbo **不写代码**,不是 teammate 的同事
- 触及 `Tech-Spec.md §14.6.4` 列出的事 → lead 立即 escalate
- 其他时候不打扰——lead 应当能用 §14.6.5 范围内的自决权处理大部分日常工程
- 联络方式:lead session 与 Wenbo 直接对话;teammate 不直接联系 Wenbo,走 lead

---

## 10. 灵魂提醒

> **如果某个技术决策让你觉得"产品好像没那么贴心了 / 没那么允许了 / 没那么诚实了"——那个决策大概率错了。**
>
> 未镜不是给所有人用的产品。它服务真正纠结的少数人,让他们在做决定前能听清自己一次。
>
> 我们靠诚实活,不靠钩子活。每一次工程取舍,问一遍:"这是让用户更清醒,还是更被命中?" 选前者。

---

*本协议与 r2-idea-v5 / PRD-4 / Tech-Spec 同源同生。任何修订需要 Wenbo 批准。*
