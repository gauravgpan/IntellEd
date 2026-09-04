---
title: A — Platform Tutorial + Assessment
---

# A — Platform Tutorial + Assessment

Full digital curriculum authoring, in-session delivery, homework, **and** a separate chess-specific assessment engine, distinct from the Cognitive Skill Snapshot.

Biggest build of the three options: an authoring pipeline, delivery tooling, and an assessment engine with its own scoring/calibration.

```mermaid
%% ThinkTurf — Business Workflow: Platform Chess Tutorial + Chess-specific Assessment
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

    %% ============ CURRICULUM AUTHORING ============
    GATE --> CA1
    subgraph CUR["Curriculum Authoring — ThinkTurf content team"]
        CA1["Author lesson<br/>(header, objective, board position, notes)"] --> CA2["Build position: drag-drop setup helper<br/>or import chapter from existing book"]
        CA2 --> CA3["Live preview + version"]
        CA3 --> CA4["Publish to lesson library"]
    end

    %% ============ DELIVERY: IN-SESSION + HOMEWORK ============
    CA4 --> DEL1
    subgraph DELIVERY["Delivery — In-session + Homework"]
        DEL1["Tutor opens scheduled class<br/>+ assigned lesson"] --> DEL2["Tutor delivers lesson live<br/>(in-person, board + auto-move player)"]
        DEL2 --> DEL3["Attendance marked"]
        DEL3 --> DEL4["Homework assigned<br/>(puzzles/drills tied to lesson)"]
        DEL4 --> DEL5["Student completes homework<br/>(self-paced, outside class)"]
    end

    %% ============ CHESS-SPECIFIC ASSESSMENT (separate & additional) ============
    DEL5 --> CH1
    subgraph CHESS["Chess-specific Assessment — separate module, NOT the Cognitive Snapshot"]
        CH1{"Assessment due?<br/>(per curriculum domain mapping)"}
        CH1 -->|Yes| CH2["Run chess skill assessment<br/>(e.g. tactics/puzzle rating)"]
        CH2 --> CH3["Store result vs Student ID"]
        CH3 --> CH4["Trend visible on student profile"]
        CH1 -->|Not yet| DEL1
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
    CH4 --> REP
    CS4 --> REP
    REP["Reports & Analytics<br/>chess assessment + cognitive snapshot +<br/>homework/attendance + school academic data (pseudonymous)"] --> OUT["Dashboards: Parent / School / ThinkTurf Ops"]
```
