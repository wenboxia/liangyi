# docs/ · 文档导览

这份文件是进入 Liangyi 方法论的入口。请按顺序读。

---

## 阅读顺序

### 1. `session-hygiene.md` · 操作规范

**先读这份**。

方法论在操作层面的核心规范——每一步用哪个 AI 窗口、为什么、产出什么文件。

关键内容：
- AI 窗口编号系统（Claude-1 到 Claude-4、DeepSeek-1/2、Kimi-1）
- "批判不改方案"原则：审查者只输出批判，修改由 Claude-2 基于人的指令执行
- P2 每一步审查的详细流程
- 常见错误（避免踩坑）

**方法论从"哲学原则"变成"可照做的工作流"，靠的是这份文档**。

### 2. `liangyi-workflow-refined.md` · 哲学基础和完整工作流

方法论的深度细化——包含：
- 核心哲学（AI 溶解 vs 替代）
- 认知场论类比及其失效点
- "为什么是 2 个 AI"的三重证明（信息论 + 认知科学 + SVD）
- "divergence 优先于能力"原理
- P0-P4 五阶段完整工作流
- 方法论门槛：证实才收录

术语已和 `session-hygiene.md` 统一（"签字" → "做出最终决策"、"家族" → "坐标"）。

### 3. `visualizations/` · 可视化资产

- `build_voyageguard_page.py` → `voyageguard-data.json`：从 `runs/` 的原始记录抽出案例数据
- `build_case_doc.py`：从上面的数据生成 [`case-voyageguard.md`](case-voyageguard.md)，数字不手抄
- `build_flow_mmd.py` → `flow-auto.mmd` / `flow-hitl.mmd`：两张纵向状态机图（auto / hitl 各一张），同时写进顶层 README（上下叠）和 `../web/index.html`（左右并排）。改图改脚本，不手改产物

旧的可视化页面（`liangyi_field_alive_v5.html`、`liangyi.html`、`voyageguard-retro.html`）和横向 SVG 版状态图脚本 `build_flow_svg.py` 已于 2026-09 退役至 `../archive/retired-2026-09/`，只作历史快照——里面的模型名和坐标标注是 2026-04 的旧分类。对外页面是 `../web/index.html`，线上 https://liangyi-five.vercel.app 。

### 4. `liangyi-auto-variant.md` · 全自动变种

方法论的衍生变种——为效率优先场景去掉了所有人工决策点。**只在任务涉及变种时才需要读**。

它和本体的关系有一条硬纪律：变种里出现的设计困难在变种内部解决，**不反向修改本体**（本体解释见 `liangyi-workflow-refined.md` 第十二章）。

变种目前是探索阶段、不是成熟方案——4 个场景的实证强度远不够本体的"被证实在大多数情况下有效"门槛。

### 5. 评测与实测（2026-09 新增）

- `case-voyageguard.md`：拿一个**已经做完的项目**倒回原始想法重跑一遍，和当年真实的返工清单对照。
  数字全部由 `visualizations/build_case_doc.py` 从运行数据生成。
- `evaluation.md`：凭什么信上面那个案例——污染防护、复判一致率、这轮自查抓到的五个解析 bug、
  拆台判定不稳定这条发现。
- `evaluation-layer-pivot.md`：为什么放弃「证明人工决策点必要」这个原目标（2026-09-08 决策记录）。

工程层的实现细节在 `../engine/PIPELINE.md`，二十条合规检验在 `../engine/VALIDATION.md`。

### 6. `longterm-and-reference.md` · 长期观察与理论借鉴

实战暴露但未到本体修订门槛的观察、以及外部学术 / 工业成果对方法论的引用 / 借鉴 / 反例对照。**实验性的问题记录和外部借鉴都放这里**——不混进本体文档、保持本体稳定性。

---

## 文档状态

**当前阶段**：方法论本体稳定；工程实现已完成并上线（`../engine/` + `../web/`，线上 https://liangyi-five.vercel.app ），评测层于 2026-09-08 转向后到此为止。

**持续演化**：方法论永远不会"完成"。未来可能有新洞察加入——这是常态，不是缺陷。

**修改原则**：
- 核心机制的新增或修改：必须经过深度讨论，不在讨论中直接改文档
- 术语统一化：等方法论下一次大版本时一起做（2026-04-23 版已完成"签字 → 做出最终决策"和"家族 → 坐标"两轮）
- 操作细节的补充：可以随时在 `session-hygiene.md` 里加

---

## 历史快照

- 2026-04-18：方法论深度思考日（认知场论、session hygiene、divergence 原理）
- 2026-04-19：迁移到当前 Cowork Project，开始落地阶段
- 2026-08-27：维度 A 判据整体更换——从"对齐算法路径"改为"冲突偏向"（A1 规范优先 / A2 权限优先 / A3 任务优先 + 未公开档）。起因是九家厂商复核发现头部厂商已停止公布 RL 算法，原判据不再可观测。**换的是判据、不是机制**；同时新增硬规则"维度 A 未公开的模型不进入方法论"。经过见 `../references/ai-training-landscape.md` 第五节
- 2026-08-30：项目重定位为思想层 + 工程层 + 评测层；开始把方法论做成可运行的 13 步链条
- 2026-09-08：评测层转向——放弃「用胜率证明人工节点有价值」，改为一次 VoyageGuard 回溯对照；四档 HITL 并为 `auto` / `hitl` 两档。记录见 `evaluation-layer-pivot.md`
- 2026-09-13：收束为可交付形态，推 GitHub、上线 Vercel
- 2026-09-15：网页两档 + 运行控制 + 两张状态机图定稿，交付形态定稿

未来的重要节点记录在这里。