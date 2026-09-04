---
title: B — Tutor-Based Feedback
---

# B — Tutor-Based Feedback

No platform-hosted curriculum or homework. Tutors teach from a lightweight, centrally-issued lesson plan. Attendance plus a per-session note and optional rating is the entire progress record.

Closest to what's already spec'd in Performance Recording — smallest build.

```mermaid
%% ThinkTurf — Business Workflow: Tutor-based Feedback + Progress Capture
%% Shared blocks with the other workflow file: Onboarding, Cognitive Skill Snapshot
flowchart TD

    %% ============ ONBOARDING (shared) ============
    subgraph OB["Onboarding (shared, MVP)"]
        T1["Tutor applies"] --> T2["Verified<br/>(credentials + background check)"]
        T2 --> T3{"Admin approval"}
        T3 -->|Approved| T4["Tutor: Active"]
        T3 -->|Rejected| T5["Tutor: Rejected"]

        S1["School: Enquiry"] --> S2["Agreement signed"]
        S2 --> S3["School: Onboarded"]
        S3 --> S4["School: Active"]

        P1["Student/Parent: Trial / Pending<br/>(roster added by school or self-onboard)"] --> P2{"Parent consent captured?"}
        P2 -->|Yes| P3["Student/Parent: Active<br/>linked to School + Tutor"]
        P2 -->|No| P4["Blocked — cannot proceed"]
    end

    T4 --> GATE["All parties Active"]
    S4 --> GATE
    P3 --> GATE

    %% ============ CURRICULUM REFERENCE (lightweight) ============
    GATE --> CR1
    subgraph CUR["Curriculum Reference — lightweight, no authoring tool"]
        CR1["ThinkTurf provides standard lesson plan / syllabus<br/>(topic, objective, reference positions —<br/>often imported from existing book)"] --> CR2["Tutor receives plan ahead of class"]
    end

    %% ============ DELIVERY: IN-SESSION ONLY ============
    CR2 --> DEL1
    subgraph DELIVERY["Delivery — In-session only"]
        DEL1["Tutor opens scheduled class"] --> DEL2["Tutor teaches live, in-person<br/>using lesson plan (no digital tutorial)"]
        DEL2 --> DEL3["Attendance marked"]
    end

    %% ============ PERFORMANCE RECORDING (core of this model) ============
    DEL3 --> PR1
    subgraph PERF["Performance Recording — tutor-authored, core module"]
        PR1["Tutor logs short performance note<br/>per session"] --> PR2["Optional 1–5 rating<br/>for trend-spotting"]
        PR2 --> PR3["Performance history stored,<br/>viewable per student in order"]
        PR3 --> PR4["Parent-visible summary<br/>(internal notes stay hidden)"]
    end

    %% ============ COGNITIVE SKILL SNAPSHOT (shared module) ============
    DEL3 --> CS1
    subgraph SNAP["Cognitive Skill Snapshot — standalone, common to both workflows"]
        CS1{"6-month cycle due?"}
        CS1 -->|Yes| CS2["Consent already captured at onboarding"]
        CS2 --> CS3["Run 6-domain snapshot<br/>(age-banded A/B/C)"]
        CS3 --> CS4["Store result vs Student ID"]
        CS1 -->|Not yet| DEL1
    end

    %% ============ REPORTS ============
    PR4 --> REP
    CS4 --> REP
    REP["Reports & Analytics<br/>performance notes + cognitive snapshot +<br/>attendance + school academic data (pseudonymous)"] --> OUT["Dashboards: Parent / School / ThinkTurf Ops"]
```
