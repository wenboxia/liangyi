# Liangyi · 两仪

English | [中文](Liangyi.zh-CN.md)

> **Liangyi** (两仪) /lyahng-ee/ — The Two Polarities.
> From the *I Ching* (易经·系辞): "太极生两仪" — *The Supreme Ultimate generates the Two Polarities.* A single unified origin divides into two opposing forces, and the tension between them gives rise to all further complexity.

**A product development methodology that resists AI's dissolution of human independent judgment.**

---

## Quick Start

**Start with [`docs/session-hygiene.md`](docs/session-hygiene.md)** — the operational spec: which AI session runs which step, why, and what each one outputs. Read that and you can run your first project by hand.

For the philosophical foundation and the reasoning behind every hard rule, continue to [`docs/liangyi-workflow-refined.md`](docs/liangyi-workflow-refined.md).

> **Note on [Liangyi.jsx](Liangyi.jsx)**: this repo also contains an interactive visual walkthrough, but **its model selection and coordinate labels are a 2026-04 snapshot and are out of date** — Dimension A was redefined on 2026-08-27. The file carries a prominent staleness notice at the top. Treat `docs/` as authoritative.

---

## What This Methodology Resists

AI increasingly makes judgment calls on behalf of humans across more and more decision points. The result: humans are **progressively absent** from product decisions — the AI's suggestions all sound reasonable, the human clicks "approve," and the moment passes. Over time, product direction gets silently captured by the AI's default preferences (trained-in conservatism, regression to the mean, a tendency to agree with whoever is talking), and the decision-maker loses the "I thought it through myself" capacity that made their judgment worth having.

**Liangyi's core claim**: At key decision points, use **two AIs that are structurally genuinely different** to produce adversarial outputs, and have the **human process the tension** — not the AI. Human decision steps are not a cost of the methodology. They are where the methodology's value lives.

---

## Methodology Structure

The methodology consists of five phases:

| Phase | What happens |
|---|---|
| **P0 · Idea Capture** | Refine the raw idea into a clear statement — no logic changes, no expansion, no challenge |
| **P1 · Adversarial Brainstorm** | Two AIs from different base-model coordinates produce proposals independently; human synthesizes → idea.md |
| **P2 · Four-Step Interrogation Chain** | P2A investor critique / P2B zero-context blind review / P2C informed review (direction-drift diagnosis) / P2D devil's advocate (attacks the premise, not the details) |
| **P3 · Engineering Docs** | Takes the idea.md already locked at the end of P2 and expands it into PRD / Tech Spec / CLAUDE.md / Dev Guide |
| **P4 · Development** | Begin actual development from the engineering docs |

**The lock point**: idea.md is locked the moment the human makes the final call at the end of P2 — that is the P2/P3 boundary. The boundary is deliberate: it stops engineering work already produced from holding the idea decision hostage.

---

## Core Mechanisms

**Four core mechanisms** — The methodology proper contains exactly four: two-AI adversarial generation, zero-context blind review, **human synthesis**, and triggered devil's advocate. Each one had to name the specific failure mode it prevents before it was admitted. Everything below is design grammar, not mechanism.

**Four-axis divergence framework** — Divergence is not one thing. It has four independent axes: AI identity axis (base-model coordinate) / persona axis (role played) / context axis (what information is visible) / scope axis (local critique vs whole-picture review). Each step of the P2 chain primarily activates one of them.

**Cross-dimension base-model coordinate (hard rule)** — Within the P2 chain, at least one pair of base models must not overlap on Dim A or Dim B (loose version; the strict version requires that pair to differ on both). The coordinate has two axes. **Dim A conflict bias** — which way the model defaults when the task and other constraints collide: A1 norm-first (a written, task-independent norm overrides the task — Claude, Gemini) / A2 permission-first (the norm is a chain of authority, not a value claim — GPT) / A3 task-first (no independent norm layer in public material; reward comes entirely from task completion — DeepSeek, Kimi, GLM). Vendors who publish neither post-training objectives nor a norm document are **not used at all** — the methodology requires selection criteria you can explain. **Dim B corpus culture** — B1 English-native / B2 Chinese-native / B3 cross-cultural dual-core. Same-coordinate models share norm constraints and corpus priors; running entirely within one coordinate produces "false coverage." The default pair — Claude A1·B1 vs DeepSeek A3·B3 — crosses both dimensions.

**Multiplicative model** — Methodology output value ≈ divergence (on dimensions relevant to this project) × min(capability_A, capability_B) × match(A, B). Divergence on irrelevant dimensions does not count. Multiplication means: if any one term approaches zero, total output approaches zero — don't pad with AIs that have obvious capability shortfalls.

**Checklists over scores** — The methodology uses qualitative checklists rather than numeric scoring. Numeric scores manufacture false certainty; checklist questions force the human into substantive judgment.

---

## Reference Combinations

**Default combination** — 7 independent sessions:

| Session | Model | Coordinate | Role |
|---|---|---|---|
| Claude-1 | Claude | A1·B1 | P0 refinement + P1 expert A |
| Claude-2 | Claude | A1·B1 | `idea.md` author — writes it, executes every revision (2A-fix / 2B-fix / 2C-rollback / 2D-fix), and produces all of P3 |
| Claude-3 | Claude | A1·B1 | P2A investor critique |
| Claude-4 | Claude | A1·B1 | P2C informed review |
| DeepSeek-1 | DeepSeek | A3·B3 | P1 expert B |
| Kimi-1 | Kimi | A3·B3 | P2B blind review — zero context, hard rule |
| DeepSeek-2 | DeepSeek | A3·B3 | P2D devil's advocate — must be an A3 (task-first) model, hard rule |

Two things this table encodes that are easy to get wrong: **revisions are always executed by Claude-2** — divergence belongs in the review steps, never in the revision step, or `idea.md` degrades into a collage. And **the devil's advocate cannot be Claude** — an A1 norm layer softens the attack exactly where it matters.

A third thing the table encodes: every model here has a **determinable Dim A** — a vendor that publishes neither its post-training objective nor a norm document is not used at all, in any window.

**When Claude is unavailable**: Gemini (A1·B1) replaces Claude-1 through Claude-4; Chinese-side coordinates unchanged

Full reference combinations (including alternates and anti-patterns) in [`docs/session-hygiene.md`](docs/session-hygiene.md#参考组合示例).

---

## Evolution Path

Early v1.0 attempted a **multi-AI role-play + Skills orchestration** implementation path, splitting the methodology into independent skill modules. Subsequent evolution found that skill fragmentation breaks workflow cohesion, and that real divergence doesn't come from "playing different roles" — it comes from **structural differences at the base-model coordinate level** (conflict bias × corpus culture). The current methodology is document-driven, built on **four core mechanisms with human synthesis at the center**; the four-axis framework is the design grammar underneath it, not the thing itself. The `docs/` directory in this repo is the authoritative source.

---

## Full Documentation

| File | Content |
|---|---|
| [`CLAUDE.md`](CLAUDE.md) | Project-level protocol (required reading for Cowork sessions) |
| [`docs/README.md`](docs/README.md) | Documentation index |
| [`docs/liangyi-workflow-refined.md`](docs/liangyi-workflow-refined.md) | Methodology proper (philosophical foundation + full workflow) |
| [`docs/session-hygiene.md`](docs/session-hygiene.md) | Operational rules (AI session numbering, reference combinations, per-step hard rules) |

---

## Project Status

The methodology is currently at a **stage-stable point** — usable for real product work, ready to apply. But the methodology will never be "finished"; it only ever reaches "good enough for this stage." Its evolution is driven by real problems encountered in practical use, not by speculative expansion.

---

## Author

Wenbo Xia (夏文博) · Product Manager, AI
