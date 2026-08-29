# Agent 评测平台(v4)

## 0. v4 相对 v3 的立场回拉

P2C 诊断指出:v3 把"统计可辩护"推到了入场门槛的位置——Spearman ρ ≥ 0.5 作为 Profile 准入硬门槛、300 条校准集、1.0 FTE Methodology Lead、5 工作日 SLA、provisional_validity 过渡态。这些修改**单看都合理**,但累积起来把产品从 v1 想服务的"PM 当周就能起一个 Profile 试"推到了"专业化小团队才能用"的测量学基础设施。v1 想服务的轻量迭代场景在 v3 里跑不起来。

v4 按 P2C 的默认处置规则做一次**重心回拉**,但不是全盘推翻:

1. **验证从门槛降为升级通路**:Profile 默认"草案态(draft)",立即可用,不要求效度验证、不要求大校准集、不要求方法论审阅。想让 Profile 承担 go/no-go 决策责任时,自愿走升级到"已验证态(verified)"的通路。
2. **judge 明确为协作者,不是测量仪**:P2C 指出 v1 是协作者、v2 是测量仪、v3 半只脚踩回来——没想清楚。v4 明确选协作者。恢复 `suggested_fix` 字段,但标明"启发式建议,不承诺对"。PM 定义"好"的话语权还给业务方。
3. **保留 v3 的工程硬底**:Langfuse 基座、EvidenceLocator schema、Scorer 接口契约、开发者工效学(CLI、mock、单测)、硬/软红线分流、Jira 字段映射、retention 分层——这些是 build-vs-buy 和文档自包含度的客观结论,**和漂移无关**,全部保留。

**一句话**:轻量起步 + 可选升级。让 PM 当周就能试,让做重决策的人在需要时走严格通路。

---

## 一、产品定位与目标用户

### 1.1 定位

**一个服务产品/政策团队快速定义、试跑、迭代评测标准的协作平台,工程形态是 Langfuse 之上的扩展层**。

- 对 **PM / 政策 / 内容负责人**:定义"好输出"的工作台,5 分钟内能跑起一个 Profile
- 对 **工程师**:Agent 调试器,给启发式线索 + 可操作证据,不是判决者
- 对 **做重决策的人**(上线评审、合规审批):可以把选定 Profile 升级到"已验证态",走更严格的准入流程

### 1.2 用户与角色

| 优先级 | 角色 | 参与方式 |
|---|---|---|
| P0 | PM / 政策负责人 | 定义维度、判据、红线,看扣分报告 |
| P0 | Agent / Prompt 工程师 | 看扣分 + 启发建议,跑 CI 回归 |
| P1 | 领域专家 | 按需参与校准集标注 |
| P2 | 方法论审阅人 | **兼任**,Profile 升级到已验证态时审阅(约 2 小时/次) |
| P2 | QA / 业务负责人 | 看趋势、回归报告 |

**关键变化**:v3 的 Methodology Lead 1.0 FTE 专职改为**兼任审阅人**。组织已有的资深 PM、数据科学家或 QA Lead 任一胜任。没有这个角色的团队,仍可用平台的草案态。

---

## 二、核心评分机制

### 2.1 两层维度体系

**第一层 · 通用基座(不可删不可改名)**

| 维度 | 含义 |
|---|---|
| Correctness | 事实、逻辑、计算是否正确 |
| Instruction Following | 完成指令 + 遵守约束 |
| Relevance | 聚焦输入诉求 |
| Completeness | 覆盖所有要点 |
| Presentation | 结构、语言、格式、可读性 |

**第二层 · 场景维度**:按任务画像(任务类型 + 业务场景 + 交付规范)推荐,可增删改权重。

新增场景维度入场景包的门槛从 v3 的 20 条判据样例降为 **10 条**——鼓励试,不鼓励慎。

### 2.2 分层打分器

**统一 Scorer 接口**

```python
class Scorer(Protocol):
    name: str
    layer: Literal["rule", "assertion", "evidence_llm", "reference"]
    def score(
        self, trace: LangfuseTrace, dimension: DimensionSpec, context: ProfileContext,
    ) -> DimensionResult: ...
```

`DimensionResult` 字段:`health`(green/yellow/red)、`deductions: list[Deduction]`、`scorer_meta`(版本、耗时、token 成本)。

**Layer 1 · 规则层(Rule)** · 正则 / JSON Schema / 长度 / 关键词 / 模板结构 / 必调用工具存在性。失败即硬扣分,不进下一层。规则为 YAML + validator 函数,YAML 在 Profile 下。

**Layer 2 · 业务断言层(Assertion)** · 业务规则结构化为断言集:

```yaml
id: R-07
name: 退款承诺必须在订单号验证后
severity: redline_hard
expr:
  when: output.contains_claim("refund_approved")
  require: trace.has_tool_call("verify_order", before=matching_message)
on_fail:
  message: "未验证订单号即承诺退款"
  evidence_node_path: "$.messages[?(@.role=='assistant')].content"
```

支持自定义函数钩子调外部 API(订单、CRM、工单)。钩子默认 timeout=3s,retry=2,超时降级为 `inconclusive`。

**政策文本 → 断言的三问法**(由 Profile 作者或审阅人在升级审阅时完成):
- 触发条件能否列出关键词/结构特征
- 违反动作能否查 trace 某节点
- 参数(天数、金额)是否显式

三问都过 → 硬断言;否则 → 软红线走 Layer 3。场景包附 30+ 已转换案例作为模板。

**Layer 3 · LLM 证据抽取层(Evidence LLM)** · 用于语气、逻辑冲突、完整性等语义维度。LLM **只抽证据不打分**,固定输出 JSON:

```json
{
  "dimension": "tone_compliance",
  "findings": [
    {
      "criterion_id": "T-03",
      "polarity": "violation",
      "evidence": { /* EvidenceLocator */ },
      "confidence": 0.82,
      "rationale": "用户表达不满,回复使用'这不是我们的问题'属于情绪对抗"
    }
  ]
}
```

`confidence < 0.7` 的 finding 标"需人工复核",进争议池候选。

**Layer 4 · 参考层(Reference,可选)** · 黄金输出存在时叠加 embedding 相似度 / 精确匹配 / ROUGE。

**聚合规则**(确定性逻辑,不走 LLM 加权):

```
if any(d.severity == "redline_hard"): health = red; verdict = 不可上线
elif any(d.severity == "redline_soft_pending"): health = red; verdict = 需人工复核
elif count(severity=="major") >= 2: health = red
elif count(severity=="major") == 1 or count(severity=="minor") >= 3: health = yellow
else: health = green
```

### 2.3 红线:硬/软分层

| 类型 | 定义 | 路径 | verdict 行为 |
|---|---|---|---|
| 硬红线 | 可 100% 断言化(Schema、禁用词、必调工具缺失、数值条款、PII) | Layer 1+2 | 触发即 `不可上线` |
| 软红线 | 语义模糊(品牌调性、情绪对抗、隐性承诺、越界建议、歧视表述) | Layer 3 抽证据 + 人审 | 未二审 → `需人工复核`;二审确认 → `不可上线` |

硬红线覆盖率从 v3 的"≥ 60% 硬要求"改为"**建议 ≥ 60%,作为 Profile 健康提示**",不作为阻断。

### 2.4 EvidenceLocator(保留 v3,工程规范)

Langfuse trace 的 observations 结构对应的统一 schema:

```json
{
  "trace_id": "tr_abc123",
  "observation_id": "obs_2",
  "node_path": "$.output.refund_amount",
  "text_span": [12, 28],
  "node_kind": "tool_call_argument"
}
```

`node_kind` 枚举:`final_message` / `intermediate_message` / `tool_call_argument` / `tool_call_result` / `retrieval_chunk` / `thought` / `system_prompt`。封装在 `EvidenceResolver` 模块,屏蔽 Langfuse trace schema 演进。

### 2.5 修复建议:恢复协作者立场

P2C 指出:v1 是协作者,v2 是测量仪,v3 半只脚踩回协作者——没想清楚。**v4 明确选协作者**。judge 是启发式调试助手,不是判决权威。

每条扣分同时输出两种信息:

```json
{
  "deduction": { ... },
  "root_cause_hints": ["retrieval_miss", "prompt_constraint_missing"],
  "suggested_fix": {
    "text": "建议在 system prompt 中增加'退款承诺前必须调用 verify_order 工具'的显式约束",
    "confidence": 0.7,
    "kind": "heuristic",
    "disclaimer": "启发式建议,不承诺对"
  }
}
```

**`suggested_fix`**(v4 恢复)· 由 LLM 自由生成的启发式修复建议。UI 明确标识 "启发式、不承诺对"。工程师一眼判断是否值得尝试,可一键标"无用"进 feedback。不做"采纳→改善率 ≥ 50%"这种承诺——承认启发式就是启发式。

**`root_cause_hints`**(保留 v3 结构)· 固定枚举,Scorer 确定性分配,可被 CI 和趋势分析消费:

| 标签 | 含义 |
|---|---|
| `prompt_constraint_missing` | system prompt 缺显式约束 |
| `prompt_fewshot_gap` | few-shot 未覆盖此类 case |
| `retrieval_miss` | 检索 chunk 未命中 |
| `retrieval_stale` | 检索到过时信息 |
| `tool_spec_unclear` | 工具描述不清 |
| `tool_not_called` | 应调用的工具未调用 |
| `router_misdispatch` | 上游路由错误 |
| `temperature_variance` | 随机性高 |
| `policy_ambiguity` | 政策文本本身有歧义 |

v3 的"采纳→消失率 ≥ 30% 否则下线 hint 类别"的 KPI 降为**可选观测指标**,不作为去留门槛。

### 2.6 信度保证(v4 降为建议 + 升级通路)

**默认态(草案 Profile)** · 不要求 κ、不要求校准集规模。UI 标识 "draft"。可跑 run、看报告、走 CI 回归,**不能挂在 go/no-go 面板**。

**升级态(已验证 Profile)** · 自愿升级,达成以下之一即升级:

| 通路 | 条件 |
|---|---|
| **快速通道** | 语义维度 100 条标注 / 维度(v3 是 200-300),κ 达到事实类 0.70、语义类 0.60、表达类 0.50(v3 略严) |
| **经验通道** | Profile 运行 ≥ 3 个月 + 争议翻转率 ≤ 15% + 已产出 ≥ 50 次报告 |

升级审阅由**兼任方法论审阅人**做,审阅 SOP 附在场景包,约 2 小时完成。

**工具**:`calibration_toolkit/kappa_ci.py`(保留 v3)输入 N + κ 返回 CI + 样本量建议。

**自动回放**:只对已验证态 Profile,cron **每月一次**(v3 是每周),降低 Jira 噪音。

### 2.7 效度:从准入门槛降为进阶验证(v4 核心回退)

**这是 v4 相对 v3 的最大回退**。

**默认态**:**不要求效度验证**。PM 定义 Profile、跑样本、看报告、迭代——不需要线上 500 条、不需要 Spearman ρ。

**已验证态的进阶门槛**:

| 通路 | 条件 |
|---|---|
| **线上指标通路** | ≥ 300 条(v3 是 500)线上样本 + ρ ≥ 0.4(v3 是 0.5),统计方法:Spearman + bootstrap 95% CI / 二元指标 clustered bootstrap / verdict 档位对比 Mann-Whitney U |
| **专家共识通路**(v4 新增) | 3 位领域专家对 100 条样本独立标"应通过/不应通过",Profile 的 verdict 和多数共识一致率 ≥ 75% |

专家共识通路是对没有线上指标数据的团队的通路——v1 对"维度定义者"的信任回归。

**月度回算**:仅针对 validity_verified Profile,漂移 > 0.15 触发复评。

**不走升级通路的 Profile**:可以长期停在草案态,没问题。v4 承认大多数 Profile 的实际用途是"帮 PM 迭代判据",本来就不需要承担 go/no-go 责任。

### 2.8 双轨评测(保留结构,明确语义)

- **B 轨 日常回归**(主力) · Profile 固定 regression set(≥ 30 条,v3 是 50)重跑,diff 展示,CI 5 分钟出。**绝大多数 run 走 B 轨**。草案态 Profile 也可用 B 轨。
- **A 轨 深度验证**(仪式) · 只在升级到已验证态 / 月度回算时跑。v4 明确承认:**A 轨是审计仪式,不是日常**,不强制所有 Profile 都跑。

### 2.9 标准化评分输出

```json
{
  "verdict": "需修复",
  "verdict_reason": "2 项严重扣分",
  "profile_maturity": "draft",
  "dimensions": [...],
  "redlines_triggered": {"hard": ["R-07"], "soft_pending_review": []},
  "meta": {"profile_id": "...", "profile_version": "...", "run_id": "...", "cost_usd": 0.042}
}
```

`profile_maturity`(v4 新增):`draft` / `verified`。UI 对 draft 加强水印,go/no-go 面板只接受 verified。

---

## 三、系统架构

### 3.1 Build-vs-Buy 能力差分表

| 能力 | Langfuse 原生 | v4 自建 |
|---|---|---|
| Trace / Dataset / Run / Prompt 版本化 / CI webhook / 人工标注 | ✅ | 直接用 |
| LLM-as-judge 执行 | ✅ | 用,只换 rubric 模板 |
| 规则层 | ⚠️基础 | 补齐,custom scorer 插件 |
| **业务断言引擎 + API 钩子** | ❌ | ✅ 自建 |
| **中文场景包库** | ❌ | ✅ 自建 |
| **升级通路(审阅流程 + 校准工作台)** | ❌ | ✅ 自建 |
| **硬/软红线路由 + 人审队列** | ⚠️无分流 | ✅ 自建 |
| **争议池** | ⚠️有反馈无流程 | 补齐 |
| **EvidenceResolver** | ❌ | ✅ 自建 |

### 3.2 架构图

```
      ┌─────────────────────────────────────────┐
      │   Langfuse (self-host)                  │
      │   Trace / Dataset / Judge / Feedback /  │
      │   Prompt Version / CI Webhook           │
      └────────┬────────────────────────▲───────┘
               │ webhook/API            │ feedback/score 写回
               ▼                        │
   ┌──────────────────────────────────────────────┐
   │   v4 Extension Layer (Python service)        │
   ├──────────────────────────────────────────────┤
   │  Orchestrator                                │
   │  Scorer Plugins                              │
   │    ├ RuleScorer (Layer 1)                    │
   │    ├ AssertionEngine (Layer 2) ──┐           │
   │    ├ EvidenceLLMScorer (Layer 3) │           │
   │    └ ReferenceScorer (Layer 4)   │           │
   │  EvidenceResolver                            │
   │  RedlineRouter                               │
   │  UpgradeWorkflow (draft → verified)          │
   │  RegressionRunner (B 轨)                     │
   │  ValidityPipeline (A 轨,仅 verified 走)     │
   └──────┬──────────────────┬────────────────────┘
          │                  │
          ▼                  ▼
   ┌──────────────┐   ┌───────────────────────┐
   │ Knowledge    │   │ Ticketing Adapter     │
   │ Adapters     │   │  Jira (主) / Linear    │
   └──────────────┘   └───────────┬───────────┘
                                  ▼
                         ┌────────────────┐
                         │ Review Queue UI │
                         └────────────────┘
```

**关键数据流**:
- **评测 run**:Langfuse webhook → Orchestrator → Scorer chain → 聚合 → 写回 Langfuse feedback + 本地 run_record
- **升级审阅**:PM 提交升级申请 → 审阅人工作台拉起校准集 + ρ 结果 + SOP 清单 → 通过/拒绝 → Profile 状态切换
- **效度/κ 漂移**(仅 verified):月度 cron → 低于阈值 → Jira issue → Slack → webhook 回传更新状态
- **争议处理**:UI "不同意" → disputes 表 → 周聚合 → 同一 criterion 争议 ≥ 5 建 Jira 工单

### 3.3 工单系统对接

Jira 为主(Linear / GitHub Issues 备选,适配器模式)。字段映射:

- `summary`: `[profile_id] dimension / drift_type - brief`
- `description`: trace_id + Langfuse dataset 链接 + κ/ρ + 阈值
- `labels`: `kappa_drift` / `validity_drift` / `dispute_cluster`
- `assignee`: Profile.calibration_owner(兜底 backup_owner → 兜底兼任审阅人)
- `due_date`: κ 工单 5 工作日,ρ 工单 30 自然日

**频率**:κ 漂移工单从 v3 的"每周"降为"**每月,仅 verified Profile**"。草案 Profile 不产生 Jira 噪音。

**Owner 连续性**:
- Profile 必填 `calibration_owner` 和 `backup_owner`(仅 verified Profile 要求)
- 离职由 HR webhook / 手动标记 → 自动转派 backup → 转派兼任审阅人 → 高优 Slack
- 请假同步日历,假期不计 SLA

### 3.4 Scorer 骨架接口契约

```
eval_ext/
  scorers/
    base.py           # Scorer Protocol, DimensionResult dataclass
    rule.py           # YAML-driven
    assertion.py      # Expr parser + hook registry
    evidence_llm.py   # LLM 调用 + JSON Schema 校验
  resolver.py         # EvidenceResolver
  profile.py          # Profile schema (pydantic), maturity 字段
  orchestrator.py     # run_profile(trace_id, profile_id) -> RunRecord
  upgrade/
    workflow.py       # 升级申请 + 审阅工作台
    sop_checklist.py
  validity/
    full.py           # A 轨(仅 verified)
    regression.py     # B 轨
  calibration/
    kappa_replay.py
    kappa_ci.py
  adapters/
    jira.py
    langfuse_client.py
```

**错误码**:`EVAL-E-{layer}-{code}`(如 `EVAL-E-ASSERT-002 hook_timeout`)。
**日志**:结构化 JSON,字段 `trace_id, profile_id, scorer, duration_ms, token_cost_usd, error`。
**健康检查**:`GET /health`(进程)、`GET /ready`(Langfuse / Jira / LLM Gateway 连通性)。

### 3.5 成本与存储

**数据量**(20 Agent × 500 样本/周):周增 200 MB,年增 10 GB。

**Retention**:

| 数据 | 热存 | 冷存 | 归档 |
|---|---|---|---|
| Trace(Langfuse) | 90 天 | 180 天 | 压缩摘要 |
| Judge 原始响应 | 30 天 | 60 天 | 删除,留 evidence JSON |
| EvidenceLocator + Criterion | 永久 | — | — |
| 校准集 + regression set | 永久 | — | — |

**预算双尺度**:
- 月度:Profile `monthly_judge_budget_usd` 必填,**默认 $20**(v3 是 $50),超 80% Slack 告警,超 100% 停 Layer 3
- 单次:`max_run_cost_usd` 必填,默认 $0.20,超即中止
- 级联定义:跨 Layer 级联——Layer 3 先 Haiku 筛,低置信/命中再 Opus 复核,实测省 20-30%

单 run 成本透传到 UI 和 CI(`::eval-cost::0.042`)。

---

## 四、冷启动与采纳路径

### 4.1 角色(v4 回退到兼任)

| 角色 | FTE | 职责 |
|---|---|---|
| PM / 政策负责人 | 兼任 | 定义维度、跑 Profile、看报告 |
| Agent 工程师 | 兼任 | CI 集成、看启发式建议 |
| **方法论审阅人** | **兼任(非专职)** | 升级到 verified 的审阅,约 2 小时/次 |
| Calibration 负责人 | 仅 verified Profile 指定 | 校准集维护、漂移响应 |
| 平台研发 | 1.0-2.0 FTE | 扩展层开发维护 |

**关键变化**:v3 的 Methodology Lead 1.0 FTE 专职改为兼任审阅人。组织已有的资深 PM、数据科学家或 QA Lead 中任一胜任。

### 4.2 单 Profile 冷启动人时(分两段)

**草案态(Draft Profile)**:
- 从场景包 fork + 调参 + 首次报告:**2-4 人时**
- 不要求校准集、不要求效度验证

**升级到已验证态(可选)**:
- 校准集标注(100 条 × 5 语义维度,LLM 预标注 + 人复核 40s/条):~12 人时
- 效度验证(300 线上样本 + ρ,或 100 条专家共识):~8 人时
- 审阅:2 人时
- 升级总成本:**~22 人时**

**对比 v3**:v3 单 Profile 冷启动 42 人时全强制;v4 让 2-4 人时能起一个,想升级再投 22 人时。**入场门槛拉低一个数量级**。

### 4.3 6 个月北极星指标

| 指标 | 目标 |
|---|---|
| 草案态 Profile 数 | ≥ 20 |
| 已验证态 Profile 数 | ≥ 4 |
| WAU | ≥ 20 |
| 团队渗透 | ≥ 5 个业务团队有 ≥ 1 个 Profile |
| B 轨日常回归次数 | ≥ 100/周 |
| 升级审阅通过率 | ≥ 70% |

v3 要求 ≥ 6 个过效度 Profile;v4 只要 4 个升级——承认大多数用法是草案态,**这才是常态**。

### 4.4 三阶段

**Phase 1 · Langfuse + 轻量 MVP(0-4 周)**
- 部署 Langfuse
- 交付 `eval_ext` 骨架 + 1 个场景包
- 让 2-3 个 PM 能用草案态 Profile 跑 Agent,不要求效度、不要求校准
- 交付物:能用的工具,不是首个已验证 Profile

**Phase 2 · 场景包 + 首个升级(4-12 周)**
- 3 个场景包(客服、知识库问答、结构化抽取)
- 第 1 个 Profile 走完升级到 verified 的流程,作为样板
- 更多团队起草案态 Profile

**Phase 3 · CI 集成 + 升级常态化(12 周+)**
- CI 集成 B 轨回归,diff 挂 PR
- 升级审阅做成月度 office hour
- 场景包治理:兼任审阅人轮值

### 4.5 采纳铁律

先给结论再给配置 / 对比优先于绝对分 / 扣分可反驳 / 工具非监督。

---

## 五、风险与对策

| 风险 | 对策 |
|---|---|
| 草案态 Profile 被误当决策依据 | UI 强水印 `draft, not for go/no-go`;go/no-go 面板只接受 verified |
| 团队都停在草案态没人升级 | 升级 office hour + SOP 清单降低升级成本;但不强制(草案态本身是合法用法) |
| `suggested_fix` 不准误导工程师 | UI 标识"启发式、不承诺对";一键标"无用"进 feedback |
| Langfuse 升级不兼容 | EvidenceResolver 适配层隔离 |
| 硬红线覆盖不足 | ≥ 60% 作为健康提示,非阻断 |
| Owner 不可用 | Backup Owner + HR webhook 自动转派(仅 verified 要求) |
| 存储成本失控 | retention 分层,Judge 原始响应 60 天删 |
| 单 run 成本黑箱 | `RunRecord.cost_usd` 透传 UI/CI,`max_run_cost_usd` 必填 |
| 扩展层干扰 Langfuse trace | 只读消费 + 写回 feedback,不改 trace 原数据 |
| 升级门槛太低"已验证"名不副实 | 审阅人按 SOP 清单,可拒绝升级;每月抽检 |
| 方法论审阅人能力不均 | SOP 清单 + 样本题库 + 跨审阅人的争议升级机制 |

---

## 六、开发者工效学(保留 v3 §6)

### 6.1 本地 debug
- **CLI**:`eval run --trace-id xxx --profile foo` 本地拉 trace 跑 scorer,可 pdb 断点
- **Offline replay**:`eval replay --from-run rr_123` 拉历史 run 快照,hook 走 mock
- **Scorer 单测**:每个 scorer 自带 pytest 套件,`tests/fixtures/` 放 trace JSON

### 6.2 Mock 与测试数据
- Assertion hook mock:测试时 `@assertion_hook` 自动替换为 `MockHookRegistry` 返回 fixture
- LLM mock:`EVAL_LLM_MODE=mock` 走 recorded response;`record` 自动录制
- Fixture 库:场景包附 `fixtures/traces/*.json`

### 6.3 单 run 成本透传
- UI:每次 run 顶部 `cost: $0.042 | duration: 3.2s | tokens: 8,123`
- CI:`::eval-cost::0.042`,GitHub Actions 可聚合 PR 总成本
- 超 `max_run_cost_usd` 立即中止 + 日志高亮

### 6.4 快速迭代循环
- B 轨是日常主力:prompt 改一行 → push → CI 5 分钟出 diff
- A 轨不阻塞日常,只在升级 / 月度回算跑

### 6.5 文档与 onboarding
- `eval_ext/README.md` 含 10 分钟 quickstart
- `docs/scorer_recipes/` 每种 scorer 一个最小可运行示例
- `eval scaffold --from customer-service --name my-agent` 一条命令 fork 场景包

---

## 七、一句话主张

Agent 评测平台是**让 PM 当周就能起一个 Profile 试、让做重决策的人在需要时走严格通路**的协作工具。默认轻量、验证是升级不是门槛、judge 是协作者不是判决者——**把"定义好"的话语权还给业务方,把"证明测得准"的严格性留给需要它的场景**。

---

## 2C-rollback 日志

### 保留 v3 的修改(工程硬底、客观结论、与漂移无关)

- **Langfuse 基座 + Build-vs-Buy 收敛**:这是 build-vs-buy 的客观结论,保留
- **四层打分器接口细节 + YAML 断言 + 三问法**(§2.2):纯文档质量提升,保留
- **硬/软红线分流**(§2.3):对 v1 一刀切的合理修正,保留(但硬红线覆盖率从硬要求降为健康提示)
- **EvidenceLocator schema + Langfuse observation 示例**(§2.4):工程规范,保留
- **Scorer 骨架接口契约 + 错误码 + 日志 + 健康检查**(§3.4):工程规范,保留
- **存储 retention 分层 + 预算双尺度 + 级联定义 + 单 run 成本透传**(§3.5):工程规范,保留
- **Jira 字段映射 + Backup Owner + HR webhook 转派**(§3.3):工程规范,保留(但频率降低、仅 verified 要求)
- **开发者工效学整节**(§6):v3 对 v2 的纯工程改进,与漂移无关,整体保留
- **B 轨日常回归 ≥ 30 条 + CI 5 分钟**(§2.8):对"小改动太重"的合理响应,保留

### 回退的修改(把漂移拉回来)

- **Spearman ρ ≥ 0.5 作为 Profile 准入硬门槛** → 降为"已验证态"的升级条件,阈值放宽到 0.4;新增"专家共识 75% 一致率"通路,让没有线上指标的团队也能升级。**理由**:P2C 指出这让 v1 的快速迭代场景跑不起来
- **校准集 200-300 条/维度硬要求** → 降为语义类 100 条,且**只在升级到 verified 时要求**;草案态无需校准集。**理由**:入场门槛回拉
- **Methodology Lead 1.0 FTE 专职** → 改为**兼任审阅人**,组织已有的资深 PM / DS / QA Lead 胜任。**理由**:P2C 指出专职化改变了目标用户画像
- **每 Profile 必填 Calibration Owner + 5 工作日 SLA** → 仅 verified Profile 要求;草案态自由。**理由**:草案态是让 PM 自己玩的
- **κ 每周自动回放 + Jira 工单** → 仅 verified Profile,频率降为**每月**。**理由**:避免草案 Profile 产生 Jira 噪音
- **删除 suggested_fix 的立场** → **恢复 suggested_fix**,但明确标识"启发式、不承诺对";同时保留 root_cause_hints 作为结构化补充。**理由**:v4 明确 judge = 协作者,不是测量仪
- **root_cause_hints 的"采纳→消失率 ≥ 30% 否则下线" KPI** → 降为**可选观测指标**。**理由**:承认启发式就是启发式,不做过度工程化承诺
- **provisional_validity + "仅供参考" + 多档降级 verdict** → 简化为 Profile `maturity` 两档(draft / verified)+ 标准 verdict。**理由**:v3 的多档降级让业务方读不懂
- **月度 LLM 预算默认 $50** → 降为 **$20**。**理由**:降低入场成本
- **新增场景维度 ≥ 20 条判据样例** → 降为 **10 条**。**理由**:鼓励试
- **单 Profile 冷启动 42 人时全强制** → 拆成草案 2-4 人时 + 升级 22 人时,大多数 Profile 只走第一段。**理由**:把一次性门槛拆成两段
- **北极星指标(≥ 6 个过效度 Profile)** → 改为 ≥ 4 个升级 + ≥ 20 个草案,承认草案态是常态。**理由**:指标反映真实用法

### 核心立场转变

P2C 第三个追问——judge 是测量仪还是协作者——是所有漂移的根源。v4 明确选**协作者**。PM 对"什么算好"有最终话语权,judge 提供启发式辅助(`suggested_fix`)+ 结构化证据(`root_cause_hints`)。需要"证明测得准"的场景走升级通路,不强制所有人走。

这把 v3 的学术仪式从"入场门"移到"需要它的那天再做"——让 v1 想服务的用户(单个 PM 想起一个维度就当周试)重新进得来。
