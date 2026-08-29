---
文件性质: 派生摘要（derived）
数据快照: 2026-08-27
来源: 各厂商公开一手材料（官方技术报告 / 论文 / model card / system card / 官方规范文本）；来源规则于 2026-08-27 变更，原 `../model-learning-strategy.txt` 保留为 2026-04 历史快照、不再作为来源
重写策略: 每次从一手资料检索后整篇重写覆盖本文件，不累积历史版本、不做增量修改
用途: 记录当前（2026-08）全球主流旗舰模型的对齐目标与规范约束现状，纯外部观察，不与 Liangyi 方法论本体耦合
---

# 底模坐标 landscape（2026-08 快照）

## 0. 如何阅读这份文档

- 这份文件是对各厂商公开一手材料的综合整理，不代表任何单一厂商的官方立场。
- 分类基于**二维坐标**：冲突偏向（维度 A）× 语料文化（维度 B）。
- **本快照相对 2026-04 有一次重大变更：维度 A 的分类依据整体更换**。原版按对齐算法路径分四档（A1 Constitutional+RLAIF / A2 传统 RLHF / A3 GRPO 家族 / A4 RLVR）。该分法在 2026-08 已失效，原因见第四节。
- 厂商随时会改自己的训练与部署配置，标签会动。本文档只代表 2026-08 这一快照。
- 需要更新时，从公开一手资料重新检索后整体重写本文件，不在末尾追加。

---

## 1. 维度 A · 冲突偏向（Conflict Bias）

**定义**：当任务要求和其他约束冲突时，这个模型默认倒向哪边。

**判据**：训练时的奖励信号设计 + 出厂后叠加的规范层，两样合起来看。证据必须是一手材料——官方技术报告、system card、公开的规范文本（宪法 / Model Spec / safety policy）、官方 system prompt。

**为什么把出厂后叠加的规范层也算进来**：厂商在权重之外还会叠东西——公开发布的 system prompt、带版本号的行为规范文档、运行时的内容分类器。使用者通过网页或 API 访问模型时，这一层始终在，绕不过去。它和训练层是同一件事的两种形态：都是独立于当前任务的规范约束，都会在关键处把手拉住。而且这一层比训练算法更可观测——规范文本是公开的，RL 算法现在多数厂商已不披露。

### A1 · 规范优先

训练目标里存在一份独立于任务的成文规范，且冲突时规范压过任务。

- **识别特征**：存在公开成文的价值规范或安全策略文本；该文本被明确声明用于生成训练信号或运行时约束；官方表述里存在"某项价值优先于有用性"这类排序
- **对使用者的含义**：它会主动做价值判断，不只执行任务；在被要求扮演极端角色时，规范层会在最关键处把攻击软化掉

### A2 · 权限优先

规范存在，但形态是"谁说了算"的排序，不是价值命题。冲突时按权限链裁决，不自己做价值判断。

- **识别特征**：存在公开的指令层级 / 权限链定义；规范文本描述的是"哪一层的指令优先"，而不是"什么是好的"
- **对使用者的含义**：给它明确授权它就照做，比 A1 更容易被 persona 推动；但运行时的拦截层仍在，极端角色仍受限

### A3 · 任务优先

公开材料里找不到独立于任务的规范层。奖励信号全部来自任务完成度——可验证任务用规则和测试用例，开放任务用 rubric + 生成式奖励模型。

- **识别特征**：技术报告中无 safety alignment / harmlessness 章节；"alignment" 一词只在技术含义下出现（模态对齐、logits 对齐等）；奖励设计围绕任务是否完成得好
- **对使用者的含义**：没有一层价值观拉住它，让它拆台它就真拆；也意味着它不会主动替你把关

### 未公开

厂商不披露后训练目标，也无公开规范文本，**无法判定坐标**。

按方法论 2026-08-27 的裁定：**A 维度未公开的模型不进入方法论的任何窗口**。理由不是这些模型不好，而是方法论要求选型依据可解释——用一个说不清它为什么会那样反应的模型，等于把判断权交回给运气。

---

## 2. 维度 B · 语料文化（Corpus Culture）

本维度 2026-08 复核无变化。

- **B1 · 英文母语**：Claude、GPT、Gemini
- **B2 · 中文母语**：GLM、豆包、ERNIE
- **B3 · 跨文化双核**：DeepSeek、Kimi、Qwen、MiniMax

语料文化决定的是"默认的问题意识、价值判断的起点、举例时脑海里浮现的场景"。做中国本地产品时，B1 和 B2/B3 的默认先验差异会直接暴露。

**B 维度比 A 维度稳定**：它由预训练语料决定，不随厂商的对齐配置调整而变，也不依赖厂商披露——直接用就能感知。

---

## 3. 厂商现状（2026-08）

### Anthropic · Claude — A1 · B1

- **当前旗舰**：Claude Fable 5（2026-06 发布）。同代另有 Claude Opus 5（2026-07-24）与受限访问的 Claude Mythos 5；Opus 5 的 system card 明确写它"整体能力并未超过我们能力最强的通用可访问模型 Claude Fable 5"
- **规范层**：公开成文宪法（2026-01 改版，全文 PDF 公开），明确排序"无害性 ≥ 有用性"；用宪法生成合成训练数据（含符合价值观的回答与回答排序），自承是 2023 年 Constitutional AI 的演进
- **部署层**：cybersecurity classifiers 作为核心保障层；官方公开发布 Claude 的 system prompt
- **方法披露程度**：具体 RL 算法（RLHF / RLAIF / PPO 的使用与配比）**未公开**。system card 只写"大量后训练与微调，目标是对齐宪法价值"
- **2026-05 另有一篇方法研究**《Teaching Claude Why》：教原理而非教示范、difficult-advice 数据集、多样化系统提示增强泛化。该文未声明已用于当前旗舰

### OpenAI · GPT — A2 · B1

- **当前旗舰**：GPT-5.6（2026-07-09，旗舰档位代号 Sol）
- **规范层**：Model Spec，现行版本 2026-08-18，定义 Root > System > Developer > User > Guideline 权限链
- **部署层**：activation classifiers（生成过程中介入阻断，本代新增）、reasoning monitor（用测试时推理做实时审查，可快速更新而无需重训分类器）
- **方法披露程度**：只写"通过强化学习训练推理"。RLHF、PPO/GRPO、RLVR、过程监督等具体算法名**未在一手材料中出现**。safe-completions 与 deliberative alignment 在 GPT-5.5 / 5.6 的 system card 中均未再作为方法名出现，是否仍在使用**未公开**

### Google · Gemini — A1 · B1

- **当前旗舰**：Gemini 3.1 Pro（2026-02-19）为 Pro 档最强；最新发布的是 Gemini 3.7 Flash（2026-08-13）。官方模型页标注 3.5 Pro coming soon，尚未发布
- **规范层**：safety policies and desiderata；Frontier Safety Framework v3.x 分级；**consequence-aware risk analysis**（2026-08 的 FSF 报告自称"a new framework"，教模型预判长期危害并选择可控风险的策略）
- **方法披露程度**：明确写使用 RLHF 与 SFT；"reinforcement learning from human and critic feedback"。RLAIF、RLVR、过程监督**未公开**
- **归 A1 的依据**：后果分级规范会覆盖任务目标——冲突时它算的是"这么做会导致什么"，不是"任务要求我做什么"

### DeepSeek — A3 · B3

- **当前旗舰**：DeepSeek-V4-Pro-0813（2026-08，1.6T 总参 / 49B 激活，MoE，1M 上下文）
- **一手技术报告**：arXiv 2606.19348《DeepSeek-V4》，2026-04-26 提交，第 5 节 Post-Training 是当前唯一的方法来源
- **后训练方法**（全部为论文原文）：
  - GRPO **仍在用**，超参"与既往研究基本一致"，但只用于训练**各领域专家模型**
  - 原来的 mixed RL 主干阶段"**被 On-Policy Distillation 完全取代**"——十余个教师模型蒸馏为单一学生模型，reverse KL，full-vocabulary logit distillation
  - 奖励侧**明确弃用标量奖励模型**：原文写"在 DeepSeek-V4 系列的后训练阶段，我们摒弃了这类传统的基于标量的奖励模型"，改用 rubric-guided RL 数据 + 生成式奖励模型（GRM），并对 GRM 本身直接做 RL
  - 易验证任务用规则验证器或测试用例；人类标注被压缩到"minimal set of diverse human annotations"
  - 后训练阶段做 FP4(MXFP4) 量化感知训练
  - 全文未出现 PPO / GSPO / DAPO / CISPO；RLHF 仅出现一次，用于说明"我们不走这条路"；过程奖励模型（PRM）完全未提及
- **归 A3 的依据**：技术报告**无 safety 章节**，"alignment" 三次出现均为技术含义（domain-aligned、logits-level alignment）。安全对齐流程未公开
- **注意**：0731 / 0813 / Vision-Exp 三次发布均未披露后训练方法改动，model card 直接指回 4 月的技术报告

### 月之暗面 · Kimi — A3 · B3

- **当前旗舰**：Kimi K3（技术报告 arXiv 2607.24653，2026-07-27 提交；2.8T 总参 / 104B 激活，1M 上下文，原生多模态，权重公开）
- **后训练方法**：三阶段范式 SFT → 领域专家 RL → Multi-Teacher On-Policy Distillation（MOPD）。RL 跨 general / general agents / coding agents 三大域 × 三档 reasoning effort，共九个专家模型再由 MOPD 合并
- **策略优化算法未点名**：只写"沿用 Kimi K2.5 的算法"。K2.5 报告写的是 token-level clipping，严格依赖 log-ratio 约束 off-policy 漂移，明确区别于 PPO clipping
- **奖励设计**：可验证任务用 rule-based outcome reward；不可验证任务用 Agentic Generative Reward Model——tournament-style 分组奖励 + 强制 judge 协议（读产出 → 生成 rubric → 逐候选打分 → 写 scorepad），配 budget-based verbosity control 防 reward hacking
- **归 A3 的依据**：K3 报告**无 safety alignment 小节**；RLHF 与人类偏好数据规模未公开

### 智谱 · GLM — A3 · B2

- **当前旗舰**：GLM-5.3（2026-08-14，API 已全量可用，1M 上下文；权重官方称"两周内开源"，截至 2026-08-27 尚未开放）。同期另有 GLM-5.3-Flash（320B/18B，原生多模态，MIT 许可）
- **后训练方法**：官方原文"GLM-5.3 我们只做了后训练的规模化，base model 与 GLM-5.2 相同，全部收益来自后训练"
  - **SAO（Single-rollout Asynchronous Optimization）**：用单 rollout 采样**取代 GRPO 的组采样**，配 value-model 训练设计与双侧 token 级 clipping
  - multi-teacher On-Policy Distillation（动态 teacher 切换 + prefetch）
  - slime 异步 RL 框架；环境端到端合成 + judge agent 生成部分 RL 奖励信号（官方自陈仍需大量 human-in-the-loop）
- **归 A3 的依据**：安全对齐流程**未公开**；奖励来自合成环境与 judge agent，无独立价值规范层
- **注意**：GLM-5.3 无独立技术报告，官方引用仍是 GLM-5 报告（arXiv 2602.15763）

### 阿里 · Qwen — 未公开 · B3

- **当前旗舰**：Qwen3.8-2.4T-A95B（2026-08-12 开源权重）/ Qwen3.8-Max（闭源商用）
- **方法披露程度**：**无技术报告 / 无 arXiv 论文**。model card 关于后训练仅一行 "Training Stage: Pre-training & Post-training"，无任何算法、奖励或数据描述
- **辨伪提醒**：QwenLM GitHub README 里出现的 "SFT, DPO, GRPO" 位于 Finetuning 章节，是**推荐用户用第三方工具去微调模型**，不是 Qwen 自身的训练方法，不能当证据
- **相对 2026-04**：Qwen3.6 与 Qwen3.8 均无技术报告，两代对齐路径在一手材料中都无描述，不存在可比对的公开信息

### 字节 · 豆包 / Seed — 未公开 · B2

- **当前旗舰**：Seed2.1 / Doubao-Seed-2.1-Pro（2026-06-23）。火山方舟平台另标注"最新模型：Seed-Evolving"（取消版本号、持续演进式交付），但该模型在 Seed 官方博客与论文列表中均无对应材料
- **方法披露程度**：**无技术报告**。官方博客中唯一与后训练相关的一句是"通过强化学习引导 agent 在 GUI 与非 GUI 动作空间中自然选择最优动作"，未点名任何算法
- **辨伪提醒**：博客中的 "human preference evaluation" 是评测榜单排名，不是训练用的人类偏好数据，不能作为 RLHF 的证据

### MiniMax — 未公开 · B3

- **当前旗舰**：MiniMax-M3（2026-06-01，约 428B 总参 / 23B 激活，1M 上下文，权重公开）
- **方法披露程度**：M3 技术报告（arXiv 2606.13392）只讲 MiniMax Sparse Attention 架构，**摘要与正文均无 post-training / RL / reward / alignment 内容**；model card 只有部署参数
- **上一次方法披露在 M2.5 时代（2026-02）**：CISPO 为核心算法、Unified Mixed-Domain Training、Process Reward、Task Completion Time Reward、Forge agent-native RL 框架
- **M3 是否仍使用 CISPO / Forge：未公开，不可推断**。可确认的只有披露程度显著下降

---

## 4. 坐标速查表

| 厂商 / 模型 | 维度 A | 维度 B | 坐标 | 方法论可用性 |
|---|---|---|---|---|
| Anthropic Claude | A1 规范优先 | B1 英文母语 | A1·B1 | 可用，不可担任 P2D |
| Google Gemini | A1 规范优先 | B1 英文母语 | A1·B1 | 可用，不可担任 P2D |
| OpenAI GPT | A2 权限优先 | B1 英文母语 | A2·B1 | 可用，不推荐担任 P2D |
| DeepSeek | A3 任务优先 | B3 跨文化双核 | A3·B3 | 可用，P2D 首选 |
| 月之暗面 Kimi | A3 任务优先 | B3 跨文化双核 | A3·B3 | 可用 |
| 智谱 GLM | A3 任务优先 | B2 中文母语 | A3·B2 | 可用 |
| 阿里 Qwen | 未公开 | B3 | — | 不进入方法论 |
| 字节 豆包 / Seed | 未公开 | B2 | — | 不进入方法论 |
| MiniMax | 未公开 | B3 | — | 不进入方法论 |

---

## 5. 本次快照相对 2026-04 的关键变化

### 变化一 · 维度 A 的原分类依据整体失效

原维度 A 按对齐算法路径分四档。2026-08 这套分法有三个问题，因此整体更换：

1. **A1 / A2 不再可观测**。Anthropic、OpenAI、Google 三家的最新 system card **都不再公布 RL 算法**，披露重心转向"评测结果 + 部署期拦截层"。已经无法从一手材料判定某家用的是 Constitutional+RLAIF 还是传统 RLHF。
2. **A3 / A4 不再互斥**。DeepSeek、Kimi 现在**同时**使用可验证奖励（数学、代码用规则和测试用例）与生成式奖励模型（开放任务用 rubric + GRM），按任务类型分流而非选择路线。"纯 RLVR"作为独立路线已不存在。
3. **A3 的定义不再有区分度**。GRPO 已成为公共基础设施，各家都在改它——智谱换成 SAO、Kimi 用自研 token 级 clipping、MiniMax 用 CISPO。"有没有自研策略优化算法"无法再区分任何两家。

新的维度 A 改按"冲突时倒向哪边"划分，判据是训练奖励设计 + 出厂后规范层，两者都取一手材料。这套判据不随算法演化失效——算法怎么变，"这家有没有一份公开的独立规范"这个事实是稳定的。

### 变化二 · 头部中国厂商的后训练形状高度趋同

DeepSeek、智谱、Kimi 三家独立走到了同一个范式：

> SFT → 领域专家分头 RL（可验证任务用规则 / 测试奖励，开放任务用 rubric + 生成式奖励模型）→ 多教师 On-Policy Distillation 合并成单一模型

这不是互相抄，是三份独立的技术报告呈现出同一形状。它同时解释了为什么这三家都落在 A3：这套范式里没有给"独立于任务的价值规范"留位置。

### 变化三 · 整体披露量下降

九家里只有 DeepSeek、Kimi、GLM 三家仍公开后训练方法细节。美国三家转向"只讲评测与部署防护"；Qwen、豆包、MiniMax 的当前旗舰完全没有方法披露（Qwen3.8 与 Seed2.1 无技术报告，MiniMax M3 的报告只覆盖注意力架构）。

---

## 6. 灰线观察（未入本体）

**"顺从用户倾向"是否应作为维度 A 的第四条方向**——即模型在用户表达立场后是否倾向于顺着用户的思路走。

现状：一手材料中**无任何证据**支持给某一家打这个标签。厂商不会在技术报告里描述这种倾向。目前只有使用中的行为直觉。

按方法论"证实才收录"的门槛，暂不入本体。待 Phase 2 消融评测实验跑多模型时顺手观察，有证据再议。

---

## 附录 · 一手来源

**Anthropic**
- https://platform.claude.com/docs/en/models/overview
- https://www.anthropic.com/news/claude-fable-5-mythos-5
- Claude Fable 5 & Mythos 5 System Card（www-cdn.anthropic.com）
- Claude Opus 5 System Card（www-cdn.anthropic.com）
- https://anthropic.com/news/claude-new-constitution ＋ 宪法全文 PDF
- https://www.anthropic.com/research/teaching-claude-why

**OpenAI**
- https://openai.com/index/gpt-5-6/
- https://deploymentsafety.openai.com/gpt-5-6/gpt-5-6.pdf
- https://model-spec.openai.com/2026-08-18.html

**Google DeepMind**
- https://deepmind.google/models/gemini/
- https://deepmind.google/models/model-cards/gemini-3-1-pro/
- Gemini 3 Pro Model Card / Gemini 3.7 Flash FSF Report（storage.googleapis.com/deepmind-media）

**DeepSeek**
- https://arxiv.org/abs/2606.19348 ＋ https://arxiv.org/html/2606.19348v1
- https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro-0813

**月之暗面 Kimi**
- https://arxiv.org/abs/2607.24653 ＋ https://arxiv.org/html/2607.24653v1
- https://arxiv.org/html/2602.02276v1（K2.5，算法血统）
- https://huggingface.co/moonshotai/Kimi-K3

**智谱 GLM**
- https://z.ai/blog/glm-5.3
- https://arxiv.org/abs/2607.07508（SAO）
- https://arxiv.org/html/2602.15763v1（GLM-5 技术报告）

**阿里 Qwen**
- https://huggingface.co/Qwen/Qwen3.8-2.4T-A95B
- https://github.com/QwenLM/Qwen3.8

**字节 Seed**
- https://seed.bytedance.com/en/blog/seed2-1-officially-released-advancing-ai-productivity
- https://seed.bytedance.com/en/public_papers

**MiniMax**
- https://arxiv.org/abs/2606.13392
- https://www.minimax.io/blog/minimax-m3
- https://www.minimax.io/blog/forge-scalable-agent-rl-en-1779896141（M2.5 时代 CISPO）
