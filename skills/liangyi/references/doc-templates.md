# Document Templates

## PRD Template (prd.md)

```markdown
# [Product Name] — Product Requirements Document

## 1. Product Overview
- One-sentence description
- Problem being solved
- Target outcome

## 2. Target Users
- Primary persona (with demographics, pain points, goals)
- Secondary persona (if applicable)

## 3. Core Features (MVP)
| Feature | Priority | User Story | Acceptance Criteria |
|---------|----------|------------|-------------------|
| ... | P0/P1/P2 | As a [user], I want [action] so that [benefit] | [Testable criteria] |

## 4. Information Architecture
- Page/screen hierarchy
- Navigation flow
- Key user journeys

## 5. Non-functional Requirements
- Performance targets
- Security requirements
- Accessibility standards

## 6. MVP Scope Boundary
- IN scope for MVP: [list]
- OUT of scope (future iterations): [list]

## 7. Success Metrics
| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| ... | ... | ... |

## 8. Multi-Agent Assessment
- Recommended: single agent / Claude Code Teams
- If Teams: agent role assignments
- Rationale
```

## Tech Spec Template (tech-spec.md)

```markdown
# [Product Name] — Technical Specification

## 1. Stack Selection
| Layer | Choice | Rationale |
|-------|--------|-----------|
| Frontend | ... | ... |
| Backend | ... | ... |
| Database | ... | ... |
| Deployment | ... | ... |

## 2. Project Structure
[Directory tree]

## 3. Module Design
[Core modules with interfaces]

## 4. Development Phases
| Phase | Tasks | Acceptance Criteria | Estimated Effort |
|-------|-------|-------------------|-----------------|
| 1 | ... | ... | ... |

## 5. Skills Dispatch Table
| Phase | Task | Recommended Skill | Rationale |
|-------|------|------------------|-----------|
| ... | ... | ... | ... |

## 6. Risk Register
| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| ... | H/M/L | H/M/L | ... |
```

## Decision Log Template (decision-log.md)

```markdown
# Decision Log

> This document records every significant human decision made during the
> product development process. Each entry captures what the AI recommended,
> what the human chose, and WHY — the judgment that AI cannot replicate.

## Decision Point 0: Expert Role Assignment
- Claude role: [name + reasoning]
- Gemini role: [name + reasoning]
- Tension rationale: [why this pair]

## Decision Point 1: [Topic]
- Role A position: [what + underlying logic]
- Role B position: [what + underlying logic]
- Core divergence: [the fundamental disagreement]
- **My choice:** [decision]
- **My reasoning:** [why — what context, intuition, or knowledge led here]
- **Why AI can't make this call:** [the human judgment involved]

## Single-Blind Review
- Gemini's one-sentence understanding: [record]
- Divergence from my intent: [where, if any]
- Root cause: [expression problem / direction problem / none]
- **Action taken:** [revised PRD / changed direction / confirmed]
```
