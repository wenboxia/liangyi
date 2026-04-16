# 两仪 · Liangyi

> **太极生两仪** — *The Supreme Ultimate generates the Two Polarities.*
> — 《易经·系辞》 / *I Ching, Great Commentary*

> 🎴 **[Live Demo → wenboxia.github.io/liangyi](https://wenboxia.github.io/liangyi/)** — Interactive ink-wash workflow navigator

A multi-model adversarial product development workflow for Claude Code.
One product idea generates two opposing expert views.
You synthesize the final decision from their structural tension.
**The disagreement is the feature.**

## Why "Liangyi"?

In the cosmology of the *I Ching* (易经), one of the oldest classical Chinese texts, all complexity unfolds from a single origin through structured opposition. **Taiji (太极)**, the unified whole, gives birth to **Liangyi (两仪)** — the two polarities of yin and yang. From their tension emerges **Sixiang (四象)**, the four dimensions, and from those, the **Bagua (八卦)**, the eight trigrams that describe every situation.

This workflow is a technical implementation of the same philosophical structure:

- One product idea (**Taiji**) splits into two opposing expert views (**Liangyi**)
- The two views generate four dimensions of analysis (**Sixiang**) — PRD, tech spec, dev guide, decision log
- Those ground the full product architecture (**Bagua**) — from concept to shipped code

Single-AI workflows fail because a single model fills its own gaps with its own biases. Liangyi refuses this. It deliberately creates two models with conflicting expert priors, lets them disagree productively, and puts you — the human — in the role that AI cannot occupy: the one who synthesizes.

## The skill family

Liangyi is the **orchestrator**. It combines four standalone skills that can also be installed independently:

| Skill | What it does | Install alone |
|-------|-------------|---------------|
| [expert-debate](https://github.com/wenboxia/expert-debate) | Adversarial brainstorm with conflicting expert roles | `npx skills add wenboxia/expert-debate` |
| [blind-review](https://github.com/wenboxia/blind-review) | Context-free document audit + devil's advocate | `npx skills add wenboxia/blind-review` |
| [doc-generator](https://github.com/wenboxia/doc-generator) | PRD, tech spec, CLAUDE.md, dev guide | `npx skills add wenboxia/doc-generator` |
| [decision-log](https://github.com/wenboxia/decision-log) | Human decision tracking + review | `npx skills add wenboxia/decision-log` |

**Install Liangyi** for the full pipeline with all modules:
```bash
npx skills add wenboxia/liangyi
```

**Or install only what you need** — each skill works independently.

## How it works

```
Raw idea (Taiji 太极)
    ↓
Phase 0: Refine language
    ↓
Phase 1: Two AI models debate as conflicting experts (Liangyi 两仪)
         (e.g., Security Architect vs Growth Hacker)
    ↓
Phase 2: Single-blind review (new Model B session, zero context)
       + Devil's advocate on consensus (with complexity gate)
    ↓
Phase 3: Generate PRD → Tech Spec → CLAUDE.md → Dev Guide (Sixiang 四象)
       + AI-simulated user validation of PRD
    ↓
Phase 4: Development with instant expert summoning (Bagua 八卦)
    ↓
Output: 6 documents + ready-to-copy Model B prompts + decision audit trail
```

## What makes this different

| Liangyi | Typical AI workflow |
|---------|-------------------|
| Structured expert role debates with professional bias | Generic "review my idea" prompts |
| Single-blind review (reviewer has zero context) | All reviewers share full history |
| Devil's advocate when models agree (with complexity gate) | Agreement = done |
| Every human decision logged with reasoning | Human approves/rejects silently |
| Modular — install one skill or all five | Monolithic, all or nothing |

## Batteries included

All reference files ship with the skill — no configuration needed to start:
- `references/expert-roles.md` — recommended expert role pairs by product type
- `references/skills-registry.md` — template for your Skills inventory
- `references/doc-templates.md` — document structure templates

## No API required

Model B prompts are generated as copyable text (auto-copied to clipboard when possible).
No API keys needed. Works with free-tier access to any LLM.

**Model B recommendation:** Gemini is recommended because its training data diverges most
from Claude's, producing higher-quality adversarial tension. GPT, Qwen, Doubao, DeepSeek,
and other capable LLMs also work. The key requirement: use a **different provider** from Claude.

## Session management

The workflow uses multiple Model B sessions. Label your browser tabs to avoid mixing contexts:

| Tab name | Purpose | Used in |
|----------|---------|---------|
| "Role B" | Model B with your idea context | Phase 1 |
| "Blind Review" | Fresh Model B session, zero context | Phase 2 |

## Usage

```
/liangyi                    # Full pipeline
/liangyi phase1             # Just the expert brainstorm
/liangyi phase3             # Just document generation
/liangyi setup              # First-time configuration
```

## Output

| File | Purpose |
|------|---------|
| `idea.md` | Final product concept |
| `prd.md` | Product requirements |
| `tech-spec.md` | Technical architecture |
| `CLAUDE.md` | Development conventions |
| `dev-guide.md` | Step-by-step operator manual |
| `decision-log.md` | Human decisions + AI review findings |
| `prompts/*.md` | Ready-to-paste Model B prompts |

## Philosophy

> "One idea, split by opposing expertise, synthesized by human judgment.
> AI models should produce structured disagreement, not smoothed consensus.
> The I Ching taught this 3,000 years ago: complexity emerges from polarity,
> not uniformity."

## Deep Dive

Read the full methodology whitepaper:

- 📘 [Methodology — English](./docs/METHODOLOGY.md)
- 📗 [完整方法论 — 中文](./docs/METHODOLOGY.zh-CN.md)

Includes phase-by-phase breakdowns, decision-gate rules, Model B prompt templates, session-management protocols, and the reasoning behind every design choice.

## License

MIT
