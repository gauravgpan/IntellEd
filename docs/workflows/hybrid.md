---
title: C — Hybrid
---

# C — Hybrid

Keeps Option A's content delivery (in-session digital board + homework) but drops the separate chess-assessment engine. Homework/lesson-completion data is surfaced to the tutor as **context only** — the tutor's note and rating remain the single source of truth for progress.

Avoids two competing 'assessment' signals (a risk in Option A), at close to Option A's build cost.

```mermaid
%% ThinkTurf — Business Workflow: Hybrid — Platform-delivered Content, Tutor-owned Assessment
%% Shared blocks with the other two workflow files: Onboarding, Cognitive Skill Snapshot
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

    %% ============ CURRICULUM AUTHORING (same pipeline as full-platform option) ============
    GATE --> CA1
    subgraph CUR["Curriculum Authoring — ThinkTurf content team"]
        CA1["Author lesson<br/>(header, objective, board position, notes)"] --> CA2["Build position: drag-drop setup helper<br/>or import chapter from existing book"]
        CA2 --> CA3["Live preview + version"]
        CA3 --> CA4["Publish to lesson library"]
    end

    %% ============ DELIVERY: IN-SESSION + HOMEWORK ============
    CA4 --> DEL1
    subgraph DELIVERY["Delivery — In-session + Homework"]
        DEL1["Tutor opens scheduled class<br/>+ assigned lesson"] --> DEL2["Tutor delivers lesson live<br/>(in-person, digital board + auto-move player)"]
        DEL2 --> DEL3["Attendance marked"]
        DEL3 --> DEL4["Homework assigned<br/>(puzzles/drills tied to lesson)"]
        DEL4 --> DEL5["Student completes homework<br/>(self-paced, outside class)"]
    end

    %% ============ ENGAGEMENT SIGNAL (telemetry, not a score) ============
    DEL5 --> ENG1
    subgraph ENG["Engagement Signal — telemetry only, no independent score"]
        ENG1["System logs lesson coverage<br/>+ homework completion"] --> ENG2["Surfaced to tutor as context"]
    end

    %% ============ PERFORMANCE RECORDING (tutor-owned, single source of truth) ============
    DEL3 --> PR1
    ENG2 --> PR1
    subgraph PERF["Performance Recording — tutor-owned, single source of truth"]
        PR1["Tutor logs session note<br/>(informed by engagement context)"] --> PR2["Optional 1–5 rating"]
        PR2 --> PR3["Performance history stored,<br/>viewable per student in order"]
        PR3 --> PR4["Parent-visible summary<br/>(internal notes stay hidden)"]
    end

    %% ============ COGNITIVE SKILL SNAPSHOT (shared module) ============
    DEL3 --> CS1
    subgraph SNAP["Cognitive Skill Snapshot — standalone, common to all three workflows"]
        CS1{"6-month cycle due?"}
        CS1 -->|Yes| CS2["Consent already captured at onboarding"]
        CS2 --> CS3["Run 6-domain snapshot<br/>(age-banded A/B/C)"]
        CS3 --> CS4["Store result vs Student ID"]
        CS1 -->|Not yet| DEL1
    end

    %% ============ REPORTS ============
    PR4 --> REP
    CS4 --> REP
    REP["Reports & Analytics<br/>tutor performance history + engagement data +<br/>cognitive snapshot + school academic data (pseudonymous)"] --> OUT["Dashboards: Parent / School / ThinkTurf Ops"]
```
