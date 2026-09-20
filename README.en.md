# Liangyi · 两仪

**Try it live →** https://liangyi-five.vercel.app — type an idea, watch it go through all 13 steps (demo tier, 3 runs per person per day).

**One idea, two polarities, one decision.**

One idea in, one proposal out — after four rounds of adversarial review.

- **P1 adversarial drafting**: two experts on different base-model coordinates draft independently; a scribe merges them into v1.
- **P2 four-round critique chain**: investor critique → zero-context blind review → drift detection with rollback → premise teardown with kill-shot grading. The scribe and each of the four critiques run in separate windows that share no context; the blind review, the premise teardown and Expert B come from vendors and alignment lineages different from the scribe's.
- **Multi-exit loop**: the teardown verdict drives rollback — back to P1 (full rerun), back to P2 (re-run the critique chain), or structural-deadlock exit; capped at two rounds.
- **HITL nodes**: human decision points at drift-rollback and teardown-verdict; switch between `auto` and `hitl` tiers.

Why: **a single model that writes and reviews its own work cannot see its own blind spots.**

**Try it online →** (link after deployment)　Paste an idea, watch it go through all 13 steps.

[中文](README.md)

---

## The problem

Ask an AI about your idea and it agrees with you. Ask again — still agrees. Three rounds later the plan looks polished, but nothing in it was ever seriously opposed. **Its boundaries were drawn by the model's compliance, not by your judgment.**

Liangyi separates the roles: the model that writes and the models that critique must sit at different base-model coordinates; four critique rounds come from four freshly opened windows; each round handles one critique; at the end a human (or a rule) decides "is this still what I wanted?"

## Quick start

```bash
pip install -r requirements.txt
cp .env.example .env        # four keys: OpenRouter / DeepSeek / Moonshot / Zhipu
python3 -m engine.run --check
python3 -m engine.run -s scenarios/what-to-wear.yaml
python3 -m engine.inspect runs/<run-dir>
```

Two modes: `--mode auto` never stops; `--mode hitl` pauses at the two boundary decisions and offers two frontier-model opinions at each.

Local web entry: `python3 web/server.py` → `http://127.0.0.1:8765`.

## The 13 steps

```
P0    Faithful refinement     Tighten the idea; no logic changes, no expansion, no critique
P1.0  Generate opposing roles Two structurally opposed expert roles, with a fake-tension check
P1A   Expert A proposal       ┐ Cannot see each other; different coordinates
P1B   Expert B proposal       ┘
P1.4  Synthesize v1           The scribe window merges them into one position

P2A   Investor critique       Market & business logic         → 2A-fix → v2
P2B   Zero-context review     A stranger who sees only the text → 2B-fix → v3
P2C   Informed review         Compare v1 vs v3 for drift        → 2C-rollback → v4
P2D   Devil's advocate        Attacks premises only             → 2D-fix, graded → v5
```

Every critique comes from a **new window at a different coordinate**; every revision is made by the **same scribe window** — divergence lives in review, never in editing, or the document becomes a collage.

The last step grades each argument (hits a premise? × concrete?) and routes to one of four endings: produce v5 · back to P1 (direction overturned) · back to P2 (premises questioned but not killed) · structural deadlock. Two rounds max, $3 cap per chain.

## Why these models

Two things are judged separately: **can the coordinate be determined** (hard rule) and **is the model capable enough**.

**Dimension A · conflict bias**: A1 norm-first (a written norm independent of the task overrides it — Claude, Gemini) / A2 authority-first (the norm is a chain of who-decides, not a value claim — GPT) / A3 task-first (no independent norm layer; reward comes entirely from task completion — DeepSeek, Kimi, GLM). **Dimension B · corpus culture**: B1 English-native / B2 Chinese-native / B3 bicultural.

**Vendors that have not disclosed their post-training objective are excluded from every combination** (Qwen, Doubao, MiniMax) — even with working keys in hand.

**Default: Claude × 4 + DeepSeek × 2 + GLM × 1.** Crossing dimensions is the hard rule; specific models are replaceable. The online demo uses the same structure on cheap tiers: GPT × 4 + DeepSeek Flash × 2 + GLM Flash × 1 — measured at 8–10 minutes and $0.07–0.09 per chain.

## Six core mechanisms

1. **Four-axis divergence** — any pair of windows should differ on model identity, role, context, and scope
2. **P2 chain crosses at least one coordinate dimension** — same coordinate = fake coverage; checked in code before launch
3. **Blind review = zero context** — the window actively refuses any injected history
4. **Author ≠ critic** — one scribe window does all edits; critics and reviewers are always fresh
5. **Linear chain against cognitive overload** — one critique at a time
6. **Informed review looks for drift, not errors** — has the plan moved away from its original positioning?

## Going deeper

| Topic | File |
|---|---|
| The methodology itself | [`docs/liangyi-workflow-refined.md`](docs/liangyi-workflow-refined.md) (Chinese) |
| A real project re-run from its original idea | [`docs/case-voyageguard.md`](docs/case-voyageguard.md) |
| Why those numbers can be trusted | [`docs/evaluation.md`](docs/evaluation.md) |
| Who runs each step, the two modes | [`engine/PIPELINE.md`](engine/PIPELINE.md) |
| Twenty compliance checks, failures included | [`engine/VALIDATION.md`](engine/VALIDATION.md) |

## What is and isn't verified

**Verified**: the chain runs end-to-end on 13 real runs (including one full retrospective comparison); 83 structural-guarantee tests lock mechanisms rather than wording; loop exits A (back to P1) and B (back to P2) were driven offline with real judgment outputs.

**Not verified**: no real run has yet completed a second round; the structural-deadlock exit C needs an issue-overlap argument the orchestrator never passes, so it is unreachable in real runs and untested; judge and re-judge come from the same vendor; the retrospective is one project, run once.

One more thing, stated plainly: **the devil's-advocate verdict is unstable.** Same scenario, same document, three runs graded "5 premise hits / 0 fatal", "5 / 2", "0 / 0". The one point in the chain that can overturn direction sits on a dice roll. Details in [`docs/evaluation.md`](docs/evaluation.md).

## Author

Wenbo Xia · AI product manager. MIT License.
