# Changelog

All notable changes to Liangyi will be documented here.

## [1.1.0] — 2026-04-18

### Added
- Explicit **Step 1D** (Synthesize merged proposal) between the decision log and Phase 2, closing the gap where Phase 2 reviewers referenced "the merged proposal" without a defined origin.
- Strict separation doctrine codified: `decision-log.md` (your judgment artifact) vs. `idea.md` (the product artifact) — different audiences, different functions.
- Chinese flow diagram node for Step 1D in `docs/METHODOLOGY.zh-CN.md`.
- Demo UI 5th step in Phase 1 — `Liangyi.jsx` and `docs/index.html` now show the synthesis step explicitly.

### Fixed
- Closed implicit gap: Phase 2 previously referenced "the merged proposal" without defining where it came from. Now Phase 1 ends with an explicit synthesis step that produces `idea.md`, and Phase 2 reads only that file.

### Principles
- **Methodology consistency > methodology completeness.** A workflow with 4 well-defined phases beats a workflow with 7 loosely-defined ones. Partial but consistent beats complete but inconsistent.

## [1.0.0] — 2026-04-16

- Initial public release of the Liangyi skill family (5 repositories).
- Main orchestrator (`liangyi`) plus 4 modular skills: `expert-debate`, `blind-review`, `doc-generator`, `decision-log`.
- Interactive ink-wash workflow navigator (bilingual EN/ZH) deployed via GitHub Pages.
- Full methodology documentation in both `docs/METHODOLOGY.md` and `docs/METHODOLOGY.zh-CN.md`.
- MIT license.
