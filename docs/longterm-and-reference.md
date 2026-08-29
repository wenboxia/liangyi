# 长期观察与理论借鉴

> 这份文件分两大块——
>
> - **长期观察**：实战中已经撞到、但还未到本体修订门槛的现象与候选观察
> - **理论借鉴**：从外部学术 / 工业成果对方法论的引用 / 启发 / 反例对照
>
> 两类内容都不进本体文档（`session-hygiene.md` / `liangyi-workflow-refined.md` / `liangyi-auto-variant.md`）——本体保持稳定性、这份文件作为"待证据成熟才考虑回灌本体"的缓冲带。
>
> **新的实验观察、新的外部借鉴、都放到这份文件里**——避免本体被未经证实的内容污染。

---

## 长期观察（待证据成熟再决定是否进入本体）

这一节记录已经撞到、但现在不到本体修订门槛的观察。等更多实战证据再决定如何处理。

### 面试价值标签（2026-08-27 加）

每条观察前标了一个标签，服务于 Phase 3 写面试叙事时的取舍。标签只影响"面试讲不讲"，**不影响这条观察本身的方法论地位**——没有任何一条因为标签被删除或降级。

- **〔面试主证据〕**——能直接讲的硬料，五分钟叙事里就该出现
- **〔面试可选〕**——被追问时才拿出来，不进主线
- **〔面试别提〕**——变种自己制造的问题的解。这些问题只在"把人从流程里拿掉"之后才存在，本体里没有。讲它们会让听众以为方法论本身有 bug，而澄清"那是我故意拆掉人工决策才有的"要花掉宝贵的时间

**关于〔面试别提〕这批的元层用法**：终止条件、Kill shot 分级、议题敏感度假设这三样，正确的讲法不是逐条介绍，而是当作一次证伪尝试的注脚——"我跑了四次实验想把人从方法论里拿掉，终止条件和 Kill shot 分级都是为了绕开'人不可少'这个结论打的补丁，最后发现绕不过去。"一句话说完，然后回到主线。它们的价值在于**证明了方法论的核心立场经得起自己的攻击**，不在于它们各自的技术细节。

### 0. 「顺从用户倾向」是否该成为维度 A 的第四条方向（2026-08-27 立）

**〔面试可选〕** 被问"你的坐标框架还在演化吗"时可用——它是一个诚实的开放问题，且有明确的验证计划（Phase 2 消融实验）。

现象：有些模型在用户表达立场之后，倾向于顺着用户的思路走，而不是独立判断；另一些（典型如 Claude）会主动挑用户想法的毛病。这两件事看起来相关，实际是两个不同的量——"愿不愿意主动提异议"和"被推的时候会不会改立场"。P2D 关心的是后者。

为什么现在不进本体：**一手材料里没有任何证据**支持给某一家打这个标签。厂商不会在技术报告里描述这种倾向。目前只有使用中的行为直觉，达不到"证实才收录"的门槛。

下一步：Phase 2 消融评测实验要跑六个场景 × 多个模型，那是天然的观测场。跑完看有没有可复现的模式，有证据再议。如果证实，它可能成为维度 A 的第四条方向，也可能被追认为 A1/A3 已经解释的现象的一个侧面——由届时的证据决定。

### 1. 新版 AI 普遍不公开训练细节 ✅ 已兑现（2026-08-27）

**〔面试主证据〕** 这是"模型换代了你的方法论怎么办"的最佳答案——不是嘴上说的，是真发生过一次并处理掉了：四个月前预判到、四个月后应验、方法论据此换掉判据但机制一个没动。和第 2 条是同一个故事。

> **结果**：这条观察在四个月后完全应验，并直接触发了维度 A 的判据更换。2026-08 复核九家厂商发现：Anthropic、OpenAI、Google 的最新 system card 都不再公布 RL 算法，A1/A2 已无法从一手材料判定；Qwen、豆包、MiniMax 的当前旗舰完全没有技术报告。方法论的应对不是"找替代判断方式"，是**把判据整体换成不依赖算法披露的东西**（冲突偏向：查厂商有没有一份公开的、独立于任务的规范文本），并把"未公开"定为不可用档位。详见 `session-hygiene.md` 原则四与 `../references/ai-training-landscape.md` 第五节。下面是这条观察当初的原文，保留备查。



方法论依赖"知道每个底模的对齐路径来配 P2 跨维度"。最新模型这个依赖会越来越难落地。

实例（2026-04-25）：
- DeepSeek 网页"专家模式"官方未公布具体调用哪个模型，外界只能猜测 V4 或 V3.2 + R1 融合
- Qwen3.6-Plus 无独立技术报告；主报告（Qwen3 系列 arXiv:2505.09388）粒度不足以严格归类对齐路径

含义：未来如果新版 AI 普遍不公开训练细节，"按底模坐标配 P2 链条"的硬规则在最新模型上会逐渐不可执行。可能需要替代判断方式（行为级测试、第三方推断等），但不立刻动。

### 2. A 维度框架本身可能需要重审 ✅ 已兑现（2026-08-27）

**〔面试主证据〕** 同第 1 条，一起讲。重点是"本体 vs 参考分离"这条纪律在真实压力下生效了——过期的是参考，本体没被动摇。

> **结果**：这条观察被证实，且比当初预计的更彻底——A 维度不是"边界条件需要重审"，是整套分类依据失效，已于 2026-08-27 整体更换。当初记下的三条技术事实全部成立：GRPO 与可验证奖励的边界确实模糊（现在各家是按任务类型分流，不是选路线）；生成式奖励模型确实让 RLAIF 思想不再是 Anthropic 独有；蒸馏确实覆盖不到（DeepSeek、Kimi、GLM 现在的主干都是 On-Policy Distillation）。新判据见 `session-hygiene.md` 原则四。下面是原文，保留备查。



来自 2026-04-25 让 DeepSeek 自评分类时它指出的几条真技术事实（不含它带立场的部分）：

- GRPO 既是 A3 算法创新、又用于实现 A4 的可验证奖励——A3 和 A4 边界天然模糊
- DeepSeek V4 用 Generative Reward Model（GRM）是 RLAIF 思想的实现——A1 不再是 Anthropic 独有
- 蒸馏（如 V4 的 On-Policy Distillation）作为对齐路径在现有 4 个标签里覆盖不到

含义：A 维度框架（A1-A4）的边界条件可能需要重审。但这是大改动，三次实战没暴露 A 维度框架问题——不立刻动，等更多实战证据。

### 3. "公司 → 单一坐标"映射粒度不准 ✅ 已消解（2026-08-27）

**〔面试可选〕** 技术细节，被追问"你这个坐标怎么打"时才讲。

> **结果**：这个问题随维度 A 换判据而消失，不需要"把坐标颗粒度降到产品线"。原因是新判据（有没有一层独立于任务的规范）是**厂商级**的属性——宪法、Model Spec、safety policy 是整个厂商的，不是某条产品线的。旧判据是算法级的，同一家不同产品线用不同算法，才会撕裂成 A3+A4+A2。换判据之后"公司 → 单一坐标"重新成立。下面是原文，保留备查。



DeepSeek 已证（V3 是 A2、R1 是 A3+A4+A2、V4 还融合 A1）。OpenAI（GPT-4 vs o1 系列）、Google（Gemini 系列）大概率有同样问题——多产品线很可能跨多个对齐路径。

docs 现在"公司 → 单一坐标"的映射对所有跨多路径的公司都不准。

含义：如果将来要细化，需要把坐标颗粒度从"公司"降到"产品线"。当前最小修复（2026-04-25 已做）只把 DeepSeek 的 A3/A4 双重出现标清楚是同系列不同产品的体现，没做全面的产品线坐标表。

### 4. P2D 议题敏感度可能是场景依赖（不是普遍规律）

**〔面试别提〕** 变种自造。"议题应稳定"是变种文档里为了规则化判定而提的假设，本体里没有这个假设——本体的 P2D 由人判断，不需要议题稳定性做前提。

来自两个场景的对比观察——

- 2026-04-25 · Agent 评测场景 Round 1 vs Round 2 的 P2D 拆台对比：5 条具体论据全部不同、底层议题层面 60% 重叠
- 2026-04-26 · ExamSniper 场景的 4 对独立比对：D1 vs D2 = 50%、D1 vs Y-R1 = 43%、D2 vs Y-R2 = 29%、Y-R1 vs Y-R2 = 33%——全部低于 60% 门槛

ExamSniper 的解读（来自实验 meta-observations）：D2 攻击"内外人格分裂"是因为 v4 写出了这套话术——P2D 跟着方案具体形态调整火力、不是议题不稳定的缺陷。

含义：议题敏感度可能是**场景依赖的、不是普遍规律**。可能的解释——Agent 评测有"judge 是测量仪还是协作者"这种核心定位锚点、议题就反复回到这一点；ExamSniper 没有同等强度的核心锚点、议题就跟方案走。

之前第 4 条写的"P2D 反复打同一组核心议题、回 P1 救不了"这个核心命题被 ExamSniper 反例了。但不能简单改写为"P2D 议题随方案演化"——更准确的表达应该是"议题稳定性可能受场景核心锚点强度影响"。

下一步：在更多场景跑同样对比、识别"什么样的场景核心锚点会让议题稳定"——这是实证问题、不是设计问题。

### 5. 拆台密度高的 seed 让新规则"提前结束"机制无法触发

**〔面试别提〕** 变种自造。"提前结束机制"是为了让全自动流程能跑完而设计的，本体里"什么时候停"是人的决定。

来自 2026-04-26 · ExamSniper 实验——

ExamSniper 涉及监管 + 合规 + 竞品三条独立硬墙、是个"必然 ≥ 2 kill shot"的场景。6 次 P2D-fix 判定（4 格 + Y 主线 2 次）全部判 ≥ 2 kill shot 触发回 P1、新规则的"≤ 1 kill shot 框架内消化"路径完全没用上。

含义：新规则的"放过"机制需要在**拆台稀薄的 seed** 上才能验证。拆台密集的 seed（涉及独立硬墙、各墙各自 K + H）撞两套规则都是回 P1、规则差异在判定结果上看不出来。

对方法论的具体影响：`liangyi-auto-variant.md` **已于 2026-08-27 在第八节"当前实证基础"补入**——明确写了新旧规则零分歧、6 次判定全判回 P1、"提前结束"路径至今未被任何场景触发过，需要在拆台稀薄的 seed 上验证。

下一步：在拆台稀薄的 seed 上跑新规则、看"放过"路径是否真的能产出合格 v5。

### 6. 规则差异决定兜底产物倾向（最重要、需更多场景验证）

**〔面试别提〕** 变种自造。两套兜底规则的产物差异是变种内部的工程问题，本体里根本没有"兜底规则"这个东西。

来自 2026-04-26 · ExamSniper 实验——

同一 seed、同一类拆台维度（差异化 / 付费引擎 / 护城河 / 合规）下、老规则与新规则的终止条件兜底产物路线分化大到几乎是两个产品：

- v5-旧（老规则兜底）：走"全面合规化重写"——重新定位为"备考期资料整理工具"、反滥用机制下沉 P0、品牌话术全面去敏感化
- v5-新（新规则兜底）：走"按维度分别处理 + 承认无法消除的 K 项"——保留"考前提分搭子"叙事、押题立场拿到正面说明、监管系统性风险写在风险清单第一条

含义：规则差异**不只是判定粒度差异、是兜底产物的设计哲学差异**——老规则因为不区分 K/F、所有论据都得当 K 处理、被迫"全维度合规化重写"；新规则因为 K/F 已分、可以"分项处理 + 对 K 坦白"。

这是 ExamSniper 场景最有价值的发现。如果跨场景复现、应该在 `liangyi-auto-variant.md` 5.2 节加一段"兜底产物倾向"——明确说明新旧规则的设计哲学差异在产物上的体现。

下一步：在 2-3 个其他场景重复跑新旧规则对照、看"兜底产物倾向差异"是否稳定。单场景的产物质量有主观性、需要更多对比才能下结论。

### 7. P2C 默认"指出漂移就回退"可能写得太严

**〔面试别提〕** 变种自造。本体的 2C-rollback 是人做的判断，没有"默认值"这回事。

来自 2026-04-26 · ExamSniper 实验——

按 `liangyi-auto-variant.md` 5.1 节、2C-rollback 默认"P2C 指出漂移就回退"。但实验 X / 实验 Y 两次 P2C 都识别出漂移（都是合规化收缩 + 承诺收窄）、Claude-2 4 次（X-R1、X-R2、Y-R1、Y-R2）都自行判断为"合理漂移、不回退"——4 次都判对。

含义：默认值"指出漂移就回退"可能太严——Claude-2 实际上需要做"漂移合理性判断"才不会过度回退。在 ExamSniper 场景下 Claude-2 的判断 4 次都对、但样本量太小、不能直接动默认值。

下一步：在更多场景观察 Claude-2 在 P2C 是否还会自行覆盖默认值、覆盖后是否依然判对。如果稳定复现、再考虑改默认值为"P2C 指出漂移 + Claude-2 判定不合理 → 回退"。

### 8. 规则代价归档机制（Claude-2 在被终止条件兜底时自动诚实标注）

**〔面试别提〕** 变种自造。有意思，但它记录的是变种规则的代价，本体里不存在这个代价。

来自 2026-04-26 · ExamSniper 实验——

X-R2 和 Y-R2 都是被终止条件强制产出 v5。Claude-2 在两次中都主动在判定文件 / 拆台响应日志里写"自由判断本应回 P1、但被终止条件压住"——是 prompt 没显式要求的自发行为。

含义：这是 `liangyi-auto-variant.md` 5.2 节"用可能产出有内部矛盾的 v5 换实验可以跑完"代价的**活样本**——代价被诚实记录、不是被掩盖。这件事修正了之前"Claude-2 元认知不值得长期观察"的判断——具体的"规则代价归档机制"和泛泛的"AI 加思考"不一样、有方法论价值。

下一步：观察其他场景下 Claude-2 在被终止条件兜底时是否也会自动诚实标注。如果稳定复现、可能值得在变种文档里显式建议这种"自动归档代价"的实践。

### 9. 变种 + 人工介入的混合形态（介于本体和变种之间的第三形态）

**〔面试可选〕** 被问"这套流程成本太高了吧、开七个窗口谁受得了"时可用——存在一个中间形态：保留窗口隔离和角色独立的硬规则，但把 fix 的决策权留在人手里。

来自 2026-04-26 / 27 · 决策模拟器场景（首次完整跑完 P0-P3 的全流程）——

本场景使用变种的窗口骨架（Claude-1 / Claude-2 / Claude-3 / Claude-4 / DeepSeek-1 / DeepSeek-2 / Qwen-1 等独立窗口、底模坐标跨维度等硬规则全部保留）+ Kill shot 分级判定 prompt + 终止条件兜底——但 Wenbo 在每个 P2 fix 步骤都人工介入做关键决策，没有让 Claude-2 自决。

具体介入：round-1 共 4 段连续介入（重设目标尺度 / 提商业模型方案 / P2C-rollback 决策权拉回 / P2D-fix 4 段战略调整 + 不进大陆 + 追问 P0 初心 + 塔罗回归）；round-2 共 2 段介入（反 Claude-2 砍英文版 / 反收窄到北美华人）。Wenbo 的核心决策（如不进大陆、塔罗作镜子、目标用户重定为大陆背景中文用户）都是人工产出、不在 Claude-2 自决路径里。

含义：这次跑法**实质上更接近本体（人在每个决策点参与）而不是变种（全自动）**——但保留变种的窗口结构和 prompt 模板。这证明了"窗口隔离 + 角色独立"的硬规则部分可以独立于"自动化决策"使用。这可能是一种值得显式命名的第三形态——既不是本体的"全人决策"、也不是变种的"全 AI 决策"、是"窗口骨架 + 人保留 fix 决策权"的混合形态。

下一步：跨场景验证这种混合形态是否稳定有效。如果跨场景复现、可能值得在变种文档（或新建一份混合形态文档）里显式记录此使用模式 + 适用场景（中等风险、可逆性中等、Wenbo 关心方向但愿意把窗口卫生交给变种自动化的项目）。

### 10. 二次 P2 验证轮作为新机制候选

**〔面试可选〕** 被问"方法论还在演化吗、你怎么决定加不加新机制"时可用——它是一个跑通了但还没进本体的候选，正好演示"证实才收录"这条门槛怎么执行。

来自 2026-04-26 / 27 · 决策模拟器场景——

round-1 跑完 idea-v5 后，Wenbo 判断"v5 还需验证、回 P2 而不是回 P1"——把 round-1 v5 直接作为 r2-idea-v1 输入、用全新 Claude-3' / Claude-4' / Qwen-1' / DeepSeek-2' 窗口（Claude-2 续保执笔连贯）跑了完整的二次 P2 链条（P2A → P2A-fix → P2B → P2B-fix → P2C → P2C-rollback → P2D → P2D-fix）。

数据：round-1 P2D 产 3 个 kill shot 候选（具体性全 H）；round-2 P2D 产 1 个 kill shot 候选（其余 4 条具体性 M）。round-2 跑完 r2-v5 在 8 处具体方面比 round-1 v5 更 solid（含主动认领反思塔罗框架、三层叙事整合产品身份退役、服务对象扩展、新增轻推演、目标用户修正、差异化重新定义、长期格式认识论显式声明、综合判断改"赌注 + 失败信号"）。

含义：本体和变种文档**都没显式设计"v5 锁定后回 P2 重跑"这条路径**——本体的 P2 是 v0→v5 的演进、不是 v5 已锁后再压一轮的验证机制。这次跑通证明这条路径在工程上可行 + 产物质量真有提升。但有一个隐含成本：Claude-2 的"防御性过度收窄"在二轮里出现了 2 次（round-1 是 0 次同类介入）——见第 11 条。

下一步：跨场景验证。关键问题：（a）"二次 P2 P2D 比首次更框架内"是稳定特征还是本场景偶然？（b）什么样的场景值得跑二次 P2、什么样的场景边际收益已不够覆盖二轮成本？（c）是否需要为这条路径明确写入方法论（增加"二次 P2 验证轮"作为本体或变种的可选机制）。

### 11. Claude-2 在 fix 阶段的"防御性过度收窄"倾向

**〔面试主证据〕** 出自变种场景，但**不是变种自造的问题**——它是"AI 溶解人的判断"的一个可复现的具体机制：AI 面对批判时会把攻击范围扩大化处理，砍掉批判压根没攻击的东西（critic 只说"双语同口径没先例"，它把整个英文版砍了）。人不在场，产品价值就这么一刀一刀丢掉。这条比任何抽象论证都好讲。

来自 2026-04-26 / 27 · 决策模拟器场景 round-2——

round-2 共有 2 次 Wenbo 人工介入，性质都不是"主动重塑产品方向"（这是 round-1 介入的性质），而是"反对 Claude-2 的过度防御性收窄"——

- **介入 1（P2A-fix）**：Claude-2 接受 P2A "双语同口径在心理类无成功先例"批评 → 直接砍掉英文版降级为 v6+ 独立产品。Wenbo 反对："为什么不能中英都做？只是加一个翻译的功能罢了。"Claude-2 自检承认"把'翻译可访问'和'native voice 同等'两件事混成一件、critic 攻击的是后者、但我把前者也砍了"。
- **介入 2（P2D-fix）**：Claude-2 接受 P2D "海外华语市场是 7 个碎片市场"批评 → 收窄到北美华人留学+工作群体。Wenbo 反对："实际主要客户群体肯定还是中国大陆的客户。"Claude-2 自检承认这是"对 P2D #3 的过度防御性回应——critic 说 7 碎片化、就缩到一个最同质的子市场、但这其实丢了产品最大的实际用户群体"。

含义：Claude-2 在面对 critic 时倾向"防御性接受"——把 critic 的攻击范围扩大化处理（只攻击 voice 同质就砍英文版、只攻击海外华语碎片化就缩到北美一个子市场）。这是 Claude-2 在二轮"保卫姿态"下的稳定倾向。可能的解释：首轮里 Claude-2 是在创造、二轮里它是在保卫——保卫姿态天然倾向"宁可砍多不愿被 critic 抓住"。

含义对方法论：即使在变种里、P2 fix 步骤的人介入余地不只是"判断 K/F"这种规则化判定，还包括"防止 Claude-2 过度防御性地丢掉产品价值"。这条观察补强了第 4 条（变种 P2D-fix 在面对真有威胁的拆台时需要人的介入余地）。

下一步：跨场景验证 Claude-2 二轮"防御性收窄"是否稳定。如果稳定、可能需要在变种 / 混合形态文档里显式建议"二轮 P2 fix 步骤强制人介入"或"在 fix prompt 里加反过度收窄护栏（如：critic 攻击 X 不等于要砍掉所有相关的 Y/Z）"。

### 12. P3.1.1 设计混淆 · 陌生用户视角 vs 老客户反馈

**〔面试可选〕** 被问"你这方法论有什么已知缺陷"时可用——是一个诚实的设计问题：一个步骤名下压了两个不同的 failure mode。

来自 2026-04-26 / 27 · 决策模拟器场景 P3.1.1 用户视角校验——

本体 P3.1.1 设计目标是模拟"陌生用户视角"（对抗知识诅咒、暴露 PRD 文档对零上下文新读者是否独立站得住）——硬规则要求"模拟用户必须是没有参与过方案讨论的陌生视角"。

Wenbo 刻意用同一个 Qwen 做了三轮 P3.1.1（PRD-1 / PRD-2 / PRD-3），理由："实际场景里反复给反馈的就是同一个客户、同一个人评估迭代后的产品比找新陌生人更有效。"

实际跑出的反馈中**有一个新陌生人 Qwen 给不出的关键洞察**——PRD-3 改动 #4（反向回拉:"双峰消失反而让她想产品是不是觉得我只适合一种"）只有"知道 PRD-2 把双峰藏起来"的用户才能提出。陌生新人 Qwen 读 PRD-3 不会说"双峰被藏过头了"——因为他不知道前一版长什么样。类似的还有"这就是我心里想说但之前没组织好的话"等典型 repeat user 反馈。

含义：Wenbo 的实际操作**捕捉到了一个 P3.1.1 本体设计没覆盖的 failure mode（老客户反馈链条），但同时没覆盖 P3.1.1 本体原本要覆盖的 failure mode（陌生新人对最终版的可读性）**。两件事都有价值、不互相替代——

- "陌生用户视角"对抗的 failure mode：PRD 文档对陌生人是否独立站得住、传播时第一眼能否读懂
- "老客户反馈"对抗的 failure mode：迭代是否真的解决了问题、是否引入了新问题

理想做法：第二轮可以新陌生 Qwen 读 PRD-2 + 同一个 Qwen 读 PRD-2，两个并行、互相补充。但本场景只跑了后者。代价：PRD-3 对陌生新人是否站得住没验证（不过本场景 PRD 主要受众是 agent teams + Wenbo、不是陌生用户、代价小）。

含义对方法论：P3.1.1 本身可能需要分两个独立步骤——P3.1.1.A "陌生用户视角校验"（用全新 AI 读最终版）+ P3.1.1.B "老客户反馈链条"（用同一 AI 读迭代版）。这两件事都不该被压在 "P3.1.1" 一个步骤名下、它们解决的不是同一个 failure mode。

下一步：跨场景验证。关键问题：（a）老客户反馈链条产出的洞察在多少场景里真的不可被陌生新人 Qwen 替代？（b）如果稳定、值得在本体或变种里把 P3.1.1 显式分两步吗？

### 13. P2D-fix 的"换战场"消解 K 项 · Kill shot 分级的隐含假设

**〔面试可选〕** 出自变种场景，但洞察超出变种：kill 级问题可能是"产品在某个环境下的属性"而非内禀属性，而"换个环境"这种产品定位级调整只能由人提出——AI 判不出来。它支撑"边界决策不可委托"这条主线，追问时可以补充。

来自 2026-04-26 / 27 · 决策模拟器场景 round-1 P2D-fix——

round-1 P2D 产 3 个 kill shot 候选，按 Kill shot 分级规则正常应回 P1。但 Wenbo 通过"Web 主战场 + 不进中国大陆"的战略调整，把 P2D #4（监管红线、K + H）从"产品在大陆无法存在"降级到"不存在"——这是一次产品定位级别的调整、不是框架内修改、也不是回 P1 重做。

含义：变种 5.2 节假设的 P2D-fix 处理路径只有"框架内修改 vs 回 P1"——这个二分背后的隐含假设是"K 项是产品本身的内禀属性、不会因为外部条件变化而消失"。但本场景证明：**K 项也可能是产品在某个特定环境下的属性（可通过环境调整消解）**——比如监管 K 项可以通过"换战场"消解、用户画像 K 项可以通过"重定义目标用户"消解。

这意味着变种 5.2 节的"框架内 vs 回 P1"二分**可能不充分**——存在第三条处理路径："产品定位级调整消解 K 项"。这条路径不能纯靠 Claude-2 自决、必须由人提出，因为产品定位调整是产品决策、不在 Claude-2 自动判定能力范围内。

含义对方法论：Kill shot 分级 + 终止条件兜底这两条规则本身没错、但它们隐含假设了"K 项是产品的内禀属性"。当 K 项实际是"产品在某个特定环境下的属性"时、纯规则化判定会产生假阳性的回 P1 触发。变种 P2D-fix 的设计应保留人的介入余地（呼应第 4 条 + 第 11 条）。

下一步：跨场景验证"换战场消解 K 项"是否在多场景出现。如果多场景稳定、值得在变种 5.2 节显式增加"产品定位级调整作为第三处理路径"，并明确这条路径必须人介入、不能 Claude-2 自决。

---

## 理论借鉴（外部成果对方法论的支持、启发与对照）

> **面试价值（2026-08-27 加）**：整节属于**〔面试可选〕**——被问"你这套东西有没有理论依据、还是自己拍脑袋想的"时，从这里取一到两条即可，不要成段讲。

这一节记录从外部学术 / 工业成果对方法论本体的关联、分三类：

- **A · 引用支持**：外部成果实证或佐证方法论已有论点的事实层面发现
- **B · 新设计候选**：可能给方法论新启发、需要更多评估的提议（明确标"候选、未到本体修订门槛"）
- **C · 反例与对照**：方法论显式拒绝或方向不同的项目、作对照参考

来源：2026-04-26 让 6 个 AI 做的全网检索（Gemini / Claude / Deepseek / Qwen / Doubao / ChatGPT）+ 自己实读的 3 份原文（MAD 论文、LangGraph interrupts 文档、Anthropic Building Effective Agents）。

### A · 引用支持

**A.1 立场一·防 AI 溶解（"零、立场前置"）**

Tencent MAD 论文（Liang 等, 2023）提出并定义 Degeneration-of-Thought (DoT) 问题——"Once the LLM-based agent has established confidence in its answers, it is unable to generate novel thoughts later through self-reflection even if the initial stance is incorrect"。三个原因：Bias and Distorted Perception、Rigidity and Resistance to Change、Limited External Feedback。**这是立场一最直接的外部实证**。链接：https://arxiv.org/abs/2305.19118

**A.2 为什么是 2 个 AI（第二章）**

- **MAD 论文增加 debater 数量损害性能的实验**：从 2 → 3 → 4 个 debater、COMET 分数 84.4 → 83.1 → 82.9 单调下降。原因是 LLM 长上下文限制（"Such LLM-based debaters tend to forget the views of other debaters during the debate"）。**方法论"为什么是 2"的另一条独立实证**——不是人脑带宽、是 LLM 长上下文限制。
- **CoThinker / United Minds（AAAI/arXiv）+ AIWG（jmagly/aiwg）**：显式使用认知负荷理论（Miller 1956 / Sweller 1988）指导 LLM 多 Agent 设计、用 Agent 专业化分布内在认知负荷。**对方法论第二章人脑带宽论证的认知科学背书**。

**A.3 divergence 优先于能力（第三章）**

- **UNC Chapel Hill ReConcile（ACL 2024）**：把 ChatGPT、Bard、Claude2 当作不同模型族 agents 圆桌讨论、多模型组件本身贡献了 6.8% 性能提升的最大部分。**异质性是核心增益来源、和"divergence 必须跨底模坐标"硬规则相互印证**。链接：https://arxiv.org/abs/2309.13007
- **Together AI MoA（ICLR 2025）**：选 LLM 时 performance 与 diversity 两个标准。**performance × diversity ≈ 方法论"价值 ≈ divergence × min(capability) × match"乘法模型**。链接：https://github.com/togethercomputer/MoA
- **CaldiaWorks Divergence Loop**：作者明确指出"分歧不能通过指令要求 AI 分歧来实现"——**印证方法论"divergence 来自结构而非 prompt"的判断**。

**A.4 P1 对抗式 Brainstorm（第七章）**

- **MIT/Google Society of Minds（Du, Tenenbaum 等）**：多 LLM 实例独立提出方案再多轮辩论——multi-agent debate 奠基论文之一。链接：https://arxiv.org/abs/2305.14325
- **Tsinghua thunlp ChatEval**：研究发现"赋予不同 persona 至关重要、同 persona 会导致性能退化"——**直接支撑 P2 链条 persona 轴的设计**。链接：https://github.com/thunlp/ChatEval

**A.5 跨轴约束（第四章）**

MAD 论文 judge 不公平实验："the judge shows a preference to the side with the same LLM as the backbone... LLMs might not be a fair judge if different LLMs are used for agents"。Turbo + GPT-4 配对实验里、judge 偏向同 backbone 的 debater 比例 120:77 vs 52:136、有显著倾向。**完全实证方法论"persona 轴受 AI identity 轴约束"的跨轴约束**——P2D 拆台不能让 Claude 扮演的根据。

**A.6 P2B 单盲（第八章）**

- **AgentV Blind A/B Comparison**：显式采用 Anthropic 的 comparator.md 和 analyzer.md 技术、实现盲审对比。**P2B 单盲机制的工程化实例**。
- **Anthropic Multi-Agent Research System**：Lead Researcher 拆解任务给 subagents 并行处理、subagents 独立 context。**对应方法论窗口隔离精神**。链接：https://www.anthropic.com/engineering/built-multi-agent-research-system

**A.7 P2D 拆台（第八章）**

ServiceNow Anticipatory Reflection 论文：引入"devil's advocate"在执行前向自己提出反问。**和方法论 P2D 同名同构**（虽然论文是单 Agent 内进行）。链接：https://arxiv.org/abs/2405.16334

**A.8 立场三·人做系统内部无法自判的决策（"零、立场前置"，2026-08-27 精确化）**

- **OpenAI AI Safety via Debate（Irving 等）**：两个 AI 轮流陈述、由人类 judge 选谁更真实——把"两个 AI 对抗 + 人类做最终判定"作为可扩展监督机制的最早奠基研究。**和方法论 P1.3 人类综合机制思路完全同构**。链接：https://arxiv.org/abs/1805.00899
- **LangGraph interrupt 机制**：节点级 interrupt 暂停等人类输入、LangGraph 不告诉你"何时该 interrupt"——把"哪些是边界决策"完全交给使用者判断。**与方法论"边界决策不可委托"完全同构**。

**A.9 P3 文档生成（第九章）**

- **MetaGPT / ChatDev**：把"PM→架构师→工程师→QA / CEO→CPO→CTO→程序员→审核员→测试员→设计师"的真实软件公司 SOP 编码进多 Agent 系统。**P3 链式文档生成的工业级先例**。链接：https://github.com/geekan/MetaGPT、https://github.com/OpenBMB/ChatDev
- **Stanford OVAL STORM / Co-STORM**：先多元视角→综合大纲→展开。**节律对应 P1（发散）→ P2（压力测试）→ P3（展开）**。链接：https://github.com/stanford-oval/storm

**A.10 Kill shot 分级方案的工业实践参照**

Anthropic Building Effective Agents 中 Evaluator-Optimizer pattern 原文未给出 Evaluator-Optimizer 内部的 fix loop 防护、把循环控制责任推给外层 Agents 层（max iterations + ground truth + human checkpoint）。**这反过来证明方法论 5.2 节 Kill shot 分级 + 终止条件方案在工业实践层面是"自己造的"——超出 Anthropic 公开推荐的精细度**。链接：https://www.anthropic.com/engineering/building-effective-agents

### B · 新设计候选

> 标"候选、未到本体修订门槛"——记录是为了未来撞到相关实战问题时可以借鉴、不立刻动方法论。

**B.1 Adaptive break 替代 / 补充 Kill shot 分级**

来自 MAD 论文。MAD 让 judge 自己判断"已达最优、可以提前结束"——而不是用次数限制。论文实证："Forcing the debate to continue will harm the translation results"、"In the majority of cases, the optimal answer can be achieved through a single round of debate"。

**潜在应用**：P2D-fix 可能用 adaptive break 替代或补充 Kill shot 分级——让 Claude-2 判断"这一轮拆台是否真增加了新信息"。和现有 Kill shot 分级不互斥、可以并存。需要实战验证。

**B.2 Ground truth check 思想**

来自 Anthropic Building Effective Agents：原文 "it's crucial for the agents to gain 'ground truth' from the environment at each step"——agent 必须从环境拿真实反馈、不能只靠自我评估循环。

**潜在应用**：P2D-fix 是 Claude-2 单方面对拆台的判定、缺 ground truth check。可能在 Claude-2 判定后加一个独立 AI 做一致性检查。但要警惕这条容易滑成"加一步专家做边界决策"——之前已经判定为虚假解。

**B.3 Idempotent side effects 原则**

来自 LangGraph interrupts 文档："side effects called before interrupt should (ideally) be idempotent"——因为节点会重跑。

**潜在应用**：变种里"回 P1 重做"涉及的 P0/P1/P2 步骤如包含 side effects（外部 prompt 调用、token 消耗、文件写入等）必须幂等。可加到 `liangyi-auto-variant.md` 5.x 节作为"工程实施提醒"。

**B.4 "tit for tat" modest level**

来自 MAD 论文。纯粹"对立到底"（disagreement 0.988）反而损害性能——会陷入 polarization、debate 变成"赢 argument"而非"找真相"。

**潜在应用**：本体里 P2D 的"全盘否定"是有意为之、不该改（已在第十二章变种归变种讨论过）。但变种里 P2D 角色可能要重新评估——"硬刚到底"是否反而让 v5 内部矛盾大于必要？需要更多场景验证。

**B.5 Strong debaters with weak judge works better than reverse**

来自 MAD 论文 judge 分析。Turbo debaters 配 Vicuna judge 比反向更好——judge 选型不必比 debater 强。

**潜在应用**：方法论 AI 选型策略——P1 专家用最强模型、P2D-fix 判定者可以用稍弱模型、节省成本不损质量。

**B.6 CitationAgent / 理由溯源剥离**

来自 Anthropic Multi-Agent Research System。把"理由溯源"从主流程剥离出来给独立 agent。

**潜在应用**：方法论 decision-log 的工程化思路——独立 AI 维护溯源版本。但本体明确人写 decision-log、不该委托给 AI——这件事属于"人很累时让 AI 维护溯源版本但人审"的灰线。

### C · 反例与对照

> 方法论显式拒绝或方向不同的项目、作对照参考。这一类不是为了借鉴、是为了清楚方法论的边界在哪里。

**C.1 单 LLM 自我反思系列（方法论 P1.4 显式反对）**

- Self-Refine（CMU + Allen AI）：单 LLM 充当 generator + feedback + refiner。链接：https://github.com/madaan/self-refine
- Reflexion（Northeastern + MIT）：单 Agent 用语言反馈做 verbal reinforcement learning。链接：https://arxiv.org/abs/2303.11366

MAD 论文显式指出这种单模型自反思会陷入 DoT——这正是方法论 P1.4 "必须新开 Claude-2 而不是续 Claude-1 自我修订"那条规则的实证依据。

**C.2 自动协商 / 机器共识系列（红线五反对）**

- AutoGen GroupChat Auto-Negotiation：自动协商替代人综合
- Mixture-of-Agents (MoA) 自动共识聚合：机器共识聚合替代人判断

红线五"不做多 Agent 自动协商"——这两类是反例。方法论始终保留人类作为最终综合者。

**C.3 任务自动化框架（方向不同、不是认知决策辅助）**

- MetaGPT / ChatDev / CAMEL / CrewAI / AgentVerse：偏任务执行 orchestration（写代码、做产品流程自动化等）
- n8n / Coze / Dify / 阿里 Qwen-Agent / 字节火山方舟 / 腾讯混元 / Microsoft Agent Framework / Google ADK：工程化执行容器

这些是和方法论**互补**的——方法论是 idea 层面的认知决策辅助、它们是工程化执行容器。可作为变种工程化落地的承载平台、但不是方法论本身的对标。

**C.4 Solo Performance Prompting (SPP)（单底模激活多 persona）**

来自 UIUC + Microsoft NAACL 2024。单底模上召唤多 persona 协作。

**对方法论的对照价值**：是 P2A "Claude 切投资人"那一步的方法论根据——persona 轴在单底模上是可激活的。**但同时也是限制的实证依据**——A1（规范优先）的 Claude 激活不了拆台 persona、必须换 A3（任务优先）的模型。链接：https://arxiv.org/abs/2307.05300

**C.5 Anthropic Collective Constitutional AI**

多视角对齐机制——不是产品方案审查、应用场景不同。但其"批判-修订循环"和方法论 2A-fix 流程结构同构。链接：https://www.anthropic.com/research/collective-constitutional-ai-aligning-a-language-model-with-public-input
