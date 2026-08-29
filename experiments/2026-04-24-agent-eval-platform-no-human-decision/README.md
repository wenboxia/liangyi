# 实验 · Agent 评测平台场景 · 无人工决策版方法论（第二次实验）

## 时间
2026-04-24

## 实验目的
对 2026-04-23 美团实验的对照实验——上次发现 P2D-fix 存在结构性死循环，本次在 P2D-fix 的判定规则里加了显式终止条件，观察：

1. 终止条件能否避免死循环
2. 如果第一次 P2D-fix 仍然触发回 P1，第二次 P2D-fix 强制走框架内修改能否跑出 v5

## 场景
Agent 评测平台——一个内部工具型产品。相比美团风控场景更简单、更技术驱动、更少监管面，作为对上次场景的轻量对照。

## 参数替换
相对方法论默认 persona / 指标的替换：

- **P1.1 专家 A 定位** → AI 评估与可观测性领域专家，偏"通用评测框架派"
- **P1.2 专家 B 定位** → Agent 工程与业务适配领域专家，偏"任务定制化评测派"
- **P2A 批判视角** → 团队工程负责人 / 技术 Lead（关切：信度效度、工具采用率、工程投入产出比、对比 LangSmith/Langfuse 或简易脚本的适配成本、评分可操作性）
- **P2B 单盲对象** → 团队里的一名 AI 工程师
- **P3.1.1 用户反馈视角** → 团队里的产品经理，负责几个 AI Agent 产品线
- **P3 PRD 评估指标** → 评测报告的信度（同一 Agent 多次跑分稳定性）/ 效度（评分与线上指标相关性）/ 工具采用率（DAU·WAU）/ 迭代周期影响（上线前测试到问题定位的时间压缩）/ 扣分原因可操作性（扣分直接指向优化动作的比例）

## 相对上次实验的变化

**唯一改动**：P2D-fix 规则加入终止条件——

- 第一次 P2D-fix：保持原规则（"强否定 + 实质支撑 → 回 P1"）
- 第二次 P2D-fix（从 P1 重新跑完到 P2D-fix 时）：**不论 P2D 说什么都走框架内修改，强制产出 v5**

其他所有自动化替代与上次一致：

| 原人工决策点 | 位置 | 自动化替代 |
|---|---|---|
| 审 P0 精炼 | P0 末尾 | 跳过 |
| 综合两份专家方案 + 写执笔指令 | P1.3 | Claude-2 读两份方案自行综合 |
| 批判取舍（响应 / 忽略） | 2A-fix / 2B-fix / 2D-fix | Claude-2 自行判断，默认"能改则改" |
| 是否回退 | 2C-rollback | Claude-2 自行判断，默认"P2C 指出漂移就回退" |
| P2D 触发条件 | P2D 入口 | 强制触发 |
| 框架内 vs 框架级判定 | 2D-fix | 规则化 + 循环终止条件（见上） |
| idea.md 锁定 | P2/P3 边界 | 2D-fix 跑完自动锁 |

保留的硬规则：AI 窗口独立、底模坐标跨维度（Claude A1·B1 + DeepSeek A3/A4·B3 + Qwen A3·B3）、单盲零上下文 + prompt 纪律、拆台由 A3/A4 路径模型扮演。

## 实际执行路径（截至归档时）

**Round 1**：P0 → P1.1 → P1.2 → P1.3+1.4（合并） → P2A → P2A-fix → P2B → P2B-fix → P2C → P2C-rollback → P2D → **P2D-fix 规则判定触发回 P1**

**Round 2**：**已跑完**——走**路径 1（最严格自动化）**。新 P0 输入 = `seed-idea.md` 唯一一份，不带 Round 1 的 P2D 拆台 / P2D-fix 判定。所有窗口新开。P2D-fix 为第 2 次 → 终止条件生效、强制走框架内修改，产出完整 v1→v5 五版演进链（观察见 meta-observations.md 观察四~十）。

路径 2（半规则化：seed + P2D-fix 判定）、路径 3（承认人决策）**未跑**——路径 1 已跑通完整闭环，没有触发跑这两条的必要（见 meta-observations.md "Round 2 的设计缺口"）。

## 本次实验的新观察

见 `meta-observations.md`。核心两条：

1. 终止条件没根治 P2D-fix，只限制了循环次数——第一次仍然触发回 P1，和上次美团实验同构
2. Claude-2 的元认知倾向被二次印证——同样分类、同样指层级、同样列根问题

## 档案清单

```
2026-04-24-agent-eval-platform-no-human-decision/
├── README.md                          (本文件)
├── meta-observations.md               (已填，含 Round 1 + Round 2 完整观察)
├── seed-idea.md                       (已填，P0 原始输入；所有 Round 共享)
├── prompts/                           (本次实验定制 prompt 归档)
│   └── P2D-fix-rule.md                (已填，核心新增变量：判定规则 + 终止条件)
├── round-1/                           (第一轮产出归档)
│   ├── P0-refined.md                  (已填)
│   ├── P1A-expert-a.md                (已填)
│   ├── P1B-expert-b.md                (已填)
│   ├── idea-v1.md                     (已填)
│   ├── idea-v2.md                     (已填)
│   ├── idea-v3.md                     (已填)
│   ├── idea-v4.md                     (已填)
│   ├── P2A-critique.md                (已填)
│   ├── P2B-blind-review.md            (已填)
│   ├── P2C-review.md                  (已填)
│   ├── P2D-devils-advocate.md         (已填)
│   └── P2D-fix-judgment.md            (已填)
└── round-2/                           (路径 1 · 已跑完，v1→v5 完整链)
    ├── P0-refined.md
    ├── P1A-expert-a.md
    ├── P1B-expert-b.md
    ├── idea-v1.md
    ├── idea-v2.md
    ├── idea-v3.md
    ├── idea-v4.md
    ├── idea-v5.md                     (第二次 P2D-fix 强制产出)
    ├── P2A-critique.md
    ├── P2B-blind-review.md
    ├── P2C-review.md
    ├── P2D-devils-advocate.md
    └── P2D-fix-judgment.md
```
