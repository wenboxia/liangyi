# Agent 评测平台(v5)

## 0. v5 相对 v4 的调整:加五层结构性守护栏

本轮是第二次 P2D 拆台。按终止条件规则,不回 P1,全部论据作为**框架内修改**消化。

P2D 的五条反驳——草案态=噪声、可选升级=永不升级、judge 协作者=reward hacking、PM 不具测量学元能力、配置坟场——虽然语气强烈,但都指向同一件事:v4 的"轻量起步 + 自愿升级 + judge 协作者"在组织行为学和测量学上都过于乐观,需要结构性护栏,不能靠用户自驱。

v5 保留 v4 的核心立场(默认轻量、judge 协作、业务方参与定义),**但为每一个 P2D 反驳加一层结构性守护**:

| P2D 论据 | v5 守护栏 |
|---|---|
| 草案态是噪声生成器 | **最低 Sanity Floor**:即使草案态也要过 50 条明暗样本的判别性测试 + UI 三明治警告 + 90 天强制决策 |
| 可选升级 = 永不升级 | **自动升级触发器**:使用强度超阈值自动入升级队列,不升级就降级为只读,不是"自愿" |
| judge 协作者 = reward hacking | **Held-out 独立评估集**:suggested_fix 绝不触达 Profile 评估集;采纳后在独立集上验证,divergence 高自动 flag |
| PM 无测量学元能力 | **Measurement Reviewer(兼任)强制共审**:维度/判据/红线入库需 MR 过目,不是"PM 单方面拍板" |
| 配置坟场 | **TTL + 使用信号治理**:60 天无更新冻结、两周无人看 CI 结果降权、季度清理例行化 |

**核心立场不变**:轻量起步 + judge 协作,但 v5 承认"轻量"不等于"无底线",护栏是结构性的,不依赖用户自驱。

---

## 一、产品定位与目标用户

### 1.1 定位

**服务产品/政策团队快速定义、试跑、迭代评测标准的协作平台,工程形态是 Langfuse 之上的扩展层;默认配备结构性守护栏防止退化为噪声或坟场**。

### 1.2 用户与角色

| 优先级 | 角色 | 参与方式 |
|---|---|---|
| P0 | PM / 政策负责人 | 定义维度、判据、红线,看扣分报告 |
| P0 | Agent / Prompt 工程师 | 看扣分 + 启发建议,跑 CI 回归 |
| P0 | **Measurement Reviewer**(兼任,v5 提升为 P0) | 维度/判据/红线入库前共审;Profile 升级审阅 |
| P1 | 领域专家 | 按需参与校准集标注 |
| P2 | QA / 业务负责人 | 看趋势、回归报告 |

**关键变化**:v4 的"方法论审阅人(P2 兼任)"在 v5 升为 **P0 Measurement Reviewer**——不是专职 FTE,但是**任何 Profile 的任何入库维度/判据必须经过 MR 过目,不能 PM 单方面落库**。组织已有的资深 PM、数据科学家、QA Lead、风控专家任一胜任。这是对 P2D 论据 4(PM 无测量学元能力)的守护。

---

## 二、核心评分机制

### 2.1 两层维度体系 + 共审门槛

**第一层 · 通用基座**:Correctness / Instruction Following / Relevance / Completeness / Presentation。

**第二层 · 场景维度**:按任务画像推荐。新增场景维度入场景包门槛:10 条判据样例 + 反例 + **MR 过目签字**。

**MR 共审的最小动作**(不是重型审查):
- 检查判据是否可操作(能不能转成判定题)
- 检查是否有明显的"测量 PM 直觉"而非"测量 Agent 行为"的风险
- 检查误杀风险(反例是否覆盖"合理拒绝"、"合规拒答"等容易被误判的 case)
- 15-30 分钟/维度,批次处理

### 2.2 分层打分器

保留 v4 的四层架构与 Scorer Protocol。细节不变:
- Layer 1 Rule · YAML-driven validator
- Layer 2 Assertion · 业务规则断言 + API 钩子 + 三问法转换
- Layer 3 Evidence LLM · 只抽证据不打分 + `confidence < 0.7` 进争议池
- Layer 4 Reference · 可选,黄金输出比对

聚合规则保留 v4:硬红线 → 不可上线;软红线未二审 → 需人工复核;major 数量触发 red/yellow。

### 2.3 红线:硬/软分层(保留 v4)

硬红线走 Layer 1+2,触发即不可上线。软红线走 Layer 3 + 人审。硬红线覆盖率 ≥ 60% 作为 Profile 健康提示。

### 2.4 EvidenceLocator(保留 v4)

JSONPath 指向 Langfuse observation + text_span + node_kind 枚举。封装在 EvidenceResolver 屏蔽 trace schema 演进。

### 2.5 修复建议 + Reward-Hacking 防护(v5 重要加固)

P2D 论据 3 的核心是:judge 作为协作者 + 工程师采纳建议消扣分 = reward hacking 合谋游戏。v5 保留协作者立场,但加**独立评估集机制**防合谋。

**双输出保留不变**:

```json
{
  "deduction": { ... },
  "root_cause_hints": ["retrieval_miss", "prompt_constraint_missing"],
  "suggested_fix": {
    "text": "建议在 system prompt 中增加'退款承诺前必须调用 verify_order 工具'的约束",
    "confidence": 0.7,
    "kind": "heuristic",
    "disclaimer": "启发式建议,不承诺对"
  }
}
```

**v5 新增 · Held-out 独立评估集机制**

每个 Profile 的样本集强制拆成两份:

- **iteration_set**(可见):PM/工程师开发时使用的样本,可反复看扣分、调 prompt
- **holdout_set**(不可见):PM/工程师在平台 UI 上看不到具体 case 内容,只能看聚合分数;每月自动轮换 30% 样本防止被间接学习

**Reward-Hacking Detector**(自动,无需人工):

- 记录每次 prompt/工具变更前后,iteration_set 和 holdout_set 上的分数变化
- 如果 iteration_set 改善 Δ > 0.3 但 holdout_set 改善 Δ < 0.1(即"只在可见集上变好"),自动 flag 为 `suspected_overfitting`
- Flag 触发后:该 Profile 的本次迭代不计入 CI 通过、通知 PM + MR、在升级审阅时作为风险点

**suggested_fix 的隔离约束**:
- suggested_fix 的生成数据**只用 iteration_set**,holdout_set 的样本绝不进入 suggested_fix 的 few-shot 或 RAG
- Profile 升级到 verified 时的效度/专家共识验证**只在 holdout_set 上做**
- 工程师采纳 suggested_fix 后,改善评估必须看 holdout_set 上的 Δ,不是 iteration_set

这套机制把 P2D 的"合谋游戏"担忧工程化了——judge 仍是协作者,但**协作只发生在 iteration_set 上,holdout_set 作为独立法官**。

`root_cause_hints` 继续作为固定枚举的结构化补充(retrieval_miss / prompt_constraint_missing 等 9 类)。

### 2.6 草案态最低 Sanity Floor(v5 对 P2D 论据 1 的守护)

P2D 反例真实:PM 在 ρ = -0.18 的噪声信号上优化三个月,硬加结尾祝福导致 CSAT 下降。v5 承认**纯无约束的草案态确实有害**,加一道入门级 sanity check。

**Draft Profile 创建时强制通过的最低 Sanity Floor**:

| 动作 | 要求 | 人时 |
|---|---|---|
| Profile 作者(或 MR)准备 50 条样本:25 条"明确好"+ 25 条"明确坏" | 两类样本必须业务上无争议,由 MR 过目确认 | 2 人时 |
| Profile 在这 50 条上跑一次,计算区分度 AUC | AUC ≥ 0.65 才允许发布为草案态 | 10 分钟 |
| 未达 AUC 的 Profile 回到判据调整,不能发布 | | — |

**这是比 v4 高但比 v3 低的门槛**:不要求 300 条、不要求算 Spearman ρ,但要求证明 Profile 起码能把"明显好"和"明显坏"分开。分不开的 Profile 就是噪声,不放出去。

**草案态的 UI 三明治警告**(不是弱水印):
- Profile 顶部红色 banner:`草案态 · 信号可靠性未经线上验证 · AUC=0.71 基于 50 条明暗样本 · 不可用于 go/no-go`
- 扣分报告底部警告:`这份报告的相对误差未经线上指标验证,建议关注分数变化趋势而非绝对值;切勿基于单次报告做单点优化`
- 当草案态 Profile 被关联到 CI 时,CI 页面顶部重复这个警告

**草案态 90 天强制决策**(对 P2D 论据 5 配置坟场的部分响应):
- 90 天内必须做出决策:升级到 verified / 转为 archived / 显式展期(需 MR 签字,每次展期 30 天,最多 3 次)
- 90 天到期无决策 → Profile 自动 freeze,CI 不再阻断,UI 标为 `expired_draft`

### 2.7 效度验证 + 自动升级触发器(v5 对 P2D 论据 2 的守护)

P2D 论据 2 的核心:一旦有"看起来工作的数字",没人自愿升级。v5 保留"默认草案态"立场,但把升级从"自愿"改为"**使用强度驱动的结构性强制**"。

**Profile 状态双态仍保留**:`draft` / `verified`。

**Verified 升级条件**(保留 v4 双通路):

| 通路 | 条件 |
|---|---|
| 线上指标通路 | ≥ 300 条线上样本 + 至少 1 个维度×指标 Spearman ρ ≥ 0.4,holdout_set 上计算 |
| 专家共识通路 | 3 位领域专家对 100 条 holdout_set 样本独立标"应通过/不应通过",Profile verdict 一致率 ≥ 75% |

升级审阅由 MR 按 SOP 做,约 2 小时。

**v5 新增 · 自动升级触发器**(结构性,不自愿):

| 触发信号 | 动作 |
|---|---|
| Profile 近 14 天 run 次数 ≥ 100 | 自动进升级队列,通知 Owner + MR;30 天内未升级 → Profile 降级为 `heavy_use_unverified` |
| Profile 挂在 ≥ 1 个 CI pipeline 并产生 blocking 决策 | 入库即标 `mandatory_upgrade`,45 天内必须升级,否则 CI 降级为 warning-only |
| Profile 出现在任意管理层仪表盘 | 自动标 `mandatory_upgrade`,同上 |
| Profile 关联到 go/no-go 评审 ≥ 1 次 | 立即升级或停止使用,不允许草案态承担决策 |

**降级机制**(结构性,硬编码):
- `heavy_use_unverified` Profile:UI 警告升级、CI 阻断失效(只产生 warning)、不进管理层仪表盘
- `mandatory_upgrade` 超期:平台自动把 CI 从 blocking 降为 warning,并通知团队 lead

这是对 P2D 论据 2(严谨性不结构性强制就会被跳过)的工程化回应。代码审查 gate 的行业路径已经证明:**严谨性必须被结构化地绑定到使用强度上,不能只靠用户自驱**。

### 2.8 双轨评测(保留 v4)

- **B 轨 日常回归**(主力) · regression set ≥ 30 条,CI 5 分钟出 diff。草案和 verified 都可用
- **A 轨 深度验证**(仪式) · 仅在升级 / 月度回算时跑,仅 verified Profile

### 2.9 标准化评分输出(v5 补 maturity 细化)

```json
{
  "verdict": "需修复",
  "verdict_reason": "2 项严重扣分",
  "profile_maturity": "draft",
  "profile_flags": ["overfitting_suspected"],
  "holdout_delta_note": "iteration_set +0.34, holdout_set +0.08 — possible overfitting",
  "dimensions": [...],
  "redlines_triggered": {"hard": ["R-07"], "soft_pending_review": []},
  "meta": {"profile_id": "...", "profile_version": "...", "run_id": "...", "cost_usd": 0.042}
}
```

`profile_flags` 新增枚举:`overfitting_suspected` / `heavy_use_unverified` / `mandatory_upgrade` / `expired_draft` / `sanity_floor_failed`。

---

## 三、系统架构

### 3.1 Build-vs-Buy 差分表(保留 v4)

Langfuse 基座 + 4 块胶水(业务断言、场景包、升级通路、硬/软红线路由)+ 2 块补齐(规则层、争议池)+ **v5 新增 3 块治理模块**(SanityFloorGate、RewardHackingDetector、LifecycleGovernor)。

### 3.2 架构图

```
                   ┌─────────────────────────────────────────┐
                   │   Langfuse (self-host)                  │
                   │   Trace / Dataset / Judge / Feedback    │
                   └────────┬────────────────────────▲───────┘
                            │ webhook/API            │ feedback 写回
                            ▼                        │
          ┌───────────────────────────────────────────────────┐
          │   v5 Extension Layer                              │
          ├───────────────────────────────────────────────────┤
          │  Orchestrator                                     │
          │  Scorer Plugins (Rule / Assertion / Ev-LLM / Ref) │
          │  EvidenceResolver                                 │
          │  RedlineRouter                                    │
          │  RegressionRunner (B 轨)                          │
          │  ValidityPipeline (A 轨,仅 verified)             │
          │  ┌─ v5 新增治理模块 ──────────────────────────┐  │
          │  │ SanityFloorGate (发布前明暗样本 AUC)      │  │
          │  │ RewardHackingDetector (iter vs holdout)   │  │
          │  │ UpgradeTriggerEngine (使用强度→升级)      │  │
          │  │ LifecycleGovernor (TTL / 冷置 / 降权)     │  │
          │  │ MeasurementReviewerQueue (MR 签字流)      │  │
          │  └───────────────────────────────────────────┘  │
          └──────┬──────────────────┬──────────────────────┘
                 │                  │
                 ▼                  ▼
          ┌──────────────┐   ┌───────────────────┐
          │ Knowledge    │   │ Ticketing (Jira)   │
          │ Adapters     │   │                   │
          └──────────────┘   └─────────┬─────────┘
                                       ▼
                               ┌───────────────┐
                               │ Review Queue  │
                               └───────────────┘
```

### 3.3 工单对接(保留 v4 + v5 新增工单类型)

Jira 为主,适配器模式。v5 新增工单类型:
- `sanity_floor_failed` · 发布前阻断,派给 Profile Owner + MR
- `upgrade_mandatory_overdue` · 超期未升级,派给 Owner + Team Lead
- `overfitting_flag` · reward-hacking detector 触发,派给 Owner + MR
- `lifecycle_expiring` · 草案 75 天提醒,90 天强制决策

Owner 连续性:Backup + HR webhook 自动转派(v4 保留)。

### 3.4 Scorer 骨架接口契约(保留 v4 + v5 新增)

```
eval_ext/
  scorers/ ...            # 保留 v4
  resolver.py             # 保留 v4
  profile.py              # Profile schema + maturity + flags
  orchestrator.py
  upgrade/
    workflow.py
    sop_checklist.py
    trigger_engine.py     # v5 新增:使用强度自动升级触发
  validity/
    full.py
    regression.py
  calibration/ ...
  governance/             # v5 新增整模块
    sanity_floor.py
    reward_hacking.py
    lifecycle.py
    mr_queue.py
  adapters/ ...
```

错误码、日志格式、健康检查 endpoint 保留 v4。

### 3.5 成本与存储(保留 v4)

retention 分层、双尺度预算($20/月默认 + 单 run $0.20 默认)、级联定义、单 run 成本透传——全部保留。

Holdout_set 存储:每 Profile 独立存,UI 层屏蔽访问,仅 scoring 后台可读。

---

## 四、冷启动与采纳路径

### 4.1 角色(v5 调整:MR 升为 P0)

| 角色 | FTE | 职责 |
|---|---|---|
| PM / 政策负责人 | 兼任 | 定义维度(需 MR 共审)、跑 Profile、看报告 |
| Agent 工程师 | 兼任 | CI 集成、处理启发式建议 |
| **Measurement Reviewer** | **兼任,P0** | 维度/判据入库共审、Sanity Floor 签字、Profile 升级审阅、reward-hacking flag 处理 |
| Calibration 负责人 | 仅 verified Profile 要求 | 校准集维护、漂移响应 |
| 平台研发 | 1.0-2.0 FTE | 扩展层开发维护 |

**v5 关键变化**:MR 从 v4 的 P2 升为 P0。任何 Profile 的第一版入库、任何新维度入场景包、任何升级到 verified,都必须有 MR 签字。没有 MR 的组织不是"用不了"——可以由资深 PM / DS / QA Lead / 风控专家中任一人兼任。但**没有这个角色,Profile 不能入库**。

### 4.2 单 Profile 冷启动人时

**草案态(含 Sanity Floor)**:
- 场景包 fork + 调参:2-4 人时
- 准备 50 条明暗样本 + MR 签字:2 人时
- AUC ≥ 0.65 通过 + 首次报告:30 分钟
- **草案态入门总成本:~5 人时**(v4 是 2-4 人时)

**升级到 verified**:
- 校准集(100 条 × 语义维度):~12 人时
- 效度/专家共识验证(在 holdout_set 上):~8 人时
- MR 升级审阅:~2 人时
- **升级总成本:~22 人时**(v4 保留)

v5 相对 v4 的增量:草案态多 1-2 人时的 Sanity Floor 成本,但降低了噪声 Profile 四处漂浮的风险。

### 4.3 6 个月北极星指标

| 指标 | 目标 |
|---|---|
| 草案态 Profile 数(通过 Sanity Floor) | ≥ 20 |
| Verified Profile 数 | ≥ 4 |
| WAU | ≥ 20 |
| 团队渗透 | ≥ 5 个业务团队 |
| B 轨日常回归次数 | ≥ 100/周 |
| 升级审阅通过率 | ≥ 70% |
| **自动升级触发命中的 Profile 升级达成率** | **≥ 60%**(v5 新增) |
| **reward-hacking flag 触发率** | **≤ 10%**(v5 新增,过高说明判据有问题) |
| **过期 draft 清理后"僵尸 Profile"残留数** | **≤ 2**(v5 新增) |

### 4.4 三阶段

**Phase 1 · Langfuse + 轻量 MVP + 治理骨架(0-6 周)**
- 部署 Langfuse
- 交付 eval_ext 骨架 + SanityFloorGate + LifecycleGovernor + MR 签字流
- 1 个场景包 + 2-3 个 PM 起草案态 Profile(每个都过 Sanity Floor)
- 交付物:能用的工具 + 防噪音地板

**Phase 2 · 场景包扩展 + 首个升级 + Reward-Hacking Detector(6-14 周)**
- 3 个场景包(客服、知识库问答、结构化抽取)
- holdout_set 机制上线,RewardHackingDetector 开始监控
- 首个 Profile 走完升级到 verified
- 更多团队起草案态

**Phase 3 · CI 集成 + 自动升级触发器 + 治理常态化(14 周+)**
- CI 集成 B 轨,自动升级触发器上线
- 月度 MR office hour 处理升级审阅
- 季度 LifecycleGovernor 清理 expired draft / 僵尸 Profile

### 4.5 采纳铁律

先给结论再给配置 / 对比优先于绝对分 / 扣分可反驳 / 工具非监督 / **护栏不可绕过**(v5 新增)。

---

## 五、风险与对策

| 风险 | 对策 |
|---|---|
| 草案态产生噪声误导 PM(P2D 论据 1) | SanityFloorGate:50 条明暗样本 AUC ≥ 0.65 才允许发布 + UI 三明治警告 + 90 天强制决策 |
| 没人自愿升级(P2D 论据 2) | UpgradeTriggerEngine:使用强度触发自动升级,超期降级为 warning-only |
| Judge 协作者 → reward hacking(P2D 论据 3) | Held-out set 机制 + RewardHackingDetector + suggested_fix 数据隔离 |
| PM 无测量学元能力(P2D 论据 4) | MR 升为 P0 共审角色,维度/判据入库必经 MR 签字 |
| 配置腐烂成坟场(P2D 论据 5) | LifecycleGovernor:60 天无更新冻结、两周无人看 CI 降权、季度清理、Profile 强制 owner 绑定 |
| Langfuse 升级不兼容 | EvidenceResolver 适配层隔离 |
| 硬红线覆盖不足 | ≥ 60% 健康提示 |
| Owner 不可用 | Backup + HR webhook(仅 verified 要求) |
| 存储成本失控 | retention 分层 |
| 单 run 成本黑箱 | RunRecord.cost_usd 透传 |
| 扩展层干扰 Langfuse trace | 只读消费 + 写回 feedback |
| MR 共审成为瓶颈 | 批次处理 + 15-30 分钟/维度的最小动作;MR 兼任可多人轮值 |
| 自动升级触发器过于激进 | 阈值可按团队调;升级失败不立即停用,而是降级 CI 为 warning |

---

## 六、开发者工效学(保留 v4 §6)

CLI / offline replay / hook mock / LLM mock / fixture 库 / 单测 / 单 run 成本透传 / 快速迭代 / onboarding——全部保留。

**v5 新增**:`eval sanity --profile foo` 命令本地跑 Sanity Floor 自测;`eval holdout-status --profile foo` 显示 holdout_set 上的 Δ 分布和 overfitting 风险。

---

## 七、一句话主张

Agent 评测平台是**让 PM 当周起 Profile + judge 协作式给建议,但被五层结构性守护栏约束**的协作工具:入门要过 Sanity Floor,使用强度超阈值自动升级,judge 建议只在 iteration_set 上协作而 holdout_set 独立评判,维度入库必经 Measurement Reviewer 共审,Profile 不更新会被 Lifecycle 回收。**轻量不等于无底线,协作者不等于合谋,业务方定义不等于单方面拍板,自愿升级不等于永不升级,默认可用不等于默认有用**。

---

## 拆台响应日志

**本次是第 2 次 P2D-fix**。按终止条件规则,**不回 P1**,P2D 的五条论据无论强弱,全部作为**框架内修改**消化为 v5 的结构性守护栏。

### 原 P2D 强否定论据如何被框架内消化

**论据 1 · 草案态是噪声生成器 → SanityFloorGate**
- 否定措辞"假设不成立"接受其事实性(无约束草案确实可能是噪声),但不推翻"默认轻量"方向
- 框架内消化:§2.6 强制草案态通过 50 条明暗样本 AUC ≥ 0.65 的最低判别性测试;UI 三明治警告(banner+底部+CI);90 天强制决策机制
- v1 的快速迭代被保留,但对"纯无约束"这种退化形态加了地板

**论据 2 · 可选升级 = 永不升级 → UpgradeTriggerEngine**
- 否定措辞"违背组织行为学常识"有实质支撑(代码审查 gate 行业路径为证)
- 框架内消化:§2.7 保留 draft/verified 双态但升级从"自愿"改为"使用强度驱动"——14 天 ≥ 100 runs、挂 CI blocking、进管理层仪表盘、用于 go/no-go 任一触发即强制入升级队列;超期降级为 warning-only
- v4 的"默认轻量"保留,但"轻量 + 使用强度低"才轻,"轻量 + 使用强度高"自动转重

**论据 3 · judge 协作者 = reward hacking → Held-out 独立集 + Detector**
- 否定措辞"从根本上误解了评测工具的立身之本",有 Google Auto-Eval 实证
- 框架内消化:§2.5 保留 suggested_fix 协作者定位,但引入 iteration_set / holdout_set 强制拆分——suggested_fix 只用 iteration 生成、升级验证只在 holdout 做、RewardHackingDetector 自动检测"只在可见集变好"的合谋模式并 flag
- Judge 仍是协作者,但协作被限制在 iteration_set 内;holdout_set 扮演 P2D 所说的"独立第二声音"角色——既保留 v4 的协作立场又堵住合谋漏洞

**论据 4 · PM 无测量学元能力 → MR 升为 P0 强制共审**
- 否定措辞"搞混了两种能力",有字节内容审核 40% 误杀的实证
- 框架内消化:§1.2 把 Measurement Reviewer 从 v4 的 P2 兼任审阅人提升为 **P0 强制共审角色**;§2.1 任何维度/判据/红线入库必须经 MR 签字;MR 检查清单显式包含"是否测量 PM 直觉而非 Agent 行为"、"误杀风险"
- "业务方话语权"被保留,但 PM 和 MR 是双签关系,不是 PM 单方面拍板

**论据 5 · 配置坟场 → LifecycleGovernor**
- 否定措辞"主动选择废墟",有所有内部度量平台的行业经验为证
- 框架内消化:§2.6 草案 90 天强制决策(升级/归档/展期);§2.7 使用强度低且 14 天无更新自动冻结;CI 结果两周无人看降权、四周无人看 read-only;季度 LifecycleGovernor 清理例行化
- v4 的"不强制升级"保留,但"不强制升级 ≠ 不清理僵尸"——Profile 生命周期被结构化管理

### 总立场

v5 承认 v4 的"轻量 + 自愿 + 协作者"在组织行为学上过于乐观,但不推翻其方向。护栏是**结构性**的(硬编码在 platform 里,不依赖用户自驱),但数量是**五层最小必要集**(不是 v3 那种全面仪式化)。

一个 PM 仍然可以在当周起一个 Profile——只是这个 Profile 必须通过 50 条明暗样本测试才能发布,超过使用强度必须升级,maintained 状态必须维持,不能永远草案。这是对 P2D 五条反驳的工程化和解,不是对 v4 方向的推翻。
