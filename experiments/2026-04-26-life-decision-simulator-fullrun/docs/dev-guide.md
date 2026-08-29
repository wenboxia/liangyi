# 未镜 The Other Path · Dev Guide

> 这份文档不是给"新加入的工程师"。本项目全程由 Claude Code agent teams 开发,Wenbo 是唯一人类、不写代码。
>
> **读者两类**:
> 1. **未来的 Wenbo 自己**——3 个月后回头维护项目、做 HF Space 部署、想自己改一行 prompt 时
> 2. **新 spawn 的 teammate**——它在 fix bug / 加 feature / 重构时,需要比 CLAUDE.md 更深一层的"为什么这么设计 + 谁挑战过 + 改它要走什么流程"
>
> **本文档与 r2-idea-v5 / PRD-4 / Tech-Spec / CLAUDE.md 不同——它是活的**,会随 Wenbo 与 lead 实操踩坑随时更新。

---

## 1. 项目 5 分钟理解

### 1.1 这是什么

**未镜 / The Other Path** ——陪用户慢慢理一遍重大人生决策(要不要离职 / 分手 / 回老家)的 web 产品。

三件事组合:
- **慢推演**(六步流水线:框定 → 拓展 → 不确定性 → 可能性认领 → 偏差审计 → Pre-mortem)
- **反思式开场镜子**(可选 30 秒,塔罗作为反思投射触发器,**不是预言**)
- **多路径人生预测**(短期具体、长期只给故事核 + 方差,类比天气预报 7 天具体、月度趋势模糊)

完整定义见 `r2-idea-v5.md §2 / §3`,产品需求见 `PRD-4.md §1-3`。

### 1.2 解决什么问题 / 给谁用

服务真正纠结的少数人——**真酝酿期用户 + 事后压力测试用户**(round-2 P2D #1 kill shot 后扩展的双使用情境)。

不服务的人:
- 想要 24/7 陪伴(去找 Replika / Pi)
- 想要直接答案(本产品没有)
- 不想花 30-60 分钟认真填(本产品最低门槛是认领 Step 4 / Step 6)

完整用户画像见 `r2-idea-v5.md §4.1`。**这个画像是设计假设,首批 50 用户深访验证**。

### 1.3 当前阶段

| 阶段 | 状态 |
|---|---|
| Idea 锁定(r2-idea-v5) | ✅ 完成 |
| PRD 锁定(PRD-4) | ✅ 完成 |
| Tech Spec 锁定 | ✅ 完成 |
| CLAUDE.md(agent teams 协议) | ✅ 完成 |
| HF Space MVP 开发 | ⏳ 待启动(Wenbo 启动 lead session) |
| Wenbo 自用 + 5-10 种子用户 | ⏳ |
| 50 用户深访 milestone | ⏳ |
| 100 付费用户 PMF 验证 | ⏳ |
| 独立部署迁移(Vercel + Railway) | v2+ |

### 1.4 为什么这样做

未镜不是 VC 故事,是 **indie 产品**。Wenbo 没指望它赚多少钱,目标是做一个**自己用得上、少数人用得上、做得诚实**的工具。

商业上限(诚实):~100 付费用户、~¥3,500-5,500/年净利。详见 `r2-idea-v5.md §10.3`。

---

## 2. 与方法论文档的关系

| 文档 | 角色 | 改动权限 | 谁读 / 何时读 |
|---|---|---|---|
| `r2-idea-v5.md` | idea 真源(锁定、只读) | Wenbo 显式批准 + 走 P2 critique 流程 | 所有 teammate spawn 时必读 §1-§11 |
| `PRD-4.md` | 产品需求(锁定、只读) | 同上 | 所有 teammate spawn 时必读 |
| `Tech-Spec.md` | 技术地图(锁定、只读) | 同上(工程实施细节可由 lead 在 §14.6.5 范围内调整) | spawn 时必读 §1 §3 §9 + 自己模块对应章节 |
| `CLAUDE.md` | agent teams 全局协议(永远在场) | 锁定 — 改动需要 Wenbo 批准 | 每个 teammate session 自动加载 |
| `dev-guide.md`(本文) | 踩坑 + 决策更新 + 操作手册 | **活文档**,Wenbo / lead 实操中持续更新 | fix bug / 重构 / 觉得"这条规则没必要"时;Wenbo 启动 / 维护 / 排错时 |

**纪律**:idea / PRD / Tech-Spec 是真源,本文是注释和操作手册——本文不能与真源冲突。冲突时以真源为准,本文需要修正。

---

## 3. 关键设计决策的"为什么 + 踩坑视角"

> **本节是新 teammate 防漂移的最后一层护栏。**
>
> 与 `Tech-Spec.md §15` 的关系:Tech Spec §15 给设计 rationale(背景痛点 + 替代 + 选择 + 不能改的边界);本节在每条之上多写两层——
>
> a. **历史挑战**:谁在 round-1 / round-2 P2 critique 中挑战过这条 / 论据是什么 / 为什么仍然没改 / 哪个文档锁定了这条
> b. **如果你想改**:具体的 escalate 路径(不是"找 lead",是"找 lead 报告 X / 触及 Y 章节 / 准备 Z 论据")
>
> **最低门槛**(适用全部 11 条):任何想改这些规则的 PR 都需要先回答一句话——"未来的 Wenbo 看到 v6 应该是诚实的,还是被推动的?" 选前者。

---

### 3.1 为什么开场镜子用反思式塔罗而不是 AI 解牌

**Tech Spec §15.1 给的 rationale**:占卜钩子转化高但与"不预言"纪律不可调和;反思塔罗保留具象触发力量、不让 AI 算。

**历史挑战**:
- **round-1 P2A #4**(投资人视角):"占卜导向的合规风险被严重低估"——质疑产品任何与塔罗相关的元素。处理:idea-v2 完全去玄学
- **round-1 P2D**(魔鬼代言人):反过来追问 P0 初心,指出"完全去玄学丢失了开场反思的具象触发"。处理:idea-v5 引入"开场镜子"模块,**主动认领反思塔罗框架**(选 Plan B)
- **round-2 P2A #3**:"The Tower 样例自证产品就是反思塔罗"——这次是正向的,要求显式认领、不要藏。处理:r2-v5 §5.3 主动认领反思式塔罗框架,不再回避
- **round-2 P2C 第四点**:反思塔罗的认识论说明被 r2-v3 删除,P2C 指出删除后语义滑动。处理:r2-v4 恢复认识论说明

**锁定来源**:`r2-idea-v5.md §5.3 + §6` + `PRD-4.md §3.3 + §11.5(方案 B)` + `CLAUDE.md §1`(不预言红线)。

**如果你想改这条**(例如想让 AI 解读塔罗、想给"AI 主动告诉用户这张牌的意思"):
1. **触及 `Tech-Spec.md §14.6.1` 第 2 条(不预言)+ `§15.1` 不能改的边界**
2. lead 立即拒绝并 escalate Wenbo
3. 若仍要讨论,需要准备的论据:
   - 为什么这次不是回到 round-1 P2A 已经反对过的占卜路线
   - 反思塔罗 vs AI 解读塔罗在用户认知上的差异、有没有用户验证数据
   - "AI 解牌"在 v6+ `Tech-Spec.md §16.1` 已被列为"永久不做"——为什么这次不一样
4. **此条永久不能改**——它不是优化空间,是产品身份

---

### 3.2 为什么原型只命名路径不分类用户

**Tech Spec §15.2 给的 rationale**:Jungian 原型若用作"你是 X 类型的人"直接落入 Barnum / Forer 效应陷阱(MBTI 在学界被钉的事)。

**历史挑战**:
- **round-1 P2D #1**(K + H 级):"Jungian 原型本身就是 Barnum"——从根本上质疑用原型这套东西的合法性。处理:idea-v5 框架内护栏——`§5.1` 删除"主导原型识别",原型只命名路径
- **round-2 P2C 第二点**(漂移):ICP 描述从中间人群 → 双峰人群,Barnum 风险因 ICP 模糊化而上升。处理:r2-v4 §3 加双峰人群总和密度说明 + 强化 Barnum 护栏修辞

**锁定来源**:`r2-idea-v5.md §6 + §8` + `PRD-4.md §3.1 §3.3` + `CLAUDE.md §1`(Barnum 护栏红线)。

**如果你想改这条**(例如想做"用户主导原型识别"问卷题、想在用户档案里存"用户原型"字段、想让 AI 输出"你是 Explorer 型"):
1. **触及 `Tech-Spec.md §14.6.1` 第 1 条(Barnum 护栏)+ `§15.2` 不能改的边界**
2. lead 立即拒绝
3. 若仍要讨论,需要准备的论据:
   - 为什么这次不是回到 idea-v1 已经被 P2D #1 钉死的路线
   - MBTI 类型学在学术界的地位:你的设计如何系统性规避 Forer 效应
   - 用户验证数据(50 用户深访中是否反映"想被分类")
4. **本条强相关于产品诚实立场,不是 UX 优化空间**

---

### 3.3 为什么 Step 4 用 5 档可能性 + 滑块而不是让用户填百分比

**Tech Spec §15.3 给的 rationale**:让真用户填具体百分比(如"35%")是认知摩擦极高的动作——他们没有 calibrated probabilities,会写假数字,认知干预没发生。

**历史挑战**:
- **round-1 P2B #3**(盲读用户):"让我自己填概率我真填不出来"——具体盲点反馈。处理:idea-v3 改为 5 档语言档位 + 滑块
- **round-1 P2C B 项**(漂移):担心 5 档会软化"用户认领自己的不确定性"这条 P0 力度。处理:idea-v4 加回认识论文字宣言("用户被迫直面自己的不确定性直觉"——这个语言留着)
- **隐含张力**:UX(让用户能填出来)与 P0 力度(强迫用户认领自己的判断)。这条规则的妥协是把"必填"放在档位上、不放在精确数字上

**锁定来源**:`r2-idea-v5.md §6` + `PRD-4.md §3.4` + `Tech-Spec.md §15.3` + `CLAUDE.md §4`(Step 4 必填红线)。

**如果你想改这条**(例如想让 AI 替用户填档位、想去掉滑块、想让 Step 4 变成可跳过):
1. **触及 `Tech-Spec.md §14.6.1` 第 5 条(Step 4 必填)+ `§15.3` 不能改的边界**
2. **特别注意**:任何想让 Step 4 "用户体验更顺"而把"用户认领"软化为"AI 推荐 + 用户确认"的提议——`CLAUDE.md §7 第 5 条`明确禁止
3. lead 立即拒绝
4. 若仍要讨论,需要准备的论据:
   - 用户认领的认知干预效果数据(无论是 50 用户深访还是行为 metrics)
   - 为什么这次不是回到 idea-v1 已经被 P2B #3 反对过的"用户自填百分比"
   - 替代方案是否仍然保留"用户主动认领"这条 P0(不是 AI 替写)

---

### 3.4 为什么长期段(>2 年)不给具体事件

**Tech Spec §15.4 给的 rationale**:5 年后的世界、技术、用户都会变。任何号称"5 年后能告诉你具体事件"的产品都是在编故事——直接落入 Barnum 陷阱。

**历史挑战**:
- **round-1 P2B #7**:"长期只给故事核算回避吗"。处理:idea-v3 措辞重写、明确这是**认识论位置**不是"回避"
- **round-2 P2D #5**(K + M):"短期具体 + 长期模糊读起来是产品在长期段瞎编"——格式自毁。处理:r2-v5 §7 加"颗粒度梯度的认识论位置"显式声明 + 类比天气预报 + §2 钩子加细化("看见 = 路径形态、成长课题、短期具体行为,不是 2031 年 7 月你具体遇到谁")。**关键**:钩子和长期格式 explicitly tie together
- **天气预报类比的来由**:r2-v5 §7 显式引——7 天具体 + 月度趋势模糊,用户接受这是诚实边界。这个类比是用户教育的核心比喻

**锁定来源**:`r2-idea-v5.md §7` + `PRD-4.md §3.5` + `Tech-Spec.md §15.4` + `CLAUDE.md §1`(长期颗粒度梯度红线)。

**如果你想改这条**(例如想让长期段输出"2031 年 7 月你会遇到 X""5 年后你会在硅谷 Senior PM"):
1. **触及 `Tech-Spec.md §14.6.1` 第 4 条(长期颗粒度梯度)+ `§15.4` 不能改的边界**
2. lead 立即拒绝
3. 若仍要讨论,需要准备的论据:
   - 为什么模型在长期段输出具体事件不是 Barnum 编造
   - 为什么这次不是回到被 round-2 P2D #5 钉死的"格式自毁"
   - 用户对"长期模糊"的实际接受度数据(50 用户深访中是否反映抗拒)
4. 输出过滤层 `core/output_filter.py` 必须保留长期段事件检测——任何工程改动都要保证这个 filter 不被绕过(`Tech-Spec.md §4.5`)

---

### 3.5 为什么不进大陆 / 但仍然主要服务大陆背景中文用户

**Tech Spec §15.5 给的 rationale**:大陆监管严(《生成式 AI 服务管理暂行办法》)。但产品是中文为主,主要用户实际是大陆背景。

**这条 evolved 过两次,要把双层修正都写明**:

**第一次修正(round-1 P2D #4 + Wenbo 战略性化解)**:
- P2D #4(K + H 级):"占卜类应用 + 大陆监管,合规风险"
- 处理:idea-v5 §4.3 战略性规避——"不进中国大陆官方市场"。理由是合规风险

**第二次修正(round-2 P2D #3 + Wenbo 第二次修正)**:
- P2D #3(K + M 级):"海外华语 7 碎片市场,每个 300-500 付费天花板"
- critic 的隐含假设:"产品的目标用户 = 海外原生华人 diaspora"——确实碎片化
- **Wenbo 战略性修正**:产品的实际目标用户是"大陆背景中文用户"(包括大陆 VPN + 海外留学/工作/移民)——是一个比 7 碎片市场大得多且更同质的市场。
- 处理:r2-v5 §4.1 + §4.3 重写明确这一点。**官方境外 + passive 服务大陆 VPN 用户**(类似 ChatGPT / Notion / Discord 的标准 posture)

**两次修正合起来的最终立场**:
- **不**:不上大陆应用市场 / 不接大陆境内支付通道 / 不做大陆 SEO/投放
- **但也不**:严格 IP-block 大陆访问 / 假装不知道大陆用户存在
- **意图**:合规上是境外服务,产品上承认主要用户是大陆背景中文人群

**锁定来源**:`r2-idea-v5.md §4.3` + `PRD-4.md §8` + `Tech-Spec.md §15.5` + `CLAUDE.md §1`(虽不直接列、隐含在产品立场中)。

**如果你想改这条**(例如想上大陆应用市场、想做大陆 SEO 投放、想接微信支付国内通道、想 IP-block 大陆访问):
1. **触及 `Tech-Spec.md §14.6.1` 第 7 条(不进中国大陆官方市场)+ `§15.5` 不能改的边界**
2. lead 立即 escalate Wenbo
3. 这条与产品的合规存活相关,**任何想"主动进大陆"的提议都是产品级判断、不是工程级判断**
4. 想"严格 IP-block 大陆"的提议也不行——会切断主要用户群

---

### 3.6 为什么用国产廉价模型而不是 Claude / GPT-5

**Tech Spec §15.6 给的 rationale**:Claude / GPT-5 单次推演成本可能 $0.5+(¥3.5+),对 indie 100 付费用户的单位经济不合理。

**历史挑战**:
- **round-1 P2A #6**:"单位经济负毛利"。处理:idea-v3 推演规模砍 + Wenbo 明确 indie 定位用国产便宜 AI
- **隐含张力**:Wenbo 个人偏好用 Claude(他自己日常用)→ 但产品定位 indie 商业可持续 → 选国产模型 + 重要环节(镜子凝练)用 Qwen-Max(贵但仍便宜于 Claude)

**锁定来源**:`r2-idea-v5.md §10.1` + `Tech-Spec.md §4.4 §4.7 §15.6` + `CLAUDE.md §4`(token 成本 ≤ ¥0.5 红线)。

**如果你想改这条**(例如想默认用 Claude Sonnet 4.6 / GPT-5、想接 Anthropic API):
1. **触及 `Tech-Spec.md §14.6.3` 第 1 条(单次完整推演 ≤ ¥0.5)+ `§14.6.4` 表格(外部 API 选型超预算)**
2. lead **必须** escalate Wenbo——这是 lead 自己不能决定的事
3. 若仍要讨论,准备的论据:
   - 实测的成本估算(用现版本的 token 用量 × 新模型单价)
   - 100 付费用户场景下的年度成本影响
   - 模型质量 vs 成本的具体对比(在哪些 step 上质量差距明显)
4. **可接受的折衷**:某个特定 step(如镜子凝练)单独换 Claude/GPT,但需要 Wenbo 显式批准

---

### 3.7 为什么不做 native 英文 rewrite(英文是人工翻译)

**Tech Spec §15.7 给的 rationale**:Native rewrite 需要 native 英文 copywriter,成本高,且 v1 主用户是中文用户。

**历史挑战**:
- **round-2 P2A #6**:"双语同口径在心理类无成功先例"——质疑做英文这件事
- **Wenbo 介入**:"为什么不能中英都做"——拒绝完全砍英文
- 处理:r2-v5 §4.3 保留中英双语,**明确英文是人工翻译版本**——质量优于机翻但不是 native rewrite。前期接受翻译腔
- **Onboarding 屏 3** `PRD-4.md §4.2.6`:对英文用户显式标注"This is a human translation, not a native rewrite. Some phrasing may feel slightly translated."(诚实标注)

**锁定来源**:`r2-idea-v5.md §4.3` + `PRD-4.md §4.2.6 §12 §12.4`(等价性) + `Tech-Spec.md §15.7` + `Tech-Spec.md §16.1`(v6+ 才考虑 native rewrite)。

**如果你想改这条**(想现在做 native 英文 rewrite、雇 native copywriter):
1. **触及 `Tech-Spec.md §16.1` v6+ 推迟项 + §15.7 不能改的边界**
2. lead escalate Wenbo
3. 若仍要讨论,准备的论据:
   - 英文用户占比 + 英文用户的反馈数据
   - native copywriter 成本估算(¥/单次)
   - 这次和 v6+ 推迟决策中的什么前提变了

---

### 3.8 为什么用 Web 而不是 native iOS / Android

**Tech Spec §15.8 给的 rationale**:Native app 发版复杂、合规复杂(App Store 审核风险高,占卜类应用易被拒)、双端开发成本高。

**历史挑战(隐含)**:
- HF Space 路径只支持 Web → 这是 indie MVP 的最优起点
- App Store 监管:占卜 / 命理类应用历来高风险审核(尤其涉及"预测"的应用)。本产品虽然不预言,但塔罗元素仍会触发审核 risk
- indie 资源:一个人 + agent teams,做不动 native 双端

**锁定来源**:`PRD-4.md §10` + `Tech-Spec.md §15.8` + `Tech-Spec.md §16.1`(v6+ 才考虑 native)。

**如果你想改这条**(想做 React Native / Flutter / native Swift / Kotlin / 上 App Store):
1. **触及 `Tech-Spec.md §16.1` v6+ 推迟项 + §15.8 不能改的边界**
2. lead escalate Wenbo
3. **特别注意 App Store 审核风险**——任何含塔罗 / 命理元素的应用上 App Store 都需要审核策略,可能被拒一次以上才能通过

---

### 3.9 为什么镜子语言用方案 B(塔罗作为镜面上的具象物)

**Tech Spec §15.9 给的 rationale**:方案 A(全产品同一套视觉语汇,塔罗作为镜面内浮现的元素)消解塔罗具象触发价值;方案 B 保留塔罗作为镜面上具象物。

**历史挑战(决策过程)**:
- `PRD-4.md §11.5` 提出 A vs B 两方案 + open question
- **Wenbo 决策**:选 B —— 保留传统牌面视觉的密度(用克制的现代化重绘版本),与底色形成柔和层次
- 关键考量:开场镜子的产品价值依赖塔罗图像的具象触发力量。如果统一为镜面雾面(A),会消解这部分价值

**锁定来源**:`PRD-4.md §11.5` + `Tech-Spec.md §5.3.6 §15.9` + `CLAUDE.md §4`(镜子层不被 AI 解读塔罗、隐含方案 B 的视觉立场)。

**如果你想改这条**(想合并塔罗视觉到镜面雾面、想去掉塔罗图像、想用浓重 Rider-Waite 风格):
1. **触及 `Tech-Spec.md §14.6.2` 第 4 条(方案 B 镜子语言 + 塔罗双层视觉)+ §15.9 不能改的边界**
2. lead escalate Wenbo(这是 PRD 锁定方向、不是工程实施细节)
3. 若想换风格:克制的现代化重绘是边界——不能浓重 Rider-Waite,也不能消解为镜面元素

---

### 3.10 为什么默认按浏览器语言判定、不按 IP 判定

**Tech Spec §15.10 给的 rationale**:大陆 VPN 用户的 IP 显示为美国 / 日本等,但他们读中文。如果按 IP 判定,会把他们错判到英文版,严重错位。

**历史挑战(决策过程)**:
- `PRD-4.md §12` 提出 A / B / C 三方案
- **Wenbo 选 C 方案**:Accept-Language header + localStorage + 用户切换最高优先级
- 关键考量:大陆 VPN 用户是主要用户群之一(见 §3.5)——按 IP 判定会系统性错判这部分人

**锁定来源**:`PRD-4.md §12.1` + `Tech-Spec.md §6.1 §15.10` + `CLAUDE.md §4`(虽不直接列)。

**如果你想改这条**(想加 IP geolocation 来辅助判定语言):
1. **触及 `Tech-Spec.md §14.6.2` 第 5 条(C 方案国际化)+ §15.10 不能改的边界**
2. lead 立即拒绝
3. **特别注意**:即使是"IP geolocation 作为 fallback"也不行——任何 IP 信号引入都会污染判定逻辑

---

### 3.11 为什么错误时刻文案不能用技术语言

**Tech Spec §15.11 给的 rationale**:错误是 voice 最容易破功的地方——用户在使用产品的脆弱时刻,如果看到"500 Server Error / Network Failure / API Timeout",整个"陪你慢慢理"的氛围崩塌。

**历史挑战 / voice 命门案例**:
- **PRD-4 §13.1 错误文案表**给出每个错误场景的硬编码文案
- 经典案例:"我跟不上了——慢一点,我们一起想"(对应 AI 调用超时 / 失败)
  - 这句话不暴露技术细节、保持"陪你慢慢理"的语气、给用户明确下一步("慢一点")
  - 任何"请稍后重试""服务器繁忙""错误代码 500"都是反例

**锁定来源**:`PRD-4.md §13` + `Tech-Spec.md §7.5 §15.11` + `CLAUDE.md §5 §7 第 7 条`(不许在错误提示里暴露技术细节)。

**如果你想改这条**(想直接返回 API 错误、想自己写错误文案、想加技术信息给用户排错):
1. **触及 `Tech-Spec.md §14.6.2` 第 1 条(错误处理 voice)+ §15.11 不能改的边界**
2. **特别注意**:前端不允许自行写错误文案,**必须从 `core/error_messages.py` 取**(`Tech-Spec.md §7.5`)
3. lead 立即拒绝任何"在错误提示里加 trace ID / 错误码 / 模型名"的提议
4. 若想改文案表本身(加新的场景文案、改现有文案的措辞):需要 Wenbo 批准、走 voice review

---

## 4. lead 启动 session 的第一步指令(Wenbo 操作手册核心)

> 这一节是 Wenbo 把 agent teams 跑起来的具体步骤。3 个月后回头看也能照做。

### 4.1 启动前 checklist

- [ ] 代码仓初始化:`git init && git remote add origin ...`
- [ ] CLAUDE.md / r2-idea-v5.md / PRD-4.md / Tech-Spec.md / dev-guide.md 已经在 repo 根目录
- [ ] HF Space repo 已创建(可在 hf.co/new-space 创建,sdk: docker)
- [ ] Supabase 项目已创建(免费 tier 即可),拿到 `DATABASE_URL`
- [ ] 模型 API key 准备好:DEEPSEEK / QWEN / DOUBAO / KIMI(至少 DEEPSEEK + QWEN)
- [ ] HF Space Secrets 配置好(对应 `Tech-Spec.md §10.2.4`)
- [ ] 个人邮箱准备好(用于 M-Feedback 一键反馈接收)

### 4.2 启动 lead session

```bash
cd /path/to/weijing-mvp
claude
```

启动后给 lead 的初始 prompt(直接复制粘贴):

```
你是未镜 The Other Path 项目的 lead session。

【你的角色】
- 阅读 r2-idea-v5.md / PRD-4.md / Tech-Spec.md / CLAUDE.md / dev-guide.md
- 按 Tech Spec §14.3 task list 启动 Phase 1
- spawn 4 个 teammates 并行开发(T-Backend-Core / T-Backend-Aux / T-Frontend / T-Devops-Legal)
- 收集 teammate 产物 + 集成 + 跑 test
- 遇到 Tech Spec §14.6 不能动清单触发时,立即停手问我

【Wenbo 在哪里】
我是 lead session 的发起者 + 唯一人类决策者,不写代码。
触及 Tech Spec §14.6.4 列出的事时立即 escalate 给我。
其他时候不打扰——你应当能用 §14.6.5 范围内的自决权处理大部分日常工程。

【现在开始】
1. 先读完 5 份文档(顺序:CLAUDE.md → r2-idea-v5 → PRD-4 → Tech-Spec → dev-guide)
2. 报告你对项目的 5 分钟理解,对照 dev-guide §1 看是否一致
3. 报告你打算如何 spawn 4 个 teammates(用什么 onboarding prompt、按什么顺序)
4. 等我批准后开始 Phase 1
```

### 4.3 启动后 Wenbo 该看什么

**第一天**:
- lead 阅读完文档后报告的"项目理解"——确认它没漂移
- spawn teammates 的 onboarding prompt——确认每个 teammate 都被告知去读 CLAUDE.md + 自己模块对应的 Tech Spec 章节
- 第一批 commit——抽查接口契约、看 db migration 是否符合 §3 schema

**Phase 1 期间(~3 天)**:
- 每天扫一眼 task list 进度
- 任何 lead 主动 escalate 的事——立即响应
- 不主动催进度——agent teams 跑起来后让它们跑

**Phase 2 期间(~5 天)**:
- 关键节点:M-AI 模块的 prompt 模板第一版出来时,Wenbo 必须自己看
  - 检查 system prompt 的"主语永远是用户"
  - 跑一次 happy path,看输出是否触发 voice 红线
  - 检查双层一致性审查 4 步流程是否实现到位
- 镜子层 UI 第一版出来时,Wenbo 必须自己看
  - 检查方案 B 视觉(塔罗作为镜面上具象物)
  - 检查反思塔罗框架(AI 不解读)

**Phase 3-4 期间**:
- 端到端集成时 Wenbo 自己跑一遍 happy path
- HF Space 部署后,Wenbo 自用 1 周再放种子用户

### 4.4 何时 lead 会向 Wenbo 要 decision

直接引 `Tech-Spec.md §14.6.4`:

| 场景 | Wenbo 该做什么 |
|---|---|
| 产品方向调整 | 看是否触及锁定纪律 → 若是则拒绝 + 引用章节;若否则做产品判断 |
| Idea 锁定后的硬约束改动 | 拒绝。若 lead 仍坚持,要求它先回答"未来的 Wenbo 看到 v6 应该是诚实的还是被推动的" |
| 外部 API 选型超预算 | 看场景必要性 + 成本影响 → 多数情况下保持国产模型,特定 step 可批准换 |
| PRD-4 锁定纪律的修订 | 拒绝。若 lead 给了真实用户证据(50 用户深访数据)、可考虑走 P2 critique 流程 |
| 一键反馈集中负面信号 | 进 backlog 逐条评估,不立即改 |

### 4.5 跑起来后的日常 monitor 节奏

| 频率 | 看什么 |
|---|---|
| 每天 | 一键反馈 alert(7 天 30% 阈值,见 `Tech-Spec.md §8.4`) / lead 主动 escalate 的事 |
| 每周 | 反馈表单(自建,数据在 Supabase `feedbacks` 表) / Sentry 错误日志 / 每周成本 |
| 每月 | 决策回访数据(`decision_followups` 表)/ 100 付费用户 PMF 进度 |
| 每季 | 核心规则是否需要修订(基于积累的用户证据)/ Tech Spec 修订日志 |

### 4.6 何时 Wenbo 该介入 vs 何时该放手

**该介入**:
- AI 调用层的 prompt 模板第一版(voice 命门)
- 镜子层 UI 第一版(产品身份命门)
- 一键反馈集中负面信号(用户在喊"产品错了")
- lead escalate 的事
- 50 / 100 用户 milestone 的产品判断

**该放手**:
- 接口字段命名 / HTTP status code 选择
- 模块内实现选择(Pydantic vs dataclass / async 写法)
- 测试 edge case 补充
- 性能优化(DB 索引等)
- 不改契约的 refactor

完整边界见 `Tech-Spec.md §14.6.4 §14.6.5`。

---

## 5. HF Space 部署 walkthrough

> Tech Spec §10 给架构,本节是操作手册——Wenbo 自己跑一遍照着做。

### 5.1 一次性配置

```bash
# 1. 创建 HF Space repo
# 在 https://huggingface.co/new-space 创建,选 Docker SDK
# clone 下来:
git clone https://huggingface.co/spaces/<username>/weijing-mvp
cd weijing-mvp

# 2. 复制项目代码进来
# (假设代码在 /path/to/dev-repo)
rsync -av /path/to/dev-repo/ ./ --exclude .git

# 3. 配置 README.md(对应 Tech-Spec.md §10.2.3)
# YAML frontmatter 必须包含 sdk: docker

# 4. 配置 HF Space Secrets(在 HF web UI 的 Settings → Variables and secrets)
# 完整清单见 Tech-Spec.md §10.2.4
```

### 5.2 部署

```bash
# 5. push 到 HF Space
git push origin main

# HF Space 会自动 build Docker image 并启动
# 在 web UI 看 build logs(Logs tab)
# 第一次 build 通常 3-5 分钟

# 6. 跑 db migration(初始化 Supabase schema)
# 通过 HF Space 的 web terminal 或本地连 Supabase 跑:
psql $DATABASE_URL -f db/migrations/001_initial.sql
```

### 5.3 验证 happy path

部署成功后,在浏览器打开 HF Space URL(`https://<username>-weijing-mvp.hf.space`),按以下顺序验证:

1. **落地页**显示正常 — 浅紫雾面背景 / "未"字应用 / "陪你慢慢理一遍"主标
2. **Onboarding 三屏**可滑动 — 屏 3 期待值管理文案完整
3. **Create Yourself 问卷**第一次填(最短 4 分钟)
4. **决策输入** — 输入"要不要离职"
5. **开场镜子(可选 30 秒)** — 跳过 / 抽牌都试一次
6. **六步流水线** — 检查每一步:
   - Step 4 必须用户认领可能性档位(AI 不替写)
   - Step 5 偏差审计是假设语气(不是断言)
   - Step 6 必须用户写 Pre-mortem
7. **多路径输出** — 检查长期段没有具体事件
8. **决策回访 push** — 90 天后 push 一次(测试时调短 push 时间)
9. **反馈入口** — 表单可提交;一键 emoji 可点

### 5.4 部署后 monitoring

- HF Space Logs(实时 stdout)
- Sentry(若已接入)
- Supabase Logs(DB 慢查询、连接错误)
- 邮箱(一键反馈 alert 默认发到 Wenbo 邮箱)

---

## 6. 常见问题与排错

### 6.1 HF Space 部署失败

| 症状 | 可能原因 | 排查 |
|---|---|---|
| Build 失败:requirements 解析超时 | 网络抖动 | 重试一次;或固定版本号 |
| Docker image build 卡在 pip install | 某个包源不通 | 看具体哪个包卡住,换镜像源 |
| Build 成功但启动失败 | 环境变量缺失 | 检查 HF Space Secrets 是否完整(对照 §10.2.4) |
| 启动后 502 / 504 | uvicorn 没监听 7860 | 检查 Dockerfile CMD;或 app.py port 设置 |
| 启动后 200 但页面空白 | 静态资产路径错 | 检查 `static/` 在 Docker image 里是否被 COPY |
| 数据库连接失败 | DATABASE_URL 错 / Supabase IP allowlist | Supabase Settings → Database → Connection string |
| DB migration 失败 | schema 冲突 | 看具体哪张表/字段冲突;不要 force drop,先备份 |

### 6.2 AI 调用超时 / 失败

按 `Tech-Spec.md §4.4.2` fallback 链处理:

```
DeepSeek (主) → Qwen (备) → Doubao (再备) → Kimi (兜底) → 硬编码 fallback 文案(§4.5.3)
```

如果整条链都失败:
- 用户面**必须**显示 `core/error_messages.py` 里的硬编码文案("我跟不上了——慢一点,我们一起想"等)
- 后端记 Sentry,Wenbo 看
- 不允许把原始错误码暴露给用户

### 6.3 用户反馈数据采集到的位置 + 怎么导出

**自建反馈表单**:数据在 Supabase `feedbacks` 表。

```sql
-- 最近 7 天的反馈
SELECT created_at, user_id, score, content
FROM feedbacks
WHERE created_at > now() - interval '7 days'
ORDER BY created_at DESC;

-- 一键 emoji 反馈聚合
SELECT
  step_id,
  emoji,
  count(*) as cnt
FROM feedbacks
WHERE source = 'one_click'
  AND created_at > now() - interval '7 days'
GROUP BY step_id, emoji
ORDER BY step_id, emoji;
```

**自动 alert**:7 天窗口内某 step 的 ☹️ 占比 > 30% 时,自动发邮件到 Wenbo(`Tech-Spec.md §8.4`)。

**导出给 Wenbo 看**:
- 每周用 `pg_dump` 导一份 `feedbacks` + `decision_followups` 表
- 或用 Supabase web UI 的 export 功能

### 6.4 用户问"我之前的推演不见了"

**v1 阶段**:推演中间态存在 localStorage(`Tech-Spec.md §7.1`),用户清浏览器 / 换设备会丢。

排查步骤:
1. 用户是否清过浏览器数据 / 用了无痕模式
2. 用户是否换过设备(没登录的话不跨设备同步)
3. 用户是否登录过 — 登录用户的**完成态**推演存 Supabase `inference_runs` 表
4. 若是登录用户、完成态丢失:Supabase 查表确认数据真在不在;若数据在但用户看不到,查前端的状态加载逻辑

**回应 voice**(给用户的话):
- ✅ "之前的草稿存在你的浏览器里、换设备 / 清数据会丢——你愿意从头再想一遍吗?我陪你"
- ❌ "数据保存在 localStorage,清除浏览器缓存会导致丢失"

---

## 7. 当 agent teams 卡住时怎么办

### 7.1 何时需要 Wenbo 介入终止 / 重新规划

| 信号 | 行动 |
|---|---|
| lead 报告"无法在 §14.6.5 范围内自决"3 次以上 | Wenbo 看 lead 卡的是哪类问题、是否需要修订 task list |
| 某个 teammate 报告同一个 bug 3 轮还没解决 | Wenbo 介入看 bug;考虑 spawn 替代 teammate |
| Phase 1-2 进度严重落后(>2 天) | Wenbo 看 task list 是否高估、需要砍范围 |
| lead 与 teammate 接口冲突无法收敛 | Wenbo 决定接口契约最终形态、广播给所有 teammate |
| 测试覆盖率 < 50% | Wenbo 要求 spawn T-Test 临时 teammate |
| 输出过滤回归测试失败 | **立即停手**——这是 voice 命门;Wenbo 必须自己看 prompt 改了什么 |

### 7.2 如何让 lead 重新 spawn 替代卡住的 teammate

给 lead 的指令:

```
T-[Teammate name] 在 [具体 task] 上卡住了 [具体表现]。

请:
1. 总结卡点(是哪个模块 / 哪段代码 / 哪个接口契约?)
2. 把当前 teammate 的产物归档(branch 留着、不删)
3. spawn 一个新 teammate(命名 T-[name]-v2),用 §14.4 onboarding prompt
4. 给新 teammate 多加一段 context:"前一版 teammate 卡在 X,已尝试 Y / Z 都没解决。请从 W 角度重新思考"
5. 报告给我新 teammate 的初步 plan
```

### 7.3 如何让 lead clean up team

参考 Claude Code agent teams 官方文档:

```
请按以下顺序清理 team:
1. 收集所有 teammate 的最终产物(代码 + 测试 + 文档)
2. merge 各 teammate 的 branch 到 main(需要解冲突的告诉我)
3. 总结每个 teammate 的交付情况、未完成项
4. 关闭所有 teammate session
5. 清理 task list 中已完成项,保留未完成项
```

### 7.4 跨 session 中断后如何恢复 task list 状态

**最佳实践**:每次 lead session 结束前让它写一份 `session-handoff.md` 到 repo:

```markdown
# Session Handoff [日期]

## 已完成
- [task] - 在 commit <sha>
- ...

## 进行中
- [task] - teammate T-X 正在做、目前进度 Y / 卡点 Z(如有)

## 待启动
- [task]

## 下次启动 lead 时
- 读 dev-guide §4.2 + 这份 handoff
- 从"进行中"任务开始接手
```

下一次启动 lead 时,把 `session-handoff.md` 加到初始 prompt:

```
[原 §4.2 启动 prompt]
+
另外:上次 session 的状态在 session-handoff.md,先读这份再继续。
```

### 7.5 极端情况:整个 team 全部失控

(预计 v1 阶段不会发生,但写出来以防万一)

- 所有 teammate session close
- lead 也 close
- 把 main 分支 reset 到最后一个稳定 commit(**先备份 branch 再 reset**)
- 重新启动一份 lead session,从 §4.2 重新开始
- 在新 lead 的初始 prompt 里加:"上次 team 全部失控、根因是 X,请避免 Y"

---

## 8. 文档维护纪律

- 本文档随 Wenbo / lead 实操踩坑随时更新——是**活的**
- §3 关键决策的"踩坑视角"——每次有新挑战 / 新决策时追加,不删旧的
- §6 常见问题——遇到新 bug / 新解决方案时追加
- §4-§7 操作手册——每次 Wenbo 跑 / lead 实操中发现描述偏差时修正
- §1-§2 项目理解 / 文档关系——只在 milestone 节点(MVP 上线 / 50 用户 / 100 用户)更新

**与真源(idea / PRD / Tech-Spec)的关系**:本文不能与真源冲突。冲突时:
- 真源是产品宣言、本文是注释
- 修正本文,不修正真源
- 若发现真源真的有问题(如 Tech Spec 的某个 §15 决策被实操推翻),走 Wenbo 批准 + P2 critique 流程

---

## 9. 末尾灵魂提醒(与 Tech Spec / CLAUDE.md 共用一句)

> **如果某个技术决策让你觉得"产品好像没那么贴心了 / 没那么允许了 / 没那么诚实了"——那个决策大概率错了。**
>
> 未镜服务真正纠结的少数人,让他们在做决定前能听清自己一次。
>
> 我们靠诚实活,不靠钩子活。每一次工程取舍 / 每一次 bug 修复 / 每一次 feature 增删,问一遍:"这是让用户更清醒,还是更被命中?" 选前者。

---

*本指南随 Wenbo / lead 实操踩坑随时更新。最后更新日期:2026-04-27 · 初版(P3.3)。*
