# Liangyi — AI-Driven Product Development Workflow v1.0

[中文版](Liangyi.zh-CN.md)

> **Liangyi** (两仪) /lyahng-ee/ — "The Two Polarities."
> From the *I Ching* (易经·系辞): "太极生两仪" —
> *The Supreme Ultimate generates the Two Polarities.*
> In Chinese cosmology, a single unified origin gives rise to two opposing
> forces (yin and yang), whose productive tension shapes all further complexity.

> A standardized AI-assisted product development framework combining multi-model
> cross-validation, adversarial expert role debates, decision logging, and Skills orchestration.
>
> **Core idea:** Assign conflicting expert roles to different AI models to create structural
> tension — simulating the debates that happen in real product teams between engineering,
> design, and business.
>
> **Model compatibility:** This workflow runs in Claude Code (Model A = Claude). For the
> adversarial challenger (Model B), Gemini is recommended, but GPT / Qwen / Doubao / DeepSeek
> all work. The key is using a **different provider** so training biases don't overlap.
> Throughout this document, "Gemini" refers to your chosen Model B.
>
> This workflow is packaged as a [Liangyi skill family](https://github.com/wenboxia/liangyi)
> — install with `npx skills add`.

---

## Skills Registry

> **These are the author's battle-tested defaults. You can use them as-is**, or customize
> freely: add your own Skills, replace any with alternatives, or remove ones you don't use.

### Development

- **Superpowers** (obra/superpowers) — Agentic framework: /review, /loop, /batch, /plan, /simplify. Phase 4.
- **Everything Claude Code** (affaan-m/everything-claude-code) — Complete Claude Code configs: agents, hooks, commands, MCPs. Phase 3-4.

### Thinking

- **Best Minds** (Ceeon/best-minds) — Simulator thinking: summon world-class expert perspectives. Phase 1-4.

### Product Management

- **Product Manager Skills** (deanpeters/Product-Manager-Skills) — Battle-tested PM framework for PRDs, user stories, strategy. Phase 1, 3.

### Knowledge & Discovery

- **NotebookLM Skill** (PleasePrompto/notebooklm-skill) — Query your Google NotebookLM from Claude Code. Phase 1-2.
- **Find Skills** (vercel-labs/skills) — Auto-discover Skills matching your current task. Phase 4.

### Skills Dispatch Matrix

| Phase | Recommended Skill | Usage |
|-------|------------------|-------|
| P0 Idea refinement | — | No Skill needed |
| P1 Role selection | **Best Minds** | Select structurally conflicting expert pair |
| P1 Brainstorm | **Best Minds** + **PM Skills** | Expert-persona proposals; PM framework |
| P1 Knowledge check | **NotebookLM** | Query your own knowledge base |
| P2 Cross-validation | **Best Minds** | Investor critique; devil's advocate |
| P3 PRD generation | **PM Skills** | Drive PRD, user stories, requirements |
| P3 PRD validation | **Best Minds** | Simulate target user reading PRD |
| P3 Tech docs | **Everything Claude Code** | Reference agent/hook/command configs |
| P4 Development | **Superpowers** | /plan, /review, /loop, /batch |
| P4 Tech decisions | **Best Minds** | Instant expert summon |
| P4 Capability gaps | **Find Skills** | Discover new Skills on demand |

### Advanced: PM Skills Sub-skill Recommendations

Optional enhancements if you have Product Manager Skills installed (not required):

| Phase | Sub-skill | What it does |
|-------|-----------|-------------|
| P0 | `jobs-to-be-done` | Validate idea against real user "jobs" |
| P0 | `problem-framing-canvas` | Structure vague idea into problem statement |
| P1 | `positioning-statement` | Crystallize positioning after expert debate |
| P3 | `prd-development` | Multi-step guided PRD workflow (recommended) |
| P3 | `user-story` | Generate proper user stories per feature |
| P3 | `prioritization-advisor` | RICE/ICE/Kano for MVP scope decisions |

---

## Phase 0 — Idea Capture

**Input:** A rough idea (one sentence is fine)

1. Record your raw idea — voice memo, rough notes, anything. Don't filter.
2. Send to **Gemini** (or your Model B) for language refinement:

```
You are a prompt refinement specialist. I have a rough product idea.
Please:
1. Remove filler words, repetition, verbal tics
2. Refine language only — do NOT change my intent or direction
3. Preserve all specific details and constraints
4. Output a clean, structured description (under 200 words)

My raw idea: [paste your raw description]
```

**Output:** A refined idea description

---

## Phase 1 — Adversarial Expert Brainstorm

> Through Best Minds role assignment, this creates not "two AIs' random differences"
> but "two real professional stances in systematic tension."

### Step 1A-0 — Select Expert Role Pair

| Product Type | Role A (Claude) | Role B (Gemini) |
|-------------|----------------|-----------------|
| Payments / Finance | Security Architect | Growth Hacker |
| Social / Content | UX Designer | Data Monetization Lead |
| Tools / Productivity | Minimalist PM | Full-Stack Architect |
| AI / Technical | AI Researcher | Commercialization Director |
| Education | Ed Psychologist | Gamification Designer |

**Universal high-tension pairs:** Investor vs Engineer, Industry Veteran vs Cross-Domain Newcomer, User Advocate vs Competitive Analyst.

**Selection rule:** If both roles would give the same top-3 advice, tension is insufficient — pick another pair.

### Step 1A — Claude Proposal (Role A)

```
【Best Minds mode activated】

You are [Role A]. 20 years of domain experience. Your thinking, priorities,
and risk tolerance must match this role exactly.

Rules:
- When your role conflicts with generic PM advice, follow your role
- Mark conflicts: "As [Role A], I prioritize X over Y because..."
- Preserve your role's blind spots — do not self-correct

Please:
1. Core value proposition (your lens)
2. Feasibility (dimensions you care about most)
3. Top 3 concerns (what keeps this role up at night)
4. Alternative approaches (2+)
5. Recommended final shape

My idea: [paste refined idea]
```

### Step 1B — Gemini Proposal (Role B)

**Critical: Do NOT share Claude's output with Gemini.** Open a new session (label the tab "Role B").

```
【Best Minds mode】

You are [Role B]. 20 years of domain experience.

Rules:
- Give your honest professional judgment only
- If something isn't your concern, say "not my focus"
- Mark how your role stance shapes your advice

Please:
1. Does this idea target a real need? (your lens)
2. Best product shape and core features
3. Top 3 risks (your perspective)
4. Your complete, independent proposal

My idea: [paste same refined idea]
```

### Step 1C — Human Comparison + Decision Log

> This is the most irreplaceable human step in the entire workflow.

```markdown
### [PRODUCT] Decision 1: Core direction
- Role A position: [one line + underlying role logic]
- Role B position: [one line + underlying role logic]
- Core divergence: [what they fundamentally disagree on]
- **My choice:** [A / B / hybrid]
- **Reasoning:** [why — what context, intuition, or constraint drove this]
- **What AI can't weigh:** [the human judgment involved]
```

---

## Phase 2 — Cross-Validation & Fusion

### Step 2A — Claude Critique (Investor Role)

```
【Best Minds — role switch】

Drop your previous role. You are now a skeptical senior investor
who has seen too many failures. Your instinct is to find how this dies.

1. 3 weakest points + hardening suggestions
2. Most likely cause of death
3. Output an improved version

Proposal: [paste your merged proposal]
```

### Step 2B — Single-Blind Model B Review

> **Key insight:** A reviewer who knows your original idea unconsciously fills in
> gaps. A reviewer with zero context evaluates what you *actually wrote*, not what
> you *meant to write*.

**Open a brand new session** (label it "Blind Review"). NOT the Role B tab.

```
Here is a product proposal. I have no background info for you.
Evaluate purely on its own merits:

1. One sentence: what does this propose?
2. Is the logic internally consistent? Where doesn't it read right?
3. As an uninformed decision-maker, would you approve? Why?
4. Which parts are ambiguous or require unstated context?
5. Improvement suggestions

Proposal:
---
[paste ONLY the proposal — no original idea, no background, no motivation]
---
```

**Validation:** Compare Gemini's one-sentence summary vs your original intent.
Divergence = the proposal has an expression problem, not a Gemini problem.

Log as `[REVIEW]` type (AI-assisted finding, not human decision).

### Step 2C — Informed Re-review (Optional)

If Step 2B found major divergence, after revision, use the **original** Gemini
session (which knows your idea) to verify the fix didn't drift from intent.

### Step 2D — Devil's Advocate (Conditional)

**Trigger:** Claude + Gemini agree with no substantive disagreement.

**Complexity gate:** Only for core architecture or strategic direction decisions.
Skip for UI tweaks, copy changes, or well-scoped small features.

```
【Best Minds — Devil's advocate】

You are [domain's most famous skeptic]. You find what everyone else missed.

This passed two reviews with no major issues. That's when you pay closest attention.

1. 2+ assumptions that will be proven wrong within 6 months
2. Paths reviewers missed due to anchoring
3. How would a competitor defeat this?
4. "At minimum, validate ______ first"

Proposal: [paste current proposal]
```

**Output:** `idea.md` — finalized product concept

---

## Phase 3 — Document Generation

### 3.1 PRD

Generate full PRD from idea.md including: product overview, target users, feature
table (P0/P1/P2), user stories, info architecture, MVP scope, success metrics,
multi-agent assessment.

### 3.1.1 PRD User Perspective Validation (Best Minds)

AI simulates target user reading PRD. Results logged as `[REVIEW]` type — clearly
labeled as AI simulation, not human decision.

```
【Best Minds — target user simulation】

You are [target user persona]. Non-technical. You only care if this solves your problem.

1. What does this product do? (one plain sentence)
2. What pain does it solve for you?
3. Would you use it? Why?
4. What would make you quit?
5. What's missing that you need?

PRD: [paste PRD draft]
```

### 3.2 Technical Spec (tech-spec.md)

Stack selection, directory structure, module design, agent assessment, development
phases, Skills dispatch table, risk register.

### 3.3 CLAUDE.md

Code conventions, Git workflow, file organization, testing requirements, agent boundaries.

### 3.4 Dev Guide (dev-guide.md)

Step-by-step operator manual: what to do, which tool, which Skill to invoke,
expected output, human decision points, acceptance criteria per phase.

**Output documents:**

| Document | Purpose | Reader |
|----------|---------|--------|
| `idea.md` | Product concept | You |
| `prd.md` | Product requirements | You + Claude Code |
| `tech-spec.md` | Technical architecture | Claude Code |
| `CLAUDE.md` | Dev conventions | Claude Code |
| `dev-guide.md` | Operator manual | You |
| `decision-log.md` | Decision + review record | You / portfolio |

---

## Phase 4 — Development

1. Load `CLAUDE.md` and `tech-spec.md` into Claude Code
2. Follow `dev-guide.md` phase by phase
3. Log significant decisions with `/decision-log`
4. For technical dilemmas, use Best Minds instant summon:

```
Who in the world knows [domain] best? Answer as that person.
Give me a recommendation with conviction, not "both have pros and cons."
```

---

## Session Management

| Tab Name | Content | Used In |
|----------|---------|---------|
| "Role B" | Model B with your idea context | Phase 1B, optionally 2C |
| "Blind Review" | Model B with zero context | Phase 2B only |

Never paste into the wrong tab — it defeats the single-blind mechanism.

---

## Skill Family

This workflow is packaged as 5 independently installable Claude Code Skills:

| Skill | Purpose | Install |
|-------|---------|---------|
| `expert-debate` | Adversarial brainstorm with role personas | `npx skills add wenboxia/expert-debate` |
| `blind-review` | Single-blind audit + devil's advocate | `npx skills add wenboxia/blind-review` |
| `doc-generator` | PRD + tech spec + CLAUDE.md | `npx skills add wenboxia/doc-generator` |
| `decision-log` | Human decision tracking | `npx skills add wenboxia/decision-log` |
| `liangyi` | Full orchestrator (all 4 above) | `npx skills add wenboxia/liangyi` |

---

## When to Simplify

| Situation | What to skip |
|-----------|-------------|
| Small feature iteration | Skip Phase 1B. Run expert-debate solo in Claude. |
| Already have an idea | Skip Phase 0-1. Start at Phase 2 or 3. |
| Technical prototype | Skip Phase 0-2. Go straight to doc-generator. |
| Urgent deadline | Only use decision-log throughout. Everything else by instinct. |
| Quick brainstorm | Just install expert-debate. Skip everything else. |
