# 实验 · ExamSniper 场景 · P2D-fix Kill shot 分级规则验证(场景一)

## 时间
2026-04-26

## 实验目的
为变种 P2D-fix 的新判定规则(Kill shot 分级,详见 `docs/liangyi-auto-variant.md` 第 5.2 节)做实战验证。

设计两个对照子实验,共享同一个 ExamSniper seed:

- **实验 X · 按老规则走主线**——P2D-fix 沿用 2026-04-24 实验的"强否定 + 实质支撑 → 回 P1 + 终止条件强制框架内"老规则,跑完 Round 1 + Round 2(预期 Round 1 触发回 P1、Round 2 终止条件兜底产出 v5-旧)
- **实验 Y · 按新规则走主线**——全新窗口、新 P0 输入只带最初 seed,P2D-fix 用 Kill shot 分级新规则(≥ 2 个 kill shot 才回 P1)。如果触发回 P1 走 Round 2,否则直接 Round 1 框架内产出 v5-新

实验 X 跑完后做 3 次事后小调用:

- D1 喂给新规则 prompt → 看新规则在 D1 上判几个 kill shot
- D2 喂给新规则 prompt → 看新规则在 D2 上判几个 kill shot
- D2 喂给老规则 prompt → 看老规则在 D2 上判定(D1 上老规则已用过、不再跑)

## 最后做 4 件比较

1. **议题敏感度**:D1 vs D2 的拆台内容是否 60% 重叠(印证 / 否证 `liangyi-auto-variant.md` 6.2 节"P2D 议题敏感度"假设)
2. **Kill shot 4 格判定矩阵**:D1 / D2 × 老规则 / 新规则 各自判几个 kill shot、是否触发回 P1
3. **v5 质量**:v5-旧(实验 X 终止条件兜底产出)vs v5-新(实验 Y 产出)哪个更站得住
4. **流程长度**:旧规则 2 轮 vs 新规则 1 或 2 轮

## 场景
ExamSniper——C 端、面向大学生期末备考的"以课件为锚 + 延伸补全"的考点狙击 AI 工具。相对前两个 B 端内部工具场景(美团风控 / Agent 评测平台),ExamSniper 提供 C 端付费场景下的对照——付费意愿不稳定、合规边界(课件版权 + 学术诚信)、和大模型 wrappers 的差异化都是该场景特有的张力源。

## 参数替换

| 参数项 | 替换内容 |
|---|---|
| **P1.1 专家 A 定位** | **应试效率派**——立场:学生付费就是为了应对考试,产品价值 = 在考前最短时间内,以最高效率把考试需要的考点和答案交付给学生。倾向解题模板化、答题套路化、考点-题型矩阵、自动判分;延伸补全的方向是"老师可能问的变式题、得分点拆解、答题模板"。现实流派对照:猿辅导 / 作业帮 / 新东方在线考研 |
| **P1.2 专家 B 定位** | **学习深化派**——立场:学生付费的深层动机是借"考试"把知识真正学懂,考试是手段不是目的。产品价值 = 用考点作为入口,引导学生回到课件深入理解原理。倾向 Socratic 引导、易错点解析、概念关联;延伸补全的方向是"理解这个考点的更深一层概念",反对直接喂答案。现实流派对照:Khan Academy / Coursera / 洋葱学院 |
| **P2A 批判视角** | C 端学习产品早期产品负责人 + VC 复合视角。关切维度:PMF 验证(期末考试是季节性需求,非考试季留存如何解决)、付费转化(大学生消费力 + ChatGPT/NotebookLM 这些低价/免费替代)、差异化(相对通用大模型的护城河,是 prompt 工程还是真有教研/数据壁垒)、合规风险(课件版权 + 学术诚信被定性"作弊工具"风险)、单位经济(联网检索 + 模型调用的推理成本能否撑 C 端定价) |
| **P2B 单盲对象** | 期末考试周的大三本科生——专业课课件密度高(经济 / 法学 / 医学 / 工科核心课其一)、期末同时有 4-6 门要应对、平时课件没认真看想速成、用过 NotebookLM 觉得课件之外什么都不答太死、用过 ChatGPT 觉得能答但答不出课件细节也不靠谱、备考时间紧容错率低 |
| **P3.1.1 用户反馈视角** | 双视角:主视角同 P2B 备考型大学生 + 对照视角"基础好的学霸型学生"(平时课跟得上、期末想再拔一把高分、对延伸的需求更多对答案模板的需求更弱) |
| **P3 PRD 评估指标** | 解答准确率(对照人工标注 + 课件考点)、延伸合理性(模型补充内容真考点率,衡量是真补全还是胡编)、溯源透明度(每条解答能否清晰指向课件页码或联网来源)、考点提取召回率、考后留存(衡量是不是只是"应急包")、免费→付费转化率、学术诚信触发率(老师 / 学校反对率) |

## 自动化替代清单(同前两次实验)

| 原人工决策点 | 位置 | 自动化替代 |
|---|---|---|
| 审 P0 精炼 | P0 末尾 | 跳过 |
| 综合两份专家方案 + 写执笔指令 | P1.3 | Claude-2 读两份方案自行综合 |
| 批判取舍(响应 / 忽略) | 2A-fix / 2B-fix / 2D-fix | Claude-2 自行判断,默认"能改则改" |
| 是否回退 | 2C-rollback | Claude-2 自行判断,默认"P2C 指出漂移就回退" |
| P2D 触发条件 | P2D 入口 | 强制触发 |
| 框架内 vs 框架级判定 | 2D-fix | 实验 X 用老规则、实验 Y 用 Kill shot 分级新规则(详见 prompts/) |
| idea.md 锁定 | P2/P3 边界 | 2D-fix 跑完自动锁 |

保留的硬规则:AI 窗口独立(Claude-1~4、DeepSeek-1/2、Qwen-1)、底模坐标跨维度(Claude A1·B1 + DeepSeek A4·B3 + Qwen A3·B3)、P2B 单盲零上下文 + prompt 纪律、P2D 拆台由 A3/A4 模型扮演。

## 实际执行路径(全部已完成)

**实验 X · Round 1**:已跑完——P2D-fix 老规则判回 P1(拆台稿 = D1)
**实验 X · Round 2**:已跑完——P2D-fix 老规则仍判回 P1(拆台稿 = D2),终止条件兜底强制产出 v5-旧
**3 次事后小调用**:已跑完——D1+新规则 / D2+新规则 / D2+老规则,产出在 post-analysis/
**实验 Y · Round 1**:已跑完(全新窗口、新 P0 输入只带 seed-idea.md)——新规则判 3 个 kill shot、回 P1
**实验 Y · Round 2**:已跑完——新规则判 4 个 kill shot、自由判断回 P1,终止条件兜底强制产出 v5-新

**核心结论**:6 次 P2D-fix 判定 6 次全判"回 P1",新旧规则零分歧。新规则的"≤1 kill shot 框架内消化"路径完全没被触发过——ExamSniper 是拆台密集的 seed。完整比较见 `meta-observations.md`。

## 档案清单

```
2026-04-26-examsniper-killshot-rule/
├── README.md                           (本文件)
├── seed-idea.md                        (P0 原始输入,所有实验 / Round 共享)
├── meta-observations.md                (4 件比较 + 跨场景对照,场景跑完后回填)
├── prompts/
│   ├── P2D-fix-old.md                  (老规则 prompt 副本,实验 X 用)
│   └── P2D-fix-new.md                  (Kill shot 分级新规则 prompt 副本,实验 Y 用)
├── experiment-X-old-rule/
│   ├── round-1/
│   │   ├── P0-refined.md
│   │   ├── P1A-expert-a.md
│   │   ├── P1B-expert-b.md
│   │   ├── idea-v1.md
│   │   ├── idea-v2.md
│   │   ├── idea-v3.md
│   │   ├── idea-v4.md
│   │   ├── P2A-critique.md
│   │   ├── P2B-blind-review.md
│   │   ├── P2C-review.md
│   │   ├── P2D-devils-advocate.md      (= D1)
│   │   └── P2D-fix-judgment.md
│   └── round-2/
│       ├── P0-refined.md
│       ├── P1A-expert-a.md
│       ├── P1B-expert-b.md
│       ├── idea-v1.md ~ idea-v5.md     (v5 = v5-旧,终止条件兜底产出)
│       ├── P2A-critique.md
│       ├── P2B-blind-review.md
│       ├── P2C-review.md
│       ├── P2D-devils-advocate.md      (= D2)
│       └── P2D-fix-judgment.md
├── experiment-Y-new-rule/
│   ├── round-1/
│   │   └── ... (P0 ~ P2D-devils-advocate + P2D-fix-judgment;若不触发回 P1 直接产出 idea-v5.md = v5-新)
│   └── round-2/                        (仅当 round-1 触发回 P1 才存在)
│       └── ...
└── post-analysis/
    ├── D1-with-new-rule.md             (D1 用新规则判的结果)
    ├── D2-with-new-rule.md             (D2 用新规则判的结果)
    └── D2-with-old-rule.md             (D2 用老规则判的结果)
```
