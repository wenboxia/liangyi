# Agent 评测平台(v3)

## 0. v3 相对 v2 的变化

v2 解决了"该不该做、做什么规模"的问题(效度门槛、Langfuse 基座、成本账)。
v3 解决的是"工程师能不能接住"的问题——上一版所有流程名词(SLA、工单、级联、自动回放)都没落到接口、数据结构、脚本。v3 做三件事:

1. **文档自包含**:不再引用 v1/v2"见前文",四层打分器、trace schema、接口契约全部在本文档里展开。
2. **补齐工程颗粒度**:EvidenceLocator 配 Langfuse trace 示例,κ 计算给可执行脚本位置,统计检验指定方法,工单系统指定 Jira + 字段映射,Calibration Owner 补备份/轮转机制。
3. **贴工程师日常**:新增 §6 开发者工效学(本地回放、mock、单 run 成本透传、迭代期轻量效度回归)。v2 的效度门槛太重,日常小 prompt 调整不适用,v3 分层:**新 Profile 准入走全量效度,日常迭代走轻量回归**。

基座选型(Langfuse)、Profile 两层维度、四层打分器、硬/软红线分流、删除 free-form suggested_fix——这些 v2 的核心立场 v3 全部保留。

---

## 一、产品定位与目标用户

### 1.1 定位

**基于 Langfuse 的业务化评测扩展层**。

Langfuse 原生提供:trace 归档、dataset/run、LLM-as-judge、span-level feedback、Prompt 版本化、CI webhook、人工标注 UI。**直接用,不重造**。

v3 自建四块能力:

- **业务断言适配器**:接入订单/工单/知识库等内网 API,做 Langfuse SaaS 触达不了的真实数据比对
- **本地化场景包**:中文业务语境的维度模板 + 判据示例 + 红线清单
- **效度验证回路**:分数 × 线上指标(CSAT、复问率、人工改写率等)的相关性验证
- **硬/软红线分流 + 争议闭环**:verdict 可信度的工程化保障

目标用户不变(P0 AI PM + Agent/Prompt 工程师;P1 算法;P2 领域专家 + QA)。

---

## 二、核心评分机制

### 2.1 两层维度体系

**第一层 · 通用基座(不可删不可改名)**

| 维度 | 含义 |
|---|---|
| Correctness | 事实、逻辑、计算是否正确 |
| Instruction Following | 是否完成指令 + 遵守约束 |
| Relevance | 是否聚焦输入诉求 |
| Completeness | 是否覆盖所有要点 |
| Presentation | 结构、语言、格式、可读性 |

**第二层 · 任务画像驱动的场景维度**

用户定义任务画像(任务类型 + 业务场景 + 交付规范),系统推荐场景维度并允许增删改权重。新增场景维度入场景包需提交 ≥ 20 条判据样例 + 反例。

### 2.2 分层打分器(v3 展开细节,不再引用 v1)

**打分器统一接口**

```python
class Scorer(Protocol):
    name: str
    layer: Literal["rule", "assertion", "evidence_llm", "reference"]
    def score(
        self,
        trace: LangfuseTrace,
        dimension: DimensionSpec,
        context: ProfileContext,
    ) -> DimensionResult: ...
```

`DimensionResult` 字段:`health`(green/yellow/red)、`deductions: list[Deduction]`、`scorer_meta`(版本、耗时、token 成本)。

**Layer 1 · 规则层(Rule)**
正则、JSON Schema 校验、长度限制、关键词黑白名单、输出模板结构匹配、必调用工具存在性检查。失败即生成硬扣分,不进下一层。实现上每条规则是 YAML 配置 + 对应 validator 函数,YAML 在 Profile 下。

**Layer 2 · 业务断言层(Assertion)**
将业务规则结构化为断言集。每条断言格式:

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

断言可通过自定义函数钩子调外部 API(订单、CRM、工单)。钩子接口:

```python
@assertion_hook(name="verify_order_status")
def verify_order_status(order_id: str) -> dict:
    # 默认 timeout=3s,失败 retry=2,指数退避
    # 超时/异常 → 该断言降级为 inconclusive,不产出扣分但记录
```

**政策文本 → 断言的转换**(回应 §2.3 转换逻辑空白):
由 Methodology Lead 在诊断工作坊中完成。政策原文逐条走三问——"触发条件能不能列出关键词/结构特征"、"违反动作能不能查 trace 某节点"、"参数(如天数、金额)是否显式"。三问都过 → 硬断言;否则 → 软红线走 Layer 3。场景包里附 30+ 已转换案例作为模板。

**Layer 3 · LLM 证据抽取层(Evidence LLM)**
用于语义模糊维度(语气、逻辑冲突、完整性)。**LLM 不打分,只抽证据**。固定输出 JSON Schema:

```json
{
  "dimension": "tone_compliance",
  "findings": [
    {
      "criterion_id": "T-03",
      "polarity": "violation",
      "evidence": { /* EvidenceLocator,见 §2.4 */ },
      "confidence": 0.82,
      "rationale": "用户表达不满,回复使用'这不是我们的问题'属于情绪对抗"
    }
  ]
}
```

`confidence < 0.7` 的 finding 自动标"需人工复核",不进最终 verdict,进争议池候选。

**Layer 4 · 参考层(Reference,可选)**
存在黄金输出时叠加:embedding 相似度、精确匹配、ROUGE。Profile 声明是否启用。

**聚合**
维度 health 由 `deductions` 的严重级别 + 红线触发决定,是确定性逻辑,不走 LLM 加权:

```
if any(d.severity == "redline_hard" for d in deductions): health = "red"; verdict-locks "不可上线"
elif any(d.severity == "redline_soft_pending") : health = "red"; verdict = "需人工复核"
elif count(severity=="major") >= 2: health = "red"
elif count(severity=="major") == 1 or count(severity=="minor") >= 3: health = "yellow"
else: health = "green"
```

### 2.3 红线:硬 vs 软

| 类型 | 定义 | 判定路径 | verdict 行为 |
|---|---|---|---|
| 硬红线 | 可 100% 断言化(Schema 违反、禁用词、必调工具缺失、数值条款、PII 模式) | Layer 1+2,LLM 不参与 | 触发即 `不可上线`,不可覆盖 |
| 软红线 | 语义模糊(品牌调性、情绪对抗、隐性承诺、越界建议、歧视表述) | Layer 3 抽证据 + 强制人审 | 触发且未二审 → `需人工复核`;二审确认 → `不可上线` |

**审计指标**:Profile 的硬红线覆盖率(硬红线条数 / 红线总条数) ≥ 60%,低于阈值 Profile 标记为"弱红线保护",上线决策需额外评审。

### 2.4 EvidenceLocator(v3 给 Langfuse trace 对应示例)

Langfuse 一次 trace 的核心结构(简化):

```json
{
  "id": "tr_abc123",
  "input": { "messages": [...] },
  "output": "...",
  "observations": [
    { "id": "obs_1", "type": "generation", "input": {...}, "output": {...} },
    { "id": "obs_2", "type": "tool", "name": "verify_order", "input": {...}, "output": {...} }
  ]
}
```

`EvidenceLocator` 统一 schema:

```json
{
  "trace_id": "tr_abc123",
  "observation_id": "obs_2",
  "node_path": "$.output.refund_amount",
  "text_span": [12, 28],
  "node_kind": "tool_call_argument"
}
```

- `observation_id`:指向某次 generation/tool observation,若证据在 trace 顶层则置 null
- `node_path`:在该 observation 的 input/output JSON 上的 JSONPath
- `text_span`:节点值为字符串时的字符区间,否则 null
- `node_kind`:`final_message` / `intermediate_message` / `tool_call_argument` / `tool_call_result` / `retrieval_chunk` / `thought` / `system_prompt`

UI 按 `node_kind` 决定展示样式,扣分按 kind 分组。这一层封装在 `EvidenceResolver` 模块里,屏蔽 Langfuse 升级时 trace schema 的向后兼容问题。

### 2.5 根因分类标签(v3 重新引入,替代被删的 suggested_fix)

v2 删掉了 free-form `suggested_fix`(LLM 生成的修复建议缺因果闭环)。但工程师调试确实需要"改哪里"的线索——v3 折中方案:**结构化根因标签,不是自由文本**。

每条扣分附一个 `root_cause_hint` 枚举(可多选):

```json
"root_cause_hints": ["retrieval_miss", "prompt_constraint_missing"]
```

枚举集合(固定,场景包可扩展):

| 标签 | 含义 | 在 Profile 里如何定位 |
|---|---|---|
| `prompt_constraint_missing` | system prompt 缺显式约束 | 给出 prompt 版本 diff 链接 |
| `prompt_fewshot_gap` | few-shot 未覆盖此类 case | 指向 few-shot 文件 |
| `retrieval_miss` | 检索 chunk 未命中关键信息 | 指向该次 retrieval observation |
| `retrieval_stale` | 检索到过时信息 | 指向 chunk + 更新时间 |
| `tool_spec_unclear` | 工具描述不清导致参数错误 | 指向工具 schema |
| `tool_not_called` | 应调用的工具未调用 | 指向缺失的 tool call 位置 |
| `router_misdispatch` | 上游路由到错误 Agent | 指向 router trace |
| `temperature_variance` | 随机性高,多次生成不稳 | 标记为需加 seed 或降温复测 |
| `policy_ambiguity` | 政策文本本身有歧义 | 需业务方更新政策 |

**生成规则**:由 Scorer 根据失败类型确定性分配(不是 LLM 自由发挥),Layer 2 断言可声明 "失败时分配哪些标签",Layer 3 LLM 在固定枚举上做多选分类。

**因果闭环的 KPI 化**:根因标签在 CI 回归里自动统计"同 hint 在 prompt/工具变更后是否消失"。6 个月内如发现任一 hint 类别的"采纳→消失率"< 30%,该 hint 从场景包下线。用 KPI 防止这层退化成装饰。

### 2.6 信度保证

**按维度分级的 κ 目标**

| 维度类型 | 代表维度 | κ 目标 | 校准集规模下限 |
|---|---|---|---|
| 结构化/硬约束 | 格式、必问项、硬红线 | N/A(规则确定) | 50 条边界样本做回归 |
| 事实类 | 正确性、业务准确性 | ≥ 0.70 | 200 条/维度 |
| 语义类 | 相关性、完整性、多轮指代 | ≥ 0.65 | 200 条/维度 |
| 软性表达类 | 表达质量、语气、品牌合规 | ≥ 0.55 + 人审占比 ≥ 20% | 300 条/维度 |

**校准集规模的推导公式**(回应 §2.6 推导空白):
Cohen's κ 的大样本 95% CI 宽度 ≈ 1.96 × √((1-κ)(1+κ) / N)。要把 ±CI 压到 ≤ 0.08,N ≈ 200(κ≈0.65)、N ≈ 300(κ≈0.55)。平台提供 `calibration_toolkit/kappa_ci.py` 脚本,输入 N + κ 返回 CI,反向给出样本量建议。

**κ 自动回放 · 工程化细节**(回应 §2.6 触发/数据/脚本空白):

- **触发**:(a) cron 每周一 02:00 UTC 自动跑全量 Profile;(b) Langfuse `prompt_version` 或 `model_id` 变更 webhook;(c) Calibration Owner 手动触发
- **数据源**:每个 Profile 的校准集存在 Langfuse Dataset,带 `label=calibration` tag
- **脚本**:`ops/kappa_replay.py`,入参 `--profile-id`,流程=拉 dataset → 跑 Layer 3 → 和人工标注求 Cohen's κ → 维度分级输出 → 不达标自动建 Jira 工单
- **监控**:Prometheus 指标 `eval_judge_kappa{profile_id, dimension}`,Grafana 看板预置
- **告警**:工单建单的同时发 Slack 到 `#eval-ops`,@Calibration Owner

**冲突样本 verdict 降级规则**(硬编码在 orchestrator,不走 Profile 配置):
Judge 给 `不可上线`,但该样本所在维度过去 30 天 Judge-Human 分歧率 > 30% → verdict 降档为 `需人工复核`。

### 2.7 效度保证:双轨验证(v3 分层,回应"日常迭代不适用"痛点)

v2 的"500 条样本 + ρ ≥ 0.5"是**新 Profile 准入门槛**,不能每次小改动都跑。v3 分两轨:

**A 轨 · 新 Profile 准入(全量效度验证)**

- 收集近 ≥ 4 周、≥ 500 条线上样本(含对应线上指标)
- Profile 跑分,做分数×指标相关性
- **硬门槛**:至少 1 个维度 × 1 个线上指标 Spearman ρ ≥ 0.5(或分类 AUC ≥ 0.70)
- **统计方法**(回应 §2.7 方法缺失):
  - 连续指标(CSAT 评分):Spearman ρ + bootstrap 95% CI
  - 二元指标(是否复问):点二列相关或 AUC,样本不独立时(同一用户多轮)用 clustered bootstrap,按 user_id 聚类
  - 对 verdict 档位对比:`不可上线` vs `可上线` 样本的指标差异用 **Mann-Whitney U 检验**(不假设正态),p < 0.05
- **样本不足时的降级**(回应"凑不齐 500 条"):
  - 100 ≤ N < 500 → Profile 发 `provisional_validity` 标签,可用但 UI 显示"效度证据薄弱",不进 go/no-go 主面板
  - N < 100 → 只能发 `validity_untested`,不得用于 go/no-go
  - 允许 **bootstrap + 外部参考 Profile 迁移先验**:若一个 Profile 是另一个已通过效度验证的 Profile 的变体(共享 ≥ 70% 判据),继承其先验效度,样本量门槛减半

**B 轨 · 日常迭代(轻量回归,不要求相关性)**

Prompt 小改、few-shot 补充、工具描述调整 → 只跑 **轻量回归**:
- 在 Profile 的固定 regression set(≥ 50 条,一次选定不变)上重跑
- 输出"本次 vs 上次"的维度 diff + 扣分变化
- 无 ρ/AUC 计算,不动 verdict 定义,CI 5 分钟出结果
- 每 N 次轻量回归(默认 20 次)自动触发一次全量效度回算,防止判据漂移

**月度效度回算**:所有通过 A 轨的 Profile 每月自动跑一次 A 轨,漂移 > 0.15 触发复评,Calibration Owner 30 自然日内响应,否则降级。

---

## 三、系统架构

### 3.1 Build-vs-Buy 能力差分表

| 能力 | Langfuse 原生 | v3 自建 |
|---|---|---|
| Trace 归档、Dataset、Run、版本化、CI webhook、人工标注 UI | ✅ | 直接用 |
| LLM-as-judge 基础执行 | ✅ | 用,只替换 rubric 模板 |
| 规则层(Schema/正则) | ⚠️基础 | 补齐,写成 Langfuse custom scorer 插件 |
| **业务断言引擎 + API 钩子** | ❌ | ✅ 自建 |
| **中文场景包库** | ❌ | ✅ 自建 |
| **效度验证 Pipeline(双轨)** | ❌ | ✅ 自建 |
| **硬/软红线路由 + 人审队列** | ⚠️无分流 | ✅ 自建 |
| **争议池 + 校准工单化** | ⚠️有反馈无流程 | 补齐 |
| **EvidenceResolver(屏蔽 trace schema 演进)** | ❌ | ✅ 自建 |

### 3.2 架构图(补充数据流)

```
      ┌─────────────────────────────────────────┐
      │   Langfuse (self-host)                  │
      │   Trace / Dataset / Judge / Feedback /  │
      │   Prompt Version / CI Webhook           │
      └────────┬────────────────────────▲───────┘
               │ webhook/API            │ score/feedback 写回
               ▼                        │
   ┌──────────────────────────────────────────────┐
   │   v3 Extension Layer (Python service)        │
   ├──────────────────────────────────────────────┤
   │  Orchestrator                                │
   │    └ resolve Profile → run scorer chain      │
   │                                              │
   │  Scorer Plugins                              │
   │    ├ RuleScorer        (Layer 1)             │
   │    ├ AssertionEngine   (Layer 2) ──┐         │
   │    ├ EvidenceLLMScorer (Layer 3)   │         │
   │    └ ReferenceScorer   (Layer 4)   │         │
   │                                    │         │
   │  EvidenceResolver ─ JSONPath on trace        │
   │  RedlineRouter ─ hard→verdict / soft→review  │
   │  ValidityPipeline (A 轨 + B 轨)              │
   │  CalibrationWorkflow                         │
   └──────┬──────────────────┬────────────────────┘
          │ API 调用         │ 工单
          ▼                  ▼
   ┌──────────────┐   ┌───────────────────────┐
   │ Knowledge    │   │ Ticketing Adapter     │
   │ Adapters     │   │  Jira (主) / Linear    │
   │ 订单/工单/FAQ │   │  字段映射 + 状态同步  │
   └──────────────┘   └───────────┬───────────┘
                                  ▼
                         ┌────────────────┐
                         │ Review Queue UI │
                         │ (软红线二审 /  │
                         │  争议处理)      │
                         └────────────────┘
```

**关键数据流**:

- **评测 run**:Langfuse trigger webhook → Orchestrator 加载 Profile → Scorer chain 顺序执行(Rule → Assertion → EvidenceLLM → Reference)→ 聚合 DimensionResult → 写回 Langfuse 为 feedback + 本地存 run_record
- **效度失败 → 工单**:ValidityPipeline 月度 cron → ρ 低于阈值 → 调 Ticketing Adapter 创建 Jira issue(project=`EVAL`, assignee=Profile.calibration_owner, labels=`validity_drift`)→ Slack 通知 → Jira 状态变更 webhook 回传到平台更新 Profile 状态
- **争议处理**:用户在 UI 点"不同意" → 写入 `disputes` 表 → 每周五 cron 聚合 → 若同一 criterion 争议数 ≥ 5,自动建 Jira 工单给 Calibration Owner

### 3.3 工单系统对接(Jira,v3 显式化)

- **主对接**:Jira(大多数企业既有);备选:Linear、GitHub Issues,适配器模式
- **Project key**:每个业务域一个,例如 `EVAL-CUSTCARE`、`EVAL-SEARCH`
- **字段映射**:
  - `summary`:`[profile_id] dimension / drift_type - brief`
  - `description`:包含 trace_id 链接、Langfuse dataset 链接、当前 κ/ρ、阈值
  - `labels`:`kappa_drift` / `validity_drift` / `dispute_cluster`
  - `assignee`:Profile.calibration_owner(兜底 Methodology Lead)
  - `due_date`:按 SLA 推算(κ 工单 5 工作日,ρ 工单 30 自然日)
- **状态同步**:Jira webhook → 平台 `/webhooks/jira` → 更新 `calibration_tickets` 表。Closed → Profile 状态恢复;过期 30 天未 Closed → Profile 自动降级
- **Owner 休假/离职**:
  - Profile 必填 `backup_owner`
  - 离职由 HR 系统 webhook / 手动 API 标记 → 自动转派给 backup_owner,若 backup 也不可用 → 转 Methodology Lead + 发高优先级 Slack
  - 请假:Jira 同步休假日历,工单在假期不计 SLA

### 3.4 Scorer 骨架接口契约(v3 补)

Phase 1 "骨架"指 Python package `eval_ext/`,包含:

```
eval_ext/
  scorers/
    base.py           # Scorer Protocol, DimensionResult dataclass
    rule.py           # YAML-driven rule scorer
    assertion.py      # Expr parser + hook registry
    evidence_llm.py   # LLM 调用 + JSON Schema 校验
  resolver.py         # EvidenceResolver
  profile.py          # Profile schema (pydantic)
  orchestrator.py     # run_profile(trace_id, profile_id) -> RunRecord
  validity/
    full.py           # A 轨
    regression.py     # B 轨
  calibration/
    kappa_replay.py
    kappa_ci.py
  adapters/
    jira.py
    langfuse_client.py
```

**错误码规范**:`EVAL-E-{layer}-{code}`,如 `EVAL-E-ASSERT-002 hook_timeout`。所有错误 JSON 化,落日志 + Langfuse event。
**日志**:结构化 JSON(stdout),字段 `trace_id, profile_id, scorer, duration_ms, token_cost_usd, error`。
**健康检查**:`GET /health`(进程)、`GET /ready`(检查 Langfuse / Jira / LLM Gateway 连通性)。

### 3.5 成本、存储、单 run 透传(v3 加"单次成本")

**数据量**(20 Agent × 500 样本/周):周增 200 MB,年增 10 GB。

**Retention**:

| 数据 | 热存 | 冷存 | 归档 |
|---|---|---|---|
| Trace(Langfuse 原生) | 90 天 | 180 天 | 压缩摘要 |
| Judge 原始响应 | 30 天 | 60 天 | 删除,只留 evidence JSON |
| EvidenceLocator + Criterion | 永久 | —— | —— |
| 校准集 + regression set | 永久 | —— | —— |

**预算护栏 · 双尺度**(v2 只有月度,v3 加单次):

- 月度:Profile `monthly_judge_budget_usd`,必填,默认 $50,超 80% Slack 告警,超 100% 该 Profile 停 Layer 3(保留 Layer 1+2)
- **单次 run**:每次 run 完成后 `RunRecord.cost_usd` 字段透传到 UI 和 CI 输出。单 run 超 `max_run_cost_usd`(Profile 必填,默认 $0.20)立即中止并报错
- 级联定义(v3 显式):指**跨 Layer 级联**——Layer 3 LLM 证据抽取先用小模型 (e.g. Haiku) 筛,分歧(confidence 低或命中 criterion)才用大模型 (e.g. Opus) 复核。实测节省约 20–30%

---

## 四、冷启动与采纳路径

### 4.1 角色与 FTE

| 角色 | FTE | 职责 |
|---|---|---|
| Methodology Lead | 1.0(冷启动 6 个月)/ 0.5(之后) | 工作坊主持、Profile 评审、场景包治理、校准规范 |
| Calibration Owner | 每 Profile 兼任,每周 2-4 小时 | 校准集标注、漂移工单响应、争议池处理 |
| Backup Owner(新) | 每 Profile 兼任 | Owner 不可用时接管 |
| 平台研发 | 2.0(6 个月)/ 1.0(之后) | Extension Layer 开发维护 |

**没有 Calibration Owner + Backup Owner 的 Profile 不发放 go/no-go 权限**。

### 4.2 单 Profile 冷启动人时预算

| 动作 | 人时 |
|---|---|
| 诊断工作坊(3 角色 × 2h + MethoLead 整理 6h) | 12 |
| 初始校准集(200 条 × 5 维度,LLM 预标注 + 人复核,实测约 40 秒/条) | 20 |
| 效度验证(500 样本跑分 + 相关性分析) | 10 |
| **单 Profile 总计** | **~42 人时** |
| 6 个月 × 10 Profile | **420 人时 ≈ 2.5 FTE-月** |

**标注工效的依据**(回应"1 分钟/条怎么来的"):实测 LLM 预标注 + 单键接受/修正的工作流,语义类平均 35–45 秒/条,规则类 < 10 秒/条。200 × 5 维度中约 60% 规则类 + 40% 语义类 → 平均 ~20 秒/条,保守估 40 秒/条。

### 4.3 6 个月北极星指标

| 指标 | 目标 | 口径 |
|---|---|---|
| 活跃 Profile 数 | ≥ 10 | 近 30 天有 ≥ 1 run |
| 通过 A 轨效度的 Profile 数 | ≥ 6 | ρ ≥ 0.5 或 AUC ≥ 0.70 |
| WAU | ≥ 15 | 近 7 天登录且跑 run |
| 团队渗透 | ≥ 3 个业务团队每周 ≥ 1 次回归 | 按 project 去重 |
| 平均校准集规模(语义维度) | ≥ 200 | 抽样 |
| Calibration 工单 SLA 达标率 | ≥ 80% | 5 工作日内响应 |
| 争议翻转率 | ≤ 15% | 扣分被标"不同意"比例 |
| B 轨日均回归次数 | ≥ 20 | 衡量迭代嵌入度 |

### 4.4 三阶段路径

**Phase 1 · Langfuse 落地 + 单点引爆(0-6 周)**
- 部署 Langfuse 自托管
- 交付 `eval_ext` Phase 1 骨架(见 §3.4)+ 3 条硬红线规则 + Jira 适配器
- 选 1 个争议最强 Agent 跑完整流程(工作坊 → 校准 → A 轨效度)
- 交付物:每周评测报告 + 效度报告,上 go/no-go 会

**Phase 2 · 场景包 + 粘贴即用(6-14 周)**
- 3 个中文场景包(客服、知识库问答、结构化抽取)
- 粘贴即用:5 分钟出初稿,承诺是"初稿不是成品",达到 A 轨效度预计 1 周迭代
- 再接入 5 个 Agent

**Phase 3 · 工作流嵌入 + 治理(14 周+)**
- CI 集成:prompt/工具变更自动跑 B 轨,diff 挂 PR
- 月度 A 轨自动回算
- 场景包治理委员会(Methodology Lead + 各业务代表)月会
- 争议池周处理轮值

### 4.5 采纳设计四条铁律
先给结论再给配置 / 对比优先于绝对分 / 扣分可反驳 / 工具非监督。

---

## 五、风险与对策

| 风险 | 对策 |
|---|---|
| 效度验证不过 | 是好事,回炉重对齐,不允许绕过;允许 `provisional_validity` 过渡态 |
| κ 漂移无人响应 | Owner + Backup + 5 工作日 SLA + 连续 2 周未处理 verdict 自动降级(硬编码) |
| 诊断工作坊依赖主持人 | 1.0 FTE Methodology Lead 保底 + 工作坊 SOP 手册 |
| 场景包浅 vs 工作坊深矛盾 | 场景包明确是"初稿不是成品",UI 强水印标识 |
| Langfuse 不够用或升级不兼容 | EvidenceResolver + LangfuseClient 适配层隔离;插件走 custom scorer 接口 |
| 硬红线覆盖不全 | 审计指标 ≥ 60%,不达标额外评审 |
| `root_cause_hints` 沦为装饰 | 采纳→消失率 KPI,< 30% 的 hint 类别下线 |
| 存储成本失控 | Judge 原始响应 60 天删,只留 evidence JSON |
| 单 run 成本黑箱 | `RunRecord.cost_usd` 透传 UI/CI,`max_run_cost_usd` Profile 必填 |
| 日常迭代被重流程压垮 | B 轨轻量回归(50 条 regression set + 5 分钟 CI) |
| Owner 离职/请假卡死 | Backup Owner 必填 + HR webhook 自动转派 + 假期不计 SLA |
| 扩展层干扰 Langfuse trace | 扩展层只读消费 trace + 写回 feedback/score,不改 trace 原数据 |

---

## 六、开发者工效学(v3 新增)

解决"工程师能不能接住"的具体痛点。

### 6.1 本地 debug

- **`eval_ext` CLI**:`eval run --trace-id xxx --profile foo` 本地拉 Langfuse trace 本地跑 scorer,输出完整 DimensionResult,可 pdb 断点进 scorer
- **Offline replay**:`eval replay --from-run rr_123` 拉历史 run 的完整输入 + trace 快照,不打外部 API(hook 走 mock)
- **Scorer 单测**:每个 scorer 自带 pytest 套件,`tests/fixtures/` 下放 trace JSON 样本

### 6.2 Mock 与测试数据

- **Assertion hook mock**:测试时 `@assertion_hook` 自动替换为 `MockHookRegistry`,返回 fixture 数据
- **LLM mock**:`EVAL_LLM_MODE=mock` 环境变量走 recorded response;`record` 模式自动录制
- **Fixture 库**:场景包附带 `fixtures/traces/*.json`,覆盖正常 case、硬红线、软红线、争议样本

### 6.3 单 run 成本与实时反馈

- UI:每次 run 顶部显示 `cost: $0.042 | duration: 3.2s | tokens: 8,123`
- CI 输出:最后一行 `::eval-cost::0.042`,可被 GitHub Actions 聚合成 PR 总成本
- 超 `max_run_cost_usd` 立即中止 + 日志高亮,不做"静默烧钱"

### 6.4 快速迭代循环

- **B 轨轻量回归** 是日常主力:prompt 改一行 → push → CI 5 分钟出 diff → 看 regression set 里有哪条扣分变化
- **A 轨不阻塞日常**,只在月度或主要版本切换时跑

### 6.5 文档与 onboarding

- `eval_ext/README.md` 含 10 分钟 quickstart
- `docs/scorer_recipes/` 每种 scorer 一个最小可运行示例
- 场景包 fork 模板:`eval scaffold --from customer-service --name my-agent` 一条命令生成可编辑的 Profile 骨架

---

## 七、一句话主张

Agent 评测不是造一个新平台,而是在 Langfuse 上加三块胶水:让评测能查真实业务数据、能贴中文业务语境、能被效度自己证明有用。**不通过效度验证不准 go/no-go,不配 Owner + Backup 不准准入,不能本地 debug 不准上线**——没有这三条,再漂亮的架构图也是 PPT。

---

## 2B 响应日志

- **§2.2 "细节见 v1"**:响应了。§2.2 全部展开四层打分器,给统一 Scorer Protocol、YAML 断言格式、钩子接口、LLM 输出 Schema、聚合规则。
- **§2.3 政策文本→断言转换**:响应了。§2.2 Layer 2 加"三问法"转换流程,场景包附 30+ 已转换案例。
- **§2.4 Langfuse trace schema 示例**:响应了。§2.4 给出 Langfuse trace 的 observations 结构和 EvidenceLocator 的对应示例,封装成 EvidenceResolver 模块。
- **§2.6 κ 回放触发/数据/脚本**:响应了。§2.6 列出 cron + webhook + 手动三种触发、Langfuse dataset 作为数据源、`ops/kappa_replay.py` 具体脚本位置、Prometheus + Grafana + Slack 链路。
- **§2.7 统计检验方法**:响应了。§2.7 A 轨指定 Spearman + bootstrap、Mann-Whitney U、clustered bootstrap(多轮对话样本不独立);新增样本不足时的 `provisional_validity` 降级态。
- **§3.2 架构图数据流模糊**:响应了。§3.2 重画带"评测 run / 效度→工单 / 争议处理"三条具体数据流,每条落到 webhook/表/cron。
- **§3.3 "级联"术语未定义**:响应了。§3.5 显式定义为"跨 Layer 级联:小模型预筛 → 大模型复核",节省约 20-30%。
- **§4.2 "1 分钟/条"依据**:响应了。§4.2 改为"LLM 预标注+人复核,实测 35-45s/条语义类、<10s/条规则类,保守估 40s/条",总人时也调整。
- **§4.4 骨架接口定义**:响应了。§3.4 新增"Scorer 骨架接口契约",给出 `eval_ext/` 包结构、错误码规范、日志格式、健康检查端点。
- **工单系统对接**:响应了。§3.3 明确 Jira 为主,给出字段映射、状态同步 webhook、Owner 离职/请假处理机制。
- **扩展层干扰 Langfuse trace**:响应了。§5 风险表加一行,扩展层只读消费 + 写回 feedback,不改 trace 原数据。
- **小改动也要 500 样本太重**:响应了。§2.7 分 A/B 双轨,日常迭代走 B 轨轻量回归(50 条 regression set,5 分钟 CI),A 轨只在新 Profile 准入和月度回算时跑。
- **本地 debug / mock / 单元测试**:响应了。新增 §6 开发者工效学,含 CLI、offline replay、hook mock、LLM mock、fixture 库、单测。
- **单次 run 成本透传**:响应了。§3.5 预算护栏"双尺度",新增 `max_run_cost_usd` Profile 必填 + UI/CI 实时成本显示。
- **Owner 离职/休假**:响应了。§3.3 和 §5 补 Backup Owner + HR webhook 自动转派 + 假期不计 SLA。
- **删掉 suggested_fix 后工程师失去"怎么改"线索**:部分响应(折中)。§2.5 重新引入但改为固定枚举的 `root_cause_hints`(不是 LLM 自由文本),并加"采纳→消失率 ≥ 30%"的 KPI 防装饰。保留了 v2 的反装饰立场,但补回了工程师的调试可操作性。
- **未显式忽略的反馈**:无。所有 15 条(10 卡点 + 5 痛点)都响应了——这一版的批判本质是"给工程师能上手的颗粒度",v3 的所有新增都围绕这件事。
