# 未镜 The Other Path · 技术规范 Tech Spec

**文档基线**:r2-idea-v5(idea 真源,已锁)+ PRD-4(产品需求真源,已锁)
**文档目的**:把 PRD-4 全部章节展开为 Claude Code agent teams 可并行执行的工程规范
**版本**:Tech Spec v1.0
**读者假设**:Spawn 出的 teammate——拥有完整工程能力,但不知道产品上下文。Tech Spec 要让它在不打扰 lead 的情况下完成 80% 的工作。

---

## 0. 阅读纪律

1. **idea 真源是 r2-idea-v5,产品真源是 PRD-4**——Tech Spec 是工程展开,不是产品再创作。任何"我觉得这样产品更好"的冲动都要 stop,先回去读 PRD-4 §15(锁定纪律)。
2. **§14 关于 Claude Code agent teams 的最佳实践基于官方文档** —— 与训练记忆冲突时以官方文档为准。本 Tech Spec 中标注 *[best-practice 推理,待跑起来后调整]* 的部分是没有官方明文支持的细节决策。
3. **§15 关键设计决策的"为什么"是 teammate 防漂移的最后护栏**——遇到设计冲突先读这一节,再决定要不要找 lead 介入。
4. **PRD-4 锁定的纪律不能动**——汇总在 §14.6"不能动清单",任何 implementation 触及这些都必须 escalate 给 Wenbo。

---

## 1. 整体架构 + 模块拆分

### 1.1 架构图(文字描述)

```
┌──────────────────────────────────────────────────────┐
│                  浏览器(Web 端)                       │
│  ┌────────────────────────────────────────────────┐  │
│  │ 前端 UI 层(浅紫雾面 + 镜子语言 + 双语 i18n)     │  │
│  │   · 落地页 / Onboarding / 问卷 / 决策输入      │  │
│  │   · 推演各 Step / 开场镜子 / 输出页 / 思考流   │  │
│  │   · 反馈表单 / 一键反馈 / 语言切换             │  │
│  └────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────┐  │
│  │ 客户端状态层(localStorage + sessionStorage)    │  │
│  │   · mirror.lang(语言)                          │  │
│  │   · mirror.draft.{decision_id}(草稿缓存)       │  │
│  │   · mirror.user.last_session                   │  │
│  └────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────┘
                          │
                          │ HTTPS(Cloudflare 边缘)
                          ▼
┌──────────────────────────────────────────────────────┐
│         应用层(HF Space 或独立 VPS)                   │
│  ┌────────────────────────────────────────────────┐  │
│  │ API 网关 / 路由 / 鉴权                          │  │
│  └────────────────────────────────────────────────┘  │
│  ┌──────────────┬──────────────┬──────────────┐     │
│  │ 用户服务模块  │ 推演模块      │ 反馈模块      │     │
│  │ (M-User)    │ (M-Inference) │ (M-Feedback) │     │
│  │             │               │               │     │
│  │ · 注册/登录  │ · 六步流水线  │ · 表单收集    │     │
│  │ · 问卷       │ · 镜子模块    │ · 一键反馈   │     │
│  │ · 画像       │ · 多路径生成  │ · 自动 alert │     │
│  │ · ToS/隐私  │ · 一致性审查  │              │     │
│  └──────────────┴──────────────┴──────────────┘     │
│  ┌──────────────┬──────────────┬──────────────┐     │
│  │ 思考流模块   │ 决策回访模块  │ AI 调用层     │     │
│  │(M-Stream)  │(M-FollowUp)  │(M-AI)        │     │
│  │             │               │               │     │
│  │ · 卡片管理   │ · 90 天 push │ · 主备模型路由│     │
│  │ · 快速捕捉   │ · 2 题问卷    │ · prompt 模板│     │
│  │ · 衔接逻辑   │ · 聚合反馈   │ · 输出过滤    │     │
│  └──────────────┴──────────────┴──────────────┘     │
└──────────────────────────────────────────────────────┘
                          │
            ┌─────────────┼─────────────┐
            ▼             ▼             ▼
    ┌──────────────┐ ┌──────────┐ ┌──────────────┐
    │ Postgres     │ │ 模型 API │ │ 邮件服务     │
    │(Supabase/    │ │ (Deep    │ │(Resend/      │
    │  Neon)       │ │  Seek    │ │  Postmark)  │
    │              │ │  /Qwen   │ │              │
    │ · users      │ │  /Doubao │ │ · 决策回访   │
    │ · profiles   │ │  /Kimi)  │ │ · 反馈通知   │
    │ · decisions  │ └──────────┘ └──────────────┘
    │ · runs       │
    │ · mirror_runs│ ┌──────────┐ ┌──────────────┐
    │ · streams    │ │ 文件存储 │ │ 支付         │
    │ · followups  │ │(Supabase│ │(Stripe/      │
    │ · feedbacks  │ │  Storage │ │ Paddle/      │
    └──────────────┘ │  / R2)  │ │ 支付宝海外/  │
                     │ · 22 张 │ │ 微信国际)    │
                     │  塔罗图 │ │              │
                     └──────────┘ └──────────────┘
```

### 1.2 模块拆分(M-Modules)

| 模块代号 | 名称 | 职责 | 主要 PRD-4 引用 |
|---|---|---|---|
| **M-User** | 用户服务 | 注册 / 登录 / 问卷 / 画像存储 / ToS 同意 / 18+ 校验 | §3.1 §8.4 §8.5 |
| **M-Inference** | 推演核心 | 六步流水线 / 镜子模块 / 多路径生成 / 双层一致性审查 | §3.3 §3.4 §3.5 |
| **M-AI** | AI 调用层 | 主备模型路由 / prompt 模板 / 输出过滤 / token 预算 | §3.3 §10.1 §13.1 |
| **M-Stream** | 思考流 | 卡片时序管理 / 快速捕捉 / 推演衔接 | §3.6 §5.6 |
| **M-FollowUp** | 决策回访 | 90 天 push / 2 题问卷 / 聚合反馈 / 匿名故事勾选 | §6.3 |
| **M-Feedback** | 反馈系统 | 表单 / 一键 emoji / 自动 alert | §14 |
| **M-i18n** | 国际化 | Accept-Language 解析 / localStorage / 跨设备同步 | §12 |
| **M-Visual** | 视觉规范 | 颜色 token / 字体加载 / 镜子语言 / 动效 | §11 |
| **M-Error** | 错误降级 | voice 纪律 / fallback / 本地缓存 | §13 |
| **M-Pay** | 支付 | 三档定价 / 决策包 / 24 小时免重支付 / 退款 | §7 §10.2 |
| **M-Legal** | 合规 | GDPR / CCPA / 数据导出删除 / 18+ 校验 | §8.5 §8.4 |

模块边界纪律:**模块间只通过 API 契约交互(§9)**,不共享内存状态。这条是 agent teams 并行开发的硬约束——两个 teammate 同时改两个模块时不会冲突。

---

## 2. 技术栈选择(分两阶段)

### 2.1 HF Space 阶段(MVP / Wenbo 自用 + 5-10 种子用户)

**目标**:**1-2 周内跑通核心闭环**,验证 idea 在真用户身上的反应。

| 层 | 选择 | 理由 |
|---|---|---|
| 平台 | **Hugging Face Spaces**(Docker SDK,非 Gradio default) | 允许自定义任意技术栈;免费 tier 足够 5-10 用户用 |
| 后端框架 | **FastAPI** + **Pydantic** | Python 生态(模型调用 SDK 在 Python 里最齐全)+ 异步 + 类型安全;比 Gradio/Streamlit 灵活,比 Django 轻 |
| 前端框架 | **Vanilla HTML + HTMX + Alpine.js** | HF Space 阶段不上 React/Vue 框架,降低部署摩擦;HTMX 让 server-rendered 体验也能有 SPA 感觉 |
| 模板引擎 | **Jinja2**(FastAPI 自带) | 服务端渲染,SEO 友好,语言切换在服务端处理 |
| CSS | **TailwindCSS**(CDN 模式) | HF Space 阶段不做 build pipeline,CDN 直接用 |
| 状态 | **localStorage**(客户端)+ **PostgreSQL**(服务端) | 草稿 / 语言 / 用户偏好用 localStorage;持久数据用外部 DB(HF Space 本身存储 ephemeral) |
| 数据库 | **Supabase Postgres**(免费 tier 500MB) | 外部托管,HF Space 重启不丢数据;Supabase 自带 Auth,但 v1 不用,只用 DB |
| 鉴权 | **简易 JWT + bcrypt**(自实现) | HF Space 阶段不依赖 Supabase Auth(避免锁定);v1 只需邮箱注册 + 登录 |
| 模型 API | **DeepSeek API** 主 + **Qwen API** 备 | §4.4 详述 |
| 邮件 | **Resend**(免费 tier 100/day) | 决策回访 push 90 天后,首批 100 用户每天最多 3-4 封,够用 |
| CDN / 静态资源 | HF Space 自带 + **jsDelivr**(字体 / 库) | 不需要独立 CDN |
| 监控 | **简易 print logging** + **Sentry**(免费 tier) | 错误监控,不上 OpenTelemetry |

**HF Space 阶段不做的事**:
- 不做 SSR 复杂应用框架(Next.js / SvelteKit) — 推迟到独立部署;
- 不做 build pipeline — Tailwind CDN + 手写 JS;
- 不做容器编排 / k8s — HF Space 自动管理;
- 不做完整 CI/CD — 推 Git → HF Space auto-deploy 即可。

### 2.2 独立部署阶段(种子用户验证后,迁移到独立域名)

**触发条件**:HF Space 阶段达到任意一个:
- 用户 ≥ 30 个,HF Space 免费 tier 限流;
- 需要 SEO 流量(HF Space URL 不利 SEO);
- 需要更复杂的前端交互(镜子涟漪 / 动效)难以在 vanilla 实现。

**目标**:**性能 + SEO + 可扩展性,但仍然是 indie 规模**。

| 层 | 选择 | 理由 |
|---|---|---|
| 前端框架 | **Next.js 14**(App Router) | SSR + SSG + 客户端交互一站式;React 生态,agent team 容易找参考;i18n routing 原生支持 |
| 后端 | **Next.js API Routes** + **FastAPI 微服务**(AI 调用层独立) | 主流量走 Next.js,模型调用走 FastAPI(Python SDK 完整) |
| 部署 | 前端 **Vercel**(免费 tier 100GB)+ 后端 **Railway / Fly.io**(海外 VPS,~$5/月) | Vercel 全球 CDN 自动;FastAPI 部署到 Railway 简单 |
| 数据库 | **Supabase Postgres**(从 HF Space 阶段直接迁移,无缝)| 不换 |
| 鉴权 | **NextAuth.js**(替换 v1 自实现 JWT) | 标准化,支持邮箱 / Google / Apple OAuth |
| 邮件 | **Resend**(从 HF Space 阶段继续) | 不换 |
| CDN / 域名 | **Cloudflare**(免费 tier) | DDoS 保护 + 全球 CDN + 不主动获取大陆流量(Cloudflare 大陆访问慢,自然限速) |
| 文件存储 | **Cloudflare R2** 或 **Supabase Storage** | 22 张塔罗图静态资产 + 用户头像(若有) |
| 支付 | **Stripe**(信用卡 / Apple Pay)+ **Paddle**(全球税务)+ **支付宝海外**+ **微信支付国际** | §7 |
| 监控 | **Sentry** + **Vercel Analytics** | 错误 + 性能 |
| 域名 | 海外注册商(Namecheap / Porkbun),`.app` 或 `.com` | 不在大陆注册 |
| 服务器位置 | 海外(美国 / 新加坡 / 日本) | 承接 PRD-4 §8 不进大陆 |

**独立部署阶段技术栈选择的为什么**:
- **Next.js 而非 SvelteKit**:agent teams 对 React/Next.js 文档训练数据更多,生成质量更高;且 Next.js i18n 原生支持(对 §12 国际化重要);
- **保留 Supabase**:从 HF Space 到独立部署不换 DB,数据迁移成本为零(Supabase 是托管 Postgres,任何应用都能连);
- **不上 Kubernetes**:indie 规模,Vercel + Railway 已够;
- **不上 Redis/缓存**:v1 不需要;模型调用结果用 Postgres JSON 字段缓存即可。

---

## 3. 核心数据模型

所有数据模型用 PostgreSQL,字段名 snake_case,主键 UUID(`gen_random_uuid()`)。

### 3.1 users

```sql
CREATE TABLE users (
  user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email TEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,  -- bcrypt
  lang_pref TEXT NOT NULL DEFAULT 'zh',  -- 'zh' | 'en'
  agreed_tos_at TIMESTAMP NOT NULL,
  agreed_age_18plus BOOLEAN NOT NULL DEFAULT FALSE,
  created_at TIMESTAMP NOT NULL DEFAULT NOW(),
  deleted_at TIMESTAMP NULL  -- soft delete; GDPR right to be forgotten 触发硬删除走 §13.1 流程
);
```

### 3.2 user_profiles(Create Yourself 问卷四层)

```sql
CREATE TABLE user_profiles (
  user_id UUID PRIMARY KEY REFERENCES users(user_id) ON DELETE CASCADE,
  -- 第一层 处境锚点
  situation_anchors JSONB NOT NULL,  
    -- {age_range, city_tier, profession_category, marital_status, financial_buffer_months}
  -- 第二层 价值张力
  value_priorities JSONB,  
    -- {free_vs_stable: 0-3, achievement_vs_relationship: 0-3, ...}
  -- 第三层 风险与时间偏好(深化阶段填,可空)
  risk_profile JSONB,  
    -- {risk_aversion_score, time_discount_score}
  -- 第四层 偏差画像(深化阶段填,可空)
  bias_profile JSONB,  
    -- {anchoring: 0-1, availability: 0-1, base_rate_neglect: 0-1, ...}
  profile_summary TEXT,  -- AI 生成的"自我画像速写"
  completed_basic_at TIMESTAMP,
  completed_deep_at TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);
```

### 3.3 decisions(决策记录)

```sql
CREATE TABLE decisions (
  decision_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
  original_prompt TEXT NOT NULL,  -- 用户原始输入
  reframed_question TEXT,  -- AI 重构的探索式提问
  decision_type TEXT,  -- 'one_time' | 'reversible' | 'chained'
  door_type TEXT,  -- 'two_door' | 'one_door'
  psychological_state TEXT,  -- 'rumination' | 'post_tentative' | 'unidentified'
  recommended_form TEXT,  -- 'basic' | 'light' | 'full'
  status TEXT NOT NULL DEFAULT 'active',  -- 'active' | 'archived'
  created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_decisions_user_id ON decisions(user_id, created_at DESC);
```

### 3.4 inference_runs(推演中间产物)

```sql
CREATE TABLE inference_runs (
  run_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  decision_id UUID NOT NULL REFERENCES decisions(decision_id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
  form_type TEXT NOT NULL,  -- 'basic' | 'light' | 'full'
  
  -- 六步流水线
  step1_framing JSONB,  -- {decision_type, door_type, framing_text}
  step2_options JSONB,  -- [{option_id, title, description}]
  step3_uncertainties JSONB,  -- {option_id: [{variable, controllable, mirror_derived: bool}]}
  step4_likelihoods JSONB,  -- {option_id: {variable: {tier: '非常可能'|...|'几乎不会', probability_range: [0.35, 0.55]}}}
  step5_bias_audit JSONB,  -- {bias_type, hypothesis_text, user_response: 'agree'|'disagree'|'agree_with_addition', user_addition?}
  step6_premortem TEXT,  -- 用户自填
  
  -- 多路径画像
  multipath_short_term JSONB,  -- {option_id: [{moment_index, time_anchor, content}]}
  multipath_medium_term JSONB,  -- {option_id: {baseline, upside, downside, prob_bands}}
  multipath_long_term JSONB,  -- {option_id: {archetype_name, plain_translation, variance_shape}}
  comparison_table JSONB,  -- [{utility_dimension, option_scores}]
  tendency_conclusion TEXT,
  undecided_acknowledgment TEXT,  -- §3.5.4 "未决定也可以"承接
  
  -- 镜子层关联
  mirror_run_id UUID REFERENCES mirror_runs(mirror_run_id),
  
  -- 一致性审查记录
  consistency_check_passes INT DEFAULT 0,
  consistency_check_log JSONB,  -- 每次重写的记录
  
  started_at TIMESTAMP NOT NULL DEFAULT NOW(),
  completed_at TIMESTAMP,
  
  -- 错误降级标记
  archetype_skipped BOOLEAN DEFAULT FALSE  -- §13.1 双层一致性 fail 后跳过原型层
);

CREATE INDEX idx_runs_decision_id ON inference_runs(decision_id, started_at DESC);
```

### 3.5 mirror_runs(开场镜子)

```sql
CREATE TABLE mirror_runs (
  mirror_run_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  decision_id UUID NOT NULL REFERENCES decisions(decision_id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
  card_drawn INT NOT NULL,  -- 0-21,大阿尔卡纳编号
  card_selection_method TEXT NOT NULL,  -- 'auto_random' | 'user_chose'
  user_projection TEXT NOT NULL,  -- 用户写的 1-3 句
  ai_distillation_draft TEXT NOT NULL,  -- AI 凝练草案
  user_choice TEXT NOT NULL,  -- 'confirm' | 'edit' | 'remove'
  final_distillation TEXT,  -- 用户编辑后的最终版本(若 user_choice=edit)
  created_at TIMESTAMP NOT NULL DEFAULT NOW()
);
```

### 3.6 thought_streams(思考流)

```sql
CREATE TABLE thought_streams (
  entry_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  decision_id UUID NOT NULL REFERENCES decisions(decision_id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
  entry_type TEXT NOT NULL,  -- 'quick_capture' | 'inference_summary' | 'mirror_run' | 'follow_up'
  ref_id UUID,  -- 关联的 run_id / mirror_run_id / followup_id
  content JSONB NOT NULL,
  incorporated_into_run_id UUID,  -- 此卡片被纳入哪次推演
  created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_streams_decision ON thought_streams(decision_id, created_at DESC);
```

### 3.7 quick_captures(快速捕捉)

```sql
CREATE TABLE quick_captures (
  capture_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  decision_id UUID NOT NULL REFERENCES decisions(decision_id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
  content TEXT NOT NULL,
  incorporated_into_run_id UUID,  -- NULL 表示未被纳入推演
  created_at TIMESTAMP NOT NULL DEFAULT NOW()
);
```

### 3.8 decision_followups(决策回访)

```sql
CREATE TABLE decision_followups (
  followup_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  decision_id UUID NOT NULL REFERENCES decisions(decision_id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
  run_id UUID NOT NULL REFERENCES inference_runs(run_id),  -- 哪次推演触发的回访
  scheduled_at TIMESTAMP NOT NULL,  -- 推演完成 + 90 天
  pushed_at TIMESTAMP,
  completed_at TIMESTAMP,
  choice TEXT,  -- 'A' | 'B' | 'C' | 'still_in_progress'
  feeling_score INT,  -- 1-10
  feeling_emoji TEXT,  -- '😌' | '😐' | '😣'
  agreed_anonymous_stories BOOLEAN DEFAULT FALSE,
  reward_granted BOOLEAN DEFAULT FALSE  -- 完成回访赠送的免费推演已发放
);

CREATE INDEX idx_followups_pending ON decision_followups(scheduled_at) WHERE pushed_at IS NULL;
```

### 3.9 feedbacks(反馈数据)

```sql
CREATE TABLE feedbacks (
  feedback_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(user_id) ON DELETE SET NULL,  -- 允许匿名反馈
  feedback_type TEXT NOT NULL,  -- 'form' | 'one_click'
  -- form 字段
  category TEXT,  -- 'bug' | 'feature' | 'content' | 'other'
  content TEXT,
  email TEXT,  -- 用户额外提供的邮箱(可与 user.email 不同)
  allow_contact BOOLEAN DEFAULT TRUE,
  -- one_click 字段
  sentiment TEXT,  -- '😊' | '😐' | '☹️'
  related_run_id UUID REFERENCES inference_runs(run_id),
  related_step TEXT,  -- 'mirror_distillation' | 'step5_bias' | 'completion' | ...
  -- 通用
  user_agent TEXT,
  created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_feedbacks_one_click_alert ON feedbacks(related_step, sentiment, created_at)
  WHERE feedback_type = 'one_click';
```

### 3.10 payments(支付)

```sql
CREATE TABLE payments (
  payment_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(user_id),
  product_type TEXT NOT NULL,  -- 'light_run' | 'full_run' | 'decision_pack' | 'monthly_sub' | 'yearly_sub'
  amount_cny INT,  -- 分
  amount_usd INT,  -- cents
  currency TEXT NOT NULL,
  payment_method TEXT NOT NULL,  -- 'stripe' | 'paddle' | 'alipay_intl' | 'wechat_intl'
  payment_status TEXT NOT NULL,  -- 'pending' | 'succeeded' | 'failed' | 'refunded'
  external_charge_id TEXT,  -- Stripe / Paddle 的 charge ID
  decision_id UUID REFERENCES decisions(decision_id),  -- 决策包关联具体决策
  bundle_remaining INT,  -- 决策包剩余次数
  created_at TIMESTAMP NOT NULL DEFAULT NOW()
);
```

### 3.11 user_entitlements(用户权益,记录免费额度 + 决策包余量)

```sql
CREATE TABLE user_entitlements (
  user_id UUID PRIMARY KEY REFERENCES users(user_id) ON DELETE CASCADE,
  free_basic_remaining INT DEFAULT 999999,  -- 永久免费,不计减
  free_light_remaining INT DEFAULT 2,
  free_full_remaining INT DEFAULT 3,
  active_subscription_type TEXT,  -- NULL | 'monthly' | 'yearly'
  subscription_expires_at TIMESTAMP,
  monthly_full_runs_used INT DEFAULT 0,  -- 月度订阅周期内已用
  monthly_period_start TIMESTAMP,
  -- 决策包关联在 payments 表 + 24 小时免重支付窗口
  last_paid_decision_id UUID,
  last_paid_at TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);
```

**24 小时免重支付窗口逻辑**(对应 PRD-4 §7.2):
- 用户付费完成一次推演后,`last_paid_decision_id` + `last_paid_at` 更新;
- 24 小时内,同一 `decision_id` 再次发起推演:不重新走支付,但仍单次扣费(后台异步)。

---

## 4. AI 调用层设计(M-AI 模块)

### 4.1 整体架构

```
┌─────────────────────────────────────────────────┐
│           上游模块(M-Inference 等)              │
│           调用 AI 调用层的统一接口                │
└─────────────────────┬───────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────┐
│   M-AI 调用层                                    │
│   ┌───────────────────────────────────────┐    │
│   │ prompt 模板库(每个 step 一个模板)     │    │
│   │ + 模板变量填充                          │    │
│   └───────────────────────────────────────┘    │
│   ┌───────────────────────────────────────┐    │
│   │ 模型路由                                │    │
│   │ · 主模型:DeepSeek-V3(便宜)            │    │
│   │ · 备模型 1:Qwen-Max(细腻文笔)         │    │
│   │ · 备模型 2:Doubao-Pro                  │    │
│   │ · 各 step 配置不同主备                  │    │
│   └───────────────────────────────────────┘    │
│   ┌───────────────────────────────────────┐    │
│   │ 重试 + 超时 + 限流处理                  │    │
│   └───────────────────────────────────────┘    │
│   ┌───────────────────────────────────────┐    │
│   │ 输出过滤层(关键词过滤 + 重写)         │    │
│   └───────────────────────────────────────┘    │
│   ┌───────────────────────────────────────┐    │
│   │ token 使用记账(每次调用记 token + 成本)│    │
│   └───────────────────────────────────────┘    │
└─────────────────────────────────────────────────┘
```

### 4.2 Prompt 模板设计原则

每个 prompt 模板必须包含 4 段:

```
1. SYSTEM ROLE 定义(产品身份 + 纪律护栏)
2. TASK 任务描述
3. CONTEXT 上下文(用户画像 + 决策 + 历史步骤)
4. OUTPUT FORMAT 输出格式约束(JSON schema 优先)
```

**镜子层 prompt 模板(完整,严格,作为参考样板)**:

```
SYSTEM ROLE:
你是未镜(The Other Path)产品的开场反思引导者。你的任务是基于用户对一张塔罗牌的自由投射,凝练他自己点出的核心担忧、期望或恐惧。

严格规则:
1. 主语永远是用户。开头必须是"你刚才点出了..." / "你看到这张牌时说的是..." 不可以是"这张牌意味着..." / "这张牌预示..."
2. 输出长度控制在 50-80 字。
3. 凝练后必须建议作为 Step 3 的一个不确定性变量(给出建议变量名)。
4. 不评价用户的投射(不说"你的洞察很深刻"等)。
5. 输出必须以 JSON 返回:{"distillation_text": "...", "suggested_variable_name": "..."}
6. 任何"意味着 / 预示 / 注定 / 命中 / 命运 / 揭示 / 暗示 / 决定了"等词出现 → 你的输出会被自动 reject 重生成。

TASK:
基于用户的塔罗投射,凝练 1 段 50-80 字的"开场镜子"。

CONTEXT:
用户画像速写:{user_profile_summary}
正在纠结的决策:{decision_reframed_question}
用户抽到的牌:{card_name}
牌的传统象征词:{card_symbols}
用户的投射:{user_projection_text}

OUTPUT FORMAT:
{
  "distillation_text": "你刚才点出了...",  // 50-80 字
  "suggested_variable_name": "继续留下的隐性成本"  // 5-12 字
}
```

**所有 step 的 prompt 模板必须遵循同样的结构**——见 §4.3。

### 4.3 各 Step 的 prompt 模板(简表,完整版本由 teammate 起草并入 codebase)

| Step | 任务 | 输出格式 | 主模型 | 备模型 |
|---|---|---|---|---|
| Decision 重构 | 把"该不该 X"改写为探索式提问 + 心理状态识别 | JSON {reframed_question, psychological_state} | DeepSeek | Qwen |
| 镜子凝练 | 用户投射 → 50-80 字凝练 + 变量建议 | JSON {distillation_text, suggested_variable} | **Qwen-Max**(细腻文笔) | Doubao |
| Step 1 决策框定 | 决策类型 + 双向门 + 门槛命名 | JSON | DeepSeek | Qwen |
| Step 2 选项展开 | ≥3 选项(含延迟决定) | JSON [option_1, option_2, ..., option_delay] | DeepSeek | Qwen |
| Step 3 不确定性识别 | 每选项 2-3 变量 + 可控/不可控 + 吸纳镜子内容 | JSON | DeepSeek | Qwen |
| Step 5 偏差审计 | 假设语气 + 用户可驳回 | JSON {bias_type, hypothesis_text} | DeepSeek | Qwen |
| 多路径短期 | 三个具体瞬间(时间锚点) | JSON [{moment_index, time_anchor, content}] | **Qwen-Max** | Doubao |
| 多路径中期 | 概率带 + 数据来源 | JSON {baseline, upside, downside} | DeepSeek | Qwen |
| 原型命名 + 长期故事核 + 大白话翻译 | 故事核 + "要面对的事"(不是"感受") | JSON {archetype_name, story_core, plain_translation} | **Qwen-Max** | Doubao |
| 倾向性结论 | 期望效用最高路径 + 边界条件 + 未决定承接 | JSON | DeepSeek | Qwen |

**Step 4 不调用 AI**——5 档可能性 + 滑块由前端实现,后端只存用户档位。

### 4.4 模型选型与降级策略

#### 4.4.1 模型选型实测要求

teammate 在 dev 阶段必须做以下对比测试,实测后选定:

| 测试用例 | 主候选 | 备候选 | 验收标准 |
|---|---|---|---|
| 镜子凝练 | Qwen-Max | DeepSeek-V3, Doubao-Pro, Kimi | 主语永远是用户;输出在 50-80 字;不出现禁用词;细腻度评分(Wenbo + 2 种子用户三人盲评) |
| 短期三个瞬间生成 | Qwen-Max | DeepSeek-V3 | 具象 + 时间锚点准确;"被发紧"程度(同盲评) |
| 原型大白话翻译 | Qwen-Max | DeepSeek-V3 | "要面对的事"列表准确,不漂回"感受是" |
| 决策框定 + 选项展开 + 偏差审计 | DeepSeek-V3(便宜) | Qwen-Plus | 结构化输出稳定;JSON 解析失败率 < 2% |
| 多路径中期 | DeepSeek-V3 | Qwen-Plus | 概率带数字稳定;数据来源标注完整 |

实测样本量:每个测试用例 30 个真实决策样本(可用历史数据合成或 Wenbo 自己的纠结)。

#### 4.4.2 主备模型 fallback 链(对应 PRD-4 §13.1 "AI 调用失败")

```
主模型调用 → 60s 超时
  ├─ 成功 → 返回结果
  ├─ 超时 → 切换备模型 1(同 step) → 60s 超时
  │       ├─ 成功 → 返回结果(记录主模型超时)
  │       └─ 超时 → 切换备模型 2 → 60s 超时
  │              ├─ 成功 → 返回结果
  │              └─ 超时 → 触发 PRD-4 §13.1 错误文案"今天我这边不太顺手..."
  └─ API error → 立即切换备模型 1(不等 60s)
```

#### 4.4.3 限流处理

- 每个模型 API 设置 RPS 上限(根据各 vendor 配额);
- 超过 RPS 时:本地排队 + 用户面显示"我跟不上了——慢一点,我们一起想"(PRD-4 §13.1);
- 队列满时:返回 429,前端显示同上文案 + 可重试按钮。

### 4.5 输出过滤层(关键词过滤 + 重写)

#### 4.5.1 禁用词清单的工程实现

PRD-4 §3.3.3 已列禁用词清单。Tech Spec 实现:

```python
# zh_blacklist.txt (一行一个词,正则字符 escape)
意味着
预示
注定
命中
命运
揭示
暗示
决定了
预言
宿命
天注定
必将
定将
终将
命运指引
你将会
你会成为
算出
算到
推算出
命相
面相
被迫
必须
强制
要求

# en_blacklist.txt
\bmeans\b
\bpredicts\b
\breveals\b
\bdestined\b
\bfate\b
\bprophecy\b
\bforetells\b
\bforetold\b
\bordained\b
\bwritten in the stars\b
\bforced to\b
\bmust\b
\brequired to\b
\bhave to\b
```

#### 4.5.2 过滤实现伪代码

```python
def filter_output(text: str, lang: str) -> tuple[str, bool]:
    """返回 (过滤后文本, 是否触发了重写)"""
    blacklist = ZH_BLACKLIST if lang == 'zh' else EN_BLACKLIST
    for word in blacklist:
        if re.search(word, text):
            return text, True  # 触发重写
    return text, False

def call_llm_with_filter(prompt: str, max_retry: int = 2) -> str:
    for attempt in range(max_retry + 1):
        output = call_llm(prompt)
        cleaned, needs_rewrite = filter_output(output, get_lang())
        if not needs_rewrite:
            return cleaned
        # 重写时给 LLM 更严格的提示
        prompt = prompt + f"\n\n你上次的输出包含了禁用词,请重新生成,严格遵守 SYSTEM ROLE 的禁用规则。"
    # 2 次重写仍失败 → 返回 fallback
    return get_fallback_for_step(step_name)
```

#### 4.5.3 fallback 模板(每个 step 一份)

| Step | Fallback 文案(中文) |
|---|---|
| 镜子凝练 | "你刚才说的我听到了——这是你自己点出的关切,我们记下来,放进推演里看看。"(无具体变量名建议时,Step 3 跳过该输入) |
| 偏差审计 | (跳过这一步,直接进 Step 6) |
| 原型 + 故事核 | (走 PRD-4 §13.1 "故事核没有顺利做出来,我先把结构化分析给你") |
| 多路径长期 | "这条路的形状,我们这次没有完整看清——你可以让我重新尝试,或者只看短期和中期部分先做判断。" |

### 4.6 双层一致性审查的工程实现(PRD-4 §5.4 + §11.5 方案 B)

#### 4.6.1 模板化对照表

```python
# archetype_consistency_rules.json
{
  "探索者的远行": {
    "expected_variance_shape": "high",
    "expected_core_themes": ["承担不确定性", "学习者", "重新做"],
    "expected_path_pattern": ["上行高 + 下行低", "学习曲线陡"],
    "structural_signals": {
      "min_uncertainty_count": 3,
      "must_have_variable_categories": ["现金流", "技能习得"]
    }
  },
  "照顾者的深耕": {
    "expected_variance_shape": "low",
    "expected_core_themes": ["责任累积", "稳定深化", "替代性低"],
    "expected_path_pattern": ["低方差 + 中位数缓慢上行"],
    "structural_signals": {
      "min_uncertainty_count": 2,
      "must_have_variable_categories": ["关系压力", "时间机会成本"]
    }
  },
  // ... 8-12 个原型
}
```

#### 4.6.2 一致性审查 4 步流程(对应 PRD-4 §5.4)

```python
def consistency_check(structural: dict, archetypal: dict) -> tuple[bool, str]:
    archetype_name = archetypal['archetype_name']
    rules = ARCHETYPE_RULES.get(archetype_name)
    if not rules:
        return False, f"未知原型: {archetype_name}"
    
    # Step 1: 比对方差形状
    if structural['variance_shape'] != rules['expected_variance_shape']:
        return False, f"方差不匹配: 结构层 {structural['variance_shape']}, 原型层期望 {rules['expected_variance_shape']}"
    
    # Step 2: 比对核心课题关键词
    archetype_themes = archetypal['core_themes']  # 从原型层提取
    overlap = set(archetype_themes) & set(rules['expected_core_themes'])
    if len(overlap) < 1:
        return False, "核心课题与原型不匹配"
    
    # Step 3: 比对结构信号
    if len(structural['uncertainties']) < rules['structural_signals']['min_uncertainty_count']:
        return False, "不确定性变量数少于原型期望"
    
    # Step 4: 通过
    return True, "OK"

def run_with_consistency(decision_context: dict) -> dict:
    structural = generate_structural_layer(decision_context)
    
    for attempt in range(3):  # 最多 2 次重写
        archetypal = generate_archetypal_layer(structural, decision_context)
        passed, reason = consistency_check(structural, archetypal)
        if passed:
            return {'structural': structural, 'archetypal': archetypal, 'passes': attempt}
        # 重写时把 reason 喂给 LLM 作为约束
        decision_context['rewrite_reason'] = reason
    
    # 3 次仍失败 → 触发 PRD-4 §13.1 跳过原型层
    log_consistency_failure(decision_context)
    return {
      'structural': structural,
      'archetypal': None,
      'archetype_skipped': True,
      'fallback_message': "这个推演的'故事核'部分今天没有顺利做出来,我先把结构化分析给你..."
    }
```

#### 4.6.3 性能预算

- 一致性审查本身不调 LLM(纯本地比对) → 延迟 < 50ms;
- 重写每次 = 1 次原型层 LLM 调用 ≈ 3-5s;
- 最坏情况(2 次重写均失败):用户多等 6-10s,在 PRD-4 §13.1 可接受范围内(超过 60s 才触发"网络好像有点慢")。

### 4.7 token 成本控制

#### 4.7.1 单次完整推演 token 预算 ≤ ¥0.5

| 模块 | token 估算(I/O) | 主模型成本(以 DeepSeek-V3 ≈ ¥0.5/1M tokens 计算) |
|---|---|---|
| Decision 重构 | 1k I + 0.5k O | ¥0.0008 |
| 镜子凝练(可选) | 2k I + 0.3k O | ¥0.005(Qwen-Max ≈ ¥4/1M) |
| Step 1 框定 | 1.5k I + 0.5k O | ¥0.001 |
| Step 2 选项 | 2k I + 1k O | ¥0.0015 |
| Step 3 不确定性 | 2k I + 1.5k O | ¥0.0018 |
| Step 5 偏差审计 | 2k I + 0.5k O | ¥0.00125 |
| 多路径短期 | 3k I + 2k O | ¥0.02(Qwen-Max) |
| 多路径中期 | 3k I + 2k O | ¥0.0025 |
| 原型 + 故事核 + 大白话 | 3k I + 1.5k O | ¥0.018(Qwen-Max) |
| 倾向性结论 | 4k I + 1k O | ¥0.0025 |
| 一致性审查重写(预算 1 次) | 3k I + 1.5k O | ¥0.018 |
| **合计预估** | | **≈ ¥0.072(完整,带镜子)** |

实际成本会有浮动,但 **¥0.5 预算非常宽松**——给 token 增长空间(用户输入更长 / context 累积更多)+ 模型涨价空间。

#### 4.7.2 轻推演 token 预算

| 模块 | token | 成本 |
|---|---|---|
| Decision 重构 + Step 1-2 | 4k I + 1.5k O | ¥0.003 |
| Step 5 偏差(对当前倾向) | 2k I + 0.5k O | ¥0.00125 |
| Step 6 用户填(无 LLM) | 0 | 0 |
| **合计** | | **≈ ¥0.005** |

#### 4.7.3 基础推演 token 预算

```
Step 1 + Step 2 + 一句话原型标签 + 3 件事卡片
≈ 5k I + 2k O ≈ ¥0.0035
```

#### 4.7.4 token 使用记账

每次 LLM 调用记录到表 `ai_call_logs`:

```sql
CREATE TABLE ai_call_logs (
  log_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID,
  decision_id UUID,
  run_id UUID,
  step_name TEXT NOT NULL,
  model_used TEXT NOT NULL,
  prompt_tokens INT,
  completion_tokens INT,
  total_cost_cny INT,  -- 厘(0.001元)
  status TEXT,  -- 'success' | 'timeout' | 'rejected_by_filter' | 'fallback'
  retry_count INT,
  created_at TIMESTAMP NOT NULL DEFAULT NOW()
);
```

每周 / 每月汇总,如果实际单次推演成本超过 ¥0.5,触发 alert(给 Wenbo 看并决定调整)。

---

## 5. UI 视觉规范的工程实现(M-Visual 模块)

### 5.1 颜色 token 体系

```css
/* Tailwind 配置 + CSS variable */
:root {
  /* 浅紫主色 */
  --color-purple-primary: #B8A4D4;       /* 主紫 */
  --color-purple-light: #D8C8E8;          /* 浅紫(渐变中段) */
  --color-purple-mist: #EFE6F5;           /* 浅紫雾 */
  --color-purple-deep: #8C7BA8;           /* 深紫(CTA 点睛,极少用) */
  
  /* 纯白基调 */
  --color-surface-white: #FEFEFE;
  --color-surface-mist: #F8F4FB;          /* 雾面 surface */
  
  /* 文字 */
  --color-text-primary: #2A2438;          /* 深灰紫,不用纯黑 */
  --color-text-secondary: #5C5470;        /* 中等灰紫 */
  --color-text-tertiary: #8C8398;         /* 浅灰紫 */
  
  /* 错误 / 警示(用稍深灰紫,不用红) */
  --color-warning: #6B5780;
  --color-error: #4A3D5C;
  
  /* 透光玻璃 */
  --glass-bg: rgba(255, 255, 255, 0.65);
  --glass-border: rgba(184, 164, 212, 0.25);
  --glass-blur: blur(12px);
}
```

**Token 命名规范**:
- 颜色:`--color-{type}-{variant}`
- 透光:`--glass-{property}`
- 间距(间距 token 由 Tailwind 标准提供,不重新定义)

[best-practice 推理,待跑起来后调整]:具体 hex 值可能需要在真实页面上调试时微调——颜色对比度在不同显示器上表现不同。teammate 实现后,Wenbo 在自己设备上 review 一次。

### 5.2 字体方案的工程落地

#### 5.2.1 思源行楷(中文品牌字体)

**HF Space 阶段**:
```html
<!-- 用 jsDelivr CDN 加载子集化版本 -->
<link href="https://cdn.jsdelivr.net/npm/cn-fontsource-source-han-serif-cn-vf-w-light/font.css" rel="stylesheet">
```
**实测发现:思源行楷在 jsDelivr 上没有完整 CDN——需要自己 host。**

**独立部署阶段(推荐方案)**:
- 自 host 思源行楷的子集化版本(只保留产品里实际用到的字符,主要是品牌名 + 标题文字);
- 子集化工具:`fonttools subset` 命令;
- 落地页 + onboarding 的标题文字大约 200-300 个汉字,子集化后字体文件 < 200KB;
- font-display: `swap`(先用 fallback,字体加载完后切换,避免 FOIT)。

**Fallback 链**:
```css
.brand-title {
  font-family: 'SourceHanSerif Brush', 'KaiTi', '楷体', 'STKaiti', serif;
}
```

#### 5.2.2 Snell Roundhand(英文品牌字体)

**全平台 fallback 链**:
```css
.brand-title-en {
  font-family: 'Snell Roundhand', 'Apple Chancery', 'Lucida Calligraphy', cursive;
}
```

**Fallback 实测**:
- macOS / iOS:Snell Roundhand 系统自带 ✓
- Windows:Lucida Calligraphy 系统自带,作为 fallback;视觉差异较大但可接受
- Android:大部分 Android 上 cursive 系统字体不一致 → **必须 self-host Snell Roundhand 的 web font**(若版权允许)或选用免费替代(如 `Allura` 或 `Pinyon Script`,Google Fonts 免费)
- Linux 浏览器:同上

[best-practice 推理]:Snell Roundhand 是 Apple 自带字体,版权属于 Apple,可能不允许 web font 使用。**teammate 实现时检查 license,如果不允许,用 `Allura`(Google Fonts) 替代——视觉感受相近**。

#### 5.2.3 现代无衬线中文版(正文)

**推荐选型**:
```css
.body-text-zh {
  font-family: -apple-system, BlinkMacSystemFont, 
               'PingFang SC', 'Hiragino Sans GB', 
               'Microsoft YaHei', '微软雅黑',
               'Source Han Sans CN', 'Noto Sans SC',
               sans-serif;
}
```

理由:**优先用系统字体**(零加载时间)。各平台默认中文无衬线已经足够现代:
- macOS / iOS:PingFang SC
- Windows:Microsoft YaHei
- Linux:Source Han Sans 或 Noto Sans CJK
- Android:Source Han Sans 系列

**不 self-host 中文正文字体**——字体文件巨大(8MB+),子集化也要 1-2MB,不值得。

#### 5.2.4 Times New Roman(英文正文)

```css
.body-text-en {
  font-family: 'Times New Roman', Times, Georgia, serif;
}
```

Fallback 到 Georgia(macOS / iOS / Windows 都有)。Android 上 TNR 默认有,无 fallback 风险。

**Mobile 实测要求**:在 iOS Safari + Android Chrome 上验证 TNR 在小字号(14px)下的渲染清晰度。如果模糊,切换到 `Georgia` 作为 mobile 默认。

### 5.3 镜子语言的工程实现

#### 5.3.1 卡片边缘微反光

```css
.mirror-card {
  background: var(--glass-bg);
  backdrop-filter: var(--glass-blur);
  border: 1px solid var(--glass-border);
  border-radius: 16px;
  /* 微反光:轻度顶部高光 */
  box-shadow: 
    inset 0 1px 0 rgba(255, 255, 255, 0.6),
    0 4px 24px rgba(184, 164, 212, 0.12);
}
```

#### 5.3.2 弧面分割线

```svg
<!-- 用 SVG path,不用纯 CSS 因为 CSS 难做弧面 -->
<svg viewBox="0 0 400 8" preserveAspectRatio="none" class="mirror-divider">
  <path d="M0,4 Q100,0 200,4 T400,4" 
        stroke="var(--color-purple-mist)" 
        stroke-width="1" 
        fill="none" />
</svg>
```

#### 5.3.3 镜面涟漪加载态(三方案对比 + v1 推荐)

| 方案 | 实现 | 性能 | 视觉效果 | 推荐 |
|---|---|---|---|---|
| **CSS 动画** | `@keyframes` + `border-radius` + `box-shadow` 扩散 | 最优(GPU 加速) | 简洁,但难做"水波"质感 | **v1 推荐** |
| Lottie | After Effects 输出 + lottie-web 库 | 中(JS 解析 + Canvas 绘制) | 细腻,水波感强 | v2+ 候选 |
| Canvas | 自己写 shader 或用 P5.js | 较差(全屏重绘) | 最自由,但开发成本高 | **不推荐** v1 |

**v1 CSS 动画实现伪代码**:
```css
.ripple-loader {
  position: relative;
  width: 60px;
  height: 60px;
  border-radius: 50%;
  background: var(--color-purple-mist);
}
.ripple-loader::before,
.ripple-loader::after {
  content: '';
  position: absolute;
  inset: 0;
  border-radius: 50%;
  border: 2px solid var(--color-purple-light);
  animation: ripple 2.4s cubic-bezier(0.4, 0, 0.2, 1) infinite;
}
.ripple-loader::after {
  animation-delay: 1.2s;
}
@keyframes ripple {
  0% { transform: scale(0.6); opacity: 1; }
  100% { transform: scale(2.4); opacity: 0; }
}
```

#### 5.3.4 空白态留倒影

```css
.empty-state {
  position: relative;
  text-align: center;
  padding: 4rem 2rem;
}
.empty-state::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%) scaleY(-1);
  width: 60%;
  height: 30%;
  background: linear-gradient(to bottom, 
    var(--color-purple-mist) 0%, 
    transparent 100%);
  opacity: 0.3;
  filter: blur(8px);
  pointer-events: none;
}
```

#### 5.3.5 输入框 focus 柔光呼吸

```css
.mirror-input:focus {
  outline: none;
  border-color: var(--color-purple-light);
  box-shadow: 0 0 0 3px rgba(216, 200, 232, 0.4);
  animation: breathe 2.4s ease-in-out infinite;
}
@keyframes breathe {
  0%, 100% { box-shadow: 0 0 0 3px rgba(216, 200, 232, 0.4); }
  50% { box-shadow: 0 0 0 5px rgba(216, 200, 232, 0.55); }
}
```

#### 5.3.6 方案 B 的塔罗视觉与镜子底色的协调实现

对应 PRD-4 §11.5 锁定的方案 B(塔罗作为镜面上的具象物)。

**资产组织**:
```
/static/tarot/
  ├── major_arcana/
  │   ├── 00_fool.svg
  │   ├── 01_magician.svg
  │   ├── ...
  │   └── 21_world.svg
  ├── card_back.svg
  └── metadata.json
```

**metadata.json 格式**:
```json
{
  "00_fool": {
    "name_zh": "愚人",
    "name_en": "The Fool",
    "symbols_zh": ["开始", "天真", "未知的旅程"],
    "symbols_en": ["beginnings", "innocence", "journey into the unknown"],
    "arcana_id": 0
  },
  ...
}
```

**SVG 选择 vs PNG**:
- 牌面用 **SVG**——可缩放、无锯齿、文件小(每张 < 50KB);
- SVG 的现代化重绘风格:**线条简洁、留白多、低对比**(承接 §11.7 反例 — 不要 Rider-Waite 浓重风格);
- 22 张牌总资产体积 < 1.5MB,首次加载用懒加载(只加载抽到的那一张)。

**镜子上的具象物视觉协调**:
```css
.tarot-card-on-mirror {
  position: relative;
  /* 牌面具象,但放在镜面上有微反光 */
  background: var(--color-surface-white);
  border-radius: 12px;
  box-shadow: 
    /* 牌的阴影 */
    0 8px 24px rgba(140, 123, 168, 0.18),
    /* 镜面顶部微反光 */
    inset 0 1px 0 rgba(255, 255, 255, 0.8);
}
.tarot-card-on-mirror::before {
  content: '';
  position: absolute;
  inset: -8px;
  border-radius: 16px;
  background: radial-gradient(circle, 
    rgba(216, 200, 232, 0.2) 0%, 
    transparent 70%);
  z-index: -1;
  /* 牌"放在镜面上"的柔光晕 */
}
```

### 5.4 动效原则的工程落地

#### 5.4.1 动效时长 token

```css
:root {
  --duration-instant: 150ms;    /* 几乎不可见(状态切换) */
  --duration-quick: 300ms;      /* 快速反馈(按钮 hover) */
  --duration-base: 500ms;       /* 默认(页面切换、卡片出现) */
  --duration-slow: 800ms;       /* 慢(强调元素,如镜面涟漪一周期) */
  --duration-breath: 2400ms;    /* 呼吸(focus / loader 循环) */
}
```

#### 5.4.2 缓动曲线 token

```css
:root {
  --ease-out-soft: cubic-bezier(0.25, 0.1, 0.25, 1);     /* 默认柔和退出 */
  --ease-in-out-soft: cubic-bezier(0.4, 0, 0.2, 1);      /* 双向柔和 */
  --ease-elastic: cubic-bezier(0.34, 1.56, 0.64, 1);     /* 极少用 */
}
```

**禁用 cubic-bezier 反例**(契合 PRD-4 §11.6):
- 不用 `cubic-bezier(0.68, -0.55, 0.265, 1.55)`(弹跳)
- 不用 `linear`(僵硬)
- 不用过冲超过 5% 的曲线(突然感)

#### 5.4.3 reduced-motion 支持

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
  .ripple-loader,
  .breathe-effect {
    animation: none;
    /* 改用静态视觉提示 */
  }
}
```

加载态在 reduced-motion 下:用静态 spinner SVG 或文字"……"代替涟漪动画。

### 5.5 暗色模式 v1 决策

**Tech Spec 决策:v1 不做暗色模式**。

理由:
- 浅紫雾面是产品 identity,暗色版本会破坏氛围(PRD-4 §11.7 反例已隐式拒绝);
- v1 资源不允许做两套视觉系统;
- 实测海外华人用户(目标主用户群)在心理类产品里大部分使用浅色模式。

作为 v2+ 候选:如果有强用户反馈("我夜里用想要暗色"),再做。届时不是简单 invert,要重新设计暗色版本的镜子语言。

---

## 6. 国际化技术方案(M-i18n 模块)

### 6.1 Accept-Language 解析逻辑

```python
def detect_language(accept_language: str) -> str:
    """
    返回 'zh' 或 'en'。
    zh-* (zh-CN, zh-TW, zh-HK, zh-SG, zh) → 'zh'
    其他 → 'en'
    无法解析 → 'en'(fallback)
    """
    if not accept_language:
        return 'en'
    
    # 解析 Accept-Language 排序(q value)
    languages = sorted(
        [parse_lang_tag(tag) for tag in accept_language.split(',')],
        key=lambda x: -x[1]  # by q value
    )
    
    for lang_code, q in languages:
        if lang_code.startswith('zh'):
            return 'zh'
        if lang_code.startswith('en'):
            return 'en'
    
    return 'en'
```

### 6.2 localStorage 实现

**键名**:`mirror.lang`(承接 PRD-4 §12.3)

**写入时机**:
1. 用户首次访问且 Accept-Language 自动判定后 → 写入判定结果;
2. 用户手动点切换按钮 → 立即覆盖;
3. 用户登录后,服务端 profile 的 lang_pref 与本地不一致 → 服务端为准,覆盖本地。

**读取时机**:
1. 页面加载第一时间(放在 `<head>` 内联 script,避免 FOUC);
2. 优先级:localStorage > 服务端 user.lang_pref(若已登录) > Accept-Language。

```html
<!-- 内联在 head 顶部,在任何 CSS / 主 JS 加载前执行 -->
<script>
  (function() {
    const lang = localStorage.getItem('mirror.lang') 
              || document.documentElement.lang 
              || 'zh';
    document.documentElement.setAttribute('lang', lang);
  })();
</script>
```

### 6.3 跨子域共享策略

v1 不需要跨子域(只有一个域名)。

如果未来上 `app.weijing.com` + `blog.weijing.com`:
- 用 cookie 替代 localStorage,设置 `domain=.weijing.com`;
- 或者每个子域独立 localStorage,无跨域同步,但用户每次切换子域要重选(可接受体验)。

### 6.4 登录用户跨设备同步

**user.lang_pref 字段同步触发时机**:

| 时机 | 动作 |
|---|---|
| 用户首次注册时 | 用 localStorage 当前值写入 user.lang_pref |
| 用户手动切换语言时(已登录) | 同步更新 user.lang_pref(异步,不阻塞 UI) |
| 用户登录新设备时 | 拉 user.lang_pref → 写入新设备 localStorage(覆盖该设备的浏览器自动判定) |
| 用户清除浏览器数据 | localStorage 丢失 → 下次登录从 user.lang_pref 拉回 |

### 6.5 文案 i18n 资源文件结构

**JSON 文件结构**(放在 `/i18n/`):

```
/i18n/
  ├── zh/
  │   ├── common.json
  │   ├── onboarding.json
  │   ├── inference.json
  │   ├── mirror.json
  │   ├── multipath.json
  │   ├── error.json
  │   ├── feedback.json
  │   └── legal.json
  ├── en/
  │   └── (同结构)
  └── _meta.json (维护翻译完成度)
```

**文件内容示例(zh/onboarding.json)**:
```json
{
  "screen_1": {
    "title": "看见你没走的那条路",
    "subtitle": "未镜陪你把心里那些想了好久没结论的事,慢慢理一遍。",
    "tertiary": "不替你做决定,只帮你看清你在选什么。",
    "cta_next": "下一步",
    "cta_skip": "跳过"
  },
  "screen_2": { ... },
  "screen_3": { ... }
}
```

**字段命名规范**:
- 用 snake_case;
- 嵌套表达页面层级(`screen_1.title` / `step_5.bias_audit_hypothesis_template`);
- 不在字段名里嵌入字数限制(限制写在注释里);
- **预留多语言扩展接口**:为 v6+ 第三种语言不做预实现,但字段名规范不允许 hard-code "zh"/"en" 之外的语言。

### 6.6 翻译工作流

**v1 翻译流程**:

1. 中文版本由 Wenbo + agent team 写;
2. 英文翻译由 agent team 翻译(单次 LLM 调用,但要审核);
3. **强制 Wenbo 在英文版本上线前过一遍**(发现明显翻译腔可改);
4. 所有翻译变更走 git commit,便于追溯。

**翻译质量审核 checklist**(放在 `_meta.json` 注释里):
- [ ] 主语规则:中文"你"对应英文"you",镜子层不漂移;
- [ ] 禁用词:中英都不出现禁用词;
- [ ] 字数:英文翻译后字符数 ≤ 中文 × 1.8(避免 UI 溢出);
- [ ] 文化适配:不强求(承接 §1.3"不是 native rewrite"),但避免明显 awkward。

**漏翻检查工具**:写一个简单 script 比对中英文件 keys 是否完全对齐,差异即是漏翻。

---

## 7. 错误处理与降级的工程实现(M-Error 模块)

### 7.1 本地缓存策略

**缓存内容 + 时机**:

| 用户输入 | 缓存 key | 时机 |
|---|---|---|
| 决策原始输入 | `mirror.draft.{decision_id}.original_prompt` | 输入框 onBlur 或 250ms debounce |
| 问卷答复(进行中) | `mirror.draft.profile.{section}` | 每选一题立即缓存 |
| Step 4 概率档位 | `mirror.draft.{run_id}.step4` | 用户认领档位后立即缓存 |
| Pre-mortem 文本 | `mirror.draft.{run_id}.step6` | onBlur 或 250ms debounce |
| 镜子层用户投射 | `mirror.draft.{mirror_run_id}.projection` | onBlur |
| 快速捕捉文本 | `mirror.draft.quick_capture.{decision_id}` | onBlur |

**清除时机**:
- 该输入成功提交到服务端后(收到 200 + ack);
- 用户登出时(全部清除);
- 用户主动清除草稿(主面板"清理本地草稿"按钮)。

**实现库**:
- HF Space 阶段:vanilla `localStorage.setItem` / `getItem`;
- 独立部署阶段:`zustand-persist` 或 `redux-persist`(取决于状态管理选型)。

[best-practice 推理]:用 `localStorage` 而非 `sessionStorage`——用户关掉 tab 再回来仍能恢复;但要注意 localStorage 5MB 限制,定期清理过期草稿(`cleanup_drafts` 任务,清除 7 天以上未更新的)。

### 7.2 模型 API 多通道 fallback 链

详见 §4.4.2,这里补 fallback 矩阵:

| 主 → 备 1 → 备 2 切换条件 | 实现 |
|---|---|
| 60s 超时 | `asyncio.wait_for(call, timeout=60)` 抛 `TimeoutError` |
| HTTP 5xx error | 立即 catch + 切换 |
| HTTP 429 限流 | 等 1s 重试 1 次,仍 429 则切换 |
| Token 截断(返回不完整) | 检查 finish_reason,非 "stop" 则切换 |

### 7.3 重试策略

```python
RETRY_STRATEGIES = {
    'mirror_distillation': {'max_retry': 2, 'backoff': 'exp', 'base_ms': 500},
    'step1_framing': {'max_retry': 3, 'backoff': 'linear', 'base_ms': 1000},
    'step3_uncertainty': {'max_retry': 2, 'backoff': 'exp', 'base_ms': 500},
    'multipath_short': {'max_retry': 1, 'backoff': 'none'},  # 慢但重要,不重试浪费
    'consistency_check_rewrite': {'max_retry': 2, 'backoff': 'none'},
}
```

### 7.4 错误日志格式

```python
class ErrorLog(BaseModel):
    log_id: UUID
    user_id: Optional[UUID]
    decision_id: Optional[UUID]
    run_id: Optional[UUID]
    step_name: str
    error_type: str  # 'timeout' | 'api_error' | 'filter_rejected' | 'consistency_fail' | 'json_parse_error'
    error_detail: dict  # {'http_status': 500, 'model': 'deepseek-v3', ...}
    user_input_hash: str  # 不存原文(隐私),只存 SHA256
    user_facing_message_shown: str  # 给用户看到的文案(对应 PRD-4 §13.1)
    fallback_taken: str  # 'retry' | 'switch_model' | 'skip_step' | 'final_failure'
    created_at: datetime
```

**重要**:`user_input_hash` 而非明文——便于产品改进时复现(用户可以协助提供原文),但日志本身不含 PII。

### 7.5 保住 voice 的工程纪律

**硬编码错误文案表**:

```python
ERROR_MESSAGES_ZH = {
    'ai_timeout_30s': "我这边再想一下——网络好像有点慢,要不要稍等几秒?",
    'ai_timeout_60s': "今天我这边不太顺手,你刚才写的内容已经存好了,要不要明天再来一次?",
    'consistency_fail': "这个推演的'故事核'部分今天没有顺利做出来,我先把结构化分析给你——你可以读结构层做判断,故事核如果你想要可以让我重新尝试。",
    'filter_rejected_after_retry': "这一段我没说清楚,让我重新组织一下。",
    'network_offline': "好像断网了——你刚才填的没有丢,网络回来我们继续。",
    'rate_limited': "我跟不上了——慢一点,我们一起想。",
    'step4_skip_attempt': "这一步我陪你想——你的直觉这件事只有你自己知道,我帮你看清它里面藏着什么。慢慢说,我等你。",
    'input_too_long': "你写得很多——为了让我能好好理一遍,先帮你保留最近的 X 字,全文我也存了,等会可以回看。",
    'payment_failed': "支付那边没走通——你的推演已经保存好了,等支付回来我们继续。要试试别的支付方式吗?",
}

ERROR_MESSAGES_EN = { ... 翻译 }
```

**这些文案 hard-coded 到错误处理模块**——后端不允许返回原始错误码到用户面;前端不允许自行写错误文案。

**code review checklist**:
- [ ] 任何 try/except 抛到用户面前的 message 必须是 `ERROR_MESSAGES_*` 里的某一条;
- [ ] 不允许 `console.error` / 调试 message 出现在用户可见区域;
- [ ] 错误发生时用户的输入必须已经 localStorage 缓存。

---

## 8. 反馈系统数据流(M-Feedback 模块)

### 8.1 入口 1 反馈表单的具体技术实现

#### 8.1.1 自建 vs 第三方对比

| 选项 | 优点 | 缺点 | 推荐 |
|---|---|---|---|
| **自建表单** | 数据自有 / 可关联用户 ID / 视觉与产品一致 | 开发量(~半天) | **v1 推荐** |
| Tally | 0 开发 / 视觉可定制 | 数据需 webhook 才能关联用户 | 不推荐 |
| Typeform | 视觉好 / 用户体验佳 | 收费($25+/月)+ 数据隔离 | 不推荐 |
| Google Forms | 完全免费 | 视觉破坏产品氛围 | 拒绝 |

**结论**:v1 自建。表单本身就是个简单的 4 字段 Form,自建成本低于集成成本。

#### 8.1.2 自建表单的实现

```typescript
// FastAPI route
@app.post("/api/feedback/form")
async def submit_feedback_form(
    feedback: FeedbackFormSubmission,
    user_id: Optional[UUID] = Depends(get_optional_user)
):
    feedback_record = await db.feedbacks.insert({
        'user_id': user_id,
        'feedback_type': 'form',
        'category': feedback.category,
        'content': feedback.content,
        'email': feedback.email,
        'allow_contact': feedback.allow_contact,
    })
    
    # 异步触发邮件通知
    await email_queue.enqueue('feedback_notify_wenbo', feedback_record.id)
    
    return {'status': 'received'}
```

**前端表单 UI 必须遵循 §11 视觉规范**——同一套浅紫雾面 + 镜子语言 + 字体方案。

### 8.2 邮件接收方案

**v1 推荐**:**Wenbo 个人邮箱接收 + Resend 转发**

```
用户提交表单
   │
   ▼
反馈数据存 DB
   │
   ▼
Resend 发邮件给 wenbo@personal.email
   │  Subject: [未镜反馈] {category} - {timestamp}
   │  Body: 反馈内容 + 用户 ID + 关联推演 ID(若有)+ 直接回复链接
   ▼
Wenbo 收件 + 自己分类 + 进 backlog
```

**升级路径**(如果反馈量上升):
- 100 用户阶段:邮箱够用;
- 500 用户阶段:迁到 Linear / Notion 工单系统(用 Resend webhook 自动转发到 Linear API)。

### 8.3 入口 2 一键反馈的数据存储

```typescript
// 推演完成页底部
<div className="quick-feedback">
  <p>今天用得舒服吗?</p>
  <button onClick={() => submitClick('😊')}>😊</button>
  <button onClick={() => submitClick('😐')}>😐</button>
  <button onClick={() => submitClick('☹️')}>☹️</button>
</div>
```

**数据写入**:
```python
@app.post("/api/feedback/one_click")
async def submit_one_click(
    feedback: OneClickFeedback,  # {sentiment, related_run_id, related_step}
    user_id: UUID = Depends(get_user)
):
    await db.feedbacks.insert({
        'user_id': user_id,
        'feedback_type': 'one_click',
        'sentiment': feedback.sentiment,
        'related_run_id': feedback.related_run_id,
        'related_step': feedback.related_step,
        'user_agent': request.headers.get('user-agent'),
    })
    
    # 触发自动 alert 检查
    await alert_check_queue.enqueue('check_negative_concentration', feedback.related_step)
    
    return {'status': 'received'}
```

**触发位置**:

| 位置 | related_step 值 |
|---|---|
| 推演完成页 | `'completion'` |
| 镜子凝练确认后 | `'mirror_distillation'` |
| Step 5 偏差审计点[我不同意]后 | `'step5_disagreed'` |
| 决策回访问卷完成后 | `'follow_up'` |

### 8.4 自动 alert 触发条件

**实现**:

```python
async def check_negative_concentration(step_name: str):
    """检查某个 step 在过去 7 天内 ☹️ 占比是否超过 30%"""
    last_7d_feedback = await db.feedbacks.find({
        'feedback_type': 'one_click',
        'related_step': step_name,
        'created_at': {'$gt': datetime.now() - timedelta(days=7)}
    })
    
    if len(last_7d_feedback) < 10:
        return  # 样本太少,不触发
    
    sad_count = sum(1 for f in last_7d_feedback if f.sentiment == '☹️')
    sad_ratio = sad_count / len(last_7d_feedback)
    
    if sad_ratio > 0.3:
        await send_alert_email(
            to='wenbo@personal.email',
            subject=f'[未镜 alert] {step_name} 负面反馈集中: {sad_ratio:.0%}',
            body=f'最近 7 天 {step_name} 收到 {len(last_7d_feedback)} 条一键反馈,'
                 f'其中 {sad_count} 条 ☹️ ({sad_ratio:.0%})。\n'
                 f'建议:看一下这部分反馈对应的推演,判断是否需要进 backlog。'
        )
```

**alert 频率限制**:同一 step 7 天内只发 1 次 alert,避免轰炸。

[best-practice 推理]:7 天窗口 + 30% 阈值是初始猜测,真实数据出来后调整。可能 14 天窗口 + 25% 更合理,但需要数据。

---

## 9. 关键接口契约(模块间)

### 9.1 设计原则

- 所有接口走 **HTTP REST + JSON**(HF Space 阶段)→ 独立部署阶段保留同样契约,只是实现可换 GraphQL / tRPC;
- 接口路径统一前缀 `/api/v1/`;
- 错误响应:不暴露技术细节,见 §7.5;
- 鉴权:JWT in `Authorization: Bearer {token}` header。

### 9.2 核心接口契约(简表 — 完整 OpenAPI 规范由 teammate 起草并入 codebase)

| 接口 | 调用方 | 被调用方 | 输入 | 输出 |
|---|---|---|---|---|
| `POST /api/v1/users/register` | 前端 | M-User | `{email, password, lang, agreed_tos, agreed_18plus}` | `{user_id, jwt}` |
| `POST /api/v1/users/login` | 前端 | M-User | `{email, password}` | `{user_id, jwt, lang_pref}` |
| `POST /api/v1/profile/basic` | 前端 | M-User | `{situation_anchors, value_priorities}` | `{profile_summary}` |
| `POST /api/v1/profile/deep` | 前端 | M-User | `{risk_profile, bias_profile}` | `{updated_summary}` |
| `POST /api/v1/decisions` | 前端 | M-Inference | `{original_prompt}` | `{decision_id, reframed_question, recommended_form, psychological_state}` |
| `POST /api/v1/decisions/{decision_id}/runs` | 前端 | M-Inference | `{form_type, mirror_used, mirror_run_id?}` | `{run_id}` |
| `POST /api/v1/runs/{run_id}/step/{step_num}` | 前端 | M-Inference | `{user_input}` | `{ai_output, next_step}` |
| `POST /api/v1/mirror_runs` | 前端 | M-Inference | `{decision_id, card_drawn, card_method, user_projection}` | `{mirror_run_id, distillation_draft, suggested_variable}` |
| `PATCH /api/v1/mirror_runs/{mirror_run_id}` | 前端 | M-Inference | `{user_choice, final_distillation?}` | `{status}` |
| `POST /api/v1/quick_captures` | 前端 | M-Stream | `{decision_id, content}` | `{capture_id}` |
| `GET /api/v1/decisions/{decision_id}/stream` | 前端 | M-Stream | - | `[stream_entries[]]` |
| `POST /api/v1/runs/{run_id}/incorporate_captures` | 前端 | M-Stream | `{capture_ids[]}` | `{updated_run}` |
| `POST /api/v1/followups/{followup_id}/respond` | 前端 | M-FollowUp | `{choice, feeling_score, feeling_emoji, agreed_anonymous_stories}` | `{aggregated_feedback}` |
| `POST /api/v1/feedback/form` | 前端 | M-Feedback | `{category, content, email?, allow_contact}` | `{status}` |
| `POST /api/v1/feedback/one_click` | 前端 | M-Feedback | `{sentiment, related_run_id, related_step}` | `{status}` |
| `POST /api/v1/payments/checkout` | 前端 | M-Pay | `{product_type, decision_id?}` | `{checkout_url}` |
| `POST /api/v1/payments/webhook` | Stripe / Paddle | M-Pay | `{webhook_payload}` | `{status}` |
| `GET /api/v1/users/me/data_export` | 前端 | M-Legal | - | `{download_url}`(JSON 格式全部数据) |
| `DELETE /api/v1/users/me` | 前端 | M-Legal | `{confirmation}` | `{status}`(24h 内执行) |

### 9.3 错误响应契约

```json
{
  "error": {
    "code": "AI_TIMEOUT",
    "user_message": "今天我这边不太顺手,你刚才写的内容已经存好了,要不要明天再来一次?",
    "retry_allowed": true,
    "fallback_action": "save_draft_and_retry"
  }
}
```

**纪律**:
- `user_message` 必须从 `ERROR_MESSAGES_*` 表取(§7.5);
- `code` 是给前端逻辑判断用,不直接展示;
- 不返回堆栈、SQL 语句、模型名等技术细节。

---

## 10. HF Space 部署方案

### 10.1 Gradio / Streamlit / FastAPI 对比 + 推荐

**选定:FastAPI Docker SDK on HF Space**(承接 §2.1)。

理由:
- Gradio 适合纯模型 demo,不适合多步推演 + 用户问卷 + 持久化数据的复杂应用;
- Streamlit 状态管理弱,多用户场景下 session state 会出问题;
- FastAPI + Docker SDK 在 HF Space 上完全自由,等于自带服务器。

### 10.2 HF Space FastAPI 部署 walkthrough

#### 10.2.1 Repo 结构

```
weijing-mvp/
├── README.md (HF Space 必须;包含 sdk: docker)
├── Dockerfile
├── requirements.txt
├── app.py (FastAPI 入口)
├── api/ (路由模块)
│   ├── users.py
│   ├── decisions.py
│   ├── inference.py
│   ├── mirror.py
│   ├── stream.py
│   ├── followup.py
│   └── feedback.py
├── core/ (业务逻辑)
│   ├── ai_layer.py
│   ├── prompts/
│   ├── consistency_check.py
│   ├── output_filter.py
│   └── error_messages.py
├── db/ (数据库连接 + migrations)
│   ├── client.py (Supabase Postgres connection)
│   └── migrations/
├── i18n/ (中英文资源)
├── static/ (CSS + 字体 + 22 张塔罗 SVG)
├── templates/ (Jinja2)
└── tests/
```

#### 10.2.2 Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 7860
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "7860"]
```

#### 10.2.3 README.md(HF Space 配置)

```yaml
---
title: 未镜 The Other Path
emoji: 🪞
colorFrom: purple
colorTo: white
sdk: docker
pinned: false
license: proprietary
---
```

#### 10.2.4 环境变量(HF Space Secrets)

```
DATABASE_URL=postgresql://...@supabase
DEEPSEEK_API_KEY=...
QWEN_API_KEY=...
DOUBAO_API_KEY=...
KIMI_API_KEY=...
RESEND_API_KEY=...
JWT_SECRET=...
SENTRY_DSN=...
```

### 10.3 HF Space 限制与对应妥协

| 限制 | 对应妥协 |
|---|---|
| 2 vCPU / 16GB RAM | 单实例够用,5-10 用户量级;不做并发优化 |
| 50GB disk | 22 张塔罗 SVG < 2MB,绰绰有余;不缓存大文件 |
| 公网访问(自由) | OK |
| 不能部署外部数据库 | 用 Supabase Postgres 外部托管(已规划) |
| 默认 ephemeral storage | 数据全部存 Supabase,本地不存 |
| 重启时间长(冷启动 30s+) | 用 HF Space "Always On"(免费 tier 也有,但限时);或接受首次访问慢 |
| API rate limit(HF 自身) | 不上百个用户时不会触发 |

### 10.4 数据持久化策略

**所有持久化数据走 Supabase**:
- Postgres for relational data(§3 数据模型);
- Supabase Storage for file uploads(若有,v1 没有用户上传);
- 22 张塔罗 SVG 静态资产 → 直接打包进 Docker image,不走 Storage。

**Backup 策略**:
- Supabase 自动 daily backup(免费 tier 7 天保留);
- 关键数据(decisions / runs)每周用 cron + pg_dump 导一份到 R2(独立存储);
- v1 阶段不做实时 replication。

### 10.5 模型 API 调用从 HF Space 出发的 latency 预期

实测预估(基于公开数据,**待真实跑起来后调整**):

| 模型 | 美国 HF Space → 模型 API 端点 | 单次延迟(p50) |
|---|---|---|
| DeepSeek(中国) | 美→中跨境 | 800-1500ms |
| Qwen(阿里云) | 美→中跨境 | 800-1500ms |
| Doubao(火山) | 美→中跨境 | 800-1500ms |
| Kimi(Moonshot) | 美→中跨境 | 1000-2000ms |

**对应推演体验影响**:
- 完整推演 ~10 次 LLM 调用,累积延迟 8-15s(纯 latency);
- 加上模型推理时间(各 step 2-8s),完整推演真实时长 ~30-60s 完成生成;
- 用户面体验:每个 Step 显示加载态(镜面涟漪),用户填表填得慢于 LLM 生成。

[best-practice 推理]:如果跨境 latency 实测 > 2s 严重影响体验,可考虑:
1. 把 HF Space 迁到亚洲 region(若 HF Space 支持);
2. 接 Cloudflare Workers 做边缘代理;
3. 独立部署阶段直接选亚洲 VPS(如新加坡 / 东京)。

---

## 11. 独立部署阶段的迁移路径

### 11.1 可复用的代码 / 配置

- **核心业务逻辑全部可复用**:`core/`(AI 调用层 / 一致性审查 / 输出过滤)、`db/`(数据库 client)、`i18n/`(翻译资源)、prompts 模板;
- **API 契约保持不变**:迁移时不改前端调用方式;
- **数据库无需迁移**:Supabase 直接连(只换连接字符串)。

### 11.2 必须重写的部分

- **前端从 Jinja2 + HTMX → Next.js 14 App Router**:
  - 落地页、Onboarding、问卷、推演 step 页全部 React 化;
  - i18n 用 `next-intl` 或 `next-i18next`;
- **鉴权从自实现 JWT → NextAuth.js**:迁移时给老用户发"重新设置密码"邮件(JWT 不兼容);
- **静态资源从 Docker image → Cloudflare R2 / Vercel CDN**;
- **支付集成全部接通**(HF Space 阶段可只做 Stripe,独立部署阶段加 Paddle / 支付宝海外 / 微信国际)。

### 11.3 数据迁移路径

1. HF Space 阶段所有数据已经在 Supabase → 独立部署阶段直接连同一个 Supabase,**零迁移**;
2. 用户账号继续用同一邮箱登录;
3. 只需通知用户:"我们升级了平台,密码需要重新设置一次"——一次性 email blast。

### 11.4 域名 / 证书 / Cloudflare / 海外 VPS 选型推荐

| 项 | 推荐 | 备选 |
|---|---|---|
| 域名注册 | **Porkbun**(便宜 + 隐私保护免费) | Namecheap |
| 域名 TLD | `.app`(自带 HSTS 强制 HTTPS) | `.com` / `.io` |
| DNS / CDN | **Cloudflare**(免费 tier 足够) | - |
| 证书 | Cloudflare 自动 SSL | Let's Encrypt |
| 前端托管 | **Vercel** | Netlify |
| 后端 VPS | **Railway**(简单)或 **Fly.io**(全球分布) | DigitalOcean |
| 数据库 | **Supabase**(继续) | Neon |
| 邮件 | **Resend**(继续) | Postmark |

### 11.5 域名建议

候选:
- `weijing.app` - 简洁,与中文名一致
- `theotherpath.app` - 与英文名一致
- `weijing.us` - 可能更便宜
- `notdog.app` - 个人 vanity 选项(基于 idea seed 提到的 GitHub repo `notdog1998`)

→ **开放点(留给 Wenbo 决策)**:
- 主域名选哪个;
- 是否同时注册多个 + 设置重定向。

---

## 12. 测试策略

### 12.1 单元测试

| 模块 | 测试覆盖 |
|---|---|
| `output_filter.py` | 所有禁用词的 regex 命中 + 边界 case(部分匹配 / 大小写 / 词内嵌入) |
| `consistency_check.py` | 各 archetype 的 rule 命中 + 不命中 + 重写循环上限 |
| `local_cache.py` | 草稿存取 + 过期清理 |
| `i18n.py` | Accept-Language 解析 + 漏翻 key 检测 |
| `error_messages.py` | 所有 error code 必须有中英对应 message |
| `consistency_check.py` | 模板化对照 4 步流程 |

### 12.2 集成测试

完整推演流程的 E2E 测试:

```
Test: 完整推演 happy path (中文用户,启用镜子)
  1. 注册 + 完成首次问卷
  2. 输入决策 "想了 6 周要不要离职"
  3. AI 重构 + 推荐完整推演
  4. 抽塔罗(自己选 The Hermit)
  5. 投射 + AI 凝练 + 用户确认
  6. 走完 Step 1-6
  7. 输出页:三个具体瞬间 / 概率带 / 故事核 / 倾向性结论 / 未决定承接
  8. 一键反馈 😊
  
  断言:
  - 全程无禁用词出现
  - run_id 关联 mirror_run_id
  - 思考流有 inference_summary entry
  - feedback 关联到 run_id
```

### 12.3 错误注入测试

- 模拟主模型 timeout → 验证切换到备模型;
- 模拟 LLM 输出禁用词 → 验证重写逻辑;
- 模拟一致性审查 fail 3 次 → 验证 archetype_skipped 被设为 true 且用户看到 fallback 文案;
- 模拟网络断开 → 验证用户输入 localStorage 缓存。

### 12.4 关键 prompt 输出过滤回归测试

**强制要求**:PRD-4 §3.3.3 禁用词清单的所有 case 必须过。

```python
# tests/test_output_filter.py
PROHIBITED_OUTPUTS_ZH = [
    "这张牌意味着你将经历一段困境",
    "你注定会成为一个领导者",
    "未来你会遇到一个对的人",
    # ... 每个禁用词至少 2 个 case
]

@pytest.mark.parametrize("output", PROHIBITED_OUTPUTS_ZH)
def test_output_filter_catches_zh(output):
    cleaned, rejected = filter_output(output, 'zh')
    assert rejected == True
```

每次 PR 必须跑过这个 test suite。

### 12.5 用户测试的工程支撑

**首批 50 用户深访的工程需求**(PRD-4 §6 + §11):

1. **每条反馈链接到具体推演**:已通过 `feedbacks.related_run_id` 实现;
2. **能 export 反馈数据给 Wenbo 分析**:实现一个内部页面 `/admin/feedback`(只 Wenbo 邮箱可访问)+ CSV 导出按钮;
3. **深访问题作为深访工具**(不在产品内,在外部 Notion / Airtable):
   - "你来用产品时这件事处于决策的什么阶段?"
   - "产品让你感觉是被陪着想,还是被推着想?"
   - "如果你推演完仍未决定,产品让你感觉这是失败还是正常状态?"
   - "你会推荐给朋友吗?"
   - "如果用一句话告诉朋友这是什么,你会怎么说?"

---

## 13. 法律 / 合规的工程化落实

### 13.1 GDPR right to be forgotten 实现

```python
@app.delete("/api/v1/users/me")
async def delete_account(
    confirmation: str,  # 用户必须输入 "DELETE MY ACCOUNT" 确认
    user_id: UUID = Depends(get_user)
):
    if confirmation != "DELETE MY ACCOUNT":
        return {'error': 'confirmation mismatch'}
    
    # 24 小时内执行(异步任务)
    await delete_queue.enqueue(
        'hard_delete_user',
        user_id,
        scheduled_for=datetime.now() + timedelta(hours=24)
    )
    
    # 即时 soft delete(用户立即看不到自己的数据)
    await db.users.update(user_id, {'deleted_at': datetime.now()})
    
    return {'status': 'scheduled', 'execution_time': '24h'}
```

**hard_delete 任务**:

```python
async def hard_delete_user(user_id: UUID):
    # CASCADE 删除所有关联数据
    await db.users.delete(user_id)
    
    # 反馈数据保留(已 SET NULL),但 user_id 字段已 NULL → 无法关联回个人
    
    # AI 调用日志:user_id 已记录,需要单独清除
    await db.ai_call_logs.delete_where({'user_id': user_id})
    
    # 邮件订阅列表(Resend):移除
    await resend.contacts.remove(user_id_to_email[user_id])
    
    log_audit_event('hard_delete_completed', {'user_id': user_id})
```

**不可逆**:用户被告知"删除后不可恢复"。

### 13.2 数据导出实现

```python
@app.get("/api/v1/users/me/data_export")
async def export_data(user_id: UUID = Depends(get_user)):
    data = {
        'user': await db.users.get(user_id),
        'profile': await db.user_profiles.get(user_id),
        'decisions': await db.decisions.find({'user_id': user_id}),
        'inference_runs': await db.inference_runs.find({'user_id': user_id}),
        'mirror_runs': await db.mirror_runs.find({'user_id': user_id}),
        'thought_streams': await db.thought_streams.find({'user_id': user_id}),
        'quick_captures': await db.quick_captures.find({'user_id': user_id}),
        'followups': await db.decision_followups.find({'user_id': user_id}),
        'payments': await db.payments.find({'user_id': user_id}),
        'feedbacks': await db.feedbacks.find({'user_id': user_id}),
    }
    
    # 移除敏感字段(password_hash 等)
    data['user'].pop('password_hash', None)
    
    # 生成临时 download URL(7 天有效)
    file_path = await generate_export_file(data, format='json')
    download_url = await generate_signed_url(file_path, ttl_days=7)
    
    return {'download_url': download_url, 'format': 'json'}
```

### 13.3 反滥用机制

**防止用户用产品做大量人对人的命运评判**:

- **Rate limiting**:每用户每天最多 10 次完整推演(免费用户),20 次(付费用户)——超过提示"今天先到这里,明天我陪你想"(voice 一致);
- **决策内容检查**:LLM 在 Decision 重构 step 检查输入是否是"针对他人的命运评判"(如"我朋友 X 该不该和 Y 在一起")—— 如果是,引导回到自己:"让我们看看你自己怎么想——是什么让你也在为这件事纠结?"
- **不存储他人的姓名 / 身份信息**:用户输入中识别到他人姓名时,产品文案不重复使用(只用代词"那个人")。

### 13.4 ToS / Privacy Policy / Cookie Policy 的产品内嵌入

**位置 + 接受流程**:

| 文档 | 嵌入位置 | 接受方式 |
|---|---|---|
| ToS | 注册页 / footer | 注册时勾选"我已阅读并同意 ToS"+ "我已年满 18 岁",一并存 `users.agreed_tos_at` + `users.agreed_age_18plus` |
| Privacy Policy | 注册页 / footer / 关于页 | 注册时同 ToS 同时同意(单一勾选) |
| Cookie Policy | 首次访问弹窗 | 首次访问显示 banner: "我们用必要 cookie 保存你的语言偏好。[了解更多 / 知道了]" |

**未成年人拒绝服务路径**:

```typescript
function handleRegistration(form) {
  if (!form.agreed_age_18plus) {
    return showError(getMessage('age_18plus_required'));
    // "明决面向 18 岁以上用户。如果你未满 18 岁,我们建议先和你信任的成年人讨论你的决策。"
  }
  // ...
}
```

---

## 14. Claude Code agent teams 分工建议

> **本节基于官方 Claude Code agent teams 文档**(参考资料中提供的"在本地 Orchestrate teams of Claude Code sessions")。
> 涉及具体 API / hook / permissions / spawn 命令处使用文档精确名称。
> 涉及 best practice(如"几个 teammate 最优"等)按文档指引推理,标注 *[best-practice 推理]*。

### 14.1 Wenbo 的角色

Wenbo 是 **lead session 的发起者 + 唯一人类决策者,不写代码**。

主 lead 是一个 Claude Code session(由 Wenbo 启动),负责:
- 阅读 Tech Spec + PRD-4 + r2-idea-v5;
- spawn teammates 执行具体模块开发;
- 收集 teammate 产物 + 集成 + 跑 test;
- 遇到 §14.6 "不能动清单" 的事 → 立即停手,问 Wenbo;
- 遇到模块外问题(如 prompt 工程不收敛)→ 自己想或问 Wenbo。

### 14.2 推荐 spawn 几个 teammates

*[best-practice 推理,待跑起来后调整]*

**推荐 3-5 个 teammates 并行**——理由:
- < 3 个:并行度不够,lead 闲置时间多;
- > 5 个:lead 协调成本上升,接口冲突概率上升;
- 4 是 sweet spot,留 1 个 slot 给临时任务。

**典型并行配置**:

| Teammate | 负责模块 | 主要交付 |
|---|---|---|
| **T-Backend-Core** | M-User + M-Inference + M-AI(核心后端) | API routes / business logic / LLM 调用层 |
| **T-Backend-Aux** | M-Stream + M-FollowUp + M-Feedback + M-Pay(辅助后端) | 边缘 API + 异步任务 |
| **T-Frontend** | 前端 UI(M-Visual) + i18n(M-i18n) | 页面 + 视觉规范落地 + 翻译资源加载 |
| **T-Devops-Legal** | HF Space 部署 + DB migration + ToS / Privacy 文档 + GDPR 实现 | 部署脚本 / 数据库 schema / 法律文档 |

**临时 slot**:
- 测试集中编写阶段:spawn T-Test 跑 §12 测试策略;
- 初期 prompt 调优阶段:spawn T-Prompt 专注 §4 prompt 模板。

### 14.3 模块依赖关系 → task list

```
Phase 1(并行,3 天)
├── T-Backend-Core: 数据库 schema(§3) + M-User 注册登录 + M-AI 调用层骨架
├── T-Frontend: 落地页 + Onboarding 三屏(§4.2.6)+ 视觉规范(§5)
├── T-Devops-Legal: HF Space repo 初始化 + Supabase 接通 + ToS / Privacy 起草
└── T-Backend-Aux: M-Feedback 表单接口(可独立先开发)

Phase 2(部分并行,5 天)— 必须 Phase 1 完成数据库 schema 后
├── T-Backend-Core: M-Inference 六步流水线 + 镜子模块(依赖 Phase 1 的 M-AI)
├── T-Frontend: 推演各 step 页面 + 镜子层 UI(方案 B 视觉)
├── T-Devops-Legal: GDPR 实现 + 18+ 校验 + 18+ 拒绝服务页
└── T-Backend-Aux: M-Stream 思考流 + 快速捕捉(依赖 M-Inference)

Phase 3(集成 + 测试,3 天)
├── 全部 teammates: 端到端集成
├── 临时 spawn T-Test: §12 测试策略实施
└── lead: 跑通 happy path + 错误注入

Phase 4(部署上线,1 天)
└── T-Devops-Legal: HF Space deploy + Wenbo 自用验证
```

总计 ~12 天到 HF Space MVP 上线。

### 14.4 每个 teammate 的 onboarding 上下文

**spawn prompt 模板** *[best-practice 推理]*:

```
你是 [Teammate name] 的开发者,负责未镜(The Other Path)产品的 [模块代号 + 名称]。

## 必读文档(按顺序)
1. r2-idea-v5.md — idea 真源,理解为什么这样做
2. PRD-4.md — 产品需求真源,理解做什么
3. Tech-Spec.md §[相关章节] — 技术规范,理解怎么做
4. Tech-Spec.md §15 关键设计决策的"为什么" — 防漂移护栏
5. Tech-Spec.md §14.6 不能动清单 — 触及就停手问 lead

## 你的任务范围
- 实现:[具体模块 + 接口契约]
- 不实现:[明确说不做的部分,避免越界]
- 输出格式:[code + tests + 文档更新]

## 接口契约
你与其他模块对接的所有接口在 §9 已定义。
不允许修改契约——如果你认为契约有问题,先问 lead。

## 不能动的事
1. r2-idea-v5 锁定纪律(Barnum 护栏 / 不预言 / 双层一致性 / 长期颗粒度梯度)
2. PRD-4 锁定方向(§11.5 方案 B / §12 C 方案 / §13.1 错误文案 / §14 双入口)
3. 禁用词清单(中英)
4. 错误文案表(§7.5)
5. 用户面文案 voice("陪你慢慢理一遍 / 我陪你想 / 我等你")

任何冲突立即停手,提交问题给 lead。

## 验收标准
- 接口契约符合 §9
- 测试覆盖 §12 列表项
- 错误处理用 §7.5 文案表
- 文案用 PRD-4 §5 用法表 + i18n 资源
```

### 14.5 跨 teammate 的接口对接方式(避免文件冲突)

**纪律**:
1. **每个模块在独立 directory**:`/api/inference/`、`/api/feedback/` 等,文件不交叉;
2. **共享文件清单**(必须由 lead 协调修改):
   - `db/migrations/` — schema 改动;
   - `i18n/` — 翻译资源;
   - `core/error_messages.py` — 错误文案表;
   - `core/output_filter.py` — 禁用词清单;
3. **接口契约**(§9):一旦写定不允许 teammate 单方面改。需要改时,提议给 lead,lead 决定后通知所有相关 teammates;
4. **commit 纪律**:每个 teammate 一个 git branch(`feature/T-Backend-Core-...`),lead 负责 merge。

### 14.6 不能动清单(集成 idea + PRD 锁定纪律)

任何 implementation 触及以下,**立即停手 + escalate 给 lead → Wenbo**:

#### 14.6.1 来自 r2-idea-v5 锁定的硬约束

| 纪律 | 出处 |
|---|---|
| **Barnum 护栏**(原型只命名路径不分类用户) | r2-v5 §6 + PRD-4 §3.1 |
| **不预言纪律**(主语永远是用户 / 禁用词 / 镜子层只作 prompt) | r2-v5 §6 + PRD-4 §3.3 |
| **双层一致性审查**(冲突时原型层重写,详见 §4.6) | r2-v5 §6 + PRD-4 §5.4 |
| **长期颗粒度梯度**(只给故事核 + 方差形状,不给具体事件) | r2-v5 §7 + PRD-4 §3.5 |
| **Step 4 必填**(用户认领可能性档位,AI 不替写) | r2-v5 §6 + PRD-4 §3.4 |
| **Step 6 必填**(用户写 Pre-mortem) | r2-v5 §6 + PRD-4 §3.4 |
| **不进中国大陆官方市场** | r2-v5 §4.3 + PRD-4 §8 |

#### 14.6.2 来自 PRD-4 锁定的方向

| 纪律 | 出处 |
|---|---|
| **错误处理 voice**(§13.1 文案表) | PRD-4 §13 |
| **UI 视觉规范红线**(§11.7 反例清单 — 不做具象奇幻 / 压迫感 / 高饱和强调色) | PRD-4 §11 |
| **国际化文案等价性**(中英不假装同质但功能要等价) | PRD-4 §12 |
| **方案 B 镜子语言 + 塔罗双层视觉** | PRD-4 §11.5 |
| **C 方案国际化**(浏览器自动判定 + 手动切换) | PRD-4 §12 |
| **付费结构**(基础免费 / 轻 ¥4.9 / 完整 ¥9.9 / 决策包 ¥19.9) | PRD-4 §7 + §10.2 |
| **决策回访极简**(2 题 + 表情 + 90 天 + 只 push 一次) | PRD-4 §6.3 |
| **双反馈入口**(表单 + 一键 ☺️/😐/☹️) | PRD-4 §14 |

#### 14.6.3 来自 Tech Spec 锁定的工程约束

| 纪律 | 出处 |
|---|---|
| **AI 单次完整推演成本 ≤ ¥0.5** | Tech Spec §4.7 |
| **本地缓存范围**(§7.1 表格全部用户输入) | Tech Spec §7.1 |
| **接口契约**(§9 表格,不允许 teammate 单方面改) | Tech Spec §9 |
| **数据库 schema**(§3,改动必须 lead 协调) | Tech Spec §3 |

#### 14.6.4 必须 lead 决策(仍是 Wenbo)的事

任何 teammate 遇到以下情况立即 escalate:

| 场景 | 例子 |
|---|---|
| 产品方向调整 | "用户反馈想要 A,但 PRD 要的是 B,改不改?" |
| Idea 锁定后的硬约束改动 | "我觉得 Step 4 可以让 AI 替写一点,体验更好" |
| 外部 API 选型超预算 | "我想用 Claude Sonnet 4.6 做镜子凝练,贵 10 倍" |
| PRD-4 锁定纪律的修订 | "禁用词清单是不是太严了,我想去掉'命中'" |
| 一键反馈集中负面信号 | "Step 5 偏差审计的 ☹️ 占了 40%,要不要进 backlog?" |

#### 14.6.5 lead 可以自己决策的事(不需要找 Wenbo)

| 场景 | 例子 |
|---|---|
| 接口细节 | API 字段命名 / HTTP status code 选择 |
| 模块内实现选择 | 用 Pydantic 还是 dataclass / async 还是同步 |
| 测试用例补充 | 额外加 edge case 测试 |
| 性能优化 | DB query 加索引 / async 改写 |
| Refactor | 在不改契约前提下整理代码 |

---

## 15. 关键设计决策的"为什么"(Teammate 防漂移最后护栏)

每条决策的格式:**背景痛点 + 我们尝试的替代 + 最终选择 + 这个选择不能改的边界**。

### 15.1 为什么开场镜子用反思式塔罗而不是 AI 解牌

**背景痛点**:占卜产品的转化率高(用户喜欢被告知答案),但与"不预言"纪律直接冲突。完全不用塔罗会失去开场反思的具象触发力量。

**尝试的替代**:
- v1 完全去玄学(被批"丢了钩子");
- v2 主动认领反思塔罗(被认可)。

**最终选择**:**反思塔罗**——AI 让用户用塔罗"投射",不让 AI 用塔罗"算"。

**不能改的边界**:
- AI 永远不解读牌、不预测牌的含义;
- 主语永远是用户;
- 输出层有禁用词过滤;
- 任何想让"AI 主动告诉用户这张牌的意思"的提议都触及这条边界。

### 15.2 为什么原型只命名路径不分类用户

**背景痛点**:Jungian 原型如果用作"你是 X 类型的人",直接落入 Barnum / Forer 效应陷阱(MBTI 在学界被钉的事)。

**尝试的替代**:
- v1 给用户做"主导原型识别"(被批是 Barnum);
- 现版本完全去掉用户分类。

**最终选择**:原型只命名**这条路径的故事核**,不命名用户。

**不能改的边界**:
- 问卷不允许有"识别用户原型"的题;
- 用户档案不存"用户原型"字段;
- 原型必须从该路径的结构层数据可推导。

### 15.3 为什么 Step 4 用 5 档可能性 + 滑块而不是让用户填百分比

**背景痛点**:让真用户填具体百分比(如"35%")是认知摩擦极高的动作——他们没有 calibrated probabilities,会写假数字,认知干预没发生。

**尝试的替代**:
- v1 用户自填百分比(被批"我真填不出来");
- 现版本 5 档语言档位 + 滑块。

**最终选择**:用户认领"非常可能 / 比较可能 / 五五开 / 不太可能 / 几乎不会"5 档,系统映射到概率范围,用户可微调滑块。

**不能改的边界**:
- 必须是用户主动认领(不是 AI 替写);
- 这是产品核心认知干预——用户被迫直面自己的不确定性直觉。

### 15.4 为什么长期段不给具体事件

**背景痛点**:5 年后的世界、技术、用户都会变。任何号称"5 年后能告诉你具体事件"的产品都是在编故事——直接落入 Barnum 陷阱。

**尝试的替代**:无——这是产品认识论位置,不是优化空间。

**最终选择**:长期(5+ 年)只给**路径形态 + 故事核 + 方差形状**——这是关于路径性质的真实信息,不是关于具体事件的伪精确。

**不能改的边界**:
- 长期段任何"具体事件 / 具体场景 / 具体年份"输出都禁止;
- 用户期待"算 5 年后"的请求,文案教育引导(类比天气预报)。

### 15.5 为什么不进大陆 / 为什么仍然主要服务大陆背景中文用户

**背景痛点**:大陆监管严(《生成式 AI 服务管理暂行办法》)。但产品是中文为主,主要用户实际是大陆背景。

**尝试的替代**:
- 试图同时进大陆 + 海外(被批合规风险);
- 完全砍掉大陆背景用户(被 Wenbo 反对——主要用户群)。

**最终选择**:**官方境外 + passive 服务大陆 VPN 用户**(类似 ChatGPT / Notion / Discord 的标准 posture)。

**不能改的边界**:
- 不上大陆应用市场;
- 不接大陆境内支付通道;
- 不做大陆 SEO/投放;
- 但也不严格 IP-block 大陆访问。

### 15.6 为什么用国产廉价模型而不是 Claude / GPT-5

**背景痛点**:Claude / GPT-5 单次推演成本可能 $0.5+(¥3.5+),对 indie 100 付费用户的单位经济不合理。

**尝试的替代**:无——成本约束是硬约束。

**最终选择**:**DeepSeek / Qwen / Doubao / Kimi 实测后选定**——单次完整推演 ≤ ¥0.5。镜子凝练等需要细腻文笔的 step 用 Qwen-Max(贵但仍便宜于 Claude)。

**不能改的边界**:
- 不允许默认调 Claude / GPT-5(成本会失控);
- 模型 API 调用前必须经过成本预估(§4.7)。

### 15.7 为什么不做 native 英文 rewrite(英文是人工翻译)

**背景痛点**:Native 英文 rewrite 需要 native 英文 copywriter,成本高,且 v1 主用户是中文用户。

**尝试的替代**:
- 完全不做英文(失去 ABCs / 海外华人后代英文用户群);
- Native rewrite(成本不允许)。

**最终选择**:**英文是人工翻译版本**——质量优于机翻但不是 native rewrite。前期接受翻译腔。

**不能改的边界**:
- 中英功能等价(英文不是阉割版);
- 但视觉与文化色彩不强求等同;
- v6+ 评估是否做 native 英文重写。

### 15.8 为什么用 Web 而不是 native iOS / Android

**背景痛点**:native app 发版复杂、合规复杂(App Store 审核风险高,占卜类应用易被拒)、双端开发成本高。

**尝试的替代**:无——Web 是 indie 的最优起点。

**最终选择**:**v1 Web only**(响应式,桌面 + 移动浏览器)。

**不能改的边界**:
- 不写 React Native / Flutter / native Swift / Kotlin;
- 不上 App Store / Google Play;
- mobile-first 设计原则在移动浏览器里完整可用。

### 15.9 为什么镜子语言用方案 B(塔罗作为镜面上的具象物)而不是方案 A

**背景痛点**:开场镜子的产品价值依赖塔罗图像的"具象触发力量"。如果统一为镜面雾面(方案 A),会消解这部分价值。

**尝试的替代**:
- 方案 A:全产品同一套视觉语汇,塔罗作为镜面内浮现的元素(被否——丢失具象触发);
- 方案 B:全产品基调是浅紫雾面 + 镜面涟漪,塔罗牌作为"放在镜面上的具象物"出现(选定)。

**最终选择**:**方案 B**——保留传统牌面视觉的密度(用克制的现代化重绘版本),与底色形成柔和层次。

**不能改的边界**:
- 塔罗牌图像必须保留(不消解为镜面元素);
- 但风格必须是"克制的现代化重绘",不是传统 Rider-Waite 浓重风格;
- 牌面只在开场镜子环节出现,其他页面不出现。

### 15.10 为什么默认按浏览器语言判定、不按 IP 判定

**背景痛点**:大陆 VPN 用户的 IP 显示为美国 / 日本等,但他们读中文。如果按 IP 判定,会把他们错判到英文版,严重错位。

**尝试的替代**:
- IP 判定(被否——错判 VPN 用户);
- 强制用户首次访问时选语言(被否——破坏 onboarding)。

**最终选择**:**Accept-Language header 判定**——浏览器自带语言偏好通常准确反映用户母语。

**不能改的边界**:
- 不允许引入 IP geolocation 来判定语言;
- 用户手动切换的优先级最高(localStorage 覆盖判定结果)。

### 15.11 为什么错误时刻文案不能用技术语言

**背景痛点**:错误是 voice 最容易破功的地方——用户在使用产品的脆弱时刻(刚做完输入,期待结果),如果看到"500 Server Error / Network Failure / API Timeout",整个"陪你慢慢理"的氛围崩塌。

**尝试的替代**:
- 显示原始错误码(被否——破 voice);
- 显示模糊文案"请稍后重试"(被否——冷感);
- 完全 hide 错误(被否——用户不知道发生了什么)。

**最终选择**:**硬编码 voice 文案表**(§7.5 / PRD-4 §13.1)——错误时刻保持"陪你慢慢理"的语气,同时给用户明确下一步。

**不能改的边界**:
- 后端不返回原始错误码到用户面;
- 前端不允许自行写错误文案(必须从 ERROR_MESSAGES_* 取);
- code review 必须检查这一条。

---

## 16. PRD-4 标注的开放点处理结果汇总

| PRD-4 开放点位置 | 内容 | Tech Spec 处理结果 |
|---|---|---|
| §11.10 #1 颜色 token 体系 | 具体 hex 值 + 命名 | **Tech Spec §5.1 给定**(浅紫主色 #B8A4D4 等) |
| §11.10 #2 暗色模式 v1 是否做 | - | **Tech Spec §5.5 决策:v1 不做,v2+ 候选** |
| §11.10 #3 中文正文无衬线选型 | - | **Tech Spec §5.2.3 给定 fallback 链**(系统字体优先) |
| §11.10 #4 字体 fallback 链 | - | **Tech Spec §5.2 各字体均有 fallback** |
| §11.10 #5 TNR mobile fallback | - | **Tech Spec §5.2.4 给方案**:fallback to Georgia |
| §11.5 #6 镜子语言与塔罗模块协调 A vs B | - | **Wenbo 已锁定方案 B**;Tech Spec §5.3.6 工程实现 |
| §11.10 #7 动效曲线 token | cubic-bezier 参数 | **Tech Spec §5.4.2 给定** |
| §11.10 #8 reduced-motion 支持 | - | **Tech Spec §5.4.3 给方案** |
| §11.10 #9 镜面涟漪实现成本 | CSS / Lottie / Canvas | **Tech Spec §5.3.3 三方案对比 + v1 推荐 CSS 动画** |
| §11.10 #10 详细 Logo 设计稿 | - | **留给设计师产物**(Tech Spec 无法给 — 不做视觉设计) |
| §11.10 #11 Logo 适配 | 最小尺寸 / favicon / app | **留给设计师产物** |
| §11.10 #12 简繁字形 | 未镜 vs 未鏡 | **留 Wenbo 决策**(v1 默认简体即可,简繁同形不冲突) |
| §11.10 #13 镜子语言工程成本 | 性能影响评估 | **Tech Spec §5.3 各项已给评估,毛玻璃 backdrop-filter 在低端 Android 上可能慢,fallback 为静态色块** |
| §13.4 错误场景重试策略 | - | **Tech Spec §7.3 给定** |
| §13.4 本地缓存实现 | localStorage vs IndexedDB | **Tech Spec §7.1 决策:v1 用 localStorage** |
| §13.4 错误日志格式 | - | **Tech Spec §7.4 给定 schema** |
| §13.4 模型 API 多通道 fallback | - | **Tech Spec §4.4.2 给定 fallback 链** |
| §14.4 反馈表单技术实现 | 自建 vs 第三方 | **Tech Spec §8.1 决策:v1 自建** |
| §14.4 邮件接收方案 | - | **Tech Spec §8.2 决策:v1 Wenbo 个人邮箱** |
| §14.4 自动 alert 触发条件 | - | **Tech Spec §8.4 给定**(7 天窗口 + 30% 阈值) |
| §8.5 法务审核成本预算 | - | **留 Wenbo 决策**(取决于法务行情) |
| §8.5 决策包退款规则 | - | **留 Wenbo 决策**(建议:未用尽时按比例退,30 天内有效) |
| §8.5 GDPR DPA 签署对象 | - | **留 Tech Spec 后续阶段评估**(Stripe / Resend 已有标准 DPA;模型 API vendor 单独评估) |
| 主域名选哪个 | weijing.app / theotherpath.app / ... | **留 Wenbo 决策**(Tech Spec §11.5 列候选) |

### 16.1 v6+ 决策(明确推迟)

- 暗色模式;
- Native 英文 rewrite;
- Native iOS / Android;
- Non-Tarot 反思触发图(风景 / 抽象 / 诗);
- 紫微 / 易经 / 星盘 / 生辰八字;
- 第三种语言扩展;
- AI 解牌(永久不做,触及 §15.1 边界);
- 大陆官方上架(战略性永久不做)。

---

## 关于 Tech Spec 的最后一段话

Tech Spec 写到这里,**所有 PRD-4 锁定的方向都有了工程展开,所有开放点都有了处理方案**(给方案的给方案,留 Wenbo 决策的留出来,留设计师产物的明确点出)。

**剩下的事**:
1. **Wenbo review**:确认开放点的决策(主域名、决策包退款、简繁字形等);
2. **Lead 启动 Phase 1**:spawn 4 个 teammates 按 §14.3 task list 并行;
3. **跑起来**:HF Space 阶段 ~12 天到 MVP;
4. **首批 5-10 种子用户验证 → 50 用户 milestone → 100 付费用户 PMF 验证**。

如果 teammate 在实施过程中遇到 §14.6 不能动清单触发,或遇到产品级判断需要,**立即停手 escalate 给 lead → Wenbo**——idea 锁定 + PRD 锁定 + Tech Spec 锁定后,任何动这些纪律的事都不是工程问题,是产品问题。

未镜的产品灵魂——"陪你慢慢理一遍 / 不替你做决定 / 主语永远是你 / 未决定也可以"——在 Tech Spec 里通过文案表、prompt 模板、错误处理、视觉规范、不能动清单**层层落地**。任何工程实施都要回到这条灵魂去 check。

如果某个具体技术决策让你觉得"产品好像没那么贴心了 / 没那么允许了 / 没那么诚实了"——那个决策大概率错了。回去读 §15。
