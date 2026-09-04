---
title: Comparison
sidebar_position: 5
---

# Pros, Cons & Effort

Low / Medium / High are relative comparisons **across these three options
only** — not actual hours or budget. Share sprint capacity / headcount for
a real timeline and cost estimate.

| Option | Pros | Cons | Build Cost | Time to Ship | Ongoing Cost |
|---|---|---|---|---|---|
| **A — Platform Tutorial + Assessment** | Standardized, scalable content; objective skill data; homework engagement | Biggest build; risk of conflicting with Cognitive Snapshot; least human nuance | **High** — authoring tool + delivery UI + assessment engine (scoring logic, content bank, calibration) | **Slowest** — full new subsystem needed before first cohort can use it | **High** — content team must keep authoring lessons + recalibrating assessment |
| **B — Tutor-Based Feedback** | Fastest to ship; cheapest; captures human nuance | No standardization across tutors; subjective/inconsistent; no homework; doesn't scale as evaluation | **Low** — mostly matches the Performance Recording spec already defined | **Fastest** — closest to what's already spec'd | **Low** — no content pipeline, just tutor training/QA |
| **C — Hybrid** | Standardized content + homework; single trusted assessment source; no duplicate/conflicting scores | Still needs full authoring build; assessment stays subjective by design; no objective chess metric | **Medium-High** — same authoring + delivery as A, minus the assessment engine | **Medium** — content pipeline still needed pre-launch, but no scoring logic to design/calibrate | **Medium** — lesson authoring continues; no assessment calibration overhead |

### Reading this table

Build cost for **C is closer to A than to B** — it still needs the full
authoring pipeline, it just skips the assessment-engine half. The real
decision splits into two smaller ones:

1. Build the content/delivery system, or don't (A & C vs. B)
2. If you build it, who owns assessment — the platform or the tutor? (A vs. C)

A spreadsheet version of this table is also available in the ThinkTurf
drive for anyone who wants to model it out further.
