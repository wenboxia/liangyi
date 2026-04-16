---
name: liangyi
description: >
  Full product development pipeline: expert role debates, single-blind review,
  document generation, and human decision logging. Orchestrates 4 modular skills
  into a complete idea-to-development flow. Use when starting a new product from
  scratch. Triggers on "product workflow", "new product", "full pipeline",
  "idea to development".
when_to_use: >
  When the user wants the complete structured pipeline from raw idea to
  development-ready documents. For individual capabilities, use the standalone
  skills: expert-debate, blind-review, doc-generator, decision-log.
disable-model-invocation: true
allowed-tools: Read Write Edit Bash
---

# Liangyi — Adversarial Product Workflow v1.0

> **Liangyi** (两仪) /lyahng-ee/ — "The Two Polarities."
> From the *I Ching* (易经·系辞): "太极生两仪" — *The Supreme Ultimate generates
> the Two Polarities.* In Chinese cosmology, a single unified origin (Taiji)
> gives rise to two opposing forces (yin and yang), whose productive tension
> shapes all further complexity.
>
> This workflow is built on the same structure: a single product idea generates
> two opposing expert views, whose structural disagreement you synthesize into
> your final decision. The tension is the feature.

Full orchestrator for the Liangyi workflow.
Combines 4 modular skills into a complete flow.

> This skill bundles all reference files in `references/`. No additional
> configuration is needed to get started.

> **Model compatibility:** This skill runs in Claude Code (Model A = Claude).
> For the independent challenger (Model B), Gemini is recommended, but any
> capable LLM works — GPT, Qwen, Doubao, DeepSeek, etc. The key is using a
> **different provider** so training biases don't overlap. Throughout this
> document, "Gemini" is used as shorthand for "your chosen Model B."

## Quick start

```
/liangyi
```

Individual phases can also be run:
```
/liangyi phase0    # Idea refinement
/liangyi phase1    # Expert brainstorm
/liangyi phase2    # Cross-validation
/liangyi phase3    # Document generation
/liangyi phase4    # Development kickoff
```

First-time setup (optional):
```
/liangyi setup
```

For standalone use of any module, install them individually:
- `/expert-debate` — just the brainstorm
- `/blind-review` — just the review
- `/doc-generator` — just the documents
- `/decision-log` — just decision tracking

## Setup (first-time configuration)

When invoked with `setup`, guide the user through:

1. **Model B selection**: "Which LLM will you use as Model B? (Gemini recommended,
   GPT/Qwen/Doubao/DeepSeek also work)"
   - Save choice to `references/config.md`

2. **Skills inventory**: Read `references/skills-registry.md` and ask:
   - "These are the default recommended Skills. Do you want to add, replace, or
     remove any? (Enter to keep defaults)"
   - If user has changes, update `references/skills-registry.md`

3. **Quick validation**: Confirm the setup by listing:
   - Model A: Claude (fixed)
   - Model B: [user's choice]
   - Active Skills: [list from registry]
   - "Ready to go. Run `/liangyi` to start."

Setup is optional — the workflow runs with defaults if skipped.

## Phase 0: Idea capture

1. Ask the user for their raw idea (voice transcript, rough notes, anything)
2. Generate a Gemini prompt for language refinement:

```
You are a prompt refinement specialist. I have a rough product idea description.
Please:
1. Remove filler words, repetition, and verbal tics
2. Only refine the language — do NOT change my intent or direction
3. Preserve all specific details and constraints I mentioned
4. Output a clean, structured description (under 200 words)

My raw idea: [paste raw idea]
```

Auto-copy to clipboard:
```bash
cat prompts/gemini-phase0.md | pbcopy 2>/dev/null || cat prompts/gemini-phase0.md | xclip -selection clipboard 2>/dev/null || echo "Prompt saved — please copy manually"
```

3. After user provides Gemini's refined version, review it together — confirm
   nothing was lost in refinement
4. Save to `idea-raw.md`

## Phase 1: Adversarial expert brainstorm

> Uses the same logic as the standalone `expert-debate` skill.

### 1.0 Select expert role pair

Read `references/expert-roles.md` for recommendations.
Help user pick two roles with structural tension. Log to `decision-log.md`:

```markdown
### [PROCESS] Decision: Expert role assignment
**Role A (Claude):** [name + why]
**Role B (Gemini):** [name + why]
**Tension point:** [where they conflict]
**What AI can't weigh:** [why this pair matters for *this specific* project]
```

### 1A: Generate proposal as Role A

Full instructions in `expert-debate` skill. Key points:
- Adopt persona completely, preserve professional biases
- Mark conflicts with generic advice explicitly
- Generate complete proposal with 5 components

### 1B: Generate Gemini prompt for Role B

Create prompt for a **separate, clean Gemini session**. Auto-copy to clipboard:
```bash
cat prompts/gemini-phase1.md | pbcopy 2>/dev/null || cat prompts/gemini-phase1.md | xclip -selection clipboard 2>/dev/null || echo "Prompt saved — please copy manually"
```

**Tell the user:** "Prompt copied. Open a new Gemini tab (label it 'Role B') and paste."

### 1C: Human comparison + decision log

Compare divergence points. Log each decision with the `[PRODUCT]` tag.
Every entry must answer: "Why did I choose this? What couldn't AI weigh?"

## Phase 2: Cross-validation & fusion

> Uses the same logic as the standalone `blind-review` skill.

### 2A: Claude critique (investor role)

Drop Role A persona. Adopt skeptical investor. Critique the merged proposal:
- 3 weakest points + hardening suggestions
- Most likely cause of death
- Output improved version

### 2B: Single-blind Gemini review

Generate prompt for a **brand new Gemini session** (label it "Blind Review").
Contains ONLY the improved proposal — no original idea, no background.

Auto-copy to clipboard. Tell user which tab to use.

After receiving Gemini's response:
- Compare one-sentence summary vs original intent
- Classify divergence: None / Minor / Major
- Log as `[REVIEW]` type (AI-assisted finding, not human decision)

### 2C: Informed re-review (optional)

If 2B found major divergence, after revision → prompt for the **original**
Gemini session (the one with context) to verify fix didn't drift.

### 2D: Devil's advocate (conditional)

**Trigger:** Claude + Gemini agree with no substantive disagreement.
**Complexity gate:** Only for core architecture / strategic direction decisions.
Skip for UI tweaks, copy changes, or well-scoped small features.

If triggered: hostile critic persona, find assumptions that will fail,
identify competitor attack vectors, specify minimum validation requirements.

**Output:** `idea.md` (finalized)

## Phase 3: Document generation

> Uses the same logic as the standalone `doc-generator` skill.

Read `references/doc-templates.md` for templates.

### 3.1: PRD (prd.md)

Generate full PRD from idea.md.

### 3.1.1: User perspective validation

AI-simulated user reads the PRD. Results logged as `[REVIEW]` type —
clearly labeled as AI simulation, not human decision.

If simulated user's understanding diverges from intent → flag before proceeding.

### 3.2: Tech spec (tech-spec.md)

Including Skills dispatch table referencing `references/skills-registry.md`.

### 3.3: CLAUDE.md

Code conventions, Git workflow, testing, agent boundaries.

### 3.4: Dev guide (dev-guide.md)

Step-by-step with Skill callouts and human decision point markers.

## Phase 4: Development kickoff

1. Load CLAUDE.md and tech-spec.md into Claude Code
2. Follow dev-guide.md phase by phase
3. Log significant decisions with `/decision-log`
4. For technical dilemmas, use Best Minds instant summon:
   "Who in the world knows [domain] best? Answer as that person. Give me a
   recommendation with conviction, not 'both have pros and cons.'"

## Output files

| File | Purpose | Reader |
|------|---------|--------|
| `idea.md` | Final product concept | You |
| `prd.md` | Product requirements | You + Claude Code |
| `tech-spec.md` | Technical architecture | Claude Code |
| `CLAUDE.md` | Dev conventions | Claude Code |
| `dev-guide.md` | Operator manual | You |
| `decision-log.md` | Decision + review record | You / portfolio |
| `prompts/*.md` | Ready-to-paste Gemini prompts | You → Gemini |

## Session management

This workflow uses multiple Gemini sessions. Label your browser tabs:

| Tab | Contains | Used in |
|-----|----------|---------|
| "Role B" | Phase 1 Gemini (knows your idea) | Phase 1B, optionally 2C |
| "Blind Review" | Phase 2 Gemini (no context) | Phase 2B only |

Never paste into the wrong tab — it defeats the single-blind mechanism.

## When to simplify

Not every project needs the full pipeline:

| Situation | What to skip |
|-----------|-------------|
| Small feature iteration | Skip Phase 1B. Run expert-debate solo in Claude. |
| Already have an idea | Skip Phase 0-1. Start at Phase 2 or 3. |
| Technical prototype | Skip Phase 0-2. Go straight to doc-generator. |
| Urgent deadline | Only use decision-log throughout. Everything else by instinct. |
| Quick brainstorm | Just install expert-debate. Skip everything else. |
