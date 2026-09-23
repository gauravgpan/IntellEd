# ThinkTurf MVP: Technical Design (Tutor workflows first)

Scope: Must-have items only, from the design-blocks doc. Flow: hybrid (Option C). App users in MVP: **Founder, Admin staff, Tutor**. Schools, students and guardians exist as records only, with no login.

Items marked *(proposed)* are my assumptions, not decisions from the doc.

---

## 1. Module map

```mermaid
flowchart LR
  subgraph Actors["MVP app users"]
    F["Founder"]
    A["Admin staff"]
    T["Tutor"]
  end
  subgraph Core["Must-have modules"]
    ON["Onboarding<br/>Tutor, School, Student records"]
    CL["Class view and Scheduling"]
    CU["Curriculum<br/>Lesson schema, Handouts"]
    PR["Performance recording"]
    AS["Assessments<br/>Cognitive Snapshot, Paper uploads"]
    RP["Reports<br/>Cognitive analytics, Trendline"]
    CM["Communications<br/>Scheduling, Reminders"]
  end
  subgraph Platform["Platform services"]
    AU["Auth: OTP and role-based access"]
    EX["Image extraction worker"]
    TH["Default ThinkTurf theme"]
  end
  DB[("Relational DB")]
  OS[("Object storage")]

  Actors --> AU
  AU --> Core
  ON --> CL
  CU --> CL
  CL --> PR
  CL --> CM
  AS --> EX
  EX --> DB
  AS --> OS
  CU --> OS
  PR --> RP
  AS --> RP
  Core --> DB
```

---

## 2. Data model (ER)

Key design points:

- `STUDENT` holds only a pseudonymous token. All PII lives in `STUDENT_IDENTITY`, which also carries the school's own student ID (the school ID to unique ID mapping).
- Tutors reach schools through `TUTOR_ASSIGNMENT` (many-to-many, via class).
- A six-month re-assessment is a new `CSS_ASSESSMENT` row with `cycle_no + 1`.
- The class view is a derived read model. Its only new table is `CLASS_LESSON_PLAN`, the ordered lessons planned for a class. Handout progress is computed from that plan, the class roster and `SUBMISSION` rows.

```mermaid
erDiagram
  USER ||--o| TUTOR : "is a"
  SCHOOL ||--o{ SCHOOL_CLASS : "has"
  TUTOR ||--o{ TUTOR_ASSIGNMENT : "holds"
  SCHOOL_CLASS ||--o{ TUTOR_ASSIGNMENT : "staffed by"
  SCHOOL_CLASS ||--o{ STUDENT : "enrols"
  STUDENT ||--|| STUDENT_IDENTITY : "PII split"
  STUDENT ||--o{ SUBSCRIPTION : "has"
  LESSON ||--o{ HANDOUT : "has"
  SCHOOL_CLASS ||--o{ SESSION : "hosts"
  TUTOR ||--o{ SESSION : "conducts"
  LESSON |o--o{ SESSION : "covered in"
  SESSION ||--o{ ATTENDANCE : "records"
  STUDENT ||--o{ ATTENDANCE : "marked"
  SESSION ||--o{ PERFORMANCE_NOTE : "has"
  STUDENT ||--o{ PERFORMANCE_NOTE : "about"
  HANDOUT ||--o{ SUBMISSION : "answered by"
  STUDENT ||--o{ SUBMISSION : "submits"
  SUBMISSION ||--o{ SUBMISSION_ENTRY : "yields"
  STUDENT ||--o{ CONSENT_RECORD : "has"
  CONSENT_RECORD ||--o{ CSS_ASSESSMENT : "authorises"
  STUDENT ||--o{ CSS_ASSESSMENT : "takes"
  CSS_ASSESSMENT ||--|{ CSS_DOMAIN_SCORE : "scores"
  SESSION ||--o{ REMINDER : "triggers"
  SCHOOL_CLASS ||--o{ CLASS_LESSON_PLAN : "plans"
  LESSON ||--o{ CLASS_LESSON_PLAN : "scheduled as"

  USER {
    uuid id PK
    string email UK
    string phone
    string role "FOUNDER, ADMIN, TUTOR"
    string status
  }
  TUTOR {
    uuid user_id PK, FK
    string full_name
    date dob
    string address
    string chess_rating
    int experience_years
    string background_check_status
    string lifecycle_state
    uuid approved_by FK
    datetime approved_at
  }
  SCHOOL {
    uuid id PK
    string name
    string address
    string poc_name
    string poc_email
    string grade_levels
    string lifecycle_state
  }
  SCHOOL_CLASS {
    uuid id PK
    uuid school_id FK
    string grade
    string section
    string academic_year
  }
  TUTOR_ASSIGNMENT {
    uuid id PK
    uuid tutor_id FK
    uuid class_id FK
    date start_date
    date end_date
    string status
  }
  STUDENT {
    uuid student_token PK
    uuid class_id FK
    string age_band "A, B or C"
    string status
  }
  STUDENT_IDENTITY {
    uuid student_token PK, FK
    string school_student_id
    string full_name
    date dob
    string guardian_name
    string guardian_email
  }
  SUBSCRIPTION {
    uuid id PK
    uuid student_token FK
    string state
    date start_date
    date end_date
  }
  LESSON {
    uuid id PK
    string header
    string learning_objective
    string board_position
    string info_text
    int version
  }
  HANDOUT {
    uuid id PK
    uuid lesson_id FK
    string kind "handout or assignment"
    string file_ref
    string qr_payload
  }
  SESSION {
    uuid id PK
    uuid class_id FK
    uuid tutor_id FK
    uuid lesson_id FK
    datetime starts_at
    datetime ends_at
    string status
  }
  ATTENDANCE {
    uuid session_id PK, FK
    uuid student_token PK, FK
    boolean present
    uuid marked_by FK
  }
  PERFORMANCE_NOTE {
    uuid id PK
    uuid session_id FK
    uuid student_token FK
    string note
    uuid author_id FK
    datetime created_at
  }
  SUBMISSION {
    uuid id PK
    uuid handout_id FK
    uuid student_token FK
    uuid uploaded_by FK
    string image_ref
    string status
    datetime uploaded_at
    uuid reviewed_by FK
    datetime reviewed_at
  }
  SUBMISSION_ENTRY {
    uuid id PK
    uuid submission_id FK
    int item_no
    string extracted_value
    string confirmed_value
    float confidence
    float score
  }
  CONSENT_RECORD {
    uuid id PK
    uuid student_token FK
    string scope
    string consent_version
    string status
    uuid captured_by FK
    datetime captured_at
  }
  CSS_ASSESSMENT {
    uuid id PK
    uuid student_token FK
    uuid consent_id FK
    string age_band
    int cycle_no
    string status
    datetime started_at
    datetime completed_at
  }
  CSS_DOMAIN_SCORE {
    uuid assessment_id PK, FK
    string domain PK
    float raw_score
    string band_label
  }
  CLASS_LESSON_PLAN {
    uuid id PK
    uuid class_id FK
    uuid lesson_id FK
    int seq_no
  }
  REMINDER {
    uuid id PK
    uuid session_id FK
    uuid recipient_user_id FK
    string channel
    datetime send_at
    string status
  }
```

---

## 3. Lifecycle state machines

### Tutor

```mermaid
stateDiagram-v2
  [*] --> Applied : record created by admin
  Applied --> Verified : credentials and background check cleared
  Verified --> Active : manual admin approval
  Active --> Suspended : admin action
  Suspended --> Active : reinstated
  Active --> Inactive : exit or lapse
  Suspended --> Inactive : exit
  Inactive --> Active : reactivated
  note right of Inactive
    Open class assignments need reassignment
  end note
```

### School

```mermaid
stateDiagram-v2
  [*] --> Enquiry
  Enquiry --> AgreementSigned : agreement signed
  AgreementSigned --> Onboarded : profile complete, roster loaded, tutors linked
  Onboarded --> Active : first session scheduled
```

The `Onboarded` to `Active` trigger is *(proposed)*.

### Student subscription

```mermaid
stateDiagram-v2
  [*] --> TrialPending
  TrialPending --> Active : activated
  Active --> Lapsed : end date passed
  Lapsed --> Active : renewed
```

---

## 4. Sequence: tutor onboarding and approval

```mermaid
sequenceDiagram
  autonumber
  actor AD as Admin
  participant APP as App
  participant DB as Database
  actor TU as Tutor
  AD->>APP: Enter personal and professional details
  APP->>DB: Create Tutor, state Applied
  AD->>APP: Record credentials and background check status
  APP->>DB: Set state Verified
  AD->>APP: Approve tutor
  APP->>APP: Check approver role is Admin or Founder
  APP->>DB: Set state Active, create login identity
  TU->>APP: Request OTP by email or phone
  APP-->>TU: OTP sent
  TU->>APP: Submit OTP
  APP-->>TU: Session started, tutor views only
```

---

## 5. Sequence: session, attendance and performance note

```mermaid
sequenceDiagram
  autonumber
  actor TU as Tutor
  participant APP as App
  participant DB as Database
  participant SC as Scheduler
  TU->>APP: Create session for class and lesson
  APP->>DB: Save Session
  APP->>SC: Register reminders
  SC-->>TU: Reminder before session
  opt Tutor reschedules
    TU->>APP: Update session time
    APP->>DB: Update Session
    APP->>SC: Re-register reminders
  end
  Note over TU,APP: Session held in person
  TU->>APP: Mark attendance per student
  APP->>DB: Save Attendance
  TU->>APP: Add short performance note per student
  APP->>DB: Save PerformanceNote
  TU->>APP: Open student history
  APP->>DB: Query notes ordered by date
  APP-->>TU: Chronological history
```

---

## 6. Class view

A tutor reaches a class from the schedule (tap a session) or by searching, limited to classes they are assigned to. The view shows strength, the roster, and handout progress.

**Definition:** a handout is done for a student when that student has submitted the assignment. For the class, a handout is Done when every enrolled student has submitted. *(Counting only Confirmed submissions is proposed; uploads still in review show as "in review".)*

```mermaid
sequenceDiagram
  autonumber
  actor TU as Tutor
  participant APP as App
  participant DB as Database
  alt From schedule
    TU->>APP: Tap a session on the schedule
    APP->>DB: Resolve class of session
  else From search
    TU->>APP: Search class by school, grade or section
    APP->>DB: Query classes limited to this tutor
  end
  APP->>DB: Check tutor is assigned to the class
  APP->>DB: Count active students, load roster
  APP->>DB: Load class lesson plan in order
  APP->>DB: Count Confirmed submissions per handout
  APP-->>TU: Class view with strength, roster and handout progress
  opt Open a student
    TU->>APP: Tap student
    APP-->>TU: Notes, attendance, submissions, latest snapshot
  end
```

### Handout status within a class (derived, not stored)

```mermaid
stateDiagram-v2
  [*] --> ToDo
  ToDo --> InProgress : first submission confirmed
  InProgress --> Done : all enrolled students submitted
```

Class view layout:

- **Header:** school, grade and section, strength, assigned tutor(s), next session.
- **Roster:** each student with handouts submitted out of planned so far.
- **Handouts:** Done, In progress (for example 22 of 30 submitted), To do, in plan order.
- **Sessions:** upcoming and past.

---

## 7. Sequence: Cognitive Skill Snapshot (tutor-run)

```mermaid
sequenceDiagram
  autonumber
  actor TU as Tutor
  participant APP as App
  participant DB as Database
  TU->>APP: Select student, start Cognitive Skill Snapshot
  APP->>DB: Look up valid consent for student
  alt No valid consent
    APP-->>TU: Blocked, consent required
    TU->>APP: Record guardian consent
    APP->>DB: Save ConsentRecord
  end
  APP->>DB: Create assessment, next cycle number, age band A B or C
  Note over TU,APP: Student completes items on the tutor device
  TU->>APP: Submit completed assessment
  APP->>APP: Score six domains
  APP->>DB: Save six domain scores, status Completed
  APP-->>TU: Latest result with domain bars and band labels
  Note over APP,DB: Six-month re-assessment is a new row, cycle number plus one, same student
```

---

## 8. Sequence: paper assignment to database entries

```mermaid
sequenceDiagram
  autonumber
  actor TU as Tutor
  participant APP as App
  participant OS as Object storage
  participant DB as Database
  participant EX as Extraction worker
  TU->>APP: Download assignment handout
  Note over TU: Printed and completed on paper in class
  TU->>APP: Upload image and tag student
  APP->>OS: Store original image
  APP->>DB: Create Submission, status Uploaded
  APP->>EX: Queue extraction job
  EX->>OS: Fetch image
  EX->>EX: Read QR, extract answers, score confidence
  EX->>DB: Write entries with confidence, status NeedsReview
  APP-->>TU: Review screen, low confidence items flagged
  TU->>APP: Confirm or correct entries
  APP->>DB: Save confirmed values, status Confirmed
  APP->>DB: Feed confirmed scores into student history
  alt Extraction fails
    EX->>DB: Set status Failed
    APP-->>TU: Re-upload or enter manually
  end
```

### Submission status

```mermaid
stateDiagram-v2
  [*] --> Uploaded
  Uploaded --> Processing : job queued
  Processing --> NeedsReview : entries extracted
  Processing --> Failed : extraction error
  Failed --> Uploaded : re-upload
  NeedsReview --> Confirmed : tutor confirms
  Confirmed --> [*]
```

---

## 9. Role permissions *(proposed)*

| Capability | Founder | Admin | Tutor |
|---|---|---|---|
| Create and verify tutors | Yes | Yes | No |
| Approve tutor to Active | Yes | Yes | No |
| Onboard schools, load rosters, link tutors | Yes | Yes | No |
| Author lessons and handouts | Yes | Yes | No |
| Download handouts | Yes | Yes | Assigned classes |
| Create and update sessions | Yes | Yes | Own sessions |
| View class (strength, roster, handout progress) | Yes | Yes | Assigned classes |
| Set a class lesson sequence | Yes | Yes | No |
| Attendance and performance notes | View | View | Assigned classes |
| Run snapshot, upload assignments | View | View | Assigned students |
| Individual reports | Yes | Yes | Assigned students |
| Cross-school and cohort analytics | Yes | Yes | No |

---

## 10. Open decisions

1. **Approval authority:** can Admin approve a tutor to Active, or Founder only?
2. **No rejection path:** the doc's tutor lifecycle has no state for an applicant who fails verification.
3. **Consent evidence:** with no parent login, how is guardian consent captured (paper form uploaded, or collected by the school)?
4. **Extraction review:** I recommend tutor confirmation before anything is committed, since handwriting and board diagrams from children will extract with errors. Also decide how the student is identified: tutor tags at upload, or a per-student code printed on the handout.
5. **Reminders:** do they go to tutors only, given there are no parent accounts?
6. **School Active trigger:** what moves a school from Onboarded to Active?
7. **Lesson sequence owner:** I assumed Admin sets each class's sequence and tutors cannot edit it. Say if tutors should reorder.
8. **Absent students:** if one student never submits, the class can never reach Done. I recommend a per-student Waived state on a handout, set by the tutor.
9. **What counts as submitted:** I assumed Confirmed only. Counting uploads still in review would inflate progress before the tutor has checked the extraction.
10. **Mid-year roster changes:** the Done denominator should use students enrolled at the time. Late joiners need a rule for past handouts.

## 11. Deliberately deferred (Good and May have)

Self-service tutor application, bulk CSV student import, state-change notifications, parent-side views, assessment history comparison, resume of interrupted assessments, norm referencing, configurable item banks, trend charts and auto-generated digests. The schema above leaves room for these without migration: the identity split, `cycle_no`, and `HANDOUT.kind`.
