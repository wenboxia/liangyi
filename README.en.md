<p align="center">
  <img src="docs/images/banner.png" alt="Liangyi · cross-vendor multi-agent workflow for refining product ideas" width="880">
</p>

<p align="center">
  <a href="https://liangyi-five.vercel.app"><strong>Live demo</strong></a> &middot;
  <a href="#quick-start"><strong>Quick start</strong></a> &middot;
  <a href="#architecture"><strong>Architecture</strong></a> &middot;
  <a href="#evaluation"><strong>Evaluation</strong></a> &middot;
  <a href="README.md"><strong>中文</strong></a>
</p>

<p align="center">
  <a href="https://liangyi-five.vercel.app"><img src="https://img.shields.io/badge/live%20demo-liangyi--five.vercel.app-D97757" alt="Live demo"></a>
  <img src="https://img.shields.io/badge/python-3.10%2B-3776AB" alt="Python 3.10+">
  <a href="engine/test_guarantees.py"><img src="https://img.shields.io/badge/structural%20tests-102-141413" alt="102 structural-guarantee tests"></a>
  <img src="https://img.shields.io/badge/models-Claude%20%C2%B7%20GPT%20%C2%B7%20DeepSeek%20%C2%B7%20GLM-8FA3B3" alt="Models: Claude · GPT · DeepSeek · GLM">
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue" alt="MIT License"></a>
</p>

<p align="center">
  <img src="docs/images/demo.gif" alt="Recording of a live run: round 1 routes back to P1, round 2 reruns the whole chain, one decision at each HITL stop in each round, v5 shipped" width="820">
  <br><sub>Recording of a live run (hitl mode, time-compressed): pick an example idea → round 1 routes back to P1 → round 2 reruns the whole chain → one decision at each stop in each round → v5 shipped. The UI is in Chinese.</sub>
</p>


# Liangyi · Cross-vendor multi-agent workflow for refining product ideas

One product idea in; one proposal out, after four independent critiques. Seven role agents with isolated contexts, spread across three vendors and assigned by base-model coordinate: the idea is first restated faithfully, two opposing experts draft without seeing each other and are merged, then the draft goes through investor critique → zero-context blind review → drift diagnosis → premise teardown, and finally the severity of the arguments decides whether to ship, restart from the top, or rerun only the critiques.

**Why: a single model that writes and reviews its own work cannot see its own blind spots.**

|        | Stage | What happens |
| ------ | --- | --- |
| **01** | Restate and draft adversarially | P0 restates the idea faithfully; P1.0 generates two opposing roles and checks for fake opposition; the two experts draft blind to each other; the scribe merges them into v1 |
| **02** | Four independent critiques | Investor critique → blind review → drift diagnosis → premise teardown. Every critique opens a new window; every revision is made by the same scribe window |
| **03** | Grade and route | Teardown arguments are graded by "hits a premise × highly specific", and a rule picks one of three exits: back to P1 (full rerun) / back to P2 (rerun the critiques) / done. Round 2 opens every window fresh; capped at two rounds |

<sub>一念生两仪，两仪成决策 — one thought gives rise to two polarities; the two polarities make a decision.</sub>

## Contents

- [Live demo](#live-demo)
- [The problem](#the-problem)
- [Architecture](#architecture): [Overview](#overview) · [Multi-agent system design](#multi-agent-system-design) · [Seven roles and their models](#seven-roles-and-their-models) · [Three exits](#three-exits) · [Full state machine](#full-state-machine)
- [Evaluation](#evaluation)
- [Repository layout](#repository-layout) · [Further reading](#further-reading) · [Quick start](#quick-start) · [Other projects by the author](#other-projects-by-the-author)

## Live demo

**https://liangyi-five.vercel.app** — type an idea and watch it go through all 13 steps; when round 1 routes back, round 2 runs straight after. The page ships three examples: a subscription manager, an error-diagnosis assistant for production services, and VoyageGuard, a travel-weather decision agent (the author's own project).

The demo tier uses three cheap models on three different coordinates (gpt-5.6-luna · deepseek-v4-flash · glm-4-flash). One round takes about 6–10 minutes and about $0.1. Each IP can start 3 new chains per day.

- **Two modes**: "auto" runs straight through; "human judgment" stops at drift rollback (2C) and the teardown verdict (2D) in every round and shows a decision card.
- **Decision card**: at 2C it leads with a one-line "you wanted X, it has become Y" summary, with the drift diagnosis underneath; at 2D it shows the scribe's grading table and verdict for every teardown argument. Both offer the same three options as the CLI plus an optional instruction. "Accept" reuses the output already produced, with no extra model call; 2C "roll back what I specify" / "keep what I specify" or 2D "revise per my instruction" reruns that one step with your instruction; 2D "the premise really is wrong" takes the back-to-P1 exit.
- **Run controls**: stop, resume, retry only the failed step, download the full run record (organised by round). The server is stateless; the run directory travels in the request body.

<p align="center">
  <img src="docs/images/decision-card.png" alt="Decision card shown when the hitl run stops at drift rollback" width="720">
</p>

## The problem

Ask an AI about your idea and it agrees with you. Ask again — still agrees. Three rounds later the plan looks polished, but nothing in it was ever seriously opposed. **Its boundaries were drawn by the model's compliance, not by your judgment.**

| Asking one model directly | Liangyi |
| --- | --- |
| The same model writes the plan and judges it | Writing and reviewing happen in separate windows; Expert B, the blind review and the premise teardown come from vendors and alignment lineages different from the scribe's |
| All feedback arrives at once, several frames to weigh together | Four critiques run in sequence, one round at a time, and the scribe decides item by item what to accept; every revision comes from the same scribe window, so the plan doesn't become a collage of several AIs |
| The plan drifts and nobody notices | P2C compares v1 with v3 specifically for drift; 2C-rollback reverts it |
| A wrong premise gets polished anyway | P2D's job is to attack the direction's premises; the scribe grades every argument, and two or more kill shots send the chain back to P1 for a full second round from the original idea |
| You can't see why anything changed | Every step's input files, output file, tokens and cost go into the trace, plus the reasoning whenever the model returns it; every accept / reject / rollback reason goes into the decision log |

## Architecture

### Overview

Adversarial drafting → four independent critiques → grading and routing; the seven role agents map to three model slots by base-model coordinate.

<p align="center">
  <img src="docs/images/architecture.en.png" alt="Liangyi overview: adversarial drafting, four independent critiques, grading and routing, and how the seven role agents map to model slots" width="880">
</p>

### Multi-agent system design

| Aspect | How | Code |
| --- | --- | --- |
| **Loop** | 13 deterministically orchestrated steps; after 2D-fix the grading rule picks one of three exits (back to P1 / back to P2 / done). Round 2 opens every window fresh, two rounds max, and round 2 is not started once cumulative spend reaches $3. The CLI and the web entry share the same routing | [`orchestrator.py`](engine/orchestrator.py) `route()` `advance()` `run_chain()` |
| **Multi-agent orchestration** | 7 role agents fixed to three model slots by role; each slot's model is chosen across vendors by two coordinates, conflict bias × corpus culture; 3 hard rules are checked before a run and a violation refuses to start | [`config.py`](engine/config.py) `check_hard_rules()` |
| **Context isolation** | One independent message array per role; the blind window starts from an empty list on every call and writes no history back, resume replay skips it, and an explicit history injection raises | [`window.py`](engine/window.py) |
| **HITL** | 2 mandatory stops (2C-rollback, 2D-fix), in every round. At 2C the person judges "is this still what I wanted?", not which design is better; at 2D the person judges whether the attacks hit the premise or can be absorbed within the framework, and "the premise really is wrong" takes the back-to-P1 exit | [`gate.py`](engine/gate.py) `PRESETS` [`interact.py`](engine/interact.py) [`digest.py`](engine/digest.py) |
| **State** | Resume continues in the latest round: finished steps are skipped and their turns are replayed into the scribe window, so every revision still comes from the same scribe | [`orchestrator.py`](engine/orchestrator.py) `restore()` · [`run.py`](engine/run.py) `--resume` |
| **Trace** | One line per step: round, window, model, input files, output file, tokens, cost, duration, plus the reasoning whenever the model returns it; itemized accept / reject / rollback reasons go into the decision log; each round's verdict and the closing reason go into run.json | [`trace.py`](engine/trace.py) |

Two shadow detectors — P0 faithfulness and 2A/2B-fix scope creep — run in the background in every mode (gpt-5.6-luna, majority of 3 votes) and only log; they never interrupt.

### Seven roles and their models

Base-model coordinates have two dimensions. **Dimension A · conflict bias**: A1 norm-first (a written norm independent of the task outranks the task — Claude, Gemini) / A2 authority-first (the norm is a chain of command — GPT) / A3 task-first (no norm layer independent of the task can be found in public material; reward design centres on task completion — DeepSeek, Kimi, GLM). **Dimension B · corpus culture**: B1 English-native / B2 Chinese-native / B3 bilingual core.

| Role agent | Slot | Primary model | Coordinate | Job |
| --- | --- | --- | --- | --- |
| Expert A | anchor | claude-sonnet-5 | A1·B1 | P0 restatement, P1.0 role generation, P1 draft |
| Expert B | divergent_a | deepseek-v4-pro | A3·B3 | Drafts independently, never sees A |
| Scribe | anchor | claude-sonnet-5 | A1·B1 | Merges into v1 and makes every revision |
| Investor critic | anchor | claude-sonnet-5 | A1·B1 | Fresh window, no authorship baggage |
| Blind reviewer | divergent_b | glm-5.3 | A3·B2 | Zero context, receives only the plan text |
| Informed reviewer | anchor | claude-sonnet-5 | A1·B1 | Compares v1 and v3 for drift |
| Premise teardown | divergent_a | deepseek-v4-pro | A3·B3 | **Must be task-first** (enforced before a run). Design rationale: a model with a norm layer softens the one cut that matters |

| Slot | Primary (CLI default) | Demo (web) |
| --- | --- | --- |
| anchor | claude-sonnet-5 · A1·B1 | gpt-5.6-luna · A2·B1 |
| divergent_a | deepseek-v4-pro · A3·B3 | deepseek-v4-flash · A3·B3 |
| divergent_b | glm-5.3 · A3·B2 | glm-4-flash · A3·B2 |

**3 hard rules**, checked before a run; a violation refuses to start:

1. Only models whose dimension A is known. Vendors that don't publish their post-training goals get no window (Qwen, Doubao, MiniMax) — the project holds a working Qwen key and still doesn't use it; a rule only counts if it binds its author
2. The four P2 critique windows must not all sit on one coordinate: at least two distinct coordinates. Same coordinate throughout is fake coverage
3. The premise teardown must be an A3 task-first model

"The blind reviewer has zero context" is guaranteed at runtime by `window.py`: every call to the blind window starts from an empty message list, resume replay skips it, and an explicit `inject_history()` raises `ZeroContextViolation`, locked by a test.

<details>
<summary><b>Six design principles</b></summary>

1. **Four-axis divergence** — model identity, role, context and scope are four independent axes, each mainly activated at one step: P1's two experts sit on different base models (identity), P2A puts the same base model in an investor's role (role), P2B has zero context (context), P2C compares v1 with v3 as a whole (scope)
2. **P2 crosses coordinates** — at least two distinct coordinates among the four critique windows; same coordinate = fake coverage. Checked before a run; no pass, no run
3. **Blind = zero context** — give it background and it starts guessing intent. The blind window starts empty on every call and receives only the plan text
4. **Author ≠ critic** — the scribe window makes every revision; critiques and reviews each open fresh
5. **Linear chain** — the four critiques run in sequence and the scribe revises against one critique per round, so no one has to hold four frames at once
6. **The informed review checks drift, not errors** — detail errors belong to 2A; it asks whether, after answering two rounds of critique, the plan has moved away from its original positioning

</details>

### Three exits

The last step grades every teardown argument: hitting a premise is K-level, being highly specific is H-level, and an argument with both is a **kill shot**. The exit rules are fixed outside the system: "≥ 2 kill shots → back to P1" and the round-2 stop condition are written into the 2D-fix prompt, and the full three-exit rule is written as code, `route()`. The scribe grades under the rule and writes a 【判定】 verdict; a back-to-P1 verdict opens round 2 for a full rerun; when v5 is shipped the code re-checks the grading table — ≥ 2 kill shots in round 1 still go back to P1, and ≥ 60% premise-level arguments go back to P2.

| Exit | Condition | Then |
| --- | --- | --- |
| Back to P1 · full rerun | Round 1 has ≥ 2 kill shots — the direction is overturned; or, in hitl, a person rules the premise wrong | Round 2: every window reopens and the chain restarts from P0 with the original idea; the roles generated in P1.0 are kept |
| Back to P2 · rerun the critiques | Round 1 shipped v5 but ≥ 60% of the arguments are premise-level | Round 2: the previous v5 becomes the new v1, P0/P1 outputs are kept, and the four critiques with their revisions rerun |
| Done · ship v5 | Otherwise; a back-to-P1 verdict in round 2 is overridden by the stop condition and v5 is shipped | v5 is the output |

Two rounds max; round 2 is not started once cumulative spend reaches $3. In hitl mode the 2D stop adds "the premise really is wrong": in round 1 it takes the back-to-P1 exit, in round 2 it closes the chain with a judgment file.

### Full state machine

The full auto / hitl state machines (Mermaid, Chinese labels) are in the [Chinese README](README.md#完整状态机); sources are [`docs/flow-auto.mmd`](docs/flow-auto.mmd) and [`docs/flow-hitl.mmd`](docs/flow-hitl.mmd), generated by [`docs/visualizations/build_flow_mmd.py`](docs/visualizations/build_flow_mmd.py).

## Evaluation

Take a project the author already finished — [VoyageGuard, a travel-weather decision agent](https://github.com/wenboxia/VoyageGuard) — reconstruct the idea as it stood before the PRD (see [`seed.md`](retrospective/voyageguard/seed.md)), run it automatically, and compare with the rework list from its real development history. The atomic-point criteria and the rework list were both sealed before the run; the chain received only the idea.

<p align="center">
  <img src="docs/images/retro-rework.en.png" alt="The 7 VoyageGuard rework items that trace back to the original PRD: the original PRD made all 7 mistakes by definition, one single-model call avoided 1, Liangyi's 13 steps avoided 4" width="820">
</p>

**VoyageGuard's rework list contains 7 product mistakes that trace back to the original PRD. Liangyi's 13 automatic steps avoided 4 of them in advance; the same idea sent to a single model in one call avoided 1.** Full walk-through: [`docs/case-voyageguard.md`](docs/case-voyageguard.md) (Chinese).

<details>
<summary><b>Atomic points: the chain argues back at the author</b></summary>

<br>

<p align="center">
  <img src="docs/images/atomic-survival.en.png" alt="How many of 14 atomic points are upheld, narrowed or altered, or overturned in the v0 baseline and in v1 to v5" width="820">
</p>

The raw idea is first split into 14 atomic points, each judged in one of four states (upheld / narrowed or altered / not upheld / can't judge), and every verdict must quote the plan. After the teardown, 8 are upheld, 4 narrowed or altered and 2 not upheld; the single-call baseline upholds 12. The two points not upheld are "internally, a hand-written agent loop" and "red-line rules written straight into the prompt"; v5 replaced them with a deterministic rule engine and three-tier thresholds with sources.

</details>

## Repository layout

```
engine/          runnable multi-agent workflow: orchestration, window isolation, routing and the multi-round loop, detectors, trace
  prompts/       prompts for every step, shared with the web entry
  fixtures/      real grading tables and judgment files used by the tests
  test_guarantees.py   102 structural-guarantee tests
web/             web entry: one stateless request per step, the run directory travels in the body
api/             Vercel entry function and rate limiting
scenarios/       scenario files (seed + optional pre-written roles)
docs/            case study, state-machine sources, images for this page and their generators
retrospective/   VoyageGuard retrospective: input seed, sealed atomic points and rework list, judging matrix
```

## Further reading

| Question | Where (Chinese) |
| --- | --- |
| Who runs each step of the multi-agent workflow, the two modes | [`engine/PIPELINE.md`](engine/PIPELINE.md) |
| Engineering notes: resume, P1.0 role generation, lessons from real runs | [`engine/README.md`](engine/README.md) |
| A real project re-run from its original idea | [`docs/case-voyageguard.md`](docs/case-voyageguard.md) |
| Web entry API and deployment | [`web/DEPLOY.md`](web/DEPLOY.md) |

## Quick start

```bash
pip install -r requirements.txt
cp .env.example .env                                         # fill in keys; comments say which vendor serves which window
python3 -m engine.run --check                                # preflight: 3 hard rules + whether each provider's key is set
python3 -m engine.run -s scenarios/voyageguard.yaml          # one full chain, primary tier, auto mode (round 2 runs when routed back)
python3 -m engine.run -s scenarios/voyageguard.yaml -p demo --mode hitl   # cheap demo tier + the two stops
python3 -m engine.run --resume runs/<run-dir>                # resume an interrupted run
python3 -m engine.test_guarantees                            # structural tests: no model calls, no cost
```

Inspect the result:

```bash
python3 -m engine.inspect runs/<run-dir>                          # who ran each step, cost, rounds, verdict
python3 -m engine.inspect runs/<run-dir> --step P2D               # one step's input and output
python3 -m engine.inspect runs/<run-dir> --reasoning              # reasoning traces for every step
python3 -m engine.inspect runs/<run-dir> --diff idea-v1.md idea-v5.md
```

Local web entry: `python3 web/server.py`, then open `http://127.0.0.1:8765`.

## Other projects by the author

| Project | What it is |
| --- | --- |
| [**AIRadar**](https://github.com/wenboxia/airadar) | A daily scheduled AI-industry intelligence workflow · [live](https://wenboxia.github.io/airadar/) |
| [**VoyageGuard**](https://github.com/wenboxia/VoyageGuard) | An AI-agent travel-weather risk decision tool for flights and boats, LLM reasoning backed by a rule-engine safety net · [live](https://voyageguard-two.vercel.app). The retrospective above uses its real development history |

## Author

Wenbo Xia (夏文博) · AI product manager · [MIT License](LICENSE)
