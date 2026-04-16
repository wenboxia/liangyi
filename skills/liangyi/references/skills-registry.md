# Skills Registry

> **This is the author's battle-tested default configuration.** You can use it
> as-is — these Skills are chosen based on real project experience and work well
> together. You can also customize freely: add your own Skills, replace any with
> alternatives you prefer, or remove ones you don't use. The workflow reads this
> file to determine which Skills to recommend at each phase.
>
> This registry is shared with both Model A (Claude) and Model B (recommended:
> Gemini; GPT / Qwen / Doubao / DeepSeek also work) during brainstorm phases.

## Default Skills

### 🔧 Development

- **Superpowers** (obra/superpowers) ⭐152k
  - Capability: Agentic skills framework with agents, hooks, commands, scripts
  - Core features: /review, /loop, /batch, /plan, /simplify
  - Use in phase: Phase 4 (full development cycle)
  - Install: `npx skills add obra/superpowers`

- **Everything Claude Code** (affaan-m/everything-claude-code) ⭐407
  - Capability: Complete Claude Code config collection — agents, skills, hooks, commands, rules, MCPs
  - Core features: Pre-configured multi-agent templates, custom commands, hooks automation
  - Use in phase: Phase 3 (reference for agent configs), Phase 4 (commands and hooks)
  - Install: `npx skills add affaan-m/everything-claude-code`

### 🧠 Thinking

- **Best Minds** (Ceeon/best-minds) ⭐90
  - Capability: Simulator thinking — summon world-class expert perspectives
  - Triggers: "best minds", "top expert", "who knows this best"
  - Use in phase: Phase 1 (expert brainstorm), Phase 2 (critique), Phase 3 (user simulation), Phase 4 (instant decisions)
  - Install: `npx skills add Ceeon/best-minds`

### 📋 Product Management

- **Product Manager Skills** (deanpeters/Product-Manager-Skills) ⭐689
  - Capability: Battle-tested PM framework for PRD, user stories, strategy, prioritization
  - Use in phase: Phase 1 (product-angle brainstorm), Phase 3 (PRD generation)
  - Install: `npx skills add deanpeters/Product-Manager-Skills`

### 🔍 Knowledge & Discovery

- **NotebookLM Skill** (PleasePrompto/notebooklm-skill) ⭐4.8k
  - Capability: Query your Google NotebookLM notebooks from Claude Code
  - Use in phase: Phase 1 (query industry research), Phase 2 (validate with your knowledge base)
  - Install: See repo README for setup

- **Find Skills** (vercel-labs/skills - find-skills)
  - Capability: Auto-discover and recommend Skills matching your current task
  - Use in phase: Phase 4 (find new Skills when you hit capability gaps)

## Customization

To add your own Skills, append them to the relevant category above following the
same format. To replace a Skill, simply edit its entry. To remove one, delete it.
The workflow will adapt to whatever is listed here.

## Advanced: PM Skills sub-skill recommendations

If you have Product Manager Skills installed, these sub-skills can optionally
enhance specific workflow phases. **These are not required steps** — the workflow
runs fine without them. Use them when you want deeper PM rigor.

| Phase | Sub-skill | What it does | How to invoke |
|-------|-----------|-------------|---------------|
| Phase 0 | `jobs-to-be-done` | Validate your idea against real user "jobs" before brainstorming | `/jobs-to-be-done` or ask Claude to run it |
| Phase 0 | `problem-framing-canvas` | Structure a vague idea into a formal problem statement | `/problem-framing-canvas` |
| Phase 1 | `positioning-statement` | Crystallize product positioning after expert debate | `/positioning-statement` |
| Phase 3 | `prd-development` | Replace the default PRD prompt with a multi-step guided PRD workflow | `/prd-development` (recommended) |
| Phase 3 | `user-story` | Generate proper user stories for each core feature in the PRD | `/user-story` |
| Phase 3 | `prioritization-advisor` | Use RICE/ICE/Kano frameworks for MVP scope decisions instead of intuition | `/prioritization-advisor` |
| Phase 3 | `epic-hypothesis` | Structure feature epics with testable hypotheses | `/epic-hypothesis` |
| Phase 4 | `roadmap-planning` | Structure the development roadmap with strategic sequencing | `/roadmap-planning` |
