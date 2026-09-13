# engine · 两仪论工作流引擎

把方法论从「一份照着做的文档」变成「一条能跑的链」。

## 为什么要有这一层

方法论手动跑的时候，最常见也最致命的错误是图省事用同一个窗口跑完整个流程——
于是单盲不单盲、综合不中立、批判不独立，方法论当场失效。`docs/session-hygiene.md`
用了整整一章讲这件事，但它终究只能靠使用者自觉。

做成代码之后，那些纪律变成了结构：

| 方法论纪律 | 手动跑 | 代码里 |
|---|---|---|
| 每个角色一个独立窗口 | 靠自觉开新标签页 | 不同的 `Window` 实例，物理隔离的 messages 数组 |
| 单盲必须零上下文 | 靠自觉不粘贴背景 | `zero_context=True` 的窗口拒绝历史注入并抛异常 |
| 拆台必须 A3 任务优先档 | 靠自己记得 | 开跑前 `check_hard_rules()` 校验，不过就拒绝启动 |
| P2 链条必须跨维度 | 靠自己算坐标 | 同上 |

另外两件手动跑做不到的事：**可复现**（消融实验成立的前提）和**可观测**
（每一步的推理过程都被记下来）。

## 快速开始

```bash
cp .env.example .env      # 填入各家 API key
python -m engine.run --check                     # 预检：硬规则 + key 可用性
python -m engine.run -s scenarios/xxx.yaml -p debug   # 跑一条完整链
```

`-p debug` 用便宜模型验证流程，`-p primary` 是正式实验配置。

## 结构

```
config.py        窗口定义（本体）+ 模型映射（参考）+ 硬规则校验
providers.py     四家 API 适配 —— OpenAI 兼容格式，差异只在 base_url/key/推理字段名
window.py        窗口抽象 = 独立 messages 数组 + 模型绑定
steps.py         链条的声明式定义
orchestrator.py  确定性编排器
trace.py         执行记录（含推理过程）
gate.py          条件触发检测器（P0 忠实性 / 范围扩大化 / 假对立）
interact.py      人工决策点的交互界面
digest.py        决策点摘要 —— 把判断收敛到人答得了的层面
judge.py         盲评打分（成对比较）
prompts/         各步骤的 prompt 模板
```

### 一个刻意的设计：窗口按角色命名，不按模型命名

代码里没有 `Claude-1`、`Kimi-1` 这种名字，只有 `expert-a`、`critic-blind`。
模型通过「槽位」映射进来，换模型只需要改 `PROFILES` 一个字典。

这不是洁癖。2026-08 复核九家厂商时，四个月前写死在文档里的版本号已经全部过期——
方法论的「本体 vs 参考分离」纪律就是为这件事定的，代码结构照着它长。

### 另一个刻意的设计：不用 agent 做编排

整条链是确定性的：下一步是什么、用哪个窗口、读哪些文件，全部在 `steps.py`
里写死。三个理由：

1. 流程的阶段结构固定且事先已知，这种情况下 workflow 比 agent loop 更合适
2. 可复现是消融实验的合法性基础——要说「v3 比 v2 好是因为 P2B 这一步」，就必须
   保证除了 P2B 之外别的都没变
3. 方法论红线三写着「不做多 Agent 自动协商」，总调度 agent 会一路滑到那里

## 链条

```
P0        expert-a         忠实精炼                    → P0-refined.md
P1.0      expert-a         设计两个专家角色 + 校验张力  → P1-roles.yaml
P1A       expert-a  (续)    专家 A 出方案               → P1A-expert-a.md
P1B       expert-b         专家 B 独立出方案            → P1B-expert-b.md
P1.4      scribe           综合成单一立场的 idea        → idea-v1.md
P2A       critic-investor  投资人批判（persona 轴）     → P2A-critique.md
2A-fix    scribe    (续)                               → idea-v2.md
P2B       critic-blind     零上下文单盲（context 轴）   → P2B-blind-review.md
2B-fix    scribe    (续)                               → idea-v3.md
P2C       critic-reviewer  方向漂移诊断（scope 轴）     → P2C-review.md
2C-rollback  scribe (续)   ← 人工决策点（必停）         → idea-v4.md
P2D       critic-devil     拆台（AI identity 轴）       → P2D-devils-advocate.md
2D-fix    scribe    (续)   ← 人工决策点（必停）         → idea-v5.md
```

四步批判正好激活四轴 divergence 的四个不同轴，各 target 一种 failure mode。
这不是巧合——failure mode 和 divergence 轴是同一块设计的两个投影。

## 断点续跑

一条链要调 12 次 API，中途断掉是常态（余额、限流、provider 拒绝）。从头重跑
既费钱又费时间，所以：

```bash
python -m engine.run --resume runs/20260829-230613-dev-diagnose
```

它会跳过已有产物的步骤，**并把这些步骤的对话补回执笔窗口的历史**。

补历史这一步不能省。执笔窗口在 2A-fix / 2B-fix / 2C-rollback / 2D-fix 之间是
连贯的同一个窗口——「修改必须由同一个执笔者做，否则 idea.md 会变成多个 AI 的
拼贴」。续跑时如果让它从空白开始，这条纪律就断了，而且断得很隐蔽：产物看起来
正常，只是后半段的修订不再基于前半段的思路。

零上下文窗口不参与重建——它每次本来就从空开始。


## 人工决策点

三档：

```bash
--mode auto      # 全自动，一次都不停。跑批、可复现
--mode hitl      # 两个必停点：2C-rollback / 2D-fix，每处给两份旗舰模型的建议再由人定

# 早期的 off / minimal / advised / full 四档已并成上面两档，旧运行目录仍可 --resume
```

**必停点**不是"重要的步骤"，是**位置本身就是边界判断**的步骤：

- `2C-rollback` —— 方向漂移了要不要回退。投资 skill 那次不停就会交付成合规文档
- `2D-fix` —— 框架内修改还是回 P1。四个变种场景全部卡在这里

**条件触发点**平时不打扰，检测到问题才叫人。检测器在 `gate.py`，用便宜模型，
单次约 $0.0002：

- `P0-review` —— 精炼版偏离原意时
- `scope-creep` —— 执笔者把批判的攻击范围扩大化时

### 界面设计的一条原则：判断层次必须和人的能力对得上

第一版界面把整篇 P2C 诊断摊开，等于要求使用者做**领域专家的设计评审**。
实测反馈是"我没有这个能力和资格去判断"。

但方法论要人判断的根本不是这个。docs 对 2C-rollback 的定义是「回退的标准是
**这偏离了产品最初要解决的问题**」——翻译过来就是「你当初说要 X，现在变成了 Y，
认不认」。这个判断不需要懂领域，只需要他是提出想法的人。

所以现在的界面先给**意图对照**（`digest.py` 提取），完整材料降级为输入
`p2c` / `v1` 等随时调阅。同一个人、同一个场景，改了问法之后就判断得了——
**这说明原来的障碍是界面，不是使用者的能力**。

## P1.0 · 专家角色的生成与校验

docs 第七章有「步骤 1.0 · 选择两个专家角色」，第一版实现把它跳过了——角色直接
手写在 `scenarios/*.yaml` 里。这在 Web 上行不通：用户输入一个想法，系统得自己
知道派哪两个专家。

现在的行为：

- 场景文件**写了**角色 → 用它（Phase E 的场景手写，保证实验可复现）
- 场景文件**没写** → P1.0 自动生成

生成完必须过**假对立检测**。这是这一步最容易犯的错：模型很容易产出「稳健派 vs
激进派」这种程度差异，而**从产物上看不出来**——两份专家方案照样写得头头是道，
只是不会真的打架，P1 的 divergence 是虚的，一路影响到后面所有步骤。

判据不是"两个角色听起来是否不同"，是**能不能构造出一个具体决策问题，让两者
给出相反答案**。判假就把失败原因喂回去重生成一次。


## 实测踩到的坑

**推理模型会把 token 预算花光在思考上。** DeepSeek-V4-Pro / Kimi-K3 / GLM-5.3
全是推理模型，`max_tokens` 给小了会返回**空 content**——实测 GLM-5.3 思考了
2980 字符还没开始回答。`providers.py` 会检测这种情况并加倍重试，而不是让空
字符串一路流到下游。

**四家的推理字段名不一样。** OpenRouter 用 `reasoning` 且需要显式请求，
DeepSeek / Kimi / GLM 用 `reasoning_content` 且默认返回。

**同一个推理模型在同一任务上时好时坏。** deepseek-v4-flash 处理同一份 P2C 诊断，
一次只花 $0.0004 就完成，另一次思考了 16001 个 token 还没吐出内容。所以
`digest.py` 的摘要任务改用 gpt-5.6-luna —— **摘要要的是"读长文档 + 结构化输出"，
不是深度推理**，任务形态和模型特性不匹配就会这样。

**等待跑批别用 `pgrep -f` 匹配自己的命令行。** 写
`while pgrep -f "engine.run.*xxx"; do sleep; done` 会匹配到等待循环自身，
永远退不出。用 PID 或检查产物文件。

## 产出

每次运行生成一个目录：

```
runs/20260829-230421-dev-diagnose/
├── run.json          运行元信息 + 成本汇总
├── scenario.yaml     场景快照（可复现的前提）
├── trace.jsonl       每步一行：谁跑的、想了什么、花了多少钱
└── artifacts/        全部产物，与实验归档同构
```

`trace.jsonl` 里的 `reasoning` 字段是最值钱的一栏。手动跑的时候只能看到最终输出，
所以「这个批判 agent 是真在批判还是在敷衍」只能靠读输出内容推断。抓到推理过程后，
它变成可以直接检验的东西——尤其可以拿 A1 和 A3 在同一个拆台任务上的思考过程对照，
看「有规范层的底模会在最关键那一刀上把攻击软化掉」这个论断到底成不成立。

## 状态

Phase C（条件触发式 HITL）。链条 13 步跑通，两个必停点与两个条件触发点全部实装
并验证过，`python -m engine.test_guarantees` 21 项结构保证通过。

剩余：2 场景 ×（全自动 vs 人介入）的对照跑批，作为 HITL 价值的展示素材。
